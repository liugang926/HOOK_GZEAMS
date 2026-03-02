from rest_framework import viewsets, mixins, permissions
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.system.models import ActivityLog
from apps.system.activity_log_serializers import ActivityLogSerializer
from apps.common.permissions.base import IsOrganizationMember


class ActivityLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ViewSet for ActivityLog (read-only list).
    Used primarily by the frontend ActivityTimeline component.
    """
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrganizationMember]
    
    def get_queryset(self):
        """Filter logs by content_type_id and object_id query params."""
        queryset = ActivityLog.objects.filter(is_deleted=False)
        
        # In a multi-tenant setup, filter by user org if not superuser
        user = self.request.user
        if not getattr(user, 'is_superuser', False) and getattr(user, 'organization_id', None):
            queryset = queryset.filter(organization=user.organization)
            
        content_type_id = self.request.query_params.get('content_type_id')
        object_code = self.request.query_params.get('object_code')
        object_id = self.request.query_params.get('object_id')
        
        if object_code and object_id:
            from apps.system.services.business_object_service import BusinessObjectService
            try:
                service = BusinessObjectService()
                model_class = service.get_model_class(object_code)
                content_type = ContentType.objects.get_for_model(model_class)
                queryset = queryset.filter(content_type=content_type, object_id=object_id)
            except Exception:
                queryset = queryset.none()
        elif content_type_id and object_id:
            queryset = queryset.filter(
                content_type_id=content_type_id,
                object_id=object_id
            )
            
        return queryset.select_related('actor').order_by('-created_at')
    
    @extend_schema(
        summary="List activity logs for an object",
        description="Get chronological activity logs for a specific object instance.",
        parameters=[
            OpenApiParameter('object_code', OpenApiTypes.STR, description='Target Object Code (e.g. Asset)', required=False),
            OpenApiParameter('content_type_id', OpenApiTypes.INT, description='Target ContentType ID (fallback)', required=False),
            OpenApiParameter('object_id', OpenApiTypes.STR, description='Target Object ID', required=True),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
