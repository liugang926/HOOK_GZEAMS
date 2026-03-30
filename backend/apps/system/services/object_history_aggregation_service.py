from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.assets.services import AssetStatusLogService
from apps.system.models import BusinessObject
from apps.system.object_catalog import get_hardcoded_object_definition
from apps.system.services.activity_log_service import ActivityLogService


class ObjectHistoryAggregationService:
    """Aggregate detail-page history entries across activity and audit sources."""

    def build_history(
        self,
        *,
        object_code: str,
        instance,
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        items.extend(self._build_activity_entries(object_code=object_code, instance=instance))

        if object_code == "Asset":
            items.extend(self._build_asset_status_entries(asset=instance))
            items.extend(self._build_configuration_change_entries(asset=instance))
        elif object_code == "ITAsset":
            asset = getattr(instance, "asset", None)
            if asset is not None:
                items.extend(self._build_configuration_change_entries(asset=asset))

        items.sort(
            key=lambda item: (
                str(item.get("createdAt") or item.get("timestamp") or ""),
                str(item.get("id") or ""),
            ),
            reverse=True,
        )
        return items

    def _build_activity_entries(self, *, object_code: str, instance) -> List[Dict[str, Any]]:
        source_label = self._resolve_object_label(object_code)
        record_label = self._resolve_record_label(instance)

        return [
            {
                "id": f"activity-{activity_log.id}",
                "action": str(activity_log.action or "update"),
                "sourceCode": object_code,
                "sourceLabel": source_label,
                "objectCode": object_code,
                "objectId": str(instance.pk),
                "recordLabel": record_label,
                "userName": self._resolve_user_name(getattr(activity_log, "actor", None)),
                "createdAt": activity_log.created_at.isoformat() if activity_log.created_at else None,
                "timestamp": activity_log.created_at.isoformat() if activity_log.created_at else None,
                "description": activity_log.description or "",
                "changes": activity_log.changes or [],
            }
            for activity_log in ActivityLogService.get_object_timeline(instance)
        ]

    def _build_asset_status_entries(self, *, asset) -> List[Dict[str, Any]]:
        record_label = self._resolve_record_label(asset)
        logs = AssetStatusLogService().get_asset_history(str(asset.id)).select_related("created_by")

        return [
            {
                "id": f"asset-status-{log.id}",
                "action": "status_change",
                "sourceCode": "AssetStatusLog",
                "sourceLabel": self._resolve_object_label("AssetStatusLog"),
                "recordLabel": record_label,
                "userName": self._resolve_user_name(getattr(log, "created_by", None)),
                "createdAt": log.created_at.isoformat() if log.created_at else None,
                "timestamp": log.created_at.isoformat() if log.created_at else None,
                "description": log.reason or "",
                "changes": [
                    {
                        "fieldCode": "asset_status",
                        "fieldLabel": "Asset Status",
                        "oldValue": log.old_status,
                        "newValue": log.new_status,
                    }
                ],
            }
            for log in logs
        ]

    def _build_configuration_change_entries(self, *, asset) -> List[Dict[str, Any]]:
        from apps.it_assets.models import ConfigurationChange

        record_label = self._resolve_record_label(asset)
        changes = (
            ConfigurationChange.objects
            .filter(asset=asset, is_deleted=False)
            .select_related("changed_by", "created_by")
            .order_by("-created_at", "-change_date")
        )

        return [
            {
                "id": f"configuration-change-{change.id}",
                "action": "update",
                "sourceCode": "ConfigurationChange",
                "sourceLabel": self._resolve_object_label("ConfigurationChange"),
                "recordLabel": record_label,
                "userName": self._resolve_user_name(
                    getattr(change, "changed_by", None) or getattr(change, "created_by", None)
                ),
                "createdAt": change.created_at.isoformat() if change.created_at else None,
                "timestamp": change.created_at.isoformat() if change.created_at else None,
                "description": change.change_reason or "",
                "changes": [
                    {
                        "fieldCode": change.field_name,
                        "fieldLabel": self._humanize_field_label(change.field_name),
                        "oldValue": change.old_value,
                        "newValue": change.new_value,
                    }
                ],
            }
            for change in changes
        ]

    def _resolve_object_label(self, object_code: str) -> str:
        business_object = (
            BusinessObject.objects
            .filter(code=object_code, is_deleted=False)
            .only("name")
            .first()
        )
        if business_object and business_object.name:
            return str(business_object.name)

        definition = get_hardcoded_object_definition(object_code)
        if definition is not None and definition.name:
            return str(definition.name)

        return self._humanize_field_label(object_code)

    def _resolve_record_label(self, instance) -> str:
        for field_name in ("asset_code", "asset_name", "request_no", "receipt_no", "code", "name", "title"):
            value = getattr(instance, field_name, None)
            if value not in (None, ""):
                return str(value)
        return str(getattr(instance, "pk", "") or "")

    @staticmethod
    def _resolve_user_name(user) -> str:
        if user is None:
            return ""
        full_name = ""
        try:
            full_name = user.get_full_name() or ""
        except Exception:
            full_name = ""
        return full_name or str(getattr(user, "username", "") or "")

    @staticmethod
    def _humanize_field_label(value: Optional[str]) -> str:
        normalized = str(value or "").replace("-", " ").replace("_", " ").strip()
        return normalized.title() if normalized else ""
