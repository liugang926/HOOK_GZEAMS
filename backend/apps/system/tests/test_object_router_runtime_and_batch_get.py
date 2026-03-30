import pytest
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.models import BusinessObject, FieldDefinition, ObjectRelationDefinition, PageLayout

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='System migrations and router tests require PostgreSQL features (e.g., ON CONFLICT).',
)


@pytest.mark.django_db
def test_object_router_runtime_returns_layout_and_fields():
    org = Organization.objects.create(name='Test Org', code='test-org')
    user = User.objects.create(username='testuser', organization=org)

    bo = BusinessObject.objects.create(code='TESTOBJ', name='Test Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    shared_form = PageLayout.objects.create(
        business_object=bo,
        layout_code='TESTOBJ_form',
        layout_name='Shared Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-form',
                    'name': 's-form',
                    'title': 'Form',
                    'columns': 2,
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    # Legacy readonly layout should be ignored by runtime readonly under shared model.
    PageLayout.objects.create(
        business_object=bo,
        layout_code='TESTOBJ_detail',
        layout_name='Detail',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's1',
                    'name': 's1',
                    'title': 'Detail',
                    'columns': 2,
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name', 'span': 12, 'readonly': True},
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/TESTOBJ/runtime/?mode=readonly')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['objectCode'] == 'TESTOBJ'
    assert data['mode'] == 'readonly'
    assert isinstance(data.get('permissions'), dict)
    assert {'view', 'add', 'change', 'delete'}.issubset(set(data['permissions'].keys()))
    workbench = data['workbench']
    assert workbench['workspaceMode'] == 'standard'
    assert workbench['primaryEntryRoute'] == '/objects/TESTOBJ'
    assert workbench['legacyAliases'] == []
    assert workbench['detailPanels'] == []
    assert workbench['asyncIndicators'] == []
    assert workbench['summaryCards'] == []
    assert workbench['queuePanels'] == []
    assert workbench['exceptionPanels'] == []
    assert workbench['closurePanel'] == {}
    assert workbench['slaIndicators'] == []
    assert workbench['recommendedActions'] == []
    assert workbench['toolbar']['primaryActions'] == []
    assert workbench['toolbar']['secondaryActions'] == []

    fields = data['fields']
    assert isinstance(fields.get('editableFields'), list)
    target = next(
        (
            f
            for f in fields['editableFields']
            if (f.get('fieldCode') or f.get('field_code') or f.get('code')) == 'name'
        ),
        None,
    )
    assert target is not None
    assert 'code' not in target
    assert (target.get('fieldCode') or target.get('field_code')) == 'name'
    assert fields.get('context') == 'form'

    layout = data['layout']
    assert isinstance(layout.get('layoutConfig'), dict)
    assert isinstance(layout['layoutConfig'].get('sections'), list)
    assert str(layout.get('id')) == str(shared_form.id)
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_object_router_runtime_applies_workbench_overrides_from_layout():
    org = Organization.objects.create(name='Workbench Org', code='workbench-org')
    user = User.objects.create(username='workbenchuser', organization=org)

    bo = BusinessObject.objects.create(code='WORKBENCHOBJ', name='Workbench Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )
    PageLayout.objects.create(
        business_object=bo,
        layout_code='WORKBENCHOBJ_form',
        layout_name='Workbench Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 'basic',
                    'name': 'basic',
                    'title': 'Basic',
                    'fields': [{'fieldCode': 'name', 'label': 'Name'}],
                }
            ],
            'workbench': {
                'workspaceMode': 'extended',
                'primaryEntryRoute': '/objects/WORKBENCHOBJ',
                'legacyAliases': ['/legacy/workbench'],
                'toolbar': {
                    'primaryActions': [{'code': 'publish'}],
                    'secondaryActions': [{'code': 'archive'}],
                },
                'detailPanels': [{'code': 'integration_logs', 'component': 'integration-log-table'}],
                'asyncIndicators': [{'code': 'sync_task', 'type': 'sync-task'}],
                'summaryCards': [{'code': 'pending_count', 'valueField': 'pendingCount'}],
                'queuePanels': [{'code': 'approaching_sla', 'queueCode': 'approaching_sla'}],
                'exceptionPanels': [{'code': 'push_failed', 'queueCode': 'push_failed'}],
                'closurePanel': {'stageField': 'status', 'ownerField': 'ownerName'},
                'slaIndicators': [{'code': 'workflow_sla', 'statusField': 'slaStatus'}],
                'recommendedActions': [{'code': 'follow_up', 'actionPath': 'follow_up'}],
            },
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/WORKBENCHOBJ/runtime/?mode=edit')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True

    workbench = payload['data']['workbench']
    assert workbench['workspaceMode'] == 'extended'
    assert workbench['primaryEntryRoute'] == '/objects/WORKBENCHOBJ'
    assert workbench['legacyAliases'] == ['/legacy/workbench']
    assert workbench['toolbar']['primaryActions'][0]['code'] == 'publish'
    assert workbench['toolbar']['secondaryActions'][0]['code'] == 'archive'
    assert workbench['detailPanels'][0]['code'] == 'integration_logs'
    assert workbench['asyncIndicators'][0]['code'] == 'sync_task'
    assert workbench['summaryCards'][0]['code'] == 'pending_count'
    assert workbench['queuePanels'][0]['queueCode'] == 'approaching_sla'
    assert workbench['exceptionPanels'][0]['queueCode'] == 'push_failed'
    assert workbench['closurePanel']['stageField'] == 'status'
    assert workbench['slaIndicators'][0]['statusField'] == 'slaStatus'
    assert workbench['recommendedActions'][0]['actionPath'] == 'follow_up'


@pytest.mark.django_db
def test_object_router_batch_get_returns_ordered_results():
    org = Organization.objects.create(name='Batch Org', code='batch-org')
    user = User.objects.create(username='batchuser', organization=org)

    # Register hardcoded object meta via BusinessObject row (ObjectRegistry reads DB first).
    BusinessObject.objects.create(
        code='Organization',
        name='Organization',
        is_hardcoded=True,
        django_model_path='apps.organizations.models.Organization',
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.post(
        '/api/system/objects/Organization/batch-get/',
        {'ids': [str(org.id)]},
        format='json',
    )
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    results = payload['data']['results']
    assert len(results) == 1
    assert results[0]['id'] == str(org.id)


@pytest.mark.django_db
def test_object_router_runtime_prefers_published_layout_over_draft_custom():
    org = Organization.objects.create(name='Runtime Priority Org', code='runtime-priority-org')
    user = User.objects.create(username='runtimepriorityuser', organization=org)

    bo = BusinessObject.objects.create(code='RTPRIOBJ', name='Runtime Priority Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_form=True,
        show_in_detail=True,
    )

    draft_custom = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_form_custom_draft',
        layout_name='Draft Custom Form',
        layout_type='form',
        mode='edit',
        status='draft',
        is_default=False,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-draft',
                    'type': 'section',
                    'title': 'Draft Form',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Draft Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    published_default = PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_form_default_published',
        layout_name='Published Default Form',
        layout_type='form',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-published',
                    'type': 'section',
                    'title': 'Published Form',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Published Form)', 'span': 12},
                    ],
                }
            ]
        },
    )
    # Legacy detail layout should not be selected for readonly runtime.
    PageLayout.objects.create(
        organization=org,
        business_object=bo,
        layout_code='rtpriobj_detail_default_published',
        layout_name='Published Default Detail Legacy',
        layout_type='detail',
        mode='readonly',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'sections': [
                {
                    'id': 's-detail',
                    'type': 'section',
                    'title': 'Published Detail Legacy',
                    'fields': [
                        {'fieldCode': 'name', 'label': 'Name (Legacy Detail)', 'span': 12, 'readonly': True},
                    ],
                }
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/RTPRIOBJ/runtime/?mode=readonly')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    layout = payload['data']['layout']
    assert str(layout['id']) == str(published_default.id)
    assert str(layout['id']) != str(draft_custom.id)
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'form'


@pytest.mark.django_db
def test_object_router_runtime_list_uses_field_driven_columns_not_legacy_list_layout():
    org = Organization.objects.create(name='Runtime List Org', code='runtime-list-org')
    user = User.objects.create(username='runtimelistuser', organization=org)

    bo = BusinessObject.objects.create(code='RTLISTOBJ', name='Runtime List Object', is_hardcoded=False)
    FieldDefinition.objects.create(
        business_object=bo,
        code='name',
        name='Name',
        field_type='text',
        show_in_list=True,
        show_in_form=True,
        show_in_detail=True,
        sort_order=1,
    )
    FieldDefinition.objects.create(
        business_object=bo,
        code='hidden_note',
        name='Hidden Note',
        field_type='text',
        show_in_list=False,
        show_in_form=True,
        show_in_detail=True,
        sort_order=2,
    )

    # Legacy list layout should no longer drive runtime list columns.
    PageLayout.objects.create(
        business_object=bo,
        layout_code='rtlistobj_list_legacy_default',
        layout_name='Legacy List',
        layout_type='list',
        mode='edit',
        status='published',
        is_default=True,
        is_active=True,
        layout_config={
            'columns': [
                {'fieldCode': 'legacy_only', 'label': 'Legacy Only', 'width': 180, 'visible': True},
            ]
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    resp = client.get('/api/system/objects/RTLISTOBJ/runtime/?mode=list')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    data = payload['data']
    assert data['mode'] == 'list'
    assert data['fields']['context'] == 'list'

    layout = data['layout']
    assert (layout.get('layoutType') or layout.get('layout_type')) == 'list'
    layout_config = layout.get('layoutConfig') or layout.get('layout_config') or {}
    columns = layout_config.get('columns') or []
    field_codes = {
        str(col.get('fieldCode') or col.get('field_code') or col.get('prop') or '')
        for col in columns
    }

    assert 'name' in field_codes
    assert 'hidden_note' not in field_codes
    assert 'legacy_only' not in field_codes


@pytest.mark.django_db
def test_object_router_runtime_relations_use_relation_definitions_for_hardcoded_objects():
    org = Organization.objects.create(name='Runtime Relation Org', code='runtime-relation-org')
    user = User.objects.create(username='runtime_relation_user', organization=org)

    BusinessObject.objects.update_or_create(
        code='Asset',
        defaults={
            'name': 'Asset',
            'name_en': 'Asset',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.Asset',
        },
    )
    BusinessObject.objects.update_or_create(
        code='AssetTransfer',
        defaults={
            'name': 'Asset Transfer',
            'name_en': 'Asset Transfer',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.AssetTransfer',
        },
    )
    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Asset',
        relation_code='transfer_orders',
        defaults={
            'target_object_code': 'AssetTransfer',
            'relation_name': 'Transfer Orders',
            'relation_kind': 'through_line_item',
            'through_object_code': 'TransferItem',
            'through_parent_fk_field': 'asset',
            'through_target_fk_field': 'transfer',
            'display_mode': 'inline_readonly',
            'display_tier': 'L2',
            'sort_order': 30,
            'is_active': True,
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

    resp = client.get('/api/system/objects/Asset/runtime/?mode=readonly&include_relations=true')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    fields = payload['data']['fields']
    reverse_relations = fields.get('reverseRelations')
    if reverse_relations is None:
        reverse_relations = fields.get('reverse_relations')
    reverse_relations = reverse_relations or []

    transfer_relation = next(
        (
            item for item in reverse_relations
            if (item.get('fieldCode') or item.get('field_code') or item.get('code')) == 'transfer_orders'
        ),
        None,
    )
    assert transfer_relation is not None
    assert (transfer_relation.get('targetObjectCode') or transfer_relation.get('target_object_code')) == 'AssetTransfer'


@pytest.mark.django_db
def test_asset_pickup_runtime_promotes_l1_items_to_editable_subtable():
    org = Organization.objects.create(name='Line Item Runtime Org', code='line-item-runtime-org')
    user = User.objects.create(username='line_item_runtime_user', organization=org)

    BusinessObject.objects.update_or_create(
        code='AssetPickup',
        defaults={
            'name': 'Asset Pickup',
            'name_en': 'Asset Pickup',
            'is_hardcoded': True,
            'django_model_path': 'apps.assets.models.AssetPickup',
        },
    )
    BusinessObject.objects.update_or_create(
        code='PickupItem',
        defaults={
            'name': 'Pickup Item',
            'name_en': 'Pickup Item',
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'object_role': 'detail',
            'is_top_level_navigable': False,
            'allow_standalone_query': True,
            'allow_standalone_route': False,
            'inherit_permissions': True,
            'inherit_workflow': True,
            'inherit_status': True,
            'inherit_lifecycle': True,
            'django_model_path': 'apps.assets.models.PickupItem',
        },
    )
    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='pickup_items',
        defaults={
            'target_object_code': 'PickupItem',
            'relation_name': 'Pickup Items',
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'target_fk_field': 'pickup',
            'display_mode': 'inline_editable',
            'detail_edit_mode': 'inline_table',
            'display_tier': 'L1',
            'sort_order': 10,
            'is_active': True,
            'cascade_soft_delete': True,
            'detail_toolbar_config': {'actions': ['add_row']},
            'detail_summary_rules': [{'field': 'quantity', 'aggregate': 'sum'}],
            'detail_validation_rules': [{'rule': 'unique_asset'}],
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    resp = client.get('/api/system/objects/AssetPickup/runtime/?mode=edit&include_relations=true')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    fields_payload = payload['data']['fields']
    editable_fields = fields_payload.get('editableFields') or fields_payload.get('editable_fields') or []
    reverse_relations = fields_payload.get('reverseRelations') or fields_payload.get('reverse_relations') or []

    items_field = next(
        (
            field for field in editable_fields
            if (field.get('fieldCode') or field.get('field_code') or field.get('code')) == 'items'
        ),
        None,
    )

    assert items_field is not None
    assert (items_field.get('fieldType') or items_field.get('field_type')) == 'sub_table'
    assert items_field.get('displayTier') == 'L1' or items_field.get('display_tier') == 'L1'
    assert (items_field.get('componentProps') or items_field.get('component_props') or {}).get('relationCode') == 'pickup_items'

    related_fields = items_field.get('relatedFields') or items_field.get('related_fields') or []
    related_codes = {
        str(field.get('fieldCode') or field.get('field_code') or field.get('code') or '')
        for field in related_fields
    }
    assert {'asset', 'quantity', 'remark'}.issubset(related_codes)
    assert all(
        (field.get('fieldCode') or field.get('field_code') or field.get('code')) != 'items'
        for field in reverse_relations
    )

    aggregate = payload['data'].get('aggregate') or {}
    detail_regions = aggregate.get('detailRegions') or aggregate.get('detail_regions') or []
    pickup_region = next(
        (
            region for region in detail_regions
            if (region.get('relationCode') or region.get('relation_code')) == 'pickup_items'
        ),
        None,
    )
    assert aggregate.get('isAggregateRoot') is True or aggregate.get('is_aggregate_root') is True
    assert pickup_region is not None
    assert (pickup_region.get('fieldCode') or pickup_region.get('field_code')) == 'items'
    assert (pickup_region.get('relationType') or pickup_region.get('relation_type')) == 'master_detail'
    assert (pickup_region.get('detailEditMode') or pickup_region.get('detail_edit_mode')) == 'inline_table'
    assert (pickup_region.get('targetObjectRole') or pickup_region.get('target_object_role')) == 'detail'
    assert bool(pickup_region.get('allowStandaloneRoute') if 'allowStandaloneRoute' in pickup_region else pickup_region.get('allow_standalone_route')) is False


@pytest.mark.django_db
def test_hidden_pickup_item_runtime_list_keeps_business_columns_visible():
    org = Organization.objects.create(name='Line Item List Org', code='line-item-list-org')
    user = User.objects.create(username='line_item_list_user', organization=org)

    BusinessObject.objects.update_or_create(
        code='PickupItem',
        defaults={
            'name': 'Pickup Item',
            'name_en': 'Pickup Item',
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'django_model_path': 'apps.assets.models.PickupItem',
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    resp = client.get('/api/system/objects/PickupItem/runtime/?mode=list&include_relations=false')
    assert resp.status_code == 200

    payload = resp.json()
    assert payload['success'] is True
    editable_fields = (
        payload['data']['fields'].get('editableFields')
        or payload['data']['fields'].get('editable_fields')
        or []
    )
    field_codes = {
        str(field.get('fieldCode') or field.get('field_code') or field.get('code') or '')
        for field in editable_fields
    }

    assert {'asset', 'quantity', 'remark'}.issubset(field_codes)
