from django.db import models
from django.contrib.auth.models import User

class MileageRecord(models.Model):
    STATUS_CHOICES = (
        ('OK', 'OK'),
        ('WARNING', 'WARNING'),
        ('ALERT', 'ALERT'),
    )
    
    SUBMISSION_STATUS = (
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
    )

    trainer = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    start_km = models.PositiveIntegerField()
    end_km = models.PositiveIntegerField(null=True, blank=True)

    start_photo = models.ImageField(upload_to='start/')
    end_photo = models.ImageField(upload_to='end/', null=True, blank=True)

    distance = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    submission_status = models.CharField(max_length=10, choices=SUBMISSION_STATUS, default='DRAFT')
    edit_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('trainer', 'date')

    def save(self, *args, **kwargs):
        # Only calculate distance if both start_km and end_km are provided
        if self.start_km is not None and self.end_km is not None:
            self.distance = self.end_km - self.start_km

            if self.distance > 125:
                self.status = 'ALERT'
            elif self.distance > 120:
                self.status = 'WARNING'
            else:
                self.status = 'OK'

        super().save(*args, **kwargs)


class MileageImage(models.Model):
    """Additional images related to a mileage record."""
    record = models.ForeignKey(MileageRecord, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='mileage/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.record} ({self.id})"

