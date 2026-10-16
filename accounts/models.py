from django.contrib.auth.models import User
from django.db import models


class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='farmer_profile')
    farmer_id_code = models.CharField(max_length=30, unique=True, blank=True)
    full_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to='profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    village = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True, default='Indore')
    state = models.CharField(max_length=100, default='Madhya Pradesh')
    experience_years = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.farmer_id_code:
            self.farmer_id_code = f"FRM-{10000 + self.pk}"
            super().save(update_fields=['farmer_id_code'])

    @property
    def initials(self):
        parts = (self.full_name or self.user.username).split()
        return ''.join(p[0] for p in parts[:2]).upper()

    def __str__(self):
        return f"{self.full_name} ({self.farmer_id_code})"


class FarmerDocument(models.Model):
    DOC_TYPES = [
        ('Aadhaar', 'Aadhaar Card'),
        ('Khasra', 'Khasra / B1 / Khatoni'),
        ('Bank', 'Bank Passbook'),
        ('KCC', 'Kisan Credit Card'),
        ('SoilCard', 'Soil Health Card'),
        ('Insurance', 'Fasal Bima Receipt'),
        ('Other', 'Other'),
    ]
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=150)
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default='Other')
    file = models.FileField(upload_to='farmer_documents/', blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
