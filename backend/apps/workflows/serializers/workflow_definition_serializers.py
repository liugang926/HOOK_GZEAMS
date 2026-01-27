"""
Serializers for WorkflowDefinition model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.workflows.models.workflow_definition import WorkflowDefinition


class WorkflowDefinitionSerializer(BaseModelSerializer):
    """
    Base serializer for WorkflowDefinition.

    Extends BaseModelSerializer with workflow-specific fields.
    """

    # Read-only fields
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    # Computed fields
    node_count = serializers.SerializerMethodField()
    approval_node_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'name',
            'description',
            'business_object_code',
            'graph_data',
            'status',
            'status_display',
            'version',
            'is_active',
            'published_at',
            'form_permissions',
            'category',
            'tags',
            'source_template',
            'node_count',
            'approval_node_count',
        ]
        extra_kwargs = {
            'graph_data': {'required': False},
            'form_permissions': {'required': False},
            'tags': {'required': False},
        }

    def get_node_count(self, obj):
        """Get total number of nodes in the workflow."""
        return len(obj.graph_data.get('nodes', []))

    def get_approval_node_count(self, obj):
        """Get number of approval nodes in the workflow."""
        return len(obj.get_approval_nodes())

    def validate_graph_data(self, value):
        """Validate graph data structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_('Graph data must be a dictionary.'))

        nodes = value.get('nodes', [])
        edges = value.get('edges', [])

        if not isinstance(nodes, list):
            raise serializers.ValidationError(_('Graph nodes must be a list.'))

        if not isinstance(edges, list):
            raise serializers.ValidationError(_('Graph edges must be a list.'))

        # Validate required nodes
        node_types = {node.get('type') for node in nodes}
        if 'start' not in node_types:
            raise serializers.ValidationError(_('Workflow must have a start node.'))

        if 'end' not in node_types:
            raise serializers.ValidationError(_('Workflow must have an end node.'))

        # Validate node ID uniqueness
        node_ids = [node.get('id') for node in nodes]
        if len(node_ids) != len(set(node_ids)):
            raise serializers.ValidationError(_('Node IDs must be unique.'))

        return value

    def validate_code(self, value):
        """Validate workflow code format."""
        if value and not value.replace('_', '').replace('-', '').isalnum():
            raise serializers.ValidationError(
                _('Workflow code can only contain letters, numbers, hyphens, and underscores.')
            )
        return value


class WorkflowDefinitionListSerializer(WorkflowDefinitionSerializer):
    """
    Lightweight serializer for workflow list views.

    Excludes large graph_data field for better performance.
    """

    class Meta(WorkflowDefinitionSerializer.Meta):
        fields = [
            'id',
            'code',
            'name',
            'description',
            'business_object_code',
            'status',
            'status_display',
            'version',
            'is_active',
            'published_at',
            'category',
            'tags',
            'node_count',
            'approval_node_count',
            'created_at',
            'updated_at',
        ]


class WorkflowDefinitionDetailSerializer(WorkflowDefinitionSerializer):
    """
    Detailed serializer for workflow detail views.

    Includes additional computed fields and nested relationships.
    """

    # Published by info
    published_by_name = serializers.CharField(source='published_by.username', read_only=True)

    # Source template info
    source_template_name = serializers.CharField(source='source_template.name', read_only=True)
    source_template_code = serializers.CharField(source='source_template.code', read_only=True)

    # Organization info
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta(WorkflowDefinitionSerializer.Meta):
        fields = WorkflowDefinitionSerializer.Meta.fields + [
            'published_by_name',
            'source_template_name',
            'source_template_code',
            'organization_name',
        ]


class WorkflowDefinitionCreateSerializer(WorkflowDefinitionSerializer):
    """
    Serializer for creating workflow definitions.

    Includes validation for required fields.
    """

    class Meta(WorkflowDefinitionSerializer.Meta):
        fields = [
            'code',
            'name',
            'description',
            'business_object_code',
            'graph_data',
            'form_permissions',
            'category',
            'tags',
            'source_template',
        ]

    def validate(self, attrs):
        """Validate workflow creation data."""
        # Ensure graph_data has at least start and end nodes
        graph_data = attrs.get('graph_data', {})
        if graph_data:
            nodes = graph_data.get('nodes', [])
            node_types = {node.get('type') for node in nodes}
            if 'start' not in node_types:
                raise serializers.ValidationError({
                    'graph_data': _('Workflow must have a start node.')
                })
            if 'end' not in node_types:
                raise serializers.ValidationError({
                    'graph_data': _('Workflow must have an end node.')
                })
        return attrs


class WorkflowDefinitionUpdateSerializer(serializers.Serializer):
    """
    Serializer for partial workflow updates.

    Allows updating specific fields without full object replacement.
    """

    name = serializers.CharField(required=False, max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    graph_data = serializers.JSONField(required=False)
    form_permissions = serializers.JSONField(required=False)
    category = serializers.CharField(required=False, allow_blank=True, max_length=100)
    tags = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_graph_data(self, value):
        """Validate graph data structure."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(_('Graph data must be a dictionary.'))
        return value


class WorkflowValidationSerializer(serializers.Serializer):
    """
    Serializer for workflow validation requests.
    """

    graph_data = serializers.JSONField()

    def validate_graph_data(self, value):
        """Validate graph data structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(_('Graph data must be a dictionary.'))

        nodes = value.get('nodes', [])
        edges = value.get('edges', [])

        if not isinstance(nodes, list):
            raise serializers.ValidationError(_('Graph nodes must be a list.'))

        if not isinstance(edges, list):
            raise serializers.ValidationError(_('Graph edges must be a list.'))

        return value


class WorkflowPublishSerializer(serializers.Serializer):
    """
    Serializer for workflow publish requests.
    """

    version_comment = serializers.CharField(required=False, allow_blank=True, max_length=500)
    force = serializers.BooleanField(required=False, default=False)
