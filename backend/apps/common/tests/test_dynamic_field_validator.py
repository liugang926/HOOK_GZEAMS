"""
Tests for DynamicFieldValidator reference field handling.
"""
import uuid
from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError

from apps.common.validators.dynamic_field import DynamicFieldValidator


class TestDynamicFieldValidatorReference:
    """Reference field validation behavior."""

    def setup_method(self):
        self.validator = DynamicFieldValidator([])
        self.field_def = SimpleNamespace(name='Supplier')

    def test_validate_reference_accepts_dict_with_id(self):
        """Validator should extract ID when payload is an expanded dict."""
        ref_id = str(uuid.uuid4())
        result = self.validator._validate_reference(self.field_def, {'id': ref_id, 'name': 'ACME'})
        assert result == ref_id

    def test_validate_reference_accepts_object_with_id_attr(self):
        """Validator should extract ID when payload is an object with id."""
        ref_id = str(uuid.uuid4())
        payload = SimpleNamespace(id=ref_id, name='ACME')
        result = self.validator._validate_reference(self.field_def, payload)
        assert result == ref_id

    def test_validate_reference_rejects_invalid_id(self):
        """Validator should raise a clear UUID error for invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator._validate_reference(self.field_def, {'id': 'not-a-uuid'})
        assert 'must be a valid UUID' in str(exc_info.value)
