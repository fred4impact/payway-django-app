"""
DEVELOPMENT/TESTING ONLY - REMOVE BEFORE PRODUCTION DEPLOYMENT

This command creates dummy test users for development and testing purposes.
These users contain fictional personal data and should NEVER be used in production.

WARNING: This command and all test users should be removed before shipping to production.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from account.models import Account, KYC
from datetime import date
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create 3 dummy users with KYC data for testing (DEVELOPMENT ONLY)'

    def handle(self, *args, **kwargs):
        # WARNING: DEVELOPMENT/TESTING ONLY - REMOVE BEFORE PRODUCTION
        # These are fictional test users with fake personal data
        # DO NOT use in production environment
        
        # Test user data
        test_users = [
            {
                'email': 'john.doe@test.com',
                'username': 'johndoe',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone_number': '+1234567890',
                'date_of_birth': date(1990, 5, 15),
                'password': 'testpass123',
                'kyc': {
                    'full_name': 'John Michael Doe',
                    'date_of_birth': date(1990, 5, 15),
                    'nationality': 'American',
                    'address': '123 Main Street, Apt 4B',
                    'city': 'New York',
                    'state': 'NY',
                    'country': 'United States',
                    'postal_code': '10001',
                    'verification_status': 'approved',
                    'document_verified': True,
                    'face_verified': True,
                    'verification_confidence': 95.5,
                    'risk_score': 0.1,
                }
            },
            {
                'email': 'sarah.smith@test.com',
                'username': 'sarahsmith',
                'first_name': 'Sarah',
                'last_name': 'Smith',
                'phone_number': '+1987654321',
                'date_of_birth': date(1988, 12, 3),
                'password': 'testpass123',
                'kyc': {
                    'full_name': 'Sarah Elizabeth Smith',
                    'date_of_birth': date(1988, 12, 3),
                    'nationality': 'Canadian',
                    'address': '456 Oak Avenue, Suite 12',
                    'city': 'Toronto',
                    'state': 'ON',
                    'country': 'Canada',
                    'postal_code': 'M5V 3A8',
                    'verification_status': 'pending',
                    'document_verified': False,
                    'face_verified': False,
                    'verification_confidence': 0.0,
                    'risk_score': 0.3,
                }
            },
            {
                'email': 'mike.wilson@test.com',
                'username': 'mikewilson',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'phone_number': '+1122334455',
                'date_of_birth': date(1995, 8, 22),
                'password': 'testpass123',
                'kyc': {
                    'full_name': 'Michael James Wilson',
                    'date_of_birth': date(1995, 8, 22),
                    'nationality': 'British',
                    'address': '789 High Street, Flat 7',
                    'city': 'London',
                    'state': 'England',
                    'country': 'United Kingdom',
                    'postal_code': 'SW1A 1AA',
                    'verification_status': 'rejected',
                    'document_verified': False,
                    'face_verified': False,
                    'verification_confidence': 25.0,
                    'risk_score': 0.8,
                }
            }
        ]

        created_users = []

        for user_data in test_users:
            # Check if user already exists
            if User.objects.filter(email=user_data['email']).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {user_data["email"]} already exists, skipping...')
                )
                continue

            # Create user
            user = User.objects.create_user(
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone_number=user_data['phone_number'],
                date_of_birth=user_data['date_of_birth'],
                password=user_data['password'],
                is_verified=True
            )

            # Get the automatically created account
            account = Account.objects.get(user=user)
            
            # Add some balance to the account
            account.account_balance = random.uniform(1000, 10000)
            account.save()

            # Create KYC data
            kyc_data = user_data['kyc']
            kyc = KYC.objects.create(
                user=user,
                full_name=kyc_data['full_name'],
                date_of_birth=kyc_data['date_of_birth'],
                nationality=kyc_data['nationality'],
                address=kyc_data['address'],
                city=kyc_data['city'],
                state=kyc_data['state'],
                country=kyc_data['country'],
                postal_code=kyc_data['postal_code'],
                verification_status=kyc_data['verification_status'],
                document_verified=kyc_data['document_verified'],
                face_verified=kyc_data['face_verified'],
                verification_confidence=kyc_data['verification_confidence'],
                risk_score=kyc_data['risk_score'],
                ai_verification_status='completed' if kyc_data['verification_status'] == 'approved' else 'pending'
            )

            created_users.append({
                'user': user,
                'account': account,
                'kyc': kyc
            })

            self.stdout.write(
                self.style.SUCCESS(
                    f'Created user: {user.email} (Account: {account.account_number}, Balance: ${account.account_balance:.2f})'
                )
            )

        if created_users:
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully created {len(created_users)} test users!')
            )
            self.stdout.write('\nTest User Credentials:')
            self.stdout.write('=' * 50)
            for i, data in enumerate(created_users, 1):
                user = data['user']
                account = data['account']
                kyc = data['kyc']
                self.stdout.write(f'\n{i}. {user.get_full_name()}')
                self.stdout.write(f'   Email: {user.email}')
                self.stdout.write(f'   Password: testpass123')
                self.stdout.write(f'   Account: {account.account_number}')
                self.stdout.write(f'   Balance: ${account.account_balance:.2f}')
                self.stdout.write(f'   KYC Status: {kyc.verification_status}')
        else:
            self.stdout.write(
                self.style.WARNING('No new users were created. All test users already exist.')
            ) 