from django.db import models
from django.contrib.auth.models import User
import random
from django.utils import timezone
from datetime import timedelta

class TrainerProfile(models.Model):
    DESIGNATION_CHOICES = [
        ('PM', 'PM'),
        ('PRC', 'PRC'),
        ('TS', 'TS'),
        ('GE', 'GE'),
        ('M&E', 'M&E'),
        ('PUM', 'PUM'),
        ('WT', 'WT'),
        ('IT', 'IT'),
        ('Finance', 'Finance'),
        ('Admin', 'Admin'),
    ]
    
    # Admin designations that have full access
    ADMIN_DESIGNATIONS = ['PM', 'PRC', 'GE', 'IT']
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_trainers"
    )
    pu_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="PU Code")
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, default='WT', verbose_name="Designation")

    def __str__(self):
        return f"{self.user.username} - {self.designation}"
    
    def is_admin(self):
        """Check if user has admin designation"""
        return self.designation in self.ADMIN_DESIGNATIONS
    
    def is_pum(self):
        """Check if user is PUM (can mark attendance)"""
        return self.designation == 'PUM'
    
    def is_wt(self):
        """Check if user is WT (warehouse technician)"""
        return self.designation == 'WT'


class PendingUserRegistration(models.Model):
    """Temporarily stores registration data until email is verified"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    password = models.CharField(max_length=255)
    pu_code = models.CharField(max_length=50)
    designation = models.CharField(max_length=20, default='WT')
    verification_code = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_expired(self):
        """Check if registration link has expired (24 hours)"""
        expiration_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiration_time
    
    def save(self, *args, **kwargs):
        if not self.verification_code:
            # Generate random 6-digit code
            self.verification_code = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.email} - Verified: {self.is_verified}"
    
    class Meta:
        verbose_name = "Pending User Registration"
        verbose_name_plural = "Pending User Registrations"


class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, blank=True)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.code:
            # Generate random 6-digit code
            self.code = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Verified: {self.is_verified}"


class Attendance(models.Model):
    """Staff attendance tracking"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances', verbose_name="Staff Member")
    date = models.DateField(verbose_name="Date")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present', verbose_name="Status")
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='marked_attendances', verbose_name="Marked By")
    marked_at = models.DateTimeField(auto_now_add=True, verbose_name="Marked At")
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date', 'user__first_name']
        verbose_name = "Attendance"
        verbose_name_plural = "Attendance Records"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.date} - {self.status}"
