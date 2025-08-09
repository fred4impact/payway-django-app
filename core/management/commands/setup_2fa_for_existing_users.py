from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from userauths.models import TwoFactorAuth

User = get_user_model()


class Command(BaseCommand):
    help = 'Create TwoFactorAuth objects for existing users who do not have them'

    def handle(self, *args, **options):
        users_without_2fa = []
        users_created = 0
        
        # Get all users
        all_users = User.objects.all()
        
        for user in all_users:
            try:
                # Check if user already has TwoFactorAuth object
                user.twofactorauth
            except:
                # User doesn't have TwoFactorAuth object, create one
                users_without_2fa.append(user)
        
        if not users_without_2fa:
            self.stdout.write(
                self.style.SUCCESS('All users already have TwoFactorAuth objects.')
            )
            return
        
        self.stdout.write(
            f'Found {len(users_without_2fa)} users without TwoFactorAuth objects.'
        )
        
        # Create TwoFactorAuth objects for users who need them
        for user in users_without_2fa:
            try:
                TwoFactorAuth.objects.create(
                    user=user,
                    method='totp',  # Default to TOTP method
                    is_enabled=False,  # Disabled by default
                    secret_key='',  # Empty secret key
                    phone_number=user.phone_number if user.phone_number else '',
                    backup_codes=[]
                )
                users_created += 1
                self.stdout.write(
                    f'Created TwoFactorAuth object for user: {user.email}'
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to create TwoFactorAuth for {user.email}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {users_created} TwoFactorAuth objects.'
            )
        )
