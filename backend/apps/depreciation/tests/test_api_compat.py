import uuid
from decimal import Decimal
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.models import User, UserOrganization
from apps.assets.models import Asset, AssetCategory
from apps.depreciation.models import DepreciationConfig, DepreciationRecord
from apps.organizations.models import Organization


class DepreciationApiCompatTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Dep Org {suffix}',
            code=f'DEP_ORG_{suffix}'
        )
        self.user = User.objects.create_user(
            username=f'dep_user_{suffix}',
            password='pass123456',
            organization=self.org
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
            code=f'DEP_CAT_{suffix}',
            name='Dep Category',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_name='Depreciation Test Asset',
            asset_category=self.category,
            purchase_price=Decimal('2000.00'),
            purchase_date=date.today(),
            useful_life=24,
            current_value=Decimal('2000.00'),
            accumulated_depreciation=Decimal('0.00'),
            created_by=self.user
        )
        self.record = DepreciationRecord.objects.create(
            organization=self.org,
            asset=self.asset,
            period='2026-02',
            depreciation_amount=Decimal('100.00'),
            accumulated_amount=Decimal('100.00'),
            net_value=Decimal('1900.00'),
            status='calculated',
            created_by=self.user
        )
        self.config = DepreciationConfig.objects.create(
            organization=self.org,
            category=self.category,
            depreciation_method='straight_line',
            useful_life=60,
            salvage_value_rate=Decimal('5.00'),
            is_active=True,
            created_by=self.user
        )

    def tearDown(self):
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        super().tearDown()

    def test_submit_and_approve_record_alias(self):
        submit_response = self.client.post(f'/api/system/objects/DepreciationRecord/{self.record.id}/submit/')
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertTrue(submit_response.data['success'])

        approve_response = self.client.post(
            f'/api/system/objects/DepreciationRecord/{self.record.id}/approve/',
            {'action': 'approve'},
            format='json'
        )
        self.assertEqual(approve_response.status_code, status.HTTP_200_OK)
        self.assertTrue(approve_response.data['success'])
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'posted')

    def test_asset_detail_endpoint_alias(self):
        response = self.client.get(f'/api/system/objects/DepreciationRecord/assets/{self.asset.id}/detail/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['asset_info']['asset_code'], self.asset.asset_code)
        self.assertEqual(len(response.data['data']['records']), 1)

    def test_export_report_endpoint_alias(self):
        response = self.client.get('/api/system/objects/DepreciationRecord/report/export/?period=2026-02&fileFormat=csv')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', response['Content-Type'])

    def test_record_list_supports_asset_keyword_filter(self):
        response = self.client.get('/api/system/objects/DepreciationRecord/', {
            'asset': 'Test Asset',
            'period': '2026-02',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['asset_name'], self.asset.asset_name)

    def test_report_returns_asset_breakdown_with_category_ids_filter(self):
        other_category = AssetCategory.objects.create(
            organization=self.org,
            code=f'{self.category.code}_OTHER',
            name='Other Category',
            created_by=self.user
        )
        other_asset = Asset.objects.create(
            organization=self.org,
            asset_name='Other Depreciation Asset',
            asset_category=other_category,
            purchase_price=Decimal('500.00'),
            purchase_date=date.today(),
            useful_life=12,
            current_value=Decimal('500.00'),
            accumulated_depreciation=Decimal('0.00'),
            created_by=self.user
        )
        DepreciationRecord.objects.create(
            organization=self.org,
            asset=other_asset,
            period='2026-02',
            depreciation_amount=Decimal('50.00'),
            accumulated_amount=Decimal('50.00'),
            net_value=Decimal('450.00'),
            status='calculated',
            created_by=self.user
        )

        response = self.client.get('/api/system/objects/DepreciationRecord/report/', {
            'period': '2026-02',
            'categoryIds': [str(self.category.id)],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        data = response.data['data']
        self.assertEqual(data['summary']['total_records'], 1)
        self.assertEqual(len(data['category_breakdown']), 1)
        self.assertEqual(data['category_breakdown'][0]['category_code'], self.category.code)
        self.assertEqual(len(data['by_asset']), 1)
        self.assertEqual(data['by_asset'][0]['asset_code'], self.asset.asset_code)
        self.assertEqual(data['by_asset'][0]['category_name'], self.category.name)

    def test_batch_post_returns_partial_failure_summary(self):
        posted_record = DepreciationRecord.objects.create(
            organization=self.org,
            asset=self.asset,
            period='2026-03',
            depreciation_amount=Decimal('100.00'),
            accumulated_amount=Decimal('200.00'),
            net_value=Decimal('1800.00'),
            status='posted',
            post_date=date.today(),
            created_by=self.user
        )

        response = self.client.post(
            '/api/system/objects/DepreciationRecord/batch_post/',
            {'ids': [str(self.record.id), str(posted_record.id)]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['summary']['succeeded'], 1)
        self.assertEqual(response.data['summary']['failed'], 1)
        self.record.refresh_from_db()
        self.assertEqual(self.record.status, 'posted')

    def test_global_and_category_config_alias(self):
        get_global = self.client.get('/api/system/objects/DepreciationConfig/global/')
        self.assertEqual(get_global.status_code, status.HTTP_200_OK)
        self.assertTrue(get_global.data['success'])

        put_global = self.client.put(
            '/api/system/objects/DepreciationConfig/global/',
            {'defaultMethod': 'straight_line', 'defaultUsefulLife': 36, 'defaultResidualRate': 4},
            format='json'
        )
        self.assertEqual(put_global.status_code, status.HTTP_200_OK)
        self.assertTrue(put_global.data['success'])

        get_category = self.client.get(f'/api/system/objects/DepreciationConfig/categories/{self.category.id}/')
        self.assertEqual(get_category.status_code, status.HTTP_200_OK)
        self.assertTrue(get_category.data['success'])

        put_category = self.client.put(
            f'/api/system/objects/DepreciationConfig/categories/{self.category.id}/',
            {'depreciationMethod': 'straight_line', 'usefulLife': 72, 'residualRate': 8},
            format='json'
        )
        self.assertEqual(put_category.status_code, status.HTTP_200_OK)
        self.assertTrue(put_category.data['success'])

    def test_object_router_depreciation_actions(self):
        submit_response = self.client.post(f'/api/system/objects/DepreciationRecord/{self.record.id}/submit/')
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        self.assertTrue(submit_response.data['success'])

        get_global = self.client.get('/api/system/objects/DepreciationConfig/global/')
        self.assertEqual(get_global.status_code, status.HTTP_200_OK)
        self.assertTrue(get_global.data['success'])

        get_category = self.client.get(f'/api/system/objects/DepreciationConfig/categories/{self.category.id}/')
        self.assertEqual(get_category.status_code, status.HTTP_200_OK)
        self.assertTrue(get_category.data['success'])

        detail_response = self.client.get(f'/api/system/objects/DepreciationRecord/assets/{self.asset.id}/detail/')
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertTrue(detail_response.data['success'])

        export_response = self.client.get('/api/system/objects/DepreciationRecord/report/export/?period=2026-02&fileFormat=csv')
        self.assertEqual(export_response.status_code, status.HTTP_200_OK)
        self.assertIn('text/csv', export_response['Content-Type'])

    def test_detail_action_uses_current_request_org_scope(self):
        first_submit = self.client.post(f'/api/system/objects/DepreciationRecord/{self.record.id}/submit/')
        self.assertEqual(first_submit.status_code, status.HTTP_200_OK)
        self.assertTrue(first_submit.data['success'])

        suffix = uuid.uuid4().hex[:8]
        org2 = Organization.objects.create(
            name=f'Dep Org Scope {suffix}',
            code=f'DEP_SCOPE_{suffix}'
        )
        user2 = User.objects.create_user(
            username=f'dep_scope_{suffix}',
            password='pass123456',
            organization=org2
        )
        UserOrganization.objects.create(
            user=user2,
            organization=org2,
            role='admin',
            is_active=True,
            is_primary=True
        )
        user2.current_organization = org2
        user2.save(update_fields=['current_organization'])

        category2 = AssetCategory.objects.create(
            organization=org2,
            code=f'DEP_SCOPE_CAT_{suffix}',
            name='Dep Scope Category',
            created_by=user2
        )
        asset2 = Asset.objects.create(
            organization=org2,
            asset_name='Depreciation Scope Asset',
            asset_category=category2,
            purchase_price=Decimal('1800.00'),
            purchase_date=date.today(),
            useful_life=18,
            current_value=Decimal('1800.00'),
            accumulated_depreciation=Decimal('0.00'),
            created_by=user2
        )
        record2 = DepreciationRecord.objects.create(
            organization=org2,
            asset=asset2,
            period='2026-03',
            depreciation_amount=Decimal('100.00'),
            accumulated_amount=Decimal('100.00'),
            net_value=Decimal('1700.00'),
            status='calculated',
            created_by=user2
        )

        client2 = APIClient()
        client2.force_authenticate(user=user2)
        client2.credentials(HTTP_X_ORGANIZATION_ID=str(org2.id))

        second_submit = client2.post(f'/api/system/objects/DepreciationRecord/{record2.id}/submit/')
        self.assertEqual(second_submit.status_code, status.HTTP_200_OK)
        self.assertTrue(second_submit.data['success'])

    def test_calculate_accepts_category_ids_payload(self):
        other_category = AssetCategory.objects.create(
            organization=self.org,
            code=f'{self.category.code}_CALC',
            name='Calculation Category',
            created_by=self.user
        )
        other_asset = Asset.objects.create(
            organization=self.org,
            asset_name='Filtered Out Asset',
            asset_category=other_category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            useful_life=24,
            current_value=Decimal('1000.00'),
            accumulated_depreciation=Decimal('0.00'),
            created_by=self.user
        )
        DepreciationConfig.objects.create(
            organization=self.org,
            category=other_category,
            depreciation_method='straight_line',
            useful_life=60,
            salvage_value_rate=Decimal('5.00'),
            is_active=True,
            created_by=self.user
        )

        response = self.client.post(
            '/api/system/objects/DepreciationRun/calculate/',
            {'period': '2026-04', 'categoryIds': [str(self.category.id)]},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertTrue(
            DepreciationRecord.objects.filter(
                organization=self.org,
                asset=self.asset,
                period='2026-04',
            ).exists()
        )
        self.assertFalse(
            DepreciationRecord.objects.filter(
                organization=self.org,
                asset=other_asset,
                period='2026-04',
            ).exists()
        )
