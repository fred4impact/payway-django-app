from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import random
import string
import re
import uuid
from cryptography.fernet import Fernet
from django.conf import settings

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


class CreditCard(models.Model):
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
        ('other', 'Other'),
    ]
    
    CARD_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    # Card owner
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_cards')
    
    # Card details (encrypted)
    card_number_encrypted = models.TextField()  # Encrypted card number
    card_holder_name = models.CharField(max_length=255)
    expiry_month = models.IntegerField()
    expiry_year = models.IntegerField()
    cvv_encrypted = models.TextField()  # Encrypted CVV
    
    # Card metadata
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    card_brand = models.CharField(max_length=50)  # Visa, Mastercard, etc.
    last_four_digits = models.CharField(max_length=4)  # Last 4 digits for display
    masked_number = models.CharField(max_length=19)  # **** **** **** 1234
    
    # Card status
    status = models.CharField(max_length=20, choices=CARD_STATUS, default='active')
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Security features
    daily_limit = models.DecimalField(max_digits=15, decimal_places=2, default=1000.00)
    monthly_limit = models.DecimalField(max_digits=15, decimal_places=2, default=5000.00)
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    
    # Usage tracking
    total_funded = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    last_used = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.card_brand} ****{self.last_four_digits} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        # Generate card ID if not exists
        if not hasattr(self, 'card_id'):
            self.card_id = self.generate_card_id()
        
        # Set default card if this is the first card
        if not self.user.credit_cards.exists():
            self.is_default = True
        
        # Ensure only one default card per user
        if self.is_default:
            self.user.credit_cards.exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def generate_card_id(self):
        """Generate a unique card ID"""
        return f"CARD{str(uuid.uuid4())[:8].upper()}"
    
    def encrypt_card_data(self, card_number, cvv):
        """Encrypt sensitive card data"""
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            # Generate a key if not exists (for development)
            key = Fernet.generate_key()
            settings.ENCRYPTION_KEY = key
        
        fernet = Fernet(settings.ENCRYPTION_KEY)
        self.card_number_encrypted = fernet.encrypt(card_number.encode()).decode()
        self.cvv_encrypted = fernet.encrypt(cvv.encode()).decode()
    
    def decrypt_card_number(self):
        """Decrypt card number (use with caution)"""
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            return None
        
        fernet = Fernet(settings.ENCRYPTION_KEY)
        try:
            return fernet.decrypt(self.card_number_encrypted.encode()).decode()
        except:
            return None
    
    def decrypt_cvv(self):
        """Decrypt CVV (use with caution)"""
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            return None
        
        fernet = Fernet(settings.ENCRYPTION_KEY)
        try:
            return fernet.decrypt(self.cvv_encrypted.encode()).decode()
        except:
            return None
    
    def mask_card_number(self, card_number):
        """Mask card number for display"""
        if len(card_number) >= 4:
            return f"**** **** **** {card_number[-4:]}"
        return "**** **** **** ****"
    
    def get_last_four_digits(self, card_number):
        """Extract last 4 digits"""
        return card_number[-4:] if len(card_number) >= 4 else ""
    
    def detect_card_type(self, card_number):
        """Detect card type based on number"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if card_number.startswith('4'):
            return 'visa', 'Visa'
        elif card_number.startswith('5'):
            return 'mastercard', 'Mastercard'
        elif card_number.startswith('34') or card_number.startswith('37'):
            return 'amex', 'American Express'
        elif card_number.startswith('6'):
            return 'discover', 'Discover'
        else:
            return 'other', 'Other'
    
    def validate_card_number(self, card_number):
        """Validate card number using Luhn algorithm"""
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if not card_number.isdigit():
            return False
        
        # Luhn algorithm
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(divmod(d * 2, 10))
        
        return checksum % 10 == 0
    
    def validate_expiry_date(self, month, year):
        """Validate expiry date"""
        from django.utils import timezone
        current_date = timezone.now()
        
        if year < current_date.year:
            return False
        elif year == current_date.year and month < current_date.month:
            return False
        
        return True
    
    def validate_cvv(self, cvv):
        """Validate CVV"""
        if not cvv.isdigit():
            return False
        
        if self.card_type in ['visa', 'mastercard', 'discover']:
            return len(cvv) == 3
        elif self.card_type == 'amex':
            return len(cvv) == 4
        
        return len(cvv) in [3, 4]
    
    def is_locked(self):
        """Check if card is locked"""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def can_fund(self, amount):
        """Check if card can be used for funding"""
        if self.is_locked():
            return False
        
        if amount > self.daily_limit:
            return False
        
        # Check monthly limit
        from django.utils import timezone
        from datetime import timedelta
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = self.user.transactions.filter(
            transaction_type='card_funding',
            created_at__gte=month_start,
            status='completed'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        if monthly_usage + amount > self.monthly_limit:
            return False
        
        return True
    
    def can_withdraw(self, amount):
        """Check if card can be used for withdrawal"""
        if self.is_locked():
            return False
        
        # Check if user has sufficient balance
        user_balance = self.user.account.account_balance
        return user_balance >= amount
    
    class Meta:
        verbose_name = 'Credit Card'
        verbose_name_plural = 'Credit Cards'
        ordering = ['-created_at']
