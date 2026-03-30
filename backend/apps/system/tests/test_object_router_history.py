from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory, AssetStatusLog
from apps.it_assets.models import ConfigurationChange, ITAssetInfo
from apps.organizations.models import Organization
from apps.system.models import BusinessObject
from apps.system.services.activity_log_service import ActivityLogService
from apps.system.services.object_registry import ObjectRegistry


def _upsert_business_object(code: str, name: str, model_path: str):
    BusinessObject.objects.update_or_create(
        code=code,
        defaults={
            "name": name,
            "name_en": name,
            "is_hardcoded": True,
            "django_model_path": model_path,
        },
    )
    ObjectRegistry.invalidate_cache(code)


def _build_client(user, organization):
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(organization.id))
    return client


@pytest.mark.django_db
def test_asset_history_endpoint_aggregates_activity_status_and_configuration_changes():
    org = Organization.objects.create(name="History Org", code="history-org")
    user = User.objects.create_user(username="history_user", password="pass123456", organization=org)

    _upsert_business_object("Asset", "Asset", "apps.assets.models.Asset")

    category = AssetCategory.objects.create(
        organization=org,
        code="HISTORY_CAT",
        name="History Category",
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name="History Asset",
        asset_category=category,
        purchase_price=Decimal("1200.00"),
        purchase_date=date.today(),
        asset_status="idle",
        created_by=user,
    )

    ActivityLogService.log_action(
        actor=user,
        action="update",
        instance=asset,
        changes=[
            {
                "fieldLabel": "Asset Name",
                "fieldCode": "asset_name",
                "oldValue": "Legacy Asset",
                "newValue": "History Asset",
            }
        ],
        description="Updated asset profile",
        organization=org,
    )
    AssetStatusLog.objects.create(
        organization=org,
        asset=asset,
        old_status="idle",
        new_status="in_use",
        reason="Assigned to user",
        created_by=user,
    )
    ConfigurationChange.objects.create(
        organization=org,
        asset=asset,
        field_name="cpu_model",
        old_value="i5",
        new_value="i7",
        change_reason="Hardware refresh",
        changed_by=user,
        change_date=date.today(),
        created_by=user,
    )

    client = _build_client(user, org)
    response = client.get(f"/api/system/objects/Asset/{asset.id}/history/")

    assert response.status_code == 200
    assert response.data["success"] is True

    payload = response.data["data"]
    assert payload["count"] == 3

    source_codes = {row.get("sourceCode") or row.get("source_code") for row in payload["results"]}
    assert source_codes == {"Asset", "AssetStatusLog", "ConfigurationChange"}

    status_entry = next(row for row in payload["results"] if (row.get("sourceCode") or row.get("source_code")) == "AssetStatusLog")
    assert status_entry["changes"][0]["fieldCode"] == "asset_status"
    assert status_entry["changes"][0]["newValue"] == "in_use"

    config_entry = next(row for row in payload["results"] if (row.get("sourceCode") or row.get("source_code")) == "ConfigurationChange")
    assert config_entry["changes"][0]["fieldCode"] == "cpu_model"
    assert config_entry["changes"][0]["newValue"] == "i7"


@pytest.mark.django_db
def test_it_asset_history_endpoint_includes_configuration_changes_from_asset_base():
    org = Organization.objects.create(name="IT History Org", code="it-history-org")
    user = User.objects.create_user(username="it_history_user", password="pass123456", organization=org)

    _upsert_business_object("ITAsset", "IT Asset", "apps.it_assets.models.ITAssetInfo")

    category = AssetCategory.objects.create(
        organization=org,
        code="IT_HISTORY_CAT",
        name="IT History Category",
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name="IT History Asset",
        asset_category=category,
        purchase_price=Decimal("2300.00"),
        purchase_date=date.today(),
        asset_status="idle",
        created_by=user,
    )
    it_asset = ITAssetInfo.objects.create(
        organization=org,
        asset=asset,
        created_by=user,
    )
    ConfigurationChange.objects.create(
        organization=org,
        asset=asset,
        field_name="ram_capacity",
        old_value="16",
        new_value="32",
        change_reason="Memory upgrade",
        changed_by=user,
        change_date=date.today(),
        created_by=user,
    )

    client = _build_client(user, org)
    response = client.get(f"/api/system/objects/ITAsset/{it_asset.id}/history/")

    assert response.status_code == 200
    assert response.data["success"] is True

    payload = response.data["data"]
    assert payload["count"] == 1
    entry = payload["results"][0]
    assert (entry.get("sourceCode") or entry.get("source_code")) == "ConfigurationChange"
    assert entry["changes"][0]["fieldCode"] == "ram_capacity"
    assert entry["changes"][0]["newValue"] == "32"
