from django import forms
from .models import KYC
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column


class KYCForm(forms.ModelForm):
    class Meta:
        model = KYC
        fields = [
            'full_name', 'date_of_birth', 'nationality', 'address', 
            'city', 'state', 'country', 'postal_code',
            'id_document', 'proof_of_address', 'selfie_photo'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your nationality'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your state/province'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your country'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your postal code'}),
            'id_document': forms.FileInput(attrs={'class': 'form-control'}),
            'proof_of_address': forms.FileInput(attrs={'class': 'form-control'}),
            'selfie_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Submit KYC', css_class='btn btn-success btn-lg w-100')) 