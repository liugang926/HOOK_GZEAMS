"""
Synchronization service for built-in catalog-backed business objects.

This service owns the persistence boundary between the static hardcoded object
catalog and BusinessObject rows in the database. It does not handle runtime
registry caching, field metadata, or layout generation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from apps.system.object_catalog import (
    HardcodedObjectDefinition,
    get_hardcoded_object_definition,
    iter_hardcoded_object_definitions,
)
from apps.system.models import BusinessObject


SYSTEM_SEED_SOURCE = "hardcoded_object_catalog"
SYSTEM_SEED_KEY = "system_seed"


@dataclass(frozen=True)
class HardcodedObjectSyncResult:
    business_object: BusinessObject
    created: bool
    updated: bool


class HardcodedObjectSyncService:
    """Persist hardcoded catalog definitions into BusinessObject rows."""

    def get_definition(self, code: str) -> Optional[HardcodedObjectDefinition]:
        return get_hardcoded_object_definition(code)

    def iter_definitions(
        self,
        codes: Optional[Iterable[str]] = None,
    ) -> Iterable[HardcodedObjectDefinition]:
        if codes is None:
            yield from iter_hardcoded_object_definitions()
            return

        for code in codes:
            definition = self.get_definition(code)
            if definition:
                yield definition

    def ensure_business_object(
        self,
        definition: HardcodedObjectDefinition,
        *,
        overwrite_existing: bool = True,
    ) -> HardcodedObjectSyncResult:
        defaults = {
            "name": definition.name,
            "name_en": definition.name_en,
            "is_hardcoded": True,
            "django_model_path": definition.django_model_path,
            "menu_category": definition.menu_category,
            "is_menu_hidden": definition.is_menu_hidden,
            "object_role": definition.object_role,
            "is_top_level_navigable": definition.is_top_level_navigable,
            "allow_standalone_query": definition.allow_standalone_query,
            "allow_standalone_route": definition.allow_standalone_route,
            "inherit_permissions": definition.inherit_permissions,
            "inherit_workflow": definition.inherit_workflow,
            "inherit_status": definition.inherit_status,
            "inherit_lifecycle": definition.inherit_lifecycle,
            "custom_fields": self._build_seed_payload(definition),
        }
        business_object, created = BusinessObject.objects.get_or_create(
            code=definition.code,
            defaults=defaults,
        )

        updated = False
        if not created and overwrite_existing:
            updated = self._update_business_object_defaults(business_object, definition)

        return HardcodedObjectSyncResult(
            business_object=business_object,
            created=created,
            updated=updated,
        )

    def sync_catalog(
        self,
        *,
        codes: Optional[Iterable[str]] = None,
        overwrite_existing: bool = True,
    ) -> list[HardcodedObjectSyncResult]:
        return [
            self.ensure_business_object(definition, overwrite_existing=overwrite_existing)
            for definition in self.iter_definitions(codes=codes)
        ]

    def _build_seed_payload(self, definition: HardcodedObjectDefinition) -> dict:
        return {
            SYSTEM_SEED_KEY: {
                "source": SYSTEM_SEED_SOURCE,
                "code": definition.code,
                "django_model_path": definition.django_model_path,
            }
        }

    def _merge_seed_payload(
        self,
        current_custom_fields: Optional[dict],
        definition: HardcodedObjectDefinition,
    ) -> dict:
        custom_fields = dict(current_custom_fields or {})
        custom_fields[SYSTEM_SEED_KEY] = {
            "source": SYSTEM_SEED_SOURCE,
            "code": definition.code,
            "django_model_path": definition.django_model_path,
        }
        return custom_fields

    def _update_business_object_defaults(
        self,
        business_object: BusinessObject,
        definition: HardcodedObjectDefinition,
    ) -> bool:
        updated_fields: list[str] = []

        if business_object.name != definition.name:
            business_object.name = definition.name
            updated_fields.append("name")
        if business_object.name_en != definition.name_en:
            business_object.name_en = definition.name_en
            updated_fields.append("name_en")
        if not business_object.is_hardcoded:
            business_object.is_hardcoded = True
            updated_fields.append("is_hardcoded")
        if business_object.django_model_path != definition.django_model_path:
            business_object.django_model_path = definition.django_model_path
            updated_fields.append("django_model_path")
        if business_object.menu_category != definition.menu_category:
            business_object.menu_category = definition.menu_category
            updated_fields.append("menu_category")
        if business_object.is_menu_hidden != definition.is_menu_hidden:
            business_object.is_menu_hidden = definition.is_menu_hidden
            updated_fields.append("is_menu_hidden")
        if business_object.object_role != definition.object_role:
            business_object.object_role = definition.object_role
            updated_fields.append("object_role")
        if business_object.is_top_level_navigable != definition.is_top_level_navigable:
            business_object.is_top_level_navigable = definition.is_top_level_navigable
            updated_fields.append("is_top_level_navigable")
        if business_object.allow_standalone_query != definition.allow_standalone_query:
            business_object.allow_standalone_query = definition.allow_standalone_query
            updated_fields.append("allow_standalone_query")
        if business_object.allow_standalone_route != definition.allow_standalone_route:
            business_object.allow_standalone_route = definition.allow_standalone_route
            updated_fields.append("allow_standalone_route")
        if business_object.inherit_permissions != definition.inherit_permissions:
            business_object.inherit_permissions = definition.inherit_permissions
            updated_fields.append("inherit_permissions")
        if business_object.inherit_workflow != definition.inherit_workflow:
            business_object.inherit_workflow = definition.inherit_workflow
            updated_fields.append("inherit_workflow")
        if business_object.inherit_status != definition.inherit_status:
            business_object.inherit_status = definition.inherit_status
            updated_fields.append("inherit_status")
        if business_object.inherit_lifecycle != definition.inherit_lifecycle:
            business_object.inherit_lifecycle = definition.inherit_lifecycle
            updated_fields.append("inherit_lifecycle")

        merged_custom_fields = self._merge_seed_payload(business_object.custom_fields, definition)
        if merged_custom_fields != (business_object.custom_fields or {}):
            business_object.custom_fields = merged_custom_fields
            updated_fields.append("custom_fields")

        if not updated_fields:
            return False

        business_object.save(update_fields=updated_fields + ["updated_at"])
        return True
