"""
API Integration Tests for Workflow Execution Engine.

Tests the REST API endpoints for workflow instances, tasks, and statistics.
"""
import uuid
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowApproval
)
from apps.organizations.models import Organization, Department, UserDepartment
from apps.accounts.models import User, UserOrganization

import json

User = get_user_model()


class WorkflowAPITestCase(TestCase):
    """Base test case for workflow API tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        import time
        self.client = APIClient()
        # Use timestamp + UUID for guaranteed uniqueness across test runs
        self.unique_suffix = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"

        # Create organization
        self.organization = Organization.objects.create(
            code=f'TEST_ORG_{self.unique_suffix}',
            name=f'Test Organization {self.unique_suffix}',
            org_type='company',
            is_active=True
        )

        # Create department
        self.department = Department.objects.create(
            code=f'TEST_DEPT_{self.unique_suffix}',
            organization=self.organization,
            name='Test Department'
        )

        # Create users
        self.admin_user = User.objects.create_user(
            username=f'admin_{self.unique_suffix}',
            email=f'admin{self.unique_suffix}@test.com',
            is_staff=True,
            is_superuser=True,
            is_active=True
        )
        self.admin_user.current_organization = self.organization
        self.admin_user.save()

        UserOrganization.objects.create(
            user=self.admin_user,
            organization=self.organization,
            role='admin',
            is_primary=True
        )

        # Create regular users
        self.initiator = User.objects.create_user(
            username=f'initiator_{self.unique_suffix}',
            email=f'initiator{self.unique_suffix}@test.com',
            is_active=True
        )
        self.initiator.current_organization = self.organization
        self.initiator.save()

        UserOrganization.objects.create(
            user=self.initiator,
            organization=self.organization,
            role='member',
            is_primary=True
        )
        UserDepartment.objects.create(
            user=self.initiator,
            organization=self.organization,
            department=self.department,
            is_primary=True
        )

        self.approver = User.objects.create_user(
            username=f'approver_{self.unique_suffix}',
            email=f'approver{self.unique_suffix}@test.com',
            is_active=True
        )
        self.approver.current_organization = self.organization
        self.approver.save()

        UserOrganization.objects.create(
            user=self.approver,
            organization=self.organization,
            role='admin',
            is_primary=True
        )
        UserDepartment.objects.create(
            user=self.approver,
            organization=self.organization,
            department=self.department,
            is_primary=True
        )

        # Simple workflow graph data
        self.simple_graph_data = {
            'nodes': [
                {
                    'id': 'start_1',
                    'type': 'start',
                    'x': 100,
                    'y': 100,
                    'text': 'Start'
                },
                {
                    'id': 'approval_1',
                    'type': 'approval',
                    'x': 300,
                    'y': 100,
                    'text': 'Department Approval',
                    'properties': {
                        'approveType': 'or',
                        'approvers': [
                            {'type': 'user', 'user_id': str(self.approver.id)}
                        ],
                        'timeout': 72
                    }
                },
                {
                    'id': 'end_1',
                    'type': 'end',
                    'x': 500,
                    'y': 100,
                    'text': 'End'
                }
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1'},
                {'id': 'edge_2', 'sourceNodeId': 'approval_1', 'targetNodeId': 'end_1'}
            ]
        }

        # Create published workflow definition
        self.workflow_definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code=f'simple_approval_{self.unique_suffix}',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.admin_user
        )

    def tearDown(self):
        """Clean up thread-local organization context after each test."""
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        super().tearDown()

    def _authenticate_with_org(self, user):
        """Authenticate user and set organization header."""
        self.client.force_authenticate(user=user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.organization.id))
        # Verify credentials were set

    def _make_instance_no(self, suffix=''):
        """Generate unique instance_no for test data."""
        unique_part = uuid.uuid4().hex[:6].upper()
        return f'TEST-{unique_part}{suffix}'


class WorkflowInstanceAPITest(WorkflowAPITestCase):
    """Tests for WorkflowInstance API endpoints."""

    def setUp(self):
        """Set up additional test data."""
        super().setUp()
        self._authenticate_with_org(self.initiator)

    def test_start_workflow_success(self):
        """Test starting a workflow via API."""
        url = '/api/workflows/instances/start/'
        data = {
            'definition_id': str(self.workflow_definition.id),
            'business_object_code': 'asset_pickup',
            'business_id': 'ASSET_001',
            'business_no': 'LY-2024-001',
            'variables': {'amount': 5000, 'reason': 'Need equipment'},
            'title': 'Asset Pickup Request',
            'priority': 'normal'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('data', response.data)

        # Verify instance was created
        instance_id = response.data['data']['id']
        instance = WorkflowInstance.objects.get(id=instance_id)
        self.assertEqual(instance.status, WorkflowInstance.STATUS_PENDING_APPROVAL)
        self.assertEqual(instance.business_no, 'LY-2024-001')

    def test_start_workflow_unpublished_definition_fails(self):
        """Test starting workflow with unpublished definition fails."""
        # Create unpublished definition
        unpublished_def = WorkflowDefinition.objects.create(
            organization=self.organization,
            code=f'unpublished_{uuid.uuid4().hex[:8]}',
            name='Unpublished Workflow',
            business_object_code='asset_pickup',
            status='draft',
            graph_data=self.simple_graph_data,
            created_by=self.admin_user
        )

        url = '/api/workflows/instances/start/'
        data = {
            'definition_id': str(unpublished_def.id),
            'business_object_code': 'asset_pickup',
            'business_id': 'ASSET_001',
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_list_my_instances(self):
        """Test listing current user's instances."""
        # Create an instance
        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        url = '/api/workflows/instances/my_instances/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertGreater(len(response.data['data']), 0)

    def test_list_instances_filters_by_status(self):
        """Test listing instances with status filter."""
        # Create instances with different statuses
        WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('002'),
            business_object_code='asset_pickup',
            business_id='ASSET_002',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_APPROVED,
            created_by=self.initiator
        )

        url = '/api/workflows/instances/my_instances/?status=running'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        for instance in results:
            self.assertEqual(instance['status'], 'running')

    def test_withdraw_workflow(self):
        """Test withdrawing a workflow via API."""
        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )


        url = f'/api/workflows/instances/{instance.id}/withdraw/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        instance.refresh_from_db()
        self.assertEqual(instance.status, WorkflowInstance.STATUS_CANCELLED)

    def test_withdraw_by_non_initiator_fails(self):
        """Test that non-initiator cannot withdraw workflow."""
        other_user = User.objects.create_user(
            username=f'other_{uuid.uuid4().hex[:8]}',
            email=f'other{uuid.uuid4().hex[:8]}@test.com',
            is_active=True
        )
        other_user.current_organization = self.organization
        other_user.save()

        # Add other_user to the organization
        UserOrganization.objects.create(
            user=other_user,
            organization=self.organization,
            role='member',
            is_primary=True
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        self.client.force_authenticate(user=other_user)
        url = f'/api/workflows/instances/{instance.id}/withdraw/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_terminate_workflow_by_admin(self):
        """Test terminating a workflow by admin."""
        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        self._authenticate_with_org(self.admin_user)
        url = f'/api/workflows/instances/{instance.id}/terminate/'
        data = {'reason': 'Emergency termination'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        instance.refresh_from_db()
        self.assertEqual(instance.status, WorkflowInstance.STATUS_TERMINATED)
        self.assertEqual(instance.terminated_by, self.admin_user)

    def test_terminate_workflow_by_non_admin_fails(self):
        """Test that non-admin cannot terminate workflow."""
        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        url = f'/api/workflows/instances/{instance.id}/terminate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_instance_timeline(self):
        """Test getting workflow instance timeline."""
        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        # Create task and approval
        task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=instance,
            node_id='approval_1',
            node_name='Test Approval',
            node_type='approval',
            assignee=self.approver,
            status=WorkflowTask.STATUS_PENDING,
            created_by=self.initiator
        )

        WorkflowApproval.objects.create(
            organization=self.organization,
            task=task,
            approver=self.approver,
            action='approve',
            comment='Approved',
            created_by=self.approver
        )

        url = f'/api/workflows/instances/{instance.id}/timeline/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertGreater(len(response.data['data']), 0)


class WorkflowTaskAPITest(WorkflowAPITestCase):
    """Tests for WorkflowTask API endpoints."""

    def setUp(self):
        """Set up additional test data."""
        super().setUp()

        # Create workflow instance with graph_snapshot
        self.instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            graph_snapshot=self.simple_graph_data,  # Include graph snapshot
            created_by=self.initiator
        )

        # Create task
        self.task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_1',
            node_name='Department Approval',
            node_type='approval',
            assignee=self.approver,
            status=WorkflowTask.STATUS_PENDING,
            created_by=self.initiator
        )

    def test_list_my_tasks(self):
        """Test listing current user's tasks."""
        self._authenticate_with_org(self.approver)
        url = '/api/workflows/tasks/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_list_tasks_with_status_filter(self):
        """Test listing tasks with status filter."""
        self._authenticate_with_org(self.approver)
        url = '/api/workflows/tasks/?status=pending'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        for task in results:
            self.assertEqual(task['status'], 'pending')

    def test_list_my_tasks_grouped(self):
        """Test getting tasks grouped by status."""
        self._authenticate_with_org(self.approver)
        url = '/api/workflows/tasks/my_tasks/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('pending', response.data['data'])
        self.assertIn('summary', response.data['data'])

    def test_approve_task_success(self):
        """Test approving a task via API."""
        self._authenticate_with_org(self.approver)
        url = f'/api/workflows/tasks/{self.task.id}/approve/'
        data = {'comment': 'Approved'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkflowTask.STATUS_APPROVED)

    def test_approve_task_by_non_assignee_fails(self):
        """Test that non-assignee cannot approve task."""
        self._authenticate_with_org(self.initiator)
        url = f'/api/workflows/tasks/{self.task.id}/approve/'
        data = {'comment': 'Trying to approve'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_reject_task_success(self):
        """Test rejecting a task via API."""
        self._authenticate_with_org(self.approver)
        url = f'/api/workflows/tasks/{self.task.id}/reject/'
        data = {'comment': 'Not approved'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkflowTask.STATUS_REJECTED)

        self.instance.refresh_from_db()
        self.assertEqual(self.instance.status, WorkflowInstance.STATUS_REJECTED)

    def test_delegate_task_success(self):
        """Test delegating a task via API."""
        self._authenticate_with_org(self.approver)
        url = f'/api/workflows/tasks/{self.task.id}/delegate/'
        data = {
            'to_user_id': str(self.initiator.id),
            'reason': 'Out of office'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.task.refresh_from_db()
        self.assertEqual(self.task.assignee, self.initiator)

    def test_reassign_task_by_admin(self):
        """Test reassigning a task by admin."""
        self._authenticate_with_org(self.admin_user)
        url = f'/api/workflows/tasks/{self.task.id}/reassign/'
        data = {
            'assignee_id': str(self.initiator.id),
            'reason': 'Admin reassignment'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        self.task.refresh_from_db()
        self.assertEqual(self.task.assignee, self.initiator)

    def test_reassign_task_by_non_admin_fails(self):
        """Test that non-admin cannot reassign task."""
        self._authenticate_with_org(self.approver)
        url = f'/api/workflows/tasks/{self.task.id}/reassign/'
        data = {
            'assignee_id': str(self.initiator.id),
            'reason': 'Trying to reassign'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class WorkflowStatisticsAPITest(WorkflowAPITestCase):
    """Tests for WorkflowStatistics API endpoints."""

    def setUp(self):
        """Set up additional test data."""
        super().setUp()
        self._authenticate_with_org(self.initiator)

        # Create various instances for statistics
        # Create instances
        self.instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('001'),
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('002'),
            business_object_code='asset_pickup',
            business_id='ASSET_002',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_APPROVED,
            completed_at=timezone.now(),
            started_at=timezone.now(),
            created_by=self.initiator
        )

        # Create task
        self.task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_1',
            node_name='Department Approval',
            node_type='approval',
            assignee=self.initiator,
            status=WorkflowTask.STATUS_PENDING,
            created_by=self.initiator
        )

    def test_get_statistics(self):
        """Test getting workflow statistics."""
        url = '/api/workflows/statistics/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        data = response.data['data']
        self.assertIn('total_instances', data)
        self.assertIn('pending_instances', data)
        self.assertIn('completed_instances', data)
        self.assertIn('my_pending_tasks', data)
        self.assertIn('instances_by_status', data)
        self.assertIn('instances_by_definition', data)

    def test_statistics_counts_are_accurate(self):
        """Test that statistics counts are accurate."""
        url = '/api/workflows/statistics/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['data']

        # Verify counts
        self.assertEqual(data['total_instances'], 2)
        self.assertGreaterEqual(data['pending_instances'], 1)
        self.assertGreaterEqual(data['completed_instances'], 1)


class WorkflowEndToEndAPITest(WorkflowAPITestCase):
    """End-to-end tests for workflow execution via API."""

    def test_full_workflow_lifecycle_via_api(self):
        """Test complete workflow lifecycle from start to completion."""
        self._authenticate_with_org(self.initiator)

        # 1. Start workflow
        start_url = '/api/workflows/instances/start/'
        start_data = {
            'definition_id': str(self.workflow_definition.id),
            'business_object_code': 'asset_pickup',
            'business_id': 'ASSET_001',
            'variables': {'amount': 5000}
        }

        response = self.client.post(start_url, start_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance_id = response.data['data']['id']

        # 2. Get pending tasks for approver
        self._authenticate_with_org(self.approver)
        tasks_url = '/api/workflows/tasks/my_tasks/'
        response = self.client.get(tasks_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pending_tasks = response.data['data']['pending']
        self.assertGreater(len(pending_tasks), 0)

        task_id = pending_tasks[0]['id']

        # 3. Approve the task
        approve_url = f'/api/workflows/tasks/{task_id}/approve/'
        response = self.client.post(approve_url, {'comment': 'Approved'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Verify workflow is completed
        instance = WorkflowInstance.objects.get(id=instance_id)
        self.assertEqual(instance.status, WorkflowInstance.STATUS_APPROVED)
        self.assertIsNotNone(instance.completed_at)

    def test_workflow_rejection_via_api(self):
        """Test workflow rejection via API."""
        self._authenticate_with_org(self.initiator)

        # Start workflow
        start_url = '/api/workflows/instances/start/'
        start_data = {
            'definition_id': str(self.workflow_definition.id),
            'business_object_code': 'asset_pickup',
            'business_id': 'ASSET_002',
        }

        response = self.client.post(start_url, start_data, format='json')
        instance_id = response.data['data']['id']

        # Reject the task
        self._authenticate_with_org(self.approver)
        tasks_url = '/api/workflows/tasks/my_tasks/'
        response = self.client.get(tasks_url)

        task_id = response.data['data']['pending'][0]['id']
        reject_url = f'/api/workflows/tasks/{task_id}/reject/'
        response = self.client.post(reject_url, {'comment': 'Not approved'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify workflow is rejected
        instance = WorkflowInstance.objects.get(id=instance_id)
        self.assertEqual(instance.status, WorkflowInstance.STATUS_REJECTED)

    def test_workflow_withdrawal_and_restart(self):
        """Test withdrawing a workflow and starting a new one."""
        self._authenticate_with_org(self.initiator)

        # Start workflow
        start_url = '/api/workflows/instances/start/'
        start_data = {
            'definition_id': str(self.workflow_definition.id),
            'business_object_code': 'asset_pickup',
            'business_id': 'ASSET_003',
        }

        response = self.client.post(start_url, start_data, format='json')
        instance_id = response.data['data']['id']

        # Withdraw workflow
        withdraw_url = f'/api/workflows/instances/{instance_id}/withdraw/'
        response = self.client.post(withdraw_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Start new workflow for same business object
        response = self.client.post(start_url, start_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
