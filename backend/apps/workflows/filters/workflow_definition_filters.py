"""
Filters for WorkflowDefinition model.

Provides filtering and searching capabilities for workflow definitions.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.workflows.models.workflow_definition import WorkflowDefinition


class WorkflowDefinitionFilter(BaseModelFilter):
    """
    FilterSet for WorkflowDefinition model.

    Extends BaseModelFilter to provide common filtering plus workflow-specific filters.
    """

    # Workflow-specific filters
    status = django_filters.ChoiceFilter(
        choices=WorkflowDefinition.STATUS_CHOICES,
        field_name='status',
        label=_('Status')
    )

    is_active = django_filters.BooleanFilter(
        field_name='is_active',
        label=_('Is Active')
    )

    business_object_code = django_filters.CharFilter(
        field_name='business_object_code',
        lookup_expr='iexact',
        label=_('Business Object Code')
    )

    business_object_code_contains = django_filters.CharFilter(
        field_name='business_object_code',
        lookup_expr='icontains',
        label=_('Business Object Code Contains')
    )

    category = django_filters.CharFilter(
        field_name='category',
        lookup_expr='iexact',
        label=_('Category')
    )

    category_contains = django_filters.CharFilter(
        field_name='category',
        lookup_expr='icontains',
        label=_('Category Contains')
    )

    # Version filters
    version = django_filters.NumberFilter(
        field_name='version',
        label=_('Version')
    )

    version_gte = django_filters.NumberFilter(
        field_name='version',
        lookup_expr='gte',
        label=_('Version Greater or Equal')
    )

    version_lte = django_filters.NumberFilter(
        field_name='version',
        lookup_expr='lte',
        label=_('Version Less or Equal')
    )

    # Published date filters
    published_at = django_filters.DateFilter(
        field_name='published_at',
        label=_('Published Date')
    )

    published_at_after = django_filters.DateFilter(
        field_name='published_at',
        lookup_expr='gte',
        label=_('Published After')
    )

    published_at_before = django_filters.DateFilter(
        field_name='published_at',
        lookup_expr='lte',
        label=_('Published Before')
    )

    # Published by filter
    published_by = django_filters.UUIDFilter(
        field_name='published_by_id',
        label=_('Published By (User ID)')
    )

    # Source template filter
    source_template = django_filters.UUIDFilter(
        field_name='source_template_id',
        label=_('Source Template ID')
    )

    # Tags filter (JSONB array contains)
    has_tag = django_filters.CharFilter(
        method='filter_has_tag',
        label=_('Has Tag')
    )

    # Node count filters (computed from graph_data)
    node_count = django_filters.NumberFilter(
        method='filter_node_count',
        label=_('Node Count')
    )

    node_count_gte = django_filters.NumberFilter(
        method='filter_node_count_gte',
        label=_('Node Count Greater or Equal')
    )

    node_count_lte = django_filters.NumberFilter(
        method='filter_node_count_lte',
        label=_('Node Count Less or Equal')
    )

    # Complex search: search within graph_data
    has_node_type = django_filters.CharFilter(
        method='filter_has_node_type',
        label=_('Has Node Type')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowDefinition
        fields = BaseModelFilter.Meta.fields + [
            'status',
            'is_active',
            'business_object_code',
            'category',
            'version',
            'published_at',
            'published_by',
            'source_template',
        ]

    def filter_has_tag(self, queryset, name, value):
        """Filter workflows that contain a specific tag."""
        return queryset.filter(tags__contains=value)

    def filter_node_count(self, queryset, name, value):
        """Filter workflows with exact node count."""
        return queryset.filter(graph_data__nodes__len=value)

    def filter_node_count_gte(self, queryset, name, value):
        """Filter workflows with node count >= value."""
        # PostgreSQL JSONB length filtering
        return queryset.extra(where=["jsonb_array_length(graph_data->'nodes') >= %s"], params=[value])

    def filter_node_count_lte(self, queryset, name, value):
        """Filter workflows with node count <= value."""
        return queryset.extra(where=["jsonb_array_length(graph_data->'nodes') <= %s"], params=[value])

    def filter_has_node_type(self, queryset, name, value):
        """Filter workflows that contain a specific node type."""
        return queryset.filter(graph_data__nodes__type=value)
