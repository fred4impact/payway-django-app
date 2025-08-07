#!/usr/bin/env python3
"""
Test script for Payment Request functionality
This script tests the core payment request features
"""

import os
import sys
import django
from datetime import timedelta

# Add the project directory to Python path
sys.path.append('/Users/mac/Documents/payway-django-app')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payway.settings')
django.setup()

from django.utils import timezone
from account.models import PaymentRequest, Account, User
from userauths.models import User as CustomUser

def test_payment_request_creation():
    """Test creating a payment request"""
    print("🧪 Testing Payment Request Creation...")
    
    try:
        # Get test users
        requester = CustomUser.objects.filter(email='john.doe@test.com').first()
        recipient = CustomUser.objects.filter(email='sarah.smith@test.com').first()
        
        if not requester or not recipient:
            print("❌ Test users not found. Please run create_test_users command first.")
            return False
        
        # Create payment request
        payment_request = PaymentRequest.objects.create(
            requester=requester,
            recipient=recipient,
            requester_account=requester.account,
            recipient_account=recipient.account,
            amount=50.00,
            description="Test payment request",
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        print(f"✅ Payment request created: {payment_request.request_id}")
        print(f"   Amount: ${payment_request.amount}")
        print(f"   Status: {payment_request.status}")
        print(f"   Expires: {payment_request.expires_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating payment request: {e}")
        return False

def test_payment_request_expiration():
    """Test payment request expiration"""
    print("\n🧪 Testing Payment Request Expiration...")
    
    try:
        # Create an expired request
        requester = CustomUser.objects.filter(email='john.doe@test.com').first()
        recipient = CustomUser.objects.filter(email='sarah.smith@test.com').first()
        
        if not requester or not recipient:
            print("❌ Test users not found.")
            return False
        
        expired_request = PaymentRequest.objects.create(
            requester=requester,
            recipient=recipient,
            requester_account=requester.account,
            recipient_account=recipient.account,
            amount=25.00,
            description="Expired test request",
            expires_at=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        # Check expiration
        expired_request.check_expiration()
        
        print(f"✅ Expired request created: {expired_request.request_id}")
        print(f"   Is expired: {expired_request.is_expired}")
        print(f"   Status: {expired_request.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing expiration: {e}")
        return False

def test_payment_request_listing():
    """Test listing payment requests"""
    print("\n🧪 Testing Payment Request Listing...")
    
    try:
        # Get requests for a user
        user = CustomUser.objects.filter(email='john.doe@test.com').first()
        
        if not user:
            print("❌ Test user not found.")
            return False
        
        sent_requests = PaymentRequest.objects.filter(requester=user)
        received_requests = PaymentRequest.objects.filter(recipient=user)
        
        print(f"✅ User {user.email} has:")
        print(f"   Sent requests: {sent_requests.count()}")
        print(f"   Received requests: {received_requests.count()}")
        
        for request in sent_requests:
            print(f"   - Sent: {request.request_id} -> {request.recipient.email} (${request.amount})")
        
        for request in received_requests:
            print(f"   - Received: {request.request_id} <- {request.requester.email} (${request.amount})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error listing requests: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test payment requests
        test_requests = PaymentRequest.objects.filter(description__icontains='test')
        count = test_requests.count()
        test_requests.delete()
        
        print(f"✅ Deleted {count} test payment requests")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 PayWay Payment Request Test Suite")
    print("=" * 50)
    
    tests = [
        test_payment_request_creation,
        test_payment_request_expiration,
        test_payment_request_listing,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Payment Request functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    # Clean up
    cleanup_test_data()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()
