from django.urls import path
from .views import (register_user, verify_email, test_email, profile,
                   CustomPasswordResetView, CustomPasswordResetDoneView,
                   CustomPasswordResetConfirmView, CustomPasswordResetCompleteView,
                   CustomPasswordChangeView, mark_attendance, view_attendance)
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register/', register_user, name='register'),
    path('verify/', verify_email, name='verify_email'),
    path('test-email/', test_email),
    path('profile/', profile, name='profile'),

    path('password_change/', 
         CustomPasswordChangeView.as_view(), 
         name='password_change'),
    path('password_change/done/', 
         auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), 
         name='password_change_done'),

    path('password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Attendance URLs
    path('attendance/mark/', mark_attendance, name='mark_attendance'),
    path('attendance/view/', view_attendance, name='view_attendance'),

]
