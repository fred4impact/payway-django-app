from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
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


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('transfer', 'Transfer'),
        ('payment_request', 'Payment Request'),
        ('card_funding', 'Card Funding'),
        ('withdrawal', 'Withdrawal'),
        ('deposit', 'Deposit'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Transaction details
    transaction_id = models.CharField(max_length=20, unique=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='transfer')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Sender and receiver
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    sender_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transactions')
    
    # Transaction status and metadata
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    
    # Fees and charges
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Security and verification
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.sender.email} to {self.receiver.email}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        if not self.total_amount:
            self.total_amount = self.amount + Decimal(str(self.transaction_fee))
        super().save(*args, **kwargs)

    def generate_transaction_id(self):
        """Generate a unique transaction ID"""
        import uuid
        return f"TXN{str(uuid.uuid4())[:8].upper()}"

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']


class PaymentRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Request details
    request_id = models.CharField(max_length=20, unique=True, blank=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    description = models.TextField(blank=True)
    
    # Sender and receiver
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    requester_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sent_requests')
    recipient_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_requests')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=REQUEST_STATUS, default='pending')
    reference = models.CharField(max_length=100, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField(blank=True, null=True)
    is_expired = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.request_id} - {self.requester.email} to {self.recipient.email}"

    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = self.generate_request_id()
        super().save(*args, **kwargs)

    def generate_request_id(self):
        """Generate a unique request ID"""
        import uuid
        return f"REQ{str(uuid.uuid4())[:8].upper()}"

    def check_expiration(self):
        """Check if the request has expired and update status"""
        from django.utils import timezone
        if self.expires_at and timezone.now() > self.expires_at:
            self.is_expired = True
            if self.status == 'pending':
                self.status = 'expired'
            self.save(update_fields=['is_expired', 'status'])
        return self.is_expired

    def is_expired_property(self):
        """Property to check if request is expired"""
        from django.utils import timezone
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    class Meta:
        verbose_name = 'Payment Request'
        verbose_name_plural = 'Payment Requests'
        ordering = ['-created_at']


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('transaction', 'Transaction'),
        ('payment_request', 'Payment Request'),
        ('kyc', 'KYC'),
        ('security', 'Security'),
        ('system', 'System'),
    ]
    
    NOTIFICATION_STATUS = [
        ('unread', 'Unread'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    ]
    
    # Notification details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=NOTIFICATION_STATUS, default='unread')
    is_email_sent = models.BooleanField(default=False)
    is_sms_sent = models.BooleanField(default=False)
    
    # Related objects
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, blank=True, null=True)
    payment_request = models.ForeignKey(PaymentRequest, on_delete=models.CASCADE, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.title}"

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']


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
