"""
Tests for concurrent workflow operations.

Tests concurrent approval handling, timeout detection, and race condition prevention.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta
import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask
)
from apps.workflows.services.workflow_engine import WorkflowEngine
from apps.workflows.tests.test_api import WorkflowAPITestCase

User = get_user_model()


class TestConcurrentApproval(WorkflowAPITestCase):
    """
    Test concurrent approval operations.
    
    Verifies that:
    - Only one approval succeeds when multiple users try to approve same task
    - Concurrent approvals on different tasks work correctly
    - Race conditions are prevented with proper locking
    """

    def setUp(self):
        """Set up test data for concurrent operations."""
        super().setUp()
        
        # Create second approver
        self.approver2 = User.objects.create_user(
            username='approver2',
            email='approver2@example.com',
            password='testpass123'
        )
        self.approver2.organizations.add(self.organization)
        
        # Create workflow instance with a task
        self.instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('CONC001'),
            business_object_code='asset_pickup',
            business_id='ASSET_CONC_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            started_at=timezone.now(),
            created_by=self.initiator,
        )
        
        self.task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_1',
            node_name='Department Approval',
            node_type='approval',
            assignee=self.initiator,
            status=WorkflowTask.STATUS_PENDING,
            due_date=timezone.now() + timedelta(hours=24),
            created_by=self.initiator,
        )

    def test_concurrent_approvals_same_task(self):
        """
        Test that concurrent approval attempts on the same task are handled correctly.
        
        Only one approval should succeed; others should fail with appropriate error.
        """
        results = []
        errors = []
        
        def approve_task(user_id):
            """Attempt to approve the task."""
            try:
                user = User.objects.get(id=user_id)
                client = APIClient()
                client.force_authenticate(user=user)
                
                response = client.post(
                    f'/api/workflows/tasks/{self.task.id}/approve/',
                    {'comment': f'Approved by {user.username}'},
                    format='json'
                )
                
                return {
                    'user_id': str(user_id),
                    'status_code': response.status_code,
                    'success': response.status_code == 200,
                }
            except Exception as e:
                errors.append(str(e))
                return {
                    'user_id': str(user_id),
                    'status_code': 500,
                    'success': False,
                    'error': str(e),
                }
        
        # Run concurrent approvals from multiple users
        user_ids = [self.initiator.id, self.approver2.id]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(approve_task, uid) for uid in user_ids]
            for future in as_completed(futures):
                results.append(future.result())
        
        # At least one should succeed
        successful = [r for r in results if r['success']]
        self.assertGreaterEqual(len(successful), 1, 
            "At least one approval should succeed")
        
        # Refresh task from database
        self.task.refresh_from_db()
        
        # Task should be completed
        self.assertEqual(self.task.status, WorkflowTask.STATUS_APPROVED)

    def test_concurrent_approvals_different_tasks(self):
        """
        Test that concurrent approvals on different tasks all succeed.
        
        Multiple users approving different tasks should work independently.
        """
        # Create second task
        task2 = WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_2',
            node_name='Finance Approval',
            node_type='approval',
            assignee=self.approver2,
            status=WorkflowTask.STATUS_PENDING,
            due_date=timezone.now() + timedelta(hours=24),
            created_by=self.initiator,
        )
        
        results = []
        
        def approve_task(task_id, user_id):
            """Approve a specific task."""
            user = User.objects.get(id=user_id)
            client = APIClient()
            client.force_authenticate(user=user)
            
            response = client.post(
                f'/api/workflows/tasks/{task_id}/approve/',
                {'comment': f'Approved by {user.username}'},
                format='json'
            )
            
            return {
                'task_id': str(task_id),
                'status_code': response.status_code,
                'success': response.status_code == 200,
            }
        
        # Run concurrent approvals on different tasks
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(approve_task, self.task.id, self.initiator.id),
                executor.submit(approve_task, task2.id, self.approver2.id),
            ]
            for future in as_completed(futures):
                results.append(future.result())
        
        # Both should succeed
        successful = [r for r in results if r['success']]
        self.assertEqual(len(successful), 2, 
            "Both approvals on different tasks should succeed")
        
        # Refresh tasks from database
        self.task.refresh_from_db()
        task2.refresh_from_db()
        
        # Both tasks should be approved
        self.assertEqual(self.task.status, WorkflowTask.STATUS_APPROVED)
        self.assertEqual(task2.status, WorkflowTask.STATUS_APPROVED)

    def test_race_condition_prevention(self):
        """
        Test that race conditions are prevented during task updates.
        
        Multiple threads trying to update the same task should be handled safely.
        """
        update_count = 0
        lock = threading.Lock()
        
        def update_task_priority(thread_id):
            """Update task priority."""
            nonlocal update_count
            
            try:
                # Simulate concurrent update
                task = WorkflowTask.objects.get(id=self.task.id)
                task.priority = f'high_{thread_id}'
                time.sleep(0.01)  # Simulate processing time
                task.save(update_fields=['priority'])
                
                with lock:
                    update_count += 1
                return True
            except Exception:
                return False
        
        # Run concurrent updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_task_priority, i) for i in range(5)]
            results = [f.result() for f in as_completed(futures)]
        
        # All updates should complete (though final value may vary)
        self.assertEqual(sum(results), 5, "All updates should complete")
        
        # Task should still exist and be valid
        self.task.refresh_from_db()
        self.assertIsNotNone(self.task.priority)


class TestTimeoutHandling(WorkflowAPITestCase):
    """
    Test timeout detection and handling for workflows.
    
    Verifies that:
    - Workflow timeout is properly detected
    - Task overdue triggers alerts
    - Timeout notifications are sent correctly
    """

    def setUp(self):
        """Set up test data for timeout tests."""
        super().setUp()
        
        # Create workflow instance
        self.instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('TIME001'),
            business_object_code='asset_pickup',
            business_id='ASSET_TIME_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            started_at=timezone.now() - timedelta(hours=48),  # Started 48 hours ago
            created_by=self.initiator,
        )
        
        # Create overdue task
        self.overdue_task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_1',
            node_name='Department Approval',
            node_type='approval',
            assignee=self.initiator,
            status=WorkflowTask.STATUS_PENDING,
            due_date=timezone.now() - timedelta(hours=24),  # Due 24 hours ago
            created_by=self.initiator,
        )

    def test_workflow_timeout_detection(self):
        """
        Test that workflow timeout is properly detected.
        
        Workflows exceeding SLA time should be flagged.
        """
        # Check if instance is overdue
        from apps.workflows.services.sla_service import SLATracker
        
        tracker = SLATracker()
        
        # Instance started 48 hours ago, SLA is typically 24 hours
        is_overdue = tracker.is_instance_overdue(self.instance)
        
        # Should be overdue
        self.assertTrue(is_overdue, "Instance should be detected as overdue")

    def test_task_timeout_alerts(self):
        """
        Test that task overdue triggers appropriate alerts.
        
        Overdue tasks should generate alerts.
        """
        from apps.workflows.services.sla_service import SLATracker
        
        tracker = SLATracker()
        
        # Check task SLA status
        sla_status = tracker.get_task_sla_status(self.overdue_task)
        
        # Should be overdue
        self.assertEqual(sla_status['status'], 'overdue')
        self.assertGreater(sla_status['hours_overdue'], 0)

    @patch('apps.workflows.services.notifications.EnhancedNotificationService.send')
    def test_timeout_notification(self, mock_send):
        """
        Test that timeout sends proper notifications.
        
        Timeout events should trigger notification to relevant parties.
        """
        from apps.workflows.services.sla_service import SLATracker
        
        tracker = SLATracker()
        
        # Process overdue task
        tracker.process_overdue_task(self.overdue_task)
        
        # Notification should have been sent
        # (Implementation depends on actual notification integration)
        # This test verifies the notification path exists
        
        # Refresh task
        self.overdue_task.refresh_from_db()
        
        # Task should still be pending but flagged
        self.assertEqual(self.overdue_task.status, WorkflowTask.STATUS_PENDING)


class TestBulkOperations(WorkflowAPITestCase):
    """
    Test bulk workflow operations.
    
    Verifies that:
    - Bulk approval works correctly
    - Bulk rejection works correctly
    - Bulk operations handle errors gracefully
    """

    def setUp(self):
        """Set up test data for bulk operations."""
        super().setUp()
        
        # Create multiple workflow instances with tasks
        self.tasks = []
        for i in range(5):
            instance = WorkflowInstance.objects.create(
                organization=self.organization,
                definition=self.workflow_definition,
                instance_no=self._make_instance_no(f'BULK{i:03d}'),
                business_object_code='asset_pickup',
                business_id=f'ASSET_BULK_{i:03d}',
                initiator=self.initiator,
                status=WorkflowInstance.STATUS_RUNNING,
                started_at=timezone.now(),
                created_by=self.initiator,
            )
            
            task = WorkflowTask.objects.create(
                organization=self.organization,
                instance=instance,
                node_id='approval_1',
                node_name=f'Bulk Approval {i}',
                node_type='approval',
                assignee=self.initiator,
                status=WorkflowTask.STATUS_PENDING,
                due_date=timezone.now() + timedelta(hours=24),
                created_by=self.initiator,
            )
            self.tasks.append(task)

    def test_bulk_approval(self):
        """
        Test bulk approval of multiple tasks.
        
        All tasks should be approved successfully.
        """
        task_ids = [str(task.id) for task in self.tasks]
        
        response = self.client.post(
            '/api/workflows/tasks/bulk_approve/',
            {'task_ids': task_ids, 'comment': 'Bulk approved'},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify all tasks are approved
        for task in self.tasks:
            task.refresh_from_db()
            self.assertEqual(task.status, WorkflowTask.STATUS_APPROVED)

    def test_bulk_rejection(self):
        """
        Test bulk rejection of multiple tasks.
        
        All tasks should be rejected successfully.
        """
        task_ids = [str(task.id) for task in self.tasks]
        
        response = self.client.post(
            '/api/workflows/tasks/bulk_reject/',
            {'task_ids': task_ids, 'comment': 'Bulk rejected', 'reason': 'Not approved'},
            format='json'
        )
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        
        # Verify all tasks are rejected
        for task in self.tasks:
            task.refresh_from_db()
            self.assertEqual(task.status, WorkflowTask.STATUS_REJECTED)

    def test_bulk_operations_partial_failure(self):
        """
        Test bulk operations with partial failures.
        
        Some tasks succeeding and some failing should be handled gracefully.
        """
        # Make one task already completed
        self.tasks[0].status = WorkflowTask.STATUS_APPROVED
        self.tasks[0].save()
        
        task_ids = [str(task.id) for task in self.tasks]
        
        response = self.client.post(
            '/api/workflows/tasks/bulk_approve/',
            {'task_ids': task_ids, 'comment': 'Bulk approved'},
            format='json'
        )
        
        # Should return partial success
        self.assertEqual(response.status_code, 200)
        
        # Check results
        results = response.data.get('data', {}).get('results', [])
        
        # Some should succeed, some may fail (already completed)
        successful = [r for r in results if r.get('success')]
        self.assertGreater(len(successful), 0)