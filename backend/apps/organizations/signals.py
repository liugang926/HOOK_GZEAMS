"""
Signals for automatic organization initialization.
"""
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Organization


@receiver(post_migrate)
def initialize_default_organization(sender, **kwargs):
    """
    Automatically initialize the default organization after migrations.
    
    This ensures there's always at least one organization available
    for the system to function properly.
    """
    if sender.name == 'organizations':
        org = Organization.initialize_default_organization()
        print(f"Default organization initialized: {org.name} ({org.code})")
