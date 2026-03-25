import pytest

from apps.system.menu_config import build_menu_config_for_object
from apps.system.models import BusinessObject, MenuEntry
from apps.system.services.object_registry import ObjectRegistry
from apps.system.menu_config import sync_menu_registry_models


@pytest.mark.django_db
def test_object_registry_auto_registers_asset_project_objects():
    BusinessObject.objects.filter(
        code__in=["AssetProject", "ProjectAsset", "ProjectMember"]
    ).delete()

    ObjectRegistry.auto_register_standard_objects()

    asset_project = BusinessObject.objects.get(code="AssetProject")
    project_asset = BusinessObject.objects.get(code="ProjectAsset")
    project_member = BusinessObject.objects.get(code="ProjectMember")

    assert asset_project.django_model_path == "apps.projects.models.AssetProject"
    assert project_asset.django_model_path == "apps.projects.models.ProjectAsset"
    assert project_member.django_model_path == "apps.projects.models.ProjectMember"


def test_build_menu_config_for_asset_project_uses_lifecycle_defaults():
    asset_project_config = build_menu_config_for_object("AssetProject", {})
    project_asset_config = build_menu_config_for_object("ProjectAsset", {})
    project_member_config = build_menu_config_for_object("ProjectMember", {})

    assert asset_project_config["url"] == "/objects/AssetProject"
    assert asset_project_config["group_code"] == "lifecycle"
    assert asset_project_config["show_in_menu"] is True
    assert asset_project_config["workbench"]["workspace_mode"] == "extended"
    assert asset_project_config["workbench"]["toolbar"]["primary_actions"][0]["code"] == "refresh_rollups"
    assert asset_project_config["workbench"]["toolbar"]["secondary_actions"][0]["code"] == "close_project"
    assert asset_project_config["workbench"]["detail_panels"][0]["component"] == "asset-project-overview"
    assert asset_project_config["workbench"]["detail_panels"][1]["component"] == "asset-project-assets"
    assert asset_project_config["workbench"]["detail_panels"][2]["component"] == "asset-project-members"
    assert asset_project_config["workbench"]["detail_panels"][3]["component"] == "asset-project-returns"
    assert asset_project_config["workbench"]["detail_panels"][4]["component"] == "asset-project-return-history"

    assert project_asset_config["url"] == "/objects/ProjectAsset"
    assert project_asset_config["show_in_menu"] is False
    assert project_member_config["url"] == "/objects/ProjectMember"
    assert project_member_config["show_in_menu"] is False


@pytest.mark.django_db
def test_sync_menu_registry_creates_asset_project_navigation_entry():
    BusinessObject.objects.get_or_create(
        code="AssetProject",
        defaults={
            "name": "Asset Project",
            "is_hardcoded": True,
            "django_model_path": "apps.projects.models.AssetProject",
        },
    )

    sync_menu_registry_models()

    entry = MenuEntry.objects.get(source_type="business_object", source_code="AssetProject")
    assert entry.route_path == "/objects/AssetProject"
    assert entry.is_visible is True
    assert entry.icon == "Collection"
