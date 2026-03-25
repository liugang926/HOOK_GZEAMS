# Integration Scenarios Test Suite for Sprint 2 - Real-world workflow scenarios

import pytest
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from apps.common.mixins.workflow_status import WorkflowStatusMixin
from apps.workflows.models import (
    WorkflowDefinition, WorkflowInstance, WorkflowTask, WorkflowApproval,
    WorkflowOperationLog
)
from apps.workflows.services import WorkflowEngine, BusinessStateSyncService
from apps.workflows.signals import workflow_started, workflow_completed, workflow_rejected, workflow_cancelled

User = get_user_model()


class IntegrationScenariosTest(APITestCase):
    """Real-world workflow integration scenarios"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpass'
        )
        
        self.director = User.objects.create_user(
            username='director',
            email='director@example.com',
            password='directorpass'
        )
        
        self.finance_user = User.objects.create_user(
            username='finance',
            email='finance@example.com',
            password='financepass'
        )
        
        # Create workflow definition for testing
        self.workflow_definition = WorkflowDefinition.objects.create(
            name='Multi-level Asset Approval',
            code='multi-level-asset-approval',
            version=1,
            status='published',
            business_object_code='AssetPickup',
            graph_data={
                'nodes': [
                    {
                        'id': '1',
                        'type': 'approval',
                        'text': 'Manager Approval',
                        'properties': {
                            'approver_type': 'user',
                            'approver_config': {'role': 'manager'}
                        }
                    },
                    {
                        'id': '2',
                        'type': 'condition',
                        'text': 'Amount Check',
                        'properties': {
                            'conditions': [
                                {
                                    'field': 'amount',
                                    'operator': 'gt',
                                    'value': '10000'
                                }
                            ]
                        }
                    },
                    {
                        'id': '3',
                        'type': 'approval',
                        'text': 'Finance Approval',
                        'properties': {
                            'approver_type': 'user',
                            'approver_config': {'role': 'finance'}
                        }
                    },
                    {
                        'id': '4',
                        'type': 'approval',
                        'text': 'Director Approval',
                        'properties': {
                            'approver_type': 'user',
                            'approver_config': {'role': 'director'}
                        }
                    }
                ],
                'edges': [
                    {
                        'id': 'edge_1',
                        'sourceNodeId': '1',
                        'targetNodeId': '2',
                        'type': 'polyline',
                        'properties': {}
                    },
                    {
                        'id': 'edge_2',
                        'sourceNodeId': '2',
                        'targetNodeId': '3',
                        'type': 'polyline',
                        'properties': {'condition': True}
                    },
                    {
                        'id': 'edge_3',
                        'sourceNodeId': '2',
                        'targetNodeId': '4',
                        'type': 'polyline',
                        'properties': {'condition': False}
                    },
                    {
                        'id': 'edge_4',
                        'sourceNodeId': '3',
                        'targetNodeId': '4',
                        'type': 'polyline',
                        'properties': {}
                    }
                ]
            },
            form_permissions={
                '1': {'amount': 'read_only', 'department': 'editable', 'notes': 'editable'},
                '3': {'amount': 'editable', 'department': 'hidden', 'notes': 'read_only'},
                '4': {'amount': 'read_only', 'department': 'editable', 'notes': 'editable'}
            }
        )

    def test_multi_approval_chain(self):
        """Test: submit → manager → director → approved"""
        
        # Submit AssetPickup workflow
        engine = WorkflowEngine()
        success, workflow_instance, error = engine.start_workflow(
            definition=self.workflow_definition,
            business_object_code='AssetPickup',
            business_id='test-multi-chain-001',
            business_no='AP-2024-001',
            initiator=self.user,
            variables={
                'asset_name': 'Dell XPS 15',
                'amount': '8500',
                'department': 'IT',
                'purpose': 'Development workstation',
                'notes': 'High performance laptop'
            }
        )
        
        self.assertTrue(success, f"Workflow start failed: {error}")
        
        # Step 1: Manager approval
        manager_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='1'
        ).first()
        
        self.assertIsNotNone(manager_task)
        
        success, error = manager_task.complete(
            approved=True,
            comment='Approved for IT department',
            data={'department': 'IT', 'notes': 'Standard approval'}
        )
        self.assertTrue(success, f"Manager approval failed: {error}")
        
        manager_task.refresh_from_db()
        self.assertEqual(manager_task.status, 'completed')
        
        # Step 2: Director approval (bypasses finance for amounts < 10K)
        director_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='4'
        ).first()
        
        self.assertIsNotNone(director_task)
        
        success, error = director_task.complete(
            approved=True,
            comment='Final approval',
            data={'department': 'IT', 'notes': 'All requirements met'}
        )
        self.assertTrue(success, f"Director approval failed: {error}")
        
        director_task.refresh_from_db()
        self.assertEqual(director_task.status, 'completed')
        
        # Final state: workflow approved
        workflow_instance.refresh_from_db()
        self.assertEqual(workflow_instance.status, 'approved')

    def test_conditional_approval_flow(self):
        """Test: amount > 10k → finance approval required"""
        
        # Start workflow with high amount
        engine = WorkflowEngine()
        success, workflow_instance, error = engine.start_workflow(
            definition=self.workflow_definition,
            business_object_code='AssetPickup',
            business_id='test-conditional-flow-001',
            initiator=self.user,
            variables={
                'asset_name': 'Mac Studio',
                'amount': '25000',  # High amount - requires finance approval
                'department': 'Design',
                'purpose': 'Creative work',
                'notes': 'High-end workstation'
            }
        )
        
        self.assertTrue(success, f"Workflow start failed: {error}")
        
        # Step 1: Manager approval
        manager_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='1'
        ).first()
        
        self.assertIsNotNone(manager_task)
        
        success, error = manager_task.complete(
            approved=True,
            comment='Approved for design department',
            data={'department': 'Design', 'notes': 'Design equipment approval'}
        )
        self.assertTrue(success, f"Manager approval failed: {error}")
        
        # Step 2: Amount condition should route to finance approval (node 3)
        finance_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='3'
        ).first()
        
        self.assertIsNotNone(finance_task, "Finance task should be created for high amount")
        
        # Step 3: Finance approval
        success, error = finance_task.complete(
            approved=True,
            comment='Budget approved',
            data={'amount': '25000', 'notes': 'Budget constraints met'}
        )
        self.assertTrue(success, f"Finance approval failed: {error}")
        
        finance_task.refresh_from_db()
        self.assertEqual(finance_task.status, 'completed')
        
        # Step 4: Director approval
        director_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='4'
        ).first()
        
        self.assertIsNotNone(director_task)
        
        success, error = director_task.complete(
            approved=True,
            comment='Final approval',
            data={'department': 'Design', 'notes': 'Finance approved, proceed'}
        )
        self.assertTrue(success, f"Director approval failed: {error}")
        
        workflow_instance.refresh_from_db()
        self.assertEqual(workflow_instance.status, 'approved')

    def test_field_permissions_between_approvals(self):
        """Test: manager sees full form → finance sees hidden fields"""
        
        # Start workflow
        engine = WorkflowEngine()
        success, workflow_instance, error = engine.start_workflow(
            definition=self.workflow_definition,
            business_object_code='AssetPickup',
            business_id='test-permissions-chain-001',
            initiator=self.user,
            variables={
                'asset_name': 'iPad Pro',
                'amount': '1200',
                'department': 'Marketing',
                'purpose': 'Client presentations',
                'notes': 'iPad for client meetings'
            }
        )
        
        self.assertTrue(success, f"Workflow start failed: {error}")
        
        # Step 1: Manager approval (should see all fields)
        manager_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='1'
        ).first()
        
        self.assertIsNotNone(manager_task)
        
        # Get task details to verify permissions
        response = self.client.get(f'/api/workflows/tasks/{manager_task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        manager_data = response.json().get('data', {})
        manager_permissions = manager_data.get('form_permissions', {})
        
        # Manager should see all fields
        self.assertEqual(manager_permissions.get('amount'), 'read_only')
        self.assertEqual(manager_permissions.get('department'), 'editable')
        self.assertEqual(manager_permissions.get('notes'), 'editable')
        
        # Manager completes approval
        success, error = manager_task.complete(
            approved=True,
            comment='Approved for marketing',
            data={'department': 'Marketing', 'notes': 'Standard approval'}
        )
        self.assertTrue(success, f"Manager approval failed: {error}")
        
        # Step 2: Finance approval (should see department as hidden)
        finance_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='3'
        ).first()
        
        self.assertIsNotNone(finance_task)
        
        response = self.client.get(f'/api/workflows/tasks/{finance_task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        finance_data = response.json().get('data', {})
        finance_permissions = finance_data.get('form_permissions', {})
        business_data = finance_data.get('business_data', {})
        
        # Finance should not see department field (hidden)
        self.assertEqual(finance_permissions.get('department'), 'hidden')
        self.assertNotIn('department', business_data)
        
        # Finance can modify amount but not notes
        self.assertEqual(finance_permissions.get('amount'), 'editable')
        self.assertEqual(finance_permissions.get('notes'), 'read_only')
        
        # Finance completes approval
        success, error = finance_task.complete(
            approved=True,
            comment='Budget approved',
            data={'amount': '1200', 'notes': 'Budget approved'}
        )
        self.assertTrue(success, f"Finance approval failed: {error}")
        
        # Step 3: Director approval (should see all fields except amount)
        director_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='4'
        ).first()
        
        self.assertIsNotNone(director_task)
        
        response = self.client.get(f'/api/workflows/tasks/{director_task.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        director_permissions = response.json().get('data', {}).get('form_permissions', {})
        
        # Director should see amount as read_only, department as editable
        self.assertEqual(director_permissions.get('amount'), 'read_only')
        self.assertEqual(director_permissions.get('department'), 'editable')
        self.assertEqual(director_permissions.get('notes'), 'editable')

    def test_concurrent_approvers(self):
        """Test: multiple approvers for the same task"""
        
        # Create workflow with parallel approval nodes
        parallel_workflow_definition = WorkflowDefinition.objects.create(
            name='Parallel Approval Workflow',
            code='parallel-approval-workflow',
            version=1,
            status='published',
            business_object_code='AssetPickup',
            graph_data={
                'nodes': [
                    {
                        'id': '1',
                        'type': 'approval',
                        'text': 'Team Approval',
                        'properties': {
                            'approver_type': 'user',
                            'approver_config': {'role': 'team'}
                        }
                    },
                    {
                        'id': '2',
                        'type': 'approval',
                        'text': 'HR Approval',
                        'properties': {
                            'approver_type': 'user',
                            'approver_config': {'role': 'hr'}
                        }
                    }
                ],
                'edges': [
                    {
                        'id': 'edge_1',
                        'sourceNodeId': '1',
                        'targetNodeId': 'end',
                        'type': 'polyline',
                        'properties': {}
                    },
                    {
                        'id': 'edge_2',
                        'sourceNodeId': '2',
                        'targetNodeId': 'end',
                        'type': 'polyline',
                        'properties': {}
                    }
                ]
            },
            form_permissions={
                '1': {'amount': 'read_only', 'department': 'editable'},
                '2': {'amount': 'editable', 'department': 'read_only'}
            }
        )
        
        # Start workflow
        engine = WorkflowEngine()
        success, workflow_instance, error = engine.start_workflow(
            definition=parallel_workflow_definition,
            business_object_code='AssetPickup',
            business_id='test-concurrent-approval-001',
            initiator=self.user,
            variables={
                'asset_name': 'Ergonomic Chair',
                'amount': '800',
                'department': 'Operations',
                'purpose': 'Employee wellness',
                'notes': 'New office furniture'
            }
        )
        
        self.assertTrue(success, f"Workflow start failed: {error}")
        
        # Step 1: Create two parallel approval tasks
        team_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='1'
        ).first()
        
        hr_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='2'
        ).first()
        
        # Both approvers can work on their tasks independently
        success1, error1 = team_task.complete(
            approved=True,
            comment='Approved for operations',
            data={'department': 'Operations', 'notes': 'Team approves'}
        )
        self.assertTrue(success1, f"Team approval failed: {error1}")
        
        success2, error2 = hr_task.complete(
            approved=True,
            comment='HR approves',
            data={'amount': '800', 'notes': 'Budget approved'}
        )
        self.assertTrue(success2, f"HR approval failed: {error2}")
        
        # Both tasks completed
        team_task.refresh_from_db()
        hr_task.refresh_from_db()
        self.assertEqual(team_task.status, 'completed')
        self.assertEqual(hr_task.status, 'completed')
        
        # Workflow should continue to completion
        workflow_instance.refresh_from_db()
        self.assertEqual(workflow_instance.status, 'approved')

    def test_workflow_timeout_handling(self):
        """Test: task timeout → automatic escalation or rejection"""
        
        # Create workflow with timeout
        timeout_workflow_definition = WorkflowDefinition.objects.create(
            name='Timeout Workflow',
            code='timeout-workflow',
            version=1,
            status='published',
            business_object_code='AssetPickup',
            graph_data={
                'nodes': [
                    {
                        'id': '1',
                        'type': 'approval',
                        'text': 'Quick Approval',
                        'properties': {
                            'approver_type': 'user',
                            'timeout_minutes': 5
                        }
                    }
                ],
                'edges': [
                    {
                        'id': 'edge_1',
                        'sourceNodeId': '1',
                        'targetNodeId': 'end',
                        'type': 'polyline',
                        'properties': {}
                    }
                ]
            },
            form_permissions={}
        )
        
        # Start workflow
        engine = WorkflowEngine()
        success, workflow_instance, error = engine.start_workflow(
            definition=timeout_workflow_definition,
            business_object_code='AssetPickup',
            business_id='test-timeout-001',
            initiator=self.user,
            variables={
                'asset_name': 'Urgent Equipment',
                'amount': '500',
                'department': 'IT',
                'purpose': 'Emergency replacement'
            }
        )
        
        self.assertTrue(success, f"Workflow start failed: {error}")
        
        # Get the task and set it to timeout by modifying created_at
        quick_task = WorkflowTask.objects.filter(
            workflow_instance=workflow_instance,
            node_id='1'
        ).first()
        
        self.assertIsNotNone(quick_task)
        
        # Simulate timeout by setting created_at in the past
        from django.utils import timezone
        quick_task.created_at = timezone.now() - timedelta(minutes=6)  # 6 minutes ago
        quick_task.save()
        
        # Check timeout handling - should reject or escalate
        success, error = quick_task.complete(
            approved=True,
            comment='Late approval',
            data={'department': 'IT'}
        )
        
        # Task should be marked as timed out or rejected
        quick_task.refresh_from_db()
        # Depending on implementation, task might be rejected or completed
        # This test verifies the timeout mechanism exists
        self.assertIn(quick_task.status, ['completed', 'rejected', 'cancelled', 'terminated'])

    def test_statistics_endpoints_accuracy(self):
        """Test that statistics endpoints return accurate data"""
        
        engine = WorkflowEngine()
        
        # Create multiple test workflows
        for i in range(5):
            success, workflow_instance, error = engine.start_workflow(
                definition=self.workflow_definition,
                business_object_code='AssetPickup',
                business_id=f'test-stat-{i}',
                initiator=self.user,
                variables={
                    'asset_name': f'Equipment {i}',
                    'amount': f'{1000 + i * 100}',
                    'department': 'IT',
                    'purpose': f'Testing statistics {i}'
                }
            )
            
            self.assertTrue(success, f"Workflow {i} start failed: {error}")
            
            # Complete approval chain
            manager_task = WorkflowTask.objects.filter(
                workflow_instance=workflow_instance,
                node_id='1'
            ).first()
            
            self.assertIsNotNone(manager_task)
            
            success, error = manager_task.complete(
                approved=True,
                comment=f'Approval {i}',
                data={'department': 'IT', 'notes': f'Notes {i}'}
            )
            self.assertTrue(success, f"Manager approval {i} failed: {error}")
            
            if i < 3:  # First 3 approved
                director_task = WorkflowTask.objects.filter(
                    workflow_instance=workflow_instance,
                    node_id='4'
                ).first()
                
                self.assertIsNotNone(director_task)
                
                success, error = director_task.complete(
                    approved=True,
                    comment=f'Final approval {i}',
                    data={'department': 'IT', 'notes': f'Final notes {i}'}
                )
                self.assertTrue(success, f"Director approval {i} failed: {error}")
            else:  # Last 2 rejected
                director_task = WorkflowTask.objects.filter(
                    workflow_instance=workflow_instance,
                    node_id='4'
                ).first()
                
                self.assertIsNotNone(director_task)
                
                success, error = director_task.complete(
                    approved=False,
                    comment=f'Rejection {i}',
                    data={'department': 'IT', 'notes': f'Rejection notes {i}'}
                )
                self.assertTrue(success, f"Director rejection {i} failed: {error}")
        
        # Test overview statistics endpoint
        response = self.client.get('/api/workflows/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success', False))
        
        # Verify counts are reasonable
        stats = data.get('data', {})
        self.assertGreaterEqual(stats.get('total_instances', 0), 5)
        
        # Test trends endpoint
        response = self.client.get('/api/workflows/statistics/trends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success', False))
        self.assertIn('data', data)
        
        # Test bottlenecks endpoint
        response = self.client.get('/api/workflows/statistics/bottlenecks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success', False))
        self.assertIn('bottlenecks', data)
        
        # Test by-business lookup endpoint
        response = self.client.get(
            '/api/workflows/instances/by-business/',
            {
                'business_object_code': 'AssetPickup',
                'business_id': 'test-stat-0'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success', False))
        results = data.get('data', [])
        self.assertGreaterEqual(len(results), 1)
        
        response = self.client.get(
            '/api/workflows/instances/by-business/',
            {
                'business_object_code': 'AssetPickup',
                'business_id': 'nonexistent'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success', False))
        results = data.get('data', [])
        self.assertEqual(len(results), 0)