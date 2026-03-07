"""
Synchronize BusinessObject.menu_config using the standard menu model.

The stored configuration remains language-neutral and contains only
stable codes, translation keys, ordering, and icon metadata.
"""
from django.core.management.base import BaseCommand

from apps.system.menu_config import MENU_GROUPS, build_menu_config_for_object
from apps.system.models import BusinessObject


class Command(BaseCommand):
    help = "Synchronize menu_config for all BusinessObjects"

    def handle(self, *args, **options):
        queryset = BusinessObject.objects.filter(is_deleted=False).order_by("code")
        total = queryset.count()
        updated = 0
        unchanged = 0

        self.stdout.write(f"Found {total} BusinessObjects")

        for obj in queryset:
            menu_config = build_menu_config_for_object(obj.code, obj.menu_config or {})

            if (obj.menu_config or {}) == menu_config:
                unchanged += 1
                continue

            obj.menu_config = menu_config
            obj.save(update_fields=["menu_config"])
            updated += 1
            self.stdout.write(
                "  UPDATED "
                f"{obj.code:30s} -> {menu_config['group_code']} ({menu_config['item_order']})"
            )

        self.stdout.write(f"\nDone. updated={updated}, unchanged={unchanged}, total={total}")

        self.stdout.write("\nMenu groups summary:")
        for group_code, group in sorted(MENU_GROUPS.items(), key=lambda item: item[1]["order"]):
            count = queryset.filter(menu_config__group_code=group_code).count()
            if count:
                self.stdout.write(f"  {group_code:20s} {count}")

