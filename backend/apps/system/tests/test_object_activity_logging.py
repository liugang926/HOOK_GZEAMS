import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.activity_log import ActivityLog
from apps.system.models import BusinessObject


@pytest.mark.django_db
def test_object_router_update_creates_activity_log():
    organization = Organization.objects.create(name='Audit Org', code='audit-org')
    user = User.objects.create(username='audit-user', organization=organization)

    BusinessObject.objects.create(
        code='Organization',
        name='Organization',
        is_hardcoded=True,
        django_model_path='apps.organizations.models.Organization',
    )

    target = Organization.objects.create(name='Old Name', code='tracked-org')

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.patch(
        f'/api/system/objects/Organization/{target.id}/',
        {'name': 'New Name'},
        format='json',
    )

    assert response.status_code == 200

    content_type = ContentType.objects.get_for_model(Organization)
    log = ActivityLog.objects.get(
        content_type=content_type,
        object_id=str(target.id),
        action='update',
    )

    assert log.actor == user
    assert log.organization == organization
    assert isinstance(log.changes, list)
    assert log.changes[0]['fieldCode'] == 'name'
    assert log.changes[0]['oldValue'] == 'Old Name'
    assert log.changes[0]['newValue'] == 'New Name'
