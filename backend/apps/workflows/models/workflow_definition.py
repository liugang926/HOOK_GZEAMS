"""
WorkflowDefinition Model - Core model for storing workflow definitions.

Stores LogicFlow-compatible workflow graph data with nodes and edges.
Supports version control, status management, and organization isolation.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class WorkflowDefinition(BaseModel):
    """
    Workflow Definition - stores complete workflow graph structure.

    Graph Data Structure (LogicFlow format):
    {
        "nodes": [
            {
                "id": "node_1",
                "type": "start|approval|condition|cc|notify|parallel|end",
                "x": 100,
                "y": 100,
                "text": "Node Name",
                "properties": {...}
            }
        ],
        "edges": [
            {
                "id": "edge_1",
                "sourceNodeId": "node_1",
                "targetNodeId": "node_2",
                "type": "polyline",
                "properties": {...}
            }
        ]
    }

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who created this workflow
    - custom_fields: Additional metadata storage
    """

    # === Status Choices ===
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('archived', _('Archived')),
        ('deprecated', _('Deprecated')),
    ]

    # === Basic Information ===
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_('Workflow Code'),
        db_comment='Unique workflow code identifier'
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Workflow Name'),
        db_comment='Human-readable workflow name'
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Detailed description of the workflow'
    )

    # === Business Object Association ===
    business_object_code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name=_('Business Object Code'),
        db_comment='Associated business object (e.g., asset_pickup, asset_transfer)'
    )

    # === Workflow Graph Data (LogicFlow format) ===
    graph_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Graph Data'),
        db_comment='Complete workflow graph data in LogicFlow format (nodes, edges)'
    )

    # === Status and Version Control ===
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status'),
        db_comment='Workflow status: draft, published, archived, deprecated'
    )
    version = models.IntegerField(
        default=1,
        verbose_name=_('Version'),
        db_comment='Workflow version number, auto-incremented on publish'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        db_comment='Whether this workflow definition is active for use'
    )

    # === Publishing Metadata ===
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Published At'),
        db_comment='Timestamp when workflow was first published'
    )
    published_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_workflows',
        verbose_name=_('Published By'),
        db_comment='User who published this workflow'
    )

    # === Form Field Permissions ===
    # Stores field permissions per node: {node_id: {field_code: permission}}
    # Permission levels: editable, read_only, hidden
    form_permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Form Permissions'),
        db_comment='Field-level permissions for each workflow node'
    )

    # === Categorization ===
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Category'),
        db_comment='Workflow category for grouping and filtering'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Tags'),
        db_comment='Tags for workflow classification and search'
    )

    # === Template Reference ===
    # If created from a template, references the source template
    source_template = models.ForeignKey(
        'WorkflowTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instantiated_workflows',
        verbose_name=_('Source Template'),
        db_comment='Template this workflow was created from'
    )

    class Meta:
        db_table = 'workflow_definitions'
        verbose_name = _('Workflow Definition')
        verbose_name_plural = _('Workflow Definitions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['business_object_code']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['organization', 'business_object_code', 'is_active']),
        ]
        unique_together = [
            ['code', 'organization'],
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(version__gte=1),
                name='workflow_definition_version_gte_1'
            )
        ]

    def __str__(self):
        return f'{self.name} (v{self.version}) - {self.get_status_display()}'

    def clean(self):
        """Validate workflow definition before saving."""
        super().clean()

        # Validate graph_data structure
        if self.graph_data:
            self._validate_graph_structure(self.graph_data)

        # Validate code format
        if self.code:
            if not self.code.replace('_', '').replace('-', '').isalnum():
                raise ValidationError({
                    'code': _('Workflow code can only contain letters, numbers, hyphens, and underscores.')
                })

    def _validate_graph_structure(self, graph_data):
        """Validate the graph data structure."""
        if not isinstance(graph_data, dict):
            raise ValidationError({
                'graph_data': _('Graph data must be a dictionary.')
            })

        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])

        # Validate nodes is a list
        if not isinstance(nodes, list):
            raise ValidationError({
                'graph_data': _('Graph nodes must be a list.')
            })

        # Validate edges is a list
        if not isinstance(edges, list):
            raise ValidationError({
                'graph_data': _('Graph edges must be a list.')
            })

        # Check for required nodes
        node_types = {node.get('type') for node in nodes}
        if 'start' not in node_types:
            raise ValidationError({
                'graph_data': _('Workflow must have a start node.')
            })
        if 'end' not in node_types:
            raise ValidationError({
                'graph_data': _('Workflow must have an end node.')
            })

        # Validate node IDs are unique
        node_ids = [node.get('id') for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise ValidationError({
                'graph_data': _('Node IDs must be unique.')
            })

        # Validate edge references
        node_id_set = set(node_ids)
        for edge in edges:
            source = edge.get('sourceNodeId')
            target = edge.get('targetNodeId')

            if source not in node_id_set:
                raise ValidationError({
                    'graph_data': _(f'Edge references non-existent source node: {source}')
                })

            if target not in node_id_set:
                raise ValidationError({
                    'graph_data': _(f'Edge references non-existent target node: {target}')
                })

    def get_nodes_by_type(self, node_type):
        """
        Get all nodes of a specific type.

        Args:
            node_type: Type of node (start, end, approval, condition, etc.)

        Returns:
            List of nodes matching the type
        """
        return [
            node for node in self.graph_data.get('nodes', [])
            if node.get('type') == node_type
        ]

    def get_node(self, node_id):
        """
        Get a specific node by ID.

        Args:
            node_id: Node ID to find

        Returns:
            Node dict or None
        """
        for node in self.graph_data.get('nodes', []):
            if node.get('id') == node_id:
                return node
        return None

    def get_approval_nodes(self):
        """Get all approval nodes in the workflow."""
        return self.get_nodes_by_type('approval')

    def get_condition_nodes(self):
        """Get all condition nodes in the workflow."""
        return self.get_nodes_by_type('condition')

    def get_start_node(self):
        """Get the start node of the workflow."""
        start_nodes = self.get_nodes_by_type('start')
        return start_nodes[0] if start_nodes else None

    def get_end_nodes(self):
        """Get all end nodes in the workflow."""
        return self.get_nodes_by_type('end')

    def publish(self, user):
        """
        Publish the workflow definition.

        Args:
            user: User publishing the workflow

        Returns:
            True if published successfully
        """
        if self.status == 'published':
            return False

        self.status = 'published'
        self.published_at = timezone.now()
        self.published_by = user
        self.save(update_fields=['status', 'published_at', 'published_by', 'updated_at'])
        return True

    def unpublish(self):
        """
        Unpublish the workflow definition.

        Returns:
            True if unpublished successfully
        """
        if self.status != 'published':
            return False

        self.status = 'draft'
        self.save(update_fields=['status', 'updated_at'])
        return True

    def create_new_version(self):
        """
        Create a new version of this workflow.

        Returns:
            New WorkflowDefinition instance with incremented version
        """
        self.pk = None
        self.id = None
        self.version += 1
        self.status = 'draft'
        self.published_at = None
        self.published_by = None
        self.save()
        return self

    def clone(self, new_name=None, new_code=None):
        """
        Clone this workflow definition.

        Args:
            new_name: Name for the cloned workflow
            new_code: Code for the cloned workflow

        Returns:
            New WorkflowDefinition instance
        """
        if new_name is None:
            new_name = f'{self.name} (copy)'
        if new_code is None:
            new_code = f'{self.code}_copy'

        cloned = WorkflowDefinition(
            code=new_code,
            name=new_name,
            description=self.description,
            business_object_code=self.business_object_code,
            graph_data=self.graph_data.copy(),
            form_permissions=self.form_permissions.copy() if self.form_permissions else {},
            category=self.category,
            tags=self.tags.copy() if self.tags else [],
            organization=self.organization,
            created_by=self.created_by,
            status='draft',
            version=1
        )
        cloned.save()
        return cloned

    def get_form_permissions_for_node(self, node_id):
        """
        Get form permissions for a specific node.

        Args:
            node_id: Node ID to get permissions for

        Returns:
            Dict of field_code -> permission level
        """
        return self.form_permissions.get(node_id, {})

    def set_form_permissions_for_node(self, node_id, permissions):
        """
        Set form permissions for a specific node.

        Args:
            node_id: Node ID to set permissions for
            permissions: Dict of field_code -> permission level
        """
        if not self.form_permissions:
            self.form_permissions = {}
        self.form_permissions[node_id] = permissions
        self.save(update_fields=['form_permissions', 'updated_at'])
