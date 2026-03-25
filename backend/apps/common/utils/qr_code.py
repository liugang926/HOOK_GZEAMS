"""
QR Code generation utility for GZEAMS.

Provides functions for:
- QR code image generation
- QR code data encoding
- Asset label QR code generation with customizable styling
"""
import io
import base64
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class QRCodeConfig:
    """Configuration for QR code generation."""

    size: int = 300  # Image size in pixels
    version: int = 1  # QR code version (1-40)
    error_correction: str = 'M'  # Error correction level: L, M, Q, H
    box_size: int = 10  # Size of each box in pixels
    border: int = 4  # Border size in boxes
    fill_color: str = 'black'  # QR code fill color
    back_color: str = 'white'  # Background color

    # Label configuration
    show_text: bool = True  # Show asset code below QR code
    font_size: int = 12  # Font size for label text


def generate_qr_code(
    data: str,
    config: Optional[QRCodeConfig] = None
) -> Tuple[bytes, str]:
    """
    Generate QR code image from data.

    Args:
        data: Data to encode in QR code
        config: QR code configuration

    Returns:
        Tuple of (image_bytes, image_format)

    Raises:
        ImportError: If qrcode library is not installed
    """
    try:
        import qrcode
    except ImportError:
        raise ImportError(
            "qrcode library is required. Install it with: pip install qrcode[pil]"
        )

    if config is None:
        config = QRCodeConfig()

    # Map error correction level
    error_map = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }
    error_level = error_map.get(config.error_correction, qrcode.constants.ERROR_CORRECT_M)

    # Create QR code
    qr = qrcode.QRCode(
        version=config.version,
        error_correction=error_level,
        box_size=config.box_size,
        border=config.border,
    )

    qr.add_data(data)
    qr.make(fit=True)

    # Generate image
    img = qr.make_image(fill_color=config.fill_color, back_color=config.back_color)

    # Add text label if configured
    if config.show_text:
        from PIL import Image, ImageDraw, ImageFont

        # Create new image with space for text
        text_height = config.font_size + 10
        new_img = Image.new(
            'RGB',
            (img.width, img.height + text_height),
            config.back_color
        )
        new_img.paste(img, (0, 0))

        # Draw text
        draw = ImageDraw.Draw(new_img)

        # Try to use a default font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config.font_size)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", config.font_size)
            except Exception:
                # Fallback to default font
                font = ImageFont.load_default()

        # Get text bounding box
        bbox = draw.textbbox((0, 0), data, font=font)
        text_width = bbox[2] - bbox[0]

        # Center text
        x = (new_img.width - text_width) // 2
        y = img.height + 5

        draw.text((x, y), data, fill=config.fill_color, font=font)
        img = new_img

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_bytes = buffer.getvalue()

    return image_bytes, 'PNG'


def generate_qr_code_base64(
    data: str,
    config: Optional[QRCodeConfig] = None
) -> str:
    """
    Generate QR code and return as base64 encoded string.

    Args:
        data: Data to encode in QR code
        config: QR code configuration

    Returns:
        Base64 encoded PNG image (data URI format: data:image/png;base64,...)

    Raises:
        ImportError: If qrcode library is not installed
    """
    image_bytes, _ = generate_qr_code(data, config)
    base64_str = base64.b64encode(image_bytes).decode('utf-8')
    return f'data:image/png;base64,{base64_str}'


def generate_asset_qr_code(asset_code: str, qr_content: Optional[str] = None) -> Tuple[bytes, str]:
    """
    Generate QR code for an asset.

    Args:
        asset_code: Asset code to display on label
        qr_content: Content to encode in QR code (defaults to asset_code)

    Returns:
        Tuple of (image_bytes, image_format)
    """
    if qr_content is None:
        qr_content = asset_code

    config = QRCodeConfig(
        size=300,
        version=1,
        error_correction='M',
        box_size=10,
        border=4,
        show_text=True,
        font_size=14
    )

    return generate_qr_code(qr_content, config)


def generate_asset_qr_url(qr_code: str, base_url: str = '') -> str:
    """
    Generate QR code content URL for asset lookup.

    Args:
        qr_code: Asset's QR code UUID
        base_url: Base URL for the application

    Returns:
        Full URL for QR code scanning
    """
    return f'{base_url}/api/assets/lookup/?qr_code={qr_code}'


def validate_qr_data(data: str) -> bool:
    """
    Validate QR code data format.

    Args:
        data: QR code data to validate

    Returns:
        True if data is valid, False otherwise
    """
    if not data or not isinstance(data, str):
        return False

    # Check minimum length
    if len(data) < 4:
        return False

    # Add more validation rules as needed
    return True


def decode_qr_data(data: str) -> dict:
    """
    Decode QR code data into structured format.

    Supports formats:
    - Direct UUID: just the QR code UUID
    - URL format: extract QR code from URL parameter

    Args:
        data: Raw QR code data

    Returns:
        Dictionary with decoded data:
        {
            'qr_code': 'uuid',
            'type': 'uuid' | 'url',
            'valid': bool
        }
    """
    result = {
        'qr_code': None,
        'type': 'unknown',
        'valid': False
    }

    if not data:
        return result

    # Check if it's a URL format
    if 'qr_code=' in data:
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(data)
            params = parse_qs(parsed.query)
            if 'qr_code' in params:
                result['qr_code'] = params['qr_code'][0]
                result['type'] = 'url'
                result['valid'] = validate_qr_data(result['qr_code'])
        except Exception:
            pass
    else:
        # Direct UUID format
        result['qr_code'] = data
        result['type'] = 'uuid'
        result['valid'] = validate_qr_data(data)

    return result
