from django.core.management.base import BaseCommand
from account.models import Currency, Bank
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate database with currencies and banks for international transfers'

    def handle(self, *args, **options):
        self.stdout.write('Populating currencies...')
        self.populate_currencies()
        
        self.stdout.write('Populating banks...')
        self.populate_banks()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated international transfer data!')
        )

    def populate_currencies(self):
        """Populate currencies with static exchange rates"""
        currencies_data = [
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'exchange_rate': 1.000000},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'exchange_rate': 0.850000},
            {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'exchange_rate': 0.730000},
            {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥', 'exchange_rate': 110.000000},
            {'code': 'CAD', 'name': 'Canadian Dollar', 'symbol': 'C$', 'exchange_rate': 1.250000},
            {'code': 'AUD', 'name': 'Australian Dollar', 'symbol': 'A$', 'exchange_rate': 1.350000},
            {'code': 'CHF', 'name': 'Swiss Franc', 'symbol': 'CHF', 'exchange_rate': 0.920000},
            {'code': 'SGD', 'name': 'Singapore Dollar', 'symbol': 'S$', 'exchange_rate': 1.350000},
            {'code': 'HKD', 'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'exchange_rate': 7.800000},
            {'code': 'NZD', 'name': 'New Zealand Dollar', 'symbol': 'NZ$', 'exchange_rate': 1.450000},
        ]
        
        for currency_data in currencies_data:
            Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults={
                    'name': currency_data['name'],
                    'symbol': currency_data['symbol'],
                    'exchange_rate_to_usd': Decimal(str(currency_data['exchange_rate'])),
                    'is_active': True
                }
            )
        
        self.stdout.write(f'Created {len(currencies_data)} currencies')

    def populate_banks(self):
        """Populate banks with major international banks"""
        banks_data = [
            # United States
            {'swift': 'CHASUS33XXX', 'name': 'JPMORGAN CHASE BANK, N.A.', 'country': 'United States', 'city': 'New York'},
            {'swift': 'BOFAUS3NXXX', 'name': 'BANK OF AMERICA, N.A.', 'country': 'United States', 'city': 'Charlotte'},
            {'swift': 'WELLSFARGO', 'name': 'WELLS FARGO BANK, N.A.', 'country': 'United States', 'city': 'San Francisco'},
            {'swift': 'CITIUS33XXX', 'name': 'CITIBANK, N.A.', 'country': 'United States', 'city': 'New York'},
            {'swift': 'GOLDUS33XXX', 'name': 'GOLDMAN SACHS BANK USA', 'country': 'United States', 'city': 'New York'},
            
            # United Kingdom
            {'swift': 'BARCGB22XXX', 'name': 'BARCLAYS BANK PLC', 'country': 'United Kingdom', 'city': 'London'},
            {'swift': 'HSBCGB2LXXX', 'name': 'HSBC BANK PLC', 'country': 'United Kingdom', 'city': 'London'},
            {'swift': 'RZBAAT2LXXX', 'name': 'ROYAL BANK OF SCOTLAND PLC', 'country': 'United Kingdom', 'city': 'Edinburgh'},
            {'swift': 'LOYDGB2LXXX', 'name': 'LLOYDS BANK PLC', 'country': 'United Kingdom', 'city': 'London'},
            {'swift': 'STANGB2LXXX', 'name': 'STANDARD CHARTERED BANK', 'country': 'United Kingdom', 'city': 'London'},
            
            # Germany
            {'swift': 'DEUTDEFFXXX', 'name': 'DEUTSCHE BANK AG', 'country': 'Germany', 'city': 'Frankfurt'},
            {'swift': 'COBADEFFXXX', 'name': 'COMMERZBANK AG', 'country': 'Germany', 'city': 'Frankfurt'},
            {'swift': 'DRESDEFFXXX', 'name': 'DRESDNER BANK AG', 'country': 'Germany', 'city': 'Frankfurt'},
            {'swift': 'UBSWDEFFXXX', 'name': 'UBS EUROPE SE', 'country': 'Germany', 'city': 'Frankfurt'},
            
            # France
            {'swift': 'BNPAFRPPXXX', 'name': 'BNP PARIBAS', 'country': 'France', 'city': 'Paris'},
            {'swift': 'CRLYFRPPXXX', 'name': 'CREDIT LYONNAIS', 'country': 'France', 'city': 'Paris'},
            {'swift': 'SOGEFRPPXXX', 'name': 'SOCIETE GENERALE', 'country': 'France', 'city': 'Paris'},
            {'swift': 'CCFRFRPPXXX', 'name': 'CREDIT AGRICOLE', 'country': 'France', 'city': 'Paris'},
            
            # Canada
            {'swift': 'ROYCCAT2XXX', 'name': 'ROYAL BANK OF CANADA', 'country': 'Canada', 'city': 'Toronto'},
            {'swift': 'TDOMCATTXXX', 'name': 'TORONTO-DOMINION BANK', 'country': 'Canada', 'city': 'Toronto'},
            {'swift': 'BMOCCAM2XXX', 'name': 'BANK OF MONTREAL', 'country': 'Canada', 'city': 'Montreal'},
            {'swift': 'CIBCCATTXXX', 'name': 'CANADIAN IMPERIAL BANK OF COMMERCE', 'country': 'Canada', 'city': 'Toronto'},
            
            # Australia
            {'swift': 'WESTAU3SXXX', 'name': 'WESTPAC BANKING CORPORATION', 'country': 'Australia', 'city': 'Sydney'},
            {'swift': 'ANZBAU3MXXX', 'name': 'AUSTRALIA AND NEW ZEALAND BANKING GROUP', 'country': 'Australia', 'city': 'Melbourne'},
            {'swift': 'CBAFAU2SXXX', 'name': 'COMMONWEALTH BANK OF AUSTRALIA', 'country': 'Australia', 'city': 'Sydney'},
            {'swift': 'NATAAU33XXX', 'name': 'NATIONAL AUSTRALIA BANK', 'country': 'Australia', 'city': 'Melbourne'},
            
            # Japan
            {'swift': 'MHCBJPJTXXX', 'name': 'MIZUHO BANK, LTD.', 'country': 'Japan', 'city': 'Tokyo'},
            {'swift': 'SMBCJPJTXXX', 'name': 'SUMITOMO MITSUI BANKING CORPORATION', 'country': 'Japan', 'city': 'Tokyo'},
            {'swift': 'BOTKJPJTXXX', 'name': 'BANK OF TOKYO-MITSUBISHI UFJ, LTD.', 'country': 'Japan', 'city': 'Tokyo'},
            {'swift': 'NORIJPJTXXX', 'name': 'NORINCHUKIN BANK', 'country': 'Japan', 'city': 'Tokyo'},
            
            # Switzerland
            {'swift': 'UBSWCHZH80A', 'name': 'UBS SWITZERLAND AG', 'country': 'Switzerland', 'city': 'Zurich'},
            {'swift': 'CRESCHZZ80A', 'name': 'CREDIT SUISSE AG', 'country': 'Switzerland', 'city': 'Zurich'},
            {'swift': 'ZKBKCHZZ80A', 'name': 'ZURCHER KANTONALBANK', 'country': 'Switzerland', 'city': 'Zurich'},
            {'swift': 'RAIFCH22XXX', 'name': 'RAIFFEISEN SCHWEIZ GENOSSENSCHAFT', 'country': 'Switzerland', 'city': 'St. Gallen'},
            
            # Singapore
            {'swift': 'DBSSSGSGXXX', 'name': 'DBS BANK LTD', 'country': 'Singapore', 'city': 'Singapore'},
            {'swift': 'OCBCSGSGXXX', 'name': 'OVERSEA-CHINESE BANKING CORPORATION', 'country': 'Singapore', 'city': 'Singapore'},
            {'swift': 'UOVBSGSGXXX', 'name': 'UNITED OVERSEAS BANK LTD', 'country': 'Singapore', 'city': 'Singapore'},
            
            # Hong Kong
            {'swift': 'HSBCHKHHXXX', 'name': 'HONGKONG AND SHANGHAI BANKING CORPORATION', 'country': 'Hong Kong', 'city': 'Hong Kong'},
            {'swift': 'BOCHHKHHXXX', 'name': 'BANK OF CHINA (HONG KONG) LIMITED', 'country': 'Hong Kong', 'city': 'Hong Kong'},
            {'swift': 'HASEHKHHXXX', 'name': 'HANG SENG BANK LIMITED', 'country': 'Hong Kong', 'city': 'Hong Kong'},
        ]
        
        for bank_data in banks_data:
            Bank.objects.get_or_create(
                swift_code=bank_data['swift'],
                defaults={
                    'bank_name': bank_data['name'],
                    'country': bank_data['country'],
                    'city': bank_data['city'],
                    'is_active': True
                }
            )
        
        self.stdout.write(f'Created {len(banks_data)} banks')
