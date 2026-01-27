"""
Admin configuration for workflow models.

Provides Django admin interfaces for WorkflowDefinition, WorkflowTemplate,
WorkflowOperationLog, WorkflowInstance, WorkflowTask, and WorkflowApproval models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count, Q

from apps.workflows.models.workflow_definition import WorkflowDefinition
from apps.workflows.models.workflow_template import WorkflowTemplate
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog
from apps.workflows.models.workflow_instance import WorkflowInstance
from apps.workflows.models.workflow_task import WorkflowTask
from apps.workflows.models.workflow_approval import WorkflowApproval


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowDefinition model.

    Features:
    - List view with key fields and filters
    - Search by code, name, description, tags
    - Soft delete handling
    - Status management actions
    - Graph data preview
    """

    list_display = [
        'code',
        'name',
        'business_object_code',
        'status',
        'version',
        'is_active',
        'node_count',
        'organization',
        'created_at',
    ]

    list_filter = [
        'status',
        'is_active',
        'business_object_code',
        'category',
        'organization',
        'created_at',
        'published_at',
    ]

    search_fields = [
        'code',
        'name',
        'description',
        'tags',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'deleted_at',
        'node_count_display',
        'edge_count_display',
        'graph_preview',
    ]

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'code',
                'name',
                'description',
                'business_object_code',
                'category',
                'tags',
            )
        }),
        (_('Workflow Graph'), {
            'fields': (
                'graph_data',
                'node_count_display',
                'edge_count_display',
                'graph_preview',
            )
        }),
        (_('Status & Version'), {
            'fields': (
                'status',
                'version',
                'is_active',
            )
        }),
        (_('Publishing'), {
            'fields': (
                'published_at',
                'published_by',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'form_permissions',
            ),
            'classes': ('collapse',),
        }),
        (_('Template'), {
            'fields': (
                'source_template',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit Information'), {
            'fields': (
                'id',
                'organization',
                'created_at',
                'updated_at',
                'created_by',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'publish_workflows',
        'unpublish_workflows',
        'activate_workflows',
        'deactivate_workflows',
        'soft_delete_selected',
    ]

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'created_by', 'published_by', 'source_template')

    def node_count(self, obj):
        """Get the number of nodes in the workflow."""
        return len(obj.graph_data.get('nodes', []))
    node_count.short_description = _('Nodes')

    def edge_count_display(self, obj):
        """Get the number of edges in the workflow."""
        return len(obj.graph_data.get('edges', []))
    edge_count_display.short_description = _('Edges')

    def node_count_display(self, obj):
        """Display node count in detail view."""
        count = len(obj.graph_data.get('nodes', []))
        return f"{count} nodes"

    def graph_preview(self, obj):
        """Show a preview of the graph structure."""
        nodes = obj.graph_data.get('nodes', [])
        edges = obj.graph_data.get('edges', [])

        node_types = {}
        for node in nodes:
            node_type = node.get('type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        type_summary = ', '.join([f"{t}: {c}" for t, c in node_types.items()])
        return format_html(
            '<strong>Nodes:</strong> {} | <strong>Edges:</strong> {}<br>'
            '<strong>Types:</strong> {}',
            len(nodes), len(edges), type_summary
        )
    graph_preview.short_description = _('Graph Preview')

    def publish_workflows(self, request, queryset):
        """Publish selected workflows."""
        from django.utils import timezone
        count = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, _(f'{count} workflow(s) published successfully.'))
    publish_workflows.short_description = _('Publish selected workflows')

    def unpublish_workflows(self, request, queryset):
        """Unpublish selected workflows."""
        count = queryset.update(status='draft')
        self.message_user(request, _(f'{count} workflow(s) unpublished successfully.'))
    unpublish_workflows.short_description = _('Unpublish selected workflows')

    def activate_workflows(self, request, queryset):
        """Activate selected workflows."""
        count = queryset.update(is_active=True)
        self.message_user(request, _(f'{count} workflow(s) activated successfully.'))
    activate_workflows.short_description = _('Activate selected workflows')

    def deactivate_workflows(self, request, queryset):
        """Deactivate selected workflows."""
        count = queryset.update(is_active=False)
        self.message_user(request, _(f'{count} workflow(s) deactivated successfully.'))
    deactivate_workflows.short_description = _('Deactivate selected workflows')

    def soft_delete_selected(self, request, queryset):
        """Soft delete selected workflows."""
        from django.utils import timezone
        count = queryset.update(is_deleted=True, deleted_at=timezone.now())
        self.message_user(request, _(f'{count} workflow(s) deleted successfully.'))
    soft_delete_selected.short_description = _('Soft delete selected workflows')


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowTemplate model.

    Features:
    - List view with usage statistics
    - Search and filter capabilities
    - Featured/public template management
    """

    list_display = [
        'code',
        'name',
        'template_type',
        'business_object_code',
        'is_featured',
        'is_public',
        'usage_count',
        'sort_order',
        'organization',
        'created_at',
    ]

    list_filter = [
        'template_type',
        'is_featured',
        'is_public',
        'business_object_code',
        'category',
        'organization',
    ]

    search_fields = [
        'code',
        'name',
        'description',
        'tags',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'usage_count',
        'node_count_display',
    ]

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'code',
                'name',
                'description',
                'template_type',
                'business_object_code',
                'category',
                'tags',
            )
        }),
        (_('Template Content'), {
            'fields': (
                'graph_data',
                'form_permissions',
                'node_count_display',
            )
        }),
        (_('Display Settings'), {
            'fields': (
                'is_featured',
                'is_public',
                'sort_order',
            )
        }),
        (_('Media'), {
            'fields': (
                'preview_image',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit Information'), {
            'fields': (
                'id',
                'organization',
                'usage_count',
                'created_at',
                'updated_at',
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'mark_as_featured',
        'remove_from_featured',
        'make_public',
        'make_private',
    ]

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'created_by')

    def node_count_display(self, obj):
        """Display node count in detail view."""
        count = len(obj.graph_data.get('nodes', []))
        return f"{count} nodes"

    def mark_as_featured(self, request, queryset):
        """Mark selected templates as featured."""
        count = queryset.update(is_featured=True)
        self.message_user(request, _(f'{count} template(s) marked as featured.'))
    mark_as_featured.short_description = _('Mark as featured')

    def remove_from_featured(self, request, queryset):
        """Remove featured status from selected templates."""
        count = queryset.update(is_featured=False)
        self.message_user(request, _(f'{count} template(s) removed from featured.'))
    remove_from_featured.short_description = _('Remove from featured')

    def make_public(self, request, queryset):
        """Make selected templates public."""
        count = queryset.update(is_public=True)
        self.message_user(request, _(f'{count} template(s) made public.'))
    make_public.short_description = _('Make public')

    def make_private(self, request, queryset):
        """Make selected templates private."""
        count = queryset.update(is_public=False)
        self.message_user(request, _(f'{count} template(s) made private.'))
    make_private.short_description = _('Make private')


@admin.register(WorkflowOperationLog)
class WorkflowOperationLogAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowOperationLog model.

    Features:
    - Read-only audit trail
    - Filtering by operation type and result
    - Performance metrics display
    """

    list_display = [
        'operation_type',
        'target_type',
        'target_name',
        'target_code',
        'result',
        'actor',
        'created_at',
    ]

    list_filter = [
        'operation_type',
        'target_type',
        'result',
        'organization',
        'created_at',
    ]

    search_fields = [
        'target_name',
        'target_code',
        'error_message',
        'actor__email',
        'actor__username',
    ]

    readonly_fields = [
        'id',
        'operation_type',
        'target_type',
        'target_name',
        'target_code',
        'actor',
        'workflow_definition',
        'workflow_template',
        'result',
        'operation_details',
        'previous_state',
        'error_message',
        'ip_address',
        'user_agent',
        'request_metadata',
        'organization',
        'created_at',
    ]

    fieldsets = (
        (_('Operation Information'), {
            'fields': (
                'operation_type',
                'target_type',
                'target_name',
                'target_code',
            )
        }),
        (_('Related Objects'), {
            'fields': (
                'workflow_definition',
                'workflow_template',
            )
        }),
        (_('Actor & Context'), {
            'fields': (
                'actor',
                'ip_address',
                'user_agent',
            )
        }),
        (_('Result'), {
            'fields': (
                'result',
                'error_message',
            )
        }),
        (_('Details'), {
            'fields': (
                'operation_details',
                'previous_state',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit Information'), {
            'fields': (
                'id',
                'organization',
                'created_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related(
            'actor',
            'organization',
            'workflow_definition',
            'workflow_template',
        )

    def has_add_permission(self, request):
        """Disable manual creation of logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make logs read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion of logs."""
        return False


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowInstance model.

    Features:
    - List view with status and progress tracking
    - Workflow lifecycle actions
    - Timeline view
    """

    list_display = [
        'instance_no',
        'definition_name',
        'business_object_code',
        'business_no',
        'status',
        'status_display',
        'initiator',
        'progress',
        'started_at',
        'completed_at',
    ]

    list_filter = [
        'status',
        'priority',
        'business_object_code',
        'organization',
        'started_at',
        'completed_at',
    ]

    search_fields = [
        'instance_no',
        'business_no',
        'title',
        'initiator__username',
        'initiator__email',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'definition',
        'instance_no',
        'progress_percentage',
        'duration_hours',
        'graph_snapshot',
    ]

    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'instance_no',
                'definition',
                'title',
                'description',
            )
        }),
        (_('Business Context'), {
            'fields': (
                'business_object_code',
                'business_id',
                'business_no',
            )
        }),
        (_('Status & Progress'), {
            'fields': (
                'status',
                'current_node_id',
                'current_node_name',
                'priority',
                'progress_percentage',
                'duration_hours',
            )
        }),
        (_('Timeline'), {
            'fields': (
                'initiator',
                'started_at',
                'completed_at',
                'terminated_at',
                'terminated_by',
                'termination_reason',
            )
        }),
        (_('Variables'), {
            'fields': (
                'variables',
                'estimated_hours',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'id',
                'organization',
                'created_at',
                'updated_at',
                'created_by',
                'graph_snapshot',
            ),
            'classes': ('collapse',),
        }),
    )

    actions = [
        'cancel_instances',
        'terminate_instances',
    ]

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('definition', 'initiator', 'organization', 'terminated_by')

    def definition_name(self, obj):
        """Get definition name."""
        return obj.definition.name if obj.definition else '-'
    definition_name.short_description = _('Definition')

    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'draft': 'gray',
            'running': 'blue',
            'pending_approval': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
            'terminated': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Status')

    def progress(self, obj):
        """Display progress bar."""
        percentage = obj.progress_percentage
        return format_html(
            '<div style="width: 100px; background: #e0e0e0; border-radius: 4px;">'
            '<div style="width: {}%; background: #28a745; border-radius: 4px; height: 8px;"></div>'
            '</div> {}%',
            percentage, percentage
        )
    progress.short_description = _('Progress')

    def cancel_instances(self, request, queryset):
        """Cancel selected instances."""
        from django.utils import timezone
        count = 0
        for instance in queryset:
            try:
                if instance.status in instance.ACTIVE_STATUSES:
                    instance.cancel(request.user)
                    count += 1
            except Exception:
                pass
        self.message_user(request, _(f'{count} instance(s) cancelled successfully.'))
    cancel_instances.short_description = _('Cancel instances')

    def terminate_instances(self, request, queryset):
        """Terminate selected instances (admin only)."""
        count = 0
        for instance in queryset:
            try:
                if instance.status not in instance.TERMINAL_STATUSES:
                    instance.terminate(request.user, 'Admin bulk termination')
                    count += 1
            except Exception:
                pass
        self.message_user(request, _(f'{count} instance(s) terminated successfully.'))
    terminate_instances.short_description = _('Terminate instances')


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowTask model.

    Features:
    - List view with task status and assignee
    - Filter by status and node type
    - Overdue task highlighting
    """

    list_display = [
        'node_name',
        'instance_no',
        'assignee',
        'status',
        'status_display',
        'is_overdue',
        'due_date',
        'created_at',
    ]

    list_filter = [
        'status',
        'node_type',
        'priority',
        'organization',
        'created_at',
        'due_date',
    ]

    search_fields = [
        'node_name',
        'node_id',
        'assignee__username',
        'assignee__email',
        'instance__instance_no',
        'instance__business_no',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'created_by',
        'instance',
        'node_id',
        'is_overdue',
        'duration_hours',
    ]

    fieldsets = (
        (_('Task Information'), {
            'fields': (
                'instance',
                'node_id',
                'node_name',
                'node_type',
                'approve_type',
                'sequence',
            )
        }),
        (_('Assignment'), {
            'fields': (
                'assignee',
                'status',
                'priority',
            )
        }),
        (_('Timing'), {
            'fields': (
                'due_date',
                'is_overdue',
                'duration_hours',
                'completed_at',
                'completed_by',
            )
        }),
        (_('Delegation'), {
            'fields': (
                'delegated_to',
                'delegated_from',
                'delegated_at',
                'delegation_reason',
            ),
            'classes': ('collapse',),
        }),
        (_('Properties'), {
            'fields': (
                'node_properties',
            ),
            'classes': ('collapse',),
        }),
        (_('Audit Information'), {
            'fields': (
                'id',
                'organization',
                'created_at',
                'updated_at',
                'created_by',
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('instance__definition', 'assignee', 'delegated_to', 'delegated_from', 'organization')

    def instance_no(self, obj):
        """Get instance number."""
        return obj.instance.instance_no
    instance_no.short_description = _('Instance')

    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'returned': 'gray',
            'cancelled': 'gray',
            'terminated': 'red',
            'delegated': 'blue',
            'withdrawn': 'gray',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Status')

    def is_overdue(self, obj):
        """Show if task is overdue."""
        if obj.is_overdue:
            return format_html('<span style="color: red;">⚠ {}</span>', _('Yes'))
        return _('No')
    is_overdue.short_description = _('Overdue')


@admin.register(WorkflowApproval)
class WorkflowApprovalAdmin(admin.ModelAdmin):
    """
    Admin interface for WorkflowApproval model.

    Features:
    - Read-only audit trail
    - Filter by action and task
    """

    list_display = [
        'action',
        'action_display',
        'task_node_name',
        'approver_name',
        'comment_preview',
        'created_at',
    ]

    list_filter = [
        'action',
        'task__node_type',
        'organization',
        'created_at',
    ]

    search_fields = [
        'approver__username',
        'approver__email',
        'comment',
        'task__node_name',
    ]

    readonly_fields = [
        'id',
        'task',
        'approver',
        'action',
        'comment',
        'attachment',
        'ip_address',
        'user_agent',
        'previous_status',
        'new_status',
        'created_at',
        'organization',
    ]

    def get_queryset(self, request):
        """Optimize queryset with related data."""
        qs = super().get_queryset(request)
        return qs.select_related('task', 'approver', 'organization')

    def task_node_name(self, obj):
        """Get task node name."""
        return obj.task.node_name if obj.task else '-'
    task_node_name.short_description = _('Task')

    def approver_name(self, obj):
        """Get approver name."""
        return obj.approver.get_full_name() or obj.approver.username
    approver_name.short_description = _('Approver')

    def action_display(self, obj):
        """Display action with color."""
        colors = {
            'approve': 'green',
            'reject': 'red',
            'return': 'orange',
            'delegate': 'blue',
            'withdraw': 'gray',
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = _('Action')

    def comment_preview(self, obj):
        """Show comment preview."""
        if obj.comment:
            preview = obj.comment[:50]
            if len(obj.comment) > 50:
                preview += '...'
            return preview
        return '-'
    comment_preview.short_description = _('Comment')

    def has_add_permission(self, request):
        """Disable manual creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Make approvals read-only."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion."""
        return False
