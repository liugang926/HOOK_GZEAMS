"""
Object-level closure summary aggregation service.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class ObjectClosureBindingService:
    """Aggregate closure state for a business object record."""

    _LEASE_DAMAGE_CONDITIONS = ('poor', 'broken', 'lost')

    @staticmethod
    def _resolve_custom_field_text(instance: Optional[Any], key: str) -> str:
        custom_fields = getattr(instance, 'custom_fields', None) or {}
        return str(custom_fields.get(key, '') or '').strip()

    def _build_cancelled_blocker(self, instance: Optional[Any]) -> str:
        cancel_reason = self._resolve_custom_field_text(instance, 'cancel_reason')
        if cancel_reason:
            return f'Cancellation reason: {cancel_reason}'
        return ''

    def get_object_closure_summary(
        self,
        *,
        object_code: str,
        business_id: str,
        instance: Optional[Any] = None,
        organization_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return a normalized closure summary for the requested business object."""
        normalized_object_code = str(object_code or '').strip()
        normalized_business_id = str(business_id or '').strip()
        summary = self._build_empty_summary(
            object_code=normalized_object_code,
            business_id=normalized_business_id,
        )
        if not normalized_object_code or not normalized_business_id:
            return summary

        if normalized_object_code == 'InventoryTask':
            return self._build_inventory_task_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'FinanceVoucher':
            return self._build_finance_voucher_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'PurchaseRequest':
            return self._build_purchase_request_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetReceipt':
            return self._build_asset_receipt_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetPickup':
            return self._build_asset_pickup_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetTransfer':
            return self._build_asset_transfer_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetReturn':
            return self._build_asset_return_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetLoan':
            return self._build_asset_loan_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'Maintenance':
            return self._build_maintenance_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'DisposalRequest':
            return self._build_disposal_request_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'InsurancePolicy':
            return self._build_insurance_policy_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'ClaimRecord':
            return self._build_claim_record_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'LeasingContract':
            return self._build_leasing_contract_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'Asset':
            return self._build_asset_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )
        if normalized_object_code == 'AssetProject':
            return self._build_asset_project_summary(
                business_id=normalized_business_id,
                instance=instance,
                fallback=summary,
                organization_id=organization_id,
            )

        return summary

    def _build_inventory_task_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.inventory.models import InventoryTask
        from apps.inventory.services import InventoryTaskClosureService

        task = instance
        if not isinstance(task, InventoryTask):
            queryset = InventoryTask.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            task = queryset.select_related('created_by').first()

        if task is None:
            return fallback

        return InventoryTaskClosureService().build_summary(task)

    def _build_finance_voucher_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.finance.models import FinanceVoucher
        from apps.integration.models import IntegrationLog

        voucher = instance
        if not isinstance(voucher, FinanceVoucher):
            queryset = FinanceVoucher.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            voucher = queryset.select_related('created_by', 'posted_by').prefetch_related('entries').first()

        if voucher is None:
            return fallback

        failed_sync_count = IntegrationLog.all_objects.filter(
            business_type='voucher',
            business_id=str(voucher.id),
            success=False,
            is_deleted=False,
        ).filter(
            organization_id=voucher.organization_id
        ).count()
        entry_count = voucher.entries.filter(is_deleted=False).count()
        completion = 10.0
        stage = 'Draft'
        blocker = 'Submit the voucher for approval.'
        approval_status = 'not_submitted'

        if voucher.status == 'submitted':
            stage = 'Awaiting approval'
            blocker = 'Approval is still pending.'
            completion = 45.0
            approval_status = 'pending'
        elif voucher.status == 'approved':
            stage = 'Ready for ERP posting'
            blocker = 'Push the voucher to ERP to finish accounting closure.'
            completion = 75.0
            approval_status = 'approved'
            if failed_sync_count > 0:
                blocker = 'Review ERP integration errors and retry the push.'
            if voucher.erp_voucher_no:
                stage = 'ERP reference received'
                blocker = ''
                completion = 90.0
        elif voucher.status == 'posted':
            stage = 'Posted to ERP' if voucher.erp_voucher_no else 'Posted internally'
            blocker = '' if voucher.erp_voucher_no else 'ERP reference is missing. Retry ERP synchronization if accounting closure is incomplete.'
            completion = 100.0 if voucher.erp_voucher_no else 90.0
            approval_status = 'approved'
        elif voucher.status == 'rejected':
            stage = 'Rejected'
            blocker = 'Update the voucher and resubmit it for approval.'
            completion = 20.0
            approval_status = 'rejected'

        return {
            'objectCode': 'FinanceVoucher',
            'businessId': str(voucher.id),
            'hasSummary': True,
            'status': voucher.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(voucher, 'posted_by', None),
                getattr(voucher, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'entryCount': entry_count,
                'totalAmount': self._serialize_number(voucher.total_amount),
                'isBalanced': bool(voucher.is_balanced()),
                'failedSyncCount': failed_sync_count,
                'hasErpReference': bool(voucher.erp_voucher_no),
            },
        }

    def _build_purchase_request_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from django.db.models import Q, Sum

        from apps.assets.models import Asset
        from apps.finance.models import FinanceVoucher
        from apps.lifecycle.models import AssetReceiptItem, PurchaseRequest, PurchaseRequestStatus

        purchase_request = instance
        if not isinstance(purchase_request, PurchaseRequest):
            queryset = PurchaseRequest.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            purchase_request = queryset.select_related(
                'applicant',
                'current_approver',
                'approved_by',
                'created_by',
            ).first()

        if purchase_request is None:
            return fallback

        linked_receipts = purchase_request.receipts.filter(is_deleted=False)
        linked_receipt_count = linked_receipts.count()
        active_receipt_count = linked_receipts.exclude(status__in=['cancelled', 'rejected']).count()
        passed_receipt_count = linked_receipts.filter(status='passed').count()
        latest_receipt = linked_receipts.order_by('-receipt_date', '-created_at').first()
        total_requested_quantity = purchase_request.items.filter(is_deleted=False).aggregate(
            total=Sum('quantity'),
        ).get('total') or 0
        pending_generation_count = AssetReceiptItem.all_objects.filter(
            organization_id=purchase_request.organization_id,
            is_deleted=False,
            asset_receipt__is_deleted=False,
            asset_receipt__purchase_request_id=purchase_request.id,
            asset_receipt__status='passed',
            qualified_quantity__gt=0,
            asset_generated=False,
        ).aggregate(total=Sum('qualified_quantity')).get('total') or 0
        generated_asset_count = Asset.all_objects.filter(
            organization_id=purchase_request.organization_id,
            is_deleted=False,
            source_purchase_request_id=purchase_request.id,
        ).count()
        linked_finance_vouchers = FinanceVoucher.all_objects.filter(
            organization_id=purchase_request.organization_id,
            is_deleted=False,
            custom_fields__source_purchase_request_id=str(purchase_request.id),
        )
        linked_finance_voucher_count = linked_finance_vouchers.count()
        open_finance_voucher_count = linked_finance_vouchers.filter(
            Q(status__in=['draft', 'submitted', 'approved', 'rejected']) |
            Q(status='posted', erp_voucher_no=''),
        ).count()
        latest_finance_voucher = linked_finance_vouchers.order_by('-voucher_date', '-created_at').first()
        cancel_reason = self._resolve_custom_field_text(purchase_request, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the purchase request for approval.'
        completion = 10.0
        approval_status = 'not_submitted'

        if purchase_request.status == PurchaseRequestStatus.SUBMITTED:
            stage = 'Awaiting approval'
            blocker = 'Approval is still pending.'
            completion = 30.0
            approval_status = 'pending'
        elif purchase_request.status == PurchaseRequestStatus.REJECTED:
            stage = 'Rejected'
            blocker = 'Update the purchase request and resubmit it for approval.'
            completion = 20.0
            approval_status = 'rejected'
        elif purchase_request.status == PurchaseRequestStatus.CANCELLED:
            stage = 'Request cancelled'
            blocker = self._build_cancelled_blocker(purchase_request)
            completion = 100.0
            approval_status = 'cancelled'
        elif active_receipt_count == 0:
            stage = 'Approved, awaiting receipt'
            blocker = 'Create an asset receipt to continue fulfillment.'
            completion = 55.0
            approval_status = 'approved'
        elif passed_receipt_count == 0:
            stage = 'Receipt in progress'
            blocker = 'Finish receipt inspection to continue fulfillment.'
            completion = 65.0
            approval_status = 'approved'
        elif pending_generation_count > 0:
            stage = 'Asset generation pending'
            blocker = 'Generate asset cards from passed receipts to continue closure.'
            completion = 75.0
            approval_status = 'approved'
        elif open_finance_voucher_count > 0:
            stage = 'Finance posting pending'
            blocker = 'Submit, approve, and post linked finance vouchers to complete financial closure.'
            completion = 90.0
            approval_status = 'approved'
        elif purchase_request.status == PurchaseRequestStatus.COMPLETED or generated_asset_count > 0:
            stage = 'Lifecycle completed'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        else:
            stage = 'Receipt recorded'
            blocker = 'Review downstream fulfillment records to complete the chain.'
            completion = 80.0
            approval_status = 'approved'

        return {
            'objectCode': 'PurchaseRequest',
            'businessId': str(purchase_request.id),
            'hasSummary': True,
            'status': purchase_request.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(purchase_request, 'current_approver', None),
                getattr(purchase_request, 'applicant', None),
                getattr(purchase_request, 'approved_by', None),
                getattr(purchase_request, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'totalRequestedQuantity': int(total_requested_quantity or 0),
                'linkedReceiptCount': linked_receipt_count,
                'activeReceiptCount': active_receipt_count,
                'passedReceiptCount': passed_receipt_count,
                'pendingGenerationCount': int(pending_generation_count or 0),
                'generatedAssetCount': generated_asset_count,
                'linkedFinanceVoucherCount': linked_finance_voucher_count,
                'openFinanceVoucherCount': open_finance_voucher_count,
                'latestReceiptNo': str(getattr(latest_receipt, 'receipt_no', '') or ''),
                'latestFinanceVoucherNo': str(getattr(latest_finance_voucher, 'voucher_no', '') or ''),
                'latestFinanceVoucherStatus': str(getattr(latest_finance_voucher, 'status', '') or ''),
                'm18PurchaseOrderNo': str(getattr(purchase_request, 'm18_purchase_order_no', '') or ''),
                'cancelReason': cancel_reason,
            },
        }

    def _build_asset_receipt_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from django.db.models import Q, Sum

        from apps.assets.models import Asset
        from apps.finance.models import FinanceVoucher
        from apps.lifecycle.models import AssetReceipt, AssetReceiptStatus

        receipt = instance
        if not isinstance(receipt, AssetReceipt):
            queryset = AssetReceipt.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            receipt = queryset.select_related(
                'purchase_request',
                'receiver',
                'inspector',
                'created_by',
            ).prefetch_related('items').first()

        if receipt is None:
            return fallback

        total_items = receipt.items.filter(is_deleted=False).count()
        total_qualified_count = receipt.items.filter(is_deleted=False).aggregate(
            total=Sum('qualified_quantity'),
        ).get('total') or 0
        generated_item_count = receipt.items.filter(
            is_deleted=False,
            asset_generated=True,
        ).count()
        generated_asset_count = Asset.all_objects.filter(
            organization_id=receipt.organization_id,
            is_deleted=False,
            source_receipt_id=receipt.id,
        ).count()
        pending_generation_count = max(int(total_qualified_count or 0) - int(generated_asset_count or 0), 0)
        linked_finance_vouchers = FinanceVoucher.all_objects.filter(
            organization_id=receipt.organization_id,
            is_deleted=False,
            custom_fields__source_receipt_id=str(receipt.id),
        )
        linked_finance_voucher_count = linked_finance_vouchers.count()
        open_finance_voucher_count = linked_finance_vouchers.filter(
            Q(status__in=['draft', 'submitted', 'approved', 'rejected']) |
            Q(status='posted', erp_voucher_no=''),
        ).count()
        latest_finance_voucher = linked_finance_vouchers.order_by('-voucher_date', '-created_at').first()
        source_purchase_request = getattr(receipt, 'purchase_request', None)
        cancel_reason = self._resolve_custom_field_text(receipt, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the receipt for inspection.'
        completion = 15.0

        if receipt.status == AssetReceiptStatus.SUBMITTED:
            stage = 'Awaiting inspection'
            blocker = 'Inspection has not started yet.'
            completion = 35.0
        elif receipt.status == AssetReceiptStatus.INSPECTING:
            stage = 'Inspection in progress'
            blocker = 'Record the inspection result to continue closure.'
            completion = 55.0
        elif receipt.status == AssetReceiptStatus.REJECTED:
            stage = 'Rejected'
            blocker = 'Update the receipt and resubmit it for inspection.'
            completion = 25.0
        elif receipt.status == AssetReceiptStatus.CANCELLED:
            stage = 'Receipt cancelled'
            blocker = self._build_cancelled_blocker(receipt)
            completion = 100.0
        elif pending_generation_count > 0:
            stage = 'Asset generation pending'
            blocker = 'Generate asset cards for qualified receipt items.'
            completion = 75.0
        elif open_finance_voucher_count > 0:
            stage = 'Finance posting pending'
            blocker = 'Submit, approve, and post linked finance vouchers to complete financial closure.'
            completion = 90.0
        elif receipt.status == AssetReceiptStatus.PASSED:
            stage = 'Receipt closed'
            blocker = ''
            completion = 100.0

        return {
            'objectCode': 'AssetReceipt',
            'businessId': str(receipt.id),
            'hasSummary': True,
            'status': receipt.status,
            'approvalStatus': 'approved' if receipt.status == AssetReceiptStatus.PASSED else None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(receipt, 'inspector', None),
                getattr(receipt, 'receiver', None),
                getattr(receipt, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'totalItems': total_items,
                'totalQualifiedCount': int(total_qualified_count or 0),
                'generatedItemCount': generated_item_count,
                'generatedAssetCount': generated_asset_count,
                'pendingGenerationCount': pending_generation_count,
                'linkedFinanceVoucherCount': linked_finance_voucher_count,
                'openFinanceVoucherCount': open_finance_voucher_count,
                'latestFinanceVoucherNo': str(getattr(latest_finance_voucher, 'voucher_no', '') or ''),
                'latestFinanceVoucherStatus': str(getattr(latest_finance_voucher, 'status', '') or ''),
                'sourcePurchaseRequestNo': str(getattr(source_purchase_request, 'request_no', '') or ''),
                'sourcePurchaseRequestId': str(getattr(source_purchase_request, 'id', '') or ''),
                'cancelReason': cancel_reason,
            },
        }

    def _build_asset_pickup_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.assets.models import AssetPickup

        pickup = instance
        if not isinstance(pickup, AssetPickup):
            queryset = AssetPickup.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            pickup = queryset.select_related(
                'applicant',
                'department',
                'approved_by',
                'created_by',
            ).prefetch_related('items').first()

        if pickup is None:
            return fallback

        item_count = pickup.items.filter(is_deleted=False).count()
        approved_item_count = item_count if pickup.status in {'approved', 'completed'} else 0
        cancel_reason = self._resolve_custom_field_text(pickup, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the pickup order for approval.'
        completion = 15.0
        approval_status = 'not_submitted'

        if pickup.status == 'pending':
            stage = 'Awaiting approval'
            blocker = 'Review and approve or reject the pickup order.'
            completion = 45.0
            approval_status = 'pending'
        elif pickup.status == 'approved':
            stage = 'Approved, awaiting handover completion'
            blocker = 'Complete the pickup order after the asset handover is finished.'
            completion = 80.0
            approval_status = 'approved'
        elif pickup.status == 'completed':
            stage = 'Pickup completed'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        elif pickup.status == 'rejected':
            stage = 'Rejected'
            blocker = 'Update the pickup order and resubmit it for approval.'
            completion = 25.0
            approval_status = 'rejected'
        elif pickup.status == 'cancelled':
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(pickup)
            completion = 100.0
            approval_status = 'cancelled'

        return {
            'objectCode': 'AssetPickup',
            'businessId': str(pickup.id),
            'hasSummary': True,
            'status': pickup.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(pickup, 'approved_by', None),
                getattr(pickup, 'applicant', None),
                getattr(pickup, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'itemCount': item_count,
                'approvedItemCount': approved_item_count,
                'applicantName': self._resolve_owner(getattr(pickup, 'applicant', None)),
                'departmentName': self._resolve_owner(getattr(pickup, 'department', None)),
                'cancelReason': cancel_reason,
            },
        }

    def _build_asset_transfer_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.assets.models import AssetTransfer

        transfer = instance
        if not isinstance(transfer, AssetTransfer):
            queryset = AssetTransfer.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            transfer = queryset.select_related(
                'from_department',
                'to_department',
                'from_approved_by',
                'to_approved_by',
                'created_by',
            ).prefetch_related('items').first()

        if transfer is None:
            return fallback

        item_count = transfer.items.filter(is_deleted=False).count()
        source_approved_count = 1 if transfer.from_approved_by_id else 0
        target_approved_count = 1 if transfer.to_approved_by_id else 0
        cancel_reason = self._resolve_custom_field_text(transfer, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the transfer order for approval.'
        completion = 10.0
        approval_status = 'not_submitted'

        if transfer.status == 'pending':
            stage = 'Awaiting source approval'
            blocker = 'Source department approval is still pending.'
            completion = 35.0
            approval_status = 'pending'
        elif transfer.status == 'out_approved':
            stage = 'Awaiting target approval'
            blocker = 'Target department approval is still pending.'
            completion = 60.0
            approval_status = 'pending'
        elif transfer.status == 'approved':
            stage = 'Approved, awaiting completion'
            blocker = 'Complete the transfer to update the asset department and location.'
            completion = 85.0
            approval_status = 'approved'
        elif transfer.status == 'completed':
            stage = 'Transfer completed'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        elif transfer.status == 'rejected':
            stage = 'Rejected'
            blocker = 'Update the transfer order and resubmit it for approval.'
            completion = 25.0
            approval_status = 'rejected'
        elif transfer.status == 'cancelled':
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(transfer)
            completion = 100.0
            approval_status = 'cancelled'

        return {
            'objectCode': 'AssetTransfer',
            'businessId': str(transfer.id),
            'hasSummary': True,
            'status': transfer.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(transfer, 'to_approved_by', None),
                getattr(transfer, 'from_approved_by', None),
                getattr(transfer, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'itemCount': item_count,
                'sourceApprovedCount': source_approved_count,
                'targetApprovedCount': target_approved_count,
                'sourceDepartmentName': self._resolve_owner(getattr(transfer, 'from_department', None)),
                'targetDepartmentName': self._resolve_owner(getattr(transfer, 'to_department', None)),
                'cancelReason': cancel_reason,
            },
        }

    def _build_asset_return_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.assets.models import AssetReturn

        return_order = instance
        if not isinstance(return_order, AssetReturn):
            queryset = AssetReturn.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            return_order = queryset.select_related(
                'returner',
                'return_location',
                'confirmed_by',
                'created_by',
            ).prefetch_related('items').first()

        if return_order is None:
            return fallback

        items = return_order.items.filter(is_deleted=False)
        item_count = items.count()
        project_allocation_count = items.filter(project_allocation__isnull=False).count()
        maintenance_after_return_count = items.filter(asset_status='maintenance').count()
        cancel_reason = self._resolve_custom_field_text(return_order, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the return order for confirmation.'
        completion = 15.0
        approval_status = 'not_submitted'

        if return_order.status == 'pending':
            stage = 'Awaiting confirmation'
            blocker = 'Confirm or reject the return order after warehouse inspection.'
            completion = 60.0
            approval_status = 'pending'
        elif return_order.status in {'completed', 'confirmed'}:
            stage = 'Return completed'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        elif return_order.status == 'rejected':
            stage = 'Rejected'
            blocker = 'Update the return order and resubmit it for confirmation.'
            completion = 25.0
            approval_status = 'rejected'
        elif return_order.status == 'cancelled':
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(return_order)
            completion = 100.0
            approval_status = 'cancelled'

        return {
            'objectCode': 'AssetReturn',
            'businessId': str(return_order.id),
            'hasSummary': True,
            'status': return_order.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(return_order, 'confirmed_by', None),
                getattr(return_order, 'returner', None),
                getattr(return_order, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'itemCount': item_count,
                'projectAllocationCount': project_allocation_count,
                'maintenanceAfterReturnCount': maintenance_after_return_count,
                'returnLocationName': self._resolve_owner(getattr(return_order, 'return_location', None)),
                'cancelReason': cancel_reason,
            },
        }

    def _build_asset_loan_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from django.utils import timezone

        from apps.assets.models import AssetLoan

        loan = instance
        if not isinstance(loan, AssetLoan):
            queryset = AssetLoan.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            loan = queryset.select_related(
                'borrower',
                'approved_by',
                'lent_by',
                'return_confirmed_by',
                'created_by',
            ).prefetch_related('items').first()

        if loan is None:
            return fallback

        item_count = loan.items.filter(is_deleted=False).count()
        overdue_days = 0
        cancel_reason = self._resolve_custom_field_text(loan, 'cancel_reason')
        if loan.expected_return_date and loan.status == 'overdue':
            overdue_days = max((timezone.now().date() - loan.expected_return_date).days, 0)

        stage = 'Draft'
        blocker = 'Submit the loan order for approval.'
        completion = 15.0
        approval_status = 'not_submitted'

        if loan.status == 'pending':
            stage = 'Awaiting approval'
            blocker = 'Review and approve or reject the loan order.'
            completion = 35.0
            approval_status = 'pending'
        elif loan.status == 'approved':
            stage = 'Approved, awaiting lending'
            blocker = 'Confirm asset lending to activate the loan.'
            completion = 65.0
            approval_status = 'approved'
        elif loan.status == 'borrowed':
            stage = 'On loan'
            blocker = 'Confirm asset return to complete the loan lifecycle.'
            completion = 80.0
            approval_status = 'approved'
        elif loan.status == 'overdue':
            stage = 'Overdue return'
            blocker = 'Recover the asset and confirm return immediately.'
            completion = 70.0
            approval_status = 'approved'
        elif loan.status == 'returned':
            stage = 'Loan returned'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        elif loan.status == 'rejected':
            stage = 'Rejected'
            blocker = 'Update the loan order and resubmit it for approval.'
            completion = 25.0
            approval_status = 'rejected'
        elif loan.status == 'cancelled':
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(loan)
            completion = 100.0
            approval_status = 'cancelled'

        return {
            'objectCode': 'AssetLoan',
            'businessId': str(loan.id),
            'hasSummary': True,
            'status': loan.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(loan, 'return_confirmed_by', None),
                getattr(loan, 'lent_by', None),
                getattr(loan, 'approved_by', None),
                getattr(loan, 'borrower', None),
                getattr(loan, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'itemCount': item_count,
                'overdueDays': overdue_days,
                'borrowerName': self._resolve_owner(getattr(loan, 'borrower', None)),
                'expectedReturnDate': str(loan.expected_return_date or ''),
                'actualReturnDate': str(loan.actual_return_date or ''),
                'cancelReason': cancel_reason,
            },
        }

    def _build_maintenance_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.lifecycle.models import Maintenance

        maintenance = instance
        if not isinstance(maintenance, Maintenance):
            queryset = Maintenance.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            maintenance = queryset.select_related(
                'asset',
                'reporter',
                'technician',
                'verified_by',
                'created_by',
            ).first()

        if maintenance is None:
            return fallback

        is_verified = bool(maintenance.verified_by_id and maintenance.verified_at)
        fault_photo_count = len(maintenance.fault_photo_urls or [])
        cancel_reason = self._resolve_custom_field_text(maintenance, 'cancel_reason')

        stage = 'Reported'
        blocker = 'Assign a technician and schedule the repair work.'
        completion = 20.0

        if maintenance.status == 'assigned':
            stage = 'Technician assigned'
            blocker = 'Start maintenance work to continue closure.'
            completion = 45.0
        elif maintenance.status == 'processing':
            stage = 'Maintenance in progress'
            blocker = 'Complete repair work and record the repair result.'
            completion = 70.0
        elif maintenance.status == 'completed':
            if is_verified:
                stage = 'Verified and closed'
                blocker = ''
                completion = 100.0
            else:
                stage = 'Completed, awaiting verification'
                blocker = 'Verify the maintenance result to finish closure.'
                completion = 90.0
        elif maintenance.status == 'cancelled':
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(maintenance)
            completion = 100.0

        return {
            'objectCode': 'Maintenance',
            'businessId': str(maintenance.id),
            'hasSummary': True,
            'status': maintenance.status,
            'approvalStatus': 'approved' if is_verified else None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(maintenance, 'technician', None),
                getattr(maintenance, 'reporter', None),
                getattr(maintenance, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'assetCode': str(getattr(getattr(maintenance, 'asset', None), 'asset_code', '') or ''),
                'technicianName': self._resolve_owner(getattr(maintenance, 'technician', None)),
                'totalCost': self._serialize_number(maintenance.total_cost),
                'workHours': self._serialize_number(maintenance.work_hours),
                'faultPhotoCount': fault_photo_count,
                'isVerified': is_verified,
                'cancelReason': cancel_reason,
            },
        }

    def _build_disposal_request_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from django.db.models import Sum

        from apps.lifecycle.models import DisposalRequest, DisposalRequestStatus

        request = instance
        if not isinstance(request, DisposalRequest):
            queryset = DisposalRequest.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            request = queryset.select_related(
                'applicant',
                'current_approver',
                'created_by',
            ).prefetch_related('items').first()

        if request is None:
            return fallback

        items = request.items.filter(is_deleted=False)
        item_count = items.count()
        appraised_item_count = items.filter(appraised_by__isnull=False).count()
        executed_item_count = items.filter(disposal_executed=True).count()
        total_net_value = items.aggregate(total=Sum('net_value')).get('total')
        pending_appraisal_count = max(item_count - appraised_item_count, 0)
        pending_execution_count = max(item_count - executed_item_count, 0)
        cancel_reason = self._resolve_custom_field_text(request, 'cancel_reason')

        stage = 'Draft'
        blocker = 'Submit the disposal request for approval.'
        completion = 15.0
        approval_status = 'not_submitted'

        if request.status == DisposalRequestStatus.SUBMITTED:
            stage = 'Awaiting appraisal'
            blocker = 'Start technical appraisal for all disposal items.'
            completion = 35.0
            approval_status = 'pending'
        elif request.status == DisposalRequestStatus.APPRAISING:
            if pending_appraisal_count > 0:
                stage = 'Appraisal in progress'
                blocker = 'Complete appraisal for all disposal items before approval.'
                completion = 55.0
            else:
                stage = 'Ready for approval'
                blocker = 'Approve or reject the disposal request to continue execution.'
                completion = 65.0
            approval_status = 'pending'
        elif request.status == DisposalRequestStatus.APPROVED:
            stage = 'Approved, awaiting execution'
            blocker = 'Start disposal execution and record actual disposal results.'
            completion = 80.0
            approval_status = 'approved'
        elif request.status == DisposalRequestStatus.EXECUTING:
            stage = 'Execution in progress'
            blocker = 'Complete disposal execution for all items.'
            completion = 90.0 if pending_execution_count == 0 else 85.0
            approval_status = 'approved'
        elif request.status == DisposalRequestStatus.COMPLETED:
            stage = 'Disposal completed'
            blocker = ''
            completion = 100.0
            approval_status = 'approved'
        elif request.status == DisposalRequestStatus.REJECTED:
            stage = 'Rejected'
            blocker = 'Update the disposal request and resubmit it for approval.'
            completion = 25.0
            approval_status = 'rejected'
        elif request.status == DisposalRequestStatus.CANCELLED:
            stage = 'Cancelled'
            blocker = self._build_cancelled_blocker(request)
            completion = 100.0
            approval_status = 'cancelled'

        return {
            'objectCode': 'DisposalRequest',
            'businessId': str(request.id),
            'hasSummary': True,
            'status': request.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(request, 'current_approver', None),
                getattr(request, 'applicant', None),
                getattr(request, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'itemCount': item_count,
                'appraisedItemCount': appraised_item_count,
                'pendingAppraisalCount': pending_appraisal_count,
                'executedItemCount': executed_item_count,
                'pendingExecutionCount': pending_execution_count,
                'totalNetValue': self._serialize_number(total_net_value),
                'disposalTypeLabel': str(request.get_disposal_type_display() or ''),
                'cancelReason': cancel_reason,
            },
        }

    def _build_insurance_policy_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.insurance.models import InsurancePolicy

        policy = instance
        if not isinstance(policy, InsurancePolicy):
            queryset = InsurancePolicy.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            policy = queryset.select_related('company', 'created_by').prefetch_related('insured_assets', 'payments', 'claims').first()

        if policy is None:
            return fallback

        pending_payment_count = policy.payments.filter(
            is_deleted=False,
            status__in=['pending', 'partial', 'overdue'],
        ).count()
        overdue_payment_count = policy.payments.filter(
            is_deleted=False,
            status='overdue',
        ).count()
        open_claim_count = policy.claims.filter(is_deleted=False).exclude(status='closed').count()
        cancel_reason = self._resolve_custom_field_text(policy, 'cancel_reason')
        completion = 15.0
        stage = 'Draft'
        blocker = 'Activate the policy to start coverage and generate premium payments.'

        if policy.status == 'active':
            stage = 'Active coverage'
            completion = 90.0
            blocker = ''
            if pending_payment_count > 0 and open_claim_count > 0:
                blocker = 'Resolve outstanding premiums and open claims before closing the policy.'
                completion = 55.0
            elif pending_payment_count > 0:
                blocker = 'Settle or waive outstanding premiums before closing the policy.'
                completion = 60.0
            elif open_claim_count > 0:
                blocker = 'Resolve open claim records before closing the policy.'
                completion = 70.0
            elif bool(policy.is_expiring_soon):
                blocker = 'Prepare renewal or closure before the policy expires.'
                completion = 85.0
        elif policy.status == 'expired':
            stage = 'Expired'
            completion = 100.0
            blocker = ''
            if pending_payment_count > 0:
                blocker = 'Outstanding premium payments remain open.'
                completion = 75.0
            elif open_claim_count > 0:
                blocker = 'Open claim records must be resolved before the policy can be fully closed.'
                completion = 80.0
        elif policy.status == 'cancelled':
            stage = 'Cancelled'
            completion = 100.0
            blocker = self._build_cancelled_blocker(policy)
        elif policy.status == 'terminated':
            stage = 'Terminated'
            completion = 100.0
            blocker = ''
        elif policy.status == 'renewed':
            stage = 'Renewed'
            completion = 100.0
            blocker = ''

        return {
            'objectCode': 'InsurancePolicy',
            'businessId': str(policy.id),
            'hasSummary': True,
            'status': policy.status,
            'approvalStatus': None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(getattr(policy, 'created_by', None)),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'insuredAssetCount': int(policy.total_insured_assets or 0),
                'claimCount': int(policy.total_claims or 0),
                'openClaimCount': open_claim_count,
                'pendingPaymentCount': pending_payment_count,
                'overduePaymentCount': overdue_payment_count,
                'unpaidPremium': self._serialize_number(policy.unpaid_premium),
                'daysUntilExpiry': policy.days_until_expiry,
                'isExpiringSoon': bool(policy.is_expiring_soon),
                'cancelReason': cancel_reason,
            },
        }

    def _build_claim_record_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.insurance.models import ClaimRecord

        claim = instance
        if not isinstance(claim, ClaimRecord):
            queryset = ClaimRecord.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            claim = queryset.select_related('policy', 'policy__company', 'asset', 'created_by').first()

        if claim is None:
            return fallback

        status_to_summary = {
            'reported': ('Reported', 'Assign investigation and review incident details.', 20.0, 'pending'),
            'investigating': ('Investigating', 'Finish investigation and approve or reject the claim.', 40.0, 'pending'),
            'approved': ('Approved for settlement', 'Record settlement payment to continue closure.', 70.0, 'approved'),
            'paid': ('Paid, awaiting closure', 'Close the claim after payment confirmation.', 90.0, 'approved'),
            'rejected': ('Rejected', 'Close the claim after communicating the rejection result.', 85.0, 'rejected'),
            'closed': ('Closed', '', 100.0, 'closed'),
        }
        stage, blocker, completion, approval_status = status_to_summary.get(
            claim.status,
            ('Reported', 'Assign investigation and review incident details.', 20.0, 'pending'),
        )

        return {
            'objectCode': 'ClaimRecord',
            'businessId': str(claim.id),
            'hasSummary': True,
            'status': claim.status,
            'approvalStatus': approval_status,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                claim.adjuster_name,
                getattr(claim, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'claimedAmount': self._serialize_number(claim.claimed_amount),
                'approvedAmount': self._serialize_number(claim.approved_amount),
                'paidAmount': self._serialize_number(claim.paid_amount),
                'payoutRatio': round(float(claim.payout_ratio or 0), 2),
            },
        }

    def _build_leasing_contract_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.leasing.models import LeaseContract

        contract = instance
        if not isinstance(contract, LeaseContract):
            queryset = LeaseContract.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            contract = queryset.select_related('created_by', 'approved_by').prefetch_related('items', 'payments', 'returns').first()

        if contract is None:
            return fallback

        leased_asset_count = contract.items.filter(is_deleted=False).count()
        returned_asset_count = contract.items.filter(
            is_deleted=False,
            actual_end_date__isnull=False,
        ).count()
        unreturned_asset_count = max(leased_asset_count - returned_asset_count, 0)
        open_payment_count = contract.payments.filter(
            is_deleted=False,
            status__in=['pending', 'partial', 'overdue'],
        ).count()
        overdue_payment_count = contract.payments.filter(
            is_deleted=False,
            status='overdue',
        ).count()
        unsettled_damage_count = contract.returns.filter(
            is_deleted=False,
            condition__in=self._LEASE_DAMAGE_CONDITIONS,
            damage_fee__lte=0,
            deposit_deduction__lte=0,
        ).count()
        completion = 10.0
        blocker = 'Activate the contract before assets can be delivered.'
        stage = 'Draft'

        if contract.status == 'active':
            stage = 'Active lease'
            completion = 85.0
            blocker = ''
            if unreturned_asset_count > 0:
                blocker = 'Record all asset returns before completing the contract.'
                completion = 45.0
            elif open_payment_count > 0:
                blocker = 'Collect, waive, or settle remaining rent before completing the contract.'
                completion = 60.0
            elif unsettled_damage_count > 0:
                blocker = 'Resolve damage charges from returned assets before completing the contract.'
                completion = 75.0
        elif contract.status == 'suspended':
            stage = 'Suspended'
            completion = 70.0
            blocker = 'Reactivate the contract or resolve the suspension reason before closing it.'
            if unreturned_asset_count > 0:
                blocker = 'Record all asset returns before completing the contract.'
                completion = 45.0
            elif open_payment_count > 0:
                blocker = 'Collect, waive, or settle remaining rent before completing the contract.'
                completion = 60.0
        elif contract.status == 'completed':
            stage = 'Completed'
            completion = 100.0
            blocker = ''
        elif contract.status == 'terminated':
            stage = 'Terminated'
            completion = 100.0
            blocker = ''
        elif contract.status == 'overdue':
            stage = 'Overdue'
            completion = 50.0
            blocker = 'Resolve overdue payments and outstanding returns before completing the contract.'

        return {
            'objectCode': 'LeasingContract',
            'businessId': str(contract.id),
            'hasSummary': True,
            'status': contract.status,
            'approvalStatus': 'approved' if getattr(contract, 'approved_by_id', None) else None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(contract, 'approved_by', None),
                getattr(contract, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'leasedAssetCount': leased_asset_count,
                'returnedAssetCount': returned_asset_count,
                'pendingReturnCount': unreturned_asset_count,
                'openPaymentCount': open_payment_count,
                'overduePaymentCount': overdue_payment_count,
                'unsettledDamageCount': unsettled_damage_count,
                'unpaidAmount': self._serialize_number(contract.unpaid_amount()),
                'daysRemaining': contract.days_remaining(),
            },
        }

    def _build_asset_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.assets.models import Asset
        from apps.finance.models import FinanceVoucher
        from apps.inventory.models import InventoryDifference, InventoryFollowUp
        from apps.lifecycle.models import AssetWarrantyStatus, DisposalRequest
        from django.db.models import Q

        asset = instance
        if not isinstance(asset, Asset):
            queryset = Asset.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            asset = queryset.select_related(
                'custodian',
                'user',
                'created_by',
                'source_receipt',
                'source_purchase_request',
            ).first()

        if asset is None:
            return fallback

        active_project_allocation_count = asset.project_allocations.filter(
            is_deleted=False,
            return_status='in_use',
        ).count()
        open_pickup_count = asset.pickup_items.filter(
            is_deleted=False,
            pickup__is_deleted=False,
            pickup__status__in=['pending', 'approved'],
        ).count()
        open_transfer_count = asset.transfer_items.filter(
            is_deleted=False,
            transfer__is_deleted=False,
            transfer__status__in=['pending', 'out_approved', 'approved'],
        ).count()
        open_return_count = asset.return_items.filter(
            is_deleted=False,
            asset_return__is_deleted=False,
            asset_return__status='pending',
        ).count()
        open_loan_count = asset.loan_items.filter(
            is_deleted=False,
            loan__is_deleted=False,
            loan__status__in=['approved', 'borrowed', 'overdue'],
        ).count()
        open_maintenance_count = asset.maintenance_records.filter(
            is_deleted=False,
        ).exclude(
            status__in=['completed', 'cancelled'],
        ).count()
        open_disposal_count = DisposalRequest.all_objects.filter(
            organization_id=asset.organization_id,
            is_deleted=False,
            items__asset=asset,
        ).exclude(
            status__in=['completed', 'cancelled', 'rejected'],
        ).distinct().count()
        pending_inventory_difference_count = asset.inventory_differences.filter(
            is_deleted=False,
        ).exclude(
            status__in=[InventoryDifference.STATUS_CLOSED, InventoryDifference.STATUS_IGNORED],
        ).count()
        pending_inventory_follow_up_count = asset.inventory_follow_up_tasks.filter(
            is_deleted=False,
            status=InventoryFollowUp.STATUS_PENDING,
        ).count()
        active_warranty_count = asset.warranties.filter(
            is_deleted=False,
            status__in=[
                AssetWarrantyStatus.ACTIVE,
                AssetWarrantyStatus.EXPIRING,
                AssetWarrantyStatus.CLAIMED,
            ],
        ).count()
        pending_depreciation_count = asset.depreciation_records.filter(
            is_deleted=False,
        ).exclude(
            status='posted',
        ).count()
        linked_finance_vouchers = FinanceVoucher.all_objects.filter(
            organization_id=asset.organization_id,
            is_deleted=False,
            custom_fields__asset_id_index__icontains=f'|{asset.id}|',
        )
        linked_finance_voucher_count = linked_finance_vouchers.count()
        open_finance_voucher_count = linked_finance_vouchers.filter(
            Q(status__in=['draft', 'submitted', 'approved', 'rejected']) |
            Q(status='posted', erp_voucher_no=''),
        ).count()
        latest_finance_voucher = linked_finance_vouchers.order_by('-voucher_date', '-created_at').first()

        stage = 'Asset record aligned'
        blocker = ''
        completion = 100.0

        if open_disposal_count > 0:
            stage = 'Disposal in progress'
            blocker = 'Finish disposal execution and downstream accounting before considering the asset closed.'
            completion = 35.0
        elif open_maintenance_count > 0:
            stage = 'Maintenance in progress'
            blocker = 'Complete maintenance and restore the asset to service before closure.'
            completion = 50.0
        elif open_transfer_count > 0:
            stage = 'Transfer in progress'
            blocker = 'Complete or cancel active transfer orders before closing the asset lifecycle.'
            completion = 55.0
        elif open_return_count > 0:
            stage = 'Return in progress'
            blocker = 'Confirm or cancel pending return orders before closing the asset lifecycle.'
            completion = 58.0
        elif open_loan_count > 0:
            stage = 'Loan in progress'
            blocker = 'Complete the loan return flow before closing the asset lifecycle.'
            completion = 60.0
        elif open_pickup_count > 0:
            stage = 'Pickup in progress'
            blocker = 'Complete or reject active pickup orders before closing the asset lifecycle.'
            completion = 62.0
        elif pending_inventory_difference_count > 0 or pending_inventory_follow_up_count > 0:
            stage = 'Inventory exception pending'
            blocker = 'Resolve inventory differences and manual follow-up tasks before closure.'
            completion = 65.0
        elif active_project_allocation_count > 0:
            stage = 'Allocated to project'
            blocker = 'Return or transfer the asset before closing the project allocation chain.'
            completion = 80.0
        elif pending_depreciation_count > 0:
            stage = 'Depreciation posting pending'
            blocker = 'Post or resolve outstanding depreciation records before accounting closure.'
            completion = 82.0
        elif open_finance_voucher_count > 0:
            stage = 'Finance posting pending'
            blocker = 'Submit, approve, and post linked finance vouchers to complete financial closure.'
            completion = 85.0
        elif str(getattr(asset, 'asset_status', '') or '').strip() in {'scrapped', 'disposed'} and active_warranty_count > 0:
            stage = 'Warranty closure pending'
            blocker = 'Close or cancel active warranties before considering the asset fully closed.'
            completion = 92.0
        elif str(getattr(asset, 'asset_status', '') or '').strip() in {'scrapped', 'disposed'}:
            stage = 'Lifecycle completed'
            blocker = ''
            completion = 100.0

        return {
            'objectCode': 'Asset',
            'businessId': str(asset.id),
            'hasSummary': True,
            'status': asset.asset_status,
            'approvalStatus': None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(asset, 'custodian', None),
                getattr(asset, 'user', None),
                getattr(asset, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'activeProjectAllocationCount': active_project_allocation_count,
                'openPickupCount': open_pickup_count,
                'openTransferCount': open_transfer_count,
                'openReturnCount': open_return_count,
                'openLoanCount': open_loan_count,
                'openMaintenanceCount': open_maintenance_count,
                'openDisposalCount': open_disposal_count,
                'pendingInventoryDifferenceCount': pending_inventory_difference_count,
                'pendingInventoryFollowUpCount': pending_inventory_follow_up_count,
                'activeWarrantyCount': active_warranty_count,
                'pendingDepreciationCount': pending_depreciation_count,
                'linkedFinanceVoucherCount': linked_finance_voucher_count,
                'openFinanceVoucherCount': open_finance_voucher_count,
                'latestFinanceVoucherNo': str(getattr(latest_finance_voucher, 'voucher_no', '') or ''),
                'latestFinanceVoucherStatus': str(getattr(latest_finance_voucher, 'status', '') or ''),
                'sourceReceiptNo': str(getattr(getattr(asset, 'source_receipt', None), 'receipt_no', '') or ''),
                'sourcePurchaseRequestNo': str(getattr(getattr(asset, 'source_purchase_request', None), 'request_no', '') or ''),
            },
        }

    def _build_asset_project_summary(
        self,
        *,
        business_id: str,
        instance: Optional[Any],
        fallback: Dict[str, Any],
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        from apps.assets.models import AssetReturn
        from apps.projects.models import AssetProject

        project = instance
        if not isinstance(project, AssetProject):
            queryset = AssetProject.all_objects.filter(id=business_id, is_deleted=False)
            if organization_id:
                queryset = queryset.filter(organization_id=organization_id)
            project = queryset.select_related('project_manager', 'created_by').first()

        if project is None:
            return fallback

        total_assets = project.project_assets.filter(is_deleted=False).count()
        active_assets = project.project_assets.filter(
            is_deleted=False,
            return_status='in_use',
        ).count()
        member_count = project.members.filter(
            is_deleted=False,
            is_active=True,
        ).count()
        pending_return_count = AssetReturn.all_objects.filter(
            organization_id=project.organization_id,
            is_deleted=False,
            status='pending',
            items__project_allocation__project_id=project.id,
        ).distinct().count()
        processed_return_count = AssetReturn.all_objects.filter(
            organization_id=project.organization_id,
            is_deleted=False,
            items__project_allocation__project_id=project.id,
        ).exclude(status='pending').distinct().count()

        progress = 0.0
        if getattr(project, 'total_milestones', 0):
            progress = round(
                (float(project.completed_milestones or 0) / float(project.total_milestones or 1)) * 100,
                2,
            )

        if project.status == 'completed':
            stage = 'Project closed'
            blocker = ''
            completion = 100.0
        elif project.status == 'cancelled':
            stage = 'Project cancelled'
            blocker = ''
            completion = 100.0
        elif active_assets > 0:
            stage = 'Active asset allocations'
            blocker = 'Return or transfer active project assets before closing the project.'
            completion = 70.0
        elif pending_return_count > 0:
            stage = 'Pending asset returns'
            blocker = 'Complete or cancel pending return orders before closing the project.'
            completion = 85.0
        elif project.status == 'planning':
            stage = 'Planning'
            blocker = 'Start the project and complete key milestones before closure.'
            completion = 25.0
        elif project.status == 'suspended':
            stage = 'Ready for closure'
            blocker = ''
            completion = 90.0
        else:
            stage = 'Ready for closure'
            blocker = ''
            completion = 90.0

        return {
            'objectCode': 'AssetProject',
            'businessId': str(project.id),
            'hasSummary': True,
            'status': project.status,
            'approvalStatus': None,
            'workflowInstanceId': None,
            'owner': self._resolve_owner(
                getattr(project, 'project_manager', None),
                getattr(project, 'created_by', None),
            ),
            'stage': stage,
            'blocker': blocker,
            'completion': completion,
            'completionDisplay': self._format_completion(completion),
            'metrics': {
                'totalAssets': total_assets,
                'activeAssets': active_assets,
                'memberCount': member_count,
                'progress': progress,
                'pendingReturnCount': pending_return_count,
                'processedReturnCount': processed_return_count,
            },
        }

    @staticmethod
    def _build_empty_summary(*, object_code: str, business_id: str) -> Dict[str, Any]:
        return {
            'objectCode': object_code,
            'businessId': business_id,
            'hasSummary': False,
            'status': None,
            'approvalStatus': None,
            'workflowInstanceId': None,
            'owner': '',
            'stage': '',
            'blocker': '',
            'completion': None,
            'completionDisplay': None,
            'metrics': {},
        }

    @staticmethod
    def _resolve_owner(*candidates: Any) -> str:
        for candidate in candidates:
            if candidate is None:
                continue
            if isinstance(candidate, str):
                normalized = candidate.strip()
                if normalized:
                    return normalized
                continue

            full_name_getter = getattr(candidate, 'get_full_name', None)
            if callable(full_name_getter):
                full_name = str(full_name_getter() or '').strip()
                if full_name:
                    return full_name

            for attr_name in ('username', 'name', 'short_name', 'code', 'id'):
                value = str(getattr(candidate, attr_name, '') or '').strip()
                if value:
                    return value
        return ''

    @staticmethod
    def _format_completion(completion: Optional[float]) -> Optional[str]:
        if completion is None:
            return None
        normalized = round(float(completion or 0), 2)
        if normalized.is_integer():
            return f'{int(normalized)}%'
        return f'{normalized}%'

    @staticmethod
    def _serialize_number(value: Any) -> Optional[float]:
        if value is None or value == '':
            return None
        return float(value)
