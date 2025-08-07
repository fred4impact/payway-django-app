#!/usr/bin/env python3
"""
Test script for Real-time Notifications feature
"""

import os
import sys
import django
import time
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/Users/mac/Documents/payway-django-app')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payway.settings')
django.setup()

from django.contrib.auth import get_user_model
from account.models import Notification, Account
from django.utils import timezone

User = get_user_model()

def test_notification_creation():
    """Test creating different types of notifications"""
    print("🔔 Testing Real-time Notification System")
    print("=" * 50)
    
    # Get test users
    try:
        john = User.objects.get(email='john@example.com')
        sarah = User.objects.get(email='sarah@example.com')
        mike = User.objects.get(email='mike@example.com')
    except User.DoesNotExist:
        print("❌ Test users not found. Please run create_test_users command first.")
        return
    
    print(f"✅ Found test users: {john.email}, {sarah.email}, {mike.email}")
    
    # Clear existing notifications for clean test
    Notification.objects.all().delete()
    print("🧹 Cleared existing notifications")
    
    # Test 1: Transaction Notification
    print("\n📊 Test 1: Creating Transaction Notification")
    transaction_notification = Notification.objects.create(
        user=sarah,
        notification_type='transaction',
        title='Money Received',
        message=f'You received $50.00 from {john.get_full_name()}',
        status='unread'
    )
    print(f"✅ Created transaction notification for {sarah.email}")
    
    # Test 2: Payment Request Notification
    print("\n📊 Test 2: Creating Payment Request Notification")
    payment_request_notification = Notification.objects.create(
        user=mike,
        notification_type='payment_request',
        title='Payment Request',
        message=f'{sarah.get_full_name()} requested $25.00 from you',
        status='unread'
    )
    print(f"✅ Created payment request notification for {mike.email}")
    
    # Test 3: KYC Notification
    print("\n📊 Test 3: Creating KYC Notification")
    kyc_notification = Notification.objects.create(
        user=john,
        notification_type='kyc',
        title='KYC Status Updated',
        message='Your KYC verification has been approved',
        status='unread'
    )
    print(f"✅ Created KYC notification for {john.email}")
    
    # Test 4: Security Notification
    print("\n📊 Test 4: Creating Security Notification")
    security_notification = Notification.objects.create(
        user=sarah,
        notification_type='security',
        title='Security Alert',
        message='New login detected from a new device',
        status='unread'
    )
    print(f"✅ Created security notification for {sarah.email}")
    
    # Test 5: System Notification
    print("\n📊 Test 5: Creating System Notification")
    system_notification = Notification.objects.create(
        user=mike,
        notification_type='system',
        title='System Maintenance',
        message='Scheduled maintenance will occur tonight at 2 AM',
        status='unread'
    )
    print(f"✅ Created system notification for {mike.email}")
    
    # Display notification counts
    print("\n📈 Notification Summary:")
    print("-" * 30)
    for user in [john, sarah, mike]:
        unread_count = Notification.objects.filter(user=user, status='unread').count()
        total_count = Notification.objects.filter(user=user).count()
        print(f"{user.email}: {unread_count} unread, {total_count} total")
    
    # Test notification types distribution
    print("\n📊 Notification Types Distribution:")
    print("-" * 35)
    for notification_type in ['transaction', 'payment_request', 'kyc', 'security', 'system']:
        count = Notification.objects.filter(notification_type=notification_type).count()
        print(f"{notification_type}: {count}")
    
    print("\n🎉 Real-time Notification System Test Complete!")
    print("\n💡 To test real-time updates:")
    print("1. Open the PayWay application in your browser")
    print("2. Log in as any test user")
    print("3. Check the notification bell in the navigation")
    print("4. The notification count should update automatically")
    print("5. New notifications should appear as toast messages")

def test_notification_mark_read():
    """Test marking notifications as read"""
    print("\n🔔 Testing Mark as Read Functionality")
    print("=" * 40)
    
    # Get a user with unread notifications
    user_with_notifications = Notification.objects.filter(status='unread').first()
    if not user_with_notifications:
        print("❌ No unread notifications found")
        return
    
    user = user_with_notifications.user
    unread_before = Notification.objects.filter(user=user, status='unread').count()
    
    print(f"📊 {user.email} has {unread_before} unread notifications")
    
    # Mark first notification as read
    first_notification = Notification.objects.filter(user=user, status='unread').first()
    if first_notification:
        first_notification.status = 'read'
        first_notification.read_at = timezone.now()
        first_notification.save()
        print(f"✅ Marked notification '{first_notification.title}' as read")
    
    unread_after = Notification.objects.filter(user=user, status='unread').count()
    print(f"📊 {user.email} now has {unread_after} unread notifications")
    
    if unread_after < unread_before:
        print("✅ Mark as read functionality working correctly")
    else:
        print("❌ Mark as read functionality failed")

def cleanup_test_notifications():
    """Clean up test notifications"""
    print("\n🧹 Cleaning up test notifications...")
    count = Notification.objects.count()
    Notification.objects.all().delete()
    print(f"✅ Deleted {count} test notifications")

if __name__ == "__main__":
    try:
        test_notification_creation()
        test_notification_mark_read()
        
        # Ask if user wants to clean up
        response = input("\n🧹 Do you want to clean up test notifications? (y/n): ")
        if response.lower() in ['y', 'yes']:
            cleanup_test_notifications()
        else:
            print("📝 Test notifications preserved for manual testing")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
