from django import forms
from django.forms.widgets import ClearableFileInput
from .models import MileageRecord


class MultipleImageInput(ClearableFileInput):
    allow_multiple_selected = True

class MileageForm(forms.ModelForm):
    images = forms.ImageField(
        required=False,
        label="Additional Images",
        help_text="You can upload multiple images",
        widget=MultipleImageInput(attrs={
            'accept': 'image/*'
        })
    )




# class MileageForm(forms.ModelForm):
#     # ✅ ADD THIS FIELD HERE
#     images = forms.ImageField(
#         required=False,
#         label="Additional Images",
#         help_text="You can upload multiple images",
#         widget=ClearableFileInput(attrs={
#             'multiple': True,
#             'accept': 'image/*'
#         })
#     )

    class Meta:
        model = MileageRecord
        fields = ['start_km', 'end_km', 'start_photo', 'end_photo']
        widgets = {
            'start_km': forms.NumberInput(attrs={'required': False, 'step': '1', 'min': '0'}),
            'end_km': forms.NumberInput(attrs={'required': False, 'step': '1', 'min': '0'}),
            'start_photo': ClearableFileInput(attrs={
                'accept': 'image/*',
                'capture': 'camera',
                'required': False
            }),
            'end_photo': ClearableFileInput(attrs={
                'accept': 'image/*',
                'capture': 'camera',
                'required': False
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_km'].required = False
        self.fields['end_km'].required = False
        self.fields['start_photo'].required = False
        self.fields['end_photo'].required = False


    def clean_start_km(self):
        """Validate start_km is a natural number (positive integer) if provided"""
        start_km = self.cleaned_data.get('start_km')
        if start_km is not None:
            if start_km < 0:
                raise forms.ValidationError('Start KM cannot be negative.')
            if not isinstance(start_km, int) or start_km != int(start_km):
                raise forms.ValidationError('Start KM must be a natural number.')
        return start_km

    def clean_end_km(self):
        """Validate end_km is a natural number (positive integer) if provided"""
        end_km = self.cleaned_data.get('end_km')
        if end_km is not None:
            if end_km < 0:
                raise forms.ValidationError('End KM cannot be negative.')
            if not isinstance(end_km, int) or end_km != int(end_km):
                raise forms.ValidationError('End KM must be a natural number.')
        return end_km

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_km')
        end = cleaned_data.get('end_km')

        # If both start and end are provided, validate their relationship
        if start is not None and end is not None and start > 0 and end > 0:
            if end <= start:
                raise forms.ValidationError("End KM must be greater than Start KM")

        return cleaned_data

