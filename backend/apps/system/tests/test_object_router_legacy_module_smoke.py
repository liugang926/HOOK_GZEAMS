import uuid

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.models import User, UserOrganization
from apps.organizations.models import Organization
from apps.system.services.object_registry import ObjectRegistry


class LegacyModuleObjectRouterSmokeTest(APITestCase):
    def setUp(self):
        # Ensure hardcoded object metadata exists for router smoke checks.
        ObjectRegistry.auto_register_standard_objects()

        self.client = APIClient()
        suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Router Smoke Org {suffix}',
            code=f'ROUTER_SMOKE_{suffix}',
        )
        self.user = User.objects.create_user(
            username=f'router_smoke_{suffix}',
            password='pass123456',
            organization=self.org,
        )
        UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            role='admin',
            is_active=True,
            is_primary=True,
        )
        self.user.current_organization = self.org
        self.user.save(update_fields=['current_organization'])
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def tearDown(self):
        from apps.common.middleware import clear_current_organization
        clear_current_organization()
        super().tearDown()

    def test_list_endpoints_for_migrated_modules(self):
        for code in [
            'FinanceVoucher',
            'DepreciationRecord',
            'ITAsset',
            'ITMaintenanceRecord',
            'ConfigurationChange',
            'Software',
            'SoftwareLicense',
            'LicenseAllocation',
            'ITSoftware',
            'ITSoftwareLicense',
            'ITLicenseAllocation',
            'LeasingContract',
            'LeaseItem',
            'RentPayment',
            'LeaseReturn',
            'LeaseExtension',
            'InsuranceCompany',
            'InsurancePolicy',
            'InsuredAsset',
            'PremiumPayment',
            'ClaimRecord',
            'PolicyRenewal',
        ]:
            response = self.client.get(f'/api/system/objects/{code}/')
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f'Expected 200 for object code {code}, got {response.status_code}',
            )
            self.assertTrue(response.data.get('success', False))

    def test_collection_custom_actions_for_migrated_modules(self):
        compliance = self.client.get('/api/system/objects/SoftwareLicense/compliance_report/')
        self.assertEqual(compliance.status_code, status.HTTP_200_OK)
        self.assertTrue(compliance.data.get('success', False))

        global_config = self.client.get('/api/system/objects/DepreciationConfig/global/')
        self.assertEqual(global_config.status_code, status.HTTP_200_OK)
        self.assertTrue(global_config.data.get('success', False))

    def test_metadata_endpoint_for_hardcoded_asset_object(self):
        """
        Regression: metadata endpoint must not crash when generating list layout
        from ModelFieldDefinition records that lack column_width/fixed attributes.
        """
        response = self.client.get('/api/system/objects/Asset/metadata/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success', False))
        self.assertEqual(response.data.get('data', {}).get('code'), 'Asset')

    def test_legacy_routes_removed(self):
        legacy_urls = [
            '/api/finance/vouchers/',
            '/api/depreciation/records/',
            '/api/it-assets/it-assets/',
            '/api/software-licenses/software/',
            '/api/leasing/lease-contracts/',
            '/api/insurance/policies/',
        ]
        for url in legacy_urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_404_NOT_FOUND,
                msg=f'Expected 404 for removed legacy route: {url}',
            )
