"""
Mobile Approval Service.

Provides business logic for mobile approval operations,
delegation management, and batch approvals.
"""
from typing import List, Dict, Optional
from django.utils import timezone
from datetime import timedelta
from django.db import models
from apps.mobile.models import ApprovalDelegate


class MobileApprovalService:
    """Mobile approval service."""

    @staticmethod
    def get_pending_approvals(user, limit: int = 20) -> List[Dict]:
        """
        Get pending approval list for user.

        Args:
            user: User object
            limit: Result count limit

        Returns:
            List of pending approval items
        """
        # Check if user has delegation
        delegate = MobileApprovalService.check_delegation(user)
        target_user = delegate if delegate else user

        # Get workflow instances (placeholder - requires workflow module)
        # For now, return empty list
        return []

    @staticmethod
    def _is_urgent(instance) -> bool:
        """
        Check if approval is urgent.

        Args:
            instance: WorkflowInstance

        Returns:
            True if urgent
        """
        if instance.created_at < timezone.now() - timedelta(days=2):
            return True
        return False

    @staticmethod
    def approve(user, instance_id: str, action: str, comment: str = '') -> Dict:
        """
        Execute approval action.

        Args:
            user: User object
            instance_id: Workflow instance ID
            action: Action type (approve/reject/transfer)
            comment: Approval comment

        Returns:
            Operation result
        """
        # Placeholder - requires workflow module integration
        return {'success': True, 'message': 'Approval processed'}

    @staticmethod
    def batch_approve(user, instance_ids: List[str], action: str, comment: str = '') -> Dict:
        """
        Batch approve multiple items.

        Args:
            user: User object
            instance_ids: List of workflow instance IDs
            action: Action type
            comment: Approval comment

        Returns:
            Batch operation result
        """
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for instance_id in instance_ids:
            result = MobileApprovalService.approve(user, instance_id, action, comment)
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'instance_id': instance_id,
                    'error': result.get('error', 'Unknown error')
                })

        return results

    @staticmethod
    def delegate_approval(user, delegate_user_id: str, config: Dict) -> ApprovalDelegate:
        """
        Set up approval delegation.

        Args:
            user: Delegator (user giving approval)
            delegate_user_id: Delegate user ID
            config: Delegation configuration

        Returns:
            ApprovalDelegate instance
        """
        from apps.accounts.models import User

        try:
            delegate = User.objects.get(id=delegate_user_id)
        except User.DoesNotExist:
            raise ValueError('Delegate user not found')

        # Deactivate existing delegations
        ApprovalDelegate.objects.filter(
            delegator=user,
            is_active=True
        ).update(is_active=False, is_revoked=True)

        return ApprovalDelegate.objects.create(
            delegator=user,
            delegate=delegate,
            delegate_type=config.get('delegate_type', 'temporary'),
            delegate_scope=config.get('delegate_scope', 'all'),
            start_time=config.get('start_time'),
            end_time=config.get('end_time'),
            scope_config=config.get('scope_config', {}),
            reason=config.get('reason', ''),
        )

    @staticmethod
    def revoke_delegation(user, delegation_id: str) -> bool:
        """
        Revoke an active delegation.

        Args:
            user: User object
            delegation_id: Delegation ID

        Returns:
            True if successful
        """
        import uuid
        # Try to parse as UUID to check if it's a valid ID
        try:
            uuid.UUID(delegation_id)
            # Valid UUID format, proceed with query
            pass
        except (ValueError, AttributeError):
            # Not a UUID format
            return False

        try:
            delegation = ApprovalDelegate.objects.get(
                id=delegation_id,
                delegator=user,
                is_active=True
            )
            delegation.is_active = False
            delegation.is_revoked = True
            delegation.revoked_at = timezone.now()
            delegation.revoked_by = user
            delegation.save()
            return True
        except ApprovalDelegate.DoesNotExist:
            return False

    @staticmethod
    def check_delegation(user, workflow_id: str = None) -> Optional['User']:
        """
        Check if user has active delegation.

        Args:
            user: Original approver
            workflow_id: Workflow ID (optional)

        Returns:
            Delegate user or None
        """
        now = timezone.now()
        delegates = ApprovalDelegate.objects.filter(
            delegator=user,
            is_active=True,
            is_revoked=False,
            start_time__lte=now
        ).filter(
            models.Q(end_time__isnull=True) | models.Q(end_time__gte=now)
        )

        for delegate in delegates:
            if delegate.delegate_scope == 'all':
                return delegate.delegate
            elif delegate.delegate_scope == 'specific':
                if workflow_id in delegate.scope_config.get('workflow_ids', []):
                    return delegate.delegate
            elif delegate.delegate_scope == 'category':
                # Category matching logic
                pass

        return None

    @staticmethod
    def get_user_delegations(user):
        """
        Get all delegations for user.

        Args:
            user: User object

        Returns:
            QuerySet of ApprovalDelegate
        """
        return ApprovalDelegate.objects.filter(
            delegator=user
        ).select_related('delegate').order_by('-created_at')

    @staticmethod
    def execute_approval(user, approval_id: str, action: str, comment: str = '') -> Dict:
        """
        Execute an approval action.

        Args:
            user: User object
            approval_id: Approval record ID
            action: Action type (approve, reject, etc.)
            comment: Optional comment

        Returns:
            Result dict with success status
        """
        # This is a simplified mock implementation
        # In production, this would integrate with the workflow module
        return {
            'success': True,
            'message': f'Approval {action} executed successfully',
            'approval_id': approval_id
        }

    @staticmethod
    def get_received_delegations(user):
        """
        Get delegations received by user.

        Args:
            user: User object

        Returns:
            QuerySet of ApprovalDelegate
        """
        return ApprovalDelegate.objects.filter(
            delegate=user
        ).select_related('delegator').order_by('-created_at')
