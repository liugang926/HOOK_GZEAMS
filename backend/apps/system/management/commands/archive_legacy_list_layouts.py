"""
Archive legacy list PageLayout rows under the single-layout model.

List pages now use field-driven columns (`show_in_list` + `sort_order`) and
user column preferences. Dedicated `layout_type='list'` rows are obsolete.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.models import PageLayout


@dataclass
class ArchiveStats:
    scanned: int = 0
    archived: int = 0
    unchanged: int = 0


class Command(BaseCommand):
    help = "Archive legacy list PageLayout rows (layout_type='list')."

    def add_arguments(self, parser):
        parser.add_argument("--object-code", type=str, default="", help="Filter by business object code")
        parser.add_argument("--organization-id", type=str, default="", help="Filter by organization id")
        parser.add_argument("--limit", type=int, default=0, help="Limit number of rows scanned")
        parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")

    def handle(self, *args, **options):
        object_code = (options.get("object_code") or "").strip()
        organization_id = (options.get("organization_id") or "").strip()
        limit = int(options.get("limit") or 0)
        apply_changes = bool(options.get("apply"))

        qs = PageLayout.objects.filter(
            is_deleted=False,
            layout_type="list",
        ).select_related("business_object", "organization").order_by("business_object__code", "layout_code")

        if object_code:
            qs = qs.filter(business_object__code=object_code)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        rows = list(qs[:limit] if limit > 0 else qs)
        stats = ArchiveStats(scanned=len(rows))

        self.stdout.write(
            f"Legacy list layouts found: {len(rows)} | apply={apply_changes} | "
            f"object_code={object_code or '*'} | organization_id={organization_id or '*'}"
        )

        with transaction.atomic():
            for layout in rows:
                should_archive = bool(layout.is_active or layout.is_default or (layout.status or "").lower() != "archived")
                if not should_archive:
                    stats.unchanged += 1
                    continue

                layout.status = "archived"
                layout.is_active = False
                layout.is_default = False
                if apply_changes:
                    layout.save(update_fields=["status", "is_active", "is_default", "updated_at"])

                stats.archived += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[ARCHIVED:list] layout={layout.id} code={layout.business_object.code} "
                        f"org={layout.organization_id or 'global'}"
                    )
                )

            if not apply_changes:
                transaction.set_rollback(True)

        self.stdout.write(
            f"Summary: scanned={stats.scanned}, archived={stats.archived}, unchanged={stats.unchanged}, apply={apply_changes}"
        )

