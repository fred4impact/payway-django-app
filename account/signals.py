from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Account

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_account(sender, instance, created, **kwargs):
    """Create an account automatically when a new user is created"""
    if created:
        Account.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_account(sender, instance, **kwargs):
    """Save the account when the user is saved"""
    if hasattr(instance, 'account'):
        instance.account.save() 