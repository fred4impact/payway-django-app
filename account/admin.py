from django.contrib import admin
from .models import Account, KYC, Transaction, PaymentRequest, Notification


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['account_number', 'user', 'account_type', 'account_balance', 'is_active', 'created_at']
    list_filter = ['account_type', 'is_active', 'created_at']
    search_fields = ['account_number', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['account_number', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'account_number', 'account_type', 'account_balance', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'verification_status', 'document_verified', 'face_verified', 'submitted_at']
    list_filter = ['verification_status', 'document_verified', 'face_verified', 'ai_verification_status', 'submitted_at']
    search_fields = ['user__email', 'full_name', 'nationality', 'city', 'country']
    readonly_fields = ['submitted_at', 'verified_at', 'updated_at']
    ordering = ['-submitted_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name', 'date_of_birth', 'nationality')
        }),
        ('Address Information', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Documents', {
            'fields': ('id_document', 'proof_of_address', 'selfie_photo')
        }),
        ('Verification Status', {
            'fields': ('verification_status', 'document_verified', 'face_verified', 'verification_confidence')
        }),
        ('AI Integration', {
            'fields': ('ai_verification_status', 'risk_score', 'ai_flagged'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'verified_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'transaction_type', 'amount', 'currency', 'sender', 'receiver', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'currency', 'created_at']
    search_fields = ['transaction_id', 'sender__email', 'receiver__email', 'description', 'reference']
    readonly_fields = ['transaction_id', 'created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_id', 'transaction_type', 'amount', 'currency', 'description', 'reference')
        }),
        ('Users', {
            'fields': ('sender', 'receiver', 'sender_account', 'receiver_account')
        }),
        ('Status & Fees', {
            'fields': ('status', 'transaction_fee', 'total_amount')
        }),
        ('Security', {
            'fields': ('is_verified', 'verification_code'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'amount', 'currency', 'requester', 'recipient', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['request_id', 'requester__email', 'recipient__email', 'description']
    readonly_fields = ['request_id', 'created_at', 'updated_at', 'paid_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': ('request_id', 'amount', 'currency', 'description', 'reference')
        }),
        ('Users', {
            'fields': ('requester', 'recipient', 'requester_account', 'recipient_account')
        }),
        ('Status & Expiration', {
            'fields': ('status', 'expires_at', 'is_expired')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'status', 'created_at']
    list_filter = ['notification_type', 'status', 'is_email_sent', 'is_sms_sent', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'title', 'message')
        }),
        ('Status', {
            'fields': ('status', 'is_email_sent', 'is_sms_sent')
        }),
        ('Related Objects', {
            'fields': ('transaction', 'payment_request'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
