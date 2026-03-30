import importlib
from datetime import date
from decimal import Decimal

import pytest
from django.apps import apps as django_apps
from django.db import connection
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory, AssetPickup, PickupItem, Supplier
from apps.consumables.models import Consumable, ConsumableCategory, ConsumablePurchase, PurchaseItem
from apps.organizations.models import Department, Organization
from apps.system.models import BusinessObject, ObjectRelationDefinition
from apps.system.services.object_registry import ObjectRegistry
from apps.system.services.relation_query_service import RelationQueryService

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='Object router relation tests require PostgreSQL test stack.',
)


def _pick(payload, *keys):
    for key in keys:
        if isinstance(payload, dict) and key in payload:
            return payload[key]
    return None


def _upsert_business_object(code: str, name: str, model_path: str):
    BusinessObject.objects.update_or_create(
        code=code,
        defaults={
            'name': name,
            'name_en': name,
            'is_hardcoded': True,
            'django_model_path': model_path,
        },
    )
    ObjectRegistry.invalidate_cache(code)


@pytest.mark.django_db
def test_realign_line_item_display_tiers_migration_demotes_through_relations():
    migration = importlib.import_module('apps.system.migrations.0040_realign_line_item_display_tiers')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='assets',
        defaults={
            'target_object_code': 'Asset',
            'relation_kind': 'through_line_item',
            'through_object_code': 'PickupItem',
            'through_parent_fk_field': 'pickup',
            'through_target_fk_field': 'asset',
            'display_mode': 'inline_readonly',
            'display_tier': 'L1',
            'sort_order': 10,
            'is_active': True,
        },
    )
    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='pickup_items',
        defaults={
            'target_object_code': 'PickupItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'pickup',
            'display_mode': 'inline_readonly',
            'display_tier': 'L2',
            'sort_order': 1,
            'is_active': True,
        },
    )

    migration.realign_line_item_display_tiers(apps=django_apps, schema_editor=None)

    assets_relation = ObjectRelationDefinition.objects.get(
        parent_object_code='AssetPickup',
        relation_code='assets',
    )
    item_relation = ObjectRelationDefinition.objects.get(
        parent_object_code='AssetPickup',
        relation_code='pickup_items',
    )

    assert assets_relation.display_tier == 'L2'
    assert item_relation.display_tier == 'L1'
    assert item_relation.display_mode == 'inline_editable'


@pytest.mark.django_db
def test_relations_endpoint_returns_locale_aware_relation_name():
    org = Organization.objects.create(name='Relation Org', code='relation-org')
    user = User.objects.create_user(username='relation_user', password='pass123456', organization=org)

    _upsert_business_object('Organization', 'Organization', 'apps.organizations.models.Organization')
    _upsert_business_object('Department', 'Department', 'apps.organizations.models.Department')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Organization',
        relation_code='departments_runtime_test',
        defaults={
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'relation_name': 'Departments Local',
            'relation_name_en': 'Departments',
            'display_mode': 'inline_readonly',
            'sort_order': 10,
            'is_active': True,
            'extra_config': {},
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

    en_resp = client.get('/api/system/objects/Organization/relations/')
    assert en_resp.status_code == 200
    assert en_resp.data['success'] is True

    en_data = en_resp.data['data']
    en_relations = _pick(en_data, 'relations') or []
    en_relation = next(
        (
            item for item in en_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_runtime_test'
        ),
        None,
    )
    assert en_relation is not None
    assert _pick(en_relation, 'relationName', 'relation_name') == 'Departments'
    assert _pick(en_relation, 'groupKey', 'group_key') is not None
    assert _pick(en_relation, 'groupName', 'group_name') is not None
    assert _pick(en_data, 'locale') == 'en-US'

    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='zh-CN,zh;q=0.9')
    zh_resp = client.get('/api/system/objects/Organization/relations/')
    assert zh_resp.status_code == 200
    assert zh_resp.data['success'] is True

    zh_data = zh_resp.data['data']
    zh_relations = _pick(zh_data, 'relations') or []
    zh_relation = next(
        (
            item for item in zh_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_runtime_test'
        ),
        None,
    )
    assert zh_relation is not None
    assert _pick(zh_relation, 'relationName', 'relation_name') == 'Departments Local'
    assert isinstance(_pick(zh_relation, 'groupOrder', 'group_order'), int)
    assert isinstance(_pick(zh_relation, 'defaultExpanded', 'default_expanded'), bool)
    assert _pick(zh_data, 'locale') == 'zh-CN'


@pytest.mark.django_db
def test_asset_pickup_relations_endpoint_keeps_assets_out_of_l1_line_items():
    org = Organization.objects.create(name='Pickup Relation Org', code='pickup-relation-org')
    user = User.objects.create_user(username='pickup_relation_user', password='pass123456', organization=org)

    _upsert_business_object('AssetPickup', 'Asset Pickup', 'apps.assets.models.AssetPickup')
    _upsert_business_object('PickupItem', 'Pickup Item', 'apps.assets.models.PickupItem')
    _upsert_business_object('Asset', 'Asset', 'apps.assets.models.Asset')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='pickup_items',
        defaults={
            'target_object_code': 'PickupItem',
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'target_fk_field': 'pickup',
            'relation_name': 'Pickup Items',
            'relation_name_en': 'Pickup Items',
            'display_mode': 'inline_editable',
            'detail_edit_mode': 'inline_table',
            'display_tier': 'L1',
            'sort_order': 1,
            'is_active': True,
            'cascade_soft_delete': True,
            'detail_toolbar_config': {'actions': ['add_row']},
            'detail_summary_rules': [{'field': 'quantity', 'aggregate': 'sum'}],
            'detail_validation_rules': [{'rule': 'unique_asset'}],
            'extra_config': {},
        },
    )
    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='assets',
        defaults={
            'target_object_code': 'Asset',
            'relation_kind': 'through_line_item',
            'through_object_code': 'PickupItem',
            'through_parent_fk_field': 'pickup',
            'through_target_fk_field': 'asset',
            'relation_name': 'Pickup Assets',
            'relation_name_en': 'Pickup Assets',
            'display_mode': 'inline_readonly',
            'display_tier': 'L2',
            'sort_order': 2,
            'is_active': True,
            'extra_config': {},
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

    resp = client.get('/api/system/objects/AssetPickup/relations/')
    assert resp.status_code == 200
    assert resp.data['success'] is True

    relations = _pick(resp.data['data'], 'relations') or []

    items_relation = next(
        (
            item for item in relations
            if _pick(item, 'relationCode', 'relation_code') == 'pickup_items'
        ),
        None,
    )
    assets_relation = next(
        (
            item for item in relations
            if _pick(item, 'relationCode', 'relation_code') == 'assets'
        ),
        None,
    )

    assert items_relation is not None
    assert assets_relation is not None
    assert _pick(items_relation, 'displayTier', 'display_tier') == 'L1'
    assert _pick(items_relation, 'relationKind', 'relation_kind') == 'direct_fk'
    assert _pick(items_relation, 'relationType', 'relation_type') == 'master_detail'
    assert _pick(items_relation, 'detailEditMode', 'detail_edit_mode') == 'inline_table'
    assert _pick(items_relation, 'cascadeSoftDelete', 'cascade_soft_delete') is True
    assert _pick(assets_relation, 'displayTier', 'display_tier') == 'L2'
    assert _pick(assets_relation, 'relationKind', 'relation_kind') == 'through_line_item'


@pytest.mark.django_db
def test_relations_endpoint_exposes_history_presentation_for_audit_objects():
    org = Organization.objects.create(name='History Relation Org', code='history-relation-org')
    user = User.objects.create_user(username='history_relation_user', password='pass123456', organization=org)

    _upsert_business_object('Asset', 'Asset', 'apps.assets.models.Asset')
    BusinessObject.objects.update_or_create(
        code='ConfigurationChange',
        defaults={
            'name': 'Configuration Change',
            'name_en': 'Configuration Change',
            'is_hardcoded': True,
            'django_model_path': 'apps.it_assets.models.ConfigurationChange',
            'object_role': 'log',
            'is_menu_hidden': True,
            'is_top_level_navigable': False,
            'allow_standalone_query': True,
            'allow_standalone_route': False,
        },
    )

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Asset',
        relation_code='configuration_changes_history_test',
        defaults={
            'target_object_code': 'ConfigurationChange',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'asset',
            'display_mode': 'inline_readonly',
            'sort_order': 160,
            'is_active': True,
            'relation_name': 'Configuration Changes',
            'relation_name_en': 'Configuration Changes',
            'extra_config': {
                'presentation_zone': 'history',
                'history_source_type': 'configuration_change',
            },
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')

    resp = client.get('/api/system/objects/Asset/relations/')
    assert resp.status_code == 200
    assert resp.data['success'] is True

    relations = _pick(resp.data['data'], 'relations') or []
    relation = next(
        (
            item for item in relations
            if _pick(item, 'relationCode', 'relation_code') == 'configuration_changes_history_test'
        ),
        None,
    )

    assert relation is not None
    assert _pick(relation, 'targetObjectRole', 'target_object_role') == 'log'
    extra_config = _pick(relation, 'extraConfig', 'extra_config') or {}
    assert extra_config.get('presentationZone', extra_config.get('presentation_zone')) == 'history'
    assert _pick(relation, 'targetAllowStandaloneRoute', 'target_allow_standalone_route') is False


@pytest.mark.django_db
def test_line_item_business_objects_bind_to_dedicated_viewsets():
    _upsert_business_object('PickupItem', 'Pickup Item', 'apps.assets.models.PickupItem')
    _upsert_business_object('TransferItem', 'Transfer Item', 'apps.assets.models.TransferItem')
    _upsert_business_object('ReturnItem', 'Return Item', 'apps.assets.models.ReturnItem')
    _upsert_business_object('LoanItem', 'Loan Item', 'apps.assets.models.LoanItem')

    assert ObjectRegistry.get_or_create_from_db('PickupItem').viewset_class.__name__ == 'PickupItemViewSet'
    assert ObjectRegistry.get_or_create_from_db('TransferItem').viewset_class.__name__ == 'TransferItemViewSet'
    assert ObjectRegistry.get_or_create_from_db('ReturnItem').viewset_class.__name__ == 'ReturnItemViewSet'
    assert ObjectRegistry.get_or_create_from_db('LoanItem').viewset_class.__name__ == 'LoanItemViewSet'


@pytest.mark.django_db
def test_asset_pickup_related_endpoint_returns_line_item_business_fields():
    org = Organization.objects.create(name='Pickup Related Data Org', code='pickup-related-data-org')
    user = User.objects.create_user(username='pickup_related_data_user', password='pass123456', organization=org)
    department = Department.objects.create(organization=org, name='IT', code='IT')

    _upsert_business_object('AssetPickup', 'Asset Pickup', 'apps.assets.models.AssetPickup')
    _upsert_business_object('PickupItem', 'Pickup Item', 'apps.assets.models.PickupItem')
    _upsert_business_object('Asset', 'Asset', 'apps.assets.models.Asset')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='AssetPickup',
        relation_code='pickup_items',
        defaults={
            'target_object_code': 'PickupItem',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'pickup',
            'relation_name': 'Pickup Items',
            'relation_name_en': 'Pickup Items',
            'display_mode': 'inline_editable',
            'display_tier': 'L1',
            'sort_order': 1,
            'is_active': True,
            'extra_config': {},
        },
    )

    category = AssetCategory.objects.create(
        organization=org,
        code='PICKUP_ITEM_CAT',
        name='Pickup Category',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name='Related Pickup Asset',
        asset_category=category,
        purchase_price=Decimal('1000.00'),
        purchase_date=date.today(),
        asset_status='idle',
        created_by=user,
    )
    pickup = AssetPickup.objects.create(
        organization=org,
        applicant=user,
        department=department,
        pickup_date=date.today(),
        pickup_reason='Need laptop',
        created_by=user,
    )
    PickupItem.objects.create(
        organization=org,
        pickup=pickup,
        asset=asset,
        quantity=2,
        remark='Related row remark',
        created_by=user,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    resp = client.get(f'/api/system/objects/AssetPickup/{pickup.id}/related/pickup_items/')
    assert resp.status_code == 200
    assert resp.data['success'] is True

    results = _pick(resp.data.get('data', {}), 'results') or []
    assert len(results) == 1

    row = results[0]
    asset_payload = _pick(row, 'asset')
    assert isinstance(asset_payload, dict)
    assert _pick(asset_payload, 'id') == str(asset.id)
    assert _pick(asset_payload, 'asset_name', 'assetName') == 'Related Pickup Asset'
    assert _pick(row, 'quantity') == 2
    assert _pick(row, 'remark') == 'Related row remark'


@pytest.mark.django_db
def test_relations_endpoint_prefers_relation_name_i18n_map():
    org = Organization.objects.create(name='I18N Org', code='i18n-org')
    user = User.objects.create_user(username='i18n_user', password='pass123456', organization=org)

    _upsert_business_object('Organization', 'Organization', 'apps.organizations.models.Organization')
    _upsert_business_object('Department', 'Department', 'apps.organizations.models.Department')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Organization',
        relation_code='departments_i18n_map_test',
        defaults={
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'relation_name': 'Legacy Name',
            'relation_name_en': 'Legacy English Name',
            'display_mode': 'inline_readonly',
            'sort_order': 15,
            'is_active': True,
            'extra_config': {
                'relation_name_i18n': {
                    'zh-CN': '部门关系',
                    'en-US': 'Department Relation',
                    'default': '部门关系',
                }
            },
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
    en_resp = client.get('/api/system/objects/Organization/relations/')
    assert en_resp.status_code == 200
    en_relations = _pick(en_resp.data['data'], 'relations') or []
    en_relation = next(
        (
            item for item in en_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_i18n_map_test'
        ),
        None,
    )
    assert en_relation is not None
    assert _pick(en_relation, 'relationName', 'relation_name') == 'Department Relation'

    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='zh-CN,zh;q=0.9')
    zh_resp = client.get('/api/system/objects/Organization/relations/')
    assert zh_resp.status_code == 200
    zh_relations = _pick(zh_resp.data['data'], 'relations') or []
    zh_relation = next(
        (
            item for item in zh_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_i18n_map_test'
        ),
        None,
    )
    assert zh_relation is not None
    assert _pick(zh_relation, 'relationName', 'relation_name') == '部门关系'


@pytest.mark.django_db
def test_relations_endpoint_prefers_relation_group_object_over_alias_fields():
    org = Organization.objects.create(name='Group Org', code='group-org')
    user = User.objects.create_user(username='group_user', password='pass123456', organization=org)

    _upsert_business_object('Organization', 'Organization', 'apps.organizations.models.Organization')
    _upsert_business_object('Department', 'Department', 'apps.organizations.models.Department')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Organization',
        relation_code='departments_group_override_test',
        defaults={
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'relation_name': 'Departments',
            'relation_name_en': 'Departments',
            'display_mode': 'inline_readonly',
            'sort_order': 16,
            'is_active': True,
            'extra_config': {
                'group_key': 'alias_group',
                'group_order': 999,
                'default_expanded': False,
                'group_name': 'Alias Group',
                'relation_group': {
                    'key': 'organization',
                    'order': 15,
                    'default_expanded': True,
                    'name_i18n': {
                        'zh-CN': '组织协同',
                        'en-US': 'Org Collaboration',
                        'default': '组织协同',
                    },
                },
            },
        },
    )

    client = APIClient()
    client.force_authenticate(user=user)

    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='en-US,en;q=0.9')
    en_resp = client.get('/api/system/objects/Organization/relations/')
    assert en_resp.status_code == 200
    en_relations = _pick(en_resp.data['data'], 'relations') or []
    en_relation = next(
        (
            item for item in en_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_group_override_test'
        ),
        None,
    )
    assert en_relation is not None
    assert _pick(en_relation, 'groupKey', 'group_key') == 'organization'
    assert _pick(en_relation, 'groupName', 'group_name') == 'Org Collaboration'
    assert _pick(en_relation, 'groupOrder', 'group_order') == 15
    assert _pick(en_relation, 'defaultExpanded', 'default_expanded') is True

    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id), HTTP_ACCEPT_LANGUAGE='zh-CN,zh;q=0.9')
    zh_resp = client.get('/api/system/objects/Organization/relations/')
    assert zh_resp.status_code == 200
    zh_relations = _pick(zh_resp.data['data'], 'relations') or []
    zh_relation = next(
        (
            item for item in zh_relations
            if _pick(item, 'relationCode', 'relation_code') == 'departments_group_override_test'
        ),
        None,
    )
    assert zh_relation is not None
    assert _pick(zh_relation, 'groupName', 'group_name') == '组织协同'


@pytest.mark.django_db
def test_related_endpoint_returns_scoped_direct_fk_records():
    org = Organization.objects.create(name='Parent Org', code='parent-org')
    other_org = Organization.objects.create(name='Other Org', code='other-org')
    user = User.objects.create_user(username='related_user', password='pass123456', organization=org)

    _upsert_business_object('Organization', 'Organization', 'apps.organizations.models.Organization')
    _upsert_business_object('Department', 'Department', 'apps.organizations.models.Department')

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Organization',
        relation_code='departments_scope_test',
        defaults={
            'target_object_code': 'Department',
            'relation_kind': 'direct_fk',
            'target_fk_field': 'organization',
            'display_mode': 'inline_readonly',
            'sort_order': 20,
            'is_active': True,
            'extra_config': {},
        },
    )

    dept_in_scope = Department.objects.create(organization=org, code='OPS', name='Ops')
    Department.objects.create(organization=other_org, code='OPS', name='Ops Other')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    resp = client.get(f'/api/system/objects/Organization/{org.id}/related/departments_scope_test/')
    assert resp.status_code == 200
    assert resp.data['success'] is True

    data = resp.data['data']
    results = _pick(data, 'results') or []
    assert len(results) == 1
    assert str(results[0]['id']) == str(dept_in_scope.id)
    assert _pick(data, 'targetObjectCode', 'target_object_code') == 'Department'


@pytest.mark.django_db
def test_related_endpoint_validation_error_uses_i18n_message_key():
    org = Organization.objects.create(name='Validation Org', code='validation-org')
    user = User.objects.create_user(username='validation_user', password='pass123456', organization=org)

    _upsert_business_object('Organization', 'Organization', 'apps.organizations.models.Organization')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    resp = client.get(f'/api/system/objects/Organization/{org.id}/related/non_existing_relation/')
    assert resp.status_code == 400
    assert resp.data['success'] is False

    error_payload = resp.data['error']
    assert error_payload['code'] == 'VALIDATION_ERROR'
    assert error_payload['message'] == 'common.messages.badRequest'


@pytest.mark.django_db
def test_relation_query_service_resolves_through_model_by_class_name_fallback():
    service = RelationQueryService()
    model_class = service._resolve_model_class_from_code('PurchaseItem')
    assert model_class is not None
    assert model_class.__name__ == 'PurchaseItem'


@pytest.mark.django_db
def test_resolve_related_queryset_supports_through_model_fallback_without_business_object():
    org = Organization.objects.create(name='Consumable Org', code='consumable-org')
    _upsert_business_object('Consumable', 'Consumable', 'apps.consumables.models.Consumable')
    _upsert_business_object('ConsumablePurchase', 'Consumable Purchase', 'apps.consumables.models.ConsumablePurchase')

    category = ConsumableCategory.objects.create(
        organization=org,
        code='OFFICE',
        name='Office Supplies',
    )
    consumable = Consumable.objects.create(
        organization=org,
        code='PAPER-A4',
        name='A4 Paper',
        category=category,
    )
    supplier = Supplier.objects.create(
        organization=org,
        code='SUP-C1',
        name='Supplier C1',
    )
    purchase = ConsumablePurchase.objects.create(
        organization=org,
        purchase_no='CPTEST0001',
        purchase_date='2026-03-05',
        supplier=supplier,
    )
    PurchaseItem.objects.create(
        organization=org,
        purchase=purchase,
        consumable=consumable,
        quantity=10,
        unit_price=10,
        amount=100,
    )

    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code='Consumable',
        relation_code='purchase_orders_through_test',
        defaults={
            'target_object_code': 'ConsumablePurchase',
            'relation_kind': 'through_line_item',
            'through_object_code': 'PurchaseItem',
            'through_parent_fk_field': 'consumable',
            'through_target_fk_field': 'purchase',
            'display_mode': 'inline_readonly',
            'sort_order': 90,
            'is_active': True,
            'extra_config': {},
        },
    )

    service = RelationQueryService()
    resolution = service.resolve_related_queryset(
        parent_object_code='Consumable',
        parent_id=str(consumable.id),
        relation_code='purchase_orders_through_test',
        organization_id=str(org.id),
    )

    results = list(resolution.target_queryset.values_list('id', flat=True))
    assert str(purchase.id) in [str(item) for item in results]


@pytest.mark.django_db
def test_object_router_supports_workflow_objects_via_registry_mapping():
    org = Organization.objects.create(name='Workflow Router Org', code='workflow-router-org')
    user = User.objects.create_user(username='workflow_router_user', password='pass123456', organization=org)

    _upsert_business_object('WorkflowDefinition', 'Workflow Definition', 'apps.workflows.models.WorkflowDefinition')
    _upsert_business_object('WorkflowInstance', 'Workflow Instance', 'apps.workflows.models.WorkflowInstance')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    definition_resp = client.get('/api/system/objects/WorkflowDefinition/')
    assert definition_resp.status_code == 200
    assert definition_resp.data['success'] is True

    instance_resp = client.get('/api/system/objects/WorkflowInstance/')
    assert instance_resp.status_code == 200
    assert instance_resp.data['success'] is True


@pytest.mark.django_db
def test_object_router_supports_workflow_aux_objects_via_registry_mapping():
    org = Organization.objects.create(name='Workflow Aux Org', code='workflow-aux-org')
    user = User.objects.create_user(username='workflow_aux_user', password='pass123456', organization=org)

    _upsert_business_object('WorkflowTemplate', 'Workflow Template', 'apps.workflows.models.WorkflowTemplate')
    _upsert_business_object('WorkflowTask', 'Workflow Task', 'apps.workflows.models.WorkflowTask')
    _upsert_business_object('WorkflowApproval', 'Workflow Approval', 'apps.workflows.models.WorkflowApproval')
    _upsert_business_object('WorkflowOperationLog', 'Workflow Operation Log', 'apps.workflows.models.WorkflowOperationLog')

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    for code in ['WorkflowTemplate', 'WorkflowTask', 'WorkflowApproval', 'WorkflowOperationLog']:
        resp = client.get(f'/api/system/objects/{code}/')
        assert resp.status_code == 200
        assert resp.data['success'] is True
