from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone

from accounts.models import FarmerProfile


def _sum(qs, field):
    return qs.aggregate(t=Sum(field))['t'] or Decimal('0')


def current_year():
    return str(timezone.localdate().year)


class Land(models.Model):
    SOIL_CHOICES = [
        ('Black Cotton', 'Kaali Mitti (Black Cotton)'),
        ('Alluvial', 'Domat Mitti (Alluvial)'),
        ('Red', 'Laal Mitti (Red)'),
        ('Sandy Loam', 'Balui Mitti (Sandy Loam)'),
        ('Other', 'Anya'),
    ]
    WATER_CHOICES = [
        ('Borewell', 'Borewell / Tube-well'), ('Well', 'Kuan'), ('Canal', 'Nahar'),
        ('River', 'Nadi / Talab'), ('Rainfed', 'Sirf Barish (Rain-fed)'),
    ]
    IRRIGATION_CHOICES = [
        ('Flood', 'Paani Bharna (Flood)'), ('Drip', 'Drip'),
        ('Sprinkler', 'Sprinkler'), ('Furrow', 'Nali / Furrow'),
    ]
    OWNERSHIP_CHOICES = [
        ('Own', 'Apni Zameen'), ('Leased', 'Theke / Kiraye Par'), ('Batai', 'Batai Par'),
    ]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='lands')
    title = models.CharField(max_length=120)
    khasra_number = models.CharField(max_length=60, blank=True)
    total_area_acres = models.DecimalField(max_digits=7, decimal_places=2)
    soil_type = models.CharField(max_length=50, choices=SOIL_CHOICES, default='Black Cotton')
    water_source = models.CharField(max_length=50, choices=WATER_CHOICES, default='Borewell')
    irrigation_type = models.CharField(max_length=50, choices=IRRIGATION_CHOICES, default='Flood')
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='Own')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']

    def sown_acres(self, exclude_crop_id=None):
        qs = self.crops.filter(is_active=True)
        if exclude_crop_id:
            qs = qs.exclude(pk=exclude_crop_id)
        return _sum(qs, 'allocated_acres')

    def available_area(self, exclude_crop_id=None):
        return self.total_area_acres - self.sown_acres(exclude_crop_id)

    def usage_pct(self):
        if not self.total_area_acres:
            return 0
        return min(100, int(self.sown_acres() / self.total_area_acres * 100))

    def __str__(self):
        return f"{self.title} ({self.total_area_acres} Acre)"


class Crop(models.Model):
    STAGE_CHOICES = [
        ('Sowing', 'Buwai (Sowing)'),
        ('Vegetative', 'Badhwar (Vegetative)'),
        ('Flowering', 'Phool Aana (Flowering)'),
        ('GrainFilling', 'Daana Pakaav (Grain Filling)'),
        ('Harvesting', 'Katayi (Harvesting)'),
        ('Completed', 'Fasal Poori Hui (Completed)'),
    ]
    STAGE_ORDER = [s[0] for s in STAGE_CHOICES]
    SEASON_CHOICES = [('Kharif', 'Kharif (Barish)'), ('Rabi', 'Rabi (Sardi)'), ('Zaid', 'Zaid (Garmi)')]

    land = models.ForeignKey(Land, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=100)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='Rabi')
    season_year = models.CharField(max_length=20, default=current_year)
    allocated_acres = models.DecimalField(max_digits=7, decimal_places=2)
    seed_info = models.CharField(max_length=200, blank=True)
    sowing_date = models.DateField(default=timezone.localdate)
    expected_harvest_date = models.DateField()
    actual_harvest_date = models.DateField(blank=True, null=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='Sowing')
    expected_yield_quintal = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    actual_yield_quintal = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sowing_date']

    def save(self, *args, **kwargs):
        self.is_active = self.stage != 'Completed'
        super().save(*args, **kwargs)

    # ---- timeline ----
    def days_to_harvest(self):
        return (self.expected_harvest_date - timezone.localdate()).days

    def is_overdue(self):
        return self.is_active and self.days_to_harvest() < 0

    def days_since_sowing(self):
        return (timezone.localdate() - self.sowing_date).days

    def progress_pct(self):
        if not self.is_active:
            return 100
        total = (self.expected_harvest_date - self.sowing_date).days or 1
        return max(0, min(100, int(self.days_since_sowing() / total * 100)))

    def next_stage(self):
        i = self.STAGE_ORDER.index(self.stage)
        return self.STAGE_ORDER[i + 1] if i + 1 < len(self.STAGE_ORDER) else None

    # ---- paisa ----
    def total_expense(self):
        return _sum(self.expenses.all(), 'amount')

    def total_revenue(self):
        return _sum(self.sales.all(), 'total_amount')

    def total_received(self):
        return _sum(self.sales.all(), 'amount_received')

    def net_profit(self):
        return self.total_revenue() - self.total_expense()

    def cost_per_acre(self):
        if not self.allocated_acres:
            return Decimal('0')
        return (self.total_expense() / self.allocated_acres).quantize(Decimal('0.01'))

    # ---- stock ----
    def total_sold_quintals(self):
        return _sum(self.sales.all(), 'quantity_quintals')

    def remaining_stock(self):
        return max(Decimal('0'), self.actual_yield_quintal - self.total_sold_quintals())

    def __str__(self):
        return f"{self.name} - {self.land.title}"


class CropOperationLog(models.Model):
    """Khet ka rozana kaam: majdoor, paani, khad, spray, jotayi, katayi..."""
    OP_TYPES = [
        ('Plowing', 'Jotayi / Khet Tayyari'),
        ('Sowing', 'Buwai'),
        ('Weeding', 'Nindayi / Gudayi'),
        ('Irrigation', 'Sinchai (Paani)'),
        ('Fertilizer', 'Khad (Urea / DAP / Micro)'),
        ('Spray', 'Keetnashak / Fungicide Spray'),
        ('Harvesting', 'Katayi'),
        ('Threshing', 'Thresher / Gahai'),
        ('Other', 'Anya Kaam'),
    ]
    EXPENSE_CATEGORY = {
        'Plowing': 'Machinery', 'Sowing': 'Labour', 'Weeding': 'Labour', 'Irrigation': 'Irrigation',
        'Fertilizer': 'Fertilizer', 'Spray': 'Pesticide', 'Harvesting': 'Labour',
        'Threshing': 'Machinery', 'Other': 'Other',
    }

    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(max_length=30, choices=OP_TYPES)
    date = models.DateField(default=timezone.localdate)
    labour_count = models.PositiveIntegerField(default=0)
    labour_cost_per_person = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    material_used = models.CharField(max_length=200, blank=True)
    hours_run = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def save(self, *args, **kwargs):
        if not self.total_cost and self.labour_count and self.labour_cost_per_person:
            self.total_cost = self.labour_count * self.labour_cost_per_person
        super().save(*args, **kwargs)
        self.sync_expense()

    def sync_expense(self):
        """Operation ka kharcha apne-aap Kharcha (ledger) me aata hai - ek hi jagah count hota hai."""
        from finance.models import FarmExpense
        if self.total_cost and self.total_cost > 0:
            parts = [self.get_operation_type_display()]
            if self.material_used:
                parts.append(self.material_used)
            FarmExpense.objects.update_or_create(
                source_operation=self,
                defaults={
                    'farmer': self.crop.land.farmer,
                    'crop': self.crop,
                    'title': ' - '.join(parts),
                    'category': self.EXPENSE_CATEGORY.get(self.operation_type, 'Other'),
                    'amount': self.total_cost,
                    'date': self.date,
                    'description': f"{self.labour_count} majdoor, {self.hours_run} ghante. {self.notes}".strip(),
                })
        else:
            FarmExpense.objects.filter(source_operation=self).delete()

    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.crop.name} ({self.date})"

from django.utils import timezone

class FarmAlert(models.Model):
    ALERT_TYPES = [
        ('weather', 'Mausam Alert'),
        ('pest', 'Keeda / Beemari Warning'),
        ('fertilizer', 'Khad Reminder'),
        ('irrigation', 'Sinchai Reminder'),
        ('harvest', 'Katayi Time Notice'),
    ]
    SEVERITY = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('danger', 'Critical'),
    ]

    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='alerts', null=True, blank=True)
    alert_type = models.CharField(max_length=40, choices=ALERT_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"