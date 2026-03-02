"""
Migrate legacy readonly/detail layouts into shared edit modeOverrides.

Goal:
- Move readonly layout structure into:
  edit.layout_config.modeOverrides.readonly
- Keep form/detail structure unified with one primary layout model.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.system.models import PageLayout


AnyDict = Dict[str, Any]


def _clone_json(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _is_readonly_layout(layout: PageLayout) -> bool:
    mode = (layout.mode or "").strip().lower()
    layout_type = (layout.layout_type or "").strip().lower()
    return mode == "readonly" or layout_type == "detail"


def _is_edit_layout(layout: PageLayout) -> bool:
    mode = (layout.mode or "").strip().lower()
    layout_type = (layout.layout_type or "").strip().lower()
    return mode == "edit" or layout_type == "form"


def _is_search_layout(layout: PageLayout) -> bool:
    mode = (layout.mode or "").strip().lower()
    layout_type = (layout.layout_type or "").strip().lower()
    return mode == "search" or layout_type == "search"


def _is_archived_layout(layout: PageLayout) -> bool:
    return (layout.status or "").strip().lower() == "archived"


def _extract_readonly_override(layout_config: AnyDict) -> AnyDict:
    sections = layout_config.get("sections") if isinstance(layout_config.get("sections"), list) else []
    actions = layout_config.get("actions") if isinstance(layout_config.get("actions"), list) else []
    override: AnyDict = {"sections": _clone_json(sections)}
    if actions:
        override["actions"] = _clone_json(actions)
    return override


def _set_readonly_override(edit_layout_config: AnyDict, override_payload: AnyDict) -> AnyDict:
    next_config = _clone_json(edit_layout_config if isinstance(edit_layout_config, dict) else {})
    existing = next_config.get("modeOverrides")
    if not isinstance(existing, dict):
        snake_existing = next_config.get("mode_overrides")
        existing = _clone_json(snake_existing) if isinstance(snake_existing, dict) else {}

    existing["readonly"] = _clone_json(override_payload)
    next_config["modeOverrides"] = existing
    if "mode_overrides" in next_config:
        del next_config["mode_overrides"]
    return next_config


def _same_json(a: Any, b: Any) -> bool:
    try:
        return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)
    except Exception:
        return a == b


def _resolve_edit_target_for(source: PageLayout, *, create_missing: bool) -> Optional[PageLayout]:
    candidates = PageLayout.objects.filter(
        business_object=source.business_object,
        organization_id=source.organization_id,
        is_deleted=False,
    ).order_by("-is_default", "-updated_at")

    same_priority = candidates.filter(priority=source.priority)
    edit_same_priority = [layout for layout in same_priority if _is_edit_layout(layout)]
    if edit_same_priority:
        return edit_same_priority[0]

    edit_any_priority = [layout for layout in candidates if _is_edit_layout(layout)]
    if edit_any_priority:
        return edit_any_priority[0]

    if not create_missing:
        return None

    code = source.business_object.code
    ts = int(time.time())
    return PageLayout.objects.create(
        business_object=source.business_object,
        organization_id=source.organization_id,
        layout_code=f"{code}_edit_shared_{ts}",
        layout_name=f"{code} Edit Shared",
        layout_type="form",
        mode="edit",
        description="Auto-created for readonly->modeOverrides migration",
        layout_config={"sections": []},
        status="draft",
        version="1.0.0",
        is_default=False,
        is_active=True,
        priority=source.priority or "global",
        context_type="",
    )


@dataclass
class MigrationStats:
    scanned: int = 0
    paired: int = 0
    migrated: int = 0
    archived: int = 0
    search_scanned: int = 0
    search_archived: int = 0
    unchanged: int = 0
    skipped_no_edit_target: int = 0
    skipped_existing_override: int = 0
    created_edit_layouts: int = 0
    default_groups: int = 0
    default_promoted: int = 0
    default_demoted: int = 0


class Command(BaseCommand):
    help = "Migrate readonly/detail PageLayout configs into edit.layout_config.modeOverrides.readonly."

    def add_arguments(self, parser):
        parser.add_argument("--object-code", type=str, default="", help="Filter by business object code (e.g. Asset)")
        parser.add_argument("--organization-id", type=str, default="", help="Filter by organization id")
        parser.add_argument("--limit", type=int, default=0, help="Limit readonly layouts scanned")
        parser.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
        parser.add_argument(
            "--archive-legacy",
            action="store_true",
            help="Archive migrated readonly/detail layouts (status=archived, is_active=false, is_default=false)",
        )
        parser.add_argument(
            "--archive-search",
            action="store_true",
            help="Archive legacy search layouts (status=archived, is_active=false, is_default=false)",
        )
        parser.add_argument(
            "--create-missing-edit",
            action="store_true",
            help="Create an edit layout if no edit target exists for a readonly layout",
        )
        parser.add_argument(
            "--overwrite-existing-readonly-override",
            action="store_true",
            help="Overwrite edit.layout_config.modeOverrides.readonly when already present",
        )
        parser.add_argument(
            "--enforce-single-default-edit",
            action="store_true",
            help="Ensure each object/org/priority has exactly one active default edit/form layout",
        )

    def _iter_sources(self, *, object_code: str, organization_id: str, limit: int) -> Iterable[PageLayout]:
        qs = PageLayout.objects.filter(is_deleted=False).select_related("business_object", "organization")
        if object_code:
            qs = qs.filter(business_object__code=object_code)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        sources = [layout for layout in qs.order_by("business_object__code", "organization_id", "layout_code") if _is_readonly_layout(layout)]
        if limit > 0:
            return sources[:limit]
        return sources

    def _iter_search_sources(self, *, object_code: str, organization_id: str, limit: int) -> Iterable[PageLayout]:
        qs = PageLayout.objects.filter(is_deleted=False).select_related("business_object", "organization")
        if object_code:
            qs = qs.filter(business_object__code=object_code)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        sources = [
            layout
            for layout in qs.order_by("business_object__code", "organization_id", "layout_code")
            if _is_search_layout(layout)
        ]
        if limit > 0:
            return sources[:limit]
        return sources

    def _archive_search_layouts(
        self,
        *,
        object_code: str,
        organization_id: str,
        limit: int,
        apply_changes: bool,
        stats: MigrationStats,
    ) -> None:
        search_sources = list(
            self._iter_search_sources(object_code=object_code, organization_id=organization_id, limit=limit)
        )
        stats.search_scanned = len(search_sources)
        for layout in search_sources:
            should_archive = bool(layout.is_active or layout.is_default or not _is_archived_layout(layout))
            if not should_archive:
                continue

            layout.status = "archived"
            layout.is_active = False
            layout.is_default = False
            if apply_changes:
                layout.save(update_fields=["status", "is_active", "is_default", "updated_at"])
            stats.search_archived += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"[ARCHIVED:search] layout={layout.id} code={layout.business_object.code} "
                    f"org={layout.organization_id or 'global'}"
                )
            )

    def _enforce_single_default_edit(
        self,
        *,
        object_code: str,
        organization_id: str,
        apply_changes: bool,
        stats: MigrationStats,
    ) -> None:
        qs = PageLayout.objects.filter(is_deleted=False).select_related("business_object", "organization")
        if object_code:
            qs = qs.filter(business_object__code=object_code)
        if organization_id:
            qs = qs.filter(organization_id=organization_id)

        candidates = [
            layout
            for layout in qs.order_by("business_object__code", "organization_id", "priority", "-updated_at")
            if _is_edit_layout(layout) and layout.is_active and not _is_archived_layout(layout)
        ]
        grouped: dict[tuple[str, str, str], list[PageLayout]] = defaultdict(list)
        for layout in candidates:
            key = (
                str(layout.business_object_id),
                str(layout.organization_id or ""),
                str(layout.priority or "global"),
            )
            grouped[key].append(layout)

        for _, layouts in grouped.items():
            if not layouts:
                continue
            stats.default_groups += 1

            # Deterministic winner:
            # 1) published > draft
            # 2) already default > non-default
            # 3) most recently updated
            winner = sorted(
                layouts,
                key=lambda x: (
                    1 if (x.status or "").lower() == "published" else 0,
                    1 if x.is_default else 0,
                    x.updated_at.timestamp() if x.updated_at else 0.0,
                ),
                reverse=True,
            )[0]

            if not winner.is_default:
                winner.is_default = True
                if apply_changes:
                    winner.save(update_fields=["is_default", "updated_at"])
                stats.default_promoted += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[DEFAULT:promote] layout={winner.id} code={winner.business_object.code} "
                        f"org={winner.organization_id or 'global'} priority={winner.priority or 'global'}"
                    )
                )

            for layout in layouts:
                if layout.id == winner.id:
                    continue
                if not layout.is_default:
                    continue
                layout.is_default = False
                if apply_changes:
                    layout.save(update_fields=["is_default", "updated_at"])
                stats.default_demoted += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[DEFAULT:demote] layout={layout.id} code={layout.business_object.code} "
                        f"org={layout.organization_id or 'global'} priority={layout.priority or 'global'}"
                    )
                )

    def handle(self, *args, **options):
        object_code = (options.get("object_code") or "").strip()
        organization_id = (options.get("organization_id") or "").strip()
        limit = int(options.get("limit") or 0)
        apply_changes = bool(options.get("apply"))
        archive_legacy = bool(options.get("archive_legacy"))
        archive_search = bool(options.get("archive_search"))
        create_missing_edit = bool(options.get("create_missing_edit"))
        overwrite_existing = bool(options.get("overwrite_existing_readonly_override"))
        enforce_single_default_edit = bool(options.get("enforce_single_default_edit"))

        stats = MigrationStats()
        sources = list(self._iter_sources(object_code=object_code, organization_id=organization_id, limit=limit))

        self.stdout.write(
            f"Readonly sources found: {len(sources)} | apply={apply_changes} "
            f"| archive_legacy={archive_legacy} | archive_search={archive_search} "
            f"| enforce_single_default_edit={enforce_single_default_edit} "
            f"| create_missing_edit={create_missing_edit}"
        )

        with transaction.atomic():
            for source in sources:
                stats.scanned += 1
                target = _resolve_edit_target_for(source, create_missing=create_missing_edit)
                if not target:
                    stats.skipped_no_edit_target += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[SKIP:no-edit] source={source.id} code={source.business_object.code} "
                            f"org={source.organization_id or 'global'}"
                        )
                    )
                    continue

                # Track whether we created this target in this pass.
                if target.created_at == target.updated_at and target.layout_name.endswith("Edit Shared"):
                    stats.created_edit_layouts += 1

                stats.paired += 1

                source_config = source.layout_config if isinstance(source.layout_config, dict) else {}
                target_config = target.layout_config if isinstance(target.layout_config, dict) else {}

                override_payload = _extract_readonly_override(source_config)
                existing_overrides = target_config.get("modeOverrides")
                if not isinstance(existing_overrides, dict):
                    existing_overrides = target_config.get("mode_overrides") if isinstance(target_config.get("mode_overrides"), dict) else {}

                existing_readonly = existing_overrides.get("readonly") if isinstance(existing_overrides, dict) else None
                if existing_readonly is not None and not overwrite_existing:
                    if _same_json(existing_readonly, override_payload):
                        stats.unchanged += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"[UNCHANGED] source={source.id} target={target.id} "
                                f"code={source.business_object.code}"
                            )
                        )
                    else:
                        stats.skipped_existing_override += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"[SKIP:override-exists] source={source.id} target={target.id} "
                                f"code={source.business_object.code} (use --overwrite-existing-readonly-override)"
                            )
                        )
                    continue

                next_target_config = _set_readonly_override(target_config, override_payload)
                if _same_json(next_target_config, target_config):
                    stats.unchanged += 1
                else:
                    target.layout_config = next_target_config
                    if apply_changes:
                        target.save(update_fields=["layout_config", "updated_at"])
                    stats.migrated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[MIGRATED] source={source.id} -> target={target.id} "
                            f"code={source.business_object.code} org={source.organization_id or 'global'}"
                        )
                    )

                if archive_legacy:
                    source.status = "archived"
                    source.is_active = False
                    source.is_default = False
                    if apply_changes:
                        source.save(update_fields=["status", "is_active", "is_default", "updated_at"])
                    stats.archived += 1

            if archive_search:
                self._archive_search_layouts(
                    object_code=object_code,
                    organization_id=organization_id,
                    limit=limit,
                    apply_changes=apply_changes,
                    stats=stats,
                )

            if enforce_single_default_edit:
                self._enforce_single_default_edit(
                    object_code=object_code,
                    organization_id=organization_id,
                    apply_changes=apply_changes,
                    stats=stats,
                )

            if not apply_changes:
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Summary: "
                f"scanned={stats.scanned}, paired={stats.paired}, migrated={stats.migrated}, "
                f"archived={stats.archived}, unchanged={stats.unchanged}, "
                f"search_scanned={stats.search_scanned}, search_archived={stats.search_archived}, "
                f"default_groups={stats.default_groups}, default_promoted={stats.default_promoted}, "
                f"default_demoted={stats.default_demoted}, "
                f"skipped_no_edit_target={stats.skipped_no_edit_target}, "
                f"skipped_existing_override={stats.skipped_existing_override}, "
                f"created_edit_layouts={stats.created_edit_layouts}, apply={apply_changes}"
            )
        )
