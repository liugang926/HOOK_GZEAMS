"""
Django management command to initialize the default organization.

Run: python manage.py init_default_org
"""
from django.core.management.base import BaseCommand
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = 'Initialize the default organization for the system'

    def handle(self, *args, **options):
        """Execute the command."""
        org = Organization.initialize_default_organization()
        
        self.stdout.write(self.style.SUCCESS(
            f"Default organization initialized:\n"
            f"  - ID: {org.id}\n"
            f"  - Name: {org.name}\n"
            f"  - Code: {org.code}\n"
            f"  - Type: {org.org_type}\n"
            f"  - Invite Code: {org.invite_code}\n"
            f"  - Is Active: {org.is_active}"
        ))
