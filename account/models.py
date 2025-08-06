from django.db import models
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()


def generate_account_number():
    """Generate a unique 10-digit account number"""
    while True:
        account_number = ''.join(random.choices(string.digits, k=10))
        if not Account.objects.filter(account_number=account_number).exists():
            return account_number


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('checking', 'Checking'),
        ('business', 'Business'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    account_number = models.CharField(max_length=10, unique=True, default=generate_account_number)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.account_number}"

    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'


class KYC(models.Model):
    VERIFICATION_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Document uploads
    id_document = models.ImageField(upload_to='kyc_documents/')
    proof_of_address = models.ImageField(upload_to='kyc_documents/')
    selfie_photo = models.ImageField(upload_to='kyc_documents/')
    
    # Verification fields
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    document_verified = models.BooleanField(default=False)
    face_verified = models.BooleanField(default=False)
    verification_confidence = models.FloatField(default=0.0)
    ai_verification_status = models.CharField(max_length=20, default='pending')
    
    # Additional fields for AI integration
    risk_score = models.FloatField(default=0.0)
    ai_flagged = models.BooleanField(default=False)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"KYC - {self.user.email}"

    class Meta:
        verbose_name = 'KYC'
        verbose_name_plural = 'KYC Documents'
