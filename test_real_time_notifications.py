import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from account.models import Notification

User = get_user_model()

# Enable database access for all tests in this file
pytestmark = pytest.mark.django_db

@pytest.fixture
def sample_users():
    User = get_user_model()

    john = User.objects.create_user(
        username="john",
        email="john@example.com",
        password="testpass123"
    )

    sarah = User.objects.create_user(
        username="sarah",
        email="sarah@example.com",
        password="testpass123"
    )

    mike = User.objects.create_user(
        username="mike",
        email="mike@example.com",
        password="testpass123"
    )

    return john, sarah, mike
def test_notification_creation(sample_users):
    john, sarah, mike = sample_users

def test_notification_creation():
    """Test creating different types of notifications"""

    # Get test users
    john = User.objects.filter(email="john@example.com").first()
    sarah = User.objects.filter(email="sarah@example.com").first()
    mike = User.objects.filter(email="mike@example.com").first()

    assert john is not None, "john@example.com should exist"
    assert sarah is not None, "sarah@example.com should exist"
    assert mike is not None, "mike@example.com should exist"

    # Clear existing notifications for clean test
    Notification.objects.all().delete()

    # Create transaction notification
    transaction_notification = Notification.objects.create(
        user=sarah,
        notification_type="transaction",
        title="Money Received",
        message=f"You received $50.00 from {john.get_full_name()}",
        status="unread",
    )

    # Create payment request notification
    payment_request_notification = Notification.objects.create(
        user=mike,
        notification_type="payment_request",
        title="Payment Request",
        message=f"{sarah.get_full_name()} requested $25.00 from you",
        status="unread",
    )

    # Create KYC notification
    kyc_notification = Notification.objects.create(
        user=john,
        notification_type="kyc",
        title="KYC Status Updated",
        message="Your KYC verification has been approved",
        status="unread",
    )

    # Create security notification
    security_notification = Notification.objects.create(
        user=sarah,
        notification_type="security",
        title="Security Alert",
        message="New login detected from a new device",
        status="unread",
    )

    # Create system notification
    system_notification = Notification.objects.create(
        user=mike,
        notification_type="system",
        title="System Maintenance",
        message="Scheduled maintenance will occur tonight at 2 AM",
        status="unread",
    )

    # Assertions
    assert transaction_notification is not None
    assert payment_request_notification is not None
    assert kyc_notification is not None
    assert security_notification is not None
    assert system_notification is not None

    assert Notification.objects.count() == 5

    # Verify unread counts
    assert Notification.objects.filter(
        user=sarah,
        status="unread"
    ).count() == 2

    assert Notification.objects.filter(
        user=mike,
        status="unread"
    ).count() == 2

    assert Notification.objects.filter(
        user=john,
        status="unread"
    ).count() == 1


def test_notification_mark_read():
    """Test marking notifications as read"""

    user = User.objects.filter(email="john@example.com").first()
    assert user is not None, "john@example.com should exist"

    # Create unread notification
    notification = Notification.objects.create(
        user=user,
        notification_type="system",
        title="Test Notification",
        message="This is a test notification",
        status="unread",
    )

    unread_before = Notification.objects.filter(
        user=user,
        status="unread"
    ).count()

    assert unread_before >= 1

    # Mark as read
    notification.status = "read"
    notification.read_at = timezone.now()
    notification.save()

    unread_after = Notification.objects.filter(
        user=user,
        status="unread"
    ).count()

    updated_notification = Notification.objects.get(id=notification.id)

    assert unread_after == unread_before - 1
    assert updated_notification.status == "read"
    assert updated_notification.read_at is not None