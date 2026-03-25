"""
Synchronize MenuGroup / MenuEntry registry models from the current defaults.

This command is useful after migrations, metadata imports, or when Docker
environments need to repair the default menu registry explicitly.
"""
from django.core.management.base import BaseCommand

from apps.system.menu_config import sync_business_object_menu_configs, sync_menu_registry_models
from apps.system.models import MenuEntry, MenuGroup


class Command(BaseCommand):
    help = "Synchronize MenuGroup and MenuEntry registry models"

    def handle(self, *args, **options):
        registry_result = sync_menu_registry_models()
        legacy_result = sync_business_object_menu_configs()

        self.stdout.write(self.style.SUCCESS("Menu registry synchronized."))
        self.stdout.write(
            "  created_groups={created_groups} created_entries={created_entries} updated_entries={updated_entries}".format(
                created_groups=len(registry_result.get("created_groups", [])),
                created_entries=len(registry_result.get("created_entries", [])),
                updated_entries=len(registry_result.get("updated_entries", [])),
            )
        )
        self.stdout.write(
            "  menu_groups={groups} menu_entries={entries}".format(
                groups=MenuGroup.objects.filter(is_deleted=False).count(),
                entries=MenuEntry.objects.filter(is_deleted=False).count(),
            )
        )
        self.stdout.write(
            "  business_object_menu_config updated={updated} unchanged={unchanged}".format(
                updated=len(legacy_result.get("updated", [])),
                unchanged=len(legacy_result.get("unchanged", [])),
            )
        )
