"""
Filters for Organization models.
"""
import django_filters
from apps.common.filters.base import BaseModelFilter
from apps.organizations.models import Department, UserDepartment


class DepartmentFilter(BaseModelFilter):
    """Filter for Department model."""

    code = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    full_path = django_filters.CharFilter(lookup_expr='icontains')
    full_path_name = django_filters.CharFilter(lookup_expr='icontains')
    leader = django_filters.UUIDFilter(field_name='leader_id')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    level = django_filters.NumberFilter()
    wework_dept_id = django_filters.CharFilter()
    dingtalk_dept_id = django_filters.CharFilter()
    feishu_dept_id = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()
    order = django_filters.OrderingFilter(
        fields=('level', 'order', 'name', 'code')
    )

    class Meta:
        model = Department
        fields = [
            'code', 'name', 'full_path', 'full_path_name',
            'leader', 'parent', 'level',
            'wework_dept_id', 'dingtalk_dept_id', 'feishu_dept_id',
            'is_active', 'order'
        ]


class UserDepartmentFilter(BaseModelFilter):
    """Filter for UserDepartment model."""

    user = django_filters.UUIDFilter(field_name='user_id')
    department = django_filters.UUIDFilter(field_name='department_id')
    is_primary = django_filters.BooleanFilter()
    is_asset_department = django_filters.BooleanFilter()
    is_leader = django_filters.BooleanFilter()
    position = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = UserDepartment
        fields = [
            'user', 'department', 'is_primary', 'is_asset_department',
            'is_leader', 'position'
        ]
