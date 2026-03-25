"""
Asset Receipt Service

Business service for asset receipt operations including:
- CRUD operations via BaseCRUDService
- Quality inspection workflow
- Asset card generation
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import AssetStatusLog, Supplier
from apps.assets.services.asset_service import AssetService
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
)
from apps.organizations.models import Department
from apps.system.services.activity_log_service import ActivityLogService
from apps.lifecycle.services.closed_loop_service import LifecycleClosedLoopService


class AssetReceiptService(BaseCRUDService):
    """
    Service for Asset Receipt operations.

    Extends BaseCRUDService with receipt workflow methods.
    """

    def __init__(self):
        super().__init__(AssetReceipt)
        self.closed_loop_service = LifecycleClosedLoopService()

    @staticmethod
    def _normalize_detail_numbers(item_data: dict) -> dict:
        payload = dict(item_data or {})
        received_quantity = int(payload.get('received_quantity') or 0)
        qualified_quantity = int(payload.get('qualified_quantity') or 0)

        if 'defective_quantity' not in payload or payload.get('defective_quantity') in (None, ''):
            payload['defective_quantity'] = received_quantity - qualified_quantity

        if 'total_amount' not in payload or payload.get('total_amount') in (None, ''):
            unit_price = Decimal(str(payload.get('unit_price') or '0'))
            payload['total_amount'] = Decimal(str(received_quantity)) * unit_price

        return payload

    def _sync_items(
        self,
        *,
        asset_receipt: AssetReceipt,
        items_data: list[dict],
        organization_id: str,
    ) -> None:
        related_field_names = {
            field.name
            for field in AssetReceiptItem._meta.fields
            if getattr(field, 'many_to_one', False) and field.name != 'asset_receipt'
        }
        existing_items = {
            str(item.id): item
            for item in asset_receipt.items.filter(is_deleted=False)
        }
        prepared_rows: list[tuple[str, dict]] = []

        for index, item_data in enumerate(items_data or [], start=1):
            payload = self._normalize_detail_numbers(item_data)
            item_id = str(payload.pop('id', '') or '').strip()
            payload['sequence'] = index
            payload['organization_id'] = organization_id
            normalized_payload = {}
            for attr, value in payload.items():
                if attr in related_field_names and not hasattr(value, '_meta'):
                    normalized_payload[f'{attr}_id'] = value
                    continue
                normalized_payload[attr] = value
            prepared_rows.append((item_id, normalized_payload))

        submitted_ids = {
            item_id
            for item_id, _normalized_payload in prepared_rows
            if item_id
        }

        for item_id, item in existing_items.items():
            if item_id not in submitted_ids:
                item.delete()

        if submitted_ids:
            for offset, item_id in enumerate(sorted(submitted_ids), start=1):
                item = existing_items.get(item_id)
                if item is None:
                    continue
                item.sequence = 1000000 + offset
                item.save(update_fields=['sequence', 'updated_at'])

        for item_id, normalized_payload in prepared_rows:
            if item_id:
                item = existing_items.get(item_id)
                if item is None:
                    raise ValidationError({
                        'items': f'Asset receipt item {item_id} does not belong to this receipt'
                    })

                for attr, value in normalized_payload.items():
                    if hasattr(item, attr):
                        setattr(item, attr, value)
                item.save()
                continue

            AssetReceiptItem.objects.create(
                asset_receipt=asset_receipt,
                **normalized_payload,
            )

    def create_with_items(
        self,
        data: dict,
        items=None,
        user=None,
        organization_id: str = None,
    ):
        """
        Create asset receipt with items.

        Args:
            data: Dictionary containing receipt data and items
            user: Current user creating the receipt

        Returns:
            Created AssetReceipt instance
        """
        payload = dict(data or {})
        if user is None and items is not None and not isinstance(items, (list, tuple)):
            user = items
            items_data = payload.pop('items', [])
        else:
            items_data = list(items or payload.pop('items', []))

        if user is None:
            raise ValidationError({'user': 'Current user is required'})

        effective_org_id = organization_id or getattr(user, 'organization_id', None)
        if not effective_org_id:
            raise ValidationError({'organization': 'Organization is required'})

        if 'receiver_id' not in payload and 'receiver' not in payload:
            payload['receiver'] = user
        payload['organization_id'] = effective_org_id

        with transaction.atomic():
            asset_receipt = AssetReceipt.objects.create(**payload)
            self._sync_items(
                asset_receipt=asset_receipt,
                items_data=items_data,
                organization_id=str(effective_org_id),
            )

            ActivityLogService.log_create(
                actor=user,
                instance=asset_receipt,
                organization=asset_receipt.organization,
            )
        if asset_receipt.purchase_request_id:
            self.closed_loop_service.sync_purchase_request_status(asset_receipt.purchase_request, actor=user)
        return asset_receipt

    def update_with_items(
        self,
        receipt_id: str,
        data: dict,
        items=None,
        user=None,
        organization_id: str = None,
    ):
        payload = dict(data or {})
        items_data = None if items is None else list(items)
        if items_data is None and 'items' in payload:
            items_data = list(payload.pop('items') or [])

        receipt = self.get(receipt_id)
        effective_org_id = organization_id or getattr(receipt, 'organization_id', None)

        if receipt.status not in [AssetReceiptStatus.DRAFT, AssetReceiptStatus.REJECTED]:
            raise ValidationError({
                'status': f'Cannot edit receipt with status {receipt.get_status_display()}'
            })

        tracked_fields = set(payload.keys())
        before_snapshot = ActivityLogService.snapshot_instance(
            receipt,
            fields=tracked_fields,
        )

        with transaction.atomic():
            for attr, value in payload.items():
                if hasattr(receipt, attr):
                    setattr(receipt, attr, value)
            receipt.save()

            if items_data is not None:
                self._sync_items(
                    asset_receipt=receipt,
                    items_data=items_data,
                    organization_id=str(effective_org_id or ''),
                )

        if user is not None:
            ActivityLogService.log_update(
                actor=user,
                before_snapshot=before_snapshot,
                instance=receipt,
                changed_fields=tracked_fields,
                organization=receipt.organization,
            )
        if receipt.purchase_request_id:
            self.closed_loop_service.sync_purchase_request_status(receipt.purchase_request, actor=user)

        receipt.refresh_from_db()
        return receipt

    def submit_for_inspection(self, receipt_id: str, actor=None):
        """
        Submit asset receipt for inspection.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Updated AssetReceipt instance

        Raises:
            ValidationError: If receipt is not editable for resubmission
        """
        receipt = self.get(receipt_id)

        if receipt.status not in [AssetReceiptStatus.DRAFT, AssetReceiptStatus.REJECTED]:
            raise ValidationError({
                'status': f'Cannot submit receipt with status {receipt.get_status_display()}'
            })

        old_status = receipt.status
        receipt.status = AssetReceiptStatus.INSPECTING
        receipt.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=receipt,
            old_status=old_status,
            new_status=receipt.status,
            description=f'Receipt {receipt.receipt_no} submitted for inspection.',
        )

        return receipt

    def record_inspection_result(self, receipt_id: str, inspector, result: str, passed: bool = True):
        """
        Record inspection result for asset receipt.

        Args:
            receipt_id: Asset receipt ID
            inspector: User performing inspection
            result: Inspection result description
            passed: True if inspection passed, False if rejected

        Returns:
            Updated AssetReceipt instance

        Raises:
            ValidationError: If receipt is not in inspecting status
        """
        receipt = self.get(receipt_id)

        if receipt.status != AssetReceiptStatus.INSPECTING:
            raise ValidationError({
                'status': f'Cannot record inspection for receipt with status {receipt.get_status_display()}'
            })

        receipt.inspector = inspector
        receipt.inspection_result = result

        old_status = receipt.status
        if passed:
            receipt.status = AssetReceiptStatus.PASSED
            receipt.passed_at = timezone.now()
        else:
            receipt.status = AssetReceiptStatus.REJECTED

        receipt.save()
        self.closed_loop_service.log_status_change(
            actor=inspector,
            instance=receipt,
            old_status=old_status,
            new_status=receipt.status,
            description=(
                f'Inspection passed for receipt {receipt.receipt_no}.'
                if passed
                else f'Inspection rejected receipt {receipt.receipt_no}.'
            ),
        )
        if receipt.purchase_request_id:
            self.closed_loop_service.sync_purchase_request_status(receipt.purchase_request, actor=inspector)

        return receipt

    def cancel(self, receipt_id: str, reason: str = None, actor=None):
        """
        Cancel asset receipt.

        Args:
            receipt_id: Asset receipt ID
            reason: Cancellation reason

        Returns:
            Updated AssetReceipt instance
        """
        receipt = self.get(receipt_id)

        if receipt.status in [AssetReceiptStatus.PASSED, AssetReceiptStatus.CANCELLED]:
            raise ValidationError({
                'status': f'Cannot cancel receipt with status {receipt.get_status_display()}'
            })

        old_status = receipt.status
        receipt.status = AssetReceiptStatus.CANCELLED
        receipt.save()
        self.closed_loop_service.log_status_change(
            actor=actor,
            instance=receipt,
            old_status=old_status,
            new_status=receipt.status,
            description=f'Receipt {receipt.receipt_no} cancelled.',
        )
        if receipt.purchase_request_id:
            self.closed_loop_service.sync_purchase_request_status(receipt.purchase_request, actor=actor)

        return receipt

    def generate_asset_cards(self, receipt_id: str, user=None):
        """
        Generate asset cards from passed receipt items.

        Args:
            receipt_id: Asset receipt ID
            user: Optional current user for audit fields

        Returns:
            Dictionary containing receipt and generated asset summary

        Raises:
            ValidationError: If receipt is not passed
        """
        receipt = self.get(receipt_id)

        if receipt.status != AssetReceiptStatus.PASSED:
            raise ValidationError({
                'status': 'Can only generate asset cards from passed receipts'
            })

        asset_service = AssetService()
        actor = user or receipt.receiver
        supplier = self._resolve_supplier(receipt)
        department = self._resolve_department(receipt)
        created_assets = []

        for item in receipt.items.filter(is_deleted=False).order_by('sequence'):
            if not item.asset_generated and item.qualified_quantity > 0:
                for index in range(1, item.qualified_quantity + 1):
                    asset = asset_service.create(
                        {
                            'asset_name': item.item_name,
                            'asset_category': item.asset_category,
                            'specification': item.specification,
                            'brand': item.brand,
                            'model': '',
                            'unit': 'unit',
                            'purchase_price': item.unit_price,
                            'current_value': item.unit_price,
                            'accumulated_depreciation': Decimal('0'),
                            'purchase_date': receipt.receipt_date,
                            'depreciation_start_date': receipt.receipt_date,
                            'supplier': supplier,
                            'supplier_order_no': receipt.m18_purchase_order_no or '',
                            'invoice_no': receipt.delivery_no or '',
                            'department': department,
                            'asset_status': 'idle',
                            'remarks': (
                                f'Generated from receipt {receipt.receipt_no} '
                                f'item #{item.sequence} ({index}/{item.qualified_quantity})'
                            ),
                            'source_receipt': receipt,
                            'source_receipt_item': item,
                            'source_purchase_request': receipt.purchase_request,
                            'organization_id': receipt.organization_id,
                        },
                        actor,
                    )
                    AssetStatusLog.objects.create(
                        organization=receipt.organization,
                        asset=asset,
                        old_status='pending',
                        new_status=asset.asset_status,
                        reason=f'Generated from receipt {receipt.receipt_no}',
                        created_by=actor,
                    )
                    ActivityLogService.log_create(
                        actor=actor,
                        instance=asset,
                        organization=receipt.organization,
                    )
                    created_assets.append(asset)

                item.asset_generated = True
                item.save()

        if created_assets:
            self.closed_loop_service.log_custom_action(
                actor=actor,
                instance=receipt,
                description=f'Generated {len(created_assets)} asset card(s) from receipt {receipt.receipt_no}.',
                changes=[
                    {
                        'fieldCode': 'generated_assets',
                        'fieldLabel': 'Generated Assets',
                        'oldValue': 0,
                        'newValue': len(created_assets),
                    }
                ],
            )
        if receipt.purchase_request_id:
            self.closed_loop_service.sync_purchase_request_status(receipt.purchase_request, actor=actor)

        return {
            'receipt': receipt,
            'generated_assets': created_assets,
            'generated_count': len(created_assets),
            'generated_item_count': sum(
                1
                for item in receipt.items.filter(is_deleted=False)
                if item.asset_generated
            ),
        }

    def _resolve_supplier(self, receipt: AssetReceipt):
        supplier_name = str(receipt.supplier or '').strip()
        if not supplier_name:
            return None

        return Supplier.objects.filter(
            organization_id=receipt.organization_id,
            name=supplier_name,
            is_deleted=False,
        ).first()

    def _resolve_department(self, receipt: AssetReceipt):
        purchase_request = getattr(receipt, 'purchase_request', None)
        if purchase_request is None or purchase_request.department_id is None:
            return None

        request_department = purchase_request.department
        department_code = str(getattr(request_department, 'code', '') or '').strip()
        if not department_code:
            return None

        return Department.objects.filter(
            organization_id=receipt.organization_id,
            code=department_code,
            is_deleted=False,
        ).first()

    def get_by_status(self, status: str, organization_id: str = None):
        """
        Get asset receipts by status.

        Args:
            status: Status to filter by
            organization_id: Filter by organization

        Returns:
            QuerySet of asset receipts with given status
        """
        queryset = AssetReceipt.objects.filter(
            status=status,
            is_deleted=False
        )

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset.order_by('-created_at')

    def get_pending_inspection(self, organization_id: str = None):
        """
        Get all receipts pending inspection.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of receipts awaiting inspection
        """
        return self.get_by_status(AssetReceiptStatus.INSPECTING, organization_id)

    def get_passed_receipts(self, organization_id: str = None):
        """
        Get all passed receipts ready for asset generation.

        Args:
            organization_id: Filter by organization

        Returns:
            QuerySet of passed receipts
        """
        return self.get_by_status(AssetReceiptStatus.PASSED, organization_id)

    def calculate_total_amount(self, receipt_id: str):
        """
        Calculate total amount from receipt items.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Total amount as Decimal
        """
        receipt = self.get(receipt_id)
        return sum(item.total_amount for item in receipt.items.all())

    def get_receipt_items_summary(self, receipt_id: str):
        """
        Get summary of receipt items.

        Args:
            receipt_id: Asset receipt ID

        Returns:
            Dictionary with items summary
        """
        receipt = self.get(receipt_id)
        items = receipt.items.all()
        total_qualified = sum(item.qualified_quantity for item in items)
        generated_items = sum(1 for item in items if item.asset_generated)
        generated_assets = sum(item.qualified_quantity for item in items if item.asset_generated)

        return {
            'total_items': items.count(),
            'total_ordered': sum(item.ordered_quantity for item in items),
            'total_received': sum(item.received_quantity for item in items),
            'total_qualified': total_qualified,
            'total_defective': sum(item.defective_quantity for item in items),
            'total_amount': sum(item.total_amount for item in items),
            'generated_items': generated_items,
            'assets_generated': generated_assets,
            'pending_generation': max(total_qualified - generated_assets, 0),
        }
