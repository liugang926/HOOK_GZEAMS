import uuid
from datetime import date

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.models import User, UserOrganization
from apps.assets.models import Asset, AssetCategory
from apps.it_assets.models import (
    Software as ITSoftware,
    SoftwareLicense as ITSoftwareLicense,
    LicenseAllocation as ITLicenseAllocation,
)
from apps.organizations.models import Organization
from apps.software_licenses.models import (
    Software as CatalogSoftware,
    SoftwareLicense as CatalogSoftwareLicense,
    LicenseAllocation as CatalogLicenseAllocation,
)


class ObjectRouterDetailActionTenantScopeTest(APITestCase):
    def _create_user_context(self, suffix_prefix: str):
        suffix = uuid.uuid4().hex[:8]
        org = Organization.objects.create(
            name=f'{suffix_prefix} Org {suffix}',
            code=f'{suffix_prefix.upper()}_{suffix}',
        )
        user = User.objects.create_user(
            username=f'{suffix_prefix}_user_{suffix}',
            password='pass123456',
            organization=org,
        )
        UserOrganization.objects.create(
            user=user,
            organization=org,
            role='admin',
            is_active=True,
            is_primary=True,
        )
        user.current_organization = org
        user.save(update_fields=['current_organization'])
        client = APIClient()
        client.force_authenticate(user=user)
        client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
        return org, user, client

    def _create_asset(self, org, user, code_prefix: str):
        category = AssetCategory.objects.create(
            organization=org,
            code=f'{code_prefix}_CAT_{uuid.uuid4().hex[:6]}',
            name=f'{code_prefix} Category',
            created_by=user,
        )
        return Asset.objects.create(
            organization=org,
            asset_name=f'{code_prefix} Asset',
            asset_category=category,
            purchase_price=1000,
            purchase_date=date.today(),
            created_by=user,
        )

    def test_catalog_license_deallocate_detail_action_respects_request_org(self):
        org1, user1, client1 = self._create_user_context('sw_scope_a')
        asset1 = self._create_asset(org1, user1, 'SWA')
        software1 = CatalogSoftware.objects.create(
            organization=org1,
            code=f'SW-A-{uuid.uuid4().hex[:8]}',
            name='Software A',
            created_by=user1,
        )
        license1 = CatalogSoftwareLicense.objects.create(
            organization=org1,
            license_no=f'LIC-A-{uuid.uuid4().hex[:8]}',
            software=software1,
            total_units=5,
            purchase_date=date.today(),
            created_by=user1,
        )
        alloc1 = CatalogLicenseAllocation.objects.create(
            organization=org1,
            license=license1,
            asset=asset1,
            allocated_date=date.today(),
            allocated_by=user1,
            created_by=user1,
        )
        resp1 = client1.post(f'/api/system/objects/LicenseAllocation/{alloc1.id}/deallocate/', format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertTrue(resp1.data.get('success', False))

        org2, user2, client2 = self._create_user_context('sw_scope_b')
        asset2 = self._create_asset(org2, user2, 'SWB')
        software2 = CatalogSoftware.objects.create(
            organization=org2,
            code=f'SW-B-{uuid.uuid4().hex[:8]}',
            name='Software B',
            created_by=user2,
        )
        license2 = CatalogSoftwareLicense.objects.create(
            organization=org2,
            license_no=f'LIC-B-{uuid.uuid4().hex[:8]}',
            software=software2,
            total_units=5,
            purchase_date=date.today(),
            created_by=user2,
        )
        alloc2 = CatalogLicenseAllocation.objects.create(
            organization=org2,
            license=license2,
            asset=asset2,
            allocated_date=date.today(),
            allocated_by=user2,
            created_by=user2,
        )
        resp2 = client2.post(f'/api/system/objects/LicenseAllocation/{alloc2.id}/deallocate/', format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data.get('success', False))

    def test_it_license_deallocate_detail_action_respects_request_org(self):
        org1, user1, client1 = self._create_user_context('it_scope_a')
        asset1 = self._create_asset(org1, user1, 'ITA')
        software1 = ITSoftware.objects.create(
            organization=org1,
            name='IT Software A',
            created_by=user1,
        )
        license1 = ITSoftwareLicense.objects.create(
            organization=org1,
            software=software1,
            license_key=f'IT-LIC-A-{uuid.uuid4().hex[:8]}',
            seats=5,
            created_by=user1,
        )
        alloc1 = ITLicenseAllocation.objects.create(
            organization=org1,
            license=license1,
            asset=asset1,
            allocated_date=date.today(),
            allocated_by=user1,
            created_by=user1,
        )
        resp1 = client1.post(f'/api/system/objects/ITLicenseAllocation/{alloc1.id}/deallocate/', format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.assertTrue(resp1.data.get('success', False))

        org2, user2, client2 = self._create_user_context('it_scope_b')
        asset2 = self._create_asset(org2, user2, 'ITB')
        software2 = ITSoftware.objects.create(
            organization=org2,
            name='IT Software B',
            created_by=user2,
        )
        license2 = ITSoftwareLicense.objects.create(
            organization=org2,
            software=software2,
            license_key=f'IT-LIC-B-{uuid.uuid4().hex[:8]}',
            seats=5,
            created_by=user2,
        )
        alloc2 = ITLicenseAllocation.objects.create(
            organization=org2,
            license=license2,
            asset=asset2,
            allocated_date=date.today(),
            allocated_by=user2,
            created_by=user2,
        )
        resp2 = client2.post(f'/api/system/objects/ITLicenseAllocation/{alloc2.id}/deallocate/', format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        self.assertTrue(resp2.data.get('success', False))
