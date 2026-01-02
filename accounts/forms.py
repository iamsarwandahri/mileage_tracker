from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordChangeForm
import re
from .models import TrainerProfile, PendingUserRegistration


def validate_password_strength(password):
    """
    Validate password meets security requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one number
    - At least one special character
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must include at least one uppercase letter (A-Z).")
    
    if not re.search(r'[0-9]', password):
        errors.append("Password must include at least one number (0-9).")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("Password must include at least one special character (!@#$%^&*()-_=+, etc).")
    
    if errors:
        raise ValidationError(errors)

class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your first name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your last name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your email'
    }))
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password (min 8 chars, 1 uppercase, 1 number, 1 special char)'
        }),
        help_text='Must be at least 8 characters with uppercase letter, number, and special character'
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    pu_code = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter PU Code (Required for PUM and WT)'
    }), label="PU Code")
    
    designation = forms.ChoiceField(
        choices=[
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
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        }),
        label="Designation"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2', 'designation']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['first_name', 'last_name', 'email', 'pu_code', 'designation']:
                field.widget.attrs['class'] = 'form-control'
                if field.label:
                    field.widget.attrs['placeholder'] = f'Enter {field.label.lower()}'

    def clean_email(self):
        """Check if email already exists"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered. Please use a different email.')
        if PendingUserRegistration.objects.filter(email=email, is_verified=False).exists():
            raise ValidationError('This email is already pending verification. Please check your inbox.')
        return email

    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password')
        if password:
            validate_password_strength(password)
        return password

    def clean(self):
        """Validate that passwords match and PU code is provided for PUM/WT"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        designation = cleaned_data.get('designation')
        pu_code = cleaned_data.get('pu_code')

        if password and password2:
            if password != password2:
                raise ValidationError('Passwords do not match. Please try again.')
        
        # Validate PU code is required for PUM and WT
        if designation in ['PUM', 'WT']:
            if not pu_code or pu_code.strip() == '':
                raise ValidationError('PU Code is required for PUM and WT designations.')
        
        return cleaned_data

    def save(self, commit=True):
        """Save registration data to PendingUserRegistration instead of creating User immediately"""
        from django.contrib.auth.hashers import make_password
        
        email = self.cleaned_data['email']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        password = self.cleaned_data['password']
        pu_code = self.cleaned_data['pu_code']
        designation = self.cleaned_data['designation']
        
        # Hash the password before storing
        hashed_password = make_password(password)
        
        # Create or update pending registration
        pending_registration, created = PendingUserRegistration.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'password': hashed_password,
                'pu_code': pu_code,
                'designation': designation,
                'is_verified': False
            }
        )
        
        # If updating, refresh the data
        if not created:
            pending_registration.first_name = first_name
            pending_registration.last_name = last_name
            pending_registration.password = hashed_password
            pending_registration.pu_code = pu_code
            pending_registration.designation = designation
            pending_registration.is_verified = False
            pending_registration.save()
        
        return pending_registration


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with strength validation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Update field widgets to include Bootstrap classes
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your new password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Confirm your new password'
        })
        
        # Update labels
        self.fields['old_password'].label = 'Current Password'
        self.fields['new_password1'].label = 'New Password'
        self.fields['new_password2'].label = 'Confirm New Password'
        
        # Add help text
        self.fields['new_password1'].help_text = 'Must be at least 8 characters with uppercase letter, number, and special character'
    
    def clean_new_password1(self):
        """Validate new password strength"""
        password = self.cleaned_data.get('new_password1')
        if password:
            validate_password_strength(password)
        return password
