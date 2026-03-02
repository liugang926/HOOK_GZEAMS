"""Debug script for approve task."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask
from apps.organizations.models import Organization, Department, UserDepartment
from apps.accounts.models import User, UserOrganization

# Clean up existing test data
User.objects.filter(username__in=['admin_debug', 'initiator_debug', 'approver_debug']).delete()
Organization.objects.filter(code='DEBUG_ORG').delete()

# Create organization
org = Organization.objects.create(code='DEBUG_ORG', name='Debug Org', org_type='company', is_active=True)
dept = Department.objects.create(code='DEBUG_DEPT', organization=org, name='Debug Dept')

# Create users
admin = User.objects.create_user(username='admin_debug', email='admin_debug@test.com', is_staff=True, is_superuser=True, is_active=True)
admin.current_organization = org
admin.save()
UserOrganization.objects.create(user=admin, organization=org, role='admin', is_primary=True)

initiator = User.objects.create_user(username='initiator_debug', email='initiator_debug@test.com', is_active=True)
initiator.current_organization = org
initiator.save()
UserOrganization.objects.create(user=initiator, organization=org, role='member', is_primary=True)
UserDepartment.objects.create(user=initiator, organization=org, department=dept, is_primary=True)

approver = User.objects.create_user(username='approver_debug', email='approver_debug@test.com', is_active=True)
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
    code='debug_approval',
    name='Debug Approval',
    business_object_code='asset_pickup',
    status='published',
    graph_data=graph_data,
    created_by=admin
)

# Create instance
instance = WorkflowInstance.objects.create(
    organization=org,
    definition=definition,
    instance_no='DEBUG-001',
    business_object_code='asset_pickup',
    business_id='ASSET_DEBUG',
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

print(f"Created task: {task.id}")
print(f"Task assignee: {task.assignee.username}")
print(f"Approver user: {approver.username}")
print(f"Task status: {task.status}")

# Test approve endpoint
client = APIClient()
client.force_authenticate(user=approver)
url = f'/api/workflows/tasks/{task.id}/approve/'
print(f"\nCalling: POST {url}")
print(f"Data: {{'comment': 'Approved'}}")

response = client.post(url, {'comment': 'Approved'}, format='json')

print(f"\nStatus Code: {response.status_code}")
print(f"Response Type: {type(response.data)}")

if isinstance(response.data, dict):
    print(f"Response Keys: {response.data.keys()}")
    print(f"Success: {response.data.get('success')}")
    print(f"Message: {response.data.get('message')}")
    if 'error' in response.data:
        print(f"Error Code: {response.data.get('error', {}).get('code')}")
        print(f"Error Message: {response.data.get('error', {}).get('message')}")
else:
    print(f"Response Data: {response.data}")

# Check task after approval
task.refresh_from_db()
print(f"\nTask status after: {task.status}")
