from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_location = models.CharField(max_length=100, blank=True)
    security_level = models.CharField(
        max_length=20,
        choices=[
            ('basic', 'Basic'),
            ('enhanced', 'Enhanced'),
            ('maximum', 'Maximum'),
        ],
        default='basic'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.account_locked_until and self.account_locked_until > timezone.now():
            return True
        return False

    def increment_failed_login(self):
        """Increment failed login attempts and lock account if necessary"""
        self.failed_login_attempts += 1
        
        # Progressive lockout: 3, 5, 10 attempts
        if self.failed_login_attempts >= 10:
            self.account_locked_until = timezone.now() + timedelta(hours=24)
        elif self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(hours=2)
        elif self.failed_login_attempts >= 3:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save()

    def reset_failed_login(self):
        """Reset failed login attempts after successful login"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()

    def can_enable_2fa(self):
        """Check if user can enable 2FA (basic requirements)"""
        return bool(self.phone_number or self.email)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')


class SecurityLog(models.Model):
    """Track all security-related activities"""
    EVENT_TYPES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('password_change', 'Password Change'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('2fa_used', '2FA Used'),
        ('2fa_failed', '2FA Failed'),
        ('2fa_required', '2FA Required'),
        ('2fa_backup_used', '2FA Backup Used'),
        ('2fa_backup_failed', '2FA Backup Failed'),
        ('2fa_setup', '2FA Setup'),
        ('2fa_backup_codes_regenerated', '2FA Backup Codes Regenerated'),
        ('account_created', 'Account Created'),
        ('registration_failed', 'Registration Failed'),
        ('login_blocked', 'Login Blocked'),
        ('login_validation_failed', 'Login Validation Failed'),
        ('account_locked', 'Account Locked'),
        ('account_unlocked', 'Account Unlocked'),
        ('device_added', 'Device Added'),
        ('device_removed', 'Device Removed'),
        ('device_trusted', 'Device Trusted'),
        ('device_untrusted', 'Device Untrusted'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('security_settings_changed', 'Security Settings Changed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    risk_score = models.IntegerField(default=0, help_text="Risk score from 0-100")
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'event_type', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.user or 'Unknown'} - {self.timestamp}"


class UserDevice(models.Model):
    """Track user devices and sessions"""
    DEVICE_TYPES = [
        ('desktop', 'Desktop'),
        ('mobile', 'Mobile'),
        ('tablet', 'Tablet'),
        ('unknown', 'Unknown'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, unique=True)
    device_name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, default='unknown')
    browser = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    is_trusted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    first_used = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True)
    user_agent = models.TextField()
    
    class Meta:
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_id']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.device_name} - {self.user.email}"


class TwoFactorAuth(models.Model):
    """Two-factor authentication settings for users"""
    AUTH_METHODS = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('totp', 'TOTP (Google Authenticator)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=AUTH_METHODS)
    is_enabled = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=255, blank=True, help_text="TOTP secret key")
    phone_number = models.CharField(max_length=15, blank=True, help_text="Phone for SMS 2FA")
    backup_codes = models.JSONField(default=list, help_text="List of backup recovery codes")
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Two-Factor Authentication'
        verbose_name_plural = 'Two-Factor Authentication'

    def __str__(self):
        return f"2FA - {self.user.email} - {self.method}"

    def generate_backup_codes(self, count=10):
        """Generate new backup codes"""
        import secrets
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()[:8]
            codes.append(code)
        self.backup_codes = codes
        self.save()
        return codes

    def verify_backup_code(self, code):
        """Verify and consume a backup code"""
        if code in self.backup_codes:
            self.backup_codes.remove(code)
            self.save()
            return True
        return False


class AccountLockout(models.Model):
    """Track account lockouts and their reasons"""
    LOCKOUT_TYPES = [
        ('failed_login', 'Failed Login Attempts'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('admin_action', 'Admin Action'),
        ('security_policy', 'Security Policy Violation'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lockout_type = models.CharField(max_length=30, choices=LOCKOUT_TYPES)
    reason = models.TextField()
    locked_at = models.DateTimeField(auto_now_add=True)
    locked_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    unlocked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='unlocked_accounts'
    )
    unlocked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['locked_until']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.lockout_type} - {self.locked_at}"

    def is_expired(self):
        """Check if lockout has expired"""
        return timezone.now() > self.locked_until

    def unlock(self, unlocked_by_user=None):
        """Unlock the account"""
        self.is_active = False
        self.unlocked_by = unlocked_by_user
        self.unlocked_at = timezone.now()
        self.save()
