"""
ViewSets for data mapping template management.

Provides ViewSets for DataMappingTemplate model following BaseModelViewSet pattern.
"""
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.integration.models import DataMappingTemplate
from apps.integration.serializers import DataMappingTemplateSerializer
from apps.integration.filters.base import BaseModelFilter
import django_filters


class DataMappingTemplateFilter(BaseModelFilter):
    """Filter for DataMappingTemplate model."""

    class Meta(BaseModelFilter.Meta):
        model = DataMappingTemplate
        fields = BaseModelFilter.Meta.fields + [
            'system_type',
            'business_type',
            'is_active',
        ]

    system_type = django_filters.CharFilter(lookup_expr='iexact')
    business_type = django_filters.CharFilter(lookup_expr='iexact')
    is_active = django_filters.BooleanFilter()
    template_name = django_filters.CharFilter(lookup_expr='icontains')


class DataMappingTemplateViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for DataMappingTemplate management.

    Provides standard CRUD operations for data mapping templates.
    """

    queryset = DataMappingTemplate.objects.filter(is_deleted=False)
    serializer_class = DataMappingTemplateSerializer
    filterset_class = DataMappingTemplateFilter

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            created_by=self.request.user,
            organization_id=organization_id
        )

    def get_queryset(self):
        """Filter queryset by organization."""
        qs = super().get_queryset()
        user = self.request.user

        # Non-admin users can only see their organization's templates
        if not user.is_superuser and not user.is_staff:
            qs = qs.filter(organization=self.request.organization)

        return qs.select_related('organization')
