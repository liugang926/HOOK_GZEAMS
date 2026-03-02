"""
SystemFile ViewSet

Provides API endpoints for file upload, management, and retrieval.
Handles file operations for dynamic object file/attachment fields.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404, HttpResponse
from django.conf import settings
import os
import zipfile
import io
from datetime import datetime

from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.system.models import SystemFile
from apps.system.serializers import (
    SystemFileSerializer,
    SystemFileListSerializer,
    SystemFileUploadSerializer,
    SystemFileBatchDeleteSerializer,
)
from apps.system.services.file_storage import FileStorageService


class SystemFileViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for SystemFile model.

    Provides standard CRUD operations plus:
    - upload(): Handle file uploads
    - download(): Serve file for download
    - batch_delete(): Batch soft delete (inherited from mixin)
    - metadata(): Get metadata for multiple files

    Inherits from BaseModelViewSetWithBatch which provides:
    - Organization isolation
    - Soft delete handling
    - Batch operations
    - Audit trail management
    """

    queryset = SystemFile.objects.filter(is_deleted=False)
    serializer_class = SystemFileSerializer
    parsers = [MultiPartParser, FormParser]  # Support file uploads
    search_fields = ['file_name', 'description']
    ordering_fields = ['file_name', 'file_size', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SystemFileListSerializer
        if self.action == 'upload':
            return SystemFileUploadSerializer
        return SystemFileSerializer

    def retrieve(self, request, *args, **kwargs):
        """Get single file record with full details."""
        try:
            instance = self.get_object()
            serializer = SystemFileSerializer(instance)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except SystemFile.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='File not found or has been deleted.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """
        Upload a file.

        Request body (multipart/form-data):
        - file: The file to upload
        - object_code: Optional business object code
        - instance_id: Optional business object instance ID
        - field_code: Optional field code for dynamic object
        - description: Optional file description

        Response format:
        {
            "success": true,
            "data": {
                "id": "uuid",
                "file_name": "example.pdf",
                "file_path": "uploads/2025/01/29/example.pdf",
                "file_size": 1048576,
                "file_type": "application/pdf",
                "file_extension": ".pdf",
                "url": "/media/uploads/2025/01/29/example.pdf",
                ...
            }
        }
        """
        serializer = SystemFileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        object_code = serializer.validated_data.get('object_code', '')
        instance_id = serializer.validated_data.get('instance_id')
        field_code = serializer.validated_data.get('field_code', '')
        description = serializer.validated_data.get('description', '')

        # Get organization from request
        organization_id = getattr(request, 'organization_id', None)

        # Fallback: Try to get user's primary organization
        if not organization_id and request.user and request.user.is_authenticated:
            try:
                primary_org = request.user.get_primary_organization()
                if primary_org:
                    organization_id = str(primary_org.id)
                    # Update request.organization_id for consistency
                    request.organization_id = organization_id
            except Exception as e:
                # Log but continue to error response
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Could not get primary organization for user {request.user.username}: {e}')

        # Final check - return proper error if still no organization
        if not organization_id:
            return BaseResponse.error(
                code='ORGANIZATION_REQUIRED',
                message='Organization context is required. Please select an organization or contact administrator.',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Use FileStorageService to save the file
        service = FileStorageService()
        result = service.save_file(
            file=uploaded_file,
            organization_id=organization_id,
            object_code=object_code,
            instance_id=instance_id,
            field_code=field_code,
            description=description
        )

        if not result['success']:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the created/found file
        file_serializer = SystemFileSerializer(result['data'])

        response_data = {
            'success': True,
            'data': file_serializer.data
        }

        # Add is_duplicate flag if file was deduplicated
        if result.get('is_duplicate'):
            response_data['message'] = 'File already exists (deduplicated).'

        http_status = status.HTTP_201_CREATED if not result.get('is_duplicate') else status.HTTP_200_OK
        return Response(response_data, status=http_status)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download a file.

        Returns the actual file for download.
        Sets appropriate Content-Disposition header.

        GET /api/system-files/{id}/download/
        """
        try:
            instance = self.get_object()

            # Build full file path
            file_path = os.path.join(settings.MEDIA_ROOT, instance.file_path)

            # Check if file exists
            if not os.path.exists(file_path):
                return BaseResponse.error(
                    code='FILE_NOT_FOUND',
                    message='The requested file could not be found on the server.',
                    http_status=status.HTTP_404_NOT_FOUND
                )

            # Return file response
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=instance.file_type or 'application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{instance.file_name}"'
            return response

        except SystemFile.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='File record not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def metadata(self, request):
        """
        Get metadata for multiple files.

        Query parameters:
        - ids: Comma-separated list of file IDs

        Response format:
        {
            "success": true,
            "data": [
                {
                    "id": "uuid",
                    "file_name": "example.pdf",
                    "url": "/media/...",
                    ...
                }
            ]
        }
        """
        ids_param = request.query_params.get('ids', '')
        if not ids_param:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='ids parameter is required (comma-separated file IDs).',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Parse IDs
        try:
            file_ids = [id.strip() for id in ids_param.split(',') if id.strip()]
        except Exception:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='Invalid ids format.',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization from request
        organization_id = getattr(request, 'organization_id', None)
        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context is required.',
                http_status=status.HTTP_401_UNAUTHORIZED
            )

        # Get file metadata
        service = FileStorageService()
        files = service.get_file_metadata(file_ids, organization_id)

        # Serialize results
        serializer = SystemFileSerializer(files, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        Batch soft delete multiple files.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Response format:
        {
            "success": true,
            "message": "Batch delete completed",
            "summary": {
                "total": 3,
                "succeeded": 3,
                "failed": 0
            },
            "results": [...]
        }
        """
        serializer = SystemFileBatchDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file_ids = serializer.validated_data['ids']

        # Get organization from request
        organization_id = getattr(request, 'organization_id', None)
        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context is required.',
                http_status=status.HTTP_401_UNAUTHORIZED
            )

        # Use FileStorageService for batch delete
        service = FileStorageService()
        result = service.batch_delete_files(
            file_ids=file_ids,
            organization_id=organization_id,
            user=request.user
        )

        http_status = status.HTTP_200_OK if result['summary']['failed'] == 0 else status.HTTP_207_MULTI_STATUS
        return Response(result, status=http_status)

    @action(detail=True, methods=['post'])
    def add_watermark(self, request, pk=None):
        """
        Add watermark to an image file.

        Request body:
        {
            "text": "CONFIDENTIAL",  // Optional watermark text
            "position": "bottom-right",  // Optional: top-left, top-right, bottom-left, bottom-right, center
            "opacity": 128  // Optional: 0-255, default 128
        }

        Response format:
        {
            "success": true,
            "data": {
                "file_id": "uuid",
                "watermarked_path": "uploads/2025/01/29/watermarked/file_watermarked.jpg",
                "width": 1920,
                "height": 1080
            }
        }
        """
        # Get request parameters
        watermark_text = request.data.get('text')
        watermark_position = request.data.get('position', 'bottom-right')
        watermark_opacity = int(request.data.get('opacity', 128))

        # Validate position
        valid_positions = ['top-left', 'top-right', 'bottom-left', 'bottom-right', 'center']
        if watermark_position not in valid_positions:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message=f'Invalid position. Must be one of: {", ".join(valid_positions)}',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Validate opacity
        if not 0 <= watermark_opacity <= 255:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='Opacity must be between 0 and 255.',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization from request
        organization_id = getattr(request, 'organization_id', None)
        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context is required.',
                http_status=status.HTTP_401_UNAUTHORIZED
            )

        # Use FileStorageService to add watermark
        service = FileStorageService()
        result = service.add_watermark_to_file(
            file_id=pk,
            organization_id=organization_id,
            watermark_text=watermark_text,
            watermark_position=watermark_position,
            watermark_opacity=watermark_opacity
        )

        if not result['success']:
            error_code = result.get('error', {}).get('code', 'WATERMARK_ERROR')
            http_status = status.HTTP_400_BAD_REQUEST
            if error_code == 'NOT_FOUND':
                http_status = status.HTTP_404_NOT_FOUND
            elif error_code == 'INVALID_FILE_TYPE':
                http_status = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            return Response(result, status=http_status)

        # Refresh and serialize the updated file
        try:
            instance = self.get_object()
            serializer = SystemFileSerializer(instance)
            result['data']['file'] = serializer.data
        except SystemFile.DoesNotExist:
            pass

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def download_watermarked(self, request, pk=None):
        """
        Download watermarked version of an image.

        Returns the watermarked image file for download.
        If no watermarked version exists, returns the original file.

        GET /api/system-files/{id}/download_watermarked/
        """
        try:
            instance = self.get_object()

            # Use watermarked version if available
            file_path = instance.watermarked_path or instance.file_path
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            # Check if file exists
            if not os.path.exists(full_path):
                return BaseResponse.error(
                    code='FILE_NOT_FOUND',
                    message='The requested file could not be found on the server.',
                    http_status=status.HTTP_404_NOT_FOUND
                )

            # Return file response
            response = FileResponse(
                open(full_path, 'rb'),
                content_type=instance.file_type or 'application/octet-stream'
            )
            # Add suffix to filename if watermarked
            download_name = instance.file_name
            if instance.watermarked_path:
                name, ext = os.path.splitext(instance.file_name)
                download_name = f"{name}_watermarked{ext}"
            response['Content-Disposition'] = f'attachment; filename="{download_name}"'
            return response

        except SystemFile.DoesNotExist:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='File record not found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def batch_download(self, request):
        """
        Batch download multiple files as a ZIP archive.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"],
            "zip_name": "files.zip"  // Optional, defaults to timestamped name
        }

        Response: ZIP file download with all requested files.
        """
        file_ids = request.data.get('ids', [])
        zip_name = request.data.get('zip_name')

        if not file_ids:
            return BaseResponse.error(
                code='VALIDATION_ERROR',
                message='ids parameter is required.',
                http_status=status.HTTP_400_BAD_REQUEST
            )

        # Get organization from request
        organization_id = getattr(request, 'organization_id', None)
        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context is required.',
                http_status=status.HTTP_401_UNAUTHORIZED
            )

        # Get files
        service = FileStorageService()
        files = service.get_file_metadata(file_ids, organization_id)

        if not files:
            return BaseResponse.error(
                code='NOT_FOUND',
                message='No valid files found.',
                http_status=status.HTTP_404_NOT_FOUND
            )

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        try:
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_obj in files:
                    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.file_path)

                    if os.path.exists(file_path):
                        # Use original filename to avoid path issues
                        zip_file.write(
                            file_path,
                            arcname=file_obj.file_name
                        )

            # Prepare response
            zip_buffer.seek(0)

            # Generate zip filename
            if not zip_name:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                zip_name = f'files_{timestamp}.zip'

            if not zip_name.endswith('.zip'):
                zip_name += '.zip'

            response = HttpResponse(
                zip_buffer.getvalue(),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
            return response

        except Exception as e:
            return BaseResponse.error(
                code='SERVER_ERROR',
                message=f'Failed to create ZIP file: {str(e)}',
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_queryset(self):
        """
        Filter queryset by organization and support additional filters.

        Supports filtering by:
        - object_code: Filter by business object
        - instance_id: Filter by instance ID
        - field_code: Filter by field code
        """
        queryset = super().get_queryset()

        # Filter by dynamic object references
        object_code = self.request.query_params.get('object_code')
        if object_code:
            queryset = queryset.filter(object_code=object_code)

        instance_id = self.request.query_params.get('instance_id')
        if instance_id:
            queryset = queryset.filter(instance_id=instance_id)

        field_code = self.request.query_params.get('field_code')
        if field_code:
            queryset = queryset.filter(field_code=field_code)

        return queryset
