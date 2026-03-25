"""
Tests for Sprint 1 Task 2: Approval Field Permissions Enforcement.

Covers:
- FormPermissionService permission resolution, validation, and filtering
- Integration checks (imports, service init)
"""
import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.workflows.services.form_permission_service import FormPermissionService


class TestFormPermissionService(TestCase):
    """Unit tests for FormPermissionService."""

    def setUp(self):
        self.service = FormPermissionService()

        # Build a fake task with instance → definition chain
        self.task = MagicMock()
        self.task.pk = uuid.uuid4()
        self.task.node_id = 'node_review'
        self.task.instance = MagicMock()
        self.task.instance.definition = MagicMock()

    # --- get_permissions_for_task ---

    def test_returns_permissions_when_configured(self):
        """Should return normalised permissions for the task's node."""
        raw_perms = {'name': 'read_only', 'amount': 'editable', 'secret': 'hidden'}
        self.task.instance.definition.get_form_permissions_for_node.return_value = raw_perms

        result = self.service.get_permissions_for_task(self.task)
        self.assertEqual(result, raw_perms)
        self.task.instance.definition.get_form_permissions_for_node.assert_called_once_with('node_review')

    def test_returns_empty_dict_when_no_config(self):
        """Should return empty dict when no permissions configured for node."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {}
        result = self.service.get_permissions_for_task(self.task)
        self.assertEqual(result, {})

    def test_normalises_unknown_permission_levels(self):
        """Unknown permission values should fall back to DEFAULT_PERMISSION."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'name': 'bogus_level',
            'amount': 'editable',
        }
        result = self.service.get_permissions_for_task(self.task)
        self.assertEqual(result['name'], 'read_only')  # DEFAULT_PERMISSION
        self.assertEqual(result['amount'], 'editable')

    # --- validate_submission ---

    def test_validate_empty_submission_is_valid(self):
        """Empty submitted data should always be valid."""
        valid, violations = self.service.validate_submission(self.task, {})
        self.assertTrue(valid)
        self.assertEqual(violations, [])

    def test_validate_allows_editable_fields(self):
        """Writing to editable fields should pass validation."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'amount': 'editable',
        }
        valid, violations = self.service.validate_submission(
            self.task, {'amount': 500}
        )
        self.assertTrue(valid)
        self.assertEqual(violations, [])

    def test_validate_rejects_read_only_fields(self):
        """Writing to read_only fields should fail validation."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'name': 'read_only',
        }
        valid, violations = self.service.validate_submission(
            self.task, {'name': 'hacked_value'}
        )
        self.assertFalse(valid)
        self.assertEqual(len(violations), 1)
        self.assertIn('read_only', violations[0])

    def test_validate_rejects_hidden_fields(self):
        """Writing to hidden fields should fail validation."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'secret': 'hidden',
        }
        valid, violations = self.service.validate_submission(
            self.task, {'secret': 'leaked'}
        )
        self.assertFalse(valid)
        self.assertIn('hidden', violations[0])

    def test_validate_multiple_violations(self):
        """Multiple violations should all be reported."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'name': 'read_only',
            'secret': 'hidden',
            'amount': 'editable',
        }
        valid, violations = self.service.validate_submission(
            self.task, {'name': 'x', 'secret': 'y', 'amount': 100}
        )
        self.assertFalse(valid)
        self.assertEqual(len(violations), 2)

    # --- filter_response_data ---

    def test_filter_removes_hidden_fields(self):
        """Hidden fields should be stripped from response data."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {
            'name': 'read_only',
            'secret': 'hidden',
            'amount': 'editable',
        }
        result = self.service.filter_response_data(
            self.task, {'name': 'Test', 'secret': '123', 'amount': 500}
        )
        self.assertEqual(result, {'name': 'Test', 'amount': 500})
        self.assertNotIn('secret', result)

    def test_filter_keeps_all_when_no_permissions(self):
        """When no permission config exists, all fields should pass through."""
        self.task.instance.definition.get_form_permissions_for_node.return_value = {}
        data = {'a': 1, 'b': 2}
        result = self.service.filter_response_data(self.task, data)
        self.assertEqual(result, data)

    def test_filter_handles_empty_data(self):
        """Empty business data should pass through regardless."""
        result = self.service.filter_response_data(self.task, {})
        self.assertEqual(result, {})

    def test_filter_handles_none_data(self):
        """None business data should pass through."""
        result = self.service.filter_response_data(self.task, None)
        self.assertIsNone(result)


class TestFormPermissionServiceConstants(TestCase):
    """Verify service constants and defaults."""

    def test_permission_levels(self):
        """PERMISSION_LEVELS should have exactly 3 levels."""
        self.assertEqual(
            set(FormPermissionService.PERMISSION_LEVELS),
            {'hidden', 'read_only', 'editable'},
        )

    def test_default_permission_is_read_only(self):
        """Safe default should be read_only."""
        self.assertEqual(FormPermissionService.DEFAULT_PERMISSION, 'read_only')


class TestFormPermissionServiceImports(TestCase):
    """Verify imports work correctly."""

    def test_import_from_service_module(self):
        from apps.workflows.services.form_permission_service import FormPermissionService
        self.assertIsNotNone(FormPermissionService)

    def test_import_from_init(self):
        from apps.workflows.services import FormPermissionService
        self.assertIsNotNone(FormPermissionService)
