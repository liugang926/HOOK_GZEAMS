"""
ViewSets for Mobile Approval and Approval Delegate models.
"""
from django.db import models
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.mobile.models import ApprovalDelegate
from apps.mobile.serializers import (
    ApprovalDelegateSerializer,
    ApprovalDelegateDetailSerializer,
)
from apps.mobile.services import MobileApprovalService
from apps.mobile.filters import ApprovalDelegateFilter


class MobileApprovalViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Mobile Approval operations.

    Handles mobile approval functionality including:
    - Pending approval retrieval
    - Approval execution
    - Batch approval operations
    - Delegation management

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get filtered queryset for current user."""
        # Get current user's devices
        return ApprovalDelegate.objects.filter(
            delegator=self.request.user
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ApprovalDelegateDetailSerializer
        return ApprovalDelegateSerializer

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get pending approvals for current user.

        Checks for active delegations first, then returns pending approvals.

        GET /api/mobile/approvals/pending/
        Query Params:
            - limit: Maximum number of approvals to return (default: 20)
        """
        limit = int(request.query_params.get('limit', 20))
        approvals = MobileApprovalService.get_pending_approvals(
            request.user,
            limit=limit
        )
        return Response({
            'count': len(approvals),
            'results': approvals
        })

    @action(detail=False, methods=['post'])
    def approve(self, request):
        """
        Execute a single approval.

        POST /api/mobile/approvals/approve/
        {
            "approval_id": "approval_uuid",
            "action": "approve",
            "comment": "Approved via mobile"
        }
        """
        approval_id = request.data.get('approval_id')
        action_type = request.data.get('action', 'approve')
        comment = request.data.get('comment', '')

        if not approval_id:
            return Response(
                {'error': 'Approval ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = MobileApprovalService.execute_approval(
            user=request.user,
            approval_id=approval_id,
            action=action_type,
            comment=comment
        )

        if result.get('success'):
            return Response(result)
        return Response(
            result,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'])
    def batch_approve(self, request):
        """
        Batch approve multiple items.

        POST /api/mobile/approvals/batch_approve/
        {
            "approvals": [
                {"approval_id": "uuid1", "action": "approve"},
                {"approval_id": "uuid2", "action": "reject", "comment": "Issues found"}
            ],
            "comment": "Batch approved"
        }
        """
        approvals_data = request.data.get('approvals', [])
        global_comment = request.data.get('comment', '')

        if not approvals_data:
            return Response(
                {'error': 'No approvals provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = []
        succeeded = 0
        failed = 0

        for item in approvals_data:
            approval_id = item.get('approval_id')
            action_type = item.get('action', 'approve')
            comment = item.get('comment', global_comment)

            result = MobileApprovalService.execute_approval(
                user=request.user,
                approval_id=approval_id,
                action=action_type,
                comment=comment
            )

            if result.get('success'):
                succeeded += 1
                results.append({
                    'approval_id': approval_id,
                    'success': True
                })
            else:
                failed += 1
                results.append({
                    'approval_id': approval_id,
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                })

        return Response({
            'message': f'Batch approval completed: {succeeded} succeeded, {failed} failed',
            'summary': {
                'total': len(approvals_data),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })

    @action(detail=False, methods=['post'])
    def delegate(self, request):
        """
        Set up approval delegation.

        POST /api/mobile/approvals/delegate/
        {
            "delegate_user_id": "delegate_uuid",
            "delegate_type": "temporary",
            "delegate_scope": "all",
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-31T23:59:59Z"
        }
        """
        delegate_user_id = request.data.get('delegate_user_id')
        delegate_type = request.data.get('delegate_type', 'temporary')
        delegate_scope = request.data.get('delegate_scope', 'all')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')

        if not delegate_user_id:
            return Response(
                {'error': 'Delegate user ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.accounts.models import User

        try:
            delegate = User.objects.get(id=delegate_user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Delegate user not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        config = {
            'delegate_type': delegate_type,
            'delegate_scope': delegate_scope,
            'start_time': start_time,
            'end_time': end_time
        }

        delegation = MobileApprovalService.delegate_approval(
            user=request.user,
            delegate_user_id=delegate_user_id,
            config=config
        )

        serializer = ApprovalDelegateSerializer(delegation)
        return Response({
            'message': 'Delegation created successfully',
            'delegation': serializer.data
        })

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """
        Revoke an active delegation.

        POST /api/mobile/approvals/{id}/revoke/
        {
            "reason": "No longer needed"
        }
        """
        reason = request.data.get('reason', '')

        success = MobileApprovalService.revoke_delegation(
            user=request.user,
            delegation_id=pk
        )

        if success:
            # Update with reason if provided
            delegation = ApprovalDelegate.objects.get(pk=pk)
            if reason:
                delegation.revoked_reason = reason
                delegation.save()

            return Response({'message': 'Delegation revoked successfully'})
        return Response(
            {'error': 'Delegation revocation failed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def my_delegations(self, request):
        """
        Get current user's active delegations (both given and received).

        GET /api/mobile/approvals/my_delegations/
        """
        from apps.mobile.models import ApprovalDelegate

        # Delegations given by user
        given = ApprovalDelegate.objects.filter(
            delegator=request.user,
            is_active=True
        )

        # Delegations received by user
        received = ApprovalDelegate.objects.filter(
            delegate=request.user,
            is_active=True
        )

        given_serializer = ApprovalDelegateSerializer(given, many=True)
        received_serializer = ApprovalDelegateSerializer(received, many=True)

        return Response({
            'given': given_serializer.data,
            'received': received_serializer.data
        })


class ApprovalDelegateViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for ApprovalDelegate management.

    Inherits from BaseModelViewSetWithBatch to get:
    - Organization filtering
    - Soft delete support
    - Batch operations
    - Audit field auto-population
    """

    permission_classes = [IsAuthenticated]
    filterset_class = ApprovalDelegateFilter

    def get_queryset(self):
        """Get filtered queryset for current user."""
        # User can see their own delegations (given or received)
        from django.db.models import Q

        return ApprovalDelegate.objects.filter(
            Q(delegator=self.request.user) |
            Q(delegate=self.request.user)
        )

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ApprovalDelegateDetailSerializer
        return ApprovalDelegateSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get currently active delegations.

        GET /api/mobile/delegates/active/
        """
        from django.utils import timezone

        now = timezone.now()
        delegations = self.get_queryset().filter(
            is_active=True,
            is_revoked=False,
            start_time__lte=now
        ).filter(
            models.Q(end_time__isnull=True) |
            models.Q(end_time__gte=now)
        )

        serializer = self.get_serializer(delegations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a delegation.

        POST /api/mobile/delegates/{id}/activate/
        """
        try:
            delegation = ApprovalDelegate.objects.get(pk=pk)
        except ApprovalDelegate.DoesNotExist:
            return Response(
                {'error': 'Delegation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        if delegation.delegator != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        delegation.is_active = True
        delegation.is_revoked = False
        delegation.save()

        return Response({'message': 'Delegation activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a delegation (without revoking).

        POST /api/mobile/delegates/{id}/deactivate/
        """
        try:
            delegation = ApprovalDelegate.objects.get(pk=pk)
        except ApprovalDelegate.DoesNotExist:
            return Response(
                {'error': 'Delegation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check permission
        if delegation.delegator != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        delegation.is_active = False
        delegation.save()

        return Response({'message': 'Delegation deactivated'})
