import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.activity_log import ActivityLog
from apps.system.models import BusinessObject


@pytest.mark.django_db
def test_activity_logs_list_filters_by_object_code_and_object_id():
    organization = Organization.objects.create(name="Timeline Org", code="timeline-org")
    user = User.objects.create(username="timeline-user", organization=organization)

    BusinessObject.objects.create(
        code="Organization",
        name="Organization",
        is_hardcoded=True,
        django_model_path="apps.organizations.models.Organization",
    )

    target_record = Organization.objects.create(name="History Target", code="history-target")
    other_record = Organization.objects.create(name="Other Target", code="other-target")
    content_type = ContentType.objects.get_for_model(Organization)

    ActivityLog.objects.create(
        organization=organization,
        actor=user,
        created_by=user,
        action="update",
        content_type=content_type,
        object_id=str(target_record.id),
        description="Name updated",
        changes=[{"fieldLabel": "Name", "fieldCode": "name", "oldValue": "Old", "newValue": "New"}],
    )
    ActivityLog.objects.create(
        organization=organization,
        actor=user,
        created_by=user,
        action="update",
        content_type=content_type,
        object_id=str(other_record.id),
        description="Should be filtered out",
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get(
        "/api/system/activity-logs/",
        {"object_code": "Organization", "object_id": str(target_record.id)},
    )

    assert response.status_code == 200
    payload = response.json()
    data = payload.get("data", payload)
    results = data.get("results", [])

    assert len(results) == 1
    assert results[0]["description"] == "Name updated"
    assert results[0]["action"] == "update"
    assert results[0]["changes"][0]["fieldCode"] == "name"
