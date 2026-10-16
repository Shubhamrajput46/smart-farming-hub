from decimal import Decimal

from django.db import models
from django.utils import timezone

from accounts.models import FarmerProfile
from farms.models import Crop, CropOperationLog


class FarmExpense(models.Model):
    CATEGORIES = [
        ('Seed', 'Beej'), ('Fertilizer', 'Khad'), ('Pesticide', 'Keetnashak / Dawai'),
        ('Labour', 'Majdoori'), ('Irrigation', 'Sinchai / Bijli Bill'), ('Machinery', 'Tractor / Machine Kiraya'),
        ('Fuel', 'Diesel / Petrol'), ('Transport', 'Dhulai / Transport'), ('Rent', 'Zameen Kiraya / Theka'),
        ('Interest', 'Loan Byaj'), ('Other', 'Anya'),
    ]
    PAYMENT_METHODS = [('Cash', 'Cash'), ('UPI', 'UPI / Online'), ('Bank', 'Bank Transfer'),
                       ('Cheque', 'Cheque'), ('Udhaar', 'Udhaar (Baad me dena)')]
    STATUS = [('Paid', 'Chukta (Paid)'), ('Pending', 'Baaki (Pending)')]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='expenses')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    source_operation = models.OneToOneField(CropOperationLog, on_delete=models.CASCADE, null=True, blank=True,
                                            related_name='expense', editable=False)
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=30, choices=CATEGORIES, default='Other')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    paid_to = models.CharField(max_length=150, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    payment_status = models.CharField(max_length=20, choices=STATUS, default='Paid')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def save(self, *args, **kwargs):
        if self.payment_method == 'Udhaar' and self._state.adding:
            self.payment_status = 'Pending'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - Rs {self.amount}"


class FarmSale(models.Model):
    STATUS = [('Paid', 'Poora Mila'), ('Partial', 'Aanshik Mila'), ('Pending', 'Paisa Baaki')]
    PLACES = [('Mandi', 'Mandi'), ('Vyapari', 'Vyapari / Aadhat'), ('Ghar', 'Ghar / Khet Se'), ('Society', 'Samiti / Sarkari Kharid')]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='sales')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    buyer_name = models.CharField(max_length=150)
    sale_place = models.CharField(max_length=20, choices=PLACES, default='Mandi')
    quantity_quintals = models.DecimalField(max_digits=9, decimal_places=2)
    price_per_quintal = models.DecimalField(max_digits=9, decimal_places=2)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=20, choices=STATUS, default='Pending', editable=False)
    sale_date = models.DateField(default=timezone.localdate)
    remarks = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sale_date', '-id']

    def save(self, *args, **kwargs):
        """Net rashi = (quintal x bhav) - katauti (tulai/hamali/commission). Status received se nikalta hai."""
        self.total_amount = (self.quantity_quintals * self.price_per_quintal) - (self.deductions or 0)
        if self.amount_received >= self.total_amount:
            self.payment_status = 'Paid'
        elif self.amount_received > 0:
            self.payment_status = 'Partial'
        else:
            self.payment_status = 'Pending'
        super().save(*args, **kwargs)

    @property
    def balance(self):
        return max(Decimal('0'), self.total_amount - self.amount_received)

    def __str__(self):
        return f"{self.buyer_name} - {self.quantity_quintals} Qt"
