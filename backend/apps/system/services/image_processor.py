"""
Image Processing Service

Provides image manipulation functions for file attachments:
- Thumbnail generation
- Image resizing/compression (for files > 5MB)
- Format conversion
- Dimension extraction
- Watermark application
"""

import os
import io
from typing import Tuple, Optional, BinaryIO
from django.conf import settings
from PIL import Image, ImageOps, ImageDraw, ImageFont
from pathlib import Path


class ImageProcessorService:
    """
    Service for processing uploaded images.

    Features:
    - Generate thumbnails for images
    - Compress images larger than 5MB
    - Extract image dimensions
    - Convert between formats
    """

    # Thumbnail size (width, height)
    THUMBNAIL_SIZE = (200, 200)
    # Max file size for automatic compression (5MB)
    MAX_AUTO_COMPRESS_SIZE = 5 * 1024 * 1024
    # Compressed image quality (1-100)
    COMPRESS_QUALITY = 85
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}

    @classmethod
    def is_image_file(cls, filename: str, mime_type: Optional[str] = None) -> bool:
        """
        Check if file is an image based on extension or MIME type.

        Args:
            filename: File name to check
            mime_type: Optional MIME type from file upload

        Returns:
            True if file is a supported image format
        """
        ext = Path(filename).suffix.lower()
        if ext in cls.SUPPORTED_FORMATS:
            return True
        if mime_type and mime_type.startswith('image/'):
            return True
        return False

    @classmethod
    def get_image_dimensions(cls, file: BinaryIO) -> Tuple[int, int]:
        """
        Extract image dimensions (width x height).

        Args:
            file: File-like object containing image data

        Returns:
            Tuple of (width, height) in pixels
        """
        file.seek(0)
        with Image.open(file) as img:
            width, height = img.size
        file.seek(0)
        return width, height

    @classmethod
    def generate_thumbnail(
        cls,
        file: BinaryIO,
        size: Tuple[int, int] = None,
        format: str = 'JPEG'
    ) -> Tuple[bytes, str, int, int]:
        """
        Generate a thumbnail from an image file.

        Args:
            file: File-like object containing image data
            size: Thumbnail size (width, height), defaults to THUMBNAIL_SIZE
            format: Output format (JPEG, PNG, WEBP)

        Returns:
            Tuple of (thumbnail_bytes, extension, width, height)
        """
        if size is None:
            size = cls.THUMBNAIL_SIZE

        file.seek(0)
        with Image.open(file) as img:
            # Convert to RGB if necessary (for JPEG output)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Create thumbnail with aspect ratio preservation
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Save to bytes buffer
            buffer = io.BytesIO()
            ext = f'.{format.lower()}'
            img.save(buffer, format=format, quality=cls.COMPRESS_QUALITY)
            thumbnail_bytes = buffer.getvalue()
            buffer.close()

        file.seek(0)
        return thumbnail_bytes, ext, img.width, img.height

    @classmethod
    def compress_image(
        cls,
        file: BinaryIO,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = None
    ) -> Tuple[bytes, str, int, int, int]:
        """
        Compress an image to reduce file size.

        1. Resize if dimensions exceed max_width/max_height
        2. Compress with specified quality

        Args:
            file: File-like object containing image data
            max_width: Maximum width in pixels
            max_height: Maximum height in pixels
            quality: JPEG quality (1-100), defaults to COMPRESS_QUALITY

        Returns:
            Tuple of (compressed_bytes, format, width, height, original_size)
        """
        if quality is None:
            quality = cls.COMPRESS_QUALITY

        file.seek(0)
        original_size = len(file.read())
        file.seek(0)

        with Image.open(file) as img:
            original_width, original_height = img.size
            width, height = original_width, original_height

            # Calculate new dimensions if needed
            if width > max_width or height > max_height:
                ratio = min(max_width / width, max_height / height)
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                width, height = new_width, new_height

            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Save compressed image
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            compressed_bytes = buffer.getvalue()
            buffer.close()

        file.seek(0)
        return compressed_bytes, '.jpg', width, height, original_size

    @classmethod
    def process_uploaded_image(
        cls,
        file: BinaryIO,
        filename: str,
        file_size: int,
        generate_thumbnail: bool = True
    ) -> dict:
        """
        Process an uploaded image file.

        - Extract dimensions
        - Generate thumbnail if requested
        - Compress if file size exceeds MAX_AUTO_COMPRESS_SIZE

        Args:
            file: File-like object containing image data
            filename: Original filename
            file_size: File size in bytes
            generate_thumbnail: Whether to generate thumbnail

        Returns:
            Dictionary with processing results:
            {
                'width': int,
                'height': int,
                'thumbnail_path': str or None,
                'is_compressed': bool,
                'original_file_id': str or None
            }
        """
        result = {
            'width': None,
            'height': None,
            'thumbnail_path': None,
            'is_compressed': False,
            'original_file_id': None
        }

        try:
            # Extract dimensions
            width, height = cls.get_image_dimensions(file)
            result['width'] = width
            result['height'] = height

            # Check if compression is needed
            needs_compression = file_size > cls.MAX_AUTO_COMPRESS_SIZE

            # Generate thumbnail
            if generate_thumbnail:
                thumbnail_bytes, ext, thumb_w, thumb_h = cls.generate_thumbnail(file)
                # Store thumbnail path will be determined by the calling service
                result['thumbnail_data'] = thumbnail_bytes
                result['thumbnail_ext'] = ext

            # Compress if needed
            if needs_compression:
                compressed_bytes, fmt, new_w, new_h, orig_size = cls.compress_image(file)
                result['is_compressed'] = True
                result['compressed_data'] = compressed_bytes
                result['compressed_ext'] = fmt
                result['compressed_width'] = new_w
                result['compressed_height'] = new_h

        except Exception as e:
            # Log error but don't fail the upload
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Image processing failed for {filename}: {e}")

        return result

    @classmethod
    def get_thumbnail_storage_path(cls, original_path: str) -> str:
        """
        Generate thumbnail file path from original file path.

        Args:
            original_path: Original file path (e.g., 'uploads/2025/01/29/file.jpg')

        Returns:
            Thumbnail path (e.g., 'uploads/2025/01/29/thumbnails/file.jpg')
        """
        path = Path(original_path)
        filename = path.stem  # filename without extension
        ext = path.suffix
        parent = path.parent

        # Create thumbnails subdirectory
        thumbnail_dir = parent / 'thumbnails'
        return str(thumbnail_dir / f'{filename}_thumb{ext}')

    @classmethod
    def save_thumbnail(cls, thumbnail_bytes: bytes, media_root: str, thumbnail_path: str) -> str:
        """
        Save thumbnail bytes to disk.

        Args:
            thumbnail_bytes: Thumbnail image data
            media_root: MEDIA_ROOT path
            thumbnail_path: Relative thumbnail path

        Returns:
            Full thumbnail path
        """
        full_path = Path(media_root) / thumbnail_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(thumbnail_bytes)

        return str(full_path)

    @classmethod
    def validate_image(cls, file: BinaryIO) -> dict:
        """
        Validate image file and extract metadata.

        Args:
            file: File-like object containing image data

        Returns:
            Dictionary with validation results:
            {
                'valid': bool,
                'error': str or None,
                'width': int or None,
                'height': int or None,
                'format': str or None
            }
        """
        result = {
            'valid': False,
            'error': None,
            'width': None,
            'height': None,
            'format': None
        }

        try:
            file.seek(0)
            with Image.open(file) as img:
                result['width'] = img.width
                result['height'] = img.height
                result['format'] = img.format
                result['valid'] = True
            file.seek(0)
        except Exception as e:
            result['error'] = str(e)

        return result

    @classmethod
    def add_watermark(
        cls,
        file: BinaryIO,
        text: str = None,
        position: str = 'bottom-right',
        opacity: int = 128,
        font_size: int = 24
    ) -> Tuple[bytes, str, int, int]:
        """
        Add watermark to an image.

        Args:
            file: File-like object containing image data
            text: Watermark text (default: organization name or 'CONFIDENTIAL')
            position: Watermark position - 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'center'
            opacity: Transparency level (0-255, default 128 = 50%)
            font_size: Font size in pixels

        Returns:
            Tuple of (watermarked_bytes, extension, width, height)
        """
        if text is None:
            text = getattr(settings, 'WATERMARK_TEXT', 'CONFIDENTIAL')

        file.seek(0)
        with Image.open(file) as img:
            # Convert to RGBA if necessary for transparency support
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Create overlay for watermark
            overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)

            # Try to load a font, fall back to default if not available
            try:
                # Try to load a TrueType font
                font = ImageFont.truetype("arial.ttf", font_size)
            except (OSError, IOError):
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
                except (OSError, IOError):
                    # Use default font as fallback
                    font = ImageFont.load_default()

            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            # Calculate position
            padding = 10
            img_width, img_height = img.size

            position_coords = {
                'top-left': (padding, padding),
                'top-right': (img_width - text_width - padding, padding),
                'bottom-left': (padding, img_height - text_height - padding),
                'bottom-right': (img_width - text_width - padding, img_height - text_height - padding),
                'center': ((img_width - text_width) // 2, (img_height - text_height) // 2)
            }

            x, y = position_coords.get(position, position_coords['bottom-right'])

            # Draw text with opacity
            draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))

            # Composite watermark onto original image
            watermarked = Image.alpha_composite(img, overlay)

            # Convert back to RGB for JPEG compatibility
            watermarked_rgb = watermarked.convert('RGB')

            # Save to bytes buffer
            buffer = io.BytesIO()
            watermarked_rgb.save(buffer, format='JPEG', quality=cls.COMPRESS_QUALITY)
            watermarked_bytes = buffer.getvalue()
            buffer.close()

        file.seek(0)
        return watermarked_bytes, '.jpg', watermarked_rgb.width, watermarked_rgb.height

    @classmethod
    def get_watermark_storage_path(cls, original_path: str) -> str:
        """
        Generate watermarked file path from original file path.

        Args:
            original_path: Original file path (e.g., 'uploads/2025/01/29/file.jpg')

        Returns:
            Watermarked path (e.g., 'uploads/2025/01/29/watermarked/file.jpg')
        """
        path = Path(original_path)
        filename = path.stem
        ext = path.suffix
        parent = path.parent

        # Create watermarked subdirectory
        watermarked_dir = parent / 'watermarked'
        return str(watermarked_dir / f'{filename}_watermarked{ext}')

    @classmethod
    def save_watermarked_image(cls, watermarked_bytes: bytes, media_root: str, watermarked_path: str) -> str:
        """
        Save watermarked image to disk.

        Args:
            watermarked_bytes: Watermarked image data
            media_root: MEDIA_ROOT path
            watermarked_path: Relative watermarked path

        Returns:
            Full watermarked image path
        """
        full_path = Path(media_root) / watermarked_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(watermarked_bytes)

        return str(full_path)
