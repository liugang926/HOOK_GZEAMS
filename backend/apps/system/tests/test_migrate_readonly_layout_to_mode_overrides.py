import pytest
from django.core.management import call_command

from apps.organizations.models import Organization
from apps.system.models import BusinessObject, PageLayout


def _build_sections(label: str):
    return [
        {
            "id": "section-basic",
            "type": "section",
            "title": "Basic",
            "fields": [
                {
                    "id": "field-name",
                    "fieldCode": "name",
                    "label": label,
                    "span": 12,
                }
            ],
        }
    ]


@pytest.mark.django_db
def test_migrate_readonly_layout_to_mode_overrides_apply():
    org = Organization.objects.create(name="ModeOverride Org", code="mode-override-org")
    bo = BusinessObject.objects.create(code="MIGROBJ", name="Migration Object", is_hardcoded=False)

    edit_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobj_edit_default",
        layout_name="Edit Layout",
        layout_type="form",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name")},
    )
    readonly_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobj_detail_default",
        layout_name="Readonly Layout",
        layout_type="detail",
        mode="readonly",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name (Readonly)")},
    )

    call_command(
        "migrate_readonly_layout_to_mode_overrides",
        "--object-code",
        bo.code,
        "--organization-id",
        str(org.id),
        "--apply",
    )

    edit_layout.refresh_from_db()
    readonly_layout.refresh_from_db()

    mode_overrides = edit_layout.layout_config.get("modeOverrides")
    assert isinstance(mode_overrides, dict)
    assert isinstance(mode_overrides.get("readonly"), dict)
    migrated_sections = mode_overrides["readonly"].get("sections") or []
    assert migrated_sections[0]["fields"][0]["label"] == "Name (Readonly)"

    # Legacy readonly layout remains available unless archive flag is provided.
    assert readonly_layout.is_active is True
    assert readonly_layout.status == "published"


@pytest.mark.django_db
def test_migrate_readonly_layout_to_mode_overrides_archive_legacy():
    org = Organization.objects.create(name="Archive Org", code="mode-override-archive-org")
    bo = BusinessObject.objects.create(code="MIGROBJARCH", name="Migration Archive Object", is_hardcoded=False)

    edit_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjarch_edit_default",
        layout_name="Edit Layout",
        layout_type="form",
        mode="edit",
        status="draft",
        is_default=False,
        is_active=True,
        layout_config={"sections": _build_sections("Name")},
    )
    readonly_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjarch_detail_default",
        layout_name="Readonly Layout",
        layout_type="detail",
        mode="readonly",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name (Readonly)")},
    )

    call_command(
        "migrate_readonly_layout_to_mode_overrides",
        "--object-code",
        bo.code,
        "--organization-id",
        str(org.id),
        "--apply",
        "--archive-legacy",
        "--overwrite-existing-readonly-override",
    )

    edit_layout.refresh_from_db()
    readonly_layout.refresh_from_db()

    mode_overrides = edit_layout.layout_config.get("modeOverrides")
    assert isinstance(mode_overrides, dict)
    migrated_sections = mode_overrides["readonly"].get("sections") or []
    assert migrated_sections[0]["fields"][0]["label"] == "Name (Readonly)"

    assert readonly_layout.status == "archived"
    assert readonly_layout.is_active is False
    assert readonly_layout.is_default is False


@pytest.mark.django_db
def test_migrate_readonly_layout_to_mode_overrides_archive_search():
    org = Organization.objects.create(name="Archive Search Org", code="mode-override-archive-search-org")
    bo = BusinessObject.objects.create(code="MIGROBJSEARCH", name="Migration Search Object", is_hardcoded=False)

    edit_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjsearch_edit_default",
        layout_name="Edit Layout",
        layout_type="form",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name")},
    )
    search_layout = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjsearch_search_default",
        layout_name="Search Layout",
        layout_type="search",
        mode="search",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name (Search)")},
    )

    call_command(
        "migrate_readonly_layout_to_mode_overrides",
        "--object-code",
        bo.code,
        "--organization-id",
        str(org.id),
        "--apply",
        "--archive-search",
    )

    edit_layout.refresh_from_db()
    search_layout.refresh_from_db()

    assert edit_layout.is_active is True
    assert edit_layout.is_default is True

    assert search_layout.status == "archived"
    assert search_layout.is_active is False
    assert search_layout.is_default is False


@pytest.mark.django_db
def test_migrate_readonly_layout_to_mode_overrides_enforce_single_default_edit():
    org = Organization.objects.create(name="Single Default Org", code="mode-override-single-default-org")
    bo = BusinessObject.objects.create(code="MIGROBJDEF", name="Migration Default Object", is_hardcoded=False)

    first_edit = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjdef_edit_default_a",
        layout_name="Edit Layout A",
        layout_type="form",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name A")},
        priority="global",
    )
    second_edit = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code="migrobjdef_edit_default_b",
        layout_name="Edit Layout B",
        layout_type="form",
        mode="edit",
        status="published",
        is_default=True,
        is_active=True,
        layout_config={"sections": _build_sections("Name B")},
        priority="global",
    )

    call_command(
        "migrate_readonly_layout_to_mode_overrides",
        "--object-code",
        bo.code,
        "--organization-id",
        str(org.id),
        "--apply",
        "--enforce-single-default-edit",
    )

    first_edit.refresh_from_db()
    second_edit.refresh_from_db()

    active_default_ids = set(
        PageLayout.objects.filter(
            business_object=bo,
            organization=org,
            mode="edit",
            layout_type="form",
            is_active=True,
            is_default=True,
            is_deleted=False,
        ).values_list("id", flat=True)
    )
    assert len(active_default_ids) == 1
    assert second_edit.id in active_default_ids
    assert first_edit.is_default is False
