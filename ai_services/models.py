from django.db import models
from accounts.models import FarmerProfile
from django.utils import timezone


class PestDetection(models.Model):
    SEVERITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]

    farmer = models.ForeignKey(
        FarmerProfile, 
        on_delete=models.CASCADE, 
        related_name='scans',
        null=True,
        blank=True
    )
    media_file = models.FileField(upload_to='pest_scans/')
    crop_name = models.CharField(max_length=100, default='Wheat')
    disease_detected = models.CharField(max_length=150, default='Leaf Rust')
    pest_detected = models.CharField(max_length=150, default='No Major Pest Detected')
    confidence_pct = models.DecimalField(max_digits=5, decimal_places=2, default=98.40)
    severity = models.CharField(max_length=50, choices=SEVERITY_CHOICES, default='High')
    health_score = models.PositiveIntegerField(default=72)
    affected_spread_pct = models.PositiveIntegerField(default=42)
    recommended_pesticide = models.CharField(max_length=255, default='Tilt 250 EC (200 ml/Acre)')
    recommended_fertilizer = models.CharField(max_length=255, default='NPK 19:19:19 (5 Kg/Acre)')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pest & Disease Scan'
        verbose_name_plural = 'Pest & Disease Scans'

    def __str__(self):
        return f"{self.crop_name} - {self.disease_detected} ({self.created_at.strftime('%d %b %Y')})"


class MandiPrice(models.Model):
    TREND_CHOICES = [
        ('rising', 'Rising'),
        ('falling', 'Falling'),
        ('stable', 'Stable'),
    ]

    crop_name = models.CharField(max_length=100)
    market_name = models.CharField(max_length=100)
    today_price = models.DecimalField(max_digits=10, decimal_places=2)
    yesterday_price = models.DecimalField(max_digits=10, decimal_places=2)
    change_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    trend = models.CharField(max_length=20, choices=TREND_CHOICES, default='rising')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Mandi Price'
        verbose_name_plural = 'Mandi Prices'
        unique_together = ('crop_name', 'market_name')

    def save(self, *args, **kwargs):
        # Auto calculate difference & trend if not explicitly passed
        self.change_amount = self.today_price - self.yesterday_price
        if self.change_amount > 0:
            self.trend = 'rising'
        elif self.change_amount < 0:
            self.trend = 'falling'
        else:
            self.trend = 'stable'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop_name} | {self.market_name} - ₹{self.today_price}"

class Scheme(models.Model):
    CATEGORY_CHOICES = [
        ('Subsidy', 'Government Subsidy'),
        ('Loan', 'Agriculture Loan'),
        ('Insurance', 'Crop Insurance'),
        ('Advisory', 'Agri Advisory'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Subsidy')
    state = models.CharField(max_length=100, default='Madhya Pradesh')
    description = models.TextField()
    official_link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  # <-- auto_now_add ki jagah default=timezone.now

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Government Scheme'
        verbose_name_plural = 'Government Schemes'

    def __str__(self):
        return f"{self.title} [{self.category}]"