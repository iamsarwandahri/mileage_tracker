from django.shortcuts import render, redirect
from django.contrib.auth.models import User, Group
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm
from .models import EmailVerification, TrainerProfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView


def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            # Save user and trainer profile using form's save method
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            
            # Assign role
            role = 'trainer'
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)

            # Create email verification and auto-generate 6-digit code
            verification = EmailVerification.objects.create(user=user)

            # Send code to user email
            send_mail(
                subject='Verify your email',
                message=f'Hello {user.first_name},\n\nYour verification code is: {verification.code}\n\nPlease enter this code to activate your account.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

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
            verification = EmailVerification.objects.get(code=code)
            verification.is_verified = True
            verification.user.is_active = True
            verification.user.save()
            verification.save()
            messages.success(request, 'Email verified! You can now login.')
            return redirect('login')
        except EmailVerification.DoesNotExist:
            messages.error(request, 'Invalid verification code')
    return render(request, 'accounts/verify_email.html')

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
