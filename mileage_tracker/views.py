from django.shortcuts import redirect
from django.contrib import messages

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')   # or 'admin_dashboard' / 'mileage_records'
    return redirect('login')

from django.contrib.auth import views as auth_views

# views.py
from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login')  # or your desired redirect        