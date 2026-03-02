"""
Management command to manually sync metadata.

Usage:
    python manage.py sync_metadata
    python manage.py sync_metadata --force
"""
from django.core.management.base import BaseCommand

from apps.system.services.metadata_sync_service import sync_metadata_on_startup


class Command(BaseCommand):
    help = 'Sync hardcoded Django models to metadata tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Force re-sync of all fields (update existing)',
        )

    def handle(self, *args, **options):
        """Execute the metadata sync command."""
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING('Starting metadata sync...'))

        if force:
            self.stdout.write(self.style.WARNING('Force mode enabled - will update existing fields'))

        results = sync_metadata_on_startup(force=force)

        # Report results
        self.stdout.write(self.style.SUCCESS(f'\n=== Metadata Sync Results ==='))

        if results['created_objects']:
            self.stdout.write(
                self.style.SUCCESS(f"Created BusinessObject records: {', '.join(results['created_objects'])}")
            )

        if results['updated_objects']:
            self.stdout.write(
                self.style.WARNING(f"Updated BusinessObject records: {', '.join(results['updated_objects'])}")
            )

        if results['synced_fields']:
            for obj_code, count in results['synced_fields'].items():
                self.stdout.write(
                    self.style.SUCCESS(f"  - {obj_code}: {count} fields synced")
                )

        if results['created_layouts']:
            self.stdout.write(
                self.style.SUCCESS(f"Created default layouts: {', '.join(results['created_layouts'])}")
            )

        if results['errors']:
            self.stdout.write(
                self.style.ERROR(f"\nErrors encountered: {len(results['errors'])}")
            )
            for error in results['errors']:
                self.stdout.write(
                    self.style.ERROR(f"  - {error['object_code']}: {error['error']}")
                )

        self.stdout.write(self.style.SUCCESS('\nMetadata sync completed!'))
