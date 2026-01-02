from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def is_trainer(user):
    return user.groups.filter(name='Trainer').exists()

def is_admin(user):
    return user.is_superuser or user.groups.filter(
        name__in=[
            'Admin',
            'Project Manager',
            'Monitoring Manager',
            'Supervisor'
        ]
    ).exists()


def admin_required(view_func):
    """
    Decorator to check if user has admin designation (PM, PRC, GE, IT)
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            if request.user.trainerprofile.is_admin():
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page. Admin access required.')
                return redirect('home')
        except:
            messages.error(request, 'Profile not found. Please contact administrator.')
            return redirect('home')
    return wrapper


def pum_or_admin_required(view_func):
    """
    Decorator to check if user is PUM or admin
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        try:
            profile = request.user.trainerprofile
            if profile.is_admin() or profile.is_pum():
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'You do not have permission to access this page. PUM or Admin access required.')
                return redirect('home')
        except:
            messages.error(request, 'Profile not found. Please contact administrator.')
            return redirect('home')
    return wrapper
