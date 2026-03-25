"""
QR Code Generator Utility.

Provides QR code generation and validation for asset inventory.
"""
import hashlib
import json
from io import BytesIO
from typing import Dict, Tuple, Optional

from django.conf import settings


class QRCodeGenerator:
    """
    QR Code Generator for asset inventory.

    Generates QR codes containing asset information with MD5 checksum.
    Format: {"type":"asset","version":"1.0","asset_id":...,"asset_code":...,"org_id":...,"checksum":...}
    """

    # QR code format version
    VERSION = "1.0"
    TYPE_ASSET = "asset"

    def generate_asset_qr_data(self, asset_id: str, asset_code: str, org_id: str) -> str:
        """
        Generate QR code data content for an asset.

        Args:
            asset_id: Asset UUID
            asset_code: Asset code
            org_id: Organization ID

        Returns:
            JSON string containing asset QR code data
        """
        # Calculate checksum
        checksum = self._calculate_checksum(asset_id, asset_code, org_id)

        # Build QR code data
        qr_data = {
            "type": self.TYPE_ASSET,
            "version": self.VERSION,
            "asset_id": asset_id,
            "asset_code": asset_code,
            "org_id": org_id,
            "checksum": checksum
        }

        return json.dumps(qr_data)

    def parse_qr_code(self, qr_content: str) -> Dict:
        """
        Parse QR code string and return data dictionary.

        Args:
            qr_content: QR code content (JSON or string format)

        Returns:
            Parsed QR code data dictionary

        Raises:
            ValueError: If QR code format is invalid
        """
        # Try to parse as JSON first
        try:
            return json.loads(qr_content)
        except json.JSONDecodeError:
            # Try to parse as string format: ASSET|asset_code|org_id|checksum
            parts = qr_content.split('|')
            if len(parts) == 4 and parts[0] == 'ASSET':
                return {
                    "type": "asset",
                    "asset_code": parts[1],
                    "org_id": parts[2],
                    "checksum": parts[3]
                }
            else:
                raise ValueError("Invalid QR code format")

    def generate_asset_qr_code(self, asset_id: str, asset_code: str, org_id: str) -> str:
        """
        Generate QR code string for an asset.

        This is a simplified version that generates a string QR code.
        For actual QR image generation, use qrcode library.

        Args:
            asset_id: Asset UUID
            asset_code: Asset code
            org_id: Organization ID

        Returns:
            QR code string (compact format: ASSET|asset_code|checksum)
        """
        checksum = self._calculate_checksum(asset_id, asset_code, org_id)
        return f"ASSET|{asset_code}|{org_id}|{checksum}"

    def validate_qr_code(self, qr_content: str, asset_code: str = None, org_id: str = None) -> Tuple[bool, str, Dict]:
        """
        Validate QR code content and checksum.

        Args:
            qr_content: QR code content (JSON or string format)
            asset_code: Expected asset code (optional)
            org_id: Expected organization ID (optional)

        Returns:
            Tuple of (is_valid, error_message, qr_data_dict)
        """
        qr_data = None

        # Try to parse as JSON first
        try:
            qr_data = json.loads(qr_content)
        except json.JSONDecodeError:
            # Try to parse as string format: ASSET|asset_code|org_id|checksum
            parts = qr_content.split('|')
            if len(parts) == 4 and parts[0] == 'ASSET':
                qr_data = {
                    "type": "asset",
                    "asset_code": parts[1],
                    "org_id": parts[2],
                    "checksum": parts[3]
                }
            else:
                return False, "Invalid QR code format", {}

        # Validate QR data structure
        if not qr_data:
            return False, "Empty QR code data", {}

        if qr_data.get("type") != self.TYPE_ASSET:
            return False, "Invalid QR code type", {}

        # Extract fields
        extracted_asset_id = qr_data.get("asset_id")
        extracted_asset_code = qr_data.get("asset_code")
        extracted_org_id = qr_data.get("org_id")
        extracted_checksum = qr_data.get("checksum")

        if not all([extracted_asset_code, extracted_org_id, extracted_checksum]):
            return False, "Missing required fields in QR code", qr_data

        # Verify asset code matches if provided
        if asset_code and extracted_asset_code != asset_code:
            return False, f"Asset code mismatch: expected {asset_code}, got {extracted_asset_code}", qr_data

        # Verify org ID matches if provided
        if org_id and extracted_org_id != org_id:
            return False, f"Organization ID mismatch: expected {org_id}, got {extracted_org_id}", qr_data

        # Verify checksum
        if extracted_asset_id:
            expected_checksum = self._calculate_checksum(
                extracted_asset_id,
                extracted_asset_code,
                extracted_org_id
            )
        else:
            # For string format without asset_id, use different calculation
            expected_checksum = self._calculate_checksum_simple(
                extracted_asset_code,
                extracted_org_id
            )

        if expected_checksum != extracted_checksum:
            return False, f"Checksum mismatch: expected {expected_checksum}, got {extracted_checksum}", qr_data

        return True, "Valid", qr_data

    def _calculate_checksum(self, asset_id: str, asset_code: str, org_id: str) -> str:
        """
        Calculate MD5 checksum for QR code data.

        Args:
            asset_id: Asset UUID
            asset_code: Asset code
            org_id: Organization ID

        Returns:
            First 8 characters of MD5 hash
        """
        data = f"{asset_id}:{asset_code}:{org_id}"
        return hashlib.md5(data.encode()).hexdigest()[:8]

    def _calculate_checksum_simple(self, asset_code: str, org_id: str) -> str:
        """
        Calculate checksum for string format (without asset_id).

        Args:
            asset_code: Asset code
            org_id: Organization ID

        Returns:
            First 8 characters of MD5 hash
        """
        data = f"{asset_code}:{org_id}"
        return hashlib.md5(data.encode()).hexdigest()[:8]

    def parse_qr_from_scan(self, scan_result: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Parse QR code from scan result.

        Args:
            scan_result: Raw scan result string

        Returns:
            Tuple of (is_valid, error_message, qr_data_dict)
        """
        return self.validate_qr_code(scan_result)

    def build_qr_url(self, asset_code: str) -> str:
        """
        Build QR code URL for accessing asset details.

        Args:
            asset_code: Asset code

        Returns:
            URL string for asset detail access
        """
        base_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
        return f"{base_url}/assets/{asset_code}"


class QRCodeImageGenerator:
    """
    QR Code Image Generator.

    Generates QR code images using qrcode library.
    This is a placeholder - actual implementation requires qrcode library.
    """

    def generate_image(self, data: str, size: int = 300) -> Optional[bytes]:
        """
        Generate QR code image as PNG bytes.

        Args:
            data: QR code content
            size: Image size in pixels

        Returns:
            PNG image bytes or None if qrcode library not available
        """
        try:
            import qrcode
            from qrcode.image.styledpil import StyledPilImage

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Resize to requested size
            img = img.resize((size, size))

            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return buffer.read()

        except ImportError:
            # qrcode library not available
            return None
        except Exception as e:
            # Error generating image
            return None

    def generate_base64(self, data: str, size: int = 300) -> Optional[str]:
        """
        Generate QR code image as base64 data URL.

        Args:
            data: QR code content
            size: Image size in pixels

        Returns:
            Data URL string or None if generation failed
        """
        import base64

        image_bytes = self.generate_image(data, size)
        if image_bytes:
            return f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        return None
