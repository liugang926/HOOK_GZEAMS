from django.core.management import call_command

import pytest

from apps.organizations.models import Organization
from apps.system.models import BusinessObject, PageLayout


@pytest.mark.django_db
def test_archive_legacy_list_layouts_dry_run_keeps_rows_active():
    org = Organization.objects.create(name="Archive List Org", code="archive-list-org")
    bo = BusinessObject.objects.create(code="ARCLISTOBJ", name="Archive List Object", is_hardcoded=False)

    list_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="arclistobj_list_default",
        layout_name="Legacy List",
        layout_type="list",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"columns": [{"fieldCode": "name", "label": "Name"}]},
    )

    call_command("archive_legacy_list_layouts")

    list_layout.refresh_from_db()
    assert list_layout.status == "published"
    assert list_layout.is_active is True
    assert list_layout.is_default is True


@pytest.mark.django_db
def test_archive_legacy_list_layouts_apply_archives_rows():
    org = Organization.objects.create(name="Archive List Org 2", code="archive-list-org-2")
    bo = BusinessObject.objects.create(code="ARCLISTOBJ2", name="Archive List Object 2", is_hardcoded=False)

    list_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="arclistobj2_list_default",
        layout_name="Legacy List",
        layout_type="list",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"columns": [{"fieldCode": "name", "label": "Name"}]},
    )

    call_command("archive_legacy_list_layouts", "--apply")

    list_layout.refresh_from_db()
    assert list_layout.status == "archived"
    assert list_layout.is_active is False
    assert list_layout.is_default is False

