#!/usr/bin/env python3
"""
Test script for International Transfers functionality
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payway.settings')
django.setup()

from account.models import Currency, Bank, InternationalTransfer, User, Account
from account.forms import InternationalTransferForm, SwiftCodeSearchForm, CurrencyConverterForm


def test_currencies():
    """Test currency data"""
    print("🔍 Testing Currencies...")
    currencies = Currency.objects.all()
    print(f"Found {currencies.count()} currencies:")
    for currency in currencies:
        print(f"  - {currency.code}: {currency.name} ({currency.symbol}) - Rate: {currency.exchange_rate_to_usd}")
    print()


def test_banks():
    """Test bank data"""
    print("🏦 Testing Banks...")
    banks = Bank.objects.all()
    print(f"Found {banks.count()} banks:")
    
    # Group by country
    countries = {}
    for bank in banks:
        if bank.country not in countries:
            countries[bank.country] = []
        countries[bank.country].append(bank)
    
    for country, country_banks in countries.items():
        print(f"  {country}: {len(country_banks)} banks")
        for bank in country_banks[:3]:  # Show first 3 banks per country
            print(f"    - {bank.swift_code}: {bank.bank_name}")
        if len(country_banks) > 3:
            print(f"    ... and {len(country_banks) - 3} more")
    print()


def test_swift_validation():
    """Test SWIFT code validation"""
    print("🔍 Testing SWIFT Code Validation...")
    
    # Test valid SWIFT codes
    valid_codes = ['CHASUS33XXX', 'BOFAUS3NXXX', 'DEUTDEFFXXX', 'BNPAFRPPXXX']
    for code in valid_codes:
        try:
            bank = Bank.objects.get(swift_code=code)
            print(f"  ✅ {code}: {bank.bank_name} ({bank.country})")
        except Bank.DoesNotExist:
            print(f"  ❌ {code}: Not found")
    
    # Test invalid SWIFT codes
    invalid_codes = ['INVALID', '123456', 'ABCDEFGHIJKLMNOP']
    for code in invalid_codes:
        try:
            bank = Bank.objects.get(swift_code=code)
            print(f"  ❌ {code}: Unexpectedly found")
        except Bank.DoesNotExist:
            print(f"  ✅ {code}: Correctly not found")
    print()


def test_fee_calculation():
    """Test fee calculation"""
    print("💰 Testing Fee Calculation...")
    
    # Test fee calculation for different amounts and currencies
    test_cases = [
        (100, 'USD'),
        (500, 'EUR'),
        (1000, 'GBP'),
        (50, 'JPY'),
        (200, 'CAD'),
    ]
    
    for amount, currency_code in test_cases:
        try:
            currency = Currency.objects.get(code=currency_code)
            
            # Calculate fee using the same logic as the form
            fee_structure = {
                'USD': {'percentage': 0.02, 'min_fee': 5.00, 'max_fee': 50.00},
                'EUR': {'percentage': 0.025, 'min_fee': 5.00, 'max_fee': 60.00},
                'GBP': {'percentage': 0.03, 'min_fee': 5.00, 'max_fee': 75.00},
                'JPY': {'percentage': 0.025, 'min_fee': 500.00, 'max_fee': 5000.00},
                'CAD': {'percentage': 0.025, 'min_fee': 6.00, 'max_fee': 60.00},
            }
            
            structure = fee_structure.get(currency_code, fee_structure['USD'])
            percentage_fee = amount * Decimal(str(structure['percentage']))
            fee = max(structure['min_fee'], min(percentage_fee, structure['max_fee']))
            total = amount + fee
            
            print(f"  {currency.symbol}{amount} ({currency_code}):")
            print(f"    Amount: {currency.symbol}{amount}")
            print(f"    Fee: {currency.symbol}{fee:.2f}")
            print(f"    Total: {currency.symbol}{total:.2f}")
            print()
            
        except Currency.DoesNotExist:
            print(f"  ❌ Currency {currency_code} not found")
    print()


def test_currency_conversion():
    """Test currency conversion"""
    print("🔄 Testing Currency Conversion...")
    
    try:
        usd = Currency.objects.get(code='USD')
        eur = Currency.objects.get(code='EUR')
        gbp = Currency.objects.get(code='GBP')
        
        # Test conversion from USD to other currencies
        amount_usd = 100
        
        # USD to EUR
        amount_eur = amount_usd * eur.exchange_rate_to_usd
        print(f"  ${amount_usd} USD = €{amount_eur:.2f} EUR")
        
        # USD to GBP
        amount_gbp = amount_usd * gbp.exchange_rate_to_usd
        print(f"  ${amount_usd} USD = £{amount_gbp:.2f} GBP")
        
        # EUR to USD
        amount_usd_from_eur = 100 / eur.exchange_rate_to_usd
        print(f"  €100 EUR = ${amount_usd_from_eur:.2f} USD")
        
    except Currency.DoesNotExist as e:
        print(f"  ❌ Currency not found: {e}")
    print()


def test_form_validation():
    """Test form validation"""
    print("📝 Testing Form Validation...")
    
    # Test valid form data
    valid_data = {
        'amount': '500',
        'currency': Currency.objects.get(code='USD').pk,
        'swift_code': 'CHASUS33XXX',
        'recipient_name': 'John Doe',
        'recipient_account_number': '1234567890',
        'recipient_country': 'United States',
        'recipient_city': 'New York',
        'description': 'Test transfer'
    }
    
    form = InternationalTransferForm(data=valid_data)
    if form.is_valid():
        print("  ✅ Valid form data accepted")
        print(f"    Bank: {form.bank.bank_name}")
        fee = form.calculate_transfer_fee(Decimal('500'), 'USD')
        print(f"    Calculated fee: ${fee}")
    else:
        print("  ❌ Valid form data rejected:")
        for field, errors in form.errors.items():
            print(f"    {field}: {errors}")
    
    # Test invalid form data
    invalid_data = {
        'amount': '0',  # Invalid amount
        'currency': Currency.objects.get(code='USD').pk,
        'swift_code': 'INVALID',  # Invalid SWIFT code
        'recipient_name': '',  # Empty name
        'recipient_account_number': '123',  # Too short
        'recipient_country': 'United States',
        'recipient_city': 'New York',
    }
    
    form = InternationalTransferForm(data=invalid_data)
    if not form.is_valid():
        print("  ✅ Invalid form data correctly rejected")
        for field, errors in form.errors.items():
            print(f"    {field}: {errors}")
    else:
        print("  ❌ Invalid form data incorrectly accepted")
    print()


def main():
    """Run all tests"""
    print("🚀 Testing International Transfers Functionality")
    print("=" * 50)
    
    test_currencies()
    test_banks()
    test_swift_validation()
    test_fee_calculation()
    test_currency_conversion()
    test_form_validation()
    
    print("✅ All tests completed!")


if __name__ == '__main__':
    main()
