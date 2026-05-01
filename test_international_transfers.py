import pytest
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model

from account.models import Currency, Bank
from account.forms import InternationalTransferForm

pytestmark = pytest.mark.django_db

from account.models import Currency, Bank
from account.forms import (
    InternationalTransferForm,
    SwiftCodeSearchForm,
    CurrencyConverterForm,
)

# # Enable database access for all tests in this file
# pytestmark = pytest.mark.django_db
@pytest.fixture
def sample_currencies():
    Currency.objects.create(
        code="USD",
        name="US Dollar",
        symbol="$",
        exchange_rate_to_usd=1.0
    )
    Currency.objects.create(
        code="EUR",
        name="Euro",
        symbol="€",
        exchange_rate_to_usd=0.92
    )
    Currency.objects.create(
        code="GBP",
        name="British Pound",
        symbol="£",
        exchange_rate_to_usd=0.79
    )


@pytest.fixture
def sample_banks():
    Bank.objects.create(
        bank_name="Chase Bank",
        swift_code="CHASUS33XXX",
        country="United States"
    )
def test_currencies(sample_currencies):
    assert Currency.objects.count() == 3
def test_banks(sample_banks):
    assert Bank.objects.count() == 1

def test_currencies():
    """Test currency data"""
    currencies = Currency.objects.all()

    assert currencies.exists()
    assert currencies.count() > 0

    for currency in currencies:
        assert currency.code is not None
        assert currency.name is not None
        assert currency.symbol is not None
        assert currency.exchange_rate_to_usd is not None


def test_banks():
    """Test bank data"""
    banks = Bank.objects.all()

    assert banks.exists()
    assert banks.count() > 0

    for bank in banks:
        assert bank.swift_code is not None
        assert bank.bank_name is not None
        assert bank.country is not None


def test_swift_validation():
    """Test SWIFT code validation"""

    valid_codes = [
        "CHASUS33XXX",
        "BOFAUS3NXXX",
        "DEUTDEFFXXX",
        "BNPAFRPPXXX",
    ]

    for code in valid_codes:
        bank = Bank.objects.filter(swift_code=code).first()
        assert bank is not None, f"{code} should exist"

    invalid_codes = [
        "INVALID",
        "123456",
        "ABCDEFGHIJKLMNOP",
    ]

    for code in invalid_codes:
        bank = Bank.objects.filter(swift_code=code).first()
        assert bank is None, f"{code} should not exist"


def test_fee_calculation():
    """Test transfer fee calculation"""

    test_cases = [
        (100, "USD"),
        (500, "EUR"),
        (1000, "GBP"),
        (50, "JPY"),
        (200, "CAD"),
    ]

    form = InternationalTransferForm()

    for amount, currency_code in test_cases:
        currency = Currency.objects.filter(code=currency_code).first()

        assert currency is not None, f"{currency_code} should exist"

        fee = form.calculate_transfer_fee(
            Decimal(str(amount)),
            currency_code
        )

        assert fee > 0
        assert isinstance(fee, Decimal)


def test_currency_conversion():
    """Test currency conversion"""

    usd = Currency.objects.filter(code="USD").first()
    eur = Currency.objects.filter(code="EUR").first()
    gbp = Currency.objects.filter(code="GBP").first()

    assert usd is not None
    assert eur is not None
    assert gbp is not None

    amount_usd = Decimal("100")

    amount_eur = amount_usd * eur.exchange_rate_to_usd
    amount_gbp = amount_usd * gbp.exchange_rate_to_usd
    amount_usd_from_eur = Decimal("100") / eur.exchange_rate_to_usd

    assert amount_eur > 0
    assert amount_gbp > 0
    assert amount_usd_from_eur > 0


def test_form_validation():
    """Test form validation"""

    usd_currency = Currency.objects.get(code="USD")

    valid_data = {
        "amount": "500",
        "currency": usd_currency.pk,
        "swift_code": "CHASUS33XXX",
        "recipient_name": "John Doe",
        "recipient_account_number": "1234567890",
        "recipient_country": "United States",
        "recipient_city": "New York",
        "description": "Test transfer",
    }

    form = InternationalTransferForm(data=valid_data)

    assert form.is_valid(), f"Form errors: {form.errors}"

    fee = form.calculate_transfer_fee(
        Decimal("500"),
        "USD"
    )

    assert fee > 0

    invalid_data = {
        "amount": "0",
        "currency": usd_currency.pk,
        "swift_code": "INVALID",
        "recipient_name": "",
        "recipient_account_number": "123",
        "recipient_country": "United States",
        "recipient_city": "New York",
    }

    invalid_form = InternationalTransferForm(data=invalid_data)

    assert not invalid_form.is_valid()

    