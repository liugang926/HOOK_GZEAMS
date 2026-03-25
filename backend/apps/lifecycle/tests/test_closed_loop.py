from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory
from apps.lifecycle.models import (
    AssetReceipt,
    AssetReceiptItem,
    DisposalReason,
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
)
from apps.lifecycle.services import (
    AssetReceiptService,
    DisposalRequestService,
    LifecycleClosedLoopService,
    MaintenanceService,
)
from apps.organizations.models import Organization
from apps.system.activity_log import ActivityLog


class LifecycleClosedLoopTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(
            name='Timeline Org',
            code='TL001',
            org_type='company',
        )
        self.department = Organization.objects.create(
            name='IT Department',
            code='IT',
            org_type='department',
            parent=self.org,
        )
        self.user = User.objects.create_user(
            username='timeline_admin',
            email='timeline@example.com',
            password='testpass123',
            organization=self.org,
        )
        self.client.force_authenticate(self.user)
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='CAT001',
            name='Computers',
        )
        self.purchase_request = PurchaseRequest.objects.create(
            organization=self.org,
            applicant=self.user,
            department=self.department,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date(),
            reason='Need laptops',
            status=PurchaseRequestStatus.APPROVED,
        )
        self.purchase_item = PurchaseRequestItem.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            quantity=2,
            unit='pcs',
            unit_price=5000,
            total_amount=10000,
            suggested_supplier='Demo Supplier',
        )

    def test_generate_assets_auto_completes_purchase_request(self):
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status='passed',
            supplier='Demo Supplier',
        )
        receipt_item = AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=receipt,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            ordered_quantity=2,
            received_quantity=2,
            qualified_quantity=2,
            defective_quantity=0,
            unit_price=5000,
            total_amount=10000,
        )

        result = AssetReceiptService().generate_asset_cards(str(receipt.id), user=self.user)

        self.purchase_request.refresh_from_db()
        receipt_item.refresh_from_db()
        self.assertEqual(result['generated_count'], 2)
        self.assertTrue(receipt_item.asset_generated)
        self.assertEqual(self.purchase_request.status, PurchaseRequestStatus.COMPLETED)
        self.assertEqual(
            Asset.objects.filter(source_purchase_request=self.purchase_request, is_deleted=False).count(),
            2,
        )

        purchase_content_type = ContentType.objects.get_for_model(PurchaseRequest)
        purchase_logs = ActivityLog.objects.filter(
            content_type=purchase_content_type,
            object_id=str(self.purchase_request.id),
            action='status_change',
        )
        self.assertTrue(
            any(
                any(change.get('newValue') == 'Completed' for change in (log.changes or []))
                for log in purchase_logs
            )
        )

    def test_purchase_request_timeline_api_includes_downstream_objects(self):
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status='passed',
            supplier='Demo Supplier',
        )
        AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=receipt,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            ordered_quantity=2,
            received_quantity=2,
            qualified_quantity=2,
            defective_quantity=0,
            unit_price=5000,
            total_amount=10000,
        )
        AssetReceiptService().generate_asset_cards(str(receipt.id), user=self.user)
        asset = Asset.objects.filter(source_receipt=receipt, is_deleted=False).first()

        MaintenanceService().create(
            {
                'asset': asset,
                'fault_description': 'Screen issue',
                'priority': 'normal',
            },
            self.user,
        )
        DisposalRequestService().create_with_items(
            {
                'department': self.department,
                'request_date': timezone.now().date(),
                'disposal_reason': 'Obsolete hardware',
                'reason_type': DisposalReason.OBSOLETE,
                'items': [
                    {
                        'asset': asset,
                        'original_value': 5000,
                        'accumulated_depreciation': 1000,
                        'net_value': 4000,
                    }
                ],
            },
            self.user,
        )

        response = self.client.get(f'/api/lifecycle/purchase-requests/{self.purchase_request.id}/timeline/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        descriptions = [str(item.get('description') or '') for item in response.data['data']]
        self.assertTrue(any('Purchase Request' in item for item in descriptions))
        self.assertTrue(any('Asset Receipt' in item for item in descriptions))
        self.assertTrue(any('Asset' in item for item in descriptions))
        self.assertTrue(any('Maintenance' in item for item in descriptions))
        self.assertTrue(any('Disposal request' in item for item in descriptions))

    def test_closed_loop_service_builds_receipt_timeline(self):
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status='passed',
            supplier='Demo Supplier',
        )
        AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=receipt,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            ordered_quantity=1,
            received_quantity=1,
            qualified_quantity=1,
            defective_quantity=0,
            unit_price=5000,
            total_amount=5000,
        )
        AssetReceiptService().generate_asset_cards(str(receipt.id), user=self.user)

        timeline = LifecycleClosedLoopService().build_receipt_timeline(receipt)

        self.assertGreaterEqual(len(timeline), 3)
        self.assertTrue(any('Asset Receipt' in str(item.get('description') or '') for item in timeline))
        self.assertTrue(any('Asset' in str(item.get('description') or '') for item in timeline))
        self.assertTrue(all(item.get('objectCode') for item in timeline))
        self.assertTrue(all(item.get('objectId') for item in timeline))
        self.assertTrue(all(item.get('sourceLabel') for item in timeline))

    def test_maintenance_completion_restores_asset_status(self):
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET-MT-001',
            asset_name='Working Laptop',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date=timezone.now().date(),
            asset_status='in_use',
        )

        maintenance = MaintenanceService().create(
            {
                'asset': asset,
                'fault_description': 'Keyboard issue',
                'priority': 'normal',
            },
            self.user,
        )
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'maintenance')

        maintenance_service = MaintenanceService()
        maintenance_service.assign_technician(str(maintenance.id), self.user)
        maintenance_service.start_work(str(maintenance.id))

        maintenance_service.complete_work(
            str(maintenance.id),
            {
                'fault_cause': 'Loose cable',
                'repair_method': 'Reconnect',
                'labor_cost': 10,
                'material_cost': 0,
                'other_cost': 0,
            },
            user=self.user,
        )

        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'in_use')

    def test_disposal_execution_and_cancel_restore_asset_status(self):
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET-DS-001',
            asset_name='Retired Laptop',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date=timezone.now().date(),
            asset_status='idle',
        )
        disposal_request = DisposalRequestService().create_with_items(
            {
                'department': self.department,
                'request_date': timezone.now().date(),
                'disposal_reason': 'Obsolete hardware',
                'reason_type': DisposalReason.OBSOLETE,
                'items': [
                    {
                        'asset': asset,
                        'original_value': 5000,
                        'accumulated_depreciation': 1000,
                        'net_value': 4000,
                    }
                ],
            },
            self.user,
        )
        disposal_request.status = 'approved'
        disposal_request.save(update_fields=['status', 'updated_at'])

        DisposalRequestService().start_execution(str(disposal_request.id), actor=self.user)
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'scrapped')

        DisposalRequestService().cancel(str(disposal_request.id), actor=self.user)
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'idle')

    def test_asset_lifecycle_timeline_api_includes_cross_object_events(self):
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status='passed',
            supplier='Demo Supplier',
        )
        AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=receipt,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            ordered_quantity=1,
            received_quantity=1,
            qualified_quantity=1,
            defective_quantity=0,
            unit_price=5000,
            total_amount=5000,
        )
        AssetReceiptService().generate_asset_cards(str(receipt.id), user=self.user)
        asset = Asset.objects.filter(source_receipt=receipt, is_deleted=False).first()
        MaintenanceService().create(
            {
                'asset': asset,
                'fault_description': 'Trackpad issue',
                'priority': 'normal',
            },
            self.user,
        )

        response = self.client.get(f'/api/assets/{asset.id}/lifecycle-timeline/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        timeline = response.data['data']
        descriptions = [str(item.get('description') or '') for item in timeline]
        self.assertTrue(any('Purchase Request' in item for item in descriptions))
        self.assertTrue(any('Asset Receipt' in item for item in descriptions))
        self.assertTrue(any('Asset' in item for item in descriptions))
        self.assertTrue(any('Maintenance' in item for item in descriptions))
        self.assertTrue(any(item.get('objectCode') == 'PurchaseRequest' for item in timeline))
        self.assertTrue(any(item.get('objectCode') == 'AssetReceipt' for item in timeline))
        self.assertTrue(any(item.get('objectCode') == 'Asset' for item in timeline))
        self.assertTrue(any(item.get('recordLabel') == asset.asset_code for item in timeline))

    def test_asset_list_supports_source_traceability_filters(self):
        receipt = AssetReceipt.objects.create(
            organization=self.org,
            purchase_request=self.purchase_request,
            receipt_date=timezone.now().date(),
            receiver=self.user,
            status='passed',
            supplier='Demo Supplier',
        )
        AssetReceiptItem.objects.create(
            organization=self.org,
            asset_receipt=receipt,
            sequence=1,
            asset_category=self.category,
            item_name='Laptop',
            specification='14-inch',
            brand='DemoBrand',
            ordered_quantity=1,
            received_quantity=1,
            qualified_quantity=1,
            defective_quantity=0,
            unit_price=5000,
            total_amount=5000,
        )
        AssetReceiptService().generate_asset_cards(str(receipt.id), user=self.user)
        asset = Asset.objects.filter(source_receipt=receipt, is_deleted=False).first()

        by_receipt = self.client.get(f'/api/assets/?source_receipt={receipt.id}')
        by_request = self.client.get(f'/api/assets/?source_purchase_request={self.purchase_request.id}')

        self.assertEqual(by_receipt.status_code, 200)
        self.assertEqual(by_request.status_code, 200)
        receipt_rows = by_receipt.data.get('results') or by_receipt.data.get('data', {}).get('results', [])
        request_rows = by_request.data.get('results') or by_request.data.get('data', {}).get('results', [])
        self.assertTrue(any(str(row.get('id')) == str(asset.id) for row in receipt_rows))
        self.assertTrue(any(str(row.get('id')) == str(asset.id) for row in request_rows))

    def test_disposal_request_list_supports_asset_filter(self):
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ASSET-DS-FILTER',
            asset_name='Filterable Laptop',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date=timezone.now().date(),
            asset_status='idle',
        )
        disposal_request = DisposalRequestService().create_with_items(
            {
                'department': self.department,
                'request_date': timezone.now().date(),
                'disposal_reason': 'Obsolete hardware',
                'reason_type': DisposalReason.OBSOLETE,
                'items': [
                    {
                        'asset': asset,
                        'original_value': 5000,
                        'accumulated_depreciation': 1000,
                        'net_value': 4000,
                    }
                ],
            },
            self.user,
        )

        response = self.client.get(f'/api/lifecycle/disposal-requests/?asset_id={asset.id}')

        self.assertEqual(response.status_code, 200)
        rows = response.data.get('results') or response.data.get('data', {}).get('results', [])
        self.assertTrue(any(str(row.get('id')) == str(disposal_request.id) for row in rows))
