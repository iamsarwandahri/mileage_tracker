from django.db import models
from django.contrib.auth.models import User

class TrainerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_trainers"
    )
    pu_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="PU Code")

    def __str__(self):
        return self.user.username
    



import random

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
