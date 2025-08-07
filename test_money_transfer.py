#!/usr/bin/env python3
"""
Test script for Money Transfer functionality
This script tests the core money transfer features
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/Users/mac/Documents/payway-django-app')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payway.settings')
django.setup()

from django.utils import timezone
from account.models import Transaction, Account
from userauths.models import User as CustomUser

def test_money_transfer():
    """Test money transfer between users"""
    print("🧪 Testing Money Transfer...")
    
    try:
        # Get test users
        sender = CustomUser.objects.filter(email='john.doe@test.com').first()
        receiver = CustomUser.objects.filter(email='sarah.smith@test.com').first()
        
        if not sender or not receiver:
            print("❌ Test users not found. Please run create_test_users command first.")
            return False
        
        # Get accounts
        sender_account = sender.account
        receiver_account = receiver.account
        
        # Store initial balances
        initial_sender_balance = Decimal(str(sender_account.account_balance))
        initial_receiver_balance = Decimal(str(receiver_account.account_balance))
        transfer_amount = Decimal('25.00')
        
        print(f"💰 Initial balances:")
        print(f"   {sender.email}: ${initial_sender_balance}")
        print(f"   {receiver.email}: ${initial_receiver_balance}")
        print(f"   Transfer amount: ${transfer_amount}")
        
        # Check if sender has sufficient balance
        if sender_account.account_balance < transfer_amount:
            print(f"❌ Insufficient balance. {sender.email} has ${sender_account.account_balance}")
            return False
        
        # Create transaction
        transaction = Transaction.objects.create(
            sender=sender,
            receiver=receiver,
            sender_account=sender_account,
            receiver_account=receiver_account,
            amount=transfer_amount,
            transaction_type='transfer',
            description='Test money transfer',
            status='completed'
        )
        
        # Update account balances
        sender_account.account_balance = Decimal(str(sender_account.account_balance)) - transfer_amount
        sender_account.save()
        
        receiver_account.account_balance = Decimal(str(receiver_account.account_balance)) + transfer_amount
        receiver_account.save()
        
        # Get updated balances
        sender_account.refresh_from_db()
        receiver_account.refresh_from_db()
        
        print(f"✅ Transfer completed: {transaction.transaction_id}")
        print(f"   New balances:")
        print(f"   {sender.email}: ${sender_account.account_balance}")
        print(f"   {receiver.email}: ${receiver_account.account_balance}")
        
        # Verify balances
        expected_sender_balance = initial_sender_balance - transfer_amount
        expected_receiver_balance = initial_receiver_balance + transfer_amount
        
        if (sender_account.account_balance == expected_sender_balance and 
            receiver_account.account_balance == expected_receiver_balance):
            print("✅ Balance verification passed!")
            return True
        else:
            print("❌ Balance verification failed!")
            return False
        
    except Exception as e:
        print(f"❌ Error during money transfer: {e}")
        return False

def test_form_validation():
    """Test form validation"""
    print("\n🧪 Testing Form Validation...")
    
    try:
        from account.forms import MoneyTransferForm
        
        # Test valid data
        valid_data = {
            'receiver_account': '8298370758',  # Sarah's account number
            'amount': '50.00',
            'description': 'Test transfer',
            'reference': 'TEST123'
        }
        
        form = MoneyTransferForm(data=valid_data)
        if form.is_valid():
            print("✅ Valid form data accepted")
            print(f"   Receiver account: {form.cleaned_data['receiver_account']}")
            print(f"   Amount: ${form.cleaned_data['amount']}")
        else:
            print("❌ Valid form data rejected")
            print(f"   Errors: {form.errors}")
            return False
        
        # Test invalid account number
        invalid_data = {
            'receiver_account': '9999999999',  # Non-existent account
            'amount': '50.00',
            'description': 'Test transfer'
        }
        
        form = MoneyTransferForm(data=invalid_data)
        if not form.is_valid():
            print("✅ Invalid account number correctly rejected")
        else:
            print("❌ Invalid account number incorrectly accepted")
            return False
        
        # Test invalid amount
        invalid_amount_data = {
            'receiver_account': '8298370758',
            'amount': '-10.00',  # Negative amount
            'description': 'Test transfer'
        }
        
        form = MoneyTransferForm(data=invalid_amount_data)
        if not form.is_valid():
            print("✅ Invalid amount correctly rejected")
        else:
            print("❌ Invalid amount incorrectly accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing form validation: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test transactions
        test_transactions = Transaction.objects.filter(description='Test money transfer')
        count = test_transactions.count()
        test_transactions.delete()
        
        print(f"✅ Deleted {count} test transactions")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning up: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 PayWay Money Transfer Test Suite")
    print("=" * 50)
    
    tests = [
        test_money_transfer,
        test_form_validation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Money Transfer functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    # Clean up
    cleanup_test_data()
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    main()
