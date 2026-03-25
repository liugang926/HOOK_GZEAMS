"""
Input Validation Service.

Comprehensive input validation and sanitization for security.
Prevents injection attacks, XSS, and other common vulnerabilities.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from django.core.exceptions import ValidationError
from django.conf import settings
import html

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Centralized input validation service.
    
    Provides:
    - Field validation
    - SQL injection prevention
    - XSS prevention
    - File upload validation
    - Data sanitization
    """
    
    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bunion\b.*\bselect\b)",
        r"(\bselect\b.*\bfrom\b)",
        r"(\bdrop\b.*\btable\b)",
        r"(\bdelete\b.*\bfrom\b)",
        r"(\binsert\b.*\binto\b)",
        r"(\bupdate\b.*\bset\b)",
        r"(\bexec\b|\bexecute\b)",
        r"(--|;|/\*|\*/)",
        r"(\bor\b.*=.*\bor\b)",
        r"(\band\b.*=.*\band\b)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
        r"onload\s*=",
        r"onerror\s*="
    ]
    
    def __init__(self):
        self.max_string_length = getattr(settings, 'MAX_STRING_LENGTH', 10000)
        self.max_list_length = getattr(settings, 'MAX_LIST_LENGTH', 1000)
        self.max_dict_depth = getattr(settings, 'MAX_DICT_DEPTH', 10)
    
    def validate_string(self, value: str, field_name: str = "field", 
                       min_length: int = 0, max_length: int = None,
                       pattern: str = None, allow_empty: bool = False) -> str:
        """
        Validate and sanitize string input.
        
        Args:
            value: Input string
            field_name: Name of the field for error messages
            min_length: Minimum allowed length
            max_length: Maximum allowed length
            pattern: Regex pattern to match
            allow_empty: Whether empty strings are allowed
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If validation fails
        """
        if value is None:
            if allow_empty:
                return ""
            raise ValidationError(f"{field_name} is required")
        
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        # Trim whitespace
        value = value.strip()
        
        # Check if empty
        if not value:
            if allow_empty:
                return ""
            raise ValidationError(f"{field_name} cannot be empty")
        
        # Check length
        actual_max = max_length or self.max_string_length
        if len(value) > actual_max:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {actual_max} characters"
            )
        
        if len(value) < min_length:
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters"
            )
        
        # Check pattern if provided
        if pattern and not re.match(pattern, value):
            raise ValidationError(f"{field_name} format is invalid")
        
        # Sanitize against XSS
        value = self.sanitize_html(value)
        
        return value
    
    def validate_email(self, email: str, field_name: str = "email") -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(email_pattern, email):
            raise ValidationError(f"{field_name} format is invalid")
        
        return email.lower().strip()
    
    def validate_integer(self, value: Any, field_name: str = "field",
                        min_value: int = None, max_value: int = None) -> int:
        """Validate integer input."""
        if value is None:
            raise ValidationError(f"{field_name} is required")
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be an integer")
        
        if min_value is not None and int_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and int_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}"
            )
        
        return int_value
    
    def validate_float(self, value: Any, field_name: str = "field",
                      min_value: float = None, max_value: float = None) -> float:
        """Validate float input."""
        if value is None:
            raise ValidationError(f"{field_name} is required")
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a number")
        
        if min_value is not None and float_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}"
            )
        
        if max_value is not None and float_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}"
            )
        
        return float_value
    
    def validate_boolean(self, value: Any, field_name: str = "field") -> bool:
        """Validate boolean input."""
        if value is None:
            raise ValidationError(f"{field_name} is required")
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            if value.lower() in ['true', '1', 'yes']:
                return True
            elif value.lower() in ['false', '0', 'no']:
                return False
        
        raise ValidationError(f"{field_name} must be a boolean value")
    
    def validate_list(self, value: Any, field_name: str = "field",
                     item_type: type = None, max_length: int = None) -> list:
        """Validate list input."""
        if value is None:
            raise ValidationError(f"{field_name} is required")
        
        if not isinstance(value, list):
            raise ValidationError(f"{field_name} must be a list")
        
        actual_max = max_length or self.max_list_length
        if len(value) > actual_max:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {actual_max} items"
            )
        
        # Validate items if type specified
        if item_type:
            for i, item in enumerate(value):
                if not isinstance(item, item_type):
                    raise ValidationError(
                        f"{field_name}[{i}] must be of type {item_type.__name__}"
                    )
        
        return value
    
    def validate_dict(self, value: Any, field_name: str = "field",
                     max_depth: int = None, required_keys: List[str] = None) -> dict:
        """Validate dictionary input."""
        if value is None:
            raise ValidationError(f"{field_name} is required")
        
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name} must be a dictionary")
        
        # Check required keys
        if required_keys:
            missing_keys = set(required_keys) - set(value.keys())
            if missing_keys:
                raise ValidationError(
                    f"{field_name} missing required keys: {', '.join(missing_keys)}"
                )
        
        # Check depth
        actual_max = max_depth or self.max_dict_depth
        depth = self._get_dict_depth(value)
        if depth > actual_max:
            raise ValidationError(
                f"{field_name} exceeds maximum depth of {actual_max}"
            )
        
        return value
    
    def _get_dict_depth(self, d: dict) -> int:
        """Calculate maximum depth of nested dictionary."""
        if not isinstance(d, dict) or not d:
            return 0
        return 1 + max(self._get_dict_depth(v) for v in d.values())
    
    def sanitize_html(self, value: str) -> str:
        """Sanitize HTML to prevent XSS attacks."""
        # Escape HTML special characters
        return html.escape(value, quote=True)
    
    def check_sql_injection(self, value: str) -> bool:
        """
        Check for potential SQL injection patterns.
        
        Returns:
            True if injection detected, False otherwise
        """
        value_lower = value.lower()
        
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower):
                logger.warning(f"SQL injection pattern detected: {pattern}")
                return True
        
        return False
    
    def check_xss(self, value: str) -> bool:
        """
        Check for potential XSS patterns.
        
        Returns:
            True if XSS detected, False otherwise
        """
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"XSS pattern detected: {pattern}")
                return True
        
        return False
    
    def validate_workflow_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate workflow submission input.
        
        Args:
            data: Workflow submission data
            
        Returns:
            Validated and sanitized data
            
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        
        # Validate required fields
        if 'definition_code' in data:
            validated['definition_code'] = self.validate_string(
                data['definition_code'],
                'definition_code',
                min_length=1,
                max_length=100,
                pattern=r'^[a-zA-Z0-9_-]+$'
            )
        
        if 'business_object_code' in data:
            validated['business_object_code'] = self.validate_string(
                data['business_object_code'],
                'business_object_code',
                min_length=1,
                max_length=100
            )
        
        if 'business_id' in data:
            validated['business_id'] = self.validate_string(
                data['business_id'],
                'business_id',
                min_length=1,
                max_length=100
            )
        
        if 'variables' in data:
            validated['variables'] = self.validate_dict(
                data['variables'],
                'variables',
                max_depth=3
            )
        
        return validated
    
    def validate_file_upload(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate file upload input.
        
        Args:
            file_data: File upload data
            
        Returns:
            Validated file data
            
        Raises:
            ValidationError: If validation fails
        """
        validated = {}
        
        # Allowed file types
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx'}
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        
        if 'filename' not in file_data:
            raise ValidationError("Filename is required")
        
        filename = self.validate_string(
            file_data['filename'],
            'filename',
            max_length=255
        )
        
        # Check file extension
        import os
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise ValidationError(f"File type {file_ext} not allowed")
        
        validated['filename'] = filename
        
        if 'size' in file_data:
            size = self.validate_integer(
                file_data['size'],
                'file size',
                min_value=0,
                max_value=MAX_FILE_SIZE
            )
            validated['size'] = size
        
        if 'content_type' in file_data:
            validated['content_type'] = self.validate_string(
                file_data['content_type'],
                'content type',
                max_length=100
            )
        
        return validated


# Global validator instance
input_validator = InputValidator()


def validate_string(value: str, field_name: str = "field", **kwargs) -> str:
    """Validate string using global validator."""
    return input_validator.validate_string(value, field_name, **kwargs)


def validate_email(email: str, field_name: str = "email") -> str:
    """Validate email using global validator."""
    return input_validator.validate_email(email, field_name)


def validate_integer(value: Any, field_name: str = "field", **kwargs) -> int:
    """Validate integer using global validator."""
    return input_validator.validate_integer(value, field_name, **kwargs)


def sanitize_html(value: str) -> str:
    """Sanitize HTML using global validator."""
    return input_validator.sanitize_html(value)


def check_sql_injection(value: str) -> bool:
    """Check for SQL injection using global validator."""
    return input_validator.check_sql_injection(value)


def check_xss(value: str) -> bool:
    """Check for XSS using global validator."""
    return input_validator.check_xss(value)


def validate_workflow_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate workflow input using global validator."""
    return input_validator.validate_workflow_input(data)