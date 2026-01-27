"""
Dynamic field validator for metadata-driven forms.

Validates data against FieldDefinition configurations.
"""
from typing import Dict, List, Any, Optional
from django.core.exceptions import ValidationError
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, date


class DynamicFieldValidator:
    """
    Validates field values based on FieldDefinition metadata.

    Usage:
        validator = DynamicFieldValidator(field_definitions)
        validator.validate(data)  # Raises ValidationError on failure
    """

    def __init__(self, field_definitions):
        """
        Initialize validator.

        Args:
            field_definitions: QuerySet or list of FieldDefinition instances
        """
        self.field_definitions = list(field_definitions)
        self._field_map = {fd.code: fd for fd in self.field_definitions}

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all fields in data.

        Args:
            data: Dict of field values to validate

        Returns:
            Validated and cleaned data

        Raises:
            ValidationError: If validation fails
        """
        errors = {}
        cleaned_data = {}

        for field_def in self.field_definitions:
            code = field_def.code
            value = data.get(code)

            try:
                cleaned_value = self._validate_field(field_def, value)
                if cleaned_value is not None or not field_def.is_required:
                    cleaned_data[code] = cleaned_value
            except ValidationError as e:
                errors[code] = e.messages if hasattr(e, 'messages') else [str(e)]

        if errors:
            raise ValidationError(errors)

        return cleaned_data

    def validate_field(self, field_code: str, value: Any) -> Any:
        """
        Validate a single field.

        Args:
            field_code: Field code
            value: Field value

        Returns:
            Cleaned value

        Raises:
            ValidationError: If validation fails
        """
        field_def = self._field_map.get(field_code)
        if not field_def:
            raise ValidationError(f"Unknown field: {field_code}")

        return self._validate_field(field_def, value)

    def _validate_field(self, field_def, value: Any) -> Any:
        """Validate single field against its definition."""
        field_type = field_def.field_type
        code = field_def.code

        # Required check
        if field_def.is_required:
            if value is None or value == '' or (isinstance(value, list) and len(value) == 0):
                raise ValidationError(f"{field_def.name} is required")

        # Skip validation for None/empty optional fields
        if value is None or value == '':
            return field_def.default_value

        # Type-specific validation
        validator_method = getattr(self, f'_validate_{field_type}', self._validate_default)
        cleaned_value = validator_method(field_def, value)

        # Regex validation
        if field_def.validation_regex:
            self._validate_regex(field_def, cleaned_value)

        # Custom expression validation
        if field_def.validation_expression:
            self._validate_expression(field_def, cleaned_value)

        # Unique validation (if applicable)
        if field_def.is_unique:
            self._validate_unique(field_def, cleaned_value)

        return cleaned_value

    def _validate_text(self, field_def, value: Any) -> str:
        """Validate text field."""
        value = str(value)

        if field_def.max_length and len(value) > field_def.max_length:
            raise ValidationError(
                f"{field_def.name} exceeds maximum length of {field_def.max_length}"
            )

        return value

    def _validate_textarea(self, field_def, value: Any) -> str:
        """Validate textarea field."""
        return self._validate_text(field_def, value)

    def _validate_number(self, field_def, value: Any) -> Decimal:
        """Validate decimal number field."""
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValidationError(f"{field_def.name} must be a valid number")

        if field_def.min_value is not None and decimal_value < Decimal(str(field_def.min_value)):
            raise ValidationError(
                f"{field_def.name} must be at least {field_def.min_value}"
            )

        if field_def.max_value is not None and decimal_value > Decimal(str(field_def.max_value)):
            raise ValidationError(
                f"{field_def.name} must be at most {field_def.max_value}"
            )

        return decimal_value

    def _validate_integer(self, field_def, value: Any) -> int:
        """Validate integer field."""
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_def.name} must be a valid integer")

        if field_def.min_value is not None and int_value < int(field_def.min_value):
            raise ValidationError(
                f"{field_def.name} must be at least {field_def.min_value}"
            )

        if field_def.max_value is not None and int_value > int(field_def.max_value):
            raise ValidationError(
                f"{field_def.name} must be at most {field_def.max_value}"
            )

        return int_value

    def _validate_float(self, field_def, value: Any) -> float:
        """Validate float field."""
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_def.name} must be a valid number")

        if field_def.min_value is not None and float_value < float(field_def.min_value):
            raise ValidationError(
                f"{field_def.name} must be at least {field_def.min_value}"
            )

        if field_def.max_value is not None and float_value > float(field_def.max_value):
            raise ValidationError(
                f"{field_def.name} must be at most {field_def.max_value}"
            )

        return float_value

    def _validate_boolean(self, field_def, value: Any) -> bool:
        """Validate boolean field."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes'):
                return True
            if value.lower() in ('false', '0', 'no'):
                return False
        raise ValidationError(f"{field_def.name} must be a boolean value")

    def _validate_date(self, field_def, value: Any) -> date:
        """Validate date field."""
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except ValueError:
                pass
        raise ValidationError(f"{field_def.name} must be a valid date (YYYY-MM-DD)")

    def _validate_datetime(self, field_def, value: Any) -> datetime:
        """Validate datetime field."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        raise ValidationError(f"{field_def.name} must be a valid datetime")

    def _validate_email(self, field_def, value: Any) -> str:
        """Validate email field."""
        value = str(value)
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, value):
            raise ValidationError(f"{field_def.name} must be a valid email address")
        return value

    def _validate_url(self, field_def, value: Any) -> str:
        """Validate URL field."""
        value = str(value)
        url_regex = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_regex, value, re.IGNORECASE):
            raise ValidationError(f"{field_def.name} must be a valid URL")
        return value

    def _validate_choice(self, field_def, value: Any) -> str:
        """Validate choice field."""
        value = str(value)
        options = field_def.options or {}

        valid_values = []
        if isinstance(options, dict):
            valid_values = list(options.keys())
        elif isinstance(options, list):
            valid_values = options

        if value not in valid_values:
            raise ValidationError(
                f"{field_def.name} must be one of: {', '.join(valid_values)}"
            )
        return value

    def _validate_multi_choice(self, field_def, value: Any) -> List[str]:
        """Validate multi-choice field."""
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list):
            raise ValidationError(f"{field_def.name} must be a list")

        options = field_def.options or {}
        valid_values = []
        if isinstance(options, dict):
            valid_values = list(options.keys())
        elif isinstance(options, list):
            valid_values = options

        for v in value:
            if str(v) not in valid_values:
                raise ValidationError(
                    f"{field_def.name} contains invalid value: {v}"
                )

        return [str(v) for v in value]

    def _validate_reference(self, field_def, value: Any) -> str:
        """Validate reference field (UUID)."""
        import uuid
        try:
            uuid.UUID(str(value))
            return str(value)
        except ValueError:
            raise ValidationError(f"{field_def.name} must be a valid UUID")

    def _validate_user(self, field_def, value: Any) -> str:
        """Validate user reference."""
        return self._validate_reference(field_def, value)

    def _validate_department(self, field_def, value: Any) -> str:
        """Validate department reference."""
        return self._validate_reference(field_def, value)

    def _validate_json(self, field_def, value: Any) -> Any:
        """Validate JSON field."""
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(f"{field_def.name} must be valid JSON")
        raise ValidationError(f"{field_def.name} must be a dict or list")

    def _validate_default(self, field_def, value: Any) -> Any:
        """Default validation (no type conversion)."""
        return value

    def _validate_regex(self, field_def, value: Any) -> None:
        """Validate against regex pattern."""
        if not isinstance(value, str):
            value = str(value)

        if not re.match(field_def.validation_regex, value):
            raise ValidationError(
                f"{field_def.name} does not match required pattern"
            )

    def _validate_expression(self, field_def, value: Any) -> None:
        """Validate against custom expression."""
        # Simple expression evaluation for validation
        # Supports: value > 0, value < 100, len(value) > 5, etc.
        try:
            from simpleeval import simple_eval
            result = simple_eval(
                field_def.validation_expression,
                names={'value': value}
            )
            if not result:
                raise ValidationError(
                    f"{field_def.name} failed validation: {field_def.validation_expression}"
                )
        except ImportError:
            # simpleeval not installed, skip expression validation
            pass
        except Exception as e:
            raise ValidationError(f"Validation expression error: {e}")

    def _validate_unique(self, field_def, value: Any) -> None:
        """Validate uniqueness (placeholder - implement with DB check)."""
        # This should be implemented with actual database lookup
        # For now, just a placeholder
        pass


def validate_dynamic_data(
    business_object_code: str,
    data: Dict[str, Any],
    exclude_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to validate data for a business object.

    Args:
        business_object_code: BusinessObject code
        data: Data to validate
        exclude_fields: Fields to skip validation

    Returns:
        Cleaned data

    Raises:
        ValidationError: If validation fails
    """
    from apps.system.models import BusinessObject

    try:
        business_object = BusinessObject.objects.get(
            code=business_object_code,
            is_active=True
        )
    except BusinessObject.DoesNotExist:
        raise ValidationError(f"BusinessObject '{business_object_code}' not found")

    field_definitions = business_object.field_definitions.filter(
        is_active=True
    )

    if exclude_fields:
        field_definitions = field_definitions.exclude(code__in=exclude_fields)

    validator = DynamicFieldValidator(field_definitions)
    return validator.validate(data)
