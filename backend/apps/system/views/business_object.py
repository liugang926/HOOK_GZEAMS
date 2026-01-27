"""
API ViewSets for Business Objects in the hybrid architecture.

Provides unified API for both hardcoded Django models and low-code
custom business objects.
"""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.system.models import (
    BusinessObject,
    ModelFieldDefinition,
    FieldDefinition,
)
from apps.system.services.business_object_service import BusinessObjectService
from apps.system.serializers.business_object import (
    BusinessObjectSerializer,
    BusinessObjectListSerializer,
    ModelFieldDefinitionSerializer,
)


class BusinessObjectViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Business Objects.

    Handles both hardcoded Django models and low-code custom objects.
    Provides unified API for the metadata engine.
    """

    queryset = BusinessObject.objects.filter(is_deleted=False)
    serializer_class = BusinessObjectSerializer

    def get_serializer_class(self):
        """Use list serializer for list actions."""
        if self.action == 'list':
            return BusinessObjectListSerializer
        return BusinessObjectSerializer

    def list(self, request, *args, **kwargs):
        """
        List all business objects, grouped by type.

        Response format:
        {
            "success": true,
            "data": {
                "hardcoded": [...],
                "custom": [...]
            }
        }
        """
        service = BusinessObjectService()
        org_id = getattr(request, 'organization_id', None)

        data = service.get_all_objects(
            organization_id=org_id,
            include_hardcoded=True,
            include_custom=True
        )

        return Response({
            'success': True,
            'data': data
        })

    def create(self, request, *args, **kwargs):
        """
        Create a new business object.

        Hardcoded objects cannot be created through API.
        """
        data = request.data

        # Prevent creating hardcoded objects via API
        if data.get('is_hardcoded'):
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Hardcoded objects cannot be created via API'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a business object.

        Hardcoded objects cannot be deleted through API.
        """
        instance = self.get_object()

        if instance.is_hardcoded:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Hardcoded objects cannot be deleted'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='reference-options')
    def reference_options(self, request):
        """
        Get objects available for reference field selection.

        Returns a flat list with type indicator for UI display.

        Response format:
        {
            "success": true,
            "data": [
                {"value": "Asset", "label": "资产", "type": "hardcoded", "icon": "box"},
                {"value": "CustomRequest", "label": "自定义申请", "type": "custom", "icon": "document"}
            ]
        }
        """
        service = BusinessObjectService()
        org_id = getattr(request, 'organization_id', None)

        data = service.get_reference_options(organization_id=org_id)

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'], url_path='fields')
    def fields(self, request):
        """
        Get field definitions for a specific business object.

        Query parameters:
            object_code: Business object code (required)

        Response format:
        {
            "success": true,
            "data": {
                "object_code": "Asset",
                "object_name": "资产",
                "is_hardcoded": true,
                "fields": [...]
            }
        }
        """
        object_code = request.query_params.get('object_code')

        if not object_code:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'object_code parameter is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        service = BusinessObjectService()
        data = service.get_object_fields(object_code)

        if 'error' in data:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': data['error']
                }
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'], url_path='hardcoded')
    def hardcoded(self, request):
        """
        Get list of all hardcoded business objects.

        Response format:
        {
            "success": true,
            "data": [
                {"code": "Asset", "name": "资产", "model_path": "apps.assets.models.Asset", ...}
            ]
        }
        """
        service = BusinessObjectService()
        data = service._get_hardcoded_objects()

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'], url_path='custom')
    def custom(self, request):
        """
        Get list of all custom low-code business objects.

        Query parameters:
            organization_id: Filter by organization (optional)

        Response format:
        {
            "success": true,
            "data": [
                {"code": "CustomRequest", "name": "自定义申请", "table_name": "dynamic_data_customrequest", ...}
            ]
        }
        """
        service = BusinessObjectService()
        org_id = getattr(request, 'organization_id', None)

        queryset = BusinessObject.objects.filter(
            is_deleted=False,
            is_hardcoded=False
        )
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        data = service._format_custom_objects(queryset)

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=True, methods=['get'], url_path='sync-fields')
    def sync_fields(self, request, pk=None):
        """
        Sync model fields for a hardcoded object.

        This action is only valid for hardcoded objects.
        It creates/updates ModelFieldDefinition entries.

        Response format:
        {
            "success": true,
            "data": {
                "synced_count": 25
            }
        }
        """
        instance = self.get_object()

        if not instance.is_hardcoded:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_OPERATION',
                    'message': 'Field sync is only available for hardcoded objects'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        service = BusinessObjectService()
        try:
            count = service.sync_model_fields(
                instance.code,
                organization_id=getattr(request, 'organization_id', None)
            )
            return Response({
                'success': True,
                'data': {
                    'synced_count': count,
                    'message': f'Synced {count} fields for {instance.name}'
                }
            })
        except ValueError as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'SYNC_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class ModelFieldDefinitionViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Model Field Definitions.

    These are read-only fields exposed from hardcoded Django models.
    """

    queryset = ModelFieldDefinition.objects.filter(is_deleted=False)
    serializer_class = ModelFieldDefinitionSerializer

    def get_queryset(self):
        """Filter by business_object if provided."""
        queryset = super().get_queryset()
        business_object_code = self.request.query_params.get('business_object')

        if business_object_code:
            queryset = queryset.filter(business_object__code=business_object_code)

        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create is disabled for model field definitions.

        Fields are auto-generated from Django model metadata.
        """
        return Response({
            'success': False,
            'error': {
                'code': 'READONLY',
                'message': 'Model field definitions are auto-generated from Django models. Use sync-fields action instead.'
            }
        }, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, *args, **kwargs):
        """
        Update is restricted for model field definitions.

        Only display-related fields can be modified.
        """
        partial = kwargs.get('partial', False)
        instance = self.get_object()

        # Only allow updating display-related fields
        allowed_fields = {
            'display_name', 'display_name_en',
            'show_in_list', 'show_in_detail', 'show_in_form',
            'sort_order'
        }

        for field in request.data:
            if field not in allowed_fields:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'READONLY_FIELD',
                        'message': f'Field "{field}" is read-only'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete is disabled for model field definitions.

        Fields are derived from Django models.
        """
        return Response({
            'success': False,
            'error': {
                'code': 'READONLY',
                'message': 'Model field definitions cannot be deleted'
            }
        }, status=status.HTTP_403_FORBIDDEN)
