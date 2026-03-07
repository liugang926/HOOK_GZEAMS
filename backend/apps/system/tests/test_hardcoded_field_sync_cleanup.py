import pytest

from apps.system.models import BusinessObject, ModelFieldDefinition
from apps.system.services.business_object_service import BusinessObjectService


@pytest.mark.django_db
def test_sync_model_fields_soft_deletes_reverse_relation_metadata():
    business_object = BusinessObject.objects.create(
        code='Asset',
        name='Asset',
        is_hardcoded=True,
        django_model_path='apps.assets.models.Asset',
    )
    ModelFieldDefinition.objects.create(
        business_object=business_object,
        field_name='transfer_items',
        display_name='transfer_items',
        field_type='text',
        django_field_type='ForeignObjectRel',
        sort_order=1,
    )

    synced_count = BusinessObjectService().sync_model_fields('Asset')

    assert synced_count > 0
    stale_field = ModelFieldDefinition.all_objects.get(
        business_object=business_object,
        field_name='transfer_items',
    )
    assert stale_field.is_deleted is True

    valid_field = ModelFieldDefinition.objects.get(
        business_object=business_object,
        field_name='asset_code',
    )
    assert valid_field.is_deleted is False
