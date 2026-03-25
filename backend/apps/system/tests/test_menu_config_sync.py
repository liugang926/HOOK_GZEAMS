import pytest

from apps.system.menu_config import build_menu_config_for_object, sync_menu_registry_models
from apps.system.models import BusinessObject, MenuEntry


def test_build_menu_config_preserves_workbench_extensions():
    config = build_menu_config_for_object(
        "FinanceVoucher",
        {
            "badge": {"variant": "warning"},
            "workbench": {
                "workspace_mode": "extended",
                "legacy_aliases": ["/finance/vouchers"],
            },
        },
    )

    assert config["url"] == "/objects/FinanceVoucher"
    assert config["show_in_menu"] is False
    assert config["badge"] == {"variant": "warning"}
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["legacy_aliases"] == ["/finance/vouchers"]


def test_build_menu_config_merges_asset_project_default_workbench_with_existing_overrides():
    config = build_menu_config_for_object(
        "AssetProject",
        {
            "workbench": {
                "toolbar": {
                    "secondary_actions": [
                        {
                            "code": "archive_snapshot",
                        }
                    ],
                },
            },
        },
    )

    assert config["url"] == "/objects/AssetProject"
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["code"] == "refresh_rollups"
    assert config["workbench"]["toolbar"]["secondary_actions"][0]["code"] == "archive_snapshot"
    assert config["workbench"]["detail_panels"][0]["component"] == "asset-project-overview"
    assert config["workbench"]["detail_panels"][1]["component"] == "asset-project-assets"
    assert config["workbench"]["detail_panels"][3]["component"] == "asset-project-returns"
    assert config["workbench"]["detail_panels"][4]["component"] == "asset-project-return-history"


@pytest.mark.django_db
def test_sync_menu_registry_updates_finance_voucher_entry_route_and_visibility():
    finance_voucher, _ = BusinessObject.objects.get_or_create(
        code="FinanceVoucher",
        defaults={
            "name": "Finance Voucher",
            "is_hardcoded": True,
            "django_model_path": "apps.finance.models.FinanceVoucher",
        },
    )

    sync_menu_registry_models()

    entry = MenuEntry.objects.get(source_type="business_object", source_code="FinanceVoucher")
    entry.route_path = "/finance/vouchers"
    entry.is_visible = True
    entry.icon = "Document"
    entry.sort_order = 999
    entry.save(update_fields=["route_path", "is_visible", "icon", "sort_order"])

    sync_menu_registry_models()

    entry.refresh_from_db()
    assert entry.route_path == "/objects/FinanceVoucher"
    assert entry.is_visible is False
    assert entry.icon == "Tickets"
    assert entry.sort_order == 10
    assert entry.business_object_id == finance_voucher.id
