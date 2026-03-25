"""
SSO Filters

Filter classes for SSO models.
All filters inherit from BaseModelFilter for consistent filtering behavior.
"""
import django_filters
from django_filters import rest_framework as filters

from apps.common.filters.base import BaseModelFilter
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState, SyncLog


class WeWorkConfigFilter(BaseModelFilter):
    """Filter for WeWorkConfig model."""

    corp_name = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Company name contains'
    )
    corp_id = django_filters.CharFilter(
        lookup_expr='exact',
        help_text='Exact corp ID match'
    )
    is_enabled = django_filters.BooleanFilter(
        help_text='Filter by enabled status'
    )
    sync_department = django_filters.BooleanFilter(
        help_text='Filter by sync department setting'
    )
    sync_user = django_filters.BooleanFilter(
        help_text='Filter by sync user setting'
    )
    auto_create_user = django_filters.BooleanFilter(
        help_text='Filter by auto create user setting'
    )

    class Meta:
        model = WeWorkConfig
        fields = [
            'corp_name',
            'corp_id',
            'is_enabled',
            'sync_department',
            'sync_user',
            'auto_create_user',
            'created_at',
            'updated_at',
        ]


class UserMappingFilter(BaseModelFilter):
    """Filter for UserMapping model."""

    platform = django_filters.ChoiceFilter(
        choices=UserMapping.PLATFORM_CHOICES,
        help_text='Filter by platform type'
    )
    platform_name = django_filters.CharFilter(
        lookup_expr='icontains',
        help_text='Platform name contains'
    )
    platform_userid = django_filters.CharFilter(
        lookup_expr='exact',
        help_text='Exact platform user ID match'
    )
    system_user = django_filters.UUIDFilter(
        field_name='system_user_id',
        help_text='Filter by system user ID'
    )

    class Meta:
        model = UserMapping
        fields = [
            'platform',
            'platform_name',
            'platform_userid',
            'system_user',
            'created_at',
        ]


class OAuthStateFilter(BaseModelFilter):
    """Filter for OAuthState model."""

    platform = django_filters.CharFilter(
        lookup_expr='exact',
        help_text='Filter by platform'
    )
    consumed = django_filters.BooleanFilter(
        help_text='Filter by consumed status'
    )
    expires_at = django_filters.DateTimeFilter(
        help_text='Filter by expiration time'
    )
    expires_at__gte = django_filters.DateTimeFilter(
        field_name='expires_at',
        lookup_expr='gte',
        help_text='Expires at or after'
    )
    expires_at__lte = django_filters.DateTimeFilter(
        field_name='expires_at',
        lookup_expr='lte',
        help_text='Expires at or before'
    )

    class Meta:
        model = OAuthState
        fields = [
            'platform',
            'consumed',
            'expires_at',
            'created_at',
        ]


class SyncLogFilter(BaseModelFilter):
    """Filter for SyncLog model."""

    sync_type = django_filters.ChoiceFilter(
        choices=SyncLog.SyncTypeChoices.choices,
        help_text='Filter by sync type'
    )
    sync_source = django_filters.ChoiceFilter(
        choices=SyncLog.SourceChoices.choices,
        help_text='Filter by sync source'
    )
    status = django_filters.ChoiceFilter(
        choices=SyncLog.StatusChoices.choices,
        help_text='Filter by status'
    )
    started_at = django_filters.DateFromToRangeFilter(
        help_text='Filter by sync time range'
    )
    total_count = django_filters.NumberFilter(
        help_text='Filter by total count'
    )
    total_count_gte = django_filters.NumberFilter(
        field_name='total_count',
        lookup_expr='gte',
        help_text='Total count (minimum)'
    )
    total_count_lte = django_filters.NumberFilter(
        field_name='total_count',
        lookup_expr='lte',
        help_text='Total count (maximum)'
    )
    failed_count_gte = django_filters.NumberFilter(
        field_name='failed_count',
        lookup_expr='gte',
        help_text='Failed count (minimum)'
    )

    class Meta:
        model = SyncLog
        fields = [
            'sync_type',
            'sync_source',
            'status',
            'started_at',
            'total_count',
            'created_at',
            'updated_at',
            'created_by',
            'is_deleted',
        ]
