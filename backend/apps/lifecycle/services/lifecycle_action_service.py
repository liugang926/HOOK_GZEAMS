"""
Lifecycle cross-object action service.

Provides a unified action protocol for key lifecycle transitions that create
or trigger records across business objects.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.assets.models import Asset
from apps.assets.services.operation_service import (
    AssetLoanService,
    AssetPickupService,
    AssetReturnService,
    AssetTransferService,
)
from apps.assets.models import Location
from apps.finance.services import FinanceVoucherService
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptStatus,
    DisposalReason,
    DisposalType,
    MaintenancePriority,
    PurchaseRequest,
    PurchaseRequestStatus,
)
from apps.lifecycle.services.disposal_service import DisposalRequestService
from apps.lifecycle.services.maintenance_service import MaintenanceService
from apps.lifecycle.services.purchase_service import PurchaseRequestService
from apps.lifecycle.services.receipt_service import AssetReceiptService
from apps.organizations.models import Department
from apps.organizations.models import Organization


class LifecycleActionService:
    """
    Unified cross-object action service for lifecycle objects.

    Phase 1 covers:
    - PurchaseRequest -> AssetReceipt
    - AssetReceipt -> generate assets
    - Asset -> Maintenance
    - Asset -> DisposalRequest
    """

    PURCHASE_CREATE_RECEIPT = 'purchase.create_receipt'
    PURCHASE_GENERATE_FINANCE = 'purchase.generate_finance_voucher'
    RECEIPT_GENERATE_ASSETS = 'receipt.generate_assets'
    RECEIPT_GENERATE_FINANCE = 'receipt.generate_finance_voucher'
    ASSET_CREATE_PICKUP = 'asset.create_pickup'
    ASSET_CREATE_TRANSFER = 'asset.create_transfer'
    ASSET_CREATE_RETURN = 'asset.create_return'
    ASSET_CREATE_LOAN = 'asset.create_loan'
    ASSET_CREATE_MAINTENANCE = 'asset.create_maintenance'
    ASSET_CREATE_DISPOSAL = 'asset.create_disposal'

    def list_actions(self, *, object_code: str, instance: Any, user) -> List[Dict[str, Any]]:
        handlers = {
            'PurchaseRequest': self._list_purchase_request_actions,
            'AssetReceipt': self._list_asset_receipt_actions,
            'Asset': self._list_asset_actions,
        }
        handler = handlers.get(str(object_code or '').strip())
        if not handler:
            return []
        return handler(instance=instance, user=user)

    def execute_action(
        self,
        *,
        object_code: str,
        action_code: str,
        instance: Any,
        user,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = payload or {}
        action_map = {
            ('PurchaseRequest', self.PURCHASE_CREATE_RECEIPT): self._execute_purchase_create_receipt,
            ('PurchaseRequest', self.PURCHASE_GENERATE_FINANCE): self._execute_purchase_generate_finance_voucher,
            ('AssetReceipt', self.RECEIPT_GENERATE_ASSETS): self._execute_receipt_generate_assets,
            ('AssetReceipt', self.RECEIPT_GENERATE_FINANCE): self._execute_receipt_generate_finance_voucher,
            ('Asset', self.ASSET_CREATE_PICKUP): self._execute_asset_create_pickup,
            ('Asset', self.ASSET_CREATE_TRANSFER): self._execute_asset_create_transfer,
            ('Asset', self.ASSET_CREATE_RETURN): self._execute_asset_create_return,
            ('Asset', self.ASSET_CREATE_LOAN): self._execute_asset_create_loan,
            ('Asset', self.ASSET_CREATE_MAINTENANCE): self._execute_asset_create_maintenance,
            ('Asset', self.ASSET_CREATE_DISPOSAL): self._execute_asset_create_disposal,
        }
        handler = action_map.get((str(object_code or '').strip(), str(action_code or '').strip()))
        if not handler:
            raise ValidationError({'action_code': [f'Unsupported action: {action_code}']})
        return handler(instance=instance, user=user, payload=payload)

    def _list_purchase_request_actions(self, *, instance: PurchaseRequest, user) -> List[Dict[str, Any]]:
        finance_service = FinanceVoucherService()
        active_receipt = AssetReceipt.objects.filter(
            purchase_request=instance,
            is_deleted=False,
        ).exclude(
            status__in=[AssetReceiptStatus.CANCELLED, AssetReceiptStatus.REJECTED]
        ).first()
        generated_asset_exists = Asset.objects.filter(
            organization_id=instance.organization_id,
            source_purchase_request=instance,
            is_deleted=False,
        ).exists()
        existing_voucher = finance_service.find_existing_voucher_by_source(
            organization_id=instance.organization_id,
            source_object_code='PurchaseRequest',
            source_id=str(instance.id),
            purchase_request_id=str(instance.id),
        )

        enabled = (
            instance.status in [PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.PROCESSING]
            and active_receipt is None
        )
        disabled_reason = ''
        if instance.status not in [PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.PROCESSING]:
            disabled_reason = 'Only approved or processing purchase requests can create receipts.'
        elif active_receipt is not None:
            disabled_reason = f'Active receipt {active_receipt.receipt_no} already exists for this request.'

        finance_enabled = (
            instance.status in [PurchaseRequestStatus.APPROVED, PurchaseRequestStatus.PROCESSING, PurchaseRequestStatus.COMPLETED]
            and generated_asset_exists
            and existing_voucher is None
        )
        finance_disabled_reason = ''
        if instance.status not in [
            PurchaseRequestStatus.APPROVED,
            PurchaseRequestStatus.PROCESSING,
            PurchaseRequestStatus.COMPLETED,
        ]:
            finance_disabled_reason = 'Only approved, processing, or completed purchase requests can create finance vouchers.'
        elif not generated_asset_exists:
            finance_disabled_reason = 'Generate asset cards from downstream receipts before creating a finance voucher.'
        elif existing_voucher is not None:
            finance_disabled_reason = (
                f'Finance voucher {existing_voucher.voucher_no} already exists for this purchase request.'
            )

        return [
            self._build_action(
                code=self.PURCHASE_CREATE_RECEIPT,
                label='Create Receipt',
                button_type='success',
                enabled=enabled,
                disabled_reason=disabled_reason,
                confirm_message='Create an asset receipt from this purchase request?',
                target_object_code='AssetReceipt',
            ),
            self._build_action(
                code=self.PURCHASE_GENERATE_FINANCE,
                label='Generate Finance Voucher',
                button_type='primary',
                enabled=finance_enabled,
                disabled_reason=finance_disabled_reason,
                confirm_message='Create a draft finance voucher for this purchase request?',
                target_object_code='FinanceVoucher',
            ),
        ]

    def _list_asset_receipt_actions(self, *, instance: AssetReceipt, user) -> List[Dict[str, Any]]:
        finance_service = FinanceVoucherService()
        pending_generation_exists = instance.items.filter(
            qualified_quantity__gt=0,
            asset_generated=False,
            is_deleted=False,
        ).exists()
        generated_asset_exists = Asset.objects.filter(
            organization_id=instance.organization_id,
            source_receipt=instance,
            is_deleted=False,
        ).exists()
        existing_voucher = finance_service.find_existing_voucher_by_source(
            organization_id=instance.organization_id,
            source_object_code='AssetReceipt',
            source_id=str(instance.id),
            purchase_request_id=str(instance.purchase_request_id or ''),
            receipt_id=str(instance.id),
        )

        enabled = instance.status == AssetReceiptStatus.PASSED and pending_generation_exists
        disabled_reason = ''
        if instance.status != AssetReceiptStatus.PASSED:
            disabled_reason = 'Only passed receipts can generate asset cards.'
        elif not pending_generation_exists:
            disabled_reason = 'No qualified receipt items are pending asset generation.'

        finance_enabled = (
            instance.status == AssetReceiptStatus.PASSED
            and not pending_generation_exists
            and generated_asset_exists
            and existing_voucher is None
        )
        finance_disabled_reason = ''
        if instance.status != AssetReceiptStatus.PASSED:
            finance_disabled_reason = 'Only passed receipts can create finance vouchers.'
        elif pending_generation_exists:
            finance_disabled_reason = 'Generate asset cards for all qualified items before creating a finance voucher.'
        elif not generated_asset_exists:
            finance_disabled_reason = 'No generated assets are available for finance voucher creation.'
        elif existing_voucher is not None:
            finance_disabled_reason = (
                f'Finance voucher {existing_voucher.voucher_no} already exists for this asset receipt.'
            )

        return [
            self._build_action(
                code=self.RECEIPT_GENERATE_ASSETS,
                label='Generate Assets',
                button_type='primary',
                enabled=enabled,
                disabled_reason=disabled_reason,
                confirm_message='Generate asset cards for all qualified receipt items?',
                target_object_code='Asset',
            ),
            self._build_action(
                code=self.RECEIPT_GENERATE_FINANCE,
                label='Generate Finance Voucher',
                button_type='primary',
                enabled=finance_enabled,
                disabled_reason=finance_disabled_reason,
                confirm_message='Create a draft finance voucher for this asset receipt?',
                target_object_code='FinanceVoucher',
            ),
        ]

    def _list_asset_actions(self, *, instance: Asset, user) -> List[Dict[str, Any]]:
        pickup_department = self._resolve_pickup_department(instance=instance)
        can_create_pickup = (
            str(getattr(instance, 'asset_status', '') or '').strip() in {'idle', 'pending'}
            and pickup_department is not None
        )
        pickup_reason = ''
        if str(getattr(instance, 'asset_status', '') or '').strip() not in {'idle', 'pending'}:
            pickup_reason = 'Only idle or pending assets can create pickup orders.'
        elif pickup_department is None:
            pickup_reason = 'No department is available for pickup order creation.'

        transfer_target_department = self._resolve_transfer_target_department(instance=instance)
        can_create_transfer = (
            str(getattr(instance, 'asset_status', '') or '').strip() != 'scrapped'
            and getattr(instance, 'department_id', None) is not None
            and transfer_target_department is not None
        )
        transfer_reason = ''
        if str(getattr(instance, 'asset_status', '') or '').strip() == 'scrapped':
            transfer_reason = 'Scrapped assets cannot create transfer orders.'
        elif getattr(instance, 'department_id', None) is None:
            transfer_reason = 'Asset department is required before creating a transfer order.'
        elif transfer_target_department is None:
            transfer_reason = 'No target department is available for transfer order creation.'

        return_location = self._resolve_return_location(instance=instance)
        can_create_return = (
            getattr(instance, 'custodian_id', None) == getattr(user, 'id', None)
            and str(getattr(instance, 'asset_status', '') or '').strip() not in {'idle', 'pending'}
            and return_location is not None
        )
        return_reason = ''
        if getattr(instance, 'custodian_id', None) != getattr(user, 'id', None):
            return_reason = 'Only the current custodian can create a return order.'
        elif str(getattr(instance, 'asset_status', '') or '').strip() in {'idle', 'pending'}:
            return_reason = 'Idle or pending assets do not require a return order.'
        elif return_location is None:
            return_reason = 'No return location is available for return order creation.'

        can_create_loan = str(getattr(instance, 'asset_status', '') or '').strip() in {'idle', 'pending'}
        loan_reason = ''
        if not can_create_loan:
            loan_reason = 'Only idle or pending assets can create loan orders.'

        can_create_maintenance = str(getattr(instance, 'asset_status', '') or '').strip() != 'scrapped'
        maintenance_reason = ''
        if not can_create_maintenance:
            maintenance_reason = 'Scrapped assets cannot create maintenance records.'

        disposal_department = self._resolve_disposal_department(instance=instance, user=user)
        can_create_disposal = str(getattr(instance, 'asset_status', '') or '').strip() != 'scrapped' and disposal_department is not None
        disposal_reason = ''
        if str(getattr(instance, 'asset_status', '') or '').strip() == 'scrapped':
            disposal_reason = 'Scrapped assets cannot create a new disposal request.'
        elif disposal_department is None:
            disposal_reason = 'No department organization is available for disposal requests.'

        return [
            self._build_action(
                code=self.ASSET_CREATE_PICKUP,
                label='Create Pickup',
                button_type='success',
                enabled=can_create_pickup,
                disabled_reason=pickup_reason,
                confirm_message='Create a pickup draft from this asset?',
                target_object_code='AssetPickup',
            ),
            self._build_action(
                code=self.ASSET_CREATE_TRANSFER,
                label='Create Transfer',
                button_type='warning',
                enabled=can_create_transfer,
                disabled_reason=transfer_reason,
                confirm_message='Create a transfer draft from this asset?',
                target_object_code='AssetTransfer',
            ),
            self._build_action(
                code=self.ASSET_CREATE_RETURN,
                label='Create Return',
                button_type='info',
                enabled=can_create_return,
                disabled_reason=return_reason,
                confirm_message='Create a return draft from this asset?',
                target_object_code='AssetReturn',
            ),
            self._build_action(
                code=self.ASSET_CREATE_LOAN,
                label='Create Loan',
                button_type='primary',
                enabled=can_create_loan,
                disabled_reason=loan_reason,
                confirm_message='Create a loan draft from this asset?',
                target_object_code='AssetLoan',
            ),
            self._build_action(
                code=self.ASSET_CREATE_MAINTENANCE,
                label='Create Maintenance',
                button_type='warning',
                enabled=can_create_maintenance,
                disabled_reason=maintenance_reason,
                confirm_message='Create a maintenance draft from this asset?',
                target_object_code='Maintenance',
            ),
            self._build_action(
                code=self.ASSET_CREATE_DISPOSAL,
                label='Create Disposal Request',
                button_type='danger',
                enabled=can_create_disposal,
                disabled_reason=disposal_reason,
                confirm_message='Create a disposal request draft from this asset?',
                target_object_code='DisposalRequest',
            ),
        ]

    @transaction.atomic
    def _execute_asset_create_pickup(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_PICKUP),
            None,
        )
        self._ensure_enabled(action)

        department = self._resolve_pickup_department(instance=instance)
        if department is None:
            raise ValidationError({'department': ['No department is available for pickup order creation.']})

        pickup = AssetPickupService().create_with_items(
            {
                'department': department,
                'pickup_date': timezone.now().date(),
                'pickup_reason': f'Created from asset {instance.asset_code}',
            },
            [{'asset_id': str(instance.id)}],
            user,
            str(instance.organization_id),
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_PICKUP,
            target_object_code='AssetPickup',
            target_id=pickup.id,
            message=f'Pickup order {pickup.pickup_no} created successfully.',
            extra={
                'target_record_no': pickup.pickup_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_asset_create_transfer(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_TRANSFER),
            None,
        )
        self._ensure_enabled(action)

        if getattr(instance, 'department_id', None) is None:
            raise ValidationError({'department': ['Asset department is required before creating a transfer order.']})
        target_department = self._resolve_transfer_target_department(instance=instance)
        if target_department is None:
            raise ValidationError({'to_department': ['No target department is available for transfer order creation.']})

        transfer = AssetTransferService().create_with_items(
            {
                'from_department': instance.department,
                'to_department': target_department,
                'transfer_date': timezone.now().date(),
                'transfer_reason': f'Created from asset {instance.asset_code}',
            },
            [{
                'asset_id': str(instance.id),
                'to_location_id': str(getattr(instance, 'location_id', '') or ''),
            }],
            user,
            str(instance.organization_id),
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_TRANSFER,
            target_object_code='AssetTransfer',
            target_id=transfer.id,
            message=f'Transfer order {transfer.transfer_no} created successfully.',
            extra={
                'target_record_no': transfer.transfer_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_asset_create_return(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_RETURN),
            None,
        )
        self._ensure_enabled(action)

        return_location = self._resolve_return_location(instance=instance)
        if return_location is None:
            raise ValidationError({'return_location': ['No return location is available for return order creation.']})

        return_order = AssetReturnService().create_with_items(
            {
                'return_date': timezone.now().date(),
                'return_reason': f'Created from asset {instance.asset_code}',
                'return_location': return_location,
            },
            [{
                'asset_id': str(instance.id),
                'asset_status': 'idle',
            }],
            user,
            str(instance.organization_id),
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_RETURN,
            target_object_code='AssetReturn',
            target_id=return_order.id,
            message=f'Return order {return_order.return_no} created successfully.',
            extra={
                'target_record_no': return_order.return_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_asset_create_loan(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_LOAN),
            None,
        )
        self._ensure_enabled(action)

        borrow_date = timezone.now().date()
        loan = AssetLoanService().create_with_items(
            {
                'borrow_date': borrow_date,
                'expected_return_date': borrow_date + timedelta(days=7),
                'loan_reason': f'Created from asset {instance.asset_code}',
            },
            [{'asset_id': str(instance.id)}],
            user,
            str(instance.organization_id),
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_LOAN,
            target_object_code='AssetLoan',
            target_id=loan.id,
            message=f'Loan order {loan.loan_no} created successfully.',
            extra={
                'target_record_no': loan.loan_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_purchase_create_receipt(self, *, instance: PurchaseRequest, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_purchase_request_actions(instance=instance, user=user) if item['action_code'] == self.PURCHASE_CREATE_RECEIPT),
            None,
        )
        self._ensure_enabled(action)

        supplier = ''
        items_data: List[Dict[str, Any]] = []
        for item in instance.items.filter(is_deleted=False).order_by('sequence'):
            if not supplier and item.suggested_supplier:
                supplier = item.suggested_supplier
            items_data.append({
                'asset_category': item.asset_category,
                'item_name': item.item_name,
                'specification': item.specification,
                'brand': item.brand,
                'ordered_quantity': item.quantity,
                'received_quantity': item.quantity,
                'qualified_quantity': item.quantity,
                'defective_quantity': 0,
                'unit_price': item.unit_price,
                'total_amount': item.total_amount,
                'remark': item.remark,
            })

        receipt_service = AssetReceiptService()
        receipt = receipt_service.create_with_items(
            {
                'purchase_request': instance,
                'receipt_date': timezone.now().date(),
                'receipt_type': 'purchase',
                'm18_purchase_order_no': instance.m18_purchase_order_no,
                'supplier': supplier,
                'delivery_no': '',
                'remark': f'Created from purchase request {instance.request_no}',
                'items': items_data,
            },
            user,
        )

        instance.refresh_from_db()

        return self._build_execution_result(
            action_code=self.PURCHASE_CREATE_RECEIPT,
            target_object_code='AssetReceipt',
            target_id=receipt.id,
            message=f'Asset receipt {receipt.receipt_no} created successfully.',
            extra={
                'target_record_no': receipt.receipt_no,
                'source_object_code': 'PurchaseRequest',
                'source_id': str(instance.id),
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_purchase_generate_finance_voucher(
        self,
        *,
        instance: PurchaseRequest,
        user,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_purchase_request_actions(instance=instance, user=user) if item['action_code'] == self.PURCHASE_GENERATE_FINANCE),
            None,
        )
        self._ensure_enabled(action)

        assets = Asset.objects.filter(
            organization_id=instance.organization_id,
            source_purchase_request=instance,
            is_deleted=False,
        ).select_related(
            'source_receipt',
            'source_purchase_request',
        )
        voucher = FinanceVoucherService().generate_purchase_voucher_for_assets(
            assets=assets,
            organization_id=instance.organization_id,
            user=user,
            business_id=str(instance.id),
            notes=f'Generated from purchase request {instance.request_no}',
            summary=f'Asset purchase voucher ({instance.request_no})',
        )

        return self._build_execution_result(
            action_code=self.PURCHASE_GENERATE_FINANCE,
            target_object_code='FinanceVoucher',
            target_id=voucher.id,
            message=f'Finance voucher {voucher.voucher_no} created successfully.',
            extra={
                'target_record_no': voucher.voucher_no,
                'source_object_code': 'PurchaseRequest',
                'source_id': str(instance.id),
                'summary': {
                    'voucher_no': voucher.voucher_no,
                    'status': voucher.status,
                    'total_amount': str(voucher.total_amount),
                },
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_receipt_generate_assets(self, *, instance: AssetReceipt, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_receipt_actions(instance=instance, user=user) if item['action_code'] == self.RECEIPT_GENERATE_ASSETS),
            None,
        )
        self._ensure_enabled(action)

        service = AssetReceiptService()
        generation_result = service.generate_asset_cards(str(instance.id), user=user)
        summary = service.get_receipt_items_summary(str(instance.id))
        instance.refresh_from_db()
        generated_assets = generation_result['generated_assets']
        generated_count = generation_result['generated_count']

        if generated_count == 1 and generated_assets:
            target_url = f'/objects/Asset/{generated_assets[0].id}'
            target_record_no = generated_assets[0].asset_code
        else:
            target_url = f'/objects/Asset?source_receipt={instance.id}'
            target_record_no = instance.receipt_no

        return {
            'action_code': self.RECEIPT_GENERATE_ASSETS,
            'message': f'Generated {generated_count} asset card(s) for receipt {instance.receipt_no}.',
            'target_object_code': 'Asset',
            'target_url': target_url,
            'target_record_no': target_record_no,
            'navigate_after_success': False,
            'summary': summary,
            'generated_count': generated_count,
            'generated_assets': [
                {
                    'id': str(asset.id),
                    'asset_code': asset.asset_code,
                    'asset_name': asset.asset_name,
                }
                for asset in generated_assets
            ],
            'refresh_current': True,
        }

    @transaction.atomic
    def _execute_receipt_generate_finance_voucher(
        self,
        *,
        instance: AssetReceipt,
        user,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_receipt_actions(instance=instance, user=user) if item['action_code'] == self.RECEIPT_GENERATE_FINANCE),
            None,
        )
        self._ensure_enabled(action)

        assets = Asset.objects.filter(
            organization_id=instance.organization_id,
            source_receipt=instance,
            is_deleted=False,
        ).select_related(
            'source_receipt',
            'source_purchase_request',
        )
        voucher = FinanceVoucherService().generate_purchase_voucher_for_assets(
            assets=assets,
            organization_id=instance.organization_id,
            user=user,
            business_id=str(instance.id),
            notes=f'Generated from asset receipt {instance.receipt_no}',
            summary=f'Asset purchase voucher ({instance.receipt_no})',
        )

        return self._build_execution_result(
            action_code=self.RECEIPT_GENERATE_FINANCE,
            target_object_code='FinanceVoucher',
            target_id=voucher.id,
            message=f'Finance voucher {voucher.voucher_no} created successfully.',
            extra={
                'target_record_no': voucher.voucher_no,
                'source_object_code': 'AssetReceipt',
                'source_id': str(instance.id),
                'summary': {
                    'voucher_no': voucher.voucher_no,
                    'status': voucher.status,
                    'total_amount': str(voucher.total_amount),
                },
                'refresh_current': True,
            },
        )

    @transaction.atomic
    def _execute_asset_create_maintenance(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_MAINTENANCE),
            None,
        )
        self._ensure_enabled(action)

        maintenance = MaintenanceService().create(
            {
                'asset': instance,
                'priority': MaintenancePriority.NORMAL,
                'fault_description': f'Created from asset {instance.asset_code}',
                'remark': 'Created by cross-object action',
            },
            user,
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_MAINTENANCE,
            target_object_code='Maintenance',
            target_id=maintenance.id,
            message=f'Maintenance draft {maintenance.maintenance_no} created successfully.',
            extra={
                'target_record_no': maintenance.maintenance_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
            },
        )

    @transaction.atomic
    def _execute_asset_create_disposal(self, *, instance: Asset, user, payload: Dict[str, Any]) -> Dict[str, Any]:
        action = next(
            (item for item in self._list_asset_actions(instance=instance, user=user) if item['action_code'] == self.ASSET_CREATE_DISPOSAL),
            None,
        )
        self._ensure_enabled(action)

        disposal_department = self._resolve_disposal_department(instance=instance, user=user)
        if disposal_department is None:
            raise ValidationError({'department': ['No department organization is available for disposal requests.']})

        original_value = self._to_decimal(getattr(instance, 'purchase_price', 0))
        current_value = self._to_decimal(getattr(instance, 'current_value', 0))
        accumulated_depreciation = self._to_decimal(getattr(instance, 'accumulated_depreciation', 0))
        if accumulated_depreciation == Decimal('0') and original_value > current_value:
            accumulated_depreciation = original_value - current_value

        disposal_request = DisposalRequestService().create_with_items(
            {
                'department': disposal_department,
                'request_date': timezone.now().date(),
                'disposal_type': DisposalType.SCRAP,
                'disposal_reason': f'Created from asset {instance.asset_code}',
                'reason_type': DisposalReason.OTHER,
                'remark': 'Created by cross-object action',
                'items': [
                    {
                        'asset': instance,
                        'original_value': original_value,
                        'accumulated_depreciation': accumulated_depreciation,
                        'net_value': current_value or original_value,
                        'remark': f'Created from asset {instance.asset_code}',
                    }
                ],
            },
            user,
        )

        return self._build_execution_result(
            action_code=self.ASSET_CREATE_DISPOSAL,
            target_object_code='DisposalRequest',
            target_id=disposal_request.id,
            message=f'Disposal request {disposal_request.request_no} created successfully.',
            extra={
                'target_record_no': disposal_request.request_no,
                'source_object_code': 'Asset',
                'source_id': str(instance.id),
            },
        )

    def _resolve_disposal_department(self, *, instance: Asset, user) -> Optional[Organization]:
        current_org = getattr(user, 'current_organization', None) or getattr(user, 'organization', None)

        asset_department = getattr(instance, 'department', None)
        if asset_department is not None:
            department_code = str(getattr(asset_department, 'code', '') or '').strip()
            if department_code:
                department = Organization.objects.filter(
                    code=department_code,
                    org_type='department',
                ).first()
                if department is not None:
                    return department

        if current_org is not None and getattr(current_org, 'org_type', '') == 'department':
            return current_org

        if current_org is None:
            return None

        return Organization.objects.filter(
            parent=current_org,
            org_type='department',
        ).order_by('code').first()

    @staticmethod
    def _resolve_pickup_department(*, instance: Asset) -> Optional[Department]:
        if getattr(instance, 'department_id', None):
            return instance.department
        return Department.objects.filter(
            organization_id=instance.organization_id,
            is_deleted=False,
        ).order_by('code').first()

    @staticmethod
    def _resolve_transfer_target_department(*, instance: Asset) -> Optional[Department]:
        if getattr(instance, 'department_id', None) is None:
            return None
        return Department.objects.filter(
            organization_id=instance.organization_id,
            is_deleted=False,
        ).exclude(id=instance.department_id).order_by('code').first()

    @staticmethod
    def _resolve_return_location(*, instance: Asset) -> Optional[Location]:
        if getattr(instance, 'location_id', None):
            return instance.location
        return Location.objects.filter(
            organization_id=instance.organization_id,
            is_deleted=False,
        ).order_by('path', 'created_at').first()

    @staticmethod
    def _build_action(
        *,
        code: str,
        label: str,
        button_type: str,
        enabled: bool,
        disabled_reason: str = '',
        confirm_message: str = '',
        target_object_code: str = '',
    ) -> Dict[str, Any]:
        return {
            'action_code': code,
            'label': label,
            'button_type': button_type,
            'enabled': bool(enabled),
            'disabled_reason': disabled_reason,
            'confirm_message': confirm_message,
            'target_object_code': target_object_code,
        }

    @staticmethod
    def _build_execution_result(
        *,
        action_code: str,
        target_object_code: str,
        target_id,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            'action_code': action_code,
            'target_object_code': target_object_code,
            'target_id': str(target_id),
            'target_url': f'/objects/{target_object_code}/{target_id}',
            'message': message,
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _ensure_enabled(action: Optional[Dict[str, Any]]) -> None:
        if not action:
            raise ValidationError({'action_code': ['Action is not available.']})
        if not action.get('enabled'):
            message = action.get('disabled_reason') or 'Action is currently disabled.'
            raise ValidationError({'action_code': [message]})

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if isinstance(value, Decimal):
            return value
        if value in (None, ''):
            return Decimal('0')
        return Decimal(str(value))
