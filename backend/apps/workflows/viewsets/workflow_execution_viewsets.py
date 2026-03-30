"""
ViewSets for workflow instance execution.

Provides ViewSets for WorkflowInstance, WorkflowTask management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, FloatField
from django.utils import timezone
from django.db.models.functions import TruncDay
from django.db import models

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.workflows.models import (
    WorkflowInstance, WorkflowTask, WorkflowDefinition, WorkflowApproval
)
from apps.workflows.serializers import (
    WorkflowInstanceListSerializer,
    WorkflowInstanceDetailSerializer,
    WorkflowInstanceStartSerializer,
    WorkflowTaskListSerializer,
    WorkflowTaskDetailSerializer,
    WorkflowTaskActionSerializer,
    WorkflowTaskDelegateSerializer,
    WorkflowTaskReassignSerializer,
    WorkflowApprovalSerializer,
    MyTasksSerializer,
    WorkflowStatisticsSerializer,
)
from apps.workflows.filters.workflow_execution_filters import WorkflowTaskFilter
from apps.workflows.services import WorkflowEngine


# === WorkflowInstance ViewSet ===

class WorkflowInstanceViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for WorkflowInstance management.

    Provides:
    - Standard CRUD operations
    - Start workflow action
    - Withdraw/terminate actions
    - Statistics and reports
    """

    queryset = WorkflowInstance.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowInstanceListSerializer
        if self.action == 'retrieve':
            return WorkflowInstanceDetailSerializer
        if self.action == 'start':
            return WorkflowInstanceStartSerializer
        return WorkflowInstanceListSerializer

    def get_queryset(self):
        """Filter queryset based on user."""
        qs = super().get_queryset()
        user = self.request.user

        # For list/my_instances actions, non-admin users only see their own instances
        # For detail/actions, we allow access to check permissions in the action
        if self.action in ['list', 'my_instances']:
            if not user.is_superuser and not user.is_staff:
                qs = qs.filter(initiator=user)

        return qs.select_related('definition', 'initiator', 'organization')

    @action(detail=False, methods=['post'])
    def start(self, request):
        """
        Start a new workflow instance.

        POST /api/workflows/instances/start/
        {
            "definition_id": "uuid",
            "business_object_code": "asset_pickup",
            "business_id": "123",
            "business_no": "LY-2024-001",
            "variables": {"amount": 10000},
            "title": "Optional title",
            "priority": "normal"
        }
        """
        serializer = WorkflowInstanceStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        definition = data['definition_id']

        # Start the workflow
        engine = WorkflowEngine(definition)
        success, instance, error = engine.start_workflow(
            definition=definition,
            business_object_code=data['business_object_code'],
            business_id=data['business_id'],
            business_no=data.get('business_no'),
            initiator=request.user,
            variables=data.get('variables'),
            title=data.get('title'),
            priority=data.get('priority', 'normal')
        )

        if success:
            result_serializer = WorkflowInstanceDetailSerializer(instance)
            return BaseResponse.success(
                data=result_serializer.data,
                message=_('Workflow started successfully.')
            )
        else:
            return BaseResponse.error(
                code='WORKFLOW_START_FAILED',
                message=error or _('Failed to start workflow.')
            )

    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """
        Withdraw a workflow instance.

        POST /api/workflows/instances/{id}/withdraw/
        """
        instance = self.get_object()

        engine = WorkflowEngine()
        success, error = engine.withdraw_instance(instance, request.user)

        if success:
            return BaseResponse.success(
                message=_('Workflow withdrawn successfully.')
            )
        else:
            return BaseResponse.error(
                code='WITHDRAW_FAILED',
                message=error or _('Failed to withdraw workflow.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk=None):
        """
        Terminate a workflow instance (admin only).

        POST /api/workflows/instances/{id}/terminate/
        {
            "reason": "Optional reason"
        }
        """
        instance = self.get_object()

        # Check admin permission
        if not request.user.is_superuser and not request.user.is_staff:
            return BaseResponse.error(
                code='PERMISSION_DENIED',
                message=_('Only administrators can terminate workflows.')
            , http_status=status.HTTP_403_FORBIDDEN)

        reason = request.data.get('reason')

        engine = WorkflowEngine()
        success, error = engine.terminate_instance(instance, request.user, reason)

        if success:
            return BaseResponse.success(
                message=_('Workflow terminated successfully.')
            )
        else:
            return BaseResponse.error(
                code='TERMINATE_FAILED',
                message=error or _('Failed to terminate workflow.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_instances(self, request):
        """
        Get current user's workflow instances.

        GET /api/workflows/instances/my_instances/
        """
        instances = self.get_queryset().filter(initiator=request.user)

        # Apply status filter
        status_filter = request.query_params.get('status')
        if status_filter:
            instances = instances.filter(status=status_filter)

        # Use BaseResponse format with pagination
        page = self.paginate_queryset(instances)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Return BaseResponse format with pagination info
            return Response(data=BaseResponse.success(data={
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }).data)

        serializer = self.get_serializer(instances, many=True)
        return BaseResponse.success(data=serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """
        Get workflow instance timeline with approvals.

        GET /api/workflows/instances/{id}/timeline/
        """
        instance = self.get_object()

        # Get all approvals for this instance
        approvals = WorkflowApproval.objects.filter(
            task__instance=instance
        ).select_related('approver', 'task').order_by('created_at')

        approval_data = []
        for approval in approvals:
            approval_data.append({
                'id': str(approval.id),
                'task_name': approval.task.node_name,
                'approver_name': approval.approver.get_full_name() or approval.approver.username,
                'action': approval.action,
                'action_display': approval.get_action_display(),
                'comment': approval.comment,
                'created_at': approval.created_at,
            })

        return BaseResponse.success(data=approval_data)

    @action(detail=False, methods=['get'], url_path='by-business')
    def by_business(self, request):
        """
        Look up the workflow instance for a given business document.

        GET /api/workflows/instances/by-business/?business_object_code=AssetPickup&business_id=<uuid>

        Returns the most recent workflow instance (if any) for the given business document.
        """
        business_object_code = request.query_params.get('business_object_code')
        business_id = request.query_params.get('business_id')

        if not business_object_code or not business_id:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=_('Both business_object_code and business_id are required.'),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        instance = WorkflowInstance.objects.filter(
            is_deleted=False,
            business_object_code=business_object_code,
            business_id=business_id,
        ).order_by('-created_at').first()

        if instance is None:
            return BaseResponse.success(data=None, message=_('No workflow instance found.'))

        serializer = WorkflowInstanceDetailSerializer(instance)
        return BaseResponse.success(data=serializer.data)


# === WorkflowTask ViewSet ===

class WorkflowTaskViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for WorkflowTask management.

    Provides:
    - List my tasks (pending, completed, overdue)
    - Task actions (approve, reject, return) with field-permission validation
    - Task delegation
    - Retrieve with resolved form_permissions per node
    """

    queryset = WorkflowTask.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    filterset_class = WorkflowTaskFilter

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from apps.workflows.services.form_permission_service import FormPermissionService
        self._perm_service = FormPermissionService()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return WorkflowTaskListSerializer
        if self.action == 'retrieve':
            return WorkflowTaskDetailSerializer
        if self.action in ['approve', 'reject', 'return', 'bulk_approve', 'bulk_reject']:
            return WorkflowTaskActionSerializer
        if self.action == 'delegate':
            return WorkflowTaskDelegateSerializer
        if self.action == 'reassign':
            return WorkflowTaskReassignSerializer
        return WorkflowTaskListSerializer

    def get_queryset(self):
        """Filter queryset based on user."""
        qs = super().get_queryset()
        user = self.request.user

        # For list action, non-admin users only see their assigned tasks
        # For detail/actions, we allow access to check permissions in the action
        if self.action == 'list':
            if not user.is_superuser and not user.is_staff:
                qs = qs.filter(assignee=user)

        return qs.select_related('instance', 'instance__definition', 'assignee')

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single task with resolved field permissions.

        GET /api/workflows/tasks/{id}/

        Response includes:
        - Standard task detail fields
        - form_permissions: resolved field permissions for this task's node
        - business_data: business document data with hidden fields filtered out
        """
        task = self.get_object()
        serializer = self.get_serializer(task)
        data = serializer.data

        # Resolve and attach form permissions
        form_permissions = self._perm_service.get_permissions_for_task(task)
        data['form_permissions'] = form_permissions

        # Attach filtered business data (strip hidden fields)
        business_data = task.instance.variables or {}
        data['business_data'] = self._perm_service.filter_response_data(
            task, business_data
        )

        return BaseResponse.success(data=data)

    def list(self, request, *args, **kwargs):
        """
        List tasks with optional status filter.

        GET /api/workflows/tasks/?status=pending
        """
        qs = self.filter_queryset(self.get_queryset())

        # Filter by status
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        # Filter overdue
        overdue_only = request.query_params.get('overdue_only')
        if overdue_only and overdue_only.lower() in ('true', '1', 'yes'):
            qs = qs.filter(
                status='pending',
                due_date__lt=timezone.now()
            )

        # Use BaseResponse format with pagination
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            # Return BaseResponse format with pagination info
            return Response(data=BaseResponse.success(data={
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }).data)

        serializer = self.get_serializer(qs, many=True)
        return BaseResponse.success(data=serializer.data)

    def _format_paginated_response(self, results):
        """Format paginated results to BaseResponse format."""
        return {
            'count': self.paginator.page.paginator.count,
            'next': self.paginator.get_next_link(),
            'previous': self.paginator.get_previous_link(),
            'results': results
        }

    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """
        Get current user's tasks grouped by status.

        GET /api/workflows/tasks/my_tasks/
        """
        user = request.user
        today = timezone.now().date()

        # Get base queryset
        qs = WorkflowTask.objects.filter(is_deleted=False, assignee=user)

        # Get pending tasks
        pending = qs.filter(
            status='pending'
        ).select_related('instance', 'instance__definition')

        # Get overdue tasks
        overdue = pending.filter(due_date__lt=timezone.now())

        # Get completed today
        completed_today = qs.filter(
            status__in=['approved', 'rejected'],
            completed_at__date=today
        ).select_related('instance', 'instance__definition')

        # Summary counts
        summary = {
            'pending_count': pending.count(),
            'overdue_count': overdue.count(),
            'completed_today_count': completed_today.count(),
        }

        serializer = WorkflowTaskListSerializer

        data = {
            'pending': serializer(pending, many=True).data,
            'overdue': serializer(overdue, many=True).data,
            'completed_today': serializer(completed_today, many=True).data,
            'summary': summary
        }

        return BaseResponse.success(data=data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a task.

        POST /api/workflows/tasks/{id}/approve/
        {
            "comment": "Approved",
            "data": {"field1": "value"}  // optional business data updates
        }
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.validated_data.get('comment')

        # Validate field-level permissions on submitted data
        submitted_data = request.data.get('data', {})
        if submitted_data:
            is_valid, violations = self._perm_service.validate_submission(
                task, submitted_data
            )
            if not is_valid:
                return BaseResponse.error(
                    code='PERMISSION_DENIED',
                    message=_('Field permission violation.'),
                    http_status=status.HTTP_403_FORBIDDEN,
                    details=violations,
                )

        engine = WorkflowEngine()
        success, instance, error = engine.execute_task(
            task=task,
            action='approve',
            actor=request.user,
            comment=comment
        )

        if success:
            # Refresh task and get updated instance
            task.refresh_from_db()
            instance_data = WorkflowInstanceDetailSerializer(instance).data

            return BaseResponse.success(
                data={
                    'task': WorkflowTaskDetailSerializer(task).data,
                    'instance': instance_data
                },
                message=_('Task approved successfully.')
            )
        else:
            return BaseResponse.error(
                code='APPROVE_FAILED',
                message=error or _('Failed to approve task.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a task.

        POST /api/workflows/tasks/{id}/reject/
        {
            "comment": "Rejected",
            "data": {}  // optional
        }
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.validated_data.get('comment')

        # Validate field-level permissions on submitted data
        submitted_data = request.data.get('data', {})
        if submitted_data:
            is_valid, violations = self._perm_service.validate_submission(
                task, submitted_data
            )
            if not is_valid:
                return BaseResponse.error(
                    code='PERMISSION_DENIED',
                    message=_('Field permission violation.'),
                    http_status=status.HTTP_403_FORBIDDEN,
                    details=violations,
                )

        engine = WorkflowEngine()
        success, instance, error = engine.execute_task(
            task=task,
            action='reject',
            actor=request.user,
            comment=comment
        )

        if success:
            task.refresh_from_db()
            instance_data = WorkflowInstanceDetailSerializer(instance).data

            return BaseResponse.success(
                data={
                    'task': WorkflowTaskDetailSerializer(task).data,
                    'instance': instance_data
                },
                message=_('Task rejected successfully.')
            )
        else:
            return BaseResponse.error(
                code='REJECT_FAILED',
                message=error or _('Failed to reject task.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk_approve')
    def bulk_approve(self, request):
        """Approve multiple tasks for the current actor."""
        return self._bulk_transition(request, action='approve')

    @action(detail=False, methods=['post'], url_path='bulk_reject')
    def bulk_reject(self, request):
        """Reject multiple tasks for the current actor."""
        return self._bulk_transition(request, action='reject')

    def _bulk_transition(self, request, action: str):
        """Apply a task transition to multiple tasks and return per-item results."""
        task_ids = request.data.get('task_ids') or request.data.get('ids') or []
        comment = request.data.get('comment') or request.data.get('reason')

        if not isinstance(task_ids, list) or not task_ids:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=_('task_ids must be a non-empty list.'),
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset().filter(id__in=task_ids)
        if not request.user.is_superuser and not request.user.is_staff:
            queryset = queryset.filter(assignee=request.user)

        tasks_by_id = {str(task.id): task for task in queryset}
        results = []
        succeeded = 0
        engine = WorkflowEngine()

        for task_id in task_ids:
            task = tasks_by_id.get(str(task_id))
            if task is None:
                results.append({
                    'id': str(task_id),
                    'success': False,
                    'error': 'Task not found or inaccessible.',
                })
                continue

            success, instance, error = engine.execute_task(
                task=task,
                action=action,
                actor=request.user,
                comment=comment,
            )
            if success:
                succeeded += 1
                results.append({'id': str(task_id), 'success': True})
            else:
                results.append({
                    'id': str(task_id),
                    'success': False,
                    'error': error or f'{action} failed.',
                })

        return BaseResponse.success(
            data={
                'summary': {
                    'total': len(task_ids),
                    'succeeded': succeeded,
                    'failed': len(task_ids) - succeeded,
                },
                'results': results,
            }
        )

    @action(detail=True, methods=['post'])
    def return_task(self, request, pk=None):
        """
        Return a task to previous step.

        POST /api/workflows/tasks/{id}/return_task/
        {
            "comment": "Needs revision",
            "data": {}  // optional
        }
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.validated_data.get('comment')

        # Validate field-level permissions on submitted data
        submitted_data = request.data.get('data', {})
        if submitted_data:
            is_valid, violations = self._perm_service.validate_submission(
                task, submitted_data
            )
            if not is_valid:
                return BaseResponse.error(
                    code='PERMISSION_DENIED',
                    message=_('Field permission violation.'),
                    http_status=status.HTTP_403_FORBIDDEN,
                    details=violations,
                )

        engine = WorkflowEngine()
        success, instance, error = engine.execute_task(
            task=task,
            action='return',
            actor=request.user,
            comment=comment
        )

        if success:
            task.refresh_from_db()
            instance_data = WorkflowInstanceDetailSerializer(instance).data

            return BaseResponse.success(
                data={
                    'task': WorkflowTaskDetailSerializer(task).data,
                    'instance': instance_data
                },
                message=_('Task returned successfully.')
            )
        else:
            return BaseResponse.error(
                code='RETURN_FAILED',
                message=error or _('Failed to return task.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        """
        Delegate a task to another user.

        POST /api/workflows/tasks/{id}/delegate/
        {
            "to_user_id": "uuid",
            "reason": "Out of office"
        }
        """
        task = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import User

        to_user_id = serializer.validated_data.get('to_user_id')
        reason = serializer.validated_data.get('reason')

        try:
            to_user = User.objects.get(id=to_user_id, is_active=True, is_deleted=False)
        except User.DoesNotExist:
            return BaseResponse.error(
                code='USER_NOT_FOUND',
                message=_('Target user not found.')
            , http_status=status.HTTP_404_NOT_FOUND)

        engine = WorkflowEngine()
        success, error = engine.reassign_task(task, to_user, request.user, reason)

        if success:
            task.refresh_from_db()
            return BaseResponse.success(
                data=WorkflowTaskDetailSerializer(task).data,
                message=_('Task delegated successfully.')
            )
        else:
            return BaseResponse.error(
                code='DELEGATE_FAILED',
                message=error or _('Failed to delegate task.')
            , http_status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reassign(self, request, pk=None):
        """
        Reassign a task to a different user (admin action).

        POST /api/workflows/tasks/{id}/reassign/
        {
            "assignee_id": "uuid",
            "reason": "Reassignment reason"
        }
        """
        task = self.get_object()

        # Check admin permission
        if not request.user.is_superuser and not request.user.is_staff:
            return BaseResponse.error(
                code='PERMISSION_DENIED',
                message=_('Only administrators can reassign tasks.')
            , http_status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import User

        assignee_id = serializer.validated_data.get('assignee_id')
        reason = serializer.validated_data.get('reason')

        try:
            assignee = User.objects.get(id=assignee_id, is_active=True, is_deleted=False)
        except User.DoesNotExist:
            return BaseResponse.error(
                code='USER_NOT_FOUND',
                message=_('Assignee user not found.')
            , http_status=status.HTTP_404_NOT_FOUND)

        engine = WorkflowEngine()
        success, error = engine.reassign_task(task, assignee, request.user, reason)

        if success:
            task.refresh_from_db()
            return BaseResponse.success(
                data=WorkflowTaskDetailSerializer(task).data,
                message=_('Task reassigned successfully.')
            )
        else:
            return BaseResponse.error(
                code='REASSIGN_FAILED',
                message=error or _('Failed to reassign task.')
            , http_status=status.HTTP_400_BAD_REQUEST)


# === WorkflowApproval ViewSet ===

class WorkflowApprovalViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for WorkflowApproval records.

    Provides read access for approval history with basic filtering.
    """

    queryset = WorkflowApproval.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    serializer_class = WorkflowApprovalSerializer
    filterset_fields = ['action', 'task', 'approver']
    search_fields = ['comment']

    def get_queryset(self):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset().select_related('task', 'task__instance', 'approver')
        user = self.request.user
        if not user.is_superuser and not user.is_staff:
            qs = qs.filter(task__assignee=user)
        return qs


# === Statistics ViewSet ===

class WorkflowStatisticsViewSet(viewsets.ViewSet):
    """
    ViewSet for workflow statistics.

    Provides:
    - Overall workflow statistics
    - User task statistics
    - Performance metrics
    """

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        Get workflow statistics.

        GET /api/workflows/statistics/
        """
        user = request.user

        # Total instances count
        total_instances = WorkflowInstance.objects.filter(
            is_deleted=False
        ).count()

        # Pending instances
        pending_instances = WorkflowInstance.objects.filter(
            is_deleted=False,
            status__in=[WorkflowInstance.STATUS_RUNNING, WorkflowInstance.STATUS_PENDING_APPROVAL]
        ).count()

        # Completed instances
        completed_instances = WorkflowInstance.objects.filter(
            is_deleted=False,
            status=WorkflowInstance.STATUS_APPROVED
        ).count()

        # User's pending tasks
        my_pending_tasks = WorkflowTask.objects.filter(
            is_deleted=False,
            assignee=user,
            status='pending'
        ).count()

        # User's completed tasks
        my_completed_tasks = WorkflowTask.objects.filter(
            is_deleted=False,
            assignee=user,
            status__in=['approved', 'rejected']
        ).count()

        # User's overdue tasks
        my_overdue_tasks = WorkflowTask.objects.filter(
            is_deleted=False,
            assignee=user,
            status='pending',
            due_date__lt=timezone.now()
        ).count()

        # Average completion time (calculated from instances)
        completed_instances_qs = WorkflowInstance.objects.filter(
            is_deleted=False,
            status=WorkflowInstance.STATUS_APPROVED,
            completed_at__isnull=False,
            started_at__isnull=False
        )

        avg_duration = 0
        if completed_instances_qs.exists():
            total_seconds = 0
            count = 0
            for inst in completed_instances_qs:
                if inst.completed_at and inst.started_at:
                    delta = inst.completed_at - inst.started_at
                    total_seconds += delta.total_seconds()
                    count += 1
            if count > 0:
                avg_duration = total_seconds / count / 3600  # Convert to hours

        # Instances by status
        instances_by_status = dict(
            WorkflowInstance.objects.filter(is_deleted=False).values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )

        # Instances by definition
        instances_by_definition = dict(
            WorkflowInstance.objects.filter(is_deleted=False).values(
                'definition__name'
            ).annotate(
                count=Count('id')
            ).values_list('definition__name', 'count')
        )

        data = {
            'total_instances': total_instances,
            'pending_instances': pending_instances,
            'completed_instances': completed_instances,
            'rejected_instances': WorkflowInstance.objects.filter(
                is_deleted=False,
                status=WorkflowInstance.STATUS_REJECTED
            ).count(),
            'my_pending_tasks': my_pending_tasks,
            'my_completed_tasks': my_completed_tasks,
            'my_overdue_tasks': my_overdue_tasks,
            'average_completion_hours': round(avg_duration or 0, 2),
            'approval_rate': round(
                (completed_instances / total_instances * 100) if total_instances > 0 else 0, 1
            ),
            'overdue_rate': round(
                (my_overdue_tasks / my_pending_tasks * 100) if my_pending_tasks > 0 else 0, 1
            ),
            'instances_by_status': instances_by_status,
            'instances_by_definition': instances_by_definition,
        }

        return BaseResponse.success(data=data)

    @action(detail=False, methods=['get'])
    def trends(self, request):
        """
        Get daily instance trends for the specified period.

        GET /api/workflows/statistics/trends/?period=7d
        Supported periods: 7d, 14d, 30d
        """
        period_param = request.query_params.get('period', '7d')
        period_map = {'7d': 7, '14d': 14, '30d': 30}
        days = period_map.get(period_param, 7)

        start_date = timezone.now() - timezone.timedelta(days=days)

        # Group instances by date and status
        started_by_day = dict(
            WorkflowInstance.objects.filter(
                is_deleted=False,
                created_at__gte=start_date,
            ).annotate(
                day=TruncDay('created_at')
            ).values('day').annotate(
                count=Count('id')
            ).values_list('day', 'count')
        )

        completed_by_day = dict(
            WorkflowInstance.objects.filter(
                is_deleted=False,
                status=WorkflowInstance.STATUS_APPROVED,
                completed_at__gte=start_date,
            ).annotate(
                day=TruncDay('completed_at')
            ).values('day').annotate(
                count=Count('id')
            ).values_list('day', 'count')
        )

        rejected_by_day = dict(
            WorkflowInstance.objects.filter(
                is_deleted=False,
                status=WorkflowInstance.STATUS_REJECTED,
                completed_at__gte=start_date,
            ).annotate(
                day=TruncDay('completed_at')
            ).values('day').annotate(
                count=Count('id')
            ).values_list('day', 'count')
        )

        # Build daily data points
        trend_data = []
        for i in range(days):
            day = (start_date + timezone.timedelta(days=i + 1)).date()
            trend_data.append({
                'date': day.isoformat(),
                'started': started_by_day.get(
                    timezone.datetime.combine(day, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone()), 0
                ),
                'completed': completed_by_day.get(
                    timezone.datetime.combine(day, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone()), 0
                ),
                'rejected': rejected_by_day.get(
                    timezone.datetime.combine(day, timezone.datetime.min.time(), tzinfo=timezone.get_current_timezone()), 0
                ),
            })

        return BaseResponse.success(data={
            'period': period_param,
            'data': trend_data,
        })

    @action(detail=False, methods=['get'])
    def bottlenecks(self, request):
        """
        Get slowest approval nodes by average duration.

        GET /api/workflows/statistics/bottlenecks/
        Returns nodes sorted by average completion time (descending).
        """
        # Calculate duration per completed task
        completed_tasks = WorkflowTask.objects.filter(
            is_deleted=False,
            status__in=['approved', 'rejected'],
            completed_at__isnull=False,
            created_at__isnull=False,
        ).values(
            'node_name',
            definition_name=F('instance__definition__name'),
        ).annotate(
            task_count=Count('id'),
            avg_duration_seconds=Avg(
                ExpressionWrapper(
                    F('completed_at') - F('created_at'),
                    output_field=models.DurationField(),
                )
            ),
        ).order_by('-avg_duration_seconds')[:10]

        bottleneck_list = []
        for item in completed_tasks:
            avg_secs = item['avg_duration_seconds'] or 0
            if hasattr(avg_secs, 'total_seconds'):
                avg_hours = avg_secs.total_seconds() / 3600
            elif isinstance(avg_secs, (int, float)):
                avg_hours = avg_secs / 3_600_000_000 if avg_secs > 86400 else avg_secs / 3600
            else:
                avg_hours = 0

            # Get overdue count for this node
            overdue_count = WorkflowTask.objects.filter(
                is_deleted=False,
                node_name=item['node_name'],
                status='pending',
                due_date__lt=timezone.now(),
            ).count()

            bottleneck_list.append({
                'node_name': item['node_name'],
                'definition_name': item['definition_name'],
                'avg_duration_hours': round(abs(avg_hours), 1),
                'task_count': item['task_count'],
                'overdue_count': overdue_count,
                'overdue_rate': round(
                    (overdue_count / item['task_count'] * 100) if item['task_count'] > 0 else 0, 1
                ),
            })

        return BaseResponse.success(data={'bottlenecks': bottleneck_list})

    @action(detail=False, methods=['get'])
    def performance(self, request):
        """
        Get per-definition performance metrics.

        GET /api/workflows/statistics/performance/
        """
        definitions = WorkflowDefinition.objects.filter(
            is_deleted=False,
            is_active=True,
        )

        perf_data = []
        for defn in definitions:
            instances = WorkflowInstance.objects.filter(
                is_deleted=False,
                definition=defn,
            )
            total = instances.count()
            if total == 0:
                continue

            approved = instances.filter(status=WorkflowInstance.STATUS_APPROVED).count()
            rejected = instances.filter(status=WorkflowInstance.STATUS_REJECTED).count()
            running = instances.filter(
                status__in=[WorkflowInstance.STATUS_RUNNING, WorkflowInstance.STATUS_PENDING_APPROVAL]
            ).count()

            # Calculate average completion hours
            completed_qs = instances.filter(
                status=WorkflowInstance.STATUS_APPROVED,
                completed_at__isnull=False,
                started_at__isnull=False,
            )
            avg_hours = 0
            completed_count = completed_qs.count()
            if completed_count > 0:
                total_secs = sum(
                    (i.completed_at - i.started_at).total_seconds()
                    for i in completed_qs
                    if i.completed_at and i.started_at
                )
                avg_hours = total_secs / completed_count / 3600

            perf_data.append({
                'definition_name': defn.name,
                'definition_code': defn.code,
                'total_instances': total,
                'approved': approved,
                'rejected': rejected,
                'running': running,
                'approval_rate': round((approved / total * 100) if total > 0 else 0, 1),
                'avg_completion_hours': round(avg_hours, 1),
            })

        return BaseResponse.success(data={'definitions': perf_data})
