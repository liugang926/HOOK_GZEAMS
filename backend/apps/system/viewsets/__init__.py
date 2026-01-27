"""
ViewSets for the metadata-driven low-code engine.

All ViewSets inherit from BaseModelViewSetWithBatch which provides:
- Organization isolation (auto-filter by current organization)
- Soft delete handling (auto-filter out deleted records)
- Audit field auto-setting (created_by, updated_at)
- Batch operations: /batch-delete/, /batch-restore/, /batch-update/
- Deleted records management: /deleted/, /{id}/restore/
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.request import Request
from django.utils import timezone
from django.db.models import Q
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    LayoutHistory,
    DynamicData,
    DynamicSubTableData,
    UserColumnPreference,
    TabConfig,
)
from apps.system.serializers import (
    BusinessObjectSerializer,
    BusinessObjectDetailSerializer,
    FieldDefinitionSerializer,
    FieldDefinitionDetailSerializer,
    PageLayoutSerializer,
    PageLayoutDetailSerializer,
    LayoutHistorySerializer,
    DynamicDataSerializer,
    DynamicDataDetailSerializer,
    DynamicDataCreateSerializer,
    DynamicDataUpdateSerializer,
    DynamicSubTableDataSerializer,
    DynamicSubTableDataCreateSerializer,
    DynamicSubTableDataUpdateSerializer,
    UserColumnPreferenceSerializer,
    UserColumnPreferenceListSerializer,
    UserColumnPreferenceUpsertSerializer,
    TabConfigSerializer,
    TabConfigListSerializer,
)
from apps.system.filters import (
    BusinessObjectFilter,
    FieldDefinitionFilter,
    PageLayoutFilter,
    DynamicDataFilter,
    DynamicSubTableDataFilter,
)


class BusinessObjectViewSet(BaseModelViewSetWithBatch):
    """
    Business Object ViewSet for hybrid architecture.

    Handles both hardcoded Django models and low-code custom objects.
    Provides unified API for the metadata engine.
    """

    queryset = BusinessObject.objects.filter(is_deleted=False)
    serializer_class = BusinessObjectSerializer
    filterset_class = BusinessObjectFilter
    search_fields = ['code', 'name', 'name_en']
    ordering_fields = ['code', 'name', 'created_at']
    ordering = ['code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return BusinessObjectDetailSerializer
        if self.action == 'list':
            return BusinessObjectSerializer
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
        from apps.system.services.business_object_service import BusinessObjectService

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

    def retrieve(self, request, *args, **kwargs):
        """Get single business object with full details."""
        instance = self.get_object()
        serializer = BusinessObjectDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-code/(?P<code>[^/]+)')
    def by_code(self, request, code=None):
        """Get business object by code."""
        try:
            instance = BusinessObject.objects.get(code=code, is_deleted=False)
            serializer = BusinessObjectDetailSerializer(instance)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

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
        from apps.system.services.business_object_service import BusinessObjectService

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
        from apps.system.services.business_object_service import BusinessObjectService

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
        from apps.system.services.business_object_service import BusinessObjectService

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
        from apps.system.services.business_object_service import BusinessObjectService

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
        from apps.system.services.business_object_service import BusinessObjectService

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


class FieldDefinitionViewSet(BaseModelViewSetWithBatch):
    """Field Definition ViewSet."""

    queryset = FieldDefinition.objects.filter(is_deleted=False)
    serializer_class = FieldDefinitionSerializer
    filterset_class = FieldDefinitionFilter
    search_fields = ['code', 'name']
    ordering_fields = ['sort_order', 'created_at', 'code']
    ordering = ['sort_order', 'code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'list']:
            return FieldDefinitionDetailSerializer
        return FieldDefinitionSerializer

    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/]+)')
    def by_object(self, request, object_code=None):
        """Get field definitions for a specific business object."""
        try:
            business_object = BusinessObject.objects.get(
                code=object_code,
                is_deleted=False
            )
            fields = business_object.field_definitions.all().order_by('sort_order')
            serializer = FieldDefinitionDetailSerializer(fields, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{object_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )


class PageLayoutViewSet(BaseModelViewSetWithBatch):
    """
    Page Layout ViewSet.

    Handles layout configuration management with version control.
    Supports custom layouts with priority over default layouts.
    """

    queryset = PageLayout.objects.filter(is_deleted=False, is_active=True)
    serializer_class = PageLayoutSerializer
    filterset_class = PageLayoutFilter
    search_fields = ['layout_code', 'layout_name', 'description']
    ordering_fields = ['layout_code', 'created_at', 'version']
    ordering = ['layout_code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'history']:
            return PageLayoutDetailSerializer
        return PageLayoutSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get single layout with full details."""
        instance = self.get_object()
        serializer = PageLayoutDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/]+)')
    def by_object(self, request, object_code=None):
        """
        Get page layouts for a specific business object.

        Returns active custom layouts first (priority), then default layouts.
        Also respects organization isolation.
        """
        try:
            # Get business object - use all_objects to bypass org filtering
            # This allows looking up global business objects (organization=None)
            business_object = BusinessObject.all_objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get org_id from request context
            org_id = getattr(request, 'organization_id', None)

            # Query layouts directly with organization filtering
            # Use all_objects to bypass org filtering, then manually apply org filter
            # Custom layouts (non-default) have priority
            custom_layouts_qs = PageLayout.all_objects.filter(
                business_object=business_object,
                is_active=True,
                is_default=False,
                is_deleted=False
            ).order_by('-created_at')

            # Apply organization filter if org_id is available
            if org_id:
                custom_layouts_qs = custom_layouts_qs.filter(organization_id=org_id)

            custom_layouts = list(custom_layouts_qs)

            # Default layouts (as fallback)
            # Include both org-specific (organization_id=org_id) AND global defaults (organization__isnull=True)
            # Use all_objects to bypass org filtering, then manually apply org filter
            default_layouts_qs = PageLayout.all_objects.filter(
                business_object=business_object,
                is_active=True,
                is_default=True,
                is_deleted=False
            )

            if org_id:
                # For org context: show org-specific defaults OR global defaults (organization=None)
                # This allows global default layouts to be available to all organizations
                default_layouts_qs = default_layouts_qs.filter(
                    Q(organization_id=org_id) | Q(organization__isnull=True)
                )

            default_layouts = list(default_layouts_qs)

            layouts = custom_layouts + default_layouts
            serializer = PageLayoutSerializer(layouts, many=True)

            return Response({
                'success': True,
                'data': serializer.data
            })
        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{object_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/]+)/(?P<layout_type>[^/]+)')
    def by_object_and_type(self, request, object_code=None, layout_type=None):
        """
        Get page layout for a specific business object and type.

        Priority: Custom layout > Default layout
        Also respects organization isolation.
        """
        try:
            # Get business object - use all_objects to bypass org filtering
            # This allows looking up global business objects (organization=None)
            business_object = BusinessObject.all_objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get org_id from request context
            org_id = getattr(request, 'organization_id', None)

            # Build base query for layouts
            base_filters = {
                'business_object': business_object,
                'layout_type': layout_type,
                'is_active': True,
                'is_deleted': False
            }

            # Try custom layout first (priority)
            custom_layouts_qs = PageLayout.objects.filter(
                **base_filters,
                is_default=False
            )

            if org_id:
                custom_layouts_qs = custom_layouts_qs.filter(organization_id=org_id)

            layout = custom_layouts_qs.first()

            # Fall back to default layout
            if not layout:
                default_layouts_qs = PageLayout.objects.filter(
                    **base_filters,
                    is_default=True
                )

                if org_id:
                    # For org context: show org-specific defaults OR global defaults (organization=None)
                    # This allows global default layouts to be available to all organizations
                    default_layouts_qs = default_layouts_qs.filter(
                        Q(organization_id=org_id) | Q(organization__isnull=True)
                    )

                layout = default_layouts_qs.first()

            if not layout:
                return BaseResponse.error(
                    code='NOT_FOUND',
                    message=f'No {layout_type} layout found for "{object_code}".',
                    http_status=status.HTTP_404_NOT_FOUND
                )

            serializer = PageLayoutSerializer(layout)
            return Response({
                'success': True,
                'data': serializer.data,
                'is_default': layout.is_default
            })
        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{object_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        """
        Publish the layout.

        Creates a new version and saves history snapshot.
        Marks as published and sets as default if requested.
        """
        instance = self.get_object()

        # Check if set as default
        set_as_default = request.data.get('set_as_default', False)
        change_summary = request.data.get('change_summary', '')

        try:
            # Unset other defaults if setting this as default
            if set_as_default:
                PageLayout.objects.filter(
                    business_object=instance.business_object,
                    layout_type=instance.layout_type,
                    is_default=True
                ).update(is_default=False)
                instance.is_default = True

            # Publish the layout (creates version and history)
            instance.publish(request.user)

            # Add change summary to history
            if change_summary:
                latest_history = instance.histories.first()
                if latest_history:
                    latest_history.change_summary = change_summary
                    latest_history.save()

            serializer = PageLayoutDetailSerializer(instance)
            return Response({
                'success': True,
                'data': serializer.data,
                'message': f'Layout published successfully as version {instance.version}.'
            })
        except Exception as e:
            return BaseResponse.error(
                code='PUBLISH_ERROR',
                message=str(e),
                http_status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """
        Get version history for this layout.

        Returns all history entries with config snapshots.
        """
        instance = self.get_object()
        histories = instance.histories.all().order_by('-created_at')
        serializer = LayoutHistorySerializer(histories, many=True)

        return Response({
            'success': True,
            'data': serializer.data,
            'count': histories.count()
        })

    @action(detail=True, methods=['post'], url_path='rollback/(?P<version>[^/]+)')
    def rollback(self, request, pk=None, version=None):
        """
        Rollback layout to a specific version.

        Creates a new version with the rolled-back config.
        """
        instance = self.get_object()

        # Find the history entry
        try:
            history_entry = instance.histories.get(version=version)
        except LayoutHistory.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Version {version} not found in history.',
                http_status=status.HTTP_404_NOT_FOUND
            )

        # Rollback by restoring the config
        old_config = instance.layout_config
        instance.layout_config = history_entry.config_snapshot
        instance.status = 'draft'
        instance.parent_version = version
        instance.save()

        # Create rollback history entry
        LayoutHistory.objects.create(
            layout=instance,
            version=f'{version}-rollback-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            config_snapshot=instance.layout_config,
            published_by=request.user,
            action='rollback',
            change_summary=f'Rollback from version {version}'
        )

        serializer = PageLayoutDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': f'Rolled back to version {version}. Please review and publish.'
        })

    @action(detail=True, methods=['post'], url_path='set-default')
    def set_default(self, request, pk=None):
        """
        Set this layout as the default for its type.

        Unsets other default layouts of the same type.
        """
        instance = self.get_object()

        # Unset other defaults
        PageLayout.objects.filter(
            business_object=instance.business_object,
            layout_type=instance.layout_type,
            is_default=True
        ).exclude(id=instance.id).update(is_default=False)

        # Set this as default
        instance.is_default = True
        instance.save()

        serializer = PageLayoutDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': f'{instance.layout_name} is now the default {instance.layout_type} layout.'
        })

    @action(detail=True, methods=['post'], url_path='duplicate')
    def duplicate(self, request, pk=None):
        """
        Duplicate this layout as a new custom layout.

        Creates a copy with modified name/code.
        """
        instance = self.get_object()

        # Create new layout code
        base_code = instance.layout_code.rstrip('_custom').rstrip('_default')
        new_code = f'{base_code}_custom_{int(timezone.now().timestamp())}'

        # Create duplicate
        new_layout = PageLayout.objects.create(
            business_object=instance.business_object,
            layout_code=new_code,
            layout_name=f'{instance.layout_name} (Copy)',
            layout_type=instance.layout_type,
            description=f'Copy of {instance.layout_name}',
            layout_config=instance.layout_config,
            status='draft',
            version='1.0.0',
            is_default=False,
            is_active=True,
            created_by=request.user
        )

        serializer = PageLayoutDetailSerializer(new_layout)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Layout duplicated successfully.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='default/(?P<object_code>[^/]+)/(?P<layout_type>[^/]+)')
    def get_default(self, request, object_code=None, layout_type=None):
        """
        Get the default layout for a business object and type.

        Used as fallback when no custom layout exists.
        """
        try:
            business_object = BusinessObject.objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get org_id from request context
            org_id = getattr(request, 'organization_id', None)

            # Query for default layouts, include both org-specific and global defaults
            layout_qs = PageLayout.objects.filter(
                business_object=business_object,
                layout_type=layout_type,
                is_active=True,
                is_default=True,
                is_deleted=False
            )

            if org_id:
                # For org context: show org-specific defaults OR global defaults (organization=None)
                layout_qs = layout_qs.filter(
                    Q(organization_id=org_id) | Q(organization__isnull=True)
                )

            layout = layout_qs.first()

            if not layout:
                # Return default template config
                from apps.system.validators import get_default_layout_config
                return Response({
                    'success': True,
                    'data': {
                        'is_template': True,
                        'layout_type': layout_type,
                        'layout_config': get_default_layout_config(layout_type)
                    },
                    'message': 'No default layout found, using template.'
                })

            serializer = PageLayoutSerializer(layout)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{object_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )


class DynamicDataViewSet(BaseModelViewSetWithBatch):
    """
    Dynamic Data ViewSet.

    Handles CRUD operations for dynamic data records.
    Uses DynamicDataService for business logic.
    """

    queryset = DynamicData.objects.filter(is_deleted=False)
    serializer_class = DynamicDataSerializer
    filterset_class = DynamicDataFilter
    search_fields = ['data_no']
    ordering_fields = ['created_at', 'data_no', '-created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return DynamicDataDetailSerializer
        if self.action == 'create':
            return DynamicDataCreateSerializer
        if self.action in ['update', 'partial_update']:
            return DynamicDataUpdateSerializer
        return DynamicDataSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get single dynamic data record with full details."""
        instance = self.get_object()
        serializer = DynamicDataDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """Create dynamic data using service layer."""
        # Import here to avoid circular import
        from apps.system.services.dynamic_data_service import DynamicDataService

        serializer = DynamicDataCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        business_object_code = serializer.validated_data['business_object_code']
        service = DynamicDataService(business_object_code)

        try:
            result = service.create(
                serializer.validated_data.get('dynamic_fields', {}),
                status=serializer.validated_data.get('status', 'draft')
            )

            return Response({
                'success': True,
                'data': result,
                'message': 'Dynamic data created successfully.'
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(e),
                http_status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Update dynamic data using service layer."""
        from apps.system.services.dynamic_data_service import DynamicDataService

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        serializer = DynamicDataUpdateSerializer(
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)

        service = DynamicDataService(instance.business_object.code)

        try:
            result = service.update(
                instance.id,
                serializer.validated_data.get('dynamic_fields', {})
            )

            # Update status if provided
            if 'status' in serializer.validated_data:
                instance.status = serializer.validated_data['status']
                instance.save()

            # Get updated record
            updated = DynamicDataDetailSerializer(instance).data

            return Response({
                'success': True,
                'data': updated,
                'message': 'Dynamic data updated successfully.'
            })

        except ValueError as e:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(e),
                http_status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/]+)')
    def by_object(self, request, object_code=None):
        """Query dynamic data for a specific business object."""
        from apps.system.services.dynamic_data_service import DynamicDataService

        service = DynamicDataService(object_code)

        try:
            # Get query parameters
            filters = request.GET.get('filters')
            search = request.GET.get('search')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            sort = request.GET.get('sort', '-created_at')

            # Parse filters if provided as JSON string
            if filters:
                import json
                filters = json.loads(filters)

            result = service.query(
                filters=filters,
                search=search,
                page=page,
                page_size=page_size,
                sort=sort
            )

            return Response({
                'success': True,
                'data': result
            })

        except ValueError as e:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(e),
                http_status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        """Submit dynamic data for approval."""
        instance = self.get_object()
        instance.status = 'submitted'
        instance.submitted_at = timezone.now()
        instance.save()

        serializer = DynamicDataDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Data submitted successfully.'
        })

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """Approve dynamic data."""
        instance = self.get_object()
        instance.status = 'approved'
        instance.approved_at = timezone.now()
        instance.approved_by = request.user
        instance.save()

        serializer = DynamicDataDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Data approved successfully.'
        })

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        """Reject dynamic data."""
        instance = self.get_object()
        instance.status = 'rejected'
        instance.save()

        serializer = DynamicDataDetailSerializer(instance)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Data rejected successfully.'
        })


class DynamicSubTableDataViewSet(BaseModelViewSetWithBatch):
    """Dynamic Sub-Table Data ViewSet."""

    queryset = DynamicSubTableData.objects.filter(is_deleted=False)
    serializer_class = DynamicSubTableDataSerializer
    filterset_class = DynamicSubTableDataFilter
    ordering_fields = ['row_order', 'created_at']
    ordering = ['parent_data', 'row_order']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return DynamicSubTableDataCreateSerializer
        if self.action in ['update', 'partial_update']:
            return DynamicSubTableDataUpdateSerializer
        return DynamicSubTableDataSerializer

    @action(detail=False, methods=['get'], url_path='by-parent/(?P<parent_id>[^/]+)')
    def by_parent(self, request, parent_id=None):
        """Get sub-table rows for a specific parent data record."""
        try:
            parent = DynamicData.objects.get(id=parent_id, is_deleted=False)
            rows = parent.sub_table_rows.all().order_by('row_order')
            serializer = DynamicSubTableDataSerializer(rows, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except DynamicData.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Parent data "{parent_id}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False,
        methods=['post'],
        url_path='by-parent/(?P<parent_id>[^/]+)/field/(?P<field_code>[^/]+)'
    )
    def add_row(self, request, parent_id=None, field_code=None):
        """Add a new row to a sub-table."""
        try:
            parent = DynamicData.objects.get(id=parent_id, is_deleted=False)
            field_def = parent.business_object.field_definitions.get(
                code=field_code,
                field_type='sub_table'
            )

            serializer = DynamicSubTableDataCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Get next row order
            max_order = parent.sub_table_rows.filter(
                field_definition=field_def
            ).order_by('-row_order').first()
            row_order = (max_order.row_order + 1) if max_order else 0

            row = DynamicSubTableData.objects.create(
                parent_data=parent,
                field_definition=field_def,
                row_order=serializer.validated_data.get('row_order', row_order),
                row_data=serializer.validated_data.get('row_data', {}),
                created_by=request.user
            )

            result_serializer = DynamicSubTableDataSerializer(row)
            return Response({
                'success': True,
                'data': result_serializer.data,
                'message': 'Row added successfully.'
            }, status=status.HTTP_201_CREATED)

        except DynamicData.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Parent data "{parent_id}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )
        except FieldDefinition.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Sub-table field "{field_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )


# ============================================================================
# Column Preference and Tab Configuration ViewSets
# ============================================================================

from apps.system.services.column_config_service import ColumnConfigService


class UserColumnPreferenceViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for User Column Preferences.

    Provides endpoints for managing user-specific column display configurations.
    Automatically filters to show only the current user's preferences.
    """

    queryset = UserColumnPreference.objects.filter(is_deleted=False)
    serializer_class = UserColumnPreferenceSerializer
    search_fields = ['object_code', 'config_name']
    ordering_fields = ['object_code', 'created_at']
    ordering = ['object_code']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return UserColumnPreferenceListSerializer
        return UserColumnPreferenceSerializer

    def get_queryset(self):
        """
        Filter to show only current user's preferences.

        Users can only see and manage their own column preferences.
        """
        queryset = super().get_queryset()
        # Handle both DRF Request and plain WSGIRequest (for tests)
        if hasattr(self.request, 'user'):
            user = self.request.user
            if user and user.is_authenticated:
                queryset = queryset.filter(user=user)
        return queryset

    def perform_create(self, serializer):
        """Set user from request when creating preference."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='upsert')
    def upsert(self, request):
        """
        Upsert column configuration for the current user.

        Request body:
        {
            "object_code": "asset",
            "column_config": {
                "columns": [...],
                "columnOrder": [...]
            }
        }

        Creates a new preference or updates existing one.
        Clears cache after saving.
        """
        # Ensure request is a DRF Request (for direct calls in tests)
        if not isinstance(request, Request):
            request = Request(request)

        from apps.system.serializers import UserColumnPreferenceUpsertSerializer

        serializer = UserColumnPreferenceUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        object_code = request.data.get('object_code')
        column_config = serializer.validated_data['column_config']

        # Use service to save
        pref = ColumnConfigService.save_user_config(
            request.user,
            object_code,
            column_config
        )

        return Response({
            'success': True,
            'data': UserColumnPreferenceSerializer(pref).data,
            'message': 'Column configuration saved successfully.'
        })

    @action(detail=False, methods=['post'], url_path='reset')
    def reset(self, request):
        """
        Reset column configuration to default.

        Request body:
        {
            "object_code": "asset"
        }

        Deletes the user's preference, causing the system to
        fall back to the default layout configuration.
        """
        # Ensure request is a DRF Request (for direct calls in tests)
        if not isinstance(request, Request):
            request = Request(request)

        object_code = request.data.get('object_code')

        if not object_code:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'object_code is required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        result = ColumnConfigService.reset_user_config(
            request.user,
            object_code
        )

        if result:
            return Response({
                'success': True,
                'message': f'Column configuration reset to default for "{object_code}".'
            })
        else:
            return Response({
                'success': False,
                'error': {
                    'code': 'SERVER_ERROR',
                    'message': 'Failed to reset configuration'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='for-object/(?P<object_code>[^/]+)')
    def for_object(self, request, object_code=None):
        """
        Get merged column configuration for a business object.

        Returns the merged configuration (user + default) for the
        specified business object. This is the primary endpoint
        that the frontend should use to get column configurations.

        Response format:
        {
            "success": true,
            "data": {
                "columns": [...],
                "columnOrder": [...],
                "source": "user" | "default"
            }
        }
        """
        config = ColumnConfigService.get_column_config(request.user, object_code)

        return Response({
            'success': True,
            'data': config
        })


class TabConfigViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Tab Configurations.

    Handles tab layout settings for forms and detail pages.
    """

    queryset = TabConfig.objects.filter(is_deleted=False, is_active=True)
    serializer_class = TabConfigSerializer
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return TabConfigListSerializer
        return TabConfigSerializer

    @action(detail=False, methods=['get'], url_path='by-object/(?P<object_code>[^/]+)')
    def by_object(self, request, object_code=None):
        """
        Get tab configurations for a specific business object.

        Returns all active tab configurations for the specified
        business object, filtered by organization.

        Response format:
        {
            "success": true,
            "data": [
                {
                    "id": "...",
                    "name": "form_tabs",
                    "position": "top",
                    "tabs_config": [...]
                }
            ]
        }
        """
        try:
            # Get business object - use all_objects to include global
            business_object = BusinessObject.all_objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get org_id from request context
            org_id = getattr(request, 'organization_id', None)

            # Query tab configs
            configs_qs = TabConfig.objects.filter(
                business_object=business_object,
                is_active=True,
                is_deleted=False
            )

            if org_id:
                # Filter by organization
                configs_qs = configs_qs.filter(
                    Q(organization_id=org_id) | Q(organization__isnull=True)
                )

            configs = configs_qs.order_by('name')
            serializer = TabConfigSerializer(configs, many=True)

            return Response({
                'success': True,
                'data': serializer.data
            })

        except BusinessObject.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message=f'Business object "{object_code}" not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )
