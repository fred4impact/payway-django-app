from django.contrib import admin
from .models import Account, KYC


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'account_number', 'account_type', 'account_balance', 'is_active', 'created_at')
    list_filter = ('account_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__username', 'account_number')
    readonly_fields = ('account_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'verification_status', 'document_verified', 'face_verified', 'submitted_at')
    list_filter = ('verification_status', 'document_verified', 'face_verified', 'submitted_at')
    search_fields = ('user__email', 'user__username', 'full_name')
    readonly_fields = ('submitted_at', 'verified_at', 'updated_at')
    ordering = ('-submitted_at',)
    
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
            'fields': ('verification_status', 'document_verified', 'face_verified', 'verification_confidence', 'ai_verification_status')
        }),
        ('AI Analysis', {
            'fields': ('risk_score', 'ai_flagged')
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'verified_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
