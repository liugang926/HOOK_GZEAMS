"""
Filters for workflow execution models.

Provides filtering and searching capabilities for workflow instances and tasks.
"""
import django_filters
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from apps.common.filters.base import BaseModelFilter
from apps.workflows.models import WorkflowInstance, WorkflowTask


class WorkflowInstanceFilter(BaseModelFilter):
    """
    FilterSet for WorkflowInstance model.

    Extends BaseModelFilter to provide common filtering plus instance-specific filters.
    """

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=WorkflowInstance.STATUS_CHOICES,
        field_name='status',
        label=_('Status')
    )

    # Priority filter
    priority = django_filters.ChoiceFilter(
        choices=[('low', _('Low')), ('normal', _('Normal')), ('high', _('High')), ('urgent', _('Urgent'))],
        field_name='priority',
        label=_('Priority')
    )

    # Definition filter
    definition = django_filters.UUIDFilter(
        field_name='definition_id',
        label=_('Workflow Definition ID')
    )

    # Business object code filter
    business_object_code = django_filters.CharFilter(
        field_name='business_object_code',
        lookup_expr='iexact',
        label=_('Business Object Code')
    )

    # Instance no filter
    instance_no = django_filters.CharFilter(
        field_name='instance_no',
        lookup_expr='icontains',
        label=_('Instance No Contains')
    )

    # Business no filter
    business_no = django_filters.CharFilter(
        field_name='business_no',
        lookup_expr='icontains',
        label=_('Business No Contains')
    )

    # Initiator filter
    initiator = django_filters.UUIDFilter(
        field_name='initiator_id',
        label=_('Initiator User ID')
    )

    # Started date range filters
    started_after = django_filters.DateTimeFilter(
        field_name='started_at',
        lookup_expr='gte',
        label=_('Started After')
    )

    started_before = django_filters.DateTimeFilter(
        field_name='started_at',
        lookup_expr='lte',
        label=_('Started Before')
    )

    # Completed date range filters
    completed_after = django_filters.DateTimeFilter(
        field_name='completed_at',
        lookup_expr='gte',
        label=_('Completed After')
    )

    completed_before = django_filters.DateTimeFilter(
        field_name='completed_at',
        lookup_expr='lte',
        label=_('Completed Before')
    )

    # Active instances (not terminal)
    is_active = django_filters.BooleanFilter(
        method='filter_is_active',
        label=_('Is Active')
    )

    # Overdue instances (has overdue pending tasks)
    has_overdue_tasks = django_filters.BooleanFilter(
        method='filter_has_overdue',
        label=_('Has Overdue Tasks')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowInstance
        fields = BaseModelFilter.Meta.fields + [
            'status',
            'priority',
            'definition',
            'business_object_code',
            'instance_no',
            'business_no',
            'initiator',
            'started_after',
            'started_before',
            'completed_after',
            'completed_before',
        ]

    def filter_is_active(self, queryset, name, value):
        """Filter for active (non-terminal) instances."""
        if value:
            return queryset.filter(status__in=WorkflowInstance.ACTIVE_STATUSES)
        return queryset.filter(status__in=WorkflowInstance.TERMINAL_STATUSES)

    def filter_has_overdue(self, queryset, name, value):
        """Filter for instances with overdue tasks."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                tasks__status='pending',
                tasks__due_date__lt=timezone.now()
            ).distinct()
        return queryset


class WorkflowTaskFilter(BaseModelFilter):
    """
    FilterSet for WorkflowTask model.

    Extends BaseModelFilter to provide common filtering plus task-specific filters.
    """

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=WorkflowTask.STATUS_CHOICES,
        field_name='status',
        label=_('Status')
    )

    # Node type filter
    node_type = django_filters.ChoiceFilter(
        choices=WorkflowTask.NODE_TYPE_CHOICES,
        field_name='node_type',
        label=_('Node Type')
    )

    # Instance filter
    instance = django_filters.UUIDFilter(
        field_name='instance_id',
        label=_('Workflow Instance ID')
    )

    # Assignee filter
    assignee = django_filters.UUIDFilter(
        field_name='assignee_id',
        label=_('Assignee User ID')
    )

    # Due date filters
    due_after = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte',
        label=_('Due After')
    )

    due_before = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte',
        label=_('Due Before')
    )

    # Overdue filter (pending tasks past due date)
    is_overdue = django_filters.BooleanFilter(
        method='filter_is_overdue',
        label=_('Is Overdue')
    )

    # Priority filter
    priority = django_filters.ChoiceFilter(
        choices=[('low', _('Low')), ('normal', _('Normal')), ('high', _('High')), ('urgent', _('Urgent'))],
        field_name='priority',
        label=_('Priority')
    )

    # Node name filter
    node_name = django_filters.CharFilter(
        field_name='node_name',
        lookup_expr='icontains',
        label=_('Node Name Contains')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowTask
        fields = BaseModelFilter.Meta.fields + [
            'status',
            'node_type',
            'instance',
            'assignee',
            'due_after',
            'due_before',
            'priority',
            'node_name',
        ]

    def filter_is_overdue(self, queryset, name, value):
        """Filter for overdue tasks."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                status='pending',
                due_date__lt=timezone.now()
            )
        return queryset.exclude(
            status='pending',
            due_date__lt=timezone.now()
        )


class WorkflowApprovalFilter(BaseModelFilter):
    """
    FilterSet for WorkflowApproval model.

    Extends BaseModelFilter to provide common filtering plus approval-specific filters.
    """

    # Action filter
    action = django_filters.ChoiceFilter(
        choices=WorkflowApproval.ACTION_CHOICES,
        field_name='action',
        label=_('Action')
    )

    # Task filter
    task = django_filters.UUIDFilter(
        field_name='task_id',
        label=_('Task ID')
    )

    # Approver filter
    approver = django_filters.UUIDFilter(
        field_name='approver_id',
        label=_('Approver User ID')
    )

    # Instance filter (via task)
    instance = django_filters.UUIDFilter(
        field_name='task__instance_id',
        label=_('Instance ID')
    )

    # Has comment filter
    has_comment = django_filters.BooleanFilter(
        method='filter_has_comment',
        label=_('Has Comment')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowApproval
        fields = BaseModelFilter.Meta.fields + [
            'action',
            'task',
            'approver',
            'instance',
        ]

    def filter_has_comment(self, queryset, name, value):
        """Filter for approvals with comments."""
        if value:
            return queryset.exclude(comment__isnull=True).exclude(comment='')
        return queryset.filter(comment__isnull=True) | queryset.filter(comment='')
