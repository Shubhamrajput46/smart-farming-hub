from django.db import models
from django.utils import timezone

from accounts.models import FarmerProfile


class Notification(models.Model):
    KINDS = [
        ('system', 'System'), ('crop', 'Fasal'), ('harvest', 'Katayi'), ('irrigation', 'Sinchai'),
        ('fertilizer', 'Khad'), ('payment', 'Payment'), ('sale', 'Bikri'), ('stock', 'Stock'),
        ('reminder', 'Yaad-dihani'), ('document', 'Document'),
    ]
    ICONS = {
        'system': 'fa-circle-info', 'crop': 'fa-seedling', 'harvest': 'fa-wheat-awn', 'irrigation': 'fa-droplet',
        'fertilizer': 'fa-flask', 'payment': 'fa-indian-rupee-sign', 'sale': 'fa-sack-dollar',
        'stock': 'fa-warehouse', 'reminder': 'fa-bell', 'document': 'fa-file-lines',
    }
    SEVERITY = [('info', 'Jaankari'), ('success', 'Safal'), ('warning', 'Savdhani'), ('danger', 'Zaroori')]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='notifications')
    kind = models.CharField(max_length=20, choices=KINDS, default='system')
    severity = models.CharField(max_length=10, choices=SEVERITY, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    dedupe_key = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['farmer', 'dedupe_key'], name='uniq_farmer_dedupe_key'),
        ]

    @property
    def icon(self):
        return self.ICONS.get(self.kind, 'fa-bell')

    def __str__(self):
        return self.title


class Reminder(models.Model):
    """Kisan ki apni yaad-dihani: 'Kal Urea dalna hai', 'Thresher book karna hai'."""
    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE, related_name='reminders')
    crop = models.ForeignKey('farms.Crop', on_delete=models.CASCADE, null=True, blank=True, related_name='reminders')
    title = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    due_date = models.DateField()
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_done', 'due_date']

    @property
    def is_overdue(self):
        return not self.is_done and self.due_date < timezone.localdate()

    def __str__(self):
        return self.title
