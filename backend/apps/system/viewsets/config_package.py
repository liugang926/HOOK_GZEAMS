"""
Configuration Package ViewSets - API endpoints for config lifecycle management.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
import json

from apps.common.viewsets import BaseModelViewSetWithBatch
from apps.system.models import ConfigPackage, ConfigImportLog
from apps.system.serializers import (
    ConfigPackageSerializer,
    ConfigPackageExportSerializer,
    ConfigPackageImportSerializer,
    ConfigImportLogSerializer,
    ConfigDiffSerializer,
)
from apps.system.services.config_package_service import ConfigPackageService


class ConfigPackageViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Configuration Packages.
    
    Provides CRUD operations plus:
    - export: Create a new package from business objects
    - import: Import a package into the system
    - diff: Compare two packages
    - download: Download package as JSON file
    """
    
    queryset = ConfigPackage.objects.select_related('exported_by').all()
    serializer_class = ConfigPackageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['package_type', 'is_valid', 'source_environment']
    search_fields = ['name', 'description']
    ordering = ['-exported_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        org = getattr(self.request, 'current_organization', None)
        if org:
            queryset = queryset.filter(organization=org)
        return queryset

    def get_service(self):
        """Get ConfigPackageService instance."""
        org = getattr(self.request, 'current_organization', None)
        return ConfigPackageService(organization=org, user=self.request.user)

    @action(detail=False, methods=['post'], url_path='export')
    def export_package(self, request):
        """
        Export business objects to a new configuration package.
        
        Request body:
        {
            "name": "My Config Package",
            "version": "1.0.0",
            "description": "Description",
            "object_codes": ["Asset", "AssetCategory"],
            "package_type": "full"
        }
        """
        serializer = ConfigPackageExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = self.get_service()
        result = service.export_package(
            name=serializer.validated_data['name'],
            version=serializer.validated_data['version'],
            object_codes=serializer.validated_data['object_codes'],
            description=serializer.validated_data.get('description', ''),
            package_type=serializer.validated_data.get('package_type', 'full')
        )
        
        return Response({
            'package': ConfigPackageSerializer(result.package).data,
            'summary': {
                'objects': result.object_count,
                'fields': result.field_count,
                'layouts': result.layout_count,
                'rules': result.rule_count,
            }
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='import')
    def import_package(self, request):
        """
        Import a configuration package.
        
        Request body:
        {
            "package_id": "uuid" or "config_data": {...},
            "strategy": "merge",
            "target_environment": "production"
        }
        """
        serializer = ConfigPackageImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get or create package
        package_id = serializer.validated_data.get('package_id')
        config_data = serializer.validated_data.get('config_data')
        
        if package_id:
            try:
                package = ConfigPackage.objects.get(id=package_id)
            except ConfigPackage.DoesNotExist:
                return Response(
                    {'error': 'Package not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif config_data:
            # Create package from uploaded data
            org = getattr(request, 'current_organization', None)
            package = ConfigPackage.objects.create(
                organization=org,
                name=config_data.get('name', 'Imported Package'),
                version=config_data.get('version', '1.0.0'),
                package_type='full',
                included_objects=config_data.get('included_objects', []),
                config_data=config_data,
                exported_by=request.user,
                source_environment='import'
            )
        else:
            return Response(
                {'error': 'Either package_id or config_data is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        service = self.get_service()
        result = service.import_package(
            package=package,
            strategy=serializer.validated_data.get('strategy', 'merge'),
            target_environment=serializer.validated_data.get('target_environment', '')
        )
        
        return Response({
            'success': result.success,
            'import_log': ConfigImportLogSerializer(result.import_log).data,
            'summary': {
                'created': result.created,
                'updated': result.updated,
                'skipped': result.skipped,
                'failed': result.failed,
            },
            'errors': result.errors
        })

    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """
        Download package as JSON file.
        """
        package = self.get_object()
        
        response = JsonResponse(package.config_data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{package.name}_v{package.version}.json"'
        return response

    @action(detail=True, methods=['post'], url_path='diff')
    def diff_packages(self, request, pk=None):
        """
        Compare this package with another package.
        
        Request body:
        {
            "compare_with": "uuid of other package"
        }
        """
        package1 = self.get_object()
        compare_with = request.data.get('compare_with')
        
        if not compare_with:
            return Response(
                {'error': 'compare_with package ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            package2 = ConfigPackage.objects.get(id=compare_with)
        except ConfigPackage.DoesNotExist:
            return Response(
                {'error': 'Comparison package not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        service = self.get_service()
        result = service.diff_packages(package1, package2)
        
        return Response({
            'items': [
                {
                    'object_code': item.object_code,
                    'item_type': item.item_type,
                    'item_key': item.item_key,
                    'change_type': item.change_type,
                    'old_value': item.old_value,
                    'new_value': item.new_value,
                }
                for item in result.items
            ],
            'summary': result.summary
        })


class ConfigImportLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Configuration Import Logs.
    """
    
    queryset = ConfigImportLog.objects.select_related('package', 'imported_by').all()
    serializer_class = ConfigImportLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['package', 'status', 'import_strategy']
    ordering = ['-imported_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        org = getattr(self.request, 'current_organization', None)
        if org:
            queryset = queryset.filter(organization=org)
        return queryset

    @action(detail=True, methods=['post'], url_path='rollback')
    def rollback(self, request, pk=None):
        """
        Rollback a previous import.
        """
        import_log = self.get_object()
        
        if not import_log.can_rollback:
            return Response(
                {'error': 'This import cannot be rolled back'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        org = getattr(request, 'current_organization', None)
        service = ConfigPackageService(organization=org, user=request.user)
        
        try:
            service.rollback_import(import_log)
            return Response({
                'success': True,
                'message': 'Import rolled back successfully'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
