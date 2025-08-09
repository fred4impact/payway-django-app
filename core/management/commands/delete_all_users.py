from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from userauths.models import TwoFactorAuth, SecurityLog, UserDevice, AccountLockout
from account.models import Account, PaymentRequest, Transaction, Notification, CreditCard, Bank, Currency, InternationalTransfer
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete all existing users and related data to start fresh'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all users',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.ERROR(
                    'This command will delete ALL users and related data!\n'
                    'Use --confirm to proceed.'
                )
            )
            return

        # Count existing data
        user_count = User.objects.count()
        account_count = Account.objects.count()
        security_log_count = SecurityLog.objects.count()
        
        self.stdout.write(f'Found {user_count} users, {account_count} accounts, {security_log_count} security logs')
        
        if user_count == 0:
            self.stdout.write(self.style.WARNING('No users to delete.'))
            return

        # Ask for final confirmation
        confirm = input(f'\nAre you sure you want to delete {user_count} users and ALL related data? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Operation cancelled.'))
            return

        try:
            with transaction.atomic():
                # Delete in order to respect foreign key constraints
                self.stdout.write('Deleting security logs...')
                SecurityLog.objects.all().delete()
                
                self.stdout.write('Deleting user devices...')
                UserDevice.objects.all().delete()
                
                self.stdout.write('Deleting account lockouts...')
                AccountLockout.objects.all().delete()
                
                self.stdout.write('Deleting two-factor auth...')
                TwoFactorAuth.objects.all().delete()
                
                self.stdout.write('Deleting notifications...')
                Notification.objects.all().delete()
                
                self.stdout.write('Deleting transactions...')
                Transaction.objects.all().delete()
                
                self.stdout.write('Deleting payment requests...')
                PaymentRequest.objects.all().delete()
                
                self.stdout.write('Deleting credit cards...')
                CreditCard.objects.all().delete()
                
                self.stdout.write('Deleting international transfers...')
                InternationalTransfer.objects.all().delete()
                
                self.stdout.write('Deleting banks...')
                Bank.objects.all().delete()
                
                self.stdout.write('Deleting currencies...')
                Currency.objects.all().delete()
                
                self.stdout.write('Deleting accounts...')
                Account.objects.all().delete()
                
                self.stdout.write('Deleting users...')
                User.objects.all().delete()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted {user_count} users and all related data!'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error deleting users: {e}')
            )
            raise
