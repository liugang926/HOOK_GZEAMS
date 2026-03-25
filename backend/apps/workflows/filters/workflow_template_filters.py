"""
Filters for WorkflowTemplate model.

Provides filtering and searching capabilities for workflow templates.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.workflows.models.workflow_template import WorkflowTemplate


class WorkflowTemplateFilter(BaseModelFilter):
    """
    FilterSet for WorkflowTemplate model.

    Extends BaseModelFilter to provide common filtering plus template-specific filters.
    """

    # Template-specific filters
    template_type = django_filters.ChoiceFilter(
        choices=WorkflowTemplate.TEMPLATE_TYPE_CHOICES,
        field_name='template_type',
        label=_('Template Type')
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

    # Featured filter
    is_featured = django_filters.BooleanFilter(
        field_name='is_featured',
        label=_('Is Featured')
    )

    # Public filter
    is_public = django_filters.BooleanFilter(
        field_name='is_public',
        label=_('Is Public')
    )

    # Usage count filters
    usage_count = django_filters.NumberFilter(
        field_name='usage_count',
        label=_('Usage Count')
    )

    usage_count_gte = django_filters.NumberFilter(
        field_name='usage_count',
        lookup_expr='gte',
        label=_('Usage Count Greater or Equal')
    )

    usage_count_lte = django_filters.NumberFilter(
        field_name='usage_count',
        lookup_expr='lte',
        label=_('Usage Count Less or Equal')
    )

    # Sort order filter
    sort_order = django_filters.NumberFilter(
        field_name='sort_order',
        label=_('Sort Order')
    )

    # Tags filter
    has_tag = django_filters.CharFilter(
        method='filter_has_tag',
        label=_('Has Tag')
    )

    # Node count filter (from graph_data)
    node_count = django_filters.NumberFilter(
        method='filter_node_count',
        label=_('Node Count')
    )

    class Meta(BaseModelFilter.Meta):
        model = WorkflowTemplate
        fields = BaseModelFilter.Meta.fields + [
            'template_type',
            'business_object_code',
            'category',
            'is_featured',
            'is_public',
            'usage_count',
            'sort_order',
        ]

    def filter_has_tag(self, queryset, name, value):
        """Filter templates that contain a specific tag."""
        return queryset.filter(tags__contains=value)

    def filter_node_count(self, queryset, name, value):
        """Filter templates with exact node count."""
        return queryset.filter(graph_data__nodes__len=value)
