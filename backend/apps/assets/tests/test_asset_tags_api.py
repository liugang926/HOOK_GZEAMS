from datetime import date
from decimal import Decimal
import uuid

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User, UserOrganization
from apps.assets.models import Asset, AssetCategory, AssetTag, AssetTagRelation, TagGroup
from apps.common.middleware import clear_current_organization
from apps.organizations.models import Department, Organization


class AssetTagApiTest(APITestCase):
    """API tests for the Phase 7.3 asset tag system."""

    def setUp(self):
        self.client = APIClient()
        suffix = uuid.uuid4().hex[:8]

        self.org = Organization.objects.create(
            name=f'Asset Tag Org {suffix}',
            code=f'ASSET_TAG_ORG_{suffix}',
        )
        self.user = User.objects.create_user(
            username=f'asset_tag_user_{suffix}',
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

        self.department = Department.objects.create(
            organization=self.org,
            code=f'DEPT_{suffix}',
            name='Asset Tag Department',
        )
        self.location = self._create_location(suffix)
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code=f'CAT_{suffix}',
            name='Asset Tag Category',
            created_by=self.user,
        )
        self.asset_one = self._create_asset('Asset One')
        self.asset_two = self._create_asset('Asset Two')
        self.asset_three = self._create_asset('Asset Three')

    def tearDown(self):
        clear_current_organization()
        super().tearDown()

    def _create_location(self, suffix: str):
        from apps.assets.models import Location

        return Location.objects.create(
            organization=self.org,
            name=f'Warehouse {suffix}',
            location_type='warehouse',
        )

    def _create_asset(self, name: str):
        return Asset.objects.create(
            organization=self.org,
            asset_name=name,
            asset_category=self.category,
            purchase_price=Decimal('1000.00'),
            purchase_date=date.today(),
            asset_status='idle',
            department=self.department,
            location=self.location,
            created_by=self.user,
        )

    def _create_group(self, **overrides):
        defaults = {
            'organization': self.org,
            'name': 'Usage Status',
            'code': f'usage_status_{uuid.uuid4().hex[:6]}',
            'color': '#409EFF',
            'created_by': self.user,
        }
        defaults.update(overrides)
        return TagGroup.objects.create(**defaults)

    def _create_tag(self, group: TagGroup, **overrides):
        defaults = {
            'organization': self.org,
            'tag_group': group,
            'name': f'Tag {uuid.uuid4().hex[:4]}',
            'code': f'tag_{uuid.uuid4().hex[:6]}',
            'color': '',
            'created_by': self.user,
        }
        defaults.update(overrides)
        return AssetTag.objects.create(**defaults)

    def test_tag_group_and_tag_crud_alias_endpoints(self):
        """Create, update, list, and soft delete groups and tags via alias routes."""
        create_group_response = self.client.post(
            '/api/objects/tags/groups/',
            {
                'name': 'Importance',
                'code': 'importance',
                'description': 'Asset importance tags',
                'color': '#E6A23C',
                'icon': 'Flag',
                'sortOrder': 10,
            },
            format='json',
        )
        self.assertEqual(create_group_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_group_response.data['success'])

        group_id = str(create_group_response.data['data']['id'])
        group = TagGroup.all_objects.get(id=group_id)
        self.assertEqual(group.organization_id, self.org.id)

        create_tag_response = self.client.post(
            '/api/objects/tags/',
            {
                'tagGroup': group_id,
                'name': 'Critical',
                'code': 'critical',
                'icon': 'WarningFilled',
                'sortOrder': 5,
            },
            format='json',
        )
        self.assertEqual(create_tag_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_tag_response.data['success'])
        self.assertEqual(create_tag_response.data['data']['tagGroup'], group_id)
        self.assertEqual(create_tag_response.data['data']['color'], '')

        tag_id = str(create_tag_response.data['data']['id'])

        list_groups_response = self.client.get('/api/objects/tags/groups/')
        self.assertEqual(list_groups_response.status_code, status.HTTP_200_OK)
        group_payload = list_groups_response.data['data']['results'][0]
        self.assertEqual(group_payload['tagsCount'], 1)
        self.assertEqual(group_payload['tags'][0]['id'], tag_id)
        self.assertEqual(group_payload['tags'][0]['groupColor'], '#E6A23C')

        update_tag_response = self.client.patch(
            f'/api/objects/tags/{tag_id}/',
            {
                'color': '#F56C6C',
                'description': 'Critical assets only',
            },
            format='json',
        )
        self.assertEqual(update_tag_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_tag_response.data['data']['color'], '#F56C6C')

        delete_tag_response = self.client.delete(f'/api/objects/tags/{tag_id}/')
        self.assertEqual(delete_tag_response.status_code, status.HTTP_200_OK)
        self.assertTrue(delete_tag_response.data['success'])
        self.assertTrue(AssetTag.all_objects.get(id=tag_id).is_deleted)

        delete_group_response = self.client.delete(f'/api/objects/tags/groups/{group_id}/')
        self.assertEqual(delete_group_response.status_code, status.HTTP_200_OK)
        self.assertTrue(delete_group_response.data['success'])
        self.assertTrue(TagGroup.all_objects.get(id=group_id).is_deleted)

    def test_system_tag_group_delete_is_blocked(self):
        """Prevent deletion of system-managed tag groups."""
        group = self._create_group(
            name='System Group',
            code='system_group',
            is_system=True,
        )

        response = self.client.delete(f'/api/objects/tags/groups/{group.id}/')
        group.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(group.is_deleted)
        self.assertEqual(response.data['error']['code'], 'PERMISSION_DENIED')

    def test_asset_tag_assignment_statistics_and_filtering(self):
        """Assign tags to assets and filter with OR and AND logic."""
        group = self._create_group(name='Usage Status', code='usage_status')
        in_use_tag = self._create_tag(group, name='In Use', code='in_use')
        idle_tag = self._create_tag(group, name='Idle', code='idle')

        add_asset_one_response = self.client.post(
            f'/api/objects/assets/{self.asset_one.id}/tags/',
            {
                'tagIds': [str(in_use_tag.id), str(idle_tag.id)],
                'notes': 'Applied in test',
            },
            format='json',
        )
        self.assertEqual(add_asset_one_response.status_code, status.HTTP_200_OK)
        self.assertEqual(add_asset_one_response.data['data']['addedCount'], 2)

        add_asset_two_response = self.client.post(
            f'/api/objects/assets/{self.asset_two.id}/tags/',
            {
                'tagIds': [str(idle_tag.id)],
            },
            format='json',
        )
        self.assertEqual(add_asset_two_response.status_code, status.HTTP_200_OK)

        get_asset_tags_response = self.client.get(f'/api/objects/assets/{self.asset_one.id}/tags/')
        self.assertEqual(get_asset_tags_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(get_asset_tags_response.data['data']['tags']), 2)

        statistics_response = self.client.get('/api/objects/tags/statistics/')
        self.assertEqual(statistics_response.status_code, status.HTTP_200_OK)
        self.assertEqual(statistics_response.data['data']['totalTags'], 2)
        self.assertEqual(statistics_response.data['data']['totalTaggedAssets'], 2)

        statistics_by_code = {
            item['code']: item for item in statistics_response.data['data']['tagStatistics']
        }
        self.assertEqual(statistics_by_code['in_use']['assetCount'], 1)
        self.assertEqual(statistics_by_code['idle']['assetCount'], 2)

        or_filter_response = self.client.get(
            f'/api/assets/?tagIds={in_use_tag.id},{idle_tag.id}&tagLogic=or'
        )
        self.assertEqual(or_filter_response.status_code, status.HTTP_200_OK)
        self.assertEqual(or_filter_response.data['data']['count'], 2)

        and_filter_response = self.client.get(
            f'/api/assets/?tagIds={in_use_tag.id},{idle_tag.id}&tagLogic=and'
        )
        self.assertEqual(and_filter_response.status_code, status.HTTP_200_OK)
        self.assertEqual(and_filter_response.data['data']['count'], 1)
        self.assertEqual(
            str(and_filter_response.data['data']['results'][0]['id']),
            str(self.asset_one.id),
        )

        by_tags_response = self.client.post(
            '/api/objects/assets/by-tags/',
            {
                'tagIds': [str(in_use_tag.id), str(idle_tag.id)],
                'matchType': 'and',
            },
            format='json',
        )
        self.assertEqual(by_tags_response.status_code, status.HTTP_200_OK)
        self.assertEqual(by_tags_response.data['data']['count'], 1)
        self.assertEqual(
            str(by_tags_response.data['data']['results'][0]['id']),
            str(self.asset_one.id),
        )

        remove_tag_response = self.client.delete(
            f'/api/objects/assets/{self.asset_one.id}/tags/{idle_tag.id}/'
        )
        self.assertEqual(remove_tag_response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            AssetTagRelation.objects.filter(
                asset=self.asset_one,
                tag=idle_tag,
                is_deleted=False,
            ).exists()
        )

    def test_batch_add_and_batch_remove_tags(self):
        """Batch endpoints should return the standard summary/results contract."""
        group = self._create_group(name='Source', code='source')
        purchase_tag = self._create_tag(group, name='Purchase', code='purchase')
        donated_tag = self._create_tag(group, name='Donated', code='donated')

        batch_add_response = self.client.post(
            '/api/objects/tags/batch-add/',
            {
                'assetIds': [str(self.asset_one.id), str(self.asset_two.id)],
                'tagIds': [str(purchase_tag.id), str(donated_tag.id)],
                'notes': 'Batch add in test',
            },
            format='json',
        )
        self.assertEqual(batch_add_response.status_code, status.HTTP_200_OK)
        self.assertTrue(batch_add_response.data['success'])
        self.assertEqual(batch_add_response.data['summary']['total'], 2)
        self.assertEqual(batch_add_response.data['summary']['succeeded'], 2)
        self.assertEqual(batch_add_response.data['summary']['failed'], 0)
        self.assertEqual(batch_add_response.data['summary']['relationsCreated'], 4)
        self.assertEqual(len(batch_add_response.data['results']), 2)
        self.assertEqual(
            AssetTagRelation.objects.filter(
                asset_id__in=[self.asset_one.id, self.asset_two.id],
                tag_id__in=[purchase_tag.id, donated_tag.id],
                is_deleted=False,
            ).count(),
            4,
        )

        batch_remove_response = self.client.post(
            '/api/objects/tags/batch-remove/',
            {
                'assetIds': [str(self.asset_two.id)],
                'tagIds': [str(donated_tag.id)],
            },
            format='json',
        )
        self.assertEqual(batch_remove_response.status_code, status.HTTP_200_OK)
        self.assertTrue(batch_remove_response.data['success'])
        self.assertEqual(batch_remove_response.data['summary']['total'], 1)
        self.assertEqual(batch_remove_response.data['summary']['succeeded'], 1)
        self.assertEqual(batch_remove_response.data['summary']['failed'], 0)
        self.assertEqual(batch_remove_response.data['summary']['relationsRemoved'], 1)
        self.assertEqual(
            AssetTagRelation.objects.filter(
                asset=self.asset_two,
                tag=donated_tag,
                is_deleted=False,
            ).count(),
            0,
        )
