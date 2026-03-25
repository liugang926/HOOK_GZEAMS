"""
Performance benchmark tests for workflow API endpoints.
"""
from time import perf_counter

from django.utils import timezone
from rest_framework import status

from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask
from apps.workflows.tests.test_api import WorkflowAPITestCase


class WorkflowPerformanceBenchmarkTest(WorkflowAPITestCase):
    """Simple benchmark coverage for key workflow API endpoints."""

    WORKFLOW_LIST_TARGET_MS = 250
    TASK_DETAIL_TARGET_MS = 200
    STATISTICS_TARGET_MS = 300

    def setUp(self):
        """Create a small benchmark dataset."""
        super().setUp()
        self._authenticate_with_org(self.initiator)

        for index in range(24):
            WorkflowDefinition.objects.create(
                organization=self.organization,
                code=f'benchmark_definition_{index}_{self.unique_suffix}',
                name=f'Benchmark Definition {index}',
                business_object_code='asset_pickup',
                status='published',
                graph_data=self.simple_graph_data,
                created_by=self.admin_user,
            )

        started_at = timezone.now() - timezone.timedelta(hours=4)
        completed_at = timezone.now() - timezone.timedelta(hours=1)

        self.instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('PERF001'),
            business_object_code='asset_pickup',
            business_id='ASSET_PERF_001',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            started_at=started_at,
            created_by=self.initiator,
        )

        WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('PERF002'),
            business_object_code='asset_pickup',
            business_id='ASSET_PERF_002',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_APPROVED,
            started_at=started_at,
            completed_at=completed_at,
            created_by=self.initiator,
        )

        WorkflowInstance.objects.create(
            organization=self.organization,
            definition=self.workflow_definition,
            instance_no=self._make_instance_no('PERF003'),
            business_object_code='asset_pickup',
            business_id='ASSET_PERF_003',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_REJECTED,
            started_at=started_at,
            completed_at=completed_at,
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
            due_date=timezone.now() + timezone.timedelta(hours=2),
            created_by=self.initiator,
        )

        WorkflowTask.objects.create(
            organization=self.organization,
            instance=self.instance,
            node_id='approval_2',
            node_name='Finance Approval',
            node_type='approval',
            assignee=self.initiator,
            status=WorkflowTask.STATUS_PENDING,
            due_date=timezone.now() - timezone.timedelta(hours=1),
            created_by=self.initiator,
        )

    def _assert_get_within_target(self, url: str, target_ms: int):
        """Warm the endpoint and assert the measured request stays within target."""
        warm_response = self.client.get(url)
        self.assertEqual(warm_response.status_code, status.HTTP_200_OK)

        start_time = perf_counter()
        response = self.client.get(url)
        duration_ms = (perf_counter() - start_time) * 1000

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(
            duration_ms,
            target_ms,
            f'Expected {url} to respond within {target_ms}ms, got {duration_ms:.2f}ms.',
        )
        return response, duration_ms

    def test_workflow_list_endpoint_response_time(self):
        """Benchmark workflow definition list response time."""
        response, _ = self._assert_get_within_target(
            '/api/workflows/definitions/?page=1&page_size=20',
            self.WORKFLOW_LIST_TARGET_MS,
        )

        self.assertTrue(response.data['success'])
        self.assertIn('results', response.data['data'])

    def test_task_detail_endpoint_response_time(self):
        """Benchmark workflow task detail response time."""
        response, _ = self._assert_get_within_target(
            f'/api/workflows/tasks/{self.task.id}/',
            self.TASK_DETAIL_TARGET_MS,
        )

        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id'], str(self.task.id))

    def test_statistics_endpoint_response_time(self):
        """Benchmark workflow statistics response time."""
        response, _ = self._assert_get_within_target(
            '/api/workflows/statistics/',
            self.STATISTICS_TARGET_MS,
        )

        self.assertTrue(response.data['success'])
        self.assertIn('total_instances', response.data['data'])
