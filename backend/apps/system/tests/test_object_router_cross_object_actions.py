from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    DisposalRequest,
    Maintenance,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.organizations.models import Organization
from apps.system.models import BusinessObject


@pytest.mark.django_db
class TestObjectRouterCrossObjectActions:
    def setup_method(self):
        self.company = Organization.objects.create(
            name='Lifecycle Company',
            code='LIFECYCLE_COMPANY',
            org_type='company',
        )
        self.department_org = Organization.objects.create(
            name='Lifecycle IT',
            code='LIFECYCLE_IT',
            org_type='department',
            parent=self.company,
        )
        self.user = User.objects.create_user(
            username='lifecycle_action_user',
            password='pass123456',
            organization=self.company,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.company.id))

        self.category = AssetCategory.objects.create(
            organization=self.company,
            code='LIFECYCLE_CAT',
            name='Lifecycle Category',
            created_by=self.user,
        )

        self._register_business_object('PurchaseRequest', 'apps.lifecycle.models.PurchaseRequest')
        self._register_business_object('AssetReceipt', 'apps.lifecycle.models.AssetReceipt')
        self._register_business_object('Asset', 'apps.assets.models.Asset')
        self._register_business_object('Maintenance', 'apps.lifecycle.models.Maintenance')
        self._register_business_object('DisposalRequest', 'apps.lifecycle.models.DisposalRequest')

    def _register_business_object(self, code: str, model_path: str) -> None:
        BusinessObject.objects.update_or_create(
            code=code,
            defaults={
                'name': code,
                'name_en': code,
                'is_hardcoded': True,
                'django_model_path': model_path,
            },
        )

    def test_purchase_request_actions_can_create_asset_receipt(self):
        purchase_request = PurchaseRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            expected_date=date.today(),
            reason='Need a new laptop',
            status=PurchaseRequestStatus.APPROVED,
            created_by=self.user,
        )
        PurchaseRequestItem.objects.create(
            organization=self.company,
            purchase_request=purchase_request,
            asset_category=self.category,
            sequence=1,
            item_name='Laptop',
            specification='14-inch',
            brand='OpenAI',
            quantity=2,
            unit='pcs',
            unit_price=Decimal('8000.00'),
            total_amount=Decimal('16000.00'),
            suggested_supplier='Preferred Vendor',
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/PurchaseRequest/{purchase_request.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        create_receipt_action = next(
            action for action in actions_payload['actions']
            if action['actionCode'] == 'purchase.create_receipt'
        )
        assert create_receipt_action['enabled'] is True

        execute_resp = self.client.post(
            f'/api/system/objects/PurchaseRequest/{purchase_request.id}/actions/purchase.create_receipt/execute/',
            {},
            format='json',
        )
        assert execute_resp.status_code == 200
        result = execute_resp.json()['data']
        assert result['targetObjectCode'] == 'AssetReceipt'
        assert result['targetUrl'].startswith('/objects/AssetReceipt/')

        receipt = AssetReceipt.objects.get(id=result['targetId'])
        assert receipt.purchase_request_id == purchase_request.id
        assert receipt.receiver_id == self.user.id
        assert receipt.items.count() == 1

        receipt_item = receipt.items.first()
        assert receipt_item.item_name == 'Laptop'
        assert receipt_item.ordered_quantity == 2
        assert receipt_item.received_quantity == 2
        assert receipt_item.qualified_quantity == 2

        purchase_request.refresh_from_db()
        assert purchase_request.status == PurchaseRequestStatus.PROCESSING

    def test_asset_receipt_actions_can_generate_assets(self):
        receipt = AssetReceipt.objects.create(
            organization=self.company,
            purchase_request=None,
            receipt_date=date.today(),
            receiver=self.user,
            status=AssetReceiptStatus.PASSED,
            created_by=self.user,
        )
        item = AssetReceiptItem.objects.create(
            organization=self.company,
            asset_receipt=receipt,
            asset_category=self.category,
            sequence=1,
            item_name='Monitor',
            specification='27-inch',
            brand='OpenAI',
            ordered_quantity=1,
            received_quantity=1,
            qualified_quantity=1,
            defective_quantity=0,
            unit_price=Decimal('1200.00'),
            total_amount=Decimal('1200.00'),
            asset_generated=False,
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/AssetReceipt/{receipt.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        generate_action = next(
            action for action in actions_payload['actions']
            if action['actionCode'] == 'receipt.generate_assets'
        )
        assert generate_action['enabled'] is True

        execute_resp = self.client.post(
            f'/api/system/objects/AssetReceipt/{receipt.id}/actions/receipt.generate_assets/execute/',
            {},
            format='json',
        )
        assert execute_resp.status_code == 200
        result = execute_resp.json()['data']
        assert result['actionCode'] == 'receipt.generate_assets'
        assert result['summary']['assetsGenerated'] == 1
        assert result['summary']['generatedItems'] == 1
        assert result['summary']['pendingGeneration'] == 0
        assert result['generatedCount'] == 1
        assert result['targetObjectCode'] == 'Asset'
        assert result['targetUrl'] == f'/objects/Asset/{result["generatedAssets"][0]["id"]}'
        assert result['navigateAfterSuccess'] is False
        assert len(result['generatedAssets']) == 1

        item.refresh_from_db()
        assert item.asset_generated is True
        asset = Asset.objects.get(id=result['generatedAssets'][0]['id'])
        assert asset.asset_name == 'Monitor'
        assert asset.source_receipt_id == receipt.id
        assert asset.source_receipt_item_id == item.id
        assert asset.source_purchase_request_id is None
        assert asset.asset_status == 'idle'
        assert asset.status_logs.count() == 1

    def test_asset_actions_can_create_maintenance_and_disposal(self):
        asset = Asset.objects.create(
            organization=self.company,
            asset_name='Demo Asset',
            asset_category=self.category,
            purchase_price=Decimal('5000.00'),
            current_value=Decimal('3200.00'),
            accumulated_depreciation=Decimal('1800.00'),
            purchase_date=date.today(),
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/Asset/{asset.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        action_codes = {action['actionCode'] for action in actions_payload['actions']}
        assert {'asset.create_maintenance', 'asset.create_disposal'}.issubset(action_codes)

        maintenance_resp = self.client.post(
            f'/api/system/objects/Asset/{asset.id}/actions/asset.create_maintenance/execute/',
            {},
            format='json',
        )
        assert maintenance_resp.status_code == 200
        maintenance_result = maintenance_resp.json()['data']
        assert maintenance_result['targetObjectCode'] == 'Maintenance'

        maintenance = Maintenance.objects.get(id=maintenance_result['targetId'])
        assert maintenance.asset_id == asset.id
        assert maintenance.reporter_id == self.user.id

        disposal_resp = self.client.post(
            f'/api/system/objects/Asset/{asset.id}/actions/asset.create_disposal/execute/',
            {},
            format='json',
        )
        assert disposal_resp.status_code == 200
        disposal_result = disposal_resp.json()['data']
        assert disposal_result['targetObjectCode'] == 'DisposalRequest'

        disposal_request = DisposalRequest.objects.get(id=disposal_result['targetId'])
        assert disposal_request.department_id == self.department_org.id
        assert disposal_request.items.count() == 1
        assert disposal_request.items.first().asset_id == asset.id
