"""
Form Permission Service.

Resolves and enforces field-level permissions for workflow approval tasks.
Permissions are stored per-node in WorkflowDefinition.form_permissions
and enforcement happens both on response filtering and submission validation.
"""
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FormPermissionService:
    """
    Resolves and enforces field-level permissions for workflow tasks.

    Permission levels (strictest to loosest):
      - 'hidden'    → field is stripped from API response
      - 'read_only' → field is visible but cannot be modified
      - 'editable'  → field can be modified by the approver

    When no configuration exists for a node, the safe default is
    'read_only' for all fields (approvers should not accidentally
    modify business data).
    """

    PERMISSION_LEVELS = ('hidden', 'read_only', 'editable')
    DEFAULT_PERMISSION = 'read_only'

    # --- Public API ---

    def get_permissions_for_task(self, task) -> Dict[str, str]:
        """
        Resolve field permissions for a specific task.

        Looks up the WorkflowDefinition.form_permissions config for
        the task's node_id. Falls back to DEFAULT_PERMISSION for all
        fields if no config exists.

        Args:
            task: WorkflowTask instance

        Returns:
            Dict mapping field_code → permission level
        """
        try:
            definition = task.instance.definition
            node_permissions = definition.get_form_permissions_for_node(task.node_id)
            if node_permissions:
                return self._normalise_permissions(node_permissions)
        except Exception:
            logger.exception(
                "Error resolving form permissions for task %s", task.pk
            )

        # No configuration → return empty dict (caller should treat
        # absent fields as DEFAULT_PERMISSION)
        return {}

    def validate_submission(
        self, task, submitted_data: dict
    ) -> Tuple[bool, List[str]]:
        """
        Validate that submitted approval data does not modify
        read_only or hidden fields.

        A violation occurs when submitted_data contains a key whose
        permission level is NOT 'editable'.

        Args:
            task: WorkflowTask instance
            submitted_data: Dict of field values submitted by the approver

        Returns:
            Tuple of (is_valid, list_of_violation_messages)
        """
        if not submitted_data:
            return True, []

        permissions = self.get_permissions_for_task(task)
        if not permissions:
            # No permission config → nothing to enforce
            return True, []

        violations: List[str] = []
        for field_code, _value in submitted_data.items():
            perm = permissions.get(field_code, self.DEFAULT_PERMISSION)
            if perm in ('read_only', 'hidden'):
                violations.append(
                    f"Field '{field_code}' is {perm} and cannot be modified."
                )

        return len(violations) == 0, violations

    def filter_response_data(
        self, task, business_data: dict
    ) -> dict:
        """
        Filter business data to remove hidden fields from the response.

        Args:
            task: WorkflowTask instance
            business_data: Full business document data dict

        Returns:
            Filtered dict with hidden fields removed
        """
        if not business_data:
            return business_data

        permissions = self.get_permissions_for_task(task)
        if not permissions:
            return business_data

        return {
            key: value
            for key, value in business_data.items()
            if permissions.get(key, self.DEFAULT_PERMISSION) != 'hidden'
        }

    def get_available_fields(self, business_object_code: str) -> List[Dict]:
        """
        Return the list of available fields for a business object
        (via FieldDefinition metadata), so the designer UI can offer
        a dropdown when configuring per-node form permissions.

        Args:
            business_object_code: Code of the business object

        Returns:
            List of dicts with 'code' and 'name' keys
        """
        try:
            from apps.system.models import FieldDefinition, BusinessObject
            bo = BusinessObject.objects.filter(
                code=business_object_code, is_deleted=False
            ).first()
            if bo is None:
                return []

            fields = FieldDefinition.objects.filter(
                business_object=bo, is_deleted=False
            ).values_list('code', 'name')
            return [{'code': code, 'name': name} for code, name in fields]
        except Exception:
            logger.exception(
                "Error fetching fields for %s", business_object_code
            )
            return []

    # --- Helpers ---

    def _normalise_permissions(self, raw: dict) -> dict:
        """
        Ensure all permission values are valid.

        Unknown values are mapped to DEFAULT_PERMISSION.
        """
        return {
            field: (perm if perm in self.PERMISSION_LEVELS else self.DEFAULT_PERMISSION)
            for field, perm in raw.items()
        }
