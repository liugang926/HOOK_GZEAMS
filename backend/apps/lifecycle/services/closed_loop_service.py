"""
Closed-loop lifecycle services.

Provides:
- Purchase request status synchronization based on downstream receipts/assets
- Cross-object timeline aggregation for purchase requests and receipts
- Lightweight activity logging helpers for lifecycle workflows
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from apps.assets.models import Asset
from apps.assets.services.asset_service import AssetStatusLogService
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptStatus,
    DisposalRequest,
    Maintenance,
    PurchaseRequest,
    PurchaseRequestStatus,
)
from apps.system.activity_log import ActivityLog
from apps.system.services.activity_log_service import ActivityLogService


@dataclass(frozen=True)
class TimelineSource:
    label: str
    code: str
    objects: Iterable[object]


class LifecycleClosedLoopService:
    """Cross-object helpers for lifecycle closed-loop workflows."""

    def log_status_change(self, *, actor, instance, old_status: str, new_status: str, description: str):
        """Persist a standardized status-change activity log."""
        if not actor or instance is None or old_status == new_status:
            return None

        return ActivityLogService.log_action(
            actor=actor,
            action='status_change',
            instance=instance,
            description=description,
            changes=[
                {
                    'fieldCode': 'status',
                    'fieldLabel': 'Status',
                    'oldValue': self._resolve_status_display(instance, old_status),
                    'newValue': self._resolve_status_display(instance, new_status),
                }
            ],
            organization=getattr(instance, 'organization', None),
        )

    def log_custom_action(self, *, actor, instance, description: str, changes: Optional[List[dict]] = None):
        """Persist a custom lifecycle activity event."""
        if not actor or instance is None or not description:
            return None

        return ActivityLogService.log_action(
            actor=actor,
            action='custom',
            instance=instance,
            description=description,
            changes=changes or [],
            organization=getattr(instance, 'organization', None),
        )

    def sync_purchase_request_status(self, purchase_request: PurchaseRequest, actor=None) -> PurchaseRequest:
        """
        Synchronize purchase request status from downstream receipt/build-card progress.

        Rules:
        - If there are linked receipts and request is still approved, move to processing.
        - If all requested items have been received on passed receipts and all qualified items
          have generated assets, move to completed.
        """
        if purchase_request is None:
            return purchase_request

        if purchase_request.status in {
            PurchaseRequestStatus.REJECTED,
            PurchaseRequestStatus.CANCELLED,
            PurchaseRequestStatus.COMPLETED,
        }:
            return purchase_request

        receipts = list(
            purchase_request.receipts.filter(is_deleted=False).prefetch_related('items')
        )
        if not receipts:
            return purchase_request

        requested_totals = {}
        for item in purchase_request.items.filter(is_deleted=False):
            key = self._build_item_key(item.asset_category_id, item.item_name, item.specification, item.brand)
            requested_totals[key] = requested_totals.get(key, 0) + int(item.quantity or 0)

        received_totals = {}
        all_qualified_generated = True
        for receipt in receipts:
            if purchase_request.status == PurchaseRequestStatus.APPROVED:
                self._transition_purchase_request(
                    purchase_request,
                    PurchaseRequestStatus.PROCESSING,
                    actor=actor,
                    description=f'Processing started after receipt {receipt.receipt_no} entered the downstream flow.',
                )

            if receipt.status != AssetReceiptStatus.PASSED:
                continue

            for item in receipt.items.filter(is_deleted=False):
                key = self._build_item_key(item.asset_category_id, item.item_name, item.specification, item.brand)
                received_totals[key] = received_totals.get(key, 0) + int(item.qualified_quantity or 0)
                if int(item.qualified_quantity or 0) > 0 and not item.asset_generated:
                    all_qualified_generated = False

        all_requested_received = all(
            received_totals.get(key, 0) >= quantity
            for key, quantity in requested_totals.items()
        )

        if all_requested_received and all_qualified_generated:
            self._transition_purchase_request(
                purchase_request,
                PurchaseRequestStatus.COMPLETED,
                actor=actor,
                description='Purchase request completed after all received items generated asset cards.',
            )

        return purchase_request

    def build_purchase_request_timeline(self, purchase_request: PurchaseRequest) -> List[dict]:
        """Build a merged timeline across purchase request, receipts, assets, maintenance, and disposal."""
        receipts = list(
            purchase_request.receipts.filter(is_deleted=False).select_related('receiver', 'inspector')
        )
        assets = list(
            Asset.objects.filter(
                Q(source_purchase_request=purchase_request)
                | Q(source_receipt__purchase_request=purchase_request),
                is_deleted=False,
            )
            .select_related('created_by')
            .distinct()
        )
        maintenances = list(
            Maintenance.objects.filter(is_deleted=False, asset__in=assets)
            .select_related('asset', 'reporter', 'created_by')
            .distinct()
        )
        disposal_requests = list(
            DisposalRequest.objects.filter(is_deleted=False, items__asset__in=assets)
            .select_related('applicant', 'created_by')
            .distinct()
        )

        sources = [
            TimelineSource('Purchase Request', 'PurchaseRequest', [purchase_request]),
            TimelineSource('Asset Receipt', 'AssetReceipt', receipts),
            TimelineSource('Asset', 'Asset', assets),
            TimelineSource('Maintenance', 'Maintenance', maintenances),
            TimelineSource('Disposal Request', 'DisposalRequest', disposal_requests),
        ]
        return self._build_timeline_entries(sources)

    def build_receipt_timeline(self, receipt: AssetReceipt) -> List[dict]:
        """Build a merged timeline for a receipt and its downstream objects."""
        assets = list(
            Asset.objects.filter(is_deleted=False, source_receipt=receipt)
            .select_related('created_by')
            .distinct()
        )
        maintenances = list(
            Maintenance.objects.filter(is_deleted=False, asset__in=assets)
            .select_related('asset', 'reporter', 'created_by')
            .distinct()
        )
        disposal_requests = list(
            DisposalRequest.objects.filter(is_deleted=False, items__asset__in=assets)
            .select_related('applicant', 'created_by')
            .distinct()
        )

        purchase_objects = [receipt.purchase_request] if receipt.purchase_request_id else []
        sources = [
            TimelineSource('Asset Receipt', 'AssetReceipt', [receipt]),
            TimelineSource('Purchase Request', 'PurchaseRequest', purchase_objects),
            TimelineSource('Asset', 'Asset', assets),
            TimelineSource('Maintenance', 'Maintenance', maintenances),
            TimelineSource('Disposal Request', 'DisposalRequest', disposal_requests),
        ]
        return self._build_timeline_entries(sources)

    def build_asset_timeline(self, asset: Asset) -> List[dict]:
        """Build a merged timeline for an asset and its upstream/downstream lifecycle records."""
        receipt = getattr(asset, 'source_receipt', None)
        purchase_request = getattr(asset, 'source_purchase_request', None)
        maintenances = list(
            Maintenance.objects.filter(is_deleted=False, asset=asset)
            .select_related('asset', 'reporter', 'created_by')
            .distinct()
        )
        disposal_requests = list(
            DisposalRequest.objects.filter(is_deleted=False, items__asset=asset)
            .select_related('applicant', 'created_by')
            .distinct()
        )

        sources = [
            TimelineSource('Asset', 'Asset', [asset]),
            TimelineSource('Asset Receipt', 'AssetReceipt', [receipt] if receipt else []),
            TimelineSource('Purchase Request', 'PurchaseRequest', [purchase_request] if purchase_request else []),
            TimelineSource('Maintenance', 'Maintenance', maintenances),
            TimelineSource('Disposal Request', 'DisposalRequest', disposal_requests),
        ]
        events = self._build_timeline_entries(sources)
        events.extend(self._build_asset_status_log_events(asset))
        events.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        return events

    def _build_timeline_entries(self, sources: List[TimelineSource]) -> List[dict]:
        model_map = {}
        instance_map = {}
        create_log_keys = set()
        events: List[dict] = []

        for source in sources:
            objects = [obj for obj in source.objects if obj is not None]
            if not objects:
                continue

            model_class = objects[0].__class__
            content_type = ContentType.objects.get_for_model(model_class)
            object_ids = [str(obj.pk) for obj in objects]
            for obj in objects:
                model_map[(content_type.id, str(obj.pk))] = source
                instance_map[(content_type.id, str(obj.pk))] = obj

            logs = (
                ActivityLog.objects.filter(
                    content_type=content_type,
                    object_id__in=object_ids,
                    is_deleted=False,
                )
                .select_related('actor')
                .order_by('-created_at')
            )
            for log in logs:
                source_info = model_map.get((log.content_type_id, log.object_id), source)
                source_instance = instance_map.get((log.content_type_id, log.object_id))
                if log.action == 'create':
                    create_log_keys.add((log.content_type_id, log.object_id))
                events.append(
                    {
                        'id': f'activity-{log.id}',
                        'action': log.action,
                        'actionLabel': log.get_action_display(),
                        'sourceCode': source_info.code,
                        'sourceLabel': source_info.label,
                        'objectCode': self._object_code(source_instance, fallback=source_info.code) if source_instance else source_info.code,
                        'objectId': str(source_instance.pk) if source_instance is not None else str(log.object_id),
                        'recordLabel': self._record_identifier(source_instance) if source_instance is not None else str(log.object_id),
                        'userName': self._user_name(log.actor),
                        'timestamp': log.created_at.isoformat(),
                        'description': self._resolve_log_description(
                            source_label=source_info.label,
                            log=log,
                            instance=source_instance,
                        ),
                        'changes': log.changes or [],
                    }
                )

            for obj in objects:
                if (content_type.id, str(obj.pk)) in create_log_keys:
                    continue
                events.append(self._build_create_event(source.label, source.code, obj))

        events.sort(key=lambda item: item.get('timestamp') or '', reverse=True)
        return events

    def _build_create_event(self, source_label: str, source_code: str, instance) -> dict:
        code = self._object_code(instance, fallback=source_code)
        record_no = self._record_identifier(instance)
        description = f'{source_label} {record_no} created.'
        if source_code == 'Asset':
            description = f'Asset {record_no} generated from lifecycle flow.'
        elif source_code == 'Maintenance':
            description = f'Maintenance {record_no} created for asset {getattr(instance.asset, "asset_code", "-")}.'
        elif source_code == 'DisposalRequest':
            description = f'Disposal request {record_no} created from downstream asset action.'

        return {
            'id': f'synthetic-{code}-{instance.pk}-create',
            'action': 'create',
            'actionLabel': 'Created',
            'sourceCode': source_code,
            'sourceLabel': source_label,
            'objectCode': code,
            'objectId': str(instance.pk),
            'recordLabel': record_no,
            'userName': self._user_name(self._fallback_actor(instance)),
            'timestamp': getattr(instance, 'created_at', None).isoformat() if getattr(instance, 'created_at', None) else '',
            'description': description,
            'changes': [],
        }

    def _build_asset_status_log_events(self, asset: Asset) -> List[dict]:
        logs = AssetStatusLogService().get_asset_history(str(asset.id)).select_related('created_by')
        return [
            {
                'id': f'asset-status-{log.id}',
                'action': 'status_change',
                'actionLabel': 'Status Changed',
                'sourceCode': 'Asset',
                'sourceLabel': 'Asset',
                'objectCode': 'Asset',
                'objectId': str(asset.pk),
                'recordLabel': asset.asset_code,
                'userName': self._user_name(log.created_by),
                'timestamp': log.created_at.isoformat() if log.created_at else '',
                'description': f'[Asset] {log.reason or f"Asset {asset.asset_code} status updated."}',
                'changes': [
                    {
                        'fieldCode': 'asset_status',
                        'fieldLabel': 'Asset Status',
                        'oldValue': log.old_status,
                        'newValue': log.new_status,
                    }
                ],
            }
            for log in logs
        ]

    def _transition_purchase_request(self, purchase_request: PurchaseRequest, new_status: str, *, actor, description: str):
        old_status = purchase_request.status
        if old_status == new_status:
            return

        purchase_request.status = new_status
        purchase_request.save(update_fields=['status', 'updated_at'])
        self.log_status_change(
            actor=actor,
            instance=purchase_request,
            old_status=old_status,
            new_status=new_status,
            description=description,
        )

    def _resolve_status_display(self, instance, value: str) -> str:
        field = instance._meta.get_field('status')
        choices = dict(field.flatchoices)
        return str(choices.get(value, value))

    def _build_item_key(self, category_id, item_name, specification, brand):
        return (
            str(category_id or ''),
            str(item_name or '').strip(),
            str(specification or '').strip(),
            str(brand or '').strip(),
        )

    def _object_code(self, instance, fallback: str) -> str:
        return getattr(instance._meta, 'object_name', fallback)

    def _record_identifier(self, instance) -> str:
        for attr in (
            'request_no',
            'receipt_no',
            'maintenance_no',
            'asset_code',
        ):
            value = getattr(instance, attr, None)
            if value:
                return str(value)
        return str(instance.pk)

    def _fallback_actor(self, instance):
        for attr in ('created_by', 'applicant', 'receiver', 'reporter'):
            actor = getattr(instance, attr, None)
            if actor:
                return actor
        return None

    def _user_name(self, actor) -> Optional[str]:
        if actor is None:
            return None
        full_name = getattr(actor, 'get_full_name', lambda: '')()
        return full_name or getattr(actor, 'username', None)

    def _prefix_description(self, source_label: str, description: Optional[str]) -> Optional[str]:
        if not description:
            return None
        return f'[{source_label}] {description}'

    def _resolve_log_description(self, *, source_label: str, log: ActivityLog, instance) -> Optional[str]:
        if log.description:
            return self._prefix_description(source_label, log.description)
        if log.action == 'create' and instance is not None:
            return self._build_create_event(source_label, self._object_code(instance, fallback=source_label), instance)['description']
        return None
