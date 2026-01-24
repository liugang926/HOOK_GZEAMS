from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import Software, SoftwareLicense, LicenseAllocation


class SoftwareFilter(BaseModelFilter):
    """Software Filter"""

    software_type = filters.CharFilter(field_name='software_type')
    vendor = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = Software
        fields = BaseModelFilter.Meta.fields + [
            'software_type', 'vendor', 'is_active',
        ]


class SoftwareLicenseFilter(BaseModelFilter):
    """Software License Filter"""

    status = filters.CharFilter()
    software = filters.CharFilter(field_name='software__code')
    expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')

    def filter_expiring_soon(self, queryset, name, value):
        """Filter licenses expiring within 30 days."""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            delta = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                expiry_date__lte=delta,
                expiry_date__gte=timezone.now().date(),
                status='active'
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = SoftwareLicense
        fields = BaseModelFilter.Meta.fields + [
            'software', 'status', 'expiry_date',
        ]


class LicenseAllocationFilter(BaseModelFilter):
    """License Allocation Filter"""

    is_active = filters.BooleanFilter()
    software = filters.CharFilter(field_name='license__software__code')

    class Meta(BaseModelFilter.Meta):
        model = LicenseAllocation
        fields = BaseModelFilter.Meta.fields + [
            'license', 'asset', 'is_active',
        ]


__all__ = [
    'SoftwareFilter',
    'SoftwareLicenseFilter',
    'LicenseAllocationFilter',
]
