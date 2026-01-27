"""
Django management command to load business object metadata from JSON file.

Usage:
    python manage.py load_metadata --file backend/fixtures/business_objects_metadata.json
    python manage.py load_metadata --update  # Update existing objects
"""
import json
import os
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from apps.system.services.metadata_service import MetadataService


class Command(BaseCommand):
    """Load business object metadata configuration from JSON file."""

    help = 'Load business object metadata configuration from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='backend/fixtures/business_objects_metadata.json',
            help='Path to metadata configuration JSON file'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing business objects'
        )

    def handle(self, *args, **options):
        """Execute the command."""
        file_path = options['file']
        update = options['update']

        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        # Load JSON file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON decode error: {e}')
            )
            return

        # Initialize service
        service = MetadataService()
        count = 0
        errors = []

        # Process each business object
        for obj_data in config.get('business_objects', []):
            code = obj_data.get('code')
            name = obj_data.get('name')

            try:
                # Check if already exists
                existing = service.get_business_object(code)

                if existing and not update:
                    self.stdout.write(
                        self.style.WARNING(
                            f'[SKIP] {name} ({code}) - already exists (use --update to modify)'
                        )
                    )
                    continue

                # Create or update
                service.create_business_object(obj_data)
                count += 1

                action = 'Updated' if existing else 'Created'
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[{action}] {name} ({code})'
                    )
                )

                # Show field count
                field_count = len(obj_data.get('fields', []))
                layout_count = len(obj_data.get('page_layouts', []))
                if field_count or layout_count:
                    self.stdout.write(
                        f'  -> Fields: {field_count}, Layouts: {layout_count}'
                    )

            except Exception as e:
                errors.append({
                    'code': code,
                    'name': name,
                    'error': str(e)
                })
                self.stdout.write(
                    self.style.ERROR(
                        f'[ERROR] {name} ({code}): {str(e)}'
                    )
                )

        # Summary
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Complete! Processed {count} business object(s)'
            )
        )

        if errors:
            self.stdout.write(
                self.style.ERROR(
                    f'Errors: {len(errors)} object(s) failed to load'
                )
            )
            for err in errors:
                self.stdout.write(f'  - {err["name"]} ({err["code"]}): {err["error"]}')
        else:
            self.stdout.write(
                self.style.SUCCESS('All objects loaded successfully!')
            )
