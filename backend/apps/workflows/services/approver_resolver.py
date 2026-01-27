"""
Approver Resolver Service

Resolves approvers based on workflow node configuration.
Supports various approver types: specific users, roles, leaders, etc.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.organizations.models import Department

User = get_user_model()

# Role model - placeholder for future implementation
# In current system, roles are stored in UserOrganization.role field
def get_users_by_role(role_name, organization_id):
    """
    Get users by role in organization.

    Args:
        role_name: Role name (admin, member, auditor)
        organization_id: Organization ID

    Returns:
        list: Users with the specified role
    """
    from apps.accounts.models import UserOrganization
    return list(User.objects.filter(
        user_orgs__organization_id=organization_id,
        user_orgs__role=role_name,
        user_orgs__is_active=True,
        is_active=True
    ).distinct())


class ApproverResolver:
    """
    Approver Resolver Service.

    Resolves the actual users who should approve a task based on
    the approver configuration in the workflow node.

    Supports:
    - user: Specific users by ID
    - role: Users with a specific role
    - leader: Department leader
    - dept_leader: Leader of a specific department
    - continuous_leader: Continuous upward leader chain
    - self_select: Allow initiator to select at runtime
    """

    # Approver type constants
    TYPE_USER = 'user'
    TYPE_ROLE = 'role'
    TYPE_LEADER = 'leader'
    TYPE_DEPT_LEADER = 'dept_leader'
    TYPE_CONTINUOUS_LEADER = 'continuous_leader'
    TYPE_SELF_SELECT = 'self_select'
    TYPE_INITIATOR = 'initiator'

    APPROVER_TYPES = [
        TYPE_USER,
        TYPE_ROLE,
        TYPE_LEADER,
        TYPE_DEPT_LEADER,
        TYPE_CONTINUOUS_LEADER,
        TYPE_SELF_SELECT,
        TYPE_INITIATOR,
    ]

    def __init__(self):
        """Initialize the approver resolver."""
        pass

    def resolve(self, approvers_config, instance, graph_data=None):
        """
        Resolve approvers based on configuration.

        Args:
            approvers_config: List of approver configurations from node properties
            instance: The WorkflowInstance context
            graph_data: Optional workflow graph data for additional context

        Returns:
            list: List of User objects who should approve the task

        Raises:
            ValidationError: If approver configuration is invalid
        """
        if not approvers_config:
            return []

        resolved_users = []

        for config in approvers_config:
            if not isinstance(config, dict):
                continue

            approver_type = config.get('type')

            if approver_type == self.TYPE_USER:
                users = self._resolve_user_type(config)
            elif approver_type == self.TYPE_ROLE:
                users = self._resolve_role_type(config, instance)
            elif approver_type == self.TYPE_LEADER:
                users = self._resolve_leader_type(config, instance)
            elif approver_type == self.TYPE_DEPT_LEADER:
                users = self._resolve_dept_leader_type(config, instance)
            elif approver_type == self.TYPE_CONTINUOUS_LEADER:
                users = self._resolve_continuous_leader_type(config, instance)
            elif approver_type == self.TYPE_INITIATOR:
                users = self._resolve_initiator_type(instance)
            elif approver_type == self.TYPE_SELF_SELECT:
                # Cannot resolve at definition time, requires runtime selection
                # Return empty list - will be filled when workflow starts
                users = []
            else:
                continue

            resolved_users.extend(users)

        # Deduplicate while preserving order
        seen = set()
        unique_users = []
        for user in resolved_users:
            if user.id not in seen:
                seen.add(user.id)
                unique_users.append(user)

        return unique_users

    def resolve_from_variables(self, approvers_config, instance, variables):
        """
        Resolve approvers with runtime variable substitution.

        Args:
            approvers_config: List of approver configurations
            instance: The WorkflowInstance context
            variables: Runtime variables containing user selections

        Returns:
            list: List of User objects
        """
        resolved_users = []

        for config in approvers_config:
            if not isinstance(config, dict):
                continue

            approver_type = config.get('type')

            if approver_type == self.TYPE_SELF_SELECT:
                # Get selected user IDs from variables
                select_key = config.get('selectKey', 'selected_approvers')
                selected_ids = variables.get(select_key, [])

                if isinstance(selected_ids, list):
                    users = User.objects.filter(
                        id__in=selected_ids,
                        organization=instance.organization,
                        is_active=True,
                        is_deleted=False
                    )
                    resolved_users.extend(users)
            else:
                # Use standard resolution
                users = self._resolve_single_type(config, instance)
                resolved_users.extend(users)

        # Deduplicate
        seen = set()
        unique_users = []
        for user in resolved_users:
            if user.id not in seen:
                seen.add(user.id)
                unique_users.append(user)

        return unique_users

    def _resolve_single_type(self, config, instance):
        """Resolve a single approver type."""
        approver_type = config.get('type')

        if approver_type == self.TYPE_USER:
            return self._resolve_user_type(config)
        elif approver_type == self.TYPE_ROLE:
            return self._resolve_role_type(config, instance)
        elif approver_type == self.TYPE_LEADER:
            return self._resolve_leader_type(config, instance)
        elif approver_type == self.TYPE_DEPT_LEADER:
            return self._resolve_dept_leader_type(config, instance)
        elif approver_type == self.TYPE_CONTINUOUS_LEADER:
            return self._resolve_continuous_leader_type(config, instance)
        elif approver_type == self.TYPE_INITIATOR:
            return self._resolve_initiator_type(instance)
        else:
            return []

    def _resolve_user_type(self, config):
        """Resolve specific users by ID."""
        user_id = config.get('user_id') or config.get('userId') or config.get('id')

        if not user_id:
            return []

        try:
            user = User.objects.get(
                id=user_id,
                is_active=True,
                is_deleted=False
            )
            return [user]
        except User.DoesNotExist:
            return []

    def _resolve_role_type(self, config, instance):
        """Resolve users with a specific role."""
        # Use role name instead of role_id (since we use UserOrganization.role)
        role_name = config.get('role_name') or config.get('roleName') or config.get('role') or config.get('name')

        if not role_name:
            # If role_id is provided, try to get role name from it
            role_id = config.get('role_id') or config.get('roleId') or config.get('id')
            if not role_id:
                return []
            # For now, return empty if only role_id is provided
            # In future, this could map role_id to role_name
            return []

        # Get users with this role in the organization
        return get_users_by_role(role_name, str(instance.organization_id))

    def _resolve_leader_type(self, config, instance):
        """Resolve the direct leader of the initiator."""
        from apps.organizations.models import UserDepartment

        initiator = instance.initiator

        # Get initiator's primary department
        user_dept = UserDepartment.objects.filter(
            user=initiator,
            organization=instance.organization,
            is_primary=True,
            is_deleted=False
        ).select_related('department').first()

        if not user_dept:
            # Try to get any department if no primary is set
            user_dept = UserDepartment.objects.filter(
                user=initiator,
                organization=instance.organization,
                is_deleted=False
            ).select_related('department').first()

        if not user_dept:
            return []

        department = user_dept.department

        # Get department leader
        if department and department.leader:
            leader = department.leader
            if leader.is_active and not leader.is_deleted:
                return [leader]

        return []

    def _resolve_dept_leader_type(self, config, instance):
        """Resolve the leader of a specific department."""
        dept_id = config.get('dept_id') or config.get('deptId') or config.get('department_id')
        dept_code = config.get('dept_code') or config.get('deptCode') or config.get('department_code')

        if not dept_id and not dept_code:
            return []

        # Get department
        try:
            if dept_id:
                department = Department.objects.get(id=dept_id, is_deleted=False)
            else:
                department = Department.objects.get(
                    code=dept_code,
                    organization=instance.organization,
                    is_deleted=False
                )
        except Department.DoesNotExist:
            return []

        # Get department leader
        if hasattr(department, 'leader') and department.leader:
            leader = department.leader
            if leader.is_active and not leader.is_deleted:
                return [leader]

        return []

    def _resolve_continuous_leader_type(self, config, instance):
        """Resolve continuous upward leader chain."""
        from apps.organizations.models import UserDepartment

        level = config.get('level', 1)  # How many levels up

        initiator = instance.initiator

        # Get initiator's primary department
        user_dept = UserDepartment.objects.filter(
            user=initiator,
            organization=instance.organization,
            is_primary=True,
            is_deleted=False
        ).select_related('department').first()

        if not user_dept:
            # Try to get any department if no primary is set
            user_dept = UserDepartment.objects.filter(
                user=initiator,
                organization=instance.organization,
                is_deleted=False
            ).select_related('department').first()

        if not user_dept or not user_dept.department:
            return []

        current_department = user_dept.department
        leaders = []

        for _ in range(level):
            if not current_department or current_department.is_deleted:
                break

            if current_department.leader:
                leader = current_department.leader
                if leader.is_active:
                    leaders.append(leader)

            # Move to parent department
            if current_department.parent and not current_department.parent.is_deleted:
                current_department = current_department.parent
            else:
                break

        return leaders

    def _resolve_initiator_type(self, instance):
        """Resolve the workflow initiator as approver."""
        initiator = instance.initiator

        if initiator.is_active and not initiator.is_deleted:
            return [initiator]

        return []

    def validate_approvers_config(self, approvers_config):
        """
        Validate approver configuration.

        Args:
            approvers_config: List of approver configurations

        Returns:
            tuple: (is_valid: bool, errors: list)

        Raises:
            ValidationError: If configuration is invalid
        """
        if not approvers_config:
            return True, []

        if not isinstance(approvers_config, list):
            return False, ['Approvers configuration must be a list.']

        errors = []

        for idx, config in enumerate(approvers_config):
            if not isinstance(config, dict):
                errors.append(f'Approvers[{idx}]: Each approver config must be an object.')
                continue

            approver_type = config.get('type')

            if not approver_type:
                errors.append(f'Approvers[{idx}]: Missing type field.')
                continue

            if approver_type not in self.APPROVER_TYPES:
                errors.append(f'Approvers[{idx}]: Invalid type "{approver_type}".')
                continue

            # Type-specific validation
            if approver_type == self.TYPE_USER:
                if not config.get('user_id') and not config.get('userId'):
                    errors.append(f'Approvers[{idx}]: user_id required for user type.')

            elif approver_type == self.TYPE_ROLE:
                if not config.get('role_id') and not config.get('roleId'):
                    errors.append(f'Approvers[{idx}]: role_id required for role type.')

            elif approver_type == self.TYPE_DEPT_LEADER:
                if not config.get('dept_id') and not config.get('dept_code'):
                    errors.append(f'Approvers[{idx}]: dept_id or dept_code required for dept_leader type.')

        return len(errors) == 0, errors
