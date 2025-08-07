from django.core.management.base import BaseCommand
from django.utils import timezone
from account.models import PaymentRequest


class Command(BaseCommand):
    help = 'Check and update expired payment requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Get all pending requests that have expired
        expired_requests = PaymentRequest.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would update {expired_requests.count()} expired payment requests'
                )
            )
            
            for request in expired_requests:
                self.stdout.write(
                    f'  - {request.request_id}: {request.requester.email} -> {request.recipient.email} '
                    f'(${request.amount}) - Expired: {request.expires_at}'
                )
        else:
            updated_count = 0
            for request in expired_requests:
                request.is_expired = True
                request.status = 'expired'
                request.save(update_fields=['is_expired', 'status'])
                updated_count += 1
                
                self.stdout.write(
                    f'Updated: {request.request_id} - {request.requester.email} -> {request.recipient.email} '
                    f'(${request.amount})'
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {updated_count} expired payment requests'
                )
            )
