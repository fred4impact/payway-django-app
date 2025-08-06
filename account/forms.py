from django import forms
from .models import KYC, Transaction, PaymentRequest
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth import get_user_model

User = get_user_model()


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


class AccountSearchForm(forms.Form):
    """Form to search for users by account number or email"""
    search_query = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter account number or email'
        }),
        help_text='Search by account number or email address'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.add_input(Submit('search', 'Search', css_class='btn btn-primary btn-sm'))


class MoneyTransferForm(forms.Form):
    """Form for money transfers"""
    receiver_account = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter recipient account number'
        }),
        help_text='Enter the 10-digit account number of the recipient'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm currency-input',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Enter the amount to transfer'
    )
    
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Optional description'
        }),
        help_text='Optional description for the transfer'
    )
    
    reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Optional reference'
        }),
        help_text='Optional reference number'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('transfer', 'Send Money', css_class='btn btn-success btn-lg w-100'))

    def clean_receiver_account(self):
        account_number = self.cleaned_data['receiver_account']
        try:
            account = Account.objects.get(account_number=account_number, is_active=True)
            return account
        except Account.DoesNotExist:
            raise forms.ValidationError('Account number not found or inactive')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount


class PaymentRequestForm(forms.Form):
    """Form for creating payment requests"""
    recipient_account = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Enter recipient account number'
        }),
        help_text='Enter the 10-digit account number of the person you want to request money from'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm currency-input',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Enter the amount you want to request'
    )
    
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'What is this payment for?'
        }),
        help_text='Explain what this payment request is for'
    )
    
    expires_in_days = forms.ChoiceField(
        choices=[
            (1, '1 day'),
            (3, '3 days'),
            (7, '1 week'),
            (14, '2 weeks'),
            (30, '1 month'),
        ],
        initial=7,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'}),
        help_text='When should this request expire?'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('request', 'Send Request', css_class='btn btn-primary btn-lg w-100'))

    def clean_recipient_account(self):
        account_number = self.cleaned_data['recipient_account']
        try:
            account = Account.objects.get(account_number=account_number, is_active=True)
            return account
        except Account.DoesNotExist:
            raise forms.ValidationError('Account number not found or inactive')

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount


class TransactionFilterForm(forms.Form):
    """Form for filtering transactions"""
    transaction_type = forms.ChoiceField(
        choices=[('', 'All Types')] + Transaction.TRANSACTION_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Transaction.TRANSACTION_STATUS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control form-control-sm'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control form-control-sm',
            'type': 'date'
        })
    )
    
    min_amount = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Min amount',
            'step': '0.01'
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'placeholder': 'Max amount',
            'step': '0.01'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.add_input(Submit('filter', 'Filter', css_class='btn btn-outline-primary btn-sm'))
        self.helper.add_input(Submit('export', 'Export CSV', css_class='btn btn-outline-success btn-sm')) 