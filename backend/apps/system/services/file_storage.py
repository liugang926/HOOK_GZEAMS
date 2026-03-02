"""
File Storage Service

Provides file upload, storage, and management functionality for the SystemFile model.
Handles file validation, storage path generation, and deduplication.
"""

import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, BinaryIO
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import File
from django.utils import timezone
import mimetypes


class FileStorageService:
    """
    Service for managing file storage operations.

    Responsibilities:
    - File upload and validation
    - Storage path generation (organized by date)
    - File deduplication using SHA256 hash
    - MIME type detection
    - Dynamic object reference tracking
    """

    # Maximum file size (50MB default)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # Allowed MIME types (empty means all types allowed)
    ALLOWED_MIME_TYPES = []

    def __init__(self):
        """Initialize file storage service."""
        self.upload_root = getattr(settings, 'MEDIA_ROOT', 'media')
        self.upload_url = getattr(settings, 'MEDIA_URL', '/media/')

    def get_storage_path(self, original_filename: str) -> str:
        """
        Generate storage path for uploaded file.

        Files are organized by date: uploads/YYYY/MM/DD/filename

        Args:
            original_filename: Original file name

        Returns:
            Relative path from MEDIA_ROOT
        """
        now = timezone.now()
        date_path = now.strftime('uploads/%Y/%m/%d')

        # Sanitize filename
        safe_filename = self.sanitize_filename(original_filename)

        # Generate unique filename if file exists
        base_path = os.path.join(self.upload_root, date_path)
        full_path = os.path.join(base_path, safe_filename)

        counter = 1
        while os.path.exists(full_path):
            name, ext = os.path.splitext(safe_filename)
            safe_filename = f"{name}_{counter}{ext}"
            full_path = os.path.join(base_path, safe_filename)
            counter += 1

        return os.path.join(date_path, safe_filename)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to remove dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Safe filename
        """
        # Remove path separators
        filename = os.path.basename(filename)

        # Keep only safe characters
        safe_chars = "-_.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        safe_filename = ''.join(c if c in safe_chars else '_' for c in filename)

        # Ensure filename is not empty
        if not safe_filename or safe_filename == '_':
            safe_filename = f"file_{timezone.now().timestamp()}"

        return safe_filename

    def calculate_file_hash(self, file: BinaryIO) -> str:
        """
        Calculate SHA256 hash of file for deduplication.

        Args:
            file: File object to hash

        Returns:
            Hexadecimal SHA256 hash
        """
        hasher = hashlib.sha256()
        # Reset file pointer
        file.seek(0)
        # Read in chunks to handle large files
        for chunk in iter(lambda: file.read(8192), b''):
            hasher.update(chunk)
        # Reset file pointer
        file.seek(0)
        return hasher.hexdigest()

    def detect_mime_type(self, filename: str) -> str:
        """
        Detect MIME type from filename.

        Args:
            filename: File name

        Returns:
            MIME type string
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    def detect_file_extension(self, filename: str) -> str:
        """
        Extract file extension from filename.

        Args:
            filename: File name

        Returns:
            File extension (with dot)
        """
        _, ext = os.path.splitext(filename)
        return ext.lower()

    def validate_file(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate uploaded file.

        Args:
            file: Uploaded file object

        Returns:
            Validation result dict with 'valid' and 'error' keys
        """
        # Check file size
        if file.size > self.MAX_FILE_SIZE:
            return {
                'valid': False,
                'error': f'File too large. Maximum size is {self.MAX_FILE_SIZE} bytes.'
            }

        # Check file is not empty
        if file.size == 0:
            return {
                'valid': False,
                'error': 'File is empty.'
            }

        # Check MIME type if restrictions are set
        if self.ALLOWED_MIME_TYPES:
            mime_type = self.detect_mime_type(file.name)
            if mime_type not in self.ALLOWED_MIME_TYPES:
                return {
                    'valid': False,
                    'error': f'File type {mime_type} is not allowed.'
                }

        return {'valid': True}

    def check_duplicate(self, file_hash: str, organization_id: str) -> Optional[Any]:
        """
        Check if file with same hash already exists.

        Args:
            file_hash: SHA256 hash of file
            organization_id: Organization ID

        Returns:
            Existing SystemFile instance if found, None otherwise
        """
        from apps.system.models import SystemFile

        try:
            return SystemFile.objects.get(
                file_hash=file_hash,
                organization_id=organization_id,
                is_deleted=False
            )
        except SystemFile.DoesNotExist:
            return None

    def save_file(self, file: UploadedFile, organization_id: str,
                  object_code: str = None, instance_id: str = None,
                  field_code: str = None, description: str = None,
                  add_watermark: bool = False, watermark_text: str = None,
                  watermark_position: str = 'bottom-right',
                  watermark_opacity: int = 128) -> Dict[str, Any]:
        """
        Save uploaded file to storage and create SystemFile record.

        Handles:
        - File validation and deduplication
        - Image processing (thumbnails, compression, watermark) for image files
        - Dynamic object reference tracking

        Args:
            file: Uploaded file object
            organization_id: Organization ID
            object_code: Optional business object code
            instance_id: Optional business object instance ID
            field_code: Optional field code for dynamic object
            description: Optional file description
            add_watermark: Whether to add watermark to image
            watermark_text: Custom watermark text (optional)
            watermark_position: Watermark position ('top-left', 'top-right', 'bottom-left', 'bottom-right', 'center')
            watermark_opacity: Watermark opacity (0-255, default 128)

        Returns:
            Dict with 'success', 'data', or 'error' keys
        """
        from apps.system.models import SystemFile
        from .image_processor import ImageProcessorService

        # Validate file
        validation = self.validate_file(file)
        if not validation['valid']:
            return {
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': validation['error']
                }
            }

        # Calculate file hash for deduplication
        file_hash = self.calculate_file_hash(file)

        # Check for duplicate
        duplicate = self.check_duplicate(file_hash, organization_id)
        if duplicate:
            # Create reference to existing file
            return {
                'success': True,
                'data': duplicate,
                'is_duplicate': True
            }

        # Detect MIME type and extension
        mime_type = self.detect_mime_type(file.name)
        extension = self.detect_file_extension(file.name)

        # Check if file is an image
        is_image = ImageProcessorService.is_image_file(file.name, mime_type)

        # Process image if applicable
        image_result = None
        final_file = file
        final_size = file.size
        final_extension = extension

        if is_image:
            try:
                # Process image: extract dimensions, generate thumbnail, compress if needed
                image_result = ImageProcessorService.process_uploaded_image(
                    file.open('rb') if hasattr(file, 'open') else file,
                    file.name,
                    file.size,
                    generate_thumbnail=True
                )

                # If image was compressed, use compressed data
                if image_result.get('is_compressed'):
                    from io import BytesIO
                    compressed_data = image_result.get('compressed_data')
                    if compressed_data:
                        # Create a new file-like object with compressed data
                        final_file = BytesIO(compressed_data)
                        final_file.name = file.name
                        final_size = len(compressed_data)
                        final_extension = image_result.get('compressed_ext', extension)

            except Exception as e:
                # Log error but continue with original file
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Image processing failed for {file.name}: {e}, using original file")

        # Generate storage path
        storage_path = self.get_storage_path(file.name)

        # Get full filesystem path
        full_path = os.path.join(self.upload_root, storage_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Write file to disk
        if isinstance(final_file, BytesIO):
            final_file.seek(0)
            with open(full_path, 'wb') as destination:
                destination.write(final_file.read())
        else:
            with open(full_path, 'wb') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

        # Save thumbnail if generated
        thumbnail_path = None
        if image_result and image_result.get('thumbnail_data'):
            thumbnail_bytes = image_result.get('thumbnail_data')
            thumbnail_ext = image_result.get('thumbnail_ext', '.jpg')
            thumbnail_path = ImageProcessorService.get_thumbnail_storage_path(storage_path)
            # Replace extension for thumbnail
            base_name = thumbnail_path.rsplit('.', 1)[0] if '.' in thumbnail_path else thumbnail_path
            thumbnail_path = base_name + thumbnail_ext
            ImageProcessorService.save_thumbnail(
                thumbnail_bytes,
                self.upload_root,
                thumbnail_path
            )

        # Save watermarked version if requested
        watermarked_path = None
        if is_image and add_watermark:
            try:
                watermarked_bytes, watermarked_ext, _, _ = ImageProcessorService.add_watermark(
                    file.open('rb') if hasattr(file, 'open') else file,
                    text=watermark_text,
                    position=watermark_position,
                    opacity=watermark_opacity
                )
                watermarked_path = ImageProcessorService.get_watermark_storage_path(storage_path)
                # Replace extension for watermarked image
                base_name = watermarked_path.rsplit('.', 1)[0] if '.' in watermarked_path else watermarked_path
                watermarked_path = base_name + watermarked_ext
                ImageProcessorService.save_watermarked_image(
                    watermarked_bytes,
                    self.upload_root,
                    watermarked_path
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Watermark generation failed for {file.name}: {e}")

        # Prepare SystemFile fields
        system_file_data = {
            'file_name': file.name,
            'file_path': storage_path,
            'file_size': final_size,
            'file_type': mime_type,
            'file_extension': final_extension,
            'file_hash': file_hash,
            'object_code': object_code or '',
            'instance_id': instance_id,
            'field_code': field_code or '',
            'description': description or '',
            'organization_id': organization_id,
            'thumbnail_path': thumbnail_path,
            'watermarked_path': watermarked_path,
        }

        # Add image-specific fields
        if image_result:
            if image_result.get('width'):
                system_file_data['width'] = image_result['width']
            if image_result.get('height'):
                system_file_data['height'] = image_result['height']
            if image_result.get('is_compressed'):
                system_file_data['is_compressed'] = True

        # Create SystemFile record
        system_file = SystemFile.objects.create(**system_file_data)

        return {
            'success': True,
            'data': system_file,
            'is_duplicate': False
        }

    def add_watermark_to_file(
        self,
        file_id: str,
        organization_id: str,
        watermark_text: str = None,
        watermark_position: str = 'bottom-right',
        watermark_opacity: int = 128
    ) -> Dict[str, Any]:
        """
        Add watermark to an existing uploaded image file.

        Args:
            file_id: SystemFile ID
            organization_id: Organization ID
            watermark_text: Custom watermark text (optional)
            watermark_position: Watermark position
            watermark_opacity: Watermark opacity (0-255)

        Returns:
            Dict with 'success', 'data', or 'error' keys
        """
        from apps.system.models import SystemFile
        from .image_processor import ImageProcessorService

        try:
            system_file = SystemFile.objects.get(
                id=file_id,
                organization_id=organization_id,
                is_deleted=False
            )
        except SystemFile.DoesNotExist:
            return {
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'File not found.'
                }
            }

        # Check if file is an image
        if not ImageProcessorService.is_image_file(system_file.file_name, system_file.file_type):
            return {
                'success': False,
                'error': {
                    'code': 'INVALID_FILE_TYPE',
                    'message': 'Watermark can only be added to image files.'
                }
            }

        # Get full file path
        full_path = os.path.join(self.upload_root, system_file.file_path)

        if not os.path.exists(full_path):
            return {
                'success': False,
                'error': {
                    'code': 'FILE_NOT_FOUND',
                    'message': 'Original file not found on disk.'
                }
            }

        try:
            # Open file and add watermark
            with open(full_path, 'rb') as f:
                watermarked_bytes, watermarked_ext, width, height = ImageProcessorService.add_watermark(
                    f,
                    text=watermark_text,
                    position=watermark_position,
                    opacity=watermark_opacity
                )

            # Generate watermarked path
            watermarked_path = ImageProcessorService.get_watermark_storage_path(system_file.file_path)
            base_name = watermarked_path.rsplit('.', 1)[0] if '.' in watermarked_path else watermarked_path
            watermarked_path = base_name + watermarked_ext

            # Save watermarked image
            ImageProcessorService.save_watermarked_image(
                watermarked_bytes,
                self.upload_root,
                watermarked_path
            )

            # Update SystemFile record
            system_file.watermarked_path = watermarked_path
            system_file.save(update_fields=['watermarked_path'])

            return {
                'success': True,
                'data': {
                    'file_id': str(system_file.id),
                    'watermarked_path': watermarked_path,
                    'width': width,
                    'height': height
                }
            }

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to add watermark to file {file_id}: {e}")
            return {
                'success': False,
                'error': {
                    'code': 'WATERMARK_ERROR',
                    'message': f'Failed to add watermark: {str(e)}'
                }
            }

    def get_file_metadata(self, file_ids: list, organization_id: str) -> list:
        """
        Get metadata for multiple files.

        Args:
            file_ids: List of file IDs
            organization_id: Organization ID

        Returns:
            List of SystemFile instances
        """
        from apps.system.models import SystemFile

        return list(SystemFile.objects.filter(
            id__in=file_ids,
            organization_id=organization_id,
            is_deleted=False
        ))

    def delete_file(self, file_id: str, organization_id: str, user=None) -> Dict[str, Any]:
        """
        Soft delete a file.

        Args:
            file_id: File ID to delete
            organization_id: Organization ID
            user: User performing the deletion

        Returns:
            Result dict with 'success' and 'message' keys
        """
        from apps.system.models import SystemFile

        try:
            system_file = SystemFile.objects.get(
                id=file_id,
                organization_id=organization_id,
                is_deleted=False
            )
            system_file.soft_delete(user)

            return {
                'success': True,
                'message': 'File deleted successfully.'
            }
        except SystemFile.DoesNotExist:
            return {
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'File not found or already deleted.'
                }
            }

    def batch_delete_files(self, file_ids: list, organization_id: str, user=None) -> Dict[str, Any]:
        """
        Batch soft delete multiple files.

        Args:
            file_ids: List of file IDs to delete
            organization_id: Organization ID
            user: User performing the deletion

        Returns:
            Result dict with 'success', 'summary', and 'results' keys
        """
        from apps.system.models import SystemFile

        results = []
        succeeded = 0
        failed = 0

        for file_id in file_ids:
            try:
                system_file = SystemFile.objects.get(
                    id=file_id,
                    organization_id=organization_id,
                    is_deleted=False
                )
                system_file.soft_delete(user)
                results.append({'id': str(file_id), 'success': True})
                succeeded += 1
            except SystemFile.DoesNotExist:
                results.append({'id': str(file_id), 'success': False, 'error': 'Not found'})
                failed += 1
            except Exception as e:
                results.append({'id': str(file_id), 'success': False, 'error': str(e)})
                failed += 1

        return {
            'success': True,
            'summary': {
                'total': len(file_ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }
