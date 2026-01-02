from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm, CustomPasswordChangeForm
from .models import EmailVerification, TrainerProfile, PendingUserRegistration, Attendance
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordChangeView
from .utils import admin_required, pum_or_admin_required
from datetime import date, timedelta
from django.db.models import Q


def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save to PendingUserRegistration (NOT to User yet)
            pending_registration = form.save(commit=True)
            
            # Send verification code to email
            send_mail(
                subject='Verify your email - CabiRos',
                message=f'Hello {pending_registration.first_name},\n\nYour verification code is: {pending_registration.verification_code}\n\nPlease enter this code to complete your registration. This code will expire in 24 hours.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[pending_registration.email],
                fail_silently=False,
            )
            
            messages.success(request, 'Registration submitted! Please check your email for the verification code.')
            # Store email in session to display on verify page
            request.session['pending_email'] = pending_registration.email
            return redirect('verify_email')
        else:
            # Form has errors, they will be displayed in the template
            pass
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register_clean.html', {'form': form})



from django.contrib import messages


def verify_email(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        try:
            pending_registration = PendingUserRegistration.objects.get(
                verification_code=code,
                is_verified=False
            )
            
            # Check if registration link has expired
            if pending_registration.is_expired():
                pending_registration.delete()
                messages.error(request, 'Verification code has expired. Please register again.')
                return redirect('register')
            
            # Create User account from pending registration
            base_username = pending_registration.email.split('@')[0]
            username = base_username
            counter = 1
            
            # Ensure username is unique
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create the User account
            from django.contrib.auth.hashers import check_password
            user = User.objects.create(
                username=username,
                email=pending_registration.email,
                first_name=pending_registration.first_name,
                last_name=pending_registration.last_name,
                is_active=True
            )
            user.password = pending_registration.password  # Use hashed password
            user.save()
            
            # Assign group based on designation
            designation = pending_registration.designation
            group, _ = Group.objects.get_or_create(name=designation)
            user.groups.add(group)
            
            # Update trainer profile with PU code (signal already created it)
            trainer_profile = TrainerProfile.objects.get(user=user)
            trainer_profile.pu_code = pending_registration.pu_code
            trainer_profile.designation = pending_registration.designation
            trainer_profile.save()
            
            # Mark pending registration as verified and delete it
            pending_registration.is_verified = True
            pending_registration.delete()
            
            # Clear email from session
            if 'pending_email' in request.session:
                del request.session['pending_email']
            
            messages.success(request, 'Email verified! Your account has been created. You can now login.')
            return redirect('login')
        except PendingUserRegistration.DoesNotExist:
            messages.error(request, 'Invalid verification code. Please try again or register again.')
    
    # Get email from session to display
    pending_email = request.session.get('pending_email', None)
    
    return render(request, 'accounts/verify_email.html', {'pending_email': pending_email})

from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    send_mail(
        subject='Test Email from Django',
        message='This is a test email. If you get it, email works!',
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=['your_personal_email@gmail.com'],
        fail_silently=False,
    )
    return HttpResponse("Test email sent!")


class ProfileForm(forms.ModelForm):
    pu_code = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter PU Code'
        }),
        label="PU Code"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            try:
                trainer_profile = self.user.trainerprofile
                self.fields['pu_code'].initial = trainer_profile.pu_code
            except TrainerProfile.DoesNotExist:
                pass

    def save(self, commit=True):
        user = super().save(commit=commit)
        pu_code = self.cleaned_data.get('pu_code')

        # Get or create trainer profile
        trainer_profile, created = TrainerProfile.objects.get_or_create(user=user)
        trainer_profile.pu_code = pu_code
        trainer_profile.save()

        return user

@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user, user=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def custom_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if email exists
        try:
            user = User.objects.get(email=email)
            # Email exists, check password
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                messages.success(request, f"Welcome back, {user_auth.first_name}!")
                return redirect('home')
            else:
                # Email exists but password is wrong
                messages.error(request, "Incorrect password. Please try again.")
        except User.DoesNotExist:
            # Email doesn't exist
            messages.error(request, "No account found with this email address. Please check your email or register for a new account.")
        except User.MultipleObjectsReturned:
            # Multiple users with same email - use the most recent one
            user = User.objects.filter(email=email).order_by('-date_joined').first()
            user_auth = authenticate(request, username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                messages.success(request, f"Welcome back, {user_auth.first_name}!")
                return redirect('home')
            else:
                messages.error(request, "Incorrect password. Please try again.")
        
        # Return form (empty) so AuthenticationForm doesn't add generic auth errors
        form = AuthenticationForm()
        return render(request, 'registration/login.html', {'form': form})
    
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login.html', {'form': form})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = '/accounts/password_reset/done/'
    subject_template_name = 'accounts/password_reset_subject.txt'

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        
        # Check if email exists in database
        if User.objects.filter(email=email).exists():
            # Email exists, proceed with normal password reset
            messages.success(self.request, "Password reset instructions have been sent to your email address.")
            return super().form_valid(form)
        else:
            # Email doesn't exist, show error message
            messages.error(self.request, "No account found with this email address. Please check your email or register for a new account.")
            return self.form_invalid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = '/accounts/reset/done/'


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view with strength validation"""
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/password_change.html'
    success_url = '/accounts/password_change/done/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been changed successfully!')
        return super().form_valid(form)


# Attendance Views
@pum_or_admin_required
def mark_attendance(request):
    """PUM and Admins can mark attendance for staff"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        attendance_date = request.POST.get('date')
        status = request.POST.get('status')
        remarks = request.POST.get('remarks', '')
        
        try:
            staff_user = User.objects.get(id=user_id)
            attendance, created = Attendance.objects.update_or_create(
                user=staff_user,
                date=attendance_date,
                defaults={
                    'status': status,
                    'marked_by': request.user,
                    'remarks': remarks
                }
            )
            if created:
                messages.success(request, f'Attendance marked for {staff_user.get_full_name()}')
            else:
                messages.success(request, f'Attendance updated for {staff_user.get_full_name()}')
        except User.DoesNotExist:
            messages.error(request, 'User not found')
        except Exception as e:
            messages.error(request, f'Error marking attendance: {str(e)}')
        
        return redirect('mark_attendance')
    
    # Get staff members (WTs and other staff) for the dropdown
    staff_members = User.objects.filter(trainerprofile__isnull=False).select_related('trainerprofile').order_by('first_name')
    
    # Get today's date
    today = date.today()
    
    # Get today's attendance records
    todays_attendance = Attendance.objects.filter(date=today).select_related('user', 'marked_by')
    
    context = {
        'staff_members': staff_members,
        'today': today,
        'todays_attendance': todays_attendance,
    }
    return render(request, 'accounts/mark_attendance.html', context)


@login_required
def view_attendance(request):
    """View attendance records - admins see all, staff see their own"""
    profile = request.user.trainerprofile
    
    # Filter parameters
    status_filter = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    user_filter = request.GET.get('user', '')
    
    # Base queryset
    if profile.is_admin():
        # Admins see all attendance
        attendances = Attendance.objects.all()
    else:
        # Staff see only their own attendance
        attendances = Attendance.objects.filter(user=request.user)
    
    # Apply filters
    if status_filter:
        attendances = attendances.filter(status=status_filter)
    
    if date_from:
        attendances = attendances.filter(date__gte=date_from)
    
    if date_to:
        attendances = attendances.filter(date__lte=date_to)
    
    if user_filter and profile.is_admin():
        attendances = attendances.filter(user_id=user_filter)
    
    attendances = attendances.select_related('user', 'marked_by').order_by('-date', 'user__first_name')
    
    # Get all users for admin filter dropdown
    all_users = User.objects.filter(trainerprofile__isnull=False).order_by('first_name') if profile.is_admin() else None
    
    context = {
        'attendances': attendances,
        'is_admin': profile.is_admin(),
        'all_users': all_users,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
        'user_filter': user_filter,
    }
    return render(request, 'accounts/view_attendance.html', context)
