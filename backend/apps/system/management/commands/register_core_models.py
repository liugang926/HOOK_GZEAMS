"""
Management command to register hardcoded Django models as BusinessObjects.

This command creates BusinessObject entries for all core hardcoded models,
making them visible in the low-code configuration UI.

Usage:
    python manage.py register_core_models
    python manage.py register_core_models --sync-fields
    python manage.py register_core_models --code Asset
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.services.business_object_service import BusinessObjectService
from apps.system.services.hardcoded_object_sync_service import HardcodedObjectSyncService


class Command(BaseCommand):
    help = 'Register hardcoded Django models as BusinessObjects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync-fields',
            action='store_true',
            dest='sync_fields',
            help='Sync model fields after registration',
        )
        parser.add_argument(
            '--code',
            type=str,
            help='Register only a specific model by code',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            help='Update existing BusinessObject entries',
        )

    def handle(self, *args, **options):
        sync_fields = options.get('sync_fields', False)
        specific_code = options.get('code')
        force = options.get('force', False)

        business_object_service = BusinessObjectService()
        sync_service = HardcodedObjectSyncService()

        # Filter models to register
        if specific_code:
            definition = sync_service.get_definition(specific_code)
            if not definition:
                self.stderr.write(
                    self.style.ERROR(f'Unknown hardcoded model: {specific_code}')
                )
                return
            definitions = [definition]
        else:
            definitions = list(sync_service.iter_definitions())

        # Register each model
        registered_count = 0
        updated_count = 0
        synced_count = 0

        with transaction.atomic():
            for definition in sorted(definitions, key=lambda item: item.code):
                result = sync_service.ensure_business_object(
                    definition,
                    overwrite_existing=force,
                )
                code = definition.code
                name = definition.name

                if result.created:
                    registered_count += 1
                    self.stdout.write(
                        f'  {self.style.SUCCESS("CREATED")}: {code} - {name}'
                    )
                elif result.updated:
                    updated_count += 1
                    self.stdout.write(
                        f'  {self.style.WARNING("UPDATED")}: {code} - {name}'
                    )
                else:
                    self.stdout.write(
                        f'  {self.style.SUCCESS("SKIP")}: {code} - {name} (already exists)'
                    )

                # Sync fields if requested
                if sync_fields:
                    try:
                        field_count = business_object_service.sync_model_fields(code)
                        synced_count += field_count
                        self.stdout.write(
                            f'    {self.style.SUCCESS("SYNCED")}: {field_count} fields'
                        )
                    except Exception as e:
                        self.stderr.write(
                            f'    {self.style.ERROR("ERROR")}: Failed to sync fields - {e}'
                        )

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('Registration Summary:')
        self.stdout.write(f'  Total processed: {len(definitions)}')
        self.stdout.write(f'  Registered: {registered_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        if sync_fields:
            self.stdout.write(f'  Fields synced: {synced_count}')
        self.stdout.write('=' * 60)
