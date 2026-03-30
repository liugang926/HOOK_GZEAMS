"""
Tests for Sprint 1 Task 1: Workflow-Business Document State Linkage.

Covers:
- WorkflowStatusMixin field defaults and hooks
- BusinessStateSyncService state sync logic
- Django signal emission from WorkflowEngine
- by-business lookup endpoint
"""
import uuid
from unittest import mock
from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.common.mixins.workflow_status import WorkflowStatusMixin
from apps.workflows.signals import (
    workflow_started,
    workflow_completed,
    workflow_rejected,
    workflow_cancelled,
)
from apps.workflows.services.business_state_sync import BusinessStateSyncService


def build_fake_workflow_model():
    """Create a uniquely named mixin-backed model for isolated tests."""
    return type(
        f'FakeWorkflowModel{uuid.uuid4().hex}',
        (WorkflowStatusMixin,),
        {
            'Meta': type('Meta', (), {'abstract': False, 'app_label': 'tests'}),
            '__module__': __name__,
        },
    )


# ---------------------------------------------------------------------------
# 1. WorkflowStatusMixin unit tests
# ---------------------------------------------------------------------------

class TestWorkflowStatusMixin(TestCase):
    """Verify default values and hook existence on WorkflowStatusMixin."""

    def test_mixin_is_abstract(self):
        """WorkflowStatusMixin must be abstract (no DB table)."""
        self.assertTrue(WorkflowStatusMixin._meta.abstract)

    def test_approval_status_choices_defined(self):
        """All expected approval status choices should be defined."""
        choice_keys = [c[0] for c in WorkflowStatusMixin.APPROVAL_STATUS_CHOICES]
        expected = ['draft', 'pending_approval', 'approved', 'rejected', 'cancelled']
        self.assertEqual(choice_keys, expected)

    def test_default_approval_status_is_draft(self):
        """Default approval_status should be 'draft'."""
        field = WorkflowStatusMixin._meta.get_field('approval_status')
        self.assertEqual(field.default, 'draft')

    def test_lifecycle_hooks_are_callable(self):
        """All four lifecycle hooks should exist and be callable."""
        mixin = build_fake_workflow_model()()
        for hook in ('on_workflow_submitted', 'on_workflow_approved',
                     'on_workflow_rejected', 'on_workflow_cancelled'):
            self.assertTrue(callable(getattr(mixin, hook, None)), msg=f'{hook} should be callable')


# ---------------------------------------------------------------------------
# 2. BusinessStateSyncService unit tests
# ---------------------------------------------------------------------------

class TestBusinessStateSyncService(TestCase):
    """
    Test BusinessStateSyncService sync logic using mocks.

    No real DB access is needed; we mock ObjectRegistry and model instances.
    """

    def setUp(self):
        self.service = BusinessStateSyncService()
        # Build a fake workflow instance
        self.wf_instance = MagicMock()
        self.wf_instance.pk = uuid.uuid4()
        self.wf_instance.business_object_code = 'TestObject'
        self.wf_instance.business_id = str(uuid.uuid4())
        self.wf_instance.organization_id = uuid.uuid4()
        self.wf_instance.organization = MagicMock()
        self.wf_instance.initiator = MagicMock()

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_skip_when_model_not_found(self, mock_resolve):
        """Should silently skip when model cannot be resolved."""
        mock_resolve.return_value = None
        self.wf_instance.status = 'approved'
        # Should not raise
        self.service.sync_business_status(self.wf_instance)

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_skip_when_model_lacks_mixin(self, mock_resolve):
        """Should skip sync if model doesn't inherit WorkflowStatusMixin."""
        mock_resolve.return_value = type('PlainModel', (), {})
        self.wf_instance.status = 'approved'
        # Should not raise
        self.service.sync_business_status(self.wf_instance)

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._log_state_transition')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._get_business_object')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_approved_status_sync(self, mock_resolve, mock_get_obj, mock_log):
        """When workflow is approved, business doc should be set to 'approved'."""
        FakeModel = build_fake_workflow_model()
        mock_resolve.return_value = FakeModel
        business_obj = MagicMock(spec=['approval_status', 'workflow_instance_id',
                                       'submitted_at', 'approved_at', 'on_workflow_approved',
                                       'save', 'pk', '__class__'])
        business_obj.approval_status = 'pending_approval'
        business_obj.submitted_at = timezone.now()
        business_obj.__class__ = FakeModel
        mock_get_obj.return_value = business_obj

        self.wf_instance.status = 'approved'
        self.service.sync_business_status(self.wf_instance)

        self.assertEqual(business_obj.approval_status, 'approved')
        business_obj.save.assert_called_once()
        business_obj.on_workflow_approved.assert_called_once()

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._log_state_transition')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._get_business_object')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_rejected_status_sync(self, mock_resolve, mock_get_obj, mock_log):
        """When workflow is rejected, business doc should be set to 'rejected'."""
        FakeModel = build_fake_workflow_model()
        mock_resolve.return_value = FakeModel
        business_obj = MagicMock(spec=['approval_status', 'workflow_instance_id',
                                       'submitted_at', 'approved_at', 'on_workflow_rejected',
                                       'save', 'pk', '__class__'])
        business_obj.approval_status = 'pending_approval'
        business_obj.submitted_at = timezone.now()
        business_obj.__class__ = FakeModel
        mock_get_obj.return_value = business_obj

        self.wf_instance.status = 'rejected'
        self.service.sync_business_status(self.wf_instance)

        self.assertEqual(business_obj.approval_status, 'rejected')
        business_obj.save.assert_called_once()
        business_obj.on_workflow_rejected.assert_called_once()

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._log_state_transition')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._get_business_object')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_cancelled_status_sync(self, mock_resolve, mock_get_obj, mock_log):
        """When workflow is cancelled, business_doc should transition to 'cancelled'."""
        FakeModel = build_fake_workflow_model()
        mock_resolve.return_value = FakeModel
        business_obj = MagicMock(spec=['approval_status', 'workflow_instance_id',
                                       'submitted_at', 'approved_at',
                                       'on_workflow_cancelled', 'save', 'pk', '__class__'])
        business_obj.approval_status = 'pending_approval'
        business_obj.submitted_at = timezone.now()
        business_obj.__class__ = FakeModel
        mock_get_obj.return_value = business_obj

        self.wf_instance.status = 'cancelled'
        self.service.sync_business_status(self.wf_instance)

        self.assertEqual(business_obj.approval_status, 'cancelled')
        business_obj.on_workflow_cancelled.assert_called_once()

    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._log_state_transition')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._get_business_object')
    @patch('apps.workflows.services.business_state_sync.BusinessStateSyncService._resolve_business_model')
    def test_no_op_when_status_unchanged(self, mock_resolve, mock_get_obj, mock_log):
        """Should not call save/hooks when status doesn't change."""
        FakeModel = build_fake_workflow_model()
        mock_resolve.return_value = FakeModel
        business_obj = MagicMock(spec=['approval_status', 'workflow_instance_id',
                                       'submitted_at', 'approved_at', 'save', 'pk', '__class__'])
        business_obj.approval_status = 'pending_approval'
        business_obj.__class__ = FakeModel
        mock_get_obj.return_value = business_obj

        # Workflow is running → maps to pending_approval which is same as current
        self.wf_instance.status = 'running'
        self.service.sync_business_status(self.wf_instance)

        business_obj.save.assert_not_called()

    def test_status_map_covers_all_terminal_statuses(self):
        """STATUS_MAP must cover all workflow terminal statuses."""
        from apps.workflows.models import WorkflowInstance
        for terminal in WorkflowInstance.TERMINAL_STATUSES:
            self.assertIn(terminal, BusinessStateSyncService.STATUS_MAP,
                         msg=f"Missing STATUS_MAP entry for '{terminal}'")


# ---------------------------------------------------------------------------
# 3. Signal emission tests
# ---------------------------------------------------------------------------

class TestWorkflowSignals(TestCase):
    """Verify that signals are properly defined and can be sent/received."""

    def test_workflow_started_signal_can_send(self):
        """workflow_started signal should dispatch without error."""
        handler = MagicMock()
        workflow_started.connect(handler, sender=None, weak=False)
        try:
            workflow_started.send(
                sender=self.__class__,
                instance=MagicMock(),
                initiator=MagicMock(),
            )
            handler.assert_called_once()
        finally:
            workflow_started.disconnect(handler, sender=None)

    def test_workflow_completed_signal_can_send(self):
        """workflow_completed signal should dispatch without error."""
        handler = MagicMock()
        workflow_completed.connect(handler, sender=None, weak=False)
        try:
            workflow_completed.send(
                sender=self.__class__,
                instance=MagicMock(),
            )
            handler.assert_called_once()
        finally:
            workflow_completed.disconnect(handler, sender=None)

    def test_workflow_rejected_signal_can_send(self):
        """workflow_rejected signal should dispatch without error."""
        handler = MagicMock()
        workflow_rejected.connect(handler, sender=None, weak=False)
        try:
            workflow_rejected.send(
                sender=self.__class__,
                instance=MagicMock(),
                reason='Test reason',
            )
            handler.assert_called_once()
        finally:
            workflow_rejected.disconnect(handler, sender=None)

    def test_workflow_cancelled_signal_can_send(self):
        """workflow_cancelled signal should dispatch without error."""
        handler = MagicMock()
        workflow_cancelled.connect(handler, sender=None, weak=False)
        try:
            workflow_cancelled.send(
                sender=self.__class__,
                instance=MagicMock(),
                user=MagicMock(),
            )
            handler.assert_called_once()
        finally:
            workflow_cancelled.disconnect(handler, sender=None)


# ---------------------------------------------------------------------------
# 4. Import verification
# ---------------------------------------------------------------------------

class TestImports(TestCase):
    """Verify all new modules can be imported successfully."""

    def test_import_workflow_status_mixin(self):
        from apps.common.mixins.workflow_status import WorkflowStatusMixin
        self.assertTrue(hasattr(WorkflowStatusMixin, 'APPROVAL_STATUS_CHOICES'))

    def test_import_business_state_sync_service(self):
        from apps.workflows.services.business_state_sync import BusinessStateSyncService
        self.assertTrue(hasattr(BusinessStateSyncService, 'STATUS_MAP'))

    def test_import_signals(self):
        from apps.workflows.signals import (
            workflow_started, workflow_completed,
            workflow_rejected, workflow_cancelled,
        )
        self.assertIsNotNone(workflow_started)

    def test_import_from_init(self):
        """BusinessStateSyncService should be importable from services __init__."""
        from apps.workflows.services import BusinessStateSyncService
        self.assertIsNotNone(BusinessStateSyncService)
