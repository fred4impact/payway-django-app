from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, TwoFactorAuth, SecurityLog
import pyotp
import qrcode
import base64
from io import BytesIO


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone number (optional)'
        })
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password1', 'password2', 'phone_number', 'date_of_birth']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Ensure first_name and last_name are set
        if 'first_name' in self.cleaned_data:
            user.first_name = self.cleaned_data['first_name']
        if 'last_name' in self.cleaned_data:
            user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        
        return user


class UserLoginForm(AuthenticationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email


class TwoFactorSetupForm(forms.ModelForm):
    """Form for setting up Two-Factor Authentication"""
    method = forms.ChoiceField(
        choices=TwoFactorAuth.AUTH_METHODS,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input'
        })
    )
    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number for SMS 2FA'
        })
    )
    confirm_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm phone number'
        })
    )
    
    class Meta:
        model = TwoFactorAuth
        fields = ['method', 'phone_number']
    
    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        phone_number = cleaned_data.get('phone_number')
        confirm_phone = cleaned_data.get('confirm_phone')
        
        if method == 'sms' and not phone_number:
            raise forms.ValidationError('Phone number is required for SMS 2FA.')
        
        if method == 'sms' and phone_number != confirm_phone:
            raise forms.ValidationError('Phone numbers do not match.')
        
        return cleaned_data


class TwoFactorVerifyForm(forms.Form):
    """Form for verifying Two-Factor Authentication codes"""
    code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Enter 6-digit code',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.strip().replace(' ', '')
            if not code.isdigit():
                raise forms.ValidationError('Code must contain only numbers.')
            if len(code) != 6:
                raise forms.ValidationError('Code must be exactly 6 digits.')
        return code


class TwoFactorBackupCodeForm(forms.Form):
    """Form for entering backup codes"""
    backup_code = forms.CharField(
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': 'Enter backup code',
            'autocomplete': 'off',
            'style': 'text-transform: uppercase;'
        })
    )
    
    def clean_backup_code(self):
        code = self.cleaned_data.get('backup_code')
        if code:
            code = code.strip().upper()
            if not code.isalnum():
                raise forms.ValidationError('Backup code must contain only letters and numbers.')
            if len(code) != 8:
                raise forms.ValidationError('Backup code must be exactly 8 characters.')
        return code


class TwoFactorDisableForm(forms.Form):
    """Form for disabling Two-Factor Authentication"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password to confirm'
        })
    )
    confirm_disable = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Incorrect password.')
        return password


class SecuritySettingsForm(forms.ModelForm):
    """Form for updating security settings"""
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password to make changes'
        })
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password (leave blank to keep current)'
        })
    )
    confirm_new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    security_level = forms.ChoiceField(
        choices=User._meta.get_field('security_level').choices,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ['security_level']
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')
        
        # If changing password, require current password
        if new_password and not current_password:
            raise forms.ValidationError('Current password is required to change password.')
        
        # If changing password, require confirmation
        if new_password and new_password != confirm_new_password:
            raise forms.ValidationError('New passwords do not match.')
        
        return cleaned_data


class DeviceTrustForm(forms.Form):
    """Form for trusting/untrusting devices"""
    device_id = forms.CharField(widget=forms.HiddenInput())
    action = forms.CharField(widget=forms.HiddenInput())
    
    def clean_action(self):
        action = self.cleaned_data.get('action')
        if action not in ['trust', 'untrust', 'remove']:
            raise forms.ValidationError('Invalid action specified.')
        return action


class SecurityLogFilterForm(forms.Form):
    """Form for filtering security logs"""
    event_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Events')] + SecurityLog.EVENT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    risk_level = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Levels'),
            ('low', 'Low (0-29)'),
            ('medium', 'Medium (30-69)'),
            ('high', 'High (70-100)')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    ip_address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by IP address'
        })
    )


# Utility functions for 2FA
def generate_totp_secret():
    """Generate a new TOTP secret key"""
    return pyotp.random_base32()


def generate_totp_qr_code(secret, user_email, issuer_name="PayWay"):
    """Generate QR code for TOTP setup"""
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user_email,
        issuer_name=issuer_name
    )
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str, provisioning_uri


def verify_totp_code(secret, code):
    """Verify a TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count=10):
    """Generate backup recovery codes"""
    import secrets
    codes = []
    for _ in range(count):
        code = secrets.token_hex(4).upper()[:8]
        codes.append(code)
    return codes 