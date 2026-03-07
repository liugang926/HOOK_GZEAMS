"""
Dynamic menu viewset backed by the standardized menu configuration model.
"""
from __future__ import annotations

from typing import Any, Dict, List

from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from apps.common.responses.base import BaseResponse
from apps.system.menu_config import (
    MENU_GROUPS,
    STATIC_MENU_ITEMS,
    build_menu_config_for_object,
    get_menu_group_definition,
)
from apps.system.models import BusinessObject


class MenuViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BusinessObject.objects.filter(is_deleted=False).order_by("code")

    def _build_group_bucket(self, group_code: str) -> Dict[str, Any]:
        group = get_menu_group_definition(group_code)
        return {
            "code": group_code,
            "name": group_code,
            "translation_key": group["translation_key"],
            "order": int(group["order"]),
            "icon": group["icon"],
            "items": [],
        }

    def _append_item(
        self,
        groups: Dict[str, Dict[str, Any]],
        flat_items: List[Dict[str, Any]],
        item: Dict[str, Any],
    ) -> None:
        group_code = str(item["group_code"])
        bucket = groups.setdefault(group_code, self._build_group_bucket(group_code))
        bucket["items"].append(item)
        flat_items.append(item)

    def list(self, request, *args, **kwargs):
        groups: Dict[str, Dict[str, Any]] = {}
        flat_items: List[Dict[str, Any]] = []

        for obj in self.get_queryset():
            menu_config = build_menu_config_for_object(obj.code, obj.menu_config or {})
            if not menu_config.get("show_in_menu", True):
                continue

            item = {
                "code": obj.code,
                "name": obj.name,
                "name_en": obj.name_en,
                "url": menu_config.get("url") or f"/objects/{obj.code}",
                "icon": menu_config.get("icon", "Document"),
                "order": int(menu_config.get("item_order", 999)),
                "group": menu_config.get("group_code", "other"),
                "group_code": menu_config.get("group_code", "other"),
                "group_translation_key": menu_config.get("group_translation_key"),
                "translation_key": menu_config.get("translation_key"),
                "badge": menu_config.get("badge"),
            }
            self._append_item(groups, flat_items, item)

        for static_item in STATIC_MENU_ITEMS:
            group = get_menu_group_definition(static_item["group_code"])
            item = {
                "code": static_item["code"],
                "name": static_item["code"],
                "url": static_item["url"],
                "icon": static_item["icon"],
                "order": int(static_item["item_order"]),
                "group": static_item["group_code"],
                "group_code": static_item["group_code"],
                "group_translation_key": group["translation_key"],
                "translation_key": static_item["translation_key"],
                "badge": static_item.get("badge"),
            }
            self._append_item(groups, flat_items, item)

        grouped_list = sorted(groups.values(), key=lambda value: value["order"])
        for group in grouped_list:
            group["items"].sort(key=lambda value: (int(value.get("order", 999)), value["code"]))

        return BaseResponse.success({"groups": grouped_list, "items": flat_items})

    @action(detail=False, methods=["get"], url_path="flat")
    def flat(self, request, *args, **kwargs):
        payload = self.list(request, *args, **kwargs).data["data"]
        return BaseResponse.success(payload["items"])

    @action(detail=False, methods=["get"], url_path="config")
    def config(self, request, *args, **kwargs):
        schema = {
            "menu_config": {
                "show_in_menu": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to show this business object in the main menu.",
                },
                "group_code": {
                    "type": "string",
                    "default": "other",
                    "description": "Stable menu group identifier.",
                },
                "group_translation_key": {
                    "type": "string",
                    "default": "menu.categories.other",
                    "description": "i18n key used to render the group label.",
                },
                "group_order": {
                    "type": "integer",
                    "default": 999,
                    "description": "Group display order.",
                },
                "group_icon": {
                    "type": "string",
                    "default": "Menu",
                    "description": "Element Plus icon used for the group.",
                },
                "item_order": {
                    "type": "integer",
                    "default": 999,
                    "description": "Menu item order within the group.",
                },
                "translation_key": {
                    "type": "string",
                    "default": None,
                    "description": "Optional i18n key used to render the item label.",
                },
                "icon": {
                    "type": "string",
                    "default": "Document",
                    "description": "Element Plus icon used for the item.",
                },
                "url": {
                    "type": "string",
                    "default": None,
                    "description": "Optional custom URL. Defaults to /objects/{code}.",
                },
                "badge": {
                    "type": "object",
                    "default": None,
                    "description": "Optional badge payload.",
                },
            }
        }

        common_groups = [
            {
                "code": code,
                "order": group["order"],
                "icon": group["icon"],
                "translation_key": group["translation_key"],
            }
            for code, group in sorted(MENU_GROUPS.items(), key=lambda item: item[1]["order"])
        ]

        return BaseResponse.success(
            {
                "schema": schema,
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
                ],
            }
        )

