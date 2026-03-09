import pytest

from apps.system.models import BusinessObject
from apps.system.services.hardcoded_object_sync_service import (
    SYSTEM_SEED_KEY,
    SYSTEM_SEED_SOURCE,
    HardcodedObjectSyncService,
)
from apps.system.services.business_object_service import BusinessObjectService
from apps.system.services.object_registry import ObjectRegistry


@pytest.mark.django_db
def test_business_object_service_lists_catalog_backed_hardcoded_objects():
    hardcoded_objects = BusinessObjectService().get_all_objects(
        include_hardcoded=True,
        include_custom=False,
    )["hardcoded"]

    asset = next(obj for obj in hardcoded_objects if obj["code"] == "Asset")
    assert asset["name"] == "资产"
    assert asset["name_en"] == "Asset"
    assert asset["model_path"] == "apps.assets.models.Asset"
    assert asset["app_label"] == "assets"


@pytest.mark.django_db
def test_object_registry_auto_register_uses_catalog_defaults():
    BusinessObject.objects.filter(code="Asset").delete()

    ObjectRegistry.auto_register_standard_objects()

    asset = BusinessObject.objects.get(code="Asset")
    assert asset.name == "资产"
    assert asset.name_en == "Asset"
    assert asset.is_hardcoded is True
    assert asset.django_model_path == "apps.assets.models.Asset"
    assert asset.custom_fields[SYSTEM_SEED_KEY]["source"] == SYSTEM_SEED_SOURCE


@pytest.mark.django_db
def test_hardcoded_object_sync_service_marks_seed_metadata_and_respects_overwrite_flag():
    service = HardcodedObjectSyncService()
    definition = service.get_definition("Asset")
    assert definition is not None

    BusinessObject.objects.create(
        code="Asset",
        name="Custom Asset Name",
        name_en="Custom Asset Name",
        is_hardcoded=True,
        django_model_path="apps.assets.models.Asset",
        custom_fields={},
    )

    skipped = service.ensure_business_object(definition, overwrite_existing=False)
    assert skipped.created is False
    assert skipped.updated is False
    skipped.business_object.refresh_from_db()
    assert skipped.business_object.name == "Custom Asset Name"

    synced = service.ensure_business_object(definition, overwrite_existing=True)
    assert synced.created is False
    assert synced.updated is True
    synced.business_object.refresh_from_db()
    assert synced.business_object.name == "资产"
    assert synced.business_object.custom_fields[SYSTEM_SEED_KEY]["source"] == SYSTEM_SEED_SOURCE
