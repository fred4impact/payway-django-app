from django import forms
from django.utils import timezone
from .models import KYC, Transaction, PaymentRequest, Account, CreditCard, Currency, Bank, InternationalTransfer
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from django.contrib.auth import get_user_model
from decimal import Decimal
import re

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


class CreditCardForm(forms.ModelForm):
    """Form for adding/editing credit cards"""
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'data-mask': '0000 0000 0000 0000'
        }),
        help_text='Enter your card number'
    )
    
    cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'data-mask': '0000'
        }),
        help_text='3 or 4 digit security code'
    )
    
    expiry_month = forms.ChoiceField(
        choices=[(i, f'{i:02d}') for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    expiry_year = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(timezone.now().year, timezone.now().year + 11)],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Set as default payment method'
    )
    
    daily_limit = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        initial=1000.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Maximum daily spending limit'
    )
    
    monthly_limit = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        initial=5000.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Maximum monthly spending limit'
    )
    
    class Meta:
        model = CreditCard
        fields = ['card_holder_name']
        widgets = {
            'card_holder_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cardholder Name'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('save', 'Save Card', css_class='btn btn-primary btn-lg w-100'))
    
    def clean_card_number(self):
        card_number = self.cleaned_data['card_number'].replace(' ', '').replace('-', '')
        
        # Basic validation
        if not card_number.isdigit():
            raise forms.ValidationError('Card number must contain only digits')
        
        if len(card_number) < 13 or len(card_number) > 19:
            raise forms.ValidationError('Card number must be between 13 and 19 digits')
        
        # Luhn algorithm validation
        if not self.instance.validate_card_number(card_number):
            raise forms.ValidationError('Invalid card number')
        
        return card_number
    
    def clean_cvv(self):
        cvv = self.cleaned_data['cvv']
        
        if not cvv.isdigit():
            raise forms.ValidationError('CVV must contain only digits')
        
        card_number = self.cleaned_data.get('card_number', '')
        card_type, _ = self.instance.detect_card_type(card_number)
        
        if card_type == 'amex' and len(cvv) != 4:
            raise forms.ValidationError('American Express cards require 4-digit CVV')
        elif card_type != 'amex' and len(cvv) != 3:
            raise forms.ValidationError('CVV must be 3 digits for this card type')
        
        return cvv
    
    def clean_expiry_month(self):
        month = int(self.cleaned_data['expiry_month'])
        year = int(self.cleaned_data['expiry_year'])
        
        if not self.instance.validate_expiry_date(month, year):
            raise forms.ValidationError('Card has expired')
        
        return month
    
    def clean_expiry_year(self):
        return int(self.cleaned_data['expiry_year'])
    
    def save(self, commit=True):
        card = super().save(commit=False)
        
        # Process card data
        card_number = self.cleaned_data['card_number'].replace(' ', '').replace('-', '')
        cvv = self.cleaned_data['cvv']
        
        # Detect card type
        card_type, card_brand = card.detect_card_type(card_number)
        card.card_type = card_type
        card.card_brand = card_brand
        
        # Set display fields
        card.last_four_digits = card.get_last_four_digits(card_number)
        card.masked_number = card.mask_card_number(card_number)
        
        # Encrypt sensitive data
        card.encrypt_card_data(card_number, cvv)
        
        if commit:
            card.save()
        
        return card


class CardFundingForm(forms.Form):
    """Form for funding account from credit card"""
    card = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the card to use for funding'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Amount to add to your account'
    )
    
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description'
        }),
        help_text='Optional description for this funding'
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['card'].queryset = user.credit_cards.filter(status='active')
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('fund', 'Fund Account', css_class='btn btn-success btn-lg w-100'))
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        card = cleaned_data.get('card')
        amount = cleaned_data.get('amount')
        
        if card and amount:
            if not card.can_fund(amount):
                raise forms.ValidationError('Card cannot be used for this amount. Check daily/monthly limits.')
        
        return cleaned_data


class CardWithdrawalForm(forms.Form):
    """Form for withdrawing money to credit card"""
    card = forms.ModelChoiceField(
        queryset=None,
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the card to withdraw to'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01'
        }),
        help_text='Amount to withdraw from your account'
    )
    
    description = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional description'
        }),
        help_text='Optional description for this withdrawal'
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['card'].queryset = user.credit_cards.filter(status='active')
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('withdraw', 'Withdraw to Card', css_class='btn btn-warning btn-lg w-100'))
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount
    
    def clean(self):
        cleaned_data = super().clean()
        card = cleaned_data.get('card')
        amount = cleaned_data.get('amount')
        
        if card and amount:
            if not card.can_withdraw(amount):
                raise forms.ValidationError('Insufficient balance or card cannot be used for withdrawal')
        
        return cleaned_data 


class InternationalTransferForm(forms.ModelForm):
    """Form for international transfers"""
    swift_code = forms.CharField(
        max_length=11,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter SWIFT/BIC code (e.g., CHASUS33XXX)',
            'autocomplete': 'off'
        }),
        help_text='Enter the 8 or 11 character SWIFT/BIC code'
    )
    
    class Meta:
        model = InternationalTransfer
        fields = [
            'amount', 'currency', 'recipient_name', 'recipient_account_number',
            'recipient_country', 'recipient_city', 'description'
        ]
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter amount',
                'step': '0.01',
                'min': '1.00'
            }),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'recipient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recipient full name'
            }),
            'recipient_account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recipient account number'
            }),
            'recipient_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recipient country'
            }),
            'recipient_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recipient city'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Transfer description (optional)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active currencies
        self.fields['currency'].queryset = Currency.objects.filter(is_active=True)
    
    def clean_swift_code(self):
        swift_code = self.cleaned_data['swift_code'].upper().strip()
        
        # Basic format validation
        if len(swift_code) not in [8, 11]:
            raise forms.ValidationError('SWIFT code must be 8 or 11 characters long')
        
        if not swift_code.isalnum():
            raise forms.ValidationError('SWIFT code must contain only letters and numbers')
        
        # Check if bank exists in our database
        try:
            bank = Bank.objects.get(swift_code=swift_code, is_active=True)
            self.bank = bank  # Store for later use
        except Bank.DoesNotExist:
            raise forms.ValidationError('SWIFT code not found in our database. Please check the code or contact support.')
        
        return swift_code
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        
        if amount < 1.00:
            raise forms.ValidationError('Minimum transfer amount is $1.00')
        
        if amount > 10000.00:
            raise forms.ValidationError('Maximum transfer amount is $10,000.00')
        
        return amount
    
    def clean_recipient_account_number(self):
        account_number = self.cleaned_data['recipient_account_number'].strip()
        
        if len(account_number) < 5:
            raise forms.ValidationError('Account number must be at least 5 characters long')
        
        if len(account_number) > 50:
            raise forms.ValidationError('Account number is too long')
        
        return account_number
    
    def calculate_transfer_fee(self, amount, currency_code):
        """Calculate international transfer fee based on amount and currency"""
        # Static fee structure for MVP
        fee_structure = {
            'USD': {'percentage': 0.02, 'min_fee': 5.00, 'max_fee': 50.00},
            'EUR': {'percentage': 0.025, 'min_fee': 5.00, 'max_fee': 60.00},
            'GBP': {'percentage': 0.03, 'min_fee': 5.00, 'max_fee': 75.00},
            'JPY': {'percentage': 0.025, 'min_fee': 500.00, 'max_fee': 5000.00},
            'CAD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 60.00},
            'AUD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 65.00},
            'CHF': {'percentage': 0.025, 'min_fee': 5.00, 'max_fee': 55.00},
            'SGD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 65.00},
            'HKD': {'percentage': 0.025, 'min_fee': 40.00, 'max_fee': 400.00},
            'NZD': {'percentage': 0.025, 'min_fee': 7.00, 'max_fee': 70.00},
        }
        
        # Default to USD structure if currency not found
        structure = fee_structure.get(currency_code, fee_structure['USD'])
        
        # Calculate percentage fee
        percentage_fee = amount * Decimal(str(structure['percentage']))
        
        # Apply min/max limits
        fee = max(structure['min_fee'], min(percentage_fee, structure['max_fee']))
        
        return fee


class SwiftCodeSearchForm(forms.Form):
    """Form for searching SWIFT codes"""
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by bank name, country, or SWIFT code...'
        })
    )
    
    country = forms.ChoiceField(
        choices=[('', 'All Countries')] + [
            ('United States', 'United States'),
            ('United Kingdom', 'United Kingdom'),
            ('Germany', 'Germany'),
            ('France', 'France'),
            ('Canada', 'Canada'),
            ('Australia', 'Australia'),
            ('Japan', 'Japan'),
            ('Switzerland', 'Switzerland'),
            ('Singapore', 'Singapore'),
            ('Hong Kong', 'Hong Kong'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CurrencyConverterForm(forms.Form):
    """Form for currency conversion"""
    from_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='From Currency'
    )
    
    to_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='To Currency'
    )
    
    amount = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount',
            'step': '0.01',
            'min': '0.01'
        })
    )
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero')
        return amount
    
    def convert_currency(self):
        """Convert amount between currencies using static rates"""
        amount = self.cleaned_data['amount']
        from_currency = self.cleaned_data['from_currency']
        to_currency = self.cleaned_data['to_currency']
        
        # Convert to USD first, then to target currency
        amount_in_usd = amount / from_currency.exchange_rate_to_usd
        converted_amount = amount_in_usd * to_currency.exchange_rate_to_usd
        
        return {
            'original_amount': amount,
            'converted_amount': converted_amount,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'exchange_rate': to_currency.exchange_rate_to_usd / from_currency.exchange_rate_to_usd
        } 