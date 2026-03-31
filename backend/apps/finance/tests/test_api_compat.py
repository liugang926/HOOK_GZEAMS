import uuid
from decimal import Decimal
from datetime import date
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.models import User, UserOrganization
from apps.assets.models import Asset, AssetCategory
from apps.depreciation.models import DepreciationRecord
from apps.finance.models import FinanceVoucher, VoucherEntry
from apps.finance.tasks import _create_failure_alert
from apps.integration.models import IntegrationLog
from apps.notifications.models import Notification
from apps.organizations.models import Department, Organization, UserDepartment


class FinanceApiCompatTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Finance Org {suffix}',
            code=f'FIN_ORG_{suffix}'
        )
        self.user = User.objects.create_user(
            username=f'fin_user_{suffix}',
            password='pass123456',
            organization=self.org
        )
        self.department = Department.objects.create(
            organization=self.org,
            code=f'FIN_DEPT_{suffix}',
            name='Finance Operations',
            created_by=self.user,
        )
        UserDepartment.objects.create(
            organization=self.org,
            user=self.user,
            department=self.department,
            is_primary=True,
            created_by=self.user,
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role='admin',
            is_active=True,
            is_primary=True
        )
        self.user.current_organization = self.org
        self.user.save(update_fields=['current_organization'])
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'CAT_{suffix}',
            name='Category',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Finance Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('1200.00'),
            purchase_date=date.today(),
            created_by=self.user
        )

        self.voucher = FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-{suffix}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Test voucher',
            total_amount=Decimal('100.00'),
            status='approved',
            created_by=self.user
        )
        VoucherEntry.objects.create(
            organization=self.org,
            voucher=self.voucher,
            account_code='1001',
            account_name='Debit',
            debit_amount=Decimal('100.00'),
            credit_amount=Decimal('0.00'),
            description='d1',
            line_no=1,
            created_by=self.user
        )
        VoucherEntry.objects.create(
            organization=self.org,
            voucher=self.voucher,
            account_code='2001',
            account_name='Credit',
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('100.00'),
            description='c1',
            line_no=2,
            created_by=self.user
        )
        self.draft_voucher = FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-DR-{suffix}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Draft voucher',
            total_amount=Decimal('80.00'),
            status='draft',
            created_by=self.user
        )

    def tearDown(self):
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        super().tearDown()

    def test_push_endpoint_alias(self):
        response = self.client.post(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/push/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['success'])
        self.assertIn('task_id', response.data['data'])
        self.assertIn('queued', response.data['data'])
        self.voucher.refresh_from_db()
        # Async mode keeps status approved until worker consumes the queue.
        self.assertIn(self.voucher.status, ['approved', 'posted'])

    def test_entries_get_and_put(self):
        get_response = self.client.get(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/entries/')
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertTrue(get_response.data['success'])
        self.assertIn('entries', get_response.data['data'])

        payload = {
            'entries': [
                {'accountCode': '1001', 'accountName': 'Debit2', 'debit': 300, 'credit': 0, 'description': 'd2'},
                {'accountCode': '2001', 'accountName': 'Credit2', 'debit': 0, 'credit': 300, 'description': 'c2'},
            ]
        }
        put_response = self.client.put(
            f'/api/system/objects/FinanceVoucher/{self.voucher.id}/entries/',
            payload,
            format='json'
        )
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.assertTrue(put_response.data['success'])
        self.assertEqual(len(put_response.data['data']['entries']), 2)
        self.assertTrue(put_response.data['data']['is_balanced'])

    def test_entries_put_validation_and_unbalanced_result(self):
        invalid_response = self.client.put(
            f'/api/system/objects/FinanceVoucher/{self.voucher.id}/entries/',
            {'entries': {'not': 'a-list'}},
            format='json'
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(invalid_response.data['success'])
        self.assertEqual(invalid_response.data['error']['code'], 'VALIDATION_ERROR')

        payload = {
            'entries': [
                {'accountCode': '1001', 'accountName': 'Debit', 'debit': 100, 'credit': 0, 'description': 'd'},
                {'accountCode': '2001', 'accountName': 'Credit', 'debit': 0, 'credit': 50, 'description': 'c'},
            ]
        }
        put_response = self.client.put(
            f'/api/system/objects/FinanceVoucher/{self.voucher.id}/entries/',
            payload,
            format='json'
        )
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.assertTrue(put_response.data['success'])
        self.assertFalse(put_response.data['data']['is_balanced'])
        self.voucher.refresh_from_db()
        self.assertEqual(self.voucher.total_amount, Decimal('100.00'))

    def test_generate_asset_purchase_and_depreciation(self):
        asset_payload = {'businessId': 'PR-1', 'assetIds': [str(self.asset.id)]}
        asset_response = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/asset-purchase/',
            asset_payload,
            format='json'
        )
        self.assertEqual(asset_response.status_code, status.HTTP_200_OK)
        self.assertTrue(asset_response.data['success'])
        self.assertEqual(asset_response.data['data']['business_type'], 'purchase')
        self.assertEqual(asset_response.data['data']['source_object_code'], 'Asset')
        self.assertEqual(asset_response.data['data']['source_record_no'], self.asset.asset_code)
        self.assertEqual(asset_response.data['data']['source_asset_count'], 1)
        self.assertEqual(asset_response.data['data']['source_summary']['asset_count'], 1)

        DepreciationRecord.objects.create(
            organization=self.org,
            asset=self.asset,
            period='2026-02',
            depreciation_amount=Decimal('80.00'),
            accumulated_amount=Decimal('80.00'),
            net_value=Decimal('1120.00'),
            status='calculated',
            created_by=self.user
        )
        dep_response = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/depreciation/',
            {'period': '2026-02'},
            format='json'
        )
        self.assertEqual(dep_response.status_code, status.HTTP_200_OK)
        self.assertTrue(dep_response.data['success'])
        self.assertEqual(dep_response.data['data']['business_type'], 'depreciation')
        self.assertEqual(dep_response.data['data']['source_object_code'], 'DepreciationRecord')
        self.assertEqual(dep_response.data['data']['source_record_no'], '2026-02')

    def test_generate_disposal(self):
        response = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/disposal/',
            {'assetId': str(self.asset.id), 'businessId': 'DSP-1'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['business_type'], 'disposal')
        self.assertEqual(Decimal(str(response.data['data']['total_amount'])), Decimal('1200.00'))
        self.assertEqual(len(response.data['data']['entries']), 2)
        self.assertEqual(response.data['data']['source_object_code'], 'Asset')
        self.assertEqual(response.data['data']['source_record_no'], self.asset.asset_code)
        self.assertEqual(response.data['data']['source_summary']['asset_count'], 1)

    def test_generate_endpoints_validation_errors(self):
        asset_missing = self.client.post('/api/system/objects/FinanceVoucher/generate/asset-purchase/', {}, format='json')
        self.assertEqual(asset_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(asset_missing.data['success'])
        self.assertEqual(asset_missing.data['error']['code'], 'VALIDATION_ERROR')

        dep_missing = self.client.post('/api/system/objects/FinanceVoucher/generate/depreciation/', {}, format='json')
        self.assertEqual(dep_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(dep_missing.data['success'])
        self.assertEqual(dep_missing.data['error']['code'], 'VALIDATION_ERROR')

        disposal_missing = self.client.post('/api/system/objects/FinanceVoucher/generate/disposal/', {}, format='json')
        self.assertEqual(disposal_missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(disposal_missing.data['success'])
        self.assertEqual(disposal_missing.data['error']['code'], 'VALIDATION_ERROR')

        disposal_not_found = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/disposal/',
            {'assetId': str(uuid.uuid4())},
            format='json'
        )
        self.assertEqual(disposal_not_found.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(disposal_not_found.data['success'])
        self.assertEqual(disposal_not_found.data['error']['code'], 'NOT_FOUND')

    def test_integration_logs_and_retry(self):
        IntegrationLog.objects.create(
            organization=self.org,
            system_type='m18',
            integration_type='m18_finance_voucher',
            action='push',
            request_method='POST',
            request_url='/external/m18/finance/vouchers',
            request_body={'voucher_id': str(self.voucher.id)},
            response_body={'error': 'timeout'},
            status_code=500,
            success=False,
            error_message='timeout',
            business_type='voucher',
            business_id=str(self.voucher.id),
            created_by=self.user
        )

        logs_response = self.client.get(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/integration-logs/')
        self.assertEqual(logs_response.status_code, status.HTTP_200_OK)
        self.assertTrue(logs_response.data['success'])
        self.assertGreaterEqual(len(logs_response.data['data']), 1)

        retry_response = self.client.post(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/retry/', format='json')
        self.assertEqual(retry_response.status_code, status.HTTP_200_OK)
        self.assertTrue(retry_response.data['success'])
        self.assertIn('task_id', retry_response.data['data'])
        self.voucher.refresh_from_db()
        self.assertIn(self.voucher.status, ['approved', 'posted'])

    def test_retry_idempotent_when_already_posted(self):
        self.voucher.status = 'posted'
        self.voucher.erp_voucher_no = 'ERP-EXISTING-001'
        self.voucher.save(update_fields=['status', 'erp_voucher_no', 'updated_at'])
        before_count = IntegrationLog.objects.filter(
            organization=self.org,
            business_id=str(self.voucher.id)
        ).count()

        response = self.client.post(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/retry/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['external_voucher_no'], 'ERP-EXISTING-001')

        after_count = IntegrationLog.objects.filter(
            organization=self.org,
            business_id=str(self.voucher.id)
        ).count()
        self.assertEqual(after_count, before_count + 1)

        latest_log = IntegrationLog.objects.filter(
            organization=self.org,
            business_id=str(self.voucher.id)
        ).order_by('-created_at').first()
        self.assertIsNotNone(latest_log)
        self.assertTrue(latest_log.success)
        self.assertEqual(latest_log.response_body.get('external_voucher_no'), 'ERP-EXISTING-001')

    def test_batch_push_async_with_mixed_results(self):
        unknown_id = str(uuid.uuid4())
        response = self.client.post(
            '/api/system/objects/FinanceVoucher/batch_push/',
            {'ids': [str(self.voucher.id), str(self.draft_voucher.id), unknown_id]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['summary']['total'], 3)
        self.assertEqual(response.data['summary']['succeeded'], 1)
        self.assertEqual(response.data['summary']['failed'], 2)

        rows = {item['id']: item for item in response.data['results']}
        self.assertIn(str(self.voucher.id), rows)
        self.assertTrue(rows[str(self.voucher.id)]['success'])
        self.assertTrue(rows[str(self.voucher.id)].get('queued', False))
        self.assertTrue(bool(rows[str(self.voucher.id)].get('task_id')))

        self.assertIn(str(self.draft_voucher.id), rows)
        self.assertFalse(rows[str(self.draft_voucher.id)]['success'])
        self.assertIn('not ready', rows[str(self.draft_voucher.id)]['error'].lower())

        self.assertIn(unknown_id, rows)
        self.assertFalse(rows[unknown_id]['success'])
        self.assertIn('not found', rows[unknown_id]['error'].lower())

    def test_object_router_finance_actions(self):
        list_response = self.client.get('/api/system/objects/FinanceVoucher/')
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertTrue(list_response.data['success'])
        self.assertIn('results', list_response.data['data'])

        push_response = self.client.post(f'/api/system/objects/FinanceVoucher/{self.voucher.id}/push/', format='json')
        self.assertEqual(push_response.status_code, status.HTTP_200_OK)
        self.assertTrue(push_response.data['success'])
        self.assertTrue(push_response.data['data']['success'])
        self.assertTrue(bool(push_response.data['data'].get('task_id')))

        generate_response = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/disposal/',
            {'assetId': str(self.asset.id), 'businessId': 'DSP-OR-1'},
            format='json'
        )
        self.assertEqual(generate_response.status_code, status.HTTP_200_OK)
        self.assertTrue(generate_response.data['success'])
        self.assertEqual(generate_response.data['data']['business_type'], 'disposal')

    def test_object_router_supports_department_filter(self):
        other_user = User.objects.create_user(
            username=f'fin_other_{uuid.uuid4().hex[:8]}',
            password='pass123456',
            organization=self.org,
        )
        other_department = Department.objects.create(
            organization=self.org,
            code=f'FIN_OTHER_{uuid.uuid4().hex[:8]}',
            name='Other Department',
            created_by=self.user,
        )
        UserDepartment.objects.create(
            organization=self.org,
            user=other_user,
            department=other_department,
            is_primary=True,
            created_by=self.user,
        )
        FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-OTHER-{uuid.uuid4().hex[:8]}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Other department voucher',
            total_amount=Decimal('66.00'),
            status='approved',
            created_by=other_user,
        )

        response = self.client.get(f'/api/system/objects/FinanceVoucher/?department={self.department.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        returned_ids = {item['id'] for item in results}
        self.assertIn(str(self.voucher.id), returned_ids)
        self.assertIn(str(self.draft_voucher.id), returned_ids)
        self.assertEqual(len(returned_ids), 2)

    def test_object_router_supports_source_asset_filter(self):
        generated_response = self.client.post(
            '/api/system/objects/FinanceVoucher/generate/disposal/',
            {'assetId': str(self.asset.id), 'businessId': 'DSP-SCOPE-1'},
            format='json'
        )
        self.assertEqual(generated_response.status_code, status.HTTP_200_OK)
        generated_id = generated_response.data['data']['id']

        other_asset = Asset.objects.create(
            organization=self.org,
            asset_name='Another Finance Asset',
            asset_category=self.category,
            purchase_price=Decimal('900.00'),
            purchase_date=date.today(),
            created_by=self.user
        )
        FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-SOURCE-{uuid.uuid4().hex[:8]}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Unrelated voucher',
            total_amount=Decimal('90.00'),
            status='draft',
            custom_fields={
                'source_object_code': 'Asset',
                'source_id': str(other_asset.id),
                'source_record_no': other_asset.asset_code,
                'asset_ids': [str(other_asset.id)],
                'asset_id_index': f'|{other_asset.id}|',
            },
            created_by=self.user,
        )

        response = self.client.get(f'/api/system/objects/FinanceVoucher/?source_asset={self.asset.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        results = response.data['data']['results']
        returned_ids = {item['id'] for item in results}
        self.assertIn(generated_id, returned_ids)
        self.assertNotIn(str(self.voucher.id), returned_ids)

    def test_object_router_supports_source_purchase_request_and_receipt_filters(self):
        purchase_voucher = FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-PR-{uuid.uuid4().hex[:8]}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Purchase request scoped voucher',
            total_amount=Decimal('1200.00'),
            status='draft',
            custom_fields={
                'source_object_code': 'PurchaseRequest',
                'source_id': 'request-primary',
                'source_record_no': 'PR-PRIMARY',
                'source_purchase_request_id': 'request-1',
                'source_purchase_request_no': 'PR-001',
                'source_receipt_id': 'receipt-1',
                'source_receipt_no': 'RC-001',
            },
            created_by=self.user,
        )
        FinanceVoucher.objects.create(
            organization=self.org,
            voucher_no=f'VCH-OTHER-{uuid.uuid4().hex[:8]}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Other source voucher',
            total_amount=Decimal('800.00'),
            status='draft',
            custom_fields={
                'source_object_code': 'PurchaseRequest',
                'source_id': 'request-other',
                'source_record_no': 'PR-OTHER',
                'source_purchase_request_id': 'request-2',
                'source_purchase_request_no': 'PR-002',
                'source_receipt_id': 'receipt-2',
                'source_receipt_no': 'RC-002',
            },
            created_by=self.user,
        )

        by_request = self.client.get('/api/system/objects/FinanceVoucher/?source_purchase_request=request-1')
        by_receipt = self.client.get('/api/system/objects/FinanceVoucher/?source_receipt=receipt-1')

        self.assertEqual(by_request.status_code, status.HTTP_200_OK)
        self.assertEqual(by_receipt.status_code, status.HTTP_200_OK)
        request_ids = {item['id'] for item in by_request.data['data']['results']}
        receipt_ids = {item['id'] for item in by_receipt.data['data']['results']}
        self.assertIn(str(purchase_voucher.id), request_ids)
        self.assertIn(str(purchase_voucher.id), receipt_ids)

    def test_detail_action_uses_current_request_org_scope(self):
        first_response = self.client.post(
            f'/api/system/objects/FinanceVoucher/{self.voucher.id}/push/',
            format='json'
        )
        self.assertEqual(first_response.status_code, status.HTTP_200_OK)

        suffix = uuid.uuid4().hex[:8]
        org2 = Organization.objects.create(
            name=f'Finance Org Scope {suffix}',
            code=f'FIN_SCOPE_{suffix}',
        )
        user2 = User.objects.create_user(
            username=f'fin_scope_{suffix}',
            password='pass123456',
            organization=org2,
        )
        UserOrganization.objects.create(
            user=user2,
            organization=org2,
            role='admin',
            is_active=True,
            is_primary=True,
        )
        user2.current_organization = org2
        user2.save(update_fields=['current_organization'])

        voucher2 = FinanceVoucher.objects.create(
            organization=org2,
            voucher_no=f'VCH-SCOPE-{suffix}',
            voucher_date=date.today(),
            business_type='purchase',
            summary='Org scope voucher',
            total_amount=Decimal('100.00'),
            status='approved',
            created_by=user2,
        )
        VoucherEntry.objects.create(
            organization=org2,
            voucher=voucher2,
            account_code='1001',
            account_name='Debit',
            debit_amount=Decimal('100.00'),
            credit_amount=Decimal('0.00'),
            description='d',
            line_no=1,
            created_by=user2,
        )
        VoucherEntry.objects.create(
            organization=org2,
            voucher=voucher2,
            account_code='2001',
            account_name='Credit',
            debit_amount=Decimal('0.00'),
            credit_amount=Decimal('100.00'),
            description='c',
            line_no=2,
            created_by=user2,
        )

        client2 = APIClient()
        client2.force_authenticate(user=user2)
        client2.credentials(HTTP_X_ORGANIZATION_ID=str(org2.id))

        second_response = client2.post(
            f'/api/system/objects/FinanceVoucher/{voucher2.id}/push/',
            format='json'
        )
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertTrue(second_response.data['success'])

    def test_failure_alert_uses_notification_service_and_preserves_org(self):
        before = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
            organization=self.org,
        ).count()

        _create_failure_alert(self.voucher, str(self.user.id), 'mock timeout')

        after = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
            organization=self.org,
        ).count()
        self.assertEqual(after, before + 1)

        notification = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
            organization=self.org,
        ).order_by('-created_at').first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.organization_id, self.org.id)
        self.assertIn(self.voucher.voucher_no, notification.title)
        self.assertIn('mock timeout', notification.content)

    def test_failure_alert_fallback_to_direct_inbox_when_service_failed(self):
        before = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
        ).count()

        with patch('apps.finance.tasks.notification_service.send', side_effect=RuntimeError('send failed')):
            _create_failure_alert(self.voucher, str(self.user.id), 'service error')

        after = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
        ).count()
        self.assertEqual(after, before + 1)

        notification = Notification.all_objects.filter(
            recipient=self.user,
            notification_type='finance_voucher_push_failed',
        ).order_by('-created_at').first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.organization_id, self.org.id)
        self.assertEqual(notification.status, 'pending')
