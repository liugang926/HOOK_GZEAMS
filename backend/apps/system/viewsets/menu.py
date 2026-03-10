"""
Unified menu viewset backed by MenuGroup / MenuEntry models.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action

from apps.common.responses.base import BaseResponse
from apps.system.menu_config import (
    MENU_GROUPS,
    build_menu_config_for_object,
    get_menu_group_definitions,
    get_menu_item_identity,
    get_object_translation_key,
    sync_menu_registry_models,
)
from apps.system.models import BusinessObject, MenuEntry, MenuGroup, Translation


class MenuViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    MENU_GROUP_CONTENT_TYPE = "system.menugroup"

    def get_queryset(self):
        return BusinessObject.objects.filter(is_deleted=False).order_by("code")

    def _get_requested_locale(self) -> str:
        raw = str(self.request.headers.get("Accept-Language") or "zh-CN").strip()
        return raw.split(",")[0].strip() or "zh-CN"

    def _get_group_locale_names(self, groups: List[MenuGroup]) -> Dict[str, Dict[str, str]]:
        if not groups:
            return {}

        content_type = ContentType.objects.get_for_model(MenuGroup, for_concrete_model=False)
        rows = (
            Translation.objects
            .filter(
                content_type=content_type,
                object_id__in=[group.id for group in groups],
                field_name="name",
                is_deleted=False,
            )
            .values("object_id", "language_code", "text")
        )

        locale_names: Dict[str, Dict[str, str]] = {}
        for row in rows:
            locale_names.setdefault(str(row["object_id"]), {})[row["language_code"]] = row["text"]
        return locale_names

    def _resolve_group_name(self, group: MenuGroup, locale_names: Dict[str, str] | None = None) -> str:
        locale_names = locale_names or {}
        requested_locale = self._get_requested_locale()
        if locale_names.get(requested_locale):
            return locale_names[requested_locale]

        if requested_locale != "en-US" and locale_names.get("en-US"):
            return locale_names["en-US"]

        if locale_names.get("zh-CN"):
            return locale_names["zh-CN"]

        return group.name

    def _serialize_entry(self, entry: MenuEntry) -> Dict[str, Any]:
        business_object = entry.business_object
        name = business_object.name if business_object else entry.name
        name_en = business_object.name_en if business_object and business_object.name_en else entry.name_en

        return {
            "code": entry.code,
            "name": name,
            "name_en": name_en,
            "url": entry.route_path,
            "icon": entry.icon,
            "order": int(entry.sort_order),
            "group": entry.menu_group.code,
            "group_code": entry.menu_group.code,
            "group_translation_key": entry.menu_group.translation_key,
            "translation_key": entry.translation_key,
            "badge": None,
        }

    def _serialize_management_entry(self, entry: MenuEntry) -> Dict[str, Any]:
        business_object = entry.business_object
        return {
            "code": entry.code,
            "name": business_object.name if business_object else entry.name,
            "name_en": business_object.name_en if business_object and business_object.name_en else entry.name_en,
            "translation_key": entry.translation_key,
            "source_type": entry.source_type,
            "source_code": entry.source_code,
            "path": entry.route_path,
            "icon": entry.icon,
            "group_code": entry.menu_group.code,
            "group_translation_key": entry.menu_group.translation_key,
            "order": int(entry.sort_order),
            "is_visible": bool(entry.is_visible),
            "is_locked": bool(entry.is_locked),
            "is_default": bool(entry.is_system),
            "supports_delete": not bool(entry.is_locked),
            "supports_visibility": True,
            "supports_reorder": True,
            "supports_group_change": True,
        }

    def _serialize_group(
        self,
        group: MenuGroup,
        entry_count: int = 0,
        locale_names: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        resolved_locale_names = locale_names or {}
        return {
            "id": str(group.id),
            "code": group.code,
            "name": self._resolve_group_name(group, resolved_locale_names),
            "translation_key": group.translation_key,
            "locale_names": resolved_locale_names,
            "order": int(group.sort_order),
            "icon": group.icon,
            "is_visible": bool(group.is_visible),
            "is_default": bool(group.is_system),
            "is_locked": bool(group.is_locked),
            "entry_count": int(entry_count),
            "supports_delete": True,
            "translation_target": {
                "content_type": self.MENU_GROUP_CONTENT_TYPE,
                "content_type_model": "menugroup",
                "object_id": str(group.id),
                "field_name": "name",
            },
        }

    def _get_active_groups(self):
        return list(MenuGroup.objects.filter(is_deleted=False).order_by("sort_order", "code"))

    def _get_active_entries(self):
        return list(
            MenuEntry.objects
            .filter(is_deleted=False)
            .select_related("menu_group", "business_object")
            .order_by("menu_group__sort_order", "sort_order", "code")
        )

    def list(self, request, *args, **kwargs):
        sync_menu_registry_models()
        groups = [group for group in self._get_active_groups() if group.is_visible]
        allowed_group_codes = {group.code for group in groups}
        locale_names_by_group_id = self._get_group_locale_names(groups)
        grouped: Dict[str, Dict[str, Any]] = {}
        flat_items: List[Dict[str, Any]] = []

        for group in groups:
            grouped[group.code] = {
                **self._serialize_group(
                    group,
                    locale_names=locale_names_by_group_id.get(str(group.id), {}),
                ),
                "items": [],
            }

        for entry in self._get_active_entries():
            if not entry.is_visible:
                continue
            if entry.menu_group.code not in allowed_group_codes:
                continue
            item = self._serialize_entry(entry)
            grouped[entry.menu_group.code]["items"].append(item)
            flat_items.append(item)

        grouped_list = [group for group in grouped.values() if group["items"]]
        for group in grouped_list:
            group["items"].sort(key=lambda value: (int(value.get("order", 999)), value["code"]))
        grouped_list.sort(key=lambda value: (int(value["order"]), value["code"]))

        return BaseResponse.success({"groups": grouped_list, "items": flat_items})

    @action(detail=False, methods=["get"], url_path="flat")
    def flat(self, request, *args, **kwargs):
        payload = self.list(request, *args, **kwargs).data["data"]
        return BaseResponse.success(payload["items"])

    @action(detail=False, methods=["get"], url_path="config")
    def config(self, request, *args, **kwargs):
        sync_menu_registry_models()
        common_groups = [
            {
                "code": code,
                "order": group["order"],
                "icon": group["icon"],
                "translation_key": group["translation_key"],
                "is_visible": definition.get("is_visible", True),
                "is_default": definition.get("is_default", True),
            }
            for code, definition in sorted(
                get_menu_group_definitions().items(),
                key=lambda item: (item[1]["order"], item[0]),
            )
            for group in [MENU_GROUPS.get(code, {"order": definition["order"], "icon": definition["icon"], "translation_key": definition["translation_key"]})]
        ]

        return BaseResponse.success(
            {
                "schema": {
                    "menu_config": {
                        "show_in_menu": {"type": "boolean", "default": True},
                        "group_code": {"type": "string", "default": "other"},
                        "item_order": {"type": "integer", "default": 999},
                        "icon": {"type": "string", "default": "Document"},
                        "url": {"type": "string", "default": None},
                        "translation_key": {"type": "string", "default": None},
                    }
                },
                "common_groups": common_groups,
                "common_icons": [
                    "Document",
                    "Folder",
                    "FolderOpened",
                    "Menu",
                    "Setting",
                    "Odometer",
                    "Goods",
                    "Box",
                    "Wallet",
                    "User",
                    "Tickets",
                    "Calendar",
                    "Clock",
                    "Bell",
                    "ChatDotRound",
                    "Message",
                    "DataLine",
                    "PieChart",
                    "TrendCharts",
                    "Monitor",
                    "Grid",
                    "Brush",
                    "Files",
                ],
            }
        )

    @action(detail=False, methods=["get", "put"], url_path="management")
    def management(self, request, *args, **kwargs):
        if request.method.lower() == "put":
            return self._update_management(request)
        return self._get_management()

    def _get_management(self):
        sync_menu_registry_models()
        groups = self._get_active_groups()
        entries = self._get_active_entries()
        locale_names_by_group_id = self._get_group_locale_names(groups)
        entry_counts: Dict[str, int] = {}
        for entry in entries:
            entry_counts[entry.menu_group.code] = entry_counts.get(entry.menu_group.code, 0) + 1

        return BaseResponse.success(
            {
                "categories": [
                    self._serialize_group(
                        group,
                        entry_counts.get(group.code, 0),
                        locale_names_by_group_id.get(str(group.id), {}),
                    )
                    for group in groups
                ],
                "items": [self._serialize_management_entry(entry) for entry in entries],
            }
        )

    def _validate_category_payload(self, categories_payload: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], List[str] | None]:
        normalized: Dict[str, Dict[str, Any]] = {}

        for category in categories_payload:
            code = str(category.get("code") or "").strip()
            if not code:
                return {}, ["Menu category code cannot be empty."]
            if code in normalized:
                return {}, [f"Duplicate menu category code '{code}'."]
            locale_names = category.get("locale_names") if isinstance(category.get("locale_names"), dict) else {}
            normalized_locale_names = {
                str(locale): str(text or "").strip()
                for locale, text in locale_names.items()
                if str(locale).strip()
            }
            normalized[code] = {
                "code": code,
                "name": str(category.get("name") or code).strip() or code,
                "locale_names": normalized_locale_names,
                "icon": str(category.get("icon") or "Menu").strip() or "Menu",
                "order": int(category.get("order") or 999),
                "is_visible": bool(category.get("is_visible", True)),
                "is_default": code in MENU_GROUPS,
            }

        return normalized, None

    def _sync_group_translations(
        self,
        group: MenuGroup,
        locale_names: Dict[str, str],
        user,
    ) -> None:
        content_type = ContentType.objects.get_for_model(MenuGroup, for_concrete_model=False)
        existing = {
            translation.language_code: translation
            for translation in Translation.objects.filter(
                content_type=content_type,
                object_id=group.id,
                field_name="name",
                is_deleted=False,
            )
        }

        for locale, text in locale_names.items():
            cleaned_text = str(text or "").strip()
            current = existing.get(locale)
            if not cleaned_text:
                if current:
                    current.soft_delete(user=user)
                continue

            if current:
                if current.text != cleaned_text:
                    current.text = cleaned_text
                    current.type = "object_field"
                    current.updated_by = user
                    current.save(update_fields=["text", "type", "updated_by", "updated_at"])
                continue

            Translation.objects.create(
                content_type=content_type,
                object_id=group.id,
                field_name="name",
                language_code=locale,
                text=cleaned_text,
                type="object_field",
                created_by=user,
                updated_by=user,
            )

    def _update_business_object_menu_config(self, entry: MenuEntry):
        if not entry.business_object:
            return

        legacy = build_menu_config_for_object(entry.business_object.code, entry.business_object.menu_config or {})
        legacy.update(
            {
                "show_in_menu": bool(entry.is_visible),
                "group_code": entry.menu_group.code,
                "group_translation_key": entry.menu_group.translation_key,
                "group_order": int(entry.menu_group.sort_order),
                "group_icon": entry.menu_group.icon,
                "item_order": int(entry.sort_order),
                "icon": entry.icon,
                "translation_key": entry.translation_key or get_object_translation_key(entry.business_object.code),
                "url": entry.route_path,
            }
        )
        entry.business_object.menu_config = legacy
        entry.business_object.save(update_fields=["menu_config"])

    def _update_management(self, request):
        sync_menu_registry_models()
        payload = request.data if isinstance(request.data, dict) else {}
        categories_payload = payload.get("categories") if isinstance(payload.get("categories"), list) else []
        items_payload = payload.get("items") if isinstance(payload.get("items"), list) else []

        category_data, errors = self._validate_category_payload(categories_payload)
        if errors:
            return BaseResponse.error(
                code="VALIDATION_ERROR",
                message="; ".join(errors),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        existing_groups = {group.code: group for group in self._get_active_groups()}
        existing_entries = {
            get_menu_item_identity(entry.source_type, entry.source_code): entry
            for entry in self._get_active_entries()
        }

        for code, data in category_data.items():
            group = existing_groups.get(code)
            if group is None:
                group = MenuGroup.all_objects.filter(code=code).first()
                if group is None:
                    group = MenuGroup(
                        code=code,
                        name=data["name"],
                        translation_key="" if code not in MENU_GROUPS else MENU_GROUPS[code]["translation_key"],
                        icon=data["icon"],
                        sort_order=int(data["order"]),
                        is_visible=bool(data["is_visible"]),
                        is_locked=False,
                        is_system=code in MENU_GROUPS,
                    )
                else:
                    group.is_deleted = False
                    group.deleted_at = None
                    group.deleted_by = None
                    group.name = data["name"]
                    group.icon = data["icon"]
                    group.sort_order = int(data["order"])
                    group.is_visible = bool(data["is_visible"])
                    group.is_locked = False
                    group.is_system = code in MENU_GROUPS
                group.save()
                self._sync_group_translations(group, data["locale_names"], getattr(request, "user", None))
                existing_groups[code] = group
                continue

            changed_fields: List[str] = []
            if group.name != data["name"]:
                group.name = data["name"]
                changed_fields.append("name")
            if group.icon != data["icon"]:
                group.icon = data["icon"]
                changed_fields.append("icon")
            if int(group.sort_order) != int(data["order"]):
                group.sort_order = int(data["order"])
                changed_fields.append("sort_order")
            if bool(group.is_visible) != bool(data["is_visible"]):
                group.is_visible = bool(data["is_visible"])
                changed_fields.append("is_visible")
            if changed_fields:
                group.save(update_fields=changed_fields)
            self._sync_group_translations(group, data["locale_names"], getattr(request, "user", None))

        payload_group_codes = set(category_data.keys())
        removed_custom_groups = [
            group for code, group in existing_groups.items()
            if code not in payload_group_codes
        ]

        for item in items_payload:
            source_type = str(item.get("source_type") or "").strip()
            source_code = str(item.get("source_code") or item.get("code") or "").strip()
            identity = get_menu_item_identity(source_type, source_code)
            entry = existing_entries.get(identity)
            if entry is None:
                return BaseResponse.error(
                    code="VALIDATION_ERROR",
                    message=f"Menu entry '{identity}' does not exist.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            target_group_code = str(item.get("group_code") or "").strip()
            target_group = existing_groups.get(target_group_code)
            if target_group is None or target_group.is_deleted:
                return BaseResponse.error(
                    code="VALIDATION_ERROR",
                    message=f"Menu category '{target_group_code}' does not exist.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )

            changed_fields: List[str] = []
            if entry.menu_group_id != target_group.id:
                entry.menu_group = target_group
                changed_fields.append("menu_group")
            desired_order = int(item.get("order") or 999)
            if int(entry.sort_order) != desired_order:
                entry.sort_order = desired_order
                changed_fields.append("sort_order")
            desired_visible = bool(item.get("is_visible", True))
            if bool(entry.is_visible) != desired_visible:
                entry.is_visible = desired_visible
                changed_fields.append("is_visible")
            if changed_fields:
                entry.save(update_fields=changed_fields)
                if entry.source_type == "business_object":
                    self._update_business_object_menu_config(entry)

        for group in removed_custom_groups:
            active_entry_count = MenuEntry.objects.filter(menu_group=group, is_deleted=False).count()
            if active_entry_count > 0:
                return BaseResponse.error(
                    code="VALIDATION_ERROR",
                    message=f"Menu category '{group.code}' still has {active_entry_count} entries. Move them before deleting the category.",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )
            group.soft_delete(user=getattr(request, "user", None))

        return self._get_management()
