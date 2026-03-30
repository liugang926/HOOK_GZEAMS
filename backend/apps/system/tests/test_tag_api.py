"""
API tests for Phase 7.3 asset tag management.
"""
from decimal import Decimal
import uuid

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Department, Organization
from apps.system.models import BusinessObject, Tag, TagAssignment


class TagAPITest(APITestCase):
    """End-to-end tests for tag CRUD, assignment, and filtering."""

    def setUp(self):
        """Create an isolated organization, user, and assets."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Tag Org {self.unique_suffix}',
            code=f'TAG_ORG_{self.unique_suffix}',
        )
        self.user = User.objects.create_user(
            username=f'tag_user_{self.unique_suffix}',
            email=f'tag_{self.unique_suffix}@example.com',
            password='testpass123',
            organization=self.org,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

        BusinessObject.all_objects.update_or_create(
            code='Asset',
            defaults={
                'name': '资产',
                'name_en': 'Asset',
                'description': 'Asset object for tag testing',
                'is_hardcoded': True,
                'django_model_path': 'apps.assets.models.Asset',
                'allow_standalone_query': True,
                'allow_standalone_route': True,
            },
        )

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'CAT_{self.unique_suffix}',
            name='Tag Test Category',
            created_by=self.user,
        )
        self.department = Department.objects.create(
            organization=self.org,
            name='Tag Test Department',
            code=f'DEPT_{self.unique_suffix}',
        )
        self.asset_one = Asset.objects.create(
            organization=self.org,
            asset_name='Tagged Laptop',
            asset_category=self.category,
            department=self.department,
            purchase_price=Decimal('1000.00'),
            purchase_date='2024-01-01',
            created_by=self.user,
        )
        self.asset_two = Asset.objects.create(
            organization=self.org,
            asset_name='Tagged Monitor',
            asset_category=self.category,
            department=self.department,
            purchase_price=Decimal('500.00'),
            purchase_date='2024-01-02',
            created_by=self.user,
        )

    def test_create_tag(self):
        """Create a tag through the system tag API."""
        response = self.client.post(
            '/api/system/tags/',
            {
                'name': 'Critical',
                'color': '#F56C6C',
                'description': 'Critical asset tag',
                'bizType': 'Asset',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            Tag.all_objects.filter(organization=self.org, is_deleted=False).count(),
            1,
        )
        self.assertEqual(
            Tag.all_objects.get(organization=self.org, is_deleted=False).biz_type,
            'Asset',
        )

    def test_apply_and_remove_tags_updates_usage_count(self):
        """Apply and remove a tag from multiple assets."""
        tag = Tag.objects.create(
            organization=self.org,
            name='Portable',
            color='#409EFF',
            biz_type='Asset',
            created_by=self.user,
        )

        apply_response = self.client.post(
            '/api/system/tags/apply/',
            {
                'tagIds': [str(tag.id)],
                'objectIds': [str(self.asset_one.id), str(self.asset_two.id)],
                'bizType': 'Asset',
            },
            format='json',
        )
        self.assertEqual(apply_response.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.usage_count, 2)
        self.assertEqual(
            TagAssignment.all_objects.filter(
                organization=self.org,
                tag=tag,
                is_deleted=False,
            ).count(),
            2,
        )

        remove_response = self.client.post(
            '/api/system/tags/remove/',
            {
                'tagIds': [str(tag.id)],
                'objectIds': [str(self.asset_two.id)],
                'bizType': 'Asset',
            },
            format='json',
        )
        self.assertEqual(remove_response.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()
        self.assertEqual(tag.usage_count, 1)
        self.assertEqual(
            TagAssignment.all_objects.filter(
                organization=self.org,
                tag=tag,
                is_deleted=False,
            ).count(),
            1,
        )

    def test_asset_list_filters_by_tag_ids(self):
        """Filter the asset list with the new tagIds query parameter."""
        tag = Tag.objects.create(
            organization=self.org,
            name='Inventory',
            color='#67C23A',
            biz_type='Asset',
            created_by=self.user,
        )
        self.client.post(
            '/api/system/tags/apply/',
            {
                'tagIds': [str(tag.id)],
                'objectIds': [str(self.asset_one.id)],
                'bizType': 'Asset',
            },
            format='json',
        )

        response = self.client.get(f'/api/assets/?tagIds={tag.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(str(results[0]['id']), str(self.asset_one.id))

    def test_statistics_endpoint_returns_summary(self):
        """Return the aggregate statistics payload for tag dashboards."""
        tag = Tag.objects.create(
            organization=self.org,
            name='Finance',
            color='#E6A23C',
            biz_type='Asset',
            created_by=self.user,
        )
        self.client.post(
            '/api/system/tags/apply/',
            {
                'tagIds': [str(tag.id)],
                'objectIds': [str(self.asset_one.id)],
                'bizType': 'Asset',
            },
            format='json',
        )

        response = self.client.get('/api/system/tags/statistics/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['total'], 1)
        self.assertEqual(response.data['data']['used'], 1)
