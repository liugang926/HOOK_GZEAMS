import pytest

from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.system.services.metadata_sync_service import MetadataSyncService


@pytest.mark.django_db
def test_ensure_default_layouts_archives_legacy_list_and_keeps_shared_form():
    bo = BusinessObject.objects.create(
        code='METADATASYNCBO',
        name='Metadata Sync BO',
        is_hardcoded=False,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_list=True,
        sort_order=1,
    )

    legacy_list = PageLayout.objects.create(
        business_object=bo,
        layout_code='metadatasyncbo_default_list',
        layout_name='Legacy List',
        layout_type='list',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={'columns': [{'fieldCode': 'name', 'label': 'Name'}]},
    )
    bo.default_list_layout = legacy_list
    bo.save(update_fields=['default_list_layout'])

    service = MetadataSyncService()
    service._ensure_default_layouts(bo, bo.code)

    form_layout = PageLayout.objects.filter(
        business_object=bo,
        layout_type='form',
        is_default=True,
        is_active=True,
    ).first()
    assert form_layout is not None

    legacy_list.refresh_from_db()
    assert legacy_list.status == 'archived'
    assert legacy_list.is_active is False
    assert legacy_list.is_default is False

    bo.refresh_from_db()
    assert bo.default_list_layout_id is None
