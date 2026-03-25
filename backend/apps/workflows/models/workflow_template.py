"""
WorkflowTemplate Model - Reusable workflow templates.

Provides pre-configured workflow structures that can be instantiated
as new workflow definitions.
"""
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class WorkflowTemplate(BaseModel):
    """
    Workflow Template - reusable workflow definition template.

    Templates provide starting points for creating new workflows.
    They contain the same graph structure as WorkflowDefinition but
    are not tied to a specific business instance.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who created this template
    - custom_fields: Additional metadata storage
    """

    # === Template Type Choices ===
    TEMPLATE_TYPE_CHOICES = [
        ('system', _('System Template')),
        ('custom', _('Custom Template')),
        ('user_created', _('User Created')),
    ]

    # === Basic Information ===
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name=_('Template Code'),
        db_comment='Unique template code identifier'
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_('Template Name'),
        db_comment='Human-readable template name'
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Detailed description of the template'
    )

    # === Template Type ===
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default='custom',
        verbose_name=_('Template Type'),
        db_comment='Type of template: system, custom, or user_created'
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
        db_comment='Complete workflow graph data in LogicFlow format'
    )

    # === Form Permissions Template ===
    form_permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Form Permissions'),
        db_comment='Default field permissions for workflow nodes'
    )

    # === Preview Image ===
    preview_image = models.TextField(
        blank=True,
        verbose_name=_('Preview Image'),
        db_comment='Base64 or URL of workflow preview image'
    )

    # === Categorization ===
    category = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Category'),
        db_comment='Template category for grouping'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Tags'),
        db_comment='Tags for template classification'
    )

    # === Usage Tracking ===
    usage_count = models.IntegerField(
        default=0,
        verbose_name=_('Usage Count'),
        db_comment='Number of times this template has been used'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Is Featured'),
        db_comment='Whether this template is featured/promoted'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_('Is Public'),
        db_comment='Whether this template is available to all organizations'
    )

    # === Sort Order ===
    sort_order = models.IntegerField(
        default=0,
        verbose_name=_('Sort Order'),
        db_comment='Display order in template list'
    )

    class Meta:
        db_table = 'workflow_templates'
        verbose_name = _('Workflow Template')
        verbose_name_plural = _('Workflow Templates')
        ordering = ['sort_order', '-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['business_object_code']),
            models.Index(fields=['template_type']),
            models.Index(fields=['category']),
            models.Index(fields=['is_featured', 'is_public']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f'{self.name} ({self.get_template_type_display()})'

    def increment_usage(self):
        """Increment the usage count when template is used."""
        self.usage_count += 1
        self.save(update_fields=['usage_count', 'updated_at'])

    def instantiate(self, organization, user, name=None, code=None):
        """
        Create a new WorkflowDefinition from this template.

        Args:
            organization: Organization for the new workflow
            user: User creating the workflow
            name: Optional name for the new workflow
            code: Optional code for the new workflow

        Returns:
            New WorkflowDefinition instance
        """
        from apps.workflows.models.workflow_definition import WorkflowDefinition

        if name is None:
            name = self.name
        if code is None:
            code = f'{self.code}_{timezone.now().strftime("%Y%m%d%H%M%S")}'

        workflow = WorkflowDefinition(
            code=code,
            name=name,
            description=self.description,
            business_object_code=self.business_object_code,
            graph_data=self.graph_data.copy() if self.graph_data else {},
            form_permissions=self.form_permissions.copy() if self.form_permissions else {},
            category=self.category,
            tags=self.tags.copy() if self.tags else [],
            organization=organization,
            created_by=user,
            source_template=self,
            status='draft',
            version=1
        )
        workflow.save()

        self.increment_usage()

        return workflow
