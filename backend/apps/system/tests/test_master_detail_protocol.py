import pytest

from apps.system.models import BusinessObject, ObjectRelationDefinition
from apps.system.services.business_object_service import BusinessObjectService
from apps.system.services.hardcoded_object_sync_service import HardcodedObjectSyncService


@pytest.mark.django_db
def test_line_item_catalog_defaults_follow_master_detail_protocol():
    hardcoded_objects = {
        obj["code"]: obj
        for obj in BusinessObjectService().get_all_objects(
            include_hardcoded=True,
            include_custom=False,
        )["hardcoded"]
    }

    pickup_item = hardcoded_objects["PickupItem"]
    assert pickup_item["object_role"] == "detail"
    assert pickup_item["is_menu_hidden"] is True
    assert pickup_item["is_top_level_navigable"] is False
    assert pickup_item["allow_standalone_query"] is True
    assert pickup_item["allow_standalone_route"] is False
    assert pickup_item["inherit_permissions"] is True
    assert pickup_item["inherit_workflow"] is True
    assert pickup_item["inherit_status"] is True
    assert pickup_item["inherit_lifecycle"] is True

    asset_receipt_item = hardcoded_objects["AssetReceiptItem"]
    assert asset_receipt_item["object_role"] == "detail"
    assert asset_receipt_item["is_menu_hidden"] is True
    assert asset_receipt_item["is_top_level_navigable"] is False
    assert asset_receipt_item["allow_standalone_query"] is True
    assert asset_receipt_item["allow_standalone_route"] is False
    assert asset_receipt_item["inherit_permissions"] is True
    assert asset_receipt_item["inherit_workflow"] is True
    assert asset_receipt_item["inherit_status"] is True
    assert asset_receipt_item["inherit_lifecycle"] is True

    disposal_item = hardcoded_objects["DisposalItem"]
    assert disposal_item["object_role"] == "detail"
    assert disposal_item["is_menu_hidden"] is True
    assert disposal_item["is_top_level_navigable"] is False
    assert disposal_item["allow_standalone_query"] is True
    assert disposal_item["allow_standalone_route"] is False
    assert disposal_item["inherit_permissions"] is True
    assert disposal_item["inherit_workflow"] is True
    assert disposal_item["inherit_status"] is True
    assert disposal_item["inherit_lifecycle"] is True


@pytest.mark.django_db
def test_hardcoded_sync_service_applies_master_detail_defaults_for_line_items():
    service = HardcodedObjectSyncService()
    definition = service.get_definition("PickupItem")
    assert definition is not None

    synced = service.ensure_business_object(definition, overwrite_existing=True)
    synced.business_object.refresh_from_db()

    assert synced.business_object.object_role == "detail"
    assert synced.business_object.is_menu_hidden is True
    assert synced.business_object.is_top_level_navigable is False
    assert synced.business_object.allow_standalone_query is True
    assert synced.business_object.allow_standalone_route is False
    assert synced.business_object.inherit_permissions is True
    assert synced.business_object.inherit_workflow is True
    assert synced.business_object.inherit_status is True
    assert synced.business_object.inherit_lifecycle is True


@pytest.mark.django_db
def test_audit_log_catalog_defaults_follow_history_protocol():
    hardcoded_objects = {
        obj["code"]: obj
        for obj in BusinessObjectService().get_all_objects(
            include_hardcoded=True,
            include_custom=False,
        )["hardcoded"]
    }

    asset_status_log = hardcoded_objects["AssetStatusLog"]
    assert asset_status_log["object_role"] == "log"
    assert asset_status_log["is_menu_hidden"] is True
    assert asset_status_log["is_top_level_navigable"] is False
    assert asset_status_log["allow_standalone_query"] is True
    assert asset_status_log["allow_standalone_route"] is False

    configuration_change = hardcoded_objects["ConfigurationChange"]
    assert configuration_change["object_role"] == "log"
    assert configuration_change["is_menu_hidden"] is True
    assert configuration_change["is_top_level_navigable"] is False
    assert configuration_change["allow_standalone_query"] is True
    assert configuration_change["allow_standalone_route"] is False


@pytest.mark.django_db
def test_business_object_can_persist_detail_role_protocol_flags(organization, django_user_model):
    user = django_user_model.objects.create_user(
        username="detail-owner",
        email="detail@example.com",
        password="pass12345",
        organization=organization,
    )
    obj = BusinessObject.objects.create(
        code="PICKUP_ITEM_TEST",
        name="Pickup Item Test",
        object_role="detail",
        is_top_level_navigable=False,
        allow_standalone_query=True,
        allow_standalone_route=False,
        inherit_permissions=True,
        inherit_workflow=True,
        inherit_status=True,
        inherit_lifecycle=True,
        organization=organization,
        created_by=user,
    )

    assert obj.object_role == "detail"
    assert obj.is_top_level_navigable is False
    assert obj.allow_standalone_query is True
    assert obj.allow_standalone_route is False
    assert obj.inherit_permissions is True
    assert obj.inherit_workflow is True
    assert obj.inherit_status is True
    assert obj.inherit_lifecycle is True


@pytest.mark.django_db
def test_object_relation_definition_can_persist_master_detail_metadata(organization, django_user_model):
    user = django_user_model.objects.create_user(
        username="relation-owner",
        email="relation@example.com",
        password="pass12345",
        organization=organization,
    )
    relation = ObjectRelationDefinition.objects.create(
        relation_code="pickup_items_protocol",
        parent_object_code="AssetPickup",
        target_object_code="PickupItem",
        relation_kind="direct_fk",
        relation_type="master_detail",
        target_fk_field="pickup",
        display_mode="inline_editable",
        detail_edit_mode="inline_table",
        cascade_soft_delete=True,
        detail_toolbar_config={"actions": ["add_row"]},
        detail_summary_rules=[{"field": "quantity", "aggregate": "sum"}],
        detail_validation_rules=[{"rule": "unique_asset"}],
        organization=organization,
        created_by=user,
    )

    assert relation.relation_type == "master_detail"
    assert relation.detail_edit_mode == "inline_table"
    assert relation.cascade_soft_delete is True
    assert relation.detail_toolbar_config["actions"] == ["add_row"]
    assert relation.detail_summary_rules[0]["field"] == "quantity"
    assert relation.detail_validation_rules[0]["rule"] == "unique_asset"
