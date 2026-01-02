from django.contrib import admin
from .models import TrainerProfile, PendingUserRegistration, EmailVerification, Attendance

admin.site.register(TrainerProfile)
admin.site.register(PendingUserRegistration)
admin.site.register(EmailVerification)
admin.site.register(Attendance)
