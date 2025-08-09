from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SecurityLog, UserDevice, TwoFactorAuth, AccountLockout


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'security_level', 'failed_login_attempts', 'is_account_locked', 'date_joined')
    list_filter = ('is_verified', 'security_level', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Add security fields to fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('Security Information', {
            'fields': ('phone_number', 'date_of_birth', 'profile_picture', 'is_verified', 'security_level')
        }),
        ('Account Security', {
            'fields': ('failed_login_attempts', 'account_locked_until', 'last_login_ip', 'last_login_location'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('failed_login_attempts', 'account_locked_until', 'last_login_ip', 'last_login_location', 'date_joined', 'last_login')
    
    actions = ['unlock_accounts', 'reset_failed_logins', 'upgrade_security_level']
    
    def is_account_locked(self, obj):
        return obj.is_account_locked()
    is_account_locked.boolean = True
    is_account_locked.short_description = 'Account Locked'
    
    def unlock_accounts(self, request, queryset):
        """Unlock selected accounts"""
        unlocked_count = 0
        failed_unlocks = 0
        
        for user in queryset:
            if user.is_account_locked():
                try:
                    user.reset_failed_login()
                    unlocked_count += 1
                except Exception as e:
                    failed_unlocks += 1
                    # Log the error for debugging
                    print(f"Failed to unlock account for user {user.email}: {e}")
                    continue
        
        if failed_unlocks > 0:
            self.message_user(request, f'Successfully unlocked {unlocked_count} accounts. Failed to unlock {failed_unlocks} accounts due to errors.')
        else:
            self.message_user(request, f'Successfully unlocked {unlocked_count} accounts.')
    unlock_accounts.short_description = 'Unlock selected accounts'
    
    def reset_failed_logins(self, request, queryset):
        """Reset failed login attempts for selected users"""
        updated_count = queryset.update(failed_login_attempts=0, account_locked_until=None)
        self.message_user(request, f'Reset failed login attempts for {updated_count} users.')
    reset_failed_logins.short_description = 'Reset failed login attempts'
    
    def upgrade_security_level(self, request, queryset):
        """Upgrade security level for selected users"""
        updated_count = queryset.update(security_level='enhanced')
        self.message_user(request, f'Upgraded security level for {updated_count} users.')
    upgrade_security_level.short_description = 'Upgrade to enhanced security'


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'user', 'ip_address', 'location', 'risk_score', 'timestamp')
    list_filter = ('event_type', 'risk_score', 'timestamp', 'location')
    search_fields = ('user__email', 'user__username', 'ip_address', 'event_type')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'user', 'timestamp')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'location', 'risk_score')
        }),
        ('Additional Information', {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Security logs should only be created by the system"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Security logs should not be editable"""
        return False


@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'user', 'device_type', 'browser', 'operating_system', 'is_trusted', 'is_active', 'last_used')
    list_filter = ('device_type', 'is_trusted', 'is_active', 'browser', 'operating_system')
    search_fields = ('user__email', 'device_name', 'device_id', 'ip_address')
    ordering = ('-last_used',)
    readonly_fields = ('device_id', 'first_used', 'last_used')
    
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'device_id', 'device_name', 'device_type')
        }),
        ('Technical Details', {
            'fields': ('browser', 'operating_system', 'user_agent')
        }),
        ('Security Settings', {
            'fields': ('is_trusted', 'is_active')
        }),
        ('Location & Usage', {
            'fields': ('ip_address', 'location', 'first_used', 'last_used')
        }),
    )
    
    actions = ['trust_devices', 'untrust_devices', 'deactivate_devices']
    
    def trust_devices(self, request, queryset):
        """Mark selected devices as trusted"""
        updated_count = queryset.update(is_trusted=True)
        self.message_user(request, f'Marked {updated_count} devices as trusted.')
    trust_devices.short_description = 'Mark devices as trusted'
    
    def untrust_devices(self, request, queryset):
        """Mark selected devices as untrusted"""
        updated_count = queryset.update(is_trusted=False)
        self.message_user(request, f'Marked {updated_count} devices as untrusted.')
    untrust_devices.short_description = 'Mark devices as untrusted'
    
    def deactivate_devices(self, request, queryset):
        """Deactivate selected devices"""
        updated_count = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated_count} devices.')
    deactivate_devices.short_description = 'Deactivate devices'


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'is_enabled', 'created_at', 'last_used')
    list_filter = ('method', 'is_enabled', 'created_at')
    search_fields = ('user__email', 'user__username', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'method')
        }),
        ('2FA Settings', {
            'fields': ('is_enabled', 'secret_key', 'phone_number')
        }),
        ('Backup Codes', {
            'fields': ('backup_codes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['enable_2fa', 'disable_2fa', 'regenerate_backup_codes']
    
    def enable_2fa(self, request, queryset):
        """Enable 2FA for selected users"""
        updated_count = queryset.update(is_enabled=True)
        self.message_user(request, f'Enabled 2FA for {updated_count} users.')
    enable_2fa.short_description = 'Enable 2FA'
    
    def disable_2fa(self, request, queryset):
        """Disable 2FA for selected users"""
        updated_count = queryset.update(is_enabled=False)
        self.message_user(request, f'Disabled 2FA for {updated_count} users.')
    disable_2fa.short_description = 'Disable 2FA'
    
    def regenerate_backup_codes(self, request, queryset):
        """Regenerate backup codes for selected users"""
        for twofa in queryset:
            twofa.generate_backup_codes()
        self.message_user(request, f'Regenerated backup codes for {queryset.count()} users.')
    regenerate_backup_codes.short_description = 'Regenerate backup codes'


@admin.register(AccountLockout)
class AccountLockoutAdmin(admin.ModelAdmin):
    list_display = ('user', 'lockout_type', 'is_active', 'locked_at', 'locked_until', 'ip_address')
    list_filter = ('lockout_type', 'is_active', 'locked_at')
    search_fields = ('user__email', 'user__username', 'ip_address', 'reason')
    ordering = ('-locked_at',)
    readonly_fields = ('locked_at', 'locked_until')
    
    fieldsets = (
        ('Lockout Information', {
            'fields': ('user', 'lockout_type', 'reason')
        }),
        ('Timing', {
            'fields': ('locked_at', 'locked_until', 'is_active')
        }),
        ('Technical Details', {
            'fields': ('ip_address',)
        }),
        ('Resolution', {
            'fields': ('unlocked_by', 'unlocked_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['unlock_accounts', 'extend_lockouts']
    
    def unlock_accounts(self, request, queryset):
        """Unlock selected accounts"""
        unlocked_count = 0
        for lockout in queryset:
            if lockout.is_active:
                lockout.unlock(request.user)
                unlocked_count += 1
        
        self.message_user(request, f'Successfully unlocked {unlocked_count} accounts.')
    unlock_accounts.short_description = 'Unlock selected accounts'
    
    def extend_lockouts(self, request, queryset):
        """Extend lockout duration for selected accounts"""
        from django.utils import timezone
        from datetime import timedelta
        
        extended_count = 0
        for lockout in queryset:
            if lockout.is_active:
                lockout.locked_until = timezone.now() + timedelta(hours=24)
                lockout.save()
                extended_count += 1
        
        self.message_user(request, f'Extended lockout duration for {extended_count} accounts.')
    extend_lockouts.short_description = 'Extend lockout duration'
