import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.system.models import BusinessObject, FieldDefinition, PageLayout


def _section(title: object) -> dict:
    return {
        "id": "basic",
        "name": "basic",
        "title": title,
        "columns": 2,
        "fields": [{"fieldCode": "name", "label": "Name"}],
    }


def _create_layout(
    business_object: BusinessObject,
    *,
    layout_type: str,
    layout_config: dict,
) -> None:
    PageLayout.objects.create(
        business_object=business_object,
        layout_code=f"{business_object.code.lower()}_{layout_type}",
        layout_name=f"{business_object.name} [{layout_type}]",
        layout_type=layout_type,
        mode="readonly" if layout_type == "detail" else ("search" if layout_type == "search" else "edit"),
        status="published",
        is_default=True,
        is_active=True,
        layout_config=layout_config,
    )


def _create_field(business_object: BusinessObject) -> None:
    FieldDefinition.objects.create(
        business_object=business_object,
        code="name",
        name="Name",
        field_type="text",
        show_in_form=True,
        show_in_detail=True,
        show_in_list=True,
        sort_order=1,
    )


@pytest.mark.django_db
def test_verify_runtime_defaults_passes_for_standard_layouts():
    business_object = BusinessObject.objects.create(
        code="VERIFYOK",
        name="Verify OK",
        is_hardcoded=False,
    )
    _create_field(business_object)

    title_payload = {"translationKey": "system.pageLayout.sections.basic"}

    _create_layout(business_object, layout_type="form", layout_config={"sections": [_section(title_payload)]})
    _create_layout(
        business_object,
        layout_type="detail",
        layout_config={"sections": [_section(title_payload)]},
    )
    _create_layout(
        business_object,
        layout_type="search",
        layout_config={"sections": [_section(title_payload)]},
    )

    call_command("verify_runtime_defaults", "--object-code", "VERIFYOK")


@pytest.mark.django_db
def test_verify_runtime_defaults_fails_when_section_title_lacks_translation_key():
    business_object = BusinessObject.objects.create(
        code="VERIFYBAD",
        name="Verify Bad",
        is_hardcoded=False,
    )
    _create_field(business_object)

    _create_layout(
        business_object,
        layout_type="form",
        layout_config={"sections": [_section("Basic")]},
    )
    _create_layout(
        business_object,
        layout_type="detail",
        layout_config={"sections": [_section({"translationKey": "system.pageLayout.sections.basic"})]},
    )
    _create_layout(
        business_object,
        layout_type="search",
        layout_config={"sections": [_section({"translationKey": "system.pageLayout.sections.basic"})]},
    )

    with pytest.raises(CommandError, match="missing translationKey payload"):
        call_command("verify_runtime_defaults", "--object-code", "VERIFYBAD")
