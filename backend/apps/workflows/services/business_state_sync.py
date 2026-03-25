"""
Business State Sync Service.

Synchronizes workflow instance state changes to linked business documents
that inherit from WorkflowStatusMixin. This service is invoked by signal
handlers when workflow lifecycle events fire.
"""
import logging

from django.utils import timezone

from apps.workflows.models import WorkflowInstance

logger = logging.getLogger(__name__)


class BusinessStateSyncService:
    """
    Synchronizes workflow instance state changes to linked business documents.

    Responsibilities:
    1. Resolve the target business model from business_object_code via ObjectRegistry
    2. Update the business document's approval_status field
    3. Call model-specific lifecycle hooks (on_workflow_approved, etc.)
    4. Log all state transitions to WorkflowOperationLog
    """

    # Map workflow instance status → business document approval_status
    STATUS_MAP = {
        'running': 'pending_approval',
        'pending_approval': 'pending_approval',
        'approved': 'approved',
        'rejected': 'rejected',
        'cancelled': 'cancelled',
        'terminated': 'cancelled',
    }

    def sync_business_status(self, instance: WorkflowInstance) -> None:
        """
        Update linked business document status based on workflow state.

        Args:
            instance: WorkflowInstance whose state has changed
        """
        model_class = self._resolve_business_model(instance.business_object_code)
        if model_class is None:
            logger.warning(
                "Could not resolve model for business_object_code=%s, "
                "skipping business status sync.",
                instance.business_object_code,
            )
            return

        # Check that model supports WorkflowStatusMixin
        from apps.common.mixins.workflow_status import WorkflowStatusMixin
        if not issubclass(model_class, WorkflowStatusMixin):
            logger.debug(
                "Model %s does not inherit WorkflowStatusMixin, "
                "skipping business status sync.",
                model_class.__name__,
            )
            return

        business_obj = self._get_business_object(
            model_class, instance.business_id, instance.organization_id
        )
        if business_obj is None:
            logger.warning(
                "Business object not found: model=%s, id=%s, org=%s",
                model_class.__name__,
                instance.business_id,
                instance.organization_id,
            )
            return

        new_status = self.STATUS_MAP.get(instance.status)
        if new_status is None:
            logger.debug(
                "No status mapping for workflow status '%s', skipping.",
                instance.status,
            )
            return

        old_status = business_obj.approval_status
        if old_status == new_status:
            return

        # Update approval_status and related timestamp fields
        update_fields = ['approval_status', 'workflow_instance_id', 'updated_at']
        business_obj.approval_status = new_status
        business_obj.workflow_instance_id = instance.pk

        if new_status == 'pending_approval' and business_obj.submitted_at is None:
            business_obj.submitted_at = timezone.now()
            update_fields.append('submitted_at')

        if new_status == 'approved':
            business_obj.approved_at = timezone.now()
            update_fields.append('approved_at')

        business_obj.save(update_fields=update_fields)

        # Call lifecycle hooks on the business object
        self._invoke_lifecycle_hook(business_obj, new_status)

        # Log the state transition
        self._log_state_transition(instance, old_status, new_status)

        logger.info(
            "Synced business status: %s #%s  %s → %s",
            model_class.__name__,
            instance.business_id,
            old_status,
            new_status,
        )

    def _resolve_business_model(self, business_object_code: str):
        """
        Resolve Django model class from business object code via ObjectRegistry.

        Args:
            business_object_code: The code identifying the business object type

        Returns:
            Django model class or None if not resolvable
        """
        try:
            from apps.system.services.object_registry import ObjectRegistry
            meta = ObjectRegistry.get_or_create_from_db(business_object_code)
            if meta and meta.model_class:
                return meta.model_class
        except Exception:
            logger.exception(
                "Error resolving model for business_object_code=%s",
                business_object_code,
            )
        return None

    def _get_business_object(self, model_class, business_id, org_id):
        """
        Retrieve the business document by ID.

        Uses all_objects manager to bypass tenant filtering since we
        already have the org context from the workflow instance.

        Args:
            model_class: Django model class
            business_id: Primary key of the business object
            org_id: Organization ID for verification

        Returns:
            Model instance or None
        """
        try:
            return model_class.all_objects.get(
                pk=business_id, is_deleted=False
            )
        except model_class.DoesNotExist:
            return None
        except Exception:
            logger.exception(
                "Error retrieving business object %s pk=%s",
                model_class.__name__,
                business_id,
            )
            return None

    @staticmethod
    def _invoke_lifecycle_hook(business_obj, new_status: str) -> None:
        """
        Call the appropriate lifecycle hook on the business object.

        Args:
            business_obj: Model instance with WorkflowStatusMixin
            new_status: The new approval_status value
        """
        hook_map = {
            'pending_approval': 'on_workflow_submitted',
            'approved': 'on_workflow_approved',
            'rejected': 'on_workflow_rejected',
            'cancelled': 'on_workflow_cancelled',
        }
        hook_name = hook_map.get(new_status)
        if hook_name:
            hook = getattr(business_obj, hook_name, None)
            if callable(hook):
                try:
                    hook()
                except Exception:
                    logger.exception(
                        "Error in lifecycle hook %s on %s #%s",
                        hook_name,
                        business_obj.__class__.__name__,
                        business_obj.pk,
                    )

    @staticmethod
    def _log_state_transition(instance: WorkflowInstance, old_status: str, new_status: str) -> None:
        """
        Log the business document state transition to WorkflowOperationLog.

        Args:
            instance: WorkflowInstance
            old_status: Previous approval status
            new_status: New approval status
        """
        try:
            from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
            WorkflowOperationLog.log_operation(
                operation_type='status_change',
                actor=instance.initiator,
                workflow_instance=instance,
                result='success',
                details={
                    'sync_type': 'business_state',
                    'business_object_code': instance.business_object_code,
                    'business_id': str(instance.business_id),
                    'old_approval_status': old_status,
                    'new_approval_status': new_status,
                },
                organization=instance.organization,
            )
        except Exception:
            logger.exception("Failed to log business state transition")
