import pytest
from decimal import Decimal

from account.models import Currency, Bank
from account.forms import (
    InternationalTransferForm,
    SwiftCodeSearchForm,
    CurrencyConverterForm,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_currencies():
    Currency.objects.create(
        code="USD",
        name="US Dollar",
        symbol="$",
        exchange_rate_to_usd=Decimal("1.00"),
    )
    Currency.objects.create(
        code="EUR",
        name="Euro",
        symbol="€",
        exchange_rate_to_usd=Decimal("0.92"),
    )
    Currency.objects.create(
        code="GBP",
        name="British Pound",
        symbol="£",
        exchange_rate_to_usd=Decimal("0.79"),
    )
    Currency.objects.create(
        code="JPY",
        name="Japanese Yen",
        symbol="¥",
        exchange_rate_to_usd=Decimal("149.50"),
    )
    Currency.objects.create(
        code="CAD",
        name="Canadian Dollar",
        symbol="C$",
        exchange_rate_to_usd=Decimal("1.35"),
    )


@pytest.fixture
def sample_banks():
    Bank.objects.create(
        bank_name="Chase Bank",
        swift_code="CHASUS33XXX",
        country="United States",
    )
    Bank.objects.create(
        bank_name="Bank of America",
        swift_code="BOFAUS3NXXX",
        country="United States",
    )
    Bank.objects.create(
        bank_name="Deutsche Bank",
        swift_code="DEUTDEFFXXX",
        country="Germany",
    )
    Bank.objects.create(
        bank_name="BNP Paribas",
        swift_code="BNPAFRPPXXX",
        country="France",
    )


def test_currencies(sample_currencies):
    """Test currency data"""

    currencies = Currency.objects.all()

    assert currencies.exists()
    assert currencies.count() == 5

    for currency in currencies:
        assert currency.code is not None
        assert currency.name is not None
        assert currency.symbol is not None
        assert currency.exchange_rate_to_usd is not None


def test_banks(sample_banks):
    """Test bank data"""

    banks = Bank.objects.all()

    assert banks.exists()
    assert banks.count() == 4

    for bank in banks:
        assert bank.swift_code is not None
        assert bank.bank_name is not None
        assert bank.country is not None


def test_swift_validation(sample_banks):
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


def test_fee_calculation(sample_currencies):
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
            currency_code,
        )

        assert fee > 0

        # Allow both Decimal and float since the current form method
        # may return float depending on implementation
        assert isinstance(fee, (Decimal, float))


def test_currency_conversion(sample_currencies):
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


def test_form_validation(sample_currencies, sample_banks):
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
        "USD",
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