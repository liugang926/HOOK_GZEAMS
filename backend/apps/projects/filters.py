"""
Filters for asset project management models.
"""
from django.db.models import Q
from django_filters import rest_framework as filters

from apps.common.filters.base import BaseModelFilter

from .models import AssetProject, ProjectAsset, ProjectMember


class AssetProjectFilter(BaseModelFilter):
    """Filter for project list and search scenarios."""

    project_code = filters.CharFilter(lookup_expr="icontains")
    project_name = filters.CharFilter(lookup_expr="icontains")
    project_type = filters.ChoiceFilter(choices=AssetProject.PROJECT_TYPE_CHOICES)
    status = filters.ChoiceFilter(choices=AssetProject.STATUS_CHOICES)
    department = filters.UUIDFilter(field_name="department_id")
    project_manager = filters.UUIDFilter(field_name="project_manager_id")
    start_date_from = filters.DateFilter(field_name="start_date", lookup_expr="gte")
    start_date_to = filters.DateFilter(field_name="start_date", lookup_expr="lte")
    end_date_from = filters.DateFilter(field_name="end_date", lookup_expr="gte")
    end_date_to = filters.DateFilter(field_name="end_date", lookup_expr="lte")
    planned_budget_from = filters.NumberFilter(field_name="planned_budget", lookup_expr="gte")
    planned_budget_to = filters.NumberFilter(field_name="planned_budget", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")

    class Meta(BaseModelFilter.Meta):
        model = AssetProject
        fields = BaseModelFilter.Meta.fields + [
            "project_code",
            "project_name",
            "project_type",
            "status",
            "department",
            "project_manager",
            "start_date",
            "end_date",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(project_code__icontains=value) |
            Q(project_name__icontains=value) |
            Q(project_alias__icontains=value) |
            Q(project_manager__username__icontains=value) |
            Q(project_manager__first_name__icontains=value) |
            Q(project_manager__last_name__icontains=value) |
            Q(department__name__icontains=value) |
            Q(description__icontains=value)
        )


class ProjectAssetFilter(BaseModelFilter):
    """Filter for project asset allocations."""

    project = filters.UUIDFilter(field_name="project_id")
    asset = filters.UUIDFilter(field_name="asset_id")
    allocation_no = filters.CharFilter(lookup_expr="icontains")
    allocation_type = filters.ChoiceFilter(choices=ProjectAsset.ALLOCATION_TYPE_CHOICES)
    return_status = filters.ChoiceFilter(choices=ProjectAsset.RETURN_STATUS_CHOICES)
    custodian = filters.UUIDFilter(field_name="custodian_id")
    allocated_by = filters.UUIDFilter(field_name="allocated_by_id")
    allocation_date_from = filters.DateFilter(field_name="allocation_date", lookup_expr="gte")
    allocation_date_to = filters.DateFilter(field_name="allocation_date", lookup_expr="lte")
    return_date_from = filters.DateFilter(field_name="return_date", lookup_expr="gte")
    return_date_to = filters.DateFilter(field_name="return_date", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")

    class Meta(BaseModelFilter.Meta):
        model = ProjectAsset
        fields = BaseModelFilter.Meta.fields + [
            "project",
            "asset",
            "allocation_no",
            "allocation_type",
            "return_status",
            "custodian",
            "allocated_by",
            "allocation_date",
            "return_date",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(allocation_no__icontains=value) |
            Q(project__project_code__icontains=value) |
            Q(project__project_name__icontains=value) |
            Q(asset__asset_code__icontains=value) |
            Q(asset__asset_name__icontains=value) |
            Q(custodian__username__icontains=value) |
            Q(allocated_by__username__icontains=value) |
            Q(purpose__icontains=value) |
            Q(usage_location__icontains=value)
        )


class ProjectMemberFilter(BaseModelFilter):
    """Filter for project membership queries."""

    project = filters.UUIDFilter(field_name="project_id")
    user = filters.UUIDFilter(field_name="user_id")
    role = filters.ChoiceFilter(choices=ProjectMember.ROLE_CHOICES)
    is_primary = filters.BooleanFilter()
    is_active = filters.BooleanFilter()
    join_date_from = filters.DateFilter(field_name="join_date", lookup_expr="gte")
    join_date_to = filters.DateFilter(field_name="join_date", lookup_expr="lte")
    leave_date_from = filters.DateFilter(field_name="leave_date", lookup_expr="gte")
    leave_date_to = filters.DateFilter(field_name="leave_date", lookup_expr="lte")
    search = filters.CharFilter(method="filter_search")

    class Meta(BaseModelFilter.Meta):
        model = ProjectMember
        fields = BaseModelFilter.Meta.fields + [
            "project",
            "user",
            "role",
            "is_primary",
            "is_active",
            "join_date",
            "leave_date",
        ]

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(project__project_code__icontains=value) |
            Q(project__project_name__icontains=value) |
            Q(user__username__icontains=value) |
            Q(user__first_name__icontains=value) |
            Q(user__last_name__icontains=value) |
            Q(responsibilities__icontains=value)
        )
