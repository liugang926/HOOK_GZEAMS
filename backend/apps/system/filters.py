"""
Filters for the metadata-driven low-code engine.

All filters inherit from BaseModelFilter which provides:
- Time range filtering (created_at_from, created_at_to, etc.)
- User filtering (created_by)
- Soft delete status filtering (is_deleted)
"""
from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData,
    DynamicSubTableData
)


class BusinessObjectFilter(BaseModelFilter):
    """
    Business Object filter.

    Inherits from BaseModelFilter which provides:
    - created_at_from, created_at_to (time range)
    - updated_at_from, updated_at_to (time range)
    - created_by (user filtering)
    - is_deleted (soft delete status)
    """

    code = filters.CharFilter(
        lookup_expr='icontains',
        label='Object Code'
    )
    name = filters.CharFilter(
        lookup_expr='icontains',
        label='Object Name'
    )
    enable_workflow = filters.BooleanFilter(label='Enable Workflow')
    enable_version = filters.BooleanFilter(label='Enable Version')

    class Meta(BaseModelFilter.Meta):
        model = BusinessObject
        fields = [
            'code',
            'name',
            'enable_workflow',
            'enable_version',
        ]


class FieldDefinitionFilter(BaseModelFilter):
    """Field Definition filter."""

    code = filters.CharFilter(
        lookup_expr='icontains',
        label='Field Code'
    )
    name = filters.CharFilter(
        lookup_expr='icontains',
        label='Field Name'
    )
    field_type = filters.ChoiceFilter(
        choices=FieldDefinition.FIELD_TYPE_CHOICES,
        label='Field Type'
    )
    is_required = filters.BooleanFilter(label='Is Required')
    is_system = filters.BooleanFilter(label='Is System')
    show_in_list = filters.BooleanFilter(label='Show in List')

    class Meta(BaseModelFilter.Meta):
        model = FieldDefinition
        fields = [
            'code',
            'name',
            'field_type',
            'is_required',
            'is_system',
            'show_in_list',
        ]


class PageLayoutFilter(BaseModelFilter):
    """Page Layout filter."""

    layout_code = filters.CharFilter(
        lookup_expr='icontains',
        label='Layout Code'
    )
    layout_name = filters.CharFilter(
        lookup_expr='icontains',
        label='Layout Name'
    )
    layout_type = filters.ChoiceFilter(
        choices=PageLayout.LAYOUT_TYPE_CHOICES,
        label='Layout Type'
    )
    is_active = filters.BooleanFilter(label='Is Active')
    is_default = filters.BooleanFilter(label='Is Default')

    class Meta(BaseModelFilter.Meta):
        model = PageLayout
        fields = [
            'layout_code',
            'layout_name',
            'layout_type',
            'is_active',
            'is_default',
        ]


class DynamicDataFilter(BaseModelFilter):
    """Dynamic Data filter."""

    data_no = filters.CharFilter(
        lookup_expr='icontains',
        label='Data Number'
    )
    status = filters.CharFilter(
        lookup_expr='exact',
        label='Status'
    )
    business_object_code = filters.CharFilter(
        field_name='business_object__code',
        lookup_expr='exact',
        label='Business Object Code'
    )

    # Date range filters for workflow timestamps
    submitted_at_from = filters.DateTimeFilter(
        field_name='submitted_at',
        lookup_expr='gte',
        label='Submitted After'
    )
    submitted_at_to = filters.DateTimeFilter(
        field_name='submitted_at',
        lookup_expr='lte',
        label='Submitted Before'
    )
    approved_at_from = filters.DateTimeFilter(
        field_name='approved_at',
        lookup_expr='gte',
        label='Approved After'
    )
    approved_at_to = filters.DateTimeFilter(
        field_name='approved_at',
        lookup_expr='lte',
        label='Approved Before'
    )

    class Meta(BaseModelFilter.Meta):
        model = DynamicData
        fields = [
            'data_no',
            'status',
            'business_object_code',
            'submitted_at_from',
            'submitted_at_to',
            'approved_at_from',
            'approved_at_to',
        ]


class DynamicSubTableDataFilter(BaseModelFilter):
    """Dynamic Sub-Table Data filter."""

    parent_data_no = filters.CharFilter(
        field_name='parent_data__data_no',
        lookup_expr='exact',
        label='Parent Data Number'
    )
    field_definition_code = filters.CharFilter(
        field_name='field_definition__code',
        lookup_expr='exact',
        label='Field Definition Code'
    )
    row_order = filters.NumberFilter(label='Row Order')

    class Meta(BaseModelFilter.Meta):
        model = DynamicSubTableData
        fields = [
            'parent_data_no',
            'field_definition_code',
            'row_order',
        ]
