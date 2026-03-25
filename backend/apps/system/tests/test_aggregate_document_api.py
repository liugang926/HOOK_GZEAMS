import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.db import connection
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import (
    Asset,
    AssetCategory,
    AssetPickup,
    AssetTransfer,
    PickupItem,
    TransferItem,
)
from apps.common.middleware import clear_current_organization, set_current_organization
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    DisposalItem,
    DisposalRequest,
    DisposalRequestStatus,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.organizations.models import Department, Organization
from apps.system.models import BusinessObject, ObjectRelationDefinition
from apps.system.services.activity_log_service import ActivityLogService
from apps.system.services.aggregate_document_service import AggregateDocumentService
from apps.workflows.models import WorkflowApproval, WorkflowDefinition, WorkflowInstance, WorkflowTask
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog

pytestmark = pytest.mark.skipif(
    connection.vendor == 'sqlite',
    reason='Aggregate document API tests require PostgreSQL-backed metadata/runtime behavior.',
)


def _register_pickup_master_detail_protocol():
    _register_master_detail_protocol(
        root_code='AssetPickup',
        root_name='Asset Pickup',
        root_model_path='apps.assets.models.AssetPickup',
        target_code='PickupItem',
        target_name='Pickup Item',
        target_model_path='apps.assets.models.PickupItem',
        relation_code='pickup_items',
        relation_name='Pickup Items',
        target_fk_field='pickup',
    )


def _register_transfer_master_detail_protocol():
    _register_master_detail_protocol(
        root_code='AssetTransfer',
        root_name='Asset Transfer',
        root_model_path='apps.assets.models.AssetTransfer',
        target_code='TransferItem',
        target_name='Transfer Item',
        target_model_path='apps.assets.models.TransferItem',
        relation_code='transfer_items',
        relation_name='Transfer Items',
        target_fk_field='transfer',
    )


def _register_purchase_request_master_detail_protocol():
    _register_master_detail_protocol(
        root_code='PurchaseRequest',
        root_name='Purchase Request',
        root_model_path='apps.lifecycle.models.PurchaseRequest',
        target_code='PurchaseRequestItem',
        target_name='Purchase Request Item',
        target_model_path='apps.lifecycle.models.PurchaseRequestItem',
        relation_code='purchase_request_items',
        relation_name='Purchase Request Items',
        target_fk_field='purchase_request',
    )


def _register_receipt_master_detail_protocol():
    _register_master_detail_protocol(
        root_code='AssetReceipt',
        root_name='Asset Receipt',
        root_model_path='apps.lifecycle.models.AssetReceipt',
        target_code='AssetReceiptItem',
        target_name='Asset Receipt Item',
        target_model_path='apps.lifecycle.models.AssetReceiptItem',
        relation_code='receipt_items',
        relation_name='Receipt Items',
        target_fk_field='asset_receipt',
    )


def _register_disposal_master_detail_protocol():
    _register_master_detail_protocol(
        root_code='DisposalRequest',
        root_name='Disposal Request',
        root_model_path='apps.lifecycle.models.DisposalRequest',
        target_code='DisposalItem',
        target_name='Disposal Item',
        target_model_path='apps.lifecycle.models.DisposalItem',
        relation_code='disposal_items',
        relation_name='Disposal Items',
        target_fk_field='disposal_request',
    )


def _register_master_detail_protocol(
    *,
    root_code,
    root_name,
    root_model_path,
    target_code,
    target_name,
    target_model_path,
    relation_code,
    relation_name,
    target_fk_field,
):
    BusinessObject.objects.update_or_create(
        code=root_code,
        defaults={
            'name': root_name,
            'name_en': root_name,
            'is_hardcoded': True,
            'django_model_path': root_model_path,
            'object_role': 'root',
            'is_top_level_navigable': True,
        },
    )
    BusinessObject.objects.update_or_create(
        code=target_code,
        defaults={
            'name': target_name,
            'name_en': target_name,
            'is_hardcoded': True,
            'is_menu_hidden': True,
            'django_model_path': target_model_path,
            'object_role': 'detail',
            'is_top_level_navigable': False,
            'allow_standalone_query': True,
            'allow_standalone_route': False,
            'inherit_permissions': True,
            'inherit_workflow': True,
            'inherit_status': True,
            'inherit_lifecycle': True,
        },
    )
    ObjectRelationDefinition.objects.update_or_create(
        parent_object_code=root_code,
        relation_code=relation_code,
        defaults={
            'target_object_code': target_code,
            'relation_name': relation_name,
            'relation_name_en': relation_name,
            'relation_kind': 'direct_fk',
            'relation_type': 'master_detail',
            'target_fk_field': target_fk_field,
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


@pytest.fixture
def pickup_document_context():
    clear_current_organization()
    suffix = uuid.uuid4().hex[:8]

    org = Organization.objects.create(name=f'Aggregate Org {suffix}', code=f'AGG_{suffix}')
    user = User.objects.create_user(
        username=f'aggregate_user_{suffix}',
        password='pass12345',
        organization=org,
    )
    department = Department.objects.create(
        organization=org,
        name='IT Department',
        code=f'IT_{suffix}',
    )
    category = AssetCategory.objects.create(
        organization=org,
        code=f'CAT_{suffix}',
        name='Computer',
        created_by=user,
    )
    asset = Asset.objects.create(
        organization=org,
        asset_name='Primary Laptop',
        asset_category=category,
        purchase_price=Decimal('1000'),
        purchase_date=date.today(),
        asset_status='idle',
        created_by=user,
    )

    _register_pickup_master_detail_protocol()
    set_current_organization(str(org.id))

    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))

    yield {
        'org': org,
        'user': user,
        'department': department,
        'category': category,
        'asset': asset,
        'client': client,
    }

    clear_current_organization()


@pytest.mark.django_db
def test_aggregate_document_create_pickup_uses_master_detail_contract(pickup_document_context):
    department = pickup_document_context['department']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']

    response = client.post(
        '/api/system/objects/AssetPickup/document/',
        {
            'master': {
                'department': str(department.id),
                'pickup_date': str(date.today()),
                'pickup_reason': 'Need a new laptop',
            },
            'details': {
                'pickup_items': {
                    'rows': [
                        {
                            'asset_id': str(asset.id),
                            'quantity': 1,
                            'remark': 'First row',
                        }
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['documentVersion'] == 1
    assert data['context']['objectCode'] == 'AssetPickup'
    assert data['context']['pageMode'] == 'edit'
    assert data['master']['pickupReason'] == 'Need a new laptop'
    assert data['details']['pickupItems']['rowCount'] == 1
    assert data['details']['pickupItems']['editable'] is True
    assert data['details']['pickupItems']['rows'][0]['quantity'] == 1
    assert data['capabilities']['canEditMaster'] is True
    assert data['capabilities']['canSubmit'] is True
    assert data['workflow']['hasInstance'] is False
    assert data['workflow']['timeline'] == []
    assert data['audit']['counts']['activityLogs'] >= 1
    assert len(data['audit']['activityLogs']) >= 1
    assert any(item['source'] == 'activity' for item in data['timeline'])

    pickup = AssetPickup.objects.get(id=data['context']['recordId'])
    assert pickup.items.count() == 1


@pytest.mark.django_db
def test_aggregate_document_get_pickup_reflects_readonly_capabilities_for_pending_status(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    department = pickup_document_context['department']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']

    pickup = AssetPickup.objects.create(
        organization=org,
        applicant=user,
        department=department,
        pickup_date=date.today(),
        pickup_reason='Pending approval',
        status='pending',
    )
    PickupItem.objects.create(
        organization=org,
        pickup=pickup,
        asset=asset,
        quantity=1,
        remark='Pending item',
    )

    response = client.get(f'/api/system/objects/AssetPickup/{pickup.id}/document/?mode=edit')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['context']['recordId'] == str(pickup.id)
    assert data['capabilities']['canEditMaster'] is False
    assert data['capabilities']['canEditDetails'] is False
    assert data['capabilities']['readOnly'] is True
    assert data['details']['pickupItems']['rowCount'] == 1
    assert data['aggregate']['detailRegions'][0]['relationType'] == 'master_detail'
    assert data['aggregate']['detailRegions'][0]['detailEditMode'] == 'inline_table'


@pytest.mark.django_db
def test_aggregate_document_update_pickup_supports_diff_patch_rows(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    department = pickup_document_context['department']
    category = pickup_document_context['category']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']

    pickup = AssetPickup.objects.create(
        organization=org,
        applicant=user,
        department=department,
        pickup_date=date.today(),
        pickup_reason='Old reason',
        status='draft',
    )
    item_keep = PickupItem.objects.create(
        organization=org,
        pickup=pickup,
        asset=asset,
        quantity=1,
        remark='Old row',
    )
    asset_b = Asset.objects.create(
        organization=org,
        asset_name='Secondary Laptop',
        asset_category=category,
        purchase_price=Decimal('1200'),
        purchase_date=date.today(),
        asset_status='idle',
        created_by=user,
    )
    asset_c = Asset.objects.create(
        organization=org,
        asset_name='Swap Laptop',
        asset_category=category,
        purchase_price=Decimal('1300'),
        purchase_date=date.today(),
        asset_status='idle',
        created_by=user,
    )
    PickupItem.objects.create(
        organization=org,
        pickup=pickup,
        asset=asset_b,
        quantity=1,
        remark='Delete me',
    )

    response = client.put(
        f'/api/system/objects/AssetPickup/{pickup.id}/document/',
        {
            'master': {
                'department': str(department.id),
                'pickup_date': str(date.today()),
                'pickup_reason': 'Updated reason',
            },
            'details': {
                'pickup_items': {
                    'rows': [
                        {
                            'id': str(item_keep.id),
                            'asset': str(asset_c.id),
                            'quantity': 2,
                            'remark': 'Updated row',
                        },
                        {
                            'asset': str(asset_b.id),
                            'quantity': 1,
                            'remark': 'Created row',
                        },
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    pickup.refresh_from_db()
    item_keep.refresh_from_db()
    updated_items = list(pickup.items.order_by('created_at'))

    assert pickup.pickup_reason == 'Updated reason'
    assert len(updated_items) == 2
    assert item_keep.asset_id == asset_c.id
    assert item_keep.quantity == 2
    assert item_keep.remark == 'Updated row'
    assert any(item.asset_id == asset_b.id and item.remark == 'Created row' for item in updated_items)

    data = payload['data']
    assert data['details']['pickupItems']['rowCount'] == 2
    assert data['capabilities']['canEditDetails'] is True


@pytest.mark.django_db
def test_aggregate_document_get_pickup_includes_workflow_timeline_and_audit_sections(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    department = pickup_document_context['department']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']

    pickup = AssetPickup.objects.create(
        organization=org,
        applicant=user,
        department=department,
        pickup_date=date.today(),
        pickup_reason='Workflow ready',
        status='pending',
        created_by=user,
    )
    PickupItem.objects.create(
        organization=org,
        pickup=pickup,
        asset=asset,
        quantity=1,
        remark='Workflow item',
        created_by=user,
    )
    ActivityLogService.log_create(actor=user, instance=pickup, organization=org)

    workflow_definition = WorkflowDefinition.objects.create(
        organization=org,
        code=f'pickup_workflow_{uuid.uuid4().hex[:8]}',
        name='Pickup Workflow',
        business_object_code='asset_pickup',
        status='published',
        graph_data={
            'nodes': [
                {'id': 'start', 'type': 'start'},
                {'id': 'end', 'type': 'end'},
            ],
            'edges': [],
        },
        created_by=user,
    )
    workflow_instance = WorkflowInstance.objects.create(
        organization=org,
        definition=workflow_definition,
        instance_no=f'WF-{uuid.uuid4().hex[:8].upper()}',
        business_object_code='asset_pickup',
        business_id=str(pickup.id),
        business_no=pickup.pickup_no,
        initiator=user,
        title='Pickup Approval',
        status=WorkflowInstance.STATUS_RUNNING,
        created_by=user,
    )
    workflow_task = WorkflowTask.objects.create(
        organization=org,
        instance=workflow_instance,
        node_id='approval_1',
        node_name='Department Approval',
        node_type='approval',
        assignee=user,
        status=WorkflowTask.STATUS_PENDING,
        created_by=user,
    )
    WorkflowApproval.objects.create(
        organization=org,
        task=workflow_task,
        approver=user,
        action=WorkflowApproval.ACTION_APPROVE,
        comment='Approved in test',
        created_by=user,
    )
    WorkflowOperationLog.log_operation(
        operation_type='start',
        actor=user,
        workflow_instance=workflow_instance,
        result='success',
        details={'business_id': str(pickup.id)},
        organization=org,
        created_by=user,
    )

    response = client.get(f'/api/system/objects/AssetPickup/{pickup.id}/document/?mode=readonly')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['workflow']['hasPublishedDefinition'] is True
    assert data['workflow']['hasInstance'] is True
    assert data['workflow']['instance']['businessObjectCode'] == 'asset_pickup'
    assert any(item['source'] == 'workflowApproval' for item in data['workflow']['timeline'])
    assert any(item['source'] == 'workflowOperation' for item in data['workflow']['timeline'])
    assert data['audit']['counts']['workflowApprovals'] == 1
    assert data['audit']['counts']['workflowOperationLogs'] == 1
    assert any(item['source'] == 'activity' for item in data['timeline'])
    assert any(item['source'] == 'workflowApproval' for item in data['timeline'])
    assert any(item['source'] == 'workflowOperation' for item in data['timeline'])


@pytest.mark.django_db
def test_aggregate_document_get_transfer_uses_same_document_contract(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    department = pickup_document_context['department']
    category = pickup_document_context['category']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']

    _register_transfer_master_detail_protocol()
    target_department = Department.objects.create(
        organization=org,
        name='Finance Department',
        code=f'FIN_{uuid.uuid4().hex[:8]}',
    )
    transfer = AssetTransfer.objects.create(
        organization=org,
        from_department=department,
        to_department=target_department,
        transfer_date=date.today(),
        transfer_reason='Department adjustment',
        status='draft',
        created_by=user,
    )
    TransferItem.objects.create(
        organization=org,
        transfer=transfer,
        asset=asset,
        remark='Transfer item',
        created_by=user,
    )

    response = client.get(f'/api/system/objects/AssetTransfer/{transfer.id}/document/?mode=edit')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['context']['objectCode'] == 'AssetTransfer'
    assert data['details']['transferItems']['rowCount'] == 1
    assert data['aggregate']['detailRegions'][0]['relationType'] == 'master_detail'
    assert data['capabilities']['canEditMaster'] is True
    assert data['workflow']['businessObjectCode'] == 'asset_transfer'


@pytest.mark.django_db
def test_aggregate_document_create_purchase_request_uses_master_detail_contract(pickup_document_context):
    org = pickup_document_context['org']
    category = pickup_document_context['category']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Procurement Department {uuid.uuid4().hex[:6]}',
        code=f'PRD_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_purchase_request_master_detail_protocol()
    set_current_organization(str(org.id))

    response = client.post(
        '/api/system/objects/PurchaseRequest/document/',
        {
            'master': {
                'department': str(request_department.id),
                'request_date': str(date.today()),
                'expected_date': str(date.today()),
                'reason': 'Need procurement approval',
                'budget_amount': '5000.00',
                'remark': 'Aggregate create',
            },
            'details': {
                'purchase_request_items': {
                    'rows': [
                        {
                            'asset_category': str(category.id),
                            'item_name': 'Business Laptop',
                            'quantity': 2,
                            'unit': 'pcs',
                            'unit_price': '2500.00',
                            'remark': 'Urgent',
                        }
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['context']['objectCode'] == 'PurchaseRequest'
    assert data['master']['reason'] == 'Need procurement approval'
    assert data['details']['purchaseRequestItems']['rowCount'] == 1
    assert data['aggregate']['detailRegions'][0]['relationType'] == 'master_detail'
    assert data['capabilities']['canSubmit'] is True
    assert data['capabilities']['canApprove'] is False
    assert data['workflow']['businessObjectCode'] == 'purchase_request'

    purchase_request = PurchaseRequest.objects.get(id=data['context']['recordId'])
    assert purchase_request.items.count() == 1


@pytest.mark.django_db
def test_aggregate_document_get_purchase_request_exposes_approval_capabilities(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    category = pickup_document_context['category']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Procurement Department {uuid.uuid4().hex[:6]}',
        code=f'PRD_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_purchase_request_master_detail_protocol()
    set_current_organization(str(org.id))

    purchase_request = PurchaseRequest.objects.create(
        organization=org,
        applicant=user,
        department=request_department,
        request_date=date.today(),
        expected_date=date.today(),
        reason='Approval required',
        status=PurchaseRequestStatus.SUBMITTED,
    )
    PurchaseRequestItem.objects.create(
        organization=org,
        purchase_request=purchase_request,
        asset_category=category,
        sequence=1,
        item_name='Docking Station',
        quantity=1,
        unit='pcs',
        unit_price=Decimal('500.00'),
        total_amount=Decimal('500.00'),
    )

    response = client.get(f'/api/system/objects/PurchaseRequest/{purchase_request.id}/document/?mode=readonly')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['capabilities']['canEditMaster'] is False
    assert data['capabilities']['canSubmit'] is False
    assert data['capabilities']['canApprove'] is True
    assert data['capabilities']['readOnly'] is True
    assert data['details']['purchaseRequestItems']['rowCount'] == 1


@pytest.mark.django_db
def test_aggregate_document_update_purchase_request_supports_diff_patch_rows(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    category = pickup_document_context['category']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Procurement Department {uuid.uuid4().hex[:6]}',
        code=f'PRD_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_purchase_request_master_detail_protocol()
    set_current_organization(str(org.id))

    purchase_request = PurchaseRequest.objects.create(
        organization=org,
        applicant=user,
        department=request_department,
        request_date=date.today(),
        expected_date=date.today(),
        reason='Old reason',
        status=PurchaseRequestStatus.DRAFT,
    )
    kept_item = PurchaseRequestItem.objects.create(
        organization=org,
        purchase_request=purchase_request,
        asset_category=category,
        sequence=1,
        item_name='Keep Item',
        quantity=1,
        unit='pcs',
        unit_price=Decimal('1000.00'),
        total_amount=Decimal('1000.00'),
        remark='Old row',
    )
    PurchaseRequestItem.objects.create(
        organization=org,
        purchase_request=purchase_request,
        asset_category=category,
        sequence=2,
        item_name='Delete Item',
        quantity=1,
        unit='pcs',
        unit_price=Decimal('300.00'),
        total_amount=Decimal('300.00'),
    )

    response = client.put(
        f'/api/system/objects/PurchaseRequest/{purchase_request.id}/document/',
        {
            'master': {
                'department': str(request_department.id),
                'request_date': str(date.today()),
                'expected_date': str(date.today()),
                'reason': 'Updated reason',
                'budget_amount': '3300.00',
            },
            'details': {
                'purchase_request_items': {
                    'rows': [
                        {
                            'id': str(kept_item.id),
                            'asset_category': str(category.id),
                            'item_name': 'Updated Item',
                            'quantity': 3,
                            'unit': 'pcs',
                            'unit_price': '1000.00',
                            'remark': 'Updated row',
                        },
                        {
                            'asset_category': str(category.id),
                            'item_name': 'New Item',
                            'quantity': 1,
                            'unit': 'pcs',
                            'unit_price': '300.00',
                            'remark': 'Created row',
                        },
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    purchase_request.refresh_from_db()
    kept_item.refresh_from_db()
    updated_items = list(purchase_request.items.order_by('sequence'))

    assert purchase_request.reason == 'Updated reason'
    assert len(updated_items) == 2
    assert kept_item.item_name == 'Updated Item'
    assert kept_item.quantity == 3
    assert kept_item.remark == 'Updated row'
    assert any(item.item_name == 'New Item' and item.remark == 'Created row' for item in updated_items)

    data = payload['data']
    assert data['details']['purchaseRequestItems']['rowCount'] == 2


@pytest.mark.django_db
def test_aggregate_document_create_asset_receipt_uses_master_detail_contract(pickup_document_context):
    org = pickup_document_context['org']
    category = pickup_document_context['category']
    client = pickup_document_context['client']

    _register_receipt_master_detail_protocol()
    set_current_organization(str(org.id))

    response = client.post(
        '/api/system/objects/AssetReceipt/document/',
        {
            'master': {
                'receipt_date': str(date.today()),
                'receipt_type': 'purchase',
                'supplier': 'Preferred Vendor',
                'delivery_no': 'DN-001',
                'remark': 'Aggregate receipt create',
            },
            'details': {
                'receipt_items': {
                    'rows': [
                        {
                            'asset_category': str(category.id),
                            'item_name': 'Business Laptop',
                            'specification': '14-inch',
                            'brand': 'OpenAI',
                            'ordered_quantity': 2,
                            'received_quantity': 2,
                            'qualified_quantity': 2,
                            'unit_price': '5000.00',
                            'remark': 'Ready for inspection',
                        }
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['context']['objectCode'] == 'AssetReceipt'
    assert data['master']['supplier'] == 'Preferred Vendor'
    assert data['details']['receiptItems']['rowCount'] == 1
    assert data['aggregate']['detailRegions'][0]['relationType'] == 'master_detail'
    assert data['capabilities']['canSubmit'] is True
    assert data['capabilities']['canApprove'] is False

    receipt = AssetReceipt.objects.get(id=data['context']['recordId'])
    assert receipt.items.count() == 1


@pytest.mark.django_db
def test_aggregate_document_update_asset_receipt_supports_diff_patch_rows(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    category = pickup_document_context['category']
    client = pickup_document_context['client']

    _register_receipt_master_detail_protocol()
    set_current_organization(str(org.id))

    receipt = AssetReceipt.objects.create(
        organization=org,
        receipt_date=date.today(),
        receipt_type='purchase',
        supplier='Old Vendor',
        delivery_no='OLD-001',
        receiver=user,
        status=AssetReceiptStatus.DRAFT,
        remark='Old remark',
    )
    existing_item = AssetReceiptItem.objects.create(
        organization=org,
        asset_receipt=receipt,
        asset_category=category,
        sequence=1,
        item_name='Old Item',
        specification='Old Spec',
        brand='OpenAI',
        ordered_quantity=1,
        received_quantity=1,
        qualified_quantity=1,
        defective_quantity=0,
        unit_price=Decimal('1000.00'),
        total_amount=Decimal('1000.00'),
        remark='Old row',
    )

    response = client.put(
        f'/api/system/objects/AssetReceipt/{receipt.id}/document/',
        {
            'master': {
                'receipt_date': str(date.today()),
                'receipt_type': 'purchase',
                'supplier': 'Updated Vendor',
                'delivery_no': 'NEW-001',
                'remark': 'Updated remark',
            },
            'details': {
                'receipt_items': {
                    'rows': [
                        {
                            'id': str(existing_item.id),
                            'asset_category': str(category.id),
                            'item_name': 'Updated Item',
                            'specification': 'Updated Spec',
                            'brand': 'OpenAI',
                            'ordered_quantity': 2,
                            'received_quantity': 2,
                            'qualified_quantity': 2,
                            'unit_price': '1500.00',
                            'remark': 'Updated row',
                        },
                        {
                            'asset_category': str(category.id),
                            'item_name': 'New Item',
                            'specification': 'New Spec',
                            'brand': 'OpenAI',
                            'ordered_quantity': 1,
                            'received_quantity': 1,
                            'qualified_quantity': 1,
                            'unit_price': '300.00',
                            'remark': 'Created row',
                        },
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    receipt.refresh_from_db()
    existing_item.refresh_from_db()
    updated_items = list(receipt.items.order_by('sequence'))

    assert receipt.supplier == 'Updated Vendor'
    assert receipt.delivery_no == 'NEW-001'
    assert len(updated_items) == 2
    assert existing_item.item_name == 'Updated Item'
    assert existing_item.received_quantity == 2
    assert existing_item.total_amount == Decimal('3000.00')
    assert any(item.item_name == 'New Item' and item.remark == 'Created row' for item in updated_items)

    data = payload['data']
    assert data['details']['receiptItems']['rowCount'] == 2


@pytest.mark.django_db
def test_aggregate_document_create_disposal_request_uses_master_detail_contract(pickup_document_context):
    org = pickup_document_context['org']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Disposal Department {uuid.uuid4().hex[:6]}',
        code=f'DSP_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_disposal_master_detail_protocol()
    set_current_organization(str(org.id))

    response = client.post(
        '/api/system/objects/DisposalRequest/document/',
        {
            'master': {
                'disposal_type': 'scrap',
                'department': str(request_department.id),
                'request_date': str(date.today()),
                'disposal_reason': 'Damaged beyond repair',
                'reason_type': 'other',
                'remark': 'Aggregate disposal create',
            },
            'details': {
                'disposal_items': {
                    'rows': [
                        {
                            'asset': str(asset.id),
                            'original_value': '1000.00',
                            'accumulated_depreciation': '100.00',
                            'net_value': '900.00',
                            'remark': 'Primary disposal item',
                        }
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['context']['objectCode'] == 'DisposalRequest'
    assert data['details']['disposalItems']['rowCount'] == 1
    assert data['aggregate']['detailRegions'][0]['relationType'] == 'master_detail'
    assert data['capabilities']['canSubmit'] is True

    disposal_request = DisposalRequest.objects.get(id=data['context']['recordId'])
    assert disposal_request.items.count() == 1


@pytest.mark.django_db
def test_aggregate_document_get_disposal_request_exposes_submitted_capabilities(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Disposal Department {uuid.uuid4().hex[:6]}',
        code=f'DSP_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_disposal_master_detail_protocol()
    set_current_organization(str(org.id))

    disposal_request = DisposalRequest.objects.create(
        organization=org,
        applicant=user,
        department=request_department,
        request_date=date.today(),
        disposal_type='scrap',
        disposal_reason='Replacement cycle',
        reason_type='other',
        status=DisposalRequestStatus.SUBMITTED,
    )
    DisposalItem.objects.create(
        organization=org,
        disposal_request=disposal_request,
        asset=asset,
        sequence=1,
        original_value=Decimal('1000.00'),
        accumulated_depreciation=Decimal('100.00'),
        net_value=Decimal('900.00'),
        remark='Submitted item',
    )

    response = client.get(f'/api/system/objects/DisposalRequest/{disposal_request.id}/document/?mode=readonly')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['capabilities']['canEditMaster'] is False
    assert data['capabilities']['canSubmit'] is False
    assert data['capabilities']['canApprove'] is True
    assert data['capabilities']['readOnly'] is True
    assert data['details']['disposalItems']['rowCount'] == 1


@pytest.mark.django_db
def test_aggregate_document_get_disposal_request_edit_mode_exposes_detail_only_capabilities(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Disposal Department {uuid.uuid4().hex[:6]}',
        code=f'DSP_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_disposal_master_detail_protocol()
    set_current_organization(str(org.id))

    disposal_request = DisposalRequest.objects.create(
        organization=org,
        applicant=user,
        department=request_department,
        request_date=date.today(),
        disposal_type='scrap',
        disposal_reason='Technical appraisal in progress',
        reason_type='other',
        status=DisposalRequestStatus.APPRAISING,
    )
    DisposalItem.objects.create(
        organization=org,
        disposal_request=disposal_request,
        asset=asset,
        sequence=1,
        original_value=Decimal('1000.00'),
        accumulated_depreciation=Decimal('100.00'),
        net_value=Decimal('900.00'),
        remark='Needs valuation',
    )

    response = client.get(f'/api/system/objects/DisposalRequest/{disposal_request.id}/document/?mode=edit')

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    data = payload['data']
    assert data['capabilities']['canEditMaster'] is False
    assert data['capabilities']['canEditDetails'] is True
    assert data['capabilities']['canSave'] is True
    assert data['capabilities']['canApprove'] is True
    assert data['capabilities']['readOnly'] is False
    assert data['details']['disposalItems']['editable'] is True


@pytest.mark.django_db
def test_aggregate_document_update_disposal_request_allows_execution_stage_detail_updates(pickup_document_context):
    org = pickup_document_context['org']
    user = pickup_document_context['user']
    asset = pickup_document_context['asset']
    client = pickup_document_context['client']
    request_department = Organization.objects.create(
        name=f'Disposal Department {uuid.uuid4().hex[:6]}',
        code=f'DSP_{uuid.uuid4().hex[:6]}',
        parent=org,
        org_type='department',
    )

    _register_disposal_master_detail_protocol()
    set_current_organization(str(org.id))

    disposal_request = DisposalRequest.objects.create(
        organization=org,
        applicant=user,
        department=request_department,
        request_date=date.today(),
        disposal_type='scrap',
        disposal_reason='Original execution reason',
        reason_type='other',
        status=DisposalRequestStatus.EXECUTING,
    )
    disposal_item = DisposalItem.objects.create(
        organization=org,
        disposal_request=disposal_request,
        asset=asset,
        sequence=1,
        original_value=Decimal('1000.00'),
        accumulated_depreciation=Decimal('100.00'),
        net_value=Decimal('900.00'),
        remark='Execution pending',
    )

    response = client.put(
        f'/api/system/objects/DisposalRequest/{disposal_request.id}/document/',
        {
            'master': {
                'disposal_reason': 'Should stay unchanged',
            },
            'details': {
                'disposal_items': {
                    'rows': [
                        {
                            'id': str(disposal_item.id),
                            'asset': str(asset.id),
                            'actual_residual_value': '250.00',
                            'buyer_info': 'Recovered materials vendor',
                            'disposal_executed': True,
                        }
                    ]
                }
            }
        },
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload['success'] is True

    disposal_request.refresh_from_db()
    disposal_item.refresh_from_db()

    assert disposal_request.disposal_reason == 'Original execution reason'
    assert disposal_item.disposal_executed is True
    assert disposal_item.actual_residual_value == Decimal('250.00')
    assert disposal_item.buyer_info == 'Recovered materials vendor'
    assert disposal_item.executed_at is not None

    data = payload['data']
    assert data['capabilities']['canEditMaster'] is False
    assert data['capabilities']['canEditDetails'] is True
    assert data['capabilities']['canSave'] is True


def test_aggregate_document_service_supports_first_batch_asset_operations():
    service = AggregateDocumentService()
    assert service.supports_object('AssetPickup') is True
    assert service.supports_object('AssetTransfer') is True
    assert service.supports_object('AssetReturn') is True
    assert service.supports_object('AssetLoan') is True
    assert service.supports_object('PurchaseRequest') is True
    assert service.supports_object('AssetReceipt') is True
    assert service.supports_object('DisposalRequest') is True
    assert service.supports_object('UnknownObject') is False
