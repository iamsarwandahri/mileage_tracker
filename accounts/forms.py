from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import TrainerProfile

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
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
    pu_code = forms.CharField(max_length=50, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter PU Code'
    }), label="PU Code")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['first_name', 'last_name', 'email', 'pu_code']:
                field.widget.attrs['class'] = 'form-control'
                if field.label:
                    field.widget.attrs['placeholder'] = f'Enter {field.label.lower()}'

    def clean_email(self):
        """Check if email already exists"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered. Please use a different email.')
        return email

    def clean(self):
        """Validate that passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and password2:
            if password != password2:
                raise ValidationError('Passwords do not match. Please try again.')
        return cleaned_data

    def save(self, commit=True):
        # Generate username from email since Django requires it
        email = self.cleaned_data['email']
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        
        # Ensure username is unique
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = super().save(commit=False)
        user.username = username
        
        if commit:
            user.save()
            # Create trainer profile with PU code
            TrainerProfile.objects.create(
                user=user,
                pu_code=self.cleaned_data['pu_code']
            )
        
        return user
