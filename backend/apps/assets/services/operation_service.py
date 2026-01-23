"""
Services for Asset Operation Models (Pickup, Transfer, Return, Loan).

All services inherit from BaseCRUDService for standard CRUD operations
and extend with business-specific methods.
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError, PermissionDenied
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import (
    Asset,
    AssetPickup,
    PickupItem,
    AssetTransfer,
    TransferItem,
    AssetReturn,
    ReturnItem,
    AssetLoan,
    LoanItem,
)


# ========== Pickup Order Service ==========

class AssetPickupService(BaseCRUDService):
    """
    Service for Asset Pickup Order operations.

    Extends BaseCRUDService with:
    - Approval workflow
    - Asset status update on approval
    - Pickup completion tracking
    """

    def __init__(self):
        super().__init__(AssetPickup)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetPickup:
        """
        Create a pickup order with items.

        Args:
            data: Pickup order data
            items: List of items with asset_id and optional quantity/remark
            user: User creating the pickup
            organization_id: Organization ID

        Returns:
            Created pickup order
        """
        # Set applicant to current user if not specified
        if 'applicant_id' not in data and 'applicant' not in data:
            data['applicant_id'] = user.id

        # Set organization
        data['organization_id'] = organization_id

        with transaction.atomic():
            pickup = self.create(data, user)

            # Create items with snapshots
            for item_data in items:
                asset_id = item_data.get('asset_id')
                try:
                    asset = Asset.objects.get(
                        id=asset_id,
                        organization_id=organization_id,
                        is_deleted=False
                    )

                    # Validate asset is available for pickup
                    if asset.asset_status not in ['idle', 'pending']:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not available (status: {asset.get_status_label()})'
                        })

                    PickupItem.objects.create(
                        pickup=pickup,
                        asset=asset,
                        quantity=item_data.get('quantity', 1),
                        remark=item_data.get('remark', ''),
                        snapshot_original_location=asset.location,
                        snapshot_original_custodian=asset.custodian,
                        organization_id=organization_id
                    )
                except Asset.DoesNotExist:
                    raise ValidationError({
                        'asset': f'Asset with ID {asset_id} not found'
                    })

            # Auto-start workflow if enabled
            self._auto_start_workflow(pickup, user, organization_id)

        return pickup

    def _auto_start_workflow(self, pickup: AssetPickup, user, organization_id: str):
        """
        Automatically start workflow for pickup order if a workflow definition exists.

        Args:
            pickup: The pickup order instance
            user: User who created the pickup
            organization_id: Organization ID
        """
        try:
            from apps.workflows.models import WorkflowDefinition
            from apps.workflows.services.workflow_engine import WorkflowEngine

            # Find active workflow definition for asset pickup
            definition = WorkflowDefinition.objects.filter(
                organization_id=organization_id,
                business_object_code='asset_pickup',
                status='published',
                is_deleted=False
            ).first()

            if definition:
                # Start workflow instance
                engine = WorkflowEngine()
                success, instance, error = engine.start_workflow(
                    definition=definition,
                    business_object_code='asset_pickup',
                    business_id=str(pickup.id),
                    business_no=pickup.pickup_no,
                    initiator=user,
                    title=f'Asset Pickup: {pickup.pickup_no}',
                    description=f'Pickup order by {pickup.applicant.username if pickup.applicant else "Unknown"}',
                    priority='normal'
                )

                if success and instance:
                    # Link workflow instance to pickup
                    pickup.workflow_instance = instance
                    pickup.save(update_fields=['workflow_instance'])
        except Exception as e:
            # Log error but don't fail the pickup creation
            # Workflow can be started manually later
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f'Failed to auto-start workflow for pickup {pickup.pickup_no}: {str(e)}')

    def submit_for_approval(self, pickup_id: str, user) -> AssetPickup:
        """
        Submit pickup order for approval.

        Args:
            pickup_id: Pickup order ID
            user: User submitting the request

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id)

        if pickup.status != 'draft':
            raise ValidationError({
                'status': f'Cannot submit pickup with status {pickup.get_status_label()}'
            })

        # Validate that pickup has items
        if pickup.items.count() == 0:
            raise ValidationError({
                'items': 'Cannot submit pickup order without items'
            })

        pickup.status = 'pending'
        pickup.save()

        return pickup

    def approve(
        self,
        pickup_id: str,
        user,
        approval: str,
        comment: str = ''
    ) -> AssetPickup:
        """
        Approve or reject a pickup order.

        Args:
            pickup_id: Pickup order ID
            user: User approving the request
            approval: 'approved' or 'rejected'
            comment: Optional approval comment

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id)

        if pickup.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve pickup with status {pickup.get_status_label()}'
            })

        pickup.approved_by = user
        pickup.approved_at = timezone.now()
        pickup.approval_comment = comment

        if approval == 'approved':
            pickup.status = 'approved'

            # Update asset status and custodian for all items
            for item in pickup.items.all():
                asset = item.asset
                asset.asset_status = 'in_use'
                asset.custodian = pickup.applicant
                asset.department = pickup.department
                asset.save()

                # Log status change
                self._log_asset_status_change(
                    asset,
                    'idle',
                    'in_use',
                    user,
                    f'Approved via pickup order {pickup.pickup_no}'
                )

        else:
            pickup.status = 'rejected'

        pickup.save()
        return pickup

    def complete_pickup(self, pickup_id: str, user) -> AssetPickup:
        """
        Mark pickup order as completed.

        Args:
            pickup_id: Pickup order ID
            user: User completing the pickup

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id)

        if pickup.status != 'approved':
            raise ValidationError({
                'status': f'Cannot complete pickup with status {pickup.get_status_label()}'
            })

        pickup.status = 'completed'
        pickup.completed_at = timezone.now()
        pickup.save()

        return pickup

    def cancel_pickup(self, pickup_id: str, user) -> AssetPickup:
        """
        Cancel a pickup order.

        Args:
            pickup_id: Pickup order ID
            user: User cancelling the request

        Returns:
            Updated pickup order
        """
        pickup = self.get(pickup_id)

        if pickup.status not in ['draft', 'pending']:
            raise ValidationError({
                'status': f'Cannot cancel pickup with status {pickup.get_status_label()}'
            })

        pickup.status = 'cancelled'
        pickup.save()

        return pickup

    def get_pending_approvals(self, organization_id: str) -> List[AssetPickup]:
        """Get all pending pickup orders for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'pending'},
            order_by='-created_at'
        )

    def _log_asset_status_change(
        self,
        asset: Asset,
        old_status: str,
        new_status: str,
        user,
        reason: str
    ):
        """Log asset status change."""
        from apps.assets.models import AssetStatusLog
        AssetStatusLog.objects.create(
            organization=asset.organization,
            asset=asset,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            created_by=user
        )


# ========== Transfer Order Service ==========

class AssetTransferService(BaseCRUDService):
    """
    Service for Asset Transfer Order operations.

    Extends BaseCRUDService with:
    - Dual approval workflow (from/to departments)
    - Asset transfer completion
    """

    def __init__(self):
        super().__init__(AssetTransfer)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetTransfer:
        """Create a transfer order with items."""
        # Validate departments are different
        if data.get('from_department') == data.get('to_department'):
            raise ValidationError({
                'to_department': 'Source and target departments must be different'
            })

        data['organization_id'] = organization_id

        with transaction.atomic():
            transfer = self.create(data, user)

            # Create items with snapshots
            for item_data in items:
                asset_id = item_data.get('asset_id')
                try:
                    asset = Asset.objects.get(
                        id=asset_id,
                        organization_id=organization_id,
                        is_deleted=False
                    )

                    TransferItem.objects.create(
                        transfer=transfer,
                        asset=asset,
                        from_location=asset.location,
                        from_custodian=asset.custodian,
                        to_location_id=item_data.get('to_location_id'),
                        remark=item_data.get('remark', ''),
                        organization_id=organization_id
                    )
                except Asset.DoesNotExist:
                    raise ValidationError({
                        'asset': f'Asset with ID {asset_id} not found'
                    })

        return transfer

    def submit_for_approval(self, transfer_id: str, user) -> AssetTransfer:
        """Submit transfer order for approval."""
        transfer = self.get(transfer_id)

        if transfer.status != 'draft':
            raise ValidationError({
                'status': f'Cannot submit transfer with status {transfer.get_status_label()}'
            })

        if transfer.items.count() == 0:
            raise ValidationError({
                'items': 'Cannot submit transfer order without items'
            })

        transfer.status = 'pending'
        transfer.save()

        return transfer

    def approve_from(
        self,
        transfer_id: str,
        user,
        comment: str = ''
    ) -> AssetTransfer:
        """Approve from source department."""
        transfer = self.get(transfer_id)

        if transfer.status != 'pending':
            raise ValidationError({
                'status': 'Transfer must be in pending status for source approval'
            })

        transfer.status = 'out_approved'
        transfer.from_approved_by = user
        transfer.from_approved_at = timezone.now()
        transfer.from_approve_comment = comment
        transfer.save()

        return transfer

    def approve_to(
        self,
        transfer_id: str,
        user,
        comment: str = ''
    ) -> AssetTransfer:
        """Approve from target department."""
        transfer = self.get(transfer_id)

        if transfer.status != 'out_approved':
            raise ValidationError({
                'status': 'Transfer must be approved by source department first'
            })

        transfer.status = 'approved'
        transfer.to_approved_by = user
        transfer.to_approved_at = timezone.now()
        transfer.to_approve_comment = comment
        transfer.save()

        return transfer

    def complete_transfer(self, transfer_id: str, user) -> AssetTransfer:
        """Complete the transfer and update assets."""
        transfer = self.get(transfer_id)

        if transfer.status != 'approved':
            raise ValidationError({
                'status': f'Cannot complete transfer with status {transfer.get_status_label()}'
            })

        with transaction.atomic():
            for item in transfer.items.all():
                asset = item.asset
                asset.department = transfer.to_department
                asset.location = item.to_location
                asset.custodian = None  # Clear custodian on transfer
                asset.save()

            transfer.status = 'completed'
            transfer.completed_at = timezone.now()
            transfer.save()

        return transfer

    def get_pending_transfers(self, organization_id: str) -> List[AssetTransfer]:
        """Get all pending transfers for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status__in': ['pending', 'out_approved']},
            order_by='-created_at'
        )


# ========== Return Order Service ==========

class AssetReturnService(BaseCRUDService):
    """
    Service for Asset Return Order operations.

    Extends BaseCRUDService with:
    - Return confirmation
    - Asset status update on completion
    """

    def __init__(self):
        super().__init__(AssetReturn)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetReturn:
        """Create a return order with items."""
        # Set returner to current user
        if 'returner_id' not in data and 'returner' not in data:
            data['returner_id'] = user.id

        data['organization_id'] = organization_id

        with transaction.atomic():
            return_order = self.create(data, user)

            # Create items
            for item_data in items:
                asset_id = item_data.get('asset_id')
                try:
                    asset = Asset.objects.get(
                        id=asset_id,
                        organization_id=organization_id,
                        is_deleted=False
                    )

                    # Validate asset custodian
                    if asset.custodian_id != user.id:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not assigned to you'
                        })

                    ReturnItem.objects.create(
                        asset_return=return_order,
                        asset=asset,
                        asset_status=item_data.get('asset_status', 'idle'),
                        condition_description=item_data.get('condition_description', ''),
                        remark=item_data.get('remark', ''),
                        organization_id=organization_id
                    )
                except Asset.DoesNotExist:
                    raise ValidationError({
                        'asset': f'Asset with ID {asset_id} not found'
                    })

        return return_order

    def confirm_return(
        self,
        return_id: str,
        user,
    ) -> AssetReturn:
        """
        Confirm and complete a return order.

        Args:
            return_id: Return order ID
            user: User confirming the return

        Returns:
            Updated return order
        """
        return_order = self.get(return_id)

        if return_order.status != 'pending':
            raise ValidationError({
                'status': f'Cannot confirm return with status {return_order.get_status_label()}'
            })

        with transaction.atomic():
            for item in return_order.items.all():
                asset = item.asset
                asset.asset_status = item.asset_status
                asset.custodian = None
                asset.location = return_order.return_location
                asset.save()

            return_order.status = 'completed'
            return_order.confirmed_by = user
            return_order.confirmed_at = timezone.now()
            return_order.completed_at = timezone.now()
            return_order.save()

        return return_order

    def reject_return(
        self,
        return_id: str,
        user,
        reason: str = ''
    ) -> AssetReturn:
        """Reject a return order."""
        return_order = self.get(return_id)

        if return_order.status != 'pending':
            raise ValidationError({
                'status': f'Cannot reject return with status {return_order.get_status_label()}'
            })

        return_order.status = 'rejected'
        return_order.reject_reason = reason
        return_order.save()

        return return_order

    def get_pending_returns(self, organization_id: str) -> List[AssetReturn]:
        """Get all pending returns for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'pending'},
            order_by='-created_at'
        )


# ========== Loan Order Service ==========

class AssetLoanService(BaseCRUDService):
    """
    Service for Asset Loan Order operations.

    Extends BaseCRUDService with:
    - Loan approval workflow
    - Borrow confirmation
    - Return confirmation
    - Overdue checking
    """

    def __init__(self):
        super().__init__(AssetLoan)

    def create_with_items(
        self,
        data: Dict,
        items: List[Dict],
        user,
        organization_id: str
    ) -> AssetLoan:
        """Create a loan order with items."""
        # Validate dates
        from datetime import timedelta

        borrow_date = data.get('borrow_date')
        return_date = data.get('expected_return_date')

        if borrow_date and return_date and return_date < borrow_date:
            raise ValidationError({
                'expected_return_date': 'Return date must be after borrow date'
            })

        # Limit loan duration to 90 days
        if borrow_date and return_date:
            max_date = borrow_date + timedelta(days=90)
            if return_date > max_date:
                raise ValidationError({
                    'expected_return_date': 'Loan duration cannot exceed 90 days'
                })

        # Set borrower to current user
        if 'borrower_id' not in data and 'borrower' not in data:
            data['borrower_id'] = user.id

        data['organization_id'] = organization_id

        with transaction.atomic():
            loan = self.create(data, user)

            # Create items
            for item_data in items:
                asset_id = item_data.get('asset_id')
                try:
                    asset = Asset.objects.get(
                        id=asset_id,
                        organization_id=organization_id,
                        is_deleted=False
                    )

                    # Validate asset is available
                    if asset.asset_status not in ['idle', 'pending']:
                        raise ValidationError({
                            'asset': f'Asset {asset.asset_name} is not available'
                        })

                    LoanItem.objects.create(
                        loan=loan,
                        asset=asset,
                        remark=item_data.get('remark', ''),
                        organization_id=organization_id
                    )
                except Asset.DoesNotExist:
                    raise ValidationError({
                        'asset': f'Asset with ID {asset_id} not found'
                    })

        return loan

    def approve_loan(
        self,
        loan_id: str,
        user,
        approval: str,
        comment: str = ''
    ) -> AssetLoan:
        """Approve or reject a loan order."""
        loan = self.get(loan_id)

        if loan.status != 'pending':
            raise ValidationError({
                'status': f'Cannot approve loan with status {loan.get_status_label()}'
            })

        loan.approved_by = user
        loan.approved_at = timezone.now()
        loan.approval_comment = comment

        if approval == 'approved':
            loan.status = 'approved'
        else:
            loan.status = 'rejected'

        loan.save()
        return loan

    def confirm_borrow(self, loan_id: str, user) -> AssetLoan:
        """Confirm that assets have been lent out."""
        loan = self.get(loan_id)

        if loan.status != 'approved':
            raise ValidationError({
                'status': f'Cannot confirm borrow with status {loan.get_status_label()}'
            })

        with transaction.atomic():
            # Update asset status
            for item in loan.items.all():
                asset = item.asset
                asset.asset_status = 'in_use'
                asset.custodian = loan.borrower
                asset.save()

            loan.status = 'borrowed'
            loan.lent_by = user
            loan.lent_at = timezone.now()
            loan.save()

        return loan

    def confirm_return(
        self,
        loan_id: str,
        user,
        condition: str = 'good',
        comment: str = ''
    ) -> AssetLoan:
        """Confirm that assets have been returned."""
        loan = self.get(loan_id)

        if loan.status not in ['borrowed', 'overdue']:
            raise ValidationError({
                'status': f'Cannot confirm return with status {loan.get_status_label()}'
            })

        with transaction.atomic():
            # Update asset status based on condition
            for item in loan.items.all():
                asset = item.asset
                if condition == 'good':
                    asset.asset_status = 'idle'
                elif condition in ['minor_damage', 'major_damage']:
                    asset.asset_status = 'maintenance'
                elif condition == 'lost':
                    asset.asset_status = 'lost'

                asset.custodian = None
                asset.save()

            loan.status = 'returned'
            loan.actual_return_date = timezone.now().date()
            loan.return_confirmed_by = user
            loan.returned_at = timezone.now()
            loan.asset_condition = condition
            loan.return_comment = comment
            loan.save()

        return loan

    def check_overdue_loans(self, organization_id: str) -> int:
        """
        Check and update overdue loans.

        Returns:
            Number of loans marked as overdue
        """
        today = timezone.now().date()
        overdue_loans = AssetLoan.objects.filter(
            organization_id=organization_id,
            status='borrowed',
            expected_return_date__lt=today,
            is_deleted=False
        )

        count = overdue_loans.update(status='overdue')
        return count

    def get_overdue_loans(self, organization_id: str) -> List[AssetLoan]:
        """Get all overdue loans for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'overdue'},
            order_by='-expected_return_date'
        )

    def get_active_loans(self, organization_id: str) -> List[AssetLoan]:
        """Get all active (borrowed) loans for an organization."""
        return self.query(
            filters={'organization_id': organization_id, 'status': 'borrowed'},
            order_by='-expected_return_date'
        )
