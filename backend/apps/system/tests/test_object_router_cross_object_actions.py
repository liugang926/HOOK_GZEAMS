from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import (
    Asset,
    AssetCategory,
    AssetLoan,
    AssetPickup,
    AssetReturn,
    AssetTransfer,
    LoanItem,
    Location,
    PickupItem,
)
from apps.finance.models import FinanceVoucher
from apps.insurance.models import InsuranceCompany, InsurancePolicy
from apps.inventory.models import InventoryTask
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    DisposalItem,
    DisposalRequest,
    Maintenance,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.organizations.models import Department, Organization
from apps.projects.models import AssetProject, ProjectAsset
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
        self._register_business_object('AssetPickup', 'apps.assets.models.AssetPickup')
        self._register_business_object('AssetTransfer', 'apps.assets.models.AssetTransfer')
        self._register_business_object('AssetReturn', 'apps.assets.models.AssetReturn')
        self._register_business_object('AssetLoan', 'apps.assets.models.AssetLoan')
        self._register_business_object('FinanceVoucher', 'apps.finance.models.FinanceVoucher')
        self._register_business_object('Maintenance', 'apps.lifecycle.models.Maintenance')
        self._register_business_object('DisposalRequest', 'apps.lifecycle.models.DisposalRequest')
        self._register_business_object('InventoryTask', 'apps.inventory.models.InventoryTask')
        self._register_business_object('InsurancePolicy', 'apps.insurance.models.InsurancePolicy')

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

    def test_purchase_request_actions_can_generate_finance_voucher(self):
        purchase_request = PurchaseRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            expected_date=date.today(),
            reason='Need a design workstation',
            status=PurchaseRequestStatus.PROCESSING,
            created_by=self.user,
        )
        asset = Asset.objects.create(
            organization=self.company,
            asset_name='Design Workstation',
            asset_category=self.category,
            purchase_price=Decimal('12888.00'),
            current_value=Decimal('12888.00'),
            purchase_date=date.today(),
            source_purchase_request=purchase_request,
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/PurchaseRequest/{purchase_request.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        generate_action = next(
            action for action in actions_payload['actions']
            if action['actionCode'] == 'purchase.generate_finance_voucher'
        )
        assert generate_action['enabled'] is True

        execute_resp = self.client.post(
            f'/api/system/objects/PurchaseRequest/{purchase_request.id}/actions/purchase.generate_finance_voucher/execute/',
            {},
            format='json',
        )
        assert execute_resp.status_code == 200
        result = execute_resp.json()['data']
        assert result['actionCode'] == 'purchase.generate_finance_voucher'
        assert result['targetObjectCode'] == 'FinanceVoucher'
        assert result['targetUrl'].startswith('/objects/FinanceVoucher/')
        assert result['summary']['voucherNo']
        assert result['summary']['totalAmount'] == '12888.00'

        voucher = FinanceVoucher.objects.get(id=result['targetId'])
        assert voucher.business_type == 'purchase'
        assert voucher.summary == f'Asset purchase voucher ({purchase_request.request_no})'
        assert voucher.total_amount == Decimal('12888.00')
        assert voucher.entries.count() == 2
        assert voucher.custom_fields['source_object_code'] == 'PurchaseRequest'
        assert voucher.custom_fields['source_id'] == str(purchase_request.id)
        assert voucher.custom_fields['source_record_no'] == purchase_request.request_no
        assert voucher.custom_fields['source_purchase_request_id'] == str(purchase_request.id)
        assert voucher.custom_fields['asset_ids'] == [str(asset.id)]

        follow_up_resp = self.client.get(f'/api/system/objects/PurchaseRequest/{purchase_request.id}/actions/')
        assert follow_up_resp.status_code == 200
        follow_up_actions = follow_up_resp.json()['data']['actions']
        follow_up_generate_action = next(
            action for action in follow_up_actions
            if action['actionCode'] == 'purchase.generate_finance_voucher'
        )
        assert follow_up_generate_action['enabled'] is False
        assert voucher.voucher_no in follow_up_generate_action['disabledReason']

    def test_asset_receipt_actions_can_generate_finance_voucher(self):
        purchase_request = PurchaseRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            expected_date=date.today(),
            reason='Need a docking station',
            status=PurchaseRequestStatus.COMPLETED,
            created_by=self.user,
        )
        receipt = AssetReceipt.objects.create(
            organization=self.company,
            purchase_request=purchase_request,
            receipt_date=date.today(),
            receiver=self.user,
            status=AssetReceiptStatus.PASSED,
            created_by=self.user,
        )
        asset = Asset.objects.create(
            organization=self.company,
            asset_name='Docking Station',
            asset_category=self.category,
            purchase_price=Decimal('699.00'),
            current_value=Decimal('699.00'),
            purchase_date=date.today(),
            source_receipt=receipt,
            source_purchase_request=purchase_request,
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/AssetReceipt/{receipt.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        generate_action = next(
            action for action in actions_payload['actions']
            if action['actionCode'] == 'receipt.generate_finance_voucher'
        )
        assert generate_action['enabled'] is True

        execute_resp = self.client.post(
            f'/api/system/objects/AssetReceipt/{receipt.id}/actions/receipt.generate_finance_voucher/execute/',
            {},
            format='json',
        )
        assert execute_resp.status_code == 200
        result = execute_resp.json()['data']
        assert result['actionCode'] == 'receipt.generate_finance_voucher'
        assert result['targetObjectCode'] == 'FinanceVoucher'
        assert result['targetUrl'].startswith('/objects/FinanceVoucher/')
        assert result['summary']['voucherNo']
        assert result['summary']['totalAmount'] == '699.00'

        voucher = FinanceVoucher.objects.get(id=result['targetId'])
        assert voucher.business_type == 'purchase'
        assert voucher.summary == f'Asset purchase voucher ({receipt.receipt_no})'
        assert voucher.total_amount == Decimal('699.00')
        assert voucher.custom_fields['source_object_code'] == 'AssetReceipt'
        assert voucher.custom_fields['source_id'] == str(receipt.id)
        assert voucher.custom_fields['source_record_no'] == receipt.receipt_no
        assert voucher.custom_fields['source_receipt_id'] == str(receipt.id)
        assert voucher.custom_fields['source_purchase_request_id'] == str(purchase_request.id)
        assert voucher.custom_fields['asset_ids'] == [str(asset.id)]

        follow_up_resp = self.client.get(f'/api/system/objects/AssetReceipt/{receipt.id}/actions/')
        assert follow_up_resp.status_code == 200
        follow_up_actions = follow_up_resp.json()['data']['actions']
        follow_up_generate_action = next(
            action for action in follow_up_actions
            if action['actionCode'] == 'receipt.generate_finance_voucher'
        )
        assert follow_up_generate_action['enabled'] is False
        assert voucher.voucher_no in follow_up_generate_action['disabledReason']

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

    def test_asset_actions_can_create_pickup_transfer_loan_and_return_drafts(self):
        asset_department = Department.objects.create(
            organization=self.company,
            code='ASSET_IT',
            name='Asset IT',
            created_by=self.user,
        )
        target_department = Department.objects.create(
            organization=self.company,
            code='ASSET_HR',
            name='Asset HR',
            created_by=self.user,
        )
        location = Location.objects.create(
            organization=self.company,
            name='Central Warehouse',
            location_type='warehouse',
            created_by=self.user,
        )

        idle_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Action Draft Asset',
            asset_category=self.category,
            purchase_price=Decimal('2800.00'),
            current_value=Decimal('2800.00'),
            purchase_date=date.today(),
            asset_status='idle',
            department=asset_department,
            location=location,
            created_by=self.user,
        )

        actions_resp = self.client.get(f'/api/system/objects/Asset/{idle_asset.id}/actions/')
        assert actions_resp.status_code == 200
        actions_payload = actions_resp.json()['data']
        action_codes = {action['actionCode'] for action in actions_payload['actions']}
        assert {
            'asset.create_pickup',
            'asset.create_transfer',
            'asset.create_loan',
        }.issubset(action_codes)

        pickup_resp = self.client.post(
            f'/api/system/objects/Asset/{idle_asset.id}/actions/asset.create_pickup/execute/',
            {},
            format='json',
        )
        assert pickup_resp.status_code == 200
        pickup = AssetPickup.objects.get(id=pickup_resp.json()['data']['targetId'])
        assert pickup.items.count() == 1
        assert pickup.items.first().asset_id == idle_asset.id

        transfer_resp = self.client.post(
            f'/api/system/objects/Asset/{idle_asset.id}/actions/asset.create_transfer/execute/',
            {},
            format='json',
        )
        assert transfer_resp.status_code == 200
        transfer = AssetTransfer.objects.get(id=transfer_resp.json()['data']['targetId'])
        assert transfer.from_department_id == asset_department.id
        assert transfer.to_department_id == target_department.id
        assert transfer.items.count() == 1
        assert transfer.items.first().asset_id == idle_asset.id

        loan_resp = self.client.post(
            f'/api/system/objects/Asset/{idle_asset.id}/actions/asset.create_loan/execute/',
            {},
            format='json',
        )
        assert loan_resp.status_code == 200
        loan = AssetLoan.objects.get(id=loan_resp.json()['data']['targetId'])
        assert loan.items.count() == 1
        assert loan.items.first().asset_id == idle_asset.id

        in_use_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Return Draft Asset',
            asset_category=self.category,
            purchase_price=Decimal('3200.00'),
            current_value=Decimal('3200.00'),
            purchase_date=date.today(),
            asset_status='in_use',
            department=asset_department,
            location=location,
            custodian=self.user,
            user=self.user,
            created_by=self.user,
        )
        project = AssetProject.objects.create(
            organization=self.company,
            project_name='Action Project',
            project_manager=self.user,
            department=asset_department,
            start_date=date.today(),
            status='active',
            created_by=self.user,
        )
        ProjectAsset.objects.create(
            organization=self.company,
            project=project,
            asset=in_use_asset,
            allocation_date=date.today(),
            allocated_by=self.user,
            custodian=self.user,
            return_status='in_use',
            created_by=self.user,
        )

        return_actions_resp = self.client.get(f'/api/system/objects/Asset/{in_use_asset.id}/actions/')
        assert return_actions_resp.status_code == 200
        return_actions = return_actions_resp.json()['data']['actions']
        return_action = next(
            action for action in return_actions
            if action['actionCode'] == 'asset.create_return'
        )
        assert return_action['enabled'] is True

        return_resp = self.client.post(
            f'/api/system/objects/Asset/{in_use_asset.id}/actions/asset.create_return/execute/',
            {},
            format='json',
        )
        assert return_resp.status_code == 200
        return_order = AssetReturn.objects.get(id=return_resp.json()['data']['targetId'])
        assert return_order.items.count() == 1
        assert return_order.items.first().asset_id == in_use_asset.id
        assert return_order.items.first().project_allocation_id is not None

    def test_detail_actions_support_workbench_direct_paths(self):
        pickup_department = Department.objects.create(
            organization=self.company,
            code='PICKUP_DEPT',
            name='Pickup Department',
            created_by=self.user,
        )
        pickup_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Pickup Approval Asset',
            asset_category=self.category,
            purchase_price=Decimal('1500.00'),
            current_value=Decimal('1500.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user,
        )
        pickup = AssetPickup.objects.create(
            organization=self.company,
            applicant=self.user,
            department=pickup_department,
            pickup_date=date.today(),
            status='pending',
            created_by=self.user,
        )
        PickupItem.objects.create(
            organization=self.company,
            pickup=pickup,
            asset=pickup_asset,
            created_by=self.user,
        )

        pickup_resp = self.client.post(
            f'/api/system/objects/AssetPickup/{pickup.id}/approve/',
            {
                'approval': 'approved',
                'comment': 'Approved from workbench',
            },
            format='json',
        )
        assert pickup_resp.status_code == 200
        pickup.refresh_from_db()
        pickup_asset.refresh_from_db()
        assert pickup.status == 'approved'
        assert pickup.approval_comment == 'Approved from workbench'
        assert pickup_asset.asset_status == 'in_use'
        assert pickup_asset.user_id == self.user.id

        loan_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Loan Approval Asset',
            asset_category=self.category,
            purchase_price=Decimal('2100.00'),
            current_value=Decimal('2100.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user,
        )
        loan = AssetLoan.objects.create(
            organization=self.company,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today(),
            status='pending',
            created_by=self.user,
        )
        LoanItem.objects.create(
            organization=self.company,
            loan=loan,
            asset=loan_asset,
            created_by=self.user,
        )

        loan_resp = self.client.post(
            f'/api/system/objects/AssetLoan/{loan.id}/approve/',
            {
                'approval': 'approved',
                'comment': 'Loan approved from workbench',
            },
            format='json',
        )
        assert loan_resp.status_code == 200
        loan.refresh_from_db()
        assert loan.status == 'approved'
        assert loan.approved_by_id == self.user.id
        assert loan.approval_comment == 'Loan approved from workbench'

        confirm_borrow_resp = self.client.post(
            f'/api/system/objects/AssetLoan/{loan.id}/confirm-borrow/',
            {},
            format='json',
        )
        assert confirm_borrow_resp.status_code == 200

        confirm_return_resp = self.client.post(
            f'/api/system/objects/AssetLoan/{loan.id}/confirm-return/',
            {
                'condition': 'minor_damage',
                'comment': 'Screen issue found on return',
            },
            format='json',
        )
        assert confirm_return_resp.status_code == 200
        loan.refresh_from_db()
        loan_asset.refresh_from_db()
        assert loan.status == 'returned'
        assert loan.asset_condition == 'minor_damage'
        assert loan.return_comment == 'Screen issue found on return'
        assert loan_asset.asset_status == 'maintenance'

        disposal_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Disposal Approval Asset',
            asset_category=self.category,
            purchase_price=Decimal('4200.00'),
            current_value=Decimal('1200.00'),
            accumulated_depreciation=Decimal('3000.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user,
        )
        disposal_request = DisposalRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            disposal_reason='Lifecycle cleanup',
            reason_type='obsolete',
            status='appraising',
            created_by=self.user,
        )
        DisposalItem.objects.create(
            organization=self.company,
            disposal_request=disposal_request,
            asset=disposal_asset,
            sequence=1,
            original_value=Decimal('4200.00'),
            accumulated_depreciation=Decimal('3000.00'),
            net_value=Decimal('1200.00'),
            appraisal_result='Recycle',
            residual_value=Decimal('100.00'),
            appraised_by=self.user,
            appraised_at=disposal_request.created_at,
            created_by=self.user,
        )

        disposal_resp = self.client.post(
            f'/api/system/objects/DisposalRequest/{disposal_request.id}/approve/',
            {
                'decision': 'approved',
                'comment': 'Approved after appraisal review',
            },
            format='json',
        )
        assert disposal_resp.status_code == 200
        disposal_request.refresh_from_db()
        assert disposal_request.status == 'approved'
        assert disposal_request.current_approver is None
        assert disposal_request.custom_fields['approval_comment'] == 'Approved after appraisal review'

        maintenance_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Maintenance Action Asset',
            asset_category=self.category,
            purchase_price=Decimal('3600.00'),
            current_value=Decimal('3600.00'),
            purchase_date=date.today(),
            asset_status='maintenance',
            created_by=self.user,
        )
        maintenance = Maintenance.objects.create(
            organization=self.company,
            asset=maintenance_asset,
            reporter=self.user,
            report_time=disposal_request.created_at,
            fault_description='Needs inspection',
            technician=self.user,
            assigned_at=disposal_request.created_at,
            status='assigned',
            created_by=self.user,
        )

        maintenance_resp = self.client.post(
            f'/api/system/objects/Maintenance/{maintenance.id}/start_work/',
            {},
            format='json',
        )
        assert maintenance_resp.status_code == 200
        maintenance.refresh_from_db()
        assert maintenance.status == 'processing'
        assert maintenance.start_time is not None

        maintenance_complete_resp = self.client.post(
            f'/api/system/objects/Maintenance/{maintenance.id}/complete_work/',
            {},
            format='json',
        )
        assert maintenance_complete_resp.status_code == 200
        maintenance.refresh_from_db()
        assert maintenance.status == 'completed'

        maintenance_verify_resp = self.client.post(
            f'/api/system/objects/Maintenance/{maintenance.id}/verify/',
            {
                'result': 'Validated and ready for reuse',
            },
            format='json',
        )
        assert maintenance_verify_resp.status_code == 200
        maintenance.refresh_from_db()
        assert maintenance.verification_result == 'Validated and ready for reuse'

    def test_detail_actions_persist_cancel_reasons_from_workbench_payloads(self):
        purchase_request = PurchaseRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            expected_date=date.today(),
            reason='Cancelled purchase request',
            status='processing',
            created_by=self.user,
        )
        purchase_request_resp = self.client.post(
            f'/api/system/objects/PurchaseRequest/{purchase_request.id}/cancel/',
            {'reason': 'Procurement scope changed'},
            format='json',
        )
        assert purchase_request_resp.status_code == 200
        purchase_request.refresh_from_db()
        assert purchase_request.status == 'cancelled'
        assert purchase_request.custom_fields['cancel_reason'] == 'Procurement scope changed'

        asset_receipt = AssetReceipt.objects.create(
            organization=self.company,
            purchase_request=purchase_request,
            receipt_date=date.today(),
            receiver=self.user,
            status='draft',
            created_by=self.user,
        )
        asset_receipt_resp = self.client.post(
            f'/api/system/objects/AssetReceipt/{asset_receipt.id}/cancel/',
            {'reason': 'Supplier will resend the shipment'},
            format='json',
        )
        assert asset_receipt_resp.status_code == 200
        asset_receipt.refresh_from_db()
        assert asset_receipt.status == 'cancelled'
        assert asset_receipt.custom_fields['cancel_reason'] == 'Supplier will resend the shipment'

        department_from = Department.objects.create(
            organization=self.company,
            code='CANCEL_FROM',
            name='Cancel Source Department',
            created_by=self.user,
        )
        department_to = Department.objects.create(
            organization=self.company,
            code='CANCEL_TO',
            name='Cancel Target Department',
            created_by=self.user,
        )
        return_location = Location.objects.create(
            organization=self.company,
            name='Cancel Return Location',
            created_by=self.user,
        )

        pickup = AssetPickup.objects.create(
            organization=self.company,
            applicant=self.user,
            department=department_from,
            pickup_date=date.today(),
            status='draft',
            created_by=self.user,
        )
        pickup_resp = self.client.post(
            f'/api/system/objects/AssetPickup/{pickup.id}/cancel/',
            {'reason': 'Applicant withdrew the request'},
            format='json',
        )
        assert pickup_resp.status_code == 200
        pickup.refresh_from_db()
        assert pickup.status == 'cancelled'
        assert pickup.custom_fields['cancel_reason'] == 'Applicant withdrew the request'

        transfer = AssetTransfer.objects.create(
            organization=self.company,
            from_department=department_from,
            to_department=department_to,
            transfer_date=date.today(),
            status='draft',
            created_by=self.user,
        )
        transfer_resp = self.client.post(
            f'/api/system/objects/AssetTransfer/{transfer.id}/cancel/',
            {'reason': 'Transfer scope changed'},
            format='json',
        )
        assert transfer_resp.status_code == 200
        transfer.refresh_from_db()
        assert transfer.status == 'cancelled'
        assert transfer.custom_fields['cancel_reason'] == 'Transfer scope changed'

        return_order = AssetReturn.objects.create(
            organization=self.company,
            returner=self.user,
            return_date=date.today(),
            return_location=return_location,
            status='draft',
            created_by=self.user,
        )
        return_resp = self.client.post(
            f'/api/system/objects/AssetReturn/{return_order.id}/cancel/',
            {'reason': 'Return will be merged into another order'},
            format='json',
        )
        assert return_resp.status_code == 200
        return_order.refresh_from_db()
        assert return_order.status == 'cancelled'
        assert return_order.custom_fields['cancel_reason'] == 'Return will be merged into another order'

        loan = AssetLoan.objects.create(
            organization=self.company,
            borrower=self.user,
            borrow_date=date.today(),
            expected_return_date=date.today(),
            status='draft',
            created_by=self.user,
        )
        loan_resp = self.client.post(
            f'/api/system/objects/AssetLoan/{loan.id}/cancel/',
            {'reason': 'Borrower no longer needs the asset'},
            format='json',
        )
        assert loan_resp.status_code == 200
        loan.refresh_from_db()
        assert loan.status == 'cancelled'
        assert loan.custom_fields['cancel_reason'] == 'Borrower no longer needs the asset'

        maintenance_asset = Asset.objects.create(
            organization=self.company,
            asset_name='Maintenance Cancel Asset',
            asset_category=self.category,
            purchase_price=Decimal('1900.00'),
            current_value=Decimal('1900.00'),
            purchase_date=date.today(),
            asset_status='idle',
            created_by=self.user,
        )
        maintenance = Maintenance.objects.create(
            organization=self.company,
            asset=maintenance_asset,
            reporter=self.user,
            report_time=pickup.created_at,
            fault_description='Issue no longer reproducible',
            status='reported',
            created_by=self.user,
        )
        maintenance_resp = self.client.post(
            f'/api/system/objects/Maintenance/{maintenance.id}/cancel/',
            {'reason': 'Fault could not be reproduced'},
            format='json',
        )
        assert maintenance_resp.status_code == 200
        maintenance.refresh_from_db()
        assert maintenance.status == 'cancelled'
        assert maintenance.custom_fields['cancel_reason'] == 'Fault could not be reproduced'

        disposal_request = DisposalRequest.objects.create(
            organization=self.company,
            applicant=self.user,
            department=self.department_org,
            request_date=date.today(),
            disposal_reason='Duplicate request',
            reason_type='other',
            status='approved',
            created_by=self.user,
        )
        disposal_resp = self.client.post(
            f'/api/system/objects/DisposalRequest/{disposal_request.id}/cancel/',
            {'reason': 'Disposal strategy changed'},
            format='json',
        )
        assert disposal_resp.status_code == 200
        disposal_request.refresh_from_db()
        assert disposal_request.status == 'cancelled'
        assert disposal_request.custom_fields['cancel_reason'] == 'Disposal strategy changed'

        inventory_task = InventoryTask.objects.create(
            organization=self.company,
            task_code='INV-CANCEL-ROUTER',
            task_name='Inventory Router Cancel',
            inventory_type=InventoryTask.TYPE_FULL,
            planned_date=date.today(),
            status='pending',
            created_by=self.user,
        )
        inventory_resp = self.client.post(
            f'/api/system/objects/InventoryTask/{inventory_task.id}/cancel/',
            {'reason': 'Store shutdown changed the counting window'},
            format='json',
        )
        assert inventory_resp.status_code == 200
        inventory_task.refresh_from_db()
        assert inventory_task.status == 'cancelled'
        assert inventory_task.custom_fields['cancel_reason'] == 'Store shutdown changed the counting window'

        insurance_company = InsuranceCompany.objects.create(
            organization=self.company,
            code='INS-CANCEL',
            name='Cancel Insurance Carrier',
            created_by=self.user,
        )
        insurance_policy = InsurancePolicy.objects.create(
            organization=self.company,
            policy_no='POL-CANCEL-ROUTER',
            company=insurance_company,
            insurance_type='property',
            start_date=date.today(),
            end_date=date.today(),
            total_insured_amount=Decimal('50000.00'),
            total_premium=Decimal('1800.00'),
            status='active',
            created_by=self.user,
        )
        insurance_resp = self.client.post(
            f'/api/system/objects/InsurancePolicy/{insurance_policy.id}/cancel/',
            {'reason': 'Coverage consolidated into the umbrella policy'},
            format='json',
        )
        assert insurance_resp.status_code == 200
        insurance_policy.refresh_from_db()
        assert insurance_policy.status == 'cancelled'
        assert insurance_policy.custom_fields['cancel_reason'] == 'Coverage consolidated into the umbrella policy'
