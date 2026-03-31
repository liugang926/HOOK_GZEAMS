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
    assert config["workbench"]["summary_cards"][0]["code"] == "project_asset_count"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"


@pytest.mark.django_db
def test_sync_menu_registry_creates_user_portal_navigation_entry():
    sync_menu_registry_models()

    entry = MenuEntry.objects.get(source_type="static", source_code="UserPortal")

    assert entry.route_path == "/portal"
    assert entry.translation_key == "menu.routes.userPortal"
    assert entry.menu_group.code == "workflow"
    assert entry.icon == "User"
    assert entry.is_visible is True


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


def test_build_menu_config_hides_asset_status_log_from_navigation():
    config = build_menu_config_for_object(
        "AssetStatusLog",
        {
            "show_in_menu": True,
            "group_code": "asset_master",
        },
    )

    assert config["url"] == "/objects/AssetStatusLog"
    assert config["show_in_menu"] is False


def test_build_menu_config_includes_finance_voucher_closed_loop_workbench():
    config = build_menu_config_for_object("FinanceVoucher", {})

    assert config["url"] == "/objects/FinanceVoucher"
    assert config["show_in_menu"] is False
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["summary_cards"][0]["code"] == "voucher_total_amount"
    assert config["workbench"]["summary_cards"][3]["value_field"] == "source_object_label"
    assert config["workbench"]["summary_cards"][4]["value_field"] == "source_record_no"
    assert config["workbench"]["queue_panels"][0]["code"] == "voucher_review_queue"
    assert config["workbench"]["exception_panels"][0]["code"] == "voucher_integration_attention"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "closure_summary.metrics.failed_sync_count"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"
    assert config["workbench"]["closure_panel"]["progress_field"] == "closure_summary.completion_display"
    assert config["workbench"]["recommended_actions"][0]["action_path"] == "push"
    assert config["workbench"]["detail_panels"][0]["component"] == "finance-voucher-entries"


def test_build_menu_config_includes_asset_closed_loop_workbench():
    config = build_menu_config_for_object("Asset", {})

    assert config["url"] == "/objects/Asset"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["summary_cards"][0]["value_field"] == "source_purchase_request_no"
    assert config["workbench"]["summary_cards"][2]["value_field"] == "closure_summary.metrics.active_project_allocation_count"
    assert config["workbench"]["summary_cards"][6]["value_field"] == "closure_summary.metrics.linked_finance_voucher_count"
    assert config["workbench"]["summary_cards"][7]["value_field"] == "closure_summary.metrics.open_finance_voucher_count"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/ProjectAsset?asset={id}&return_status=in_use"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/InventoryItem?asset={id}&unresolved_only=true"
    assert config["workbench"]["queue_panels"][4]["route"] == "/objects/FinanceVoucher?source_asset={id}"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "closure_summary.metrics.pending_inventory_follow_up_count"
    assert config["workbench"]["closure_panel"]["blocker_field"] == "closure_summary.blocker"
    assert config["workbench"]["recommended_actions"] == []


def test_build_menu_config_includes_purchase_request_closed_loop_workbench():
    config = build_menu_config_for_object("PurchaseRequest", {})

    assert config["url"] == "/objects/PurchaseRequest"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["summary_cards"][1]["value_field"] == "closure_summary.metrics.linked_receipt_count"
    assert config["workbench"]["summary_cards"][4]["value_field"] == "closure_summary.metrics.linked_finance_voucher_count"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/AssetReceipt?purchase_request_id={id}"
    assert config["workbench"]["queue_panels"][2]["route"] == "/objects/FinanceVoucher?source_purchase_request={id}"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "closure_summary.metrics.pending_generation_count"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"


def test_build_menu_config_includes_asset_receipt_closed_loop_workbench():
    config = build_menu_config_for_object("AssetReceipt", {})

    assert config["url"] == "/objects/AssetReceipt"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["summary_cards"][0]["value_field"] == "closure_summary.metrics.source_purchase_request_no"
    assert config["workbench"]["summary_cards"][2]["value_field"] == "closure_summary.metrics.generated_asset_count"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/Asset?source_receipt={id}"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/FinanceVoucher?source_receipt={id}"
    assert config["workbench"]["exception_panels"][0]["route"] == "/objects/AssetReceiptItem?asset_receipt_id={id}&asset_generated=false"
    assert config["workbench"]["closure_panel"]["progress_field"] == "closure_summary.completion_display"


def test_build_menu_config_includes_inventory_task_closed_loop_workbench():
    config = build_menu_config_for_object("InventoryTask", {})

    assert config["url"] == "/objects/InventoryTask"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "submit-workflow"
    assert config["workbench"]["toolbar"]["primary_actions"][1]["action_path"] == "start"
    assert config["workbench"]["detail_panels"][0]["component"] == "inventory-task-executor-progress"
    assert config["workbench"]["summary_cards"][2]["value_field"] == "progress_percentage"
    assert config["workbench"]["summary_cards"][3]["value_field"] == "difference_summary.total_differences"
    assert config["workbench"]["summary_cards"][5]["value_field"] == "difference_summary.manual_follow_up_open_count"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/InventoryTask?status=in_progress"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/InventoryItem?task={id}&status=pending"
    assert config["workbench"]["queue_panels"][6]["route"] == "/objects/InventoryItem?task={id}&manual_follow_up_only=true&unresolved_only=true"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "difference_summary.by_type.missing"
    assert config["workbench"]["exception_panels"][2]["route"] == "/objects/InventoryItem?task={id}&difference_type=location_mismatch"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"
    assert config["workbench"]["closure_panel"]["progress_field"] == "closure_summary.completion_display"
    assert config["workbench"]["sla_indicators"][0]["code"] == "inventory_task_workflow_sla"
    assert config["workbench"]["recommended_actions"][0]["action_path"] == "submit-workflow"


def test_build_menu_config_includes_inventory_item_difference_workbench():
    config = build_menu_config_for_object("InventoryItem", {})

    assert config["url"] == "/objects/InventoryItem"
    assert config["show_in_menu"] is False
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "confirm"
    assert config["workbench"]["toolbar"]["secondary_actions"][0]["action_path"] == "ignore"
    assert config["workbench"]["detail_panels"][0]["component"] == "inventory-difference-closure"
    assert config["workbench"]["detail_panels"][0]["props"]["linked_action_options"][0]["code"] == "location_correction"
    assert config["workbench"]["detail_panels"][0]["props"]["linked_action_options"][2]["code"] == "asset.create_maintenance"
    assert config["workbench"]["summary_cards"][0]["value_field"] == "difference_type_label"
    assert config["workbench"]["closure_panel"]["owner_field"] == "closure_summary.owner"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"
    assert config["workbench"]["closure_panel"]["blocker_field"] == "closure_summary.blocker"
    assert config["workbench"]["recommended_actions"] == []


def test_build_menu_config_includes_inventory_follow_up_workbench():
    config = build_menu_config_for_object("InventoryFollowUp", {})

    assert config["url"] == "/objects/InventoryFollowUp"
    assert config["show_in_menu"] is False
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "complete"
    assert config["workbench"]["toolbar"]["secondary_actions"][0]["action_path"] == "reopen"
    assert config["workbench"]["summary_cards"][0]["value_field"] == "status_label"
    assert config["workbench"]["summary_cards"][3]["value_field"] == "reminder_count"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"
    assert config["workbench"]["closure_panel"]["owner_field"] == "closure_summary.owner"


def test_build_menu_config_includes_insurance_policy_workbench():
    config = build_menu_config_for_object("InsurancePolicy", {})

    assert config["url"] == "/objects/InsurancePolicy"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "activate"
    assert config["workbench"]["summary_cards"][2]["value_field"] == "closure_summary.metrics.pending_payment_count"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/ClaimRecord?policy={id}"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "closure_summary.metrics.pending_payment_count"
    assert config["workbench"]["closure_panel"]["stage_field"] == "closure_summary.stage"
    assert config["workbench"]["recommended_actions"][0]["action_path"] == "activate"


def test_build_menu_config_includes_claim_record_workbench():
    config = build_menu_config_for_object("ClaimRecord", {})

    assert config["url"] == "/objects/ClaimRecord"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "approve"
    assert config["workbench"]["toolbar"]["primary_actions"][1]["action_path"] == "record-payment"
    assert config["workbench"]["summary_cards"][3]["suffix"] == "%"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/ClaimRecord?status=approved"
    assert config["workbench"]["closure_panel"]["progress_field"] == "closure_summary.completion_display"
    assert config["workbench"]["recommended_actions"][1]["action_path"] == "record-payment"


def test_build_menu_config_includes_leasing_contract_workbench():
    config = build_menu_config_for_object("LeasingContract", {})

    assert config["url"] == "/objects/LeasingContract"
    assert config["show_in_menu"] is True
    assert config["workbench"]["workspace_mode"] == "extended"
    assert config["workbench"]["toolbar"]["primary_actions"][0]["action_path"] == "activate"
    assert config["workbench"]["toolbar"]["primary_actions"][1]["action_path"] == "complete"
    assert config["workbench"]["summary_cards"][0]["value_field"] == "closure_summary.metrics.leased_asset_count"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/RentPayment?contract={id}"
    assert config["workbench"]["exception_panels"][0]["count_field"] == "closure_summary.metrics.unsettled_damage_count"
    assert config["workbench"]["closure_panel"]["blocker_field"] == "closure_summary.blocker"
    assert config["workbench"]["recommended_actions"][0]["action_path"] == "activate"


def test_build_menu_config_includes_asset_project_closure_sections():
    config = build_menu_config_for_object("AssetProject", {})

    assert config["url"] == "/objects/AssetProject"
    assert config["show_in_menu"] is True
    assert config["workbench"]["summary_cards"][1]["value_field"] == "active_asset_count"
    assert config["workbench"]["summary_cards"][3]["suffix"] == "%"
    assert config["workbench"]["summary_cards"][4]["value_field"] == "closure_summary.metrics.pending_return_count"
    assert config["workbench"]["queue_panels"][0]["route"] == "/objects/ProjectAsset?project={id}&return_status=in_use"
    assert config["workbench"]["queue_panels"][1]["route"] == "/objects/AssetReturn?project={id}&status=pending"
    assert config["workbench"]["closure_panel"]["progress_field"] == "closure_summary.completion_display"
    assert config["workbench"]["recommended_actions"][0]["action_path"] == "close"
