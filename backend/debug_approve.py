"""Debug script for approve task."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask
from apps.organizations.models import Organization, Department, UserDepartment
from apps.accounts.models import User, UserOrganization

# Create organization
org = Organization.objects.create(code='TEST_ORG3', name='Test Org3', org_type='company', is_active=True)
dept = Department.objects.create(code='TEST_DEPT3', organization=org, name='Test Dept3')

# Create users
admin = User.objects.create_user(username='admin3', email='admin3@test.com', is_staff=True, is_superuser=True, is_active=True)
admin.current_organization = org
admin.save()
UserOrganization.objects.create(user=admin, organization=org, role='admin', is_primary=True)

initiator = User.objects.create_user(username='initiator3', email='initiator3@test.com', is_active=True)
initiator.current_organization = org
initiator.save()
UserOrganization.objects.create(user=initiator, organization=org, role='member', is_primary=True)
UserDepartment.objects.create(user=initiator, organization=org, department=dept, is_primary=True)

approver = User.objects.create_user(username='approver3', email='approver3@test.com', is_active=True)
approver.current_organization = org
approver.save()
UserOrganization.objects.create(user=approver, organization=org, role='admin', is_primary=True)
UserDepartment.objects.create(user=approver, organization=org, department=dept, is_primary=True)

# Simple workflow graph
graph_data = {
    'nodes': [
        {'id': 'start_1', 'type': 'start', 'x': 100, 'y': 100, 'text': 'Start'},
        {'id': 'approval_1', 'type': 'approval', 'x': 300, 'y': 100, 'text': 'Department Approval',
         'properties': {'approveType': 'or', 'approvers': [{'type': 'user', 'user_id': str(approver.id)}], 'timeout': 72}},
        {'id': 'end_1', 'type': 'end', 'x': 500, 'y': 100, 'text': 'End'}
    ],
    'edges': [
        {'id': 'edge_1', 'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1'},
        {'id': 'edge_2', 'sourceNodeId': 'approval_1', 'targetNodeId': 'end_1'}
    ]
}

# Create definition
definition = WorkflowDefinition.objects.create(
    organization=org,
    code='simple_approval3',
    name='Simple Approval3',
    business_object_code='asset_pickup',
    status='published',
    graph_data=graph_data,
    created_by=admin
)

# Create instance
instance = WorkflowInstance.objects.create(
    organization=org,
    definition=definition,
    instance_no='TEST-003',
    business_object_code='asset_pickup',
    business_id='ASSET_003',
    initiator=initiator,
    status=WorkflowInstance.STATUS_RUNNING,
    created_by=initiator
)

# Create task
task = WorkflowTask.objects.create(
    organization=org,
    instance=instance,
    node_id='approval_1',
    node_name='Department Approval',
    node_type='approval',
    assignee=approver,
    status=WorkflowTask.STATUS_PENDING,
    created_by=initiator
)

# Test approve endpoint
client = APIClient()
client.force_authenticate(user=approver)
url = f'/api/workflows/tasks/{task.id}/approve/'
response = client.post(url, {'comment': 'Approved'}, format='json')

print('Status:', response.status_code)
print('Data:', response.data)
print('Type:', type(response.data))
