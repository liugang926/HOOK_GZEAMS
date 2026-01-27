"""
Tests for workflow execution engine.

Tests for WorkflowEngine, ApproverResolver, and ConditionEvaluator services.
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowApproval
)
from apps.workflows.services.workflow_engine import WorkflowEngine
from apps.workflows.services.approver_resolver import ApproverResolver
from apps.workflows.services.condition_evaluator import ConditionEvaluator
from apps.organizations.models import Organization, Department, UserDepartment
from apps.accounts.models import User, UserOrganization

User = get_user_model()


class WorkflowExecutionEngineTest(TestCase):
    """Tests for workflow execution engine."""

    def setUp(self):
        """Set up test data."""
        self.organization = Organization.objects.create(
            code='TEST_ORG',
            name='Test Organization',
            org_type='company',
            is_active=True
        )

        self.department = Department.objects.create(
            code='TEST_DEPT',
            organization=self.organization,
            name='Test Department'
        )

        # Set department leader
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@test.com',
            is_active=True
        )
        self.department.leader = self.leader
        self.department.save()

        self.initiator = User.objects.create_user(
            username='initiator',
            email='initiator@test.com',
            is_active=True
        )
        self.initiator.current_organization = self.organization
        self.initiator.save()

        # Add initiator to organization
        UserOrganization.objects.create(
            user=self.initiator,
            organization=self.organization,
            role='member',
            is_primary=True
        )

        # Add initiator to department
        UserDepartment.objects.create(
            user=self.initiator,
            organization=self.organization,
            department=self.department,
            is_primary=True
        )

        self.approver1 = User.objects.create_user(
            username='approver1',
            email='approver1@test.com',
            is_active=True
        )
        self.approver1.current_organization = self.organization
        self.approver1.save()

        UserOrganization.objects.create(
            user=self.approver1,
            organization=self.organization,
            role='admin',
            is_primary=True
        )

        UserDepartment.objects.create(
            user=self.approver1,
            organization=self.organization,
            department=self.department,
            is_primary=True
        )

        self.approver2 = User.objects.create_user(
            username='approver2',
            email='approver2@test.com',
            is_active=True
        )
        self.approver2.current_organization = self.organization
        self.approver2.save()

        UserOrganization.objects.create(
            user=self.approver2,
            organization=self.organization,
            role='member',
            is_primary=True
        )

        UserDepartment.objects.create(
            user=self.approver2,
            organization=self.organization,
            department=self.department,
            is_primary=True
        )

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
                            {'type': 'user', 'user_id': str(self.approver1.id)}
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

        self.multi_approver_graph_data = {
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
                        'approveType': 'and',
                        'approvers': [
                            {'type': 'user', 'user_id': str(self.approver1.id)},
                            {'type': 'user', 'user_id': str(self.approver2.id)}
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


class TestWorkflowEngine(WorkflowExecutionEngineTest):
    """Tests for WorkflowEngine service."""

    def test_start_workflow_success(self):
        """Test starting a workflow successfully."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, error = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator,
            variables={'amount': 5000, 'reason': 'Need equipment'}
        )

        if not success:
            print(f"ERROR: {error}")
            print(f"Instance: {instance}")

        self.assertTrue(success, f"Failed to start workflow: {error}")
        self.assertIsNotNone(instance)
        self.assertIsNone(error)
        self.assertEqual(instance.status, WorkflowInstance.STATUS_PENDING_APPROVAL)
        self.assertEqual(instance.initiator, self.initiator)
        self.assertEqual(instance.business_no, 'LY-2024-001')
        self.assertEqual(instance.business_id, 'ASSET_001')
        self.assertIsNotNone(instance.started_at)
        self.assertEqual(instance.get_variable('amount'), 5000)

    def test_start_workflow_creates_tasks(self):
        """Test that starting workflow creates approval tasks."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, _ = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator
        )

        # Check tasks were created
        tasks = instance.tasks.filter(node_type='approval')
        self.assertEqual(tasks.count(), 1)

        task = tasks.first()
        self.assertEqual(task.status, WorkflowTask.STATUS_PENDING)
        self.assertEqual(task.node_type, 'approval')

    def test_approve_task_or_type(self):
        """Test OR approval type (any one can approve)."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, _ = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator
        )

        # Get the task
        task = instance.tasks.filter(assignee=self.approver1).first()
        self.assertIsNotNone(task)

        # Approve
        success, updated_instance, error = engine.execute_task(
            task=task,
            action='approve',
            actor=self.approver1,
            comment='Approved'
        )

        self.assertTrue(success)
        self.assertEqual(updated_instance.status, WorkflowInstance.STATUS_APPROVED)
        self.assertIsNotNone(updated_instance.completed_at)

        # Check task status
        task.refresh_from_db()
        self.assertEqual(task.status, WorkflowTask.STATUS_APPROVED)

    def test_reject_task(self):
        """Test rejecting a task."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, _ = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator
        )

        task = instance.tasks.filter(assignee=self.approver1).first()

        # Reject
        success, instance, _ = engine.execute_task(
            task=task,
            action='reject',
            actor=self.approver1,
            comment='Not approved - insufficient documentation'
        )

        self.assertTrue(success)
        self.assertEqual(instance.status, WorkflowInstance.STATUS_REJECTED)
        self.assertIsNotNone(instance.completed_at)

    def test_withdraw_workflow(self):
        """Test withdrawing a workflow."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, _ = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator
        )

        # Withdraw
        success, error = engine.withdraw_instance(instance, self.initiator)

        self.assertTrue(success)
        self.assertIsNone(error)

        instance.refresh_from_db()
        self.assertEqual(instance.status, WorkflowInstance.STATUS_CANCELLED)

    def test_terminate_workflow(self):
        """Test terminating a workflow (admin action)."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='simple_approval',
            name='Simple Approval',
            business_object_code='asset_pickup',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        engine = WorkflowEngine()

        success, instance, _ = engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id='ASSET_001',
            business_no='LY-2024-001',
            initiator=self.initiator
        )

        # Create admin user
        admin = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            is_staff=True,
            is_active=True
        )
        admin.current_organization = self.organization
        admin.save()

        UserOrganization.objects.create(
            user=admin,
            organization=self.organization,
            role='admin',
            is_primary=True
        )

        # Terminate
        success, error = engine.terminate_instance(
            instance, admin, 'Emergency termination'
        )

        self.assertTrue(success)
        self.assertIsNone(error)

        instance.refresh_from_db()
        self.assertEqual(instance.status, WorkflowInstance.STATUS_TERMINATED)
        self.assertEqual(instance.terminated_by, admin)


class TestApproverResolver(WorkflowExecutionEngineTest):
    """Tests for ApproverResolver service."""

    def test_resolve_user_type(self):
        """Test resolving specific users."""
        resolver = ApproverResolver()

        # Create instance
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-001',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        configs = [
            {'type': 'user', 'user_id': str(self.initiator.id)}
        ]

        users = resolver.resolve(configs, instance)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self.initiator)

    def test_resolve_initiator_type(self):
        """Test resolving initiator as approver."""
        resolver = ApproverResolver()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-002',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        configs = [
            {'type': 'initiator'}
        ]

        users = resolver.resolve(configs, instance)

        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], self.initiator)

    def test_deduplicate_users(self):
        """Test duplicate user deduplication."""
        resolver = ApproverResolver()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-003',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        configs = [
            {'type': 'user', 'user_id': str(self.initiator.id)},
            {'type': 'user', 'user_id': str(self.initiator.id)},  # Duplicate
        ]

        users = resolver.resolve(configs, instance)

        self.assertEqual(len(users), 1)


class TestConditionEvaluator(WorkflowExecutionEngineTest):
    """Tests for ConditionEvaluator service."""

    def test_evaluate_eq_condition(self):
        """Test evaluating equals condition."""
        evaluator = ConditionEvaluator()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-004',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={'amount': 10000},
            created_by=self.initiator
        )

        result = evaluator.evaluate_condition(
            {'field': 'amount', 'operator': 'eq', 'value': '10000'},
            instance
        )

        self.assertTrue(result)

    def test_evaluate_gt_condition(self):
        """Test evaluating greater than condition."""
        evaluator = ConditionEvaluator()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-005',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={'amount': 15000},
            created_by=self.initiator
        )

        result = evaluator.evaluate_condition(
            {'field': 'amount', 'operator': 'gt', 'value': '10000'},
            instance
        )

        self.assertTrue(result)

    def test_evaluate_in_condition(self):
        """Test evaluating in condition."""
        evaluator = ConditionEvaluator()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-006',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={'status': 'pending'},
            created_by=self.initiator
        )

        result = evaluator.evaluate_condition(
            {'field': 'status', 'operator': 'in', 'value': ['pending', 'running']},
            instance
        )

        self.assertTrue(result)

    def test_evaluate_nested_field(self):
        """Test evaluating nested field condition."""
        evaluator = ConditionEvaluator()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-007',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={
                'applicant': {
                    'department': {
                        'id': 5
                    }
                }
            },
            created_by=self.initiator
        )

        result = evaluator.evaluate_condition(
            {'field': 'applicant.department.id', 'operator': 'eq', 'value': 5},
            instance
        )

        self.assertTrue(result)

    def test_evaluate_multiple_conditions(self):
        """Test evaluating multiple conditions (AND logic)."""
        evaluator = ConditionEvaluator()

        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-008',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={'amount': 15000, 'status': 'pending'},
            created_by=self.initiator
        )

        conditions = [
            {'field': 'amount', 'operator': 'gt', 'value': '10000'},
            {'field': 'status', 'operator': 'eq', 'value': 'pending'}
        ]

        result = evaluator.evaluate_conditions(conditions, instance)

        self.assertTrue(result)


class TestWorkflowInstanceModel(WorkflowExecutionEngineTest):
    """Tests for WorkflowInstance model methods."""

    def test_get_variable(self):
        """Test getting variable from instance."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-009',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={'amount': 5000, 'reason': 'Need equipment'},
            created_by=self.initiator
        )

        self.assertEqual(instance.get_variable('amount'), 5000)
        self.assertEqual(instance.get_variable('reason'), 'Need equipment')
        self.assertIsNone(instance.get_variable('nonexistent'))
        self.assertEqual(instance.get_variable('nonexistent', 'default'), 'default')

    def test_set_variable(self):
        """Test setting variable on instance."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-010',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            variables={},
            created_by=self.initiator
        )

        instance.set_variable('amount', 10000)

        self.assertEqual(instance.get_variable('amount'), 10000)

    def test_progress_percentage(self):
        """Test progress percentage calculation."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-011',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            total_tasks=4,
            completed_tasks=2,
            created_by=self.initiator
        )

        self.assertEqual(instance.progress_percentage, 50)

    def test_is_active_property(self):
        """Test is_active property."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-012',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        self.assertTrue(instance.is_active)
        self.assertFalse(instance.is_terminal)

    def test_cancel_method(self):
        """Test cancel method."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-013',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status=WorkflowInstance.STATUS_RUNNING,
            created_by=self.initiator
        )

        instance.cancel()

        self.assertEqual(instance.status, WorkflowInstance.STATUS_CANCELLED)
        self.assertIsNotNone(instance.completed_at)


class TestWorkflowTaskModel(WorkflowExecutionEngineTest):
    """Tests for WorkflowTask model methods."""

    def test_approve_method(self):
        """Test task approve method."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-014',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=instance,
            node_id='approval_1',
            node_name='Test Approval',
            node_type='approval',
            assignee=self.approver1,
            status=WorkflowTask.STATUS_PENDING,
            created_by=self.initiator
        )

        task.approve(self.approver1, 'Approved')

        self.assertEqual(task.status, WorkflowTask.STATUS_APPROVED)
        self.assertIsNotNone(task.completed_at)
        self.assertEqual(task.completed_by, self.approver1)

    def test_is_overdue_property(self):
        """Test is_overdue property."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-015',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        # Create overdue task
        past_date = timezone.now() - timezone.timedelta(hours=1)
        task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=instance,
            node_id='approval_1',
            node_name='Test Approval',
            node_type='approval',
            assignee=self.approver1,
            status=WorkflowTask.STATUS_PENDING,
            due_date=past_date,
            created_by=self.initiator
        )

        self.assertTrue(task.is_overdue)


class TestWorkflowApprovalModel(WorkflowExecutionEngineTest):
    """Tests for WorkflowApproval model."""

    def test_approval_creation(self):
        """Test creating an approval record."""
        definition = WorkflowDefinition.objects.create(
            organization=self.organization,
            code='test_def',
            name='Test Definition',
            business_object_code='test',
            status='published',
            graph_data=self.simple_graph_data,
            created_by=self.initiator
        )

        instance = WorkflowInstance.objects.create(
            organization=self.organization,
            definition=definition,
            instance_no='TEST-016',
            business_object_code='test',
            business_id='123',
            initiator=self.initiator,
            status='running',
            created_by=self.initiator
        )

        task = WorkflowTask.objects.create(
            organization=self.organization,
            instance=instance,
            node_id='approval_1',
            node_name='Test Approval',
            node_type='approval',
            assignee=self.approver1,
            status=WorkflowTask.STATUS_PENDING,
            created_by=self.initiator
        )

        approval = WorkflowApproval.objects.create(
            organization=self.organization,
            task=task,
            approver=self.approver1,
            action='approve',
            comment='Approved this request',
            created_by=self.approver1
        )

        self.assertEqual(approval.action, 'approve')
        self.assertEqual(approval.approver, self.approver1)
        self.assertEqual(approval.comment, 'Approved this request')
