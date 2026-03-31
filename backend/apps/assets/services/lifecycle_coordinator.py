"""
Asset lifecycle coordination helpers.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from apps.assets.models import Asset
from apps.assets.services.asset_service import AssetStatusLogService


@dataclass(frozen=True)
class _UnsetValue:
    """Sentinel wrapper used to distinguish omitted values from explicit None."""


UNSET = _UnsetValue()


class AssetLifecycleCoordinatorService:
    """Centralize operational asset state mutations and status logging."""

    def __init__(self):
        self.status_log_service = AssetStatusLogService()

    def apply_state_change(
        self,
        asset: Asset,
        *,
        actor: Any,
        reason: str = '',
        new_status: Any = UNSET,
        custodian: Any = UNSET,
        assigned_user: Any = UNSET,
        department: Any = UNSET,
        location: Any = UNSET,
    ) -> Asset:
        """Apply a coordinated lifecycle update and persist a status log when needed."""
        changed_fields: list[str] = []
        old_status = str(getattr(asset, 'asset_status', '') or '')
        status_changed = new_status is not UNSET and str(new_status or '') != old_status

        if status_changed:
            asset.asset_status = new_status
            changed_fields.append('asset_status')
        if custodian is not UNSET and asset.custodian_id != self._resolve_fk_id(custodian):
            asset.custodian = custodian
            changed_fields.append('custodian')
        if assigned_user is not UNSET and asset.user_id != self._resolve_fk_id(assigned_user):
            asset.user = assigned_user
            changed_fields.append('user')
        if department is not UNSET and asset.department_id != self._resolve_fk_id(department):
            asset.department = department
            changed_fields.append('department')
        if location is not UNSET and asset.location_id != self._resolve_fk_id(location):
            asset.location = location
            changed_fields.append('location')

        if changed_fields:
            asset.save(update_fields=[*changed_fields, 'updated_at'])

        if status_changed and actor is not None:
            self.status_log_service.log_status_change(
                asset=asset,
                old_status=old_status,
                new_status=asset.asset_status,
                user=actor,
                reason=reason,
            )

        return asset

    @staticmethod
    def _resolve_fk_id(value: Any):
        if value is None:
            return None
        return getattr(value, 'id', value)
