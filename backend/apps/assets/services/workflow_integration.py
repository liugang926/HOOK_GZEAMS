"""
Workflow Integration Service for Asset Operations

Integrates asset operations (pickup, transfer, loan, return) with workflow engine.
Handles automatic workflow启动 on operation submission and asset status updates on workflow completion.
"""
from typing import Dict, Any, Optional
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from apps.workflows.models import WorkflowDefinition, WorkflowInstance
from apps.workflows.services.workflow_engine import WorkflowEngine


class AssetWorkflowIntegration:
    """
    Service to integrate asset operations with workflow.

    Handles:
    - Starting workflow when operation is submitted
    - Updating operation status when workflow completes
    - Triggering asset status updates
    """

    # Workflow process keys for different operation types
    PROCESS_PICKUP = 'asset_pickup'
    PROCESS_TRANSFER = 'asset_transfer'
    PROCESS_LOAN = 'asset_loan'
    PROCESS_RETURN = 'asset_return'

    @classmethod
    def get_workflow_definition(cls, process_key: str, organization_id: str) -> Optional[WorkflowDefinition]:
        """
        Get published workflow definition for a process.

        Args:
            process_key: Workflow process key (e.g., 'asset_pickup')
            organization_id: Organization ID to scope the search

        Returns:
            WorkflowDefinition if found, None otherwise
        """
        try:
            return WorkflowDefinition.objects.filter(
                business_object_code=process_key,
                status='published',
                organization_id=organization_id,
                is_deleted=False
            ).first()
        except Exception as e:
            logger.error(f"Error getting workflow definition: {e}")
            return None

    @classmethod
    def start_operation_workflow(
        cls,
        process_key: str,
        operation_instance: Any,
        initiator: Any,
        organization_id: str
    ) -> tuple[bool, Optional[WorkflowInstance], Optional[str]]:
        """
        Start workflow for an asset operation.

        Args:
            process_key: Workflow process key (e.g., 'asset_pickup')
            operation_instance: The operation instance (AssetPickup, etc.)
            initiator: User initiating the workflow
            organization_id: Organization ID

        Returns:
            (success, workflow_instance, error)
            - success: True if workflow started or auto-approved, False otherwise
            - workflow_instance: Created WorkflowInstance if started, None if auto-approved
            - error: Error message if failed, None otherwise
        """
        definition = cls.get_workflow_definition(process_key, organization_id)

        if not definition:
            # No workflow defined, auto-approve
            logger.warning(f"No workflow definition found for {process_key}, auto-approving")
            return True, None, None

        engine = WorkflowEngine(definition)

        # Get business number from operation instance
        business_no = (
            getattr(operation_instance, 'pickup_no', None) or
            getattr(operation_instance, 'transfer_no', None) or
            getattr(operation_instance, 'loan_no', None) or
            getattr(operation_instance, 'return_no', None) or
            f"{process_key}-{str(operation_instance.id)[:8]}"
        )

        # Get items count for variables
        items_count = 0
        if hasattr(operation_instance, 'items'):
            items_count = operation_instance.items.count() if hasattr(operation_instance.items, 'count') else len(operation_instance.items.all())

        success, instance, error = engine.start_workflow(
            definition=definition,
            business_object_code=process_key,
            business_id=str(operation_instance.id),
            business_no=business_no,
            initiator=initiator,
            variables={
                'operation_data': {
                    'id': str(operation_instance.id),
                    'type': process_key,
                    'items_count': items_count,
                    'applicant': initiator.username if initiator else 'System'
                }
            }
        )

        return success, instance, error

    @classmethod
    def handle_workflow_completion(
        cls,
        workflow_instance: WorkflowInstance
    ) -> tuple[bool, Optional[str]]:
        """
        Handle workflow completion.

        Update the related operation status and trigger asset updates.

        Args:
            workflow_instance: Completed workflow instance

        Returns:
            (success, error)
        """
        if workflow_instance.status != WorkflowInstance.STATUS_APPROVED:
            return True, None  # No action needed for rejected workflows

        process_key = workflow_instance.business_object_code
        business_id = workflow_instance.business_id

        try:
            if process_key == cls.PROCESS_PICKUP:
                return cls._complete_pickup(business_id, workflow_instance)
            elif process_key == cls.PROCESS_TRANSFER:
                return cls._complete_transfer(business_id, workflow_instance)
            elif process_key == cls.PROCESS_LOAN:
                return cls._complete_loan(business_id, workflow_instance)
            elif process_key == cls.PROCESS_RETURN:
                return cls._complete_return(business_id, workflow_instance)
            else:
                logger.warning(f"Unknown process key: {process_key}")
                return True, None

        except Exception as e:
            logger.error(f"Error handling workflow completion: {e}")
            return False, str(e)

    @classmethod
    def _complete_pickup(cls, business_id: str, workflow_instance: WorkflowInstance) -> tuple[bool, Optional[str]]:
        """Complete pickup operation after workflow approval."""
        from apps.assets.models import AssetPickup
        from apps.assets.services.operation_service import AssetPickupService

        try:
            pickup = AssetPickup.objects.get(id=business_id)
            service = AssetPickupService()

            # Get the approver from workflow
            approver = workflow_instance.initiator
            if workflow_instance.approvals.exists():
                last_approval = workflow_instance.approvals.filter(status='approved').order_by('-approved_at').first()
                if last_approval and last_approval.approver:
                    approver = last_approval.approver

            service.complete_pickup(pickup.id, approver)
            return True, None
        except AssetPickup.DoesNotExist:
            return False, "Pickup order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _complete_transfer(cls, business_id: str, workflow_instance: WorkflowInstance) -> tuple[bool, Optional[str]]:
        """Complete transfer operation after workflow approval."""
        from apps.assets.models import AssetTransfer
        from apps.assets.services.operation_service import AssetTransferService

        try:
            transfer = AssetTransfer.objects.get(id=business_id)
            service = AssetTransferService()

            # Get the approver from workflow
            approver = workflow_instance.initiator
            if workflow_instance.approvals.exists():
                last_approval = workflow_instance.approvals.filter(status='approved').order_by('-approved_at').first()
                if last_approval and last_approval.approver:
                    approver = last_approval.approver

            service.complete_transfer(transfer.id, approver)
            return True, None
        except AssetTransfer.DoesNotExist:
            return False, "Transfer order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _complete_loan(cls, business_id: str, workflow_instance: WorkflowInstance) -> tuple[bool, Optional[str]]:
        """Complete loan operation after workflow approval."""
        from apps.assets.models import AssetLoan
        from apps.assets.services.operation_service import AssetLoanService

        try:
            loan = AssetLoan.objects.get(id=business_id)
            service = AssetLoanService()

            # Get the approver from workflow
            approver = workflow_instance.initiator
            if workflow_instance.approvals.exists():
                last_approval = workflow_instance.approvals.filter(status='approved').order_by('-approved_at').first()
                if last_approval and last_approval.approver:
                    approver = last_approval.approver

            service.confirm_borrow(loan.id, approver)
            return True, None
        except AssetLoan.DoesNotExist:
            return False, "Loan order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _complete_return(cls, business_id: str, workflow_instance: WorkflowInstance) -> tuple[bool, Optional[str]]:
        """Complete return operation after workflow approval."""
        from apps.assets.models import AssetReturn
        from apps.assets.services.operation_service import AssetReturnService

        try:
            return_order = AssetReturn.objects.get(id=business_id)
            service = AssetReturnService()

            # Get the approver from workflow
            approver = workflow_instance.initiator
            if workflow_instance.approvals.exists():
                last_approval = workflow_instance.approvals.filter(status='approved').order_by('-approved_at').first()
                if last_approval and last_approval.approver:
                    approver = last_approval.approver

            service.confirm_return(return_order.id, approver)
            return True, None
        except AssetReturn.DoesNotExist:
            return False, "Return order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def handle_workflow_rejection(
        cls,
        workflow_instance: WorkflowInstance
    ) -> tuple[bool, Optional[str]]:
        """
        Handle workflow rejection.

        Update the related operation status to rejected.

        Args:
            workflow_instance: Rejected workflow instance

        Returns:
            (success, error)
        """
        if workflow_instance.status != WorkflowInstance.STATUS_REJECTED:
            return True, None

        process_key = workflow_instance.business_object_code
        business_id = workflow_instance.business_id

        try:
            if process_key == cls.PROCESS_PICKUP:
                return cls._reject_pickup(business_id)
            elif process_key == cls.PROCESS_TRANSFER:
                return cls._reject_transfer(business_id)
            elif process_key == cls.PROCESS_LOAN:
                return cls._reject_loan(business_id)
            elif process_key == cls.PROCESS_RETURN:
                return cls._reject_return(business_id)
            else:
                return True, None
        except Exception as e:
            logger.error(f"Error handling workflow rejection: {e}")
            return False, str(e)

    @classmethod
    def _reject_pickup(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Reject pickup operation."""
        from apps.assets.models import AssetPickup

        try:
            pickup = AssetPickup.objects.get(id=business_id)
            pickup.status = 'rejected'
            pickup.save(update_fields=['status', 'updated_at'])
            return True, None
        except AssetPickup.DoesNotExist:
            return False, "Pickup order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _reject_transfer(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Reject transfer operation."""
        from apps.assets.models import AssetTransfer

        try:
            transfer = AssetTransfer.objects.get(id=business_id)
            transfer.status = 'rejected'
            transfer.save(update_fields=['status', 'updated_at'])
            return True, None
        except AssetTransfer.DoesNotExist:
            return False, "Transfer order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _reject_loan(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Reject loan operation."""
        from apps.assets.models import AssetLoan

        try:
            loan = AssetLoan.objects.get(id=business_id)
            loan.status = 'rejected'
            loan.save(update_fields=['status', 'updated_at'])
            return True, None
        except AssetLoan.DoesNotExist:
            return False, "Loan order not found"
        except Exception as e:
            return False, str(e)

    @classmethod
    def _reject_return(cls, business_id: str) -> tuple[bool, Optional[str]]:
        """Reject return operation."""
        from apps.assets.models import AssetReturn

        try:
            return_order = AssetReturn.objects.get(id=business_id)
            return_order.status = 'rejected'
            return_order.save(update_fields=['status', 'updated_at'])
            return True, None
        except AssetReturn.DoesNotExist:
            return False, "Return order not found"
        except Exception as e:
            return False, str(e)
