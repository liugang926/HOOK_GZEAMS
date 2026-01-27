"""
Serializers for WorkflowTemplate model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.workflows.models.workflow_template import WorkflowTemplate


class WorkflowTemplateSerializer(BaseModelSerializer):
    """
    Base serializer for WorkflowTemplate.

    Extends BaseModelSerializer with template-specific fields.
    """

    # Read-only fields
    template_type_display = serializers.CharField(
        source='get_template_type_display',
        read_only=True
    )

    # Computed fields
    node_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowTemplate
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'name',
            'description',
            'template_type',
            'template_type_display',
            'business_object_code',
            'graph_data',
            'form_permissions',
            'preview_image',
            'category',
            'tags',
            'usage_count',
            'is_featured',
            'is_public',
            'sort_order',
            'node_count',
        ]
        extra_kwargs = {
            'graph_data': {'required': False},
            'form_permissions': {'required': False},
            'tags': {'required': False},
        }

    def get_node_count(self, obj):
        """Get total number of nodes in the template."""
        return len(obj.graph_data.get('nodes', []))


class WorkflowTemplateDetailSerializer(WorkflowTemplateSerializer):
    """
    Detailed serializer for workflow template detail views.

    Includes additional computed fields.
    """

    class Meta(WorkflowTemplateSerializer.Meta):
        fields = WorkflowTemplateSerializer.Meta.fields


class WorkflowTemplateListSerializer(WorkflowTemplateSerializer):
    """
    Lightweight serializer for template list views.

    Excludes large graph_data field.
    """

    class Meta(WorkflowTemplateSerializer.Meta):
        fields = [
            'id',
            'code',
            'name',
            'description',
            'template_type',
            'template_type_display',
            'business_object_code',
            'category',
            'tags',
            'usage_count',
            'is_featured',
            'is_public',
            'sort_order',
            'node_count',
            'preview_image',
            'created_at',
            'updated_at',
        ]


class WorkflowTemplateInstantiateSerializer(serializers.Serializer):
    """
    Serializer for instantiating a workflow from a template.
    """

    name = serializers.CharField(max_length=200, required=False)
    code = serializers.CharField(max_length=50, required=False)

    def validate_code(self, value):
        """Validate workflow code format."""
        if value and not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                _('Workflow code can only contain letters, numbers, hyphens, and underscores.')
            )
        return value
