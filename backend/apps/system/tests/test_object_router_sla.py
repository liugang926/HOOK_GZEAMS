from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject
from apps.workflows.models import WorkflowDefinition, WorkflowInstance, WorkflowTask

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='Object router SLA tests run against PostgreSQL-backed object routing behavior.',
)


def _create_workflow_definition(*, organization, user, business_object_code: str) -> WorkflowDefinition:
    return WorkflowDefinition.objects.create(
        organization=organization,
        code=f"sla_{business_object_code.lower()}_{organization.code.lower()}",
        name='SLA Workflow',
        business_object_code=business_object_code,
        status='published',
        graph_data={
            'nodes': [
                {'id': 'start_1', 'type': 'start', 'text': 'Start'},
                {'id': 'approval_1', 'type': 'approval', 'text': 'Approval'},
                {'id': 'end_1', 'type': 'end', 'text': 'End'},
            ],
            'edges': [
                {'id': 'edge_1', 'sourceNodeId': 'start_1', 'targetNodeId': 'approval_1'},
                {'id': 'edge_2', 'sourceNodeId': 'approval_1', 'targetNodeId': 'end_1'},
            ],
        },
        created_by=user,
    )


def _register_organization_object():
    BusinessObject.objects.get_or_create(
        code='Organization',
        defaults={
            'name': 'Organization',
            'is_hardcoded': True,
            'django_model_path': 'apps.organizations.models.Organization',
        },
    )


@pytest.mark.django_db
def test_object_router_sla_returns_empty_summary_when_no_instance():
    organization = Organization.objects.create(name='SLA Org', code='sla-org')
    user = User.objects.create(username='slauser', organization=organization)
    _register_organization_object()

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f'/api/system/objects/Organization/{organization.id}/sla/')
    assert response.status_code == 200

    payload = response.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['objectCode'] == 'Organization'
    assert data['businessId'] == str(organization.id)
    assert data['hasInstance'] is False
    assert data['status'] == 'unknown'
    assert data['dueDate'] is None
    assert data['assignee'] is None


@pytest.mark.django_db
def test_object_router_sla_returns_overdue_summary_for_active_workflow_task():
    organization = Organization.objects.create(name='Active SLA Org', code='active-sla-org')
    user = User.objects.create(username='active-sla-user', organization=organization)
    _register_organization_object()
    definition = _create_workflow_definition(
        organization=organization,
        user=user,
        business_object_code='organization',
    )
    workflow_instance = WorkflowInstance.objects.create(
        organization=organization,
        definition=definition,
        instance_no='WF-SLA-001',
        business_object_code='organization',
        business_id=str(organization.id),
        initiator=user,
        status=WorkflowInstance.STATUS_PENDING_APPROVAL,
        current_node_id='approval_1',
        current_node_name='Department Approval',
        created_by=user,
    )
    overdue_task = WorkflowTask.objects.create(
        organization=organization,
        instance=workflow_instance,
        node_id='approval_1',
        node_name='Department Approval',
        node_type='approval',
        assignee=user,
        status=WorkflowTask.STATUS_PENDING,
        due_date=timezone.now() - timedelta(hours=5),
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f'/api/system/objects/Organization/{organization.id}/sla/')
    assert response.status_code == 200

    payload = response.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['hasInstance'] is True
    assert data['instanceId'] == str(workflow_instance.id)
    assert data['instanceNo'] == 'WF-SLA-001'
    assert data['status'] == 'overdue'
    assert data['hoursOverdue'] > 0
    assert data['activeTaskId'] == str(overdue_task.id)
    assert data['activeTaskCount'] == 1
    assert data['currentNode']['name'] == 'Department Approval'
    assert data['assignee']['username'] == 'active-sla-user'


@pytest.mark.django_db
def test_object_router_sla_returns_completed_status_for_terminal_instance():
    organization = Organization.objects.create(name='Completed SLA Org', code='completed-sla-org')
    user = User.objects.create(username='completed-sla-user', organization=organization)
    _register_organization_object()
    definition = _create_workflow_definition(
        organization=organization,
        user=user,
        business_object_code='Organization',
    )
    workflow_instance = WorkflowInstance.objects.create(
        organization=organization,
        definition=definition,
        instance_no='WF-SLA-002',
        business_object_code='Organization',
        business_id=str(organization.id),
        initiator=user,
        status=WorkflowInstance.STATUS_APPROVED,
        current_node_id='end_1',
        current_node_name='Completed',
        completed_at=timezone.now(),
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(f'/api/system/objects/Organization/{organization.id}/sla/')
    assert response.status_code == 200

    payload = response.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['hasInstance'] is True
    assert data['instanceId'] == str(workflow_instance.id)
    assert data['status'] == 'completed'
    assert data['instanceStatus'] == WorkflowInstance.STATUS_APPROVED
    assert data['activeTaskCount'] == 0
    assert data['assignee'] is None
