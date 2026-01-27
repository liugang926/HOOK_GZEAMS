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

from apps.system.services.business_object_service import (
    BusinessObjectService,
    CORE_HARDcoded_MODELS,
    HARDCODED_OBJECT_NAMES,
)


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

        service = BusinessObjectService()

        # Filter models to register
        if specific_code:
            if specific_code not in CORE_HARDcoded_MODELS:
                self.stderr.write(
                    self.style.ERROR(f'Unknown hardcoded model: {specific_code}')
                )
                return
            models_to_register = {specific_code: CORE_HARDcoded_MODELS[specific_code]}
        else:
            models_to_register = CORE_HARDcoded_MODELS

        # Register each model
        registered_count = 0
        updated_count = 0
        synced_count = 0

        with transaction.atomic():
            for code, model_path in sorted(models_to_register.items()):
                names = HARDCODED_OBJECT_NAMES.get(code, (code, code))
                name = names[0]
                name_en = names[1]

                # Check if already exists
                from apps.system.models import BusinessObject
                existing = BusinessObject.objects.filter(code=code).first()

                if existing:
                    if force:
                        # Update existing
                        existing.name = name
                        existing.name_en = name_en
                        existing.is_hardcoded = True
                        existing.django_model_path = model_path
                        existing.save()
                        updated_count += 1
                        self.stdout.write(
                            f'  {self.style.WARNING("UPDATED")}: {code} - {name}'
                        )
                    else:
                        self.stdout.write(
                            f'  {self.style.SUCCESS("SKIP")}: {code} - {name} (already exists)'
                        )
                        registered_count += 1
                else:
                    # Create new
                    obj = service.register_hardcoded_object(code, name, name_en)
                    registered_count += 1
                    self.stdout.write(
                        f'  {self.style.SUCCESS("CREATED")}: {code} - {name}'
                    )

                # Sync fields if requested
                if sync_fields:
                    try:
                        field_count = service.sync_model_fields(code)
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
        self.stdout.write(f'  Total processed: {len(models_to_register)}')
        self.stdout.write(f'  Registered: {registered_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        if sync_fields:
            self.stdout.write(f'  Fields synced: {synced_count}')
        self.stdout.write('=' * 60)
