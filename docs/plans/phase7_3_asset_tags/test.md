# Phase 7.3: 资产标签系统 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，确保标签组管理、标签分配、批量操作、自动规则功能的可靠性。

---

## 单元测试

### 后端模型测试

```python
# apps/tags/tests/test_models.py

from django.test import TestCase
from apps.tags.models import TagGroup, AssetTag, AssetTagRelation, TagAutoRule
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization
from django.utils import timezone


class TagGroupModelTest(TestCase):
    """TagGroup模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_tag_group_creation(self):
        """测试标签组创建"""
        group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            description='资产当前使用状态',
            color='#409eff',
            icon='status',
            sort_order=1,
            is_system=True,
            is_active=True,
            created_by=self.user,
        )

        self.assertEqual(group.name, '使用状态')
        self.assertEqual(group.code, 'usage_status')
        self.assertEqual(group.color, '#409eff')
        self.assertTrue(group.is_system)
        self.assertTrue(group.is_active)

    def test_tag_group_soft_delete(self):
        """测试标签组软删除"""
        group = TagGroup.objects.create(
            organization=self.org,
            name='测试组',
            code='test_group',
            created_by=self.user,
        )

        # 软删除
        group.soft_delete()

        self.assertTrue(group.is_deleted)
        self.assertIsNotNone(group.deleted_at)

        # 正常查询无法获取
        active_groups = TagGroup.objects.filter(code='test_group')
        self.assertEqual(active_groups.count(), 0)

    def test_tag_group_ordering(self):
        """测试标签组排序"""
        group1 = TagGroup.objects.create(
            organization=self.org,
            name='第一组',
            code='group1',
            sort_order=2,
            created_by=self.user,
        )

        group2 = TagGroup.objects.create(
            organization=self.org,
            name='第二组',
            code='group2',
            sort_order=1,
            created_by=self.user,
        )

        groups = list(TagGroup.objects.all())
        self.assertEqual(groups[0], group2)  # sort_order=1 在前
        self.assertEqual(groups[1], group1)

    def test_system_tag_group_cannot_delete(self):
        """测试系统标签组不能删除"""
        group = TagGroup.objects.create(
            organization=self.org,
            name='系统组',
            code='system_group',
            is_system=True,
            created_by=self.user,
        )

        # 系统标签组删除应被阻止
        with self.assertRaises(Exception) as ctx:
            group.delete()

        # 验证错误消息
        self.assertIn('系统标签组', str(ctx.exception))

    def test_organization_isolation(self):
        """测试组织隔离"""
        org2 = Organization.objects.create(code='TEST2', name='Test Org 2')

        group = TagGroup.objects.create(
            organization=self.org,
            name='测试组',
            code='test_group',
            created_by=self.user,
        )

        # 同组织可以查询
        groups = TagGroup.objects.filter(organization=self.org)
        self.assertEqual(groups.count(), 1)

        # 不同组织无法查询
        groups_org2 = TagGroup.objects.filter(organization=org2)
        self.assertEqual(groups_org2.count(), 0)


class AssetTagModelTest(TestCase):
    """AssetTag模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            color='#409eff',
            created_by=self.user,
        )

    def test_tag_creation(self):
        """测试标签创建"""
        tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            color='#409eff',
            description='资产正在使用中',
            sort_order=1,
            is_active=True,
            created_by=self.user,
        )

        self.assertEqual(tag.tag_group, self.group)
        self.assertEqual(tag.name, '在用')
        self.assertEqual(tag.code, 'in_use')

    def test_tag_group_unique_constraint(self):
        """测试同一标签组下标签编码唯一"""
        AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        # 重复创建应该失败
        with self.assertRaises(Exception):
            AssetTag.objects.create(
                organization=self.org,
                tag_group=self.group,
                name='在用2',
                code='in_use',  # 重复编码
                created_by=self.user,
            )

    def test_tag_soft_delete(self):
        """测试标签软删除"""
        tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        # 软删除
        tag.soft_delete()

        self.assertTrue(tag.is_deleted)
        self.assertIsNotNone(tag.deleted_at)

    def test_tag_ordering(self):
        """测试标签排序"""
        tag1 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='标签1',
            code='tag1',
            sort_order=2,
            created_by=self.user,
        )

        tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='标签2',
            code='tag2',
            sort_order=1,
            created_by=self.user,
        )

        tags = list(AssetTag.objects.filter(tag_group=self.group))
        self.assertEqual(tags[0], tag2)
        self.assertEqual(tags[1], tag1)


class AssetTagRelationModelTest(TestCase):
    """AssetTagRelation模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            created_by=self.user,
        )

        self.tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            created_by=self.user,
        )

    def test_add_tag_to_asset(self):
        """测试为资产添加标签"""
        relation = AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
            notes='日常使用',
        )

        self.assertEqual(relation.asset, self.asset)
        self.assertEqual(relation.tag, self.tag)
        self.assertEqual(relation.tagged_by, self.user)
        self.assertEqual(relation.notes, '日常使用')

    def test_unique_asset_tag_constraint(self):
        """测试资产标签唯一约束"""
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        # 重复添加应该失败
        with self.assertRaises(Exception):
            AssetTagRelation.objects.create(
                organization=self.org,
                asset=self.asset,
                tag=self.tag,
                tagged_by=self.user,
            )

    def test_remove_tag_from_asset(self):
        """测试从资产移除标签"""
        relation = AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        # 删除关联
        relation_id = relation.id
        relation.delete()

        # 验证删除
        exists = AssetTagRelation.objects.filter(id=relation_id).exists()
        self.assertFalse(exists)

    def test_get_asset_tags(self):
        """测试获取资产标签"""
        tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            color='#f56c6c',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=tag2,
            tagged_by=self.user,
            notes='核心设备',
        )

        # 获取资产标签
        relations = AssetTagRelation.objects.filter(asset=self.asset)
        self.assertEqual(relations.count(), 2)

    def test_get_tagged_assets(self):
        """测试获取打标签的资产"""
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=self.tag,
            tagged_by=self.user,
        )

        # 获取打标签的资产
        relations = AssetTagRelation.objects.filter(tag=self.tag)
        self.assertEqual(relations.count(), 2)


class TagAutoRuleModelTest(TestCase):
    """TagAutoRule模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='重要性',
            code='importance',
            created_by=self.user,
        )

        self.tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            created_by=self.user,
        )

    def test_condition_rule_creation(self):
        """测试条件规则创建"""
        rule = TagAutoRule.objects.create(
            organization=self.org,
            name='高值设备自动打标',
            rule_type='condition',
            tag=self.tag,
            condition={
                'field': 'purchase_price',
                'operator': 'gt',
                'value': 10000
            },
            is_active=True,
            created_by=self.user,
        )

        self.assertEqual(rule.rule_type, 'condition')
        self.assertEqual(rule.tag, self.tag)
        self.assertEqual(rule.condition['field'], 'purchase_price')

    def test_schedule_rule_creation(self):
        """测试定时规则创建"""
        rule = TagAutoRule.objects.create(
            organization=self.org,
            name='每月折旧标记',
            rule_type='schedule',
            tag=self.tag,
            schedule='0 0 1 * *',  # 每月1号
            is_active=True,
            created_by=self.user,
        )

        self.assertEqual(rule.rule_type, 'schedule')
        self.assertEqual(rule.schedule, '0 0 1 * *')

    def test_rule_execution_tracking(self):
        """测试规则执行跟踪"""
        rule = TagAutoRule.objects.create(
            organization=self.org,
            name='测试规则',
            rule_type='condition',
            tag=self.tag,
            condition={'field': 'status', 'operator': 'eq', 'value': 'active'},
            is_active=True,
            created_by=self.user,
        )

        # 执行前没有执行时间
        self.assertIsNone(rule.last_executed_at)

        # 更新执行时间
        rule.last_executed_at = timezone.now()
        rule.save()

        rule.refresh_from_db()
        self.assertIsNotNone(rule.last_executed_at)
```

### 后端服务测试

```python
# apps/tags/tests/test_services.py

from django.test import TestCase
from apps.tags.services import AssetTagService
from apps.tags.models import TagGroup, AssetTag, AssetTagRelation
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization


class AssetTagServiceTest(TestCase):
    """AssetTagService测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)
        self.service = AssetTagService()

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            created_by=self.user,
        )

        self.tag1 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        self.tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            color='#f56c6c',
            created_by=self.user,
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            purchase_price=15000,
            created_by=self.user,
        )

    def test_add_single_tag_to_asset(self):
        """测试为资产添加单个标签"""
        relations = self.service.add_tags_to_asset(
            asset=self.asset,
            tag_ids=[str(self.tag1.id)],
            user=self.user,
            notes='日常使用'
        )

        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0].tag, self.tag1)
        self.assertEqual(relations[0].notes, '日常使用')

    def test_add_multiple_tags_to_asset(self):
        """测试为资产添加多个标签"""
        relations = self.service.add_tags_to_asset(
            asset=self.asset,
            tag_ids=[str(self.tag1.id), str(self.tag2.id)],
            user=self.user,
            notes='批量打标签'
        )

        self.assertEqual(len(relations), 2)

    def test_add_existing_tag_skips(self):
        """测试添加已存在的标签跳过"""
        # 第一次添加
        self.service.add_tags_to_asset(
            asset=self.asset,
            tag_ids=[str(self.tag1.id)],
            user=self.user
        )

        # 第二次添加（应该跳过已存在的）
        relations = self.service.add_tags_to_asset(
            asset=self.asset,
            tag_ids=[str(self.tag1.id)],
            user=self.user
        )

        # 应该只有一个关联
        count = AssetTagRelation.objects.filter(asset=self.asset, tag=self.tag1).count()
        self.assertEqual(count, 1)

    def test_remove_tags_from_asset(self):
        """测试从资产移除标签"""
        # 添加标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag1,
            tagged_by=self.user
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag2,
            tagged_by=self.user
        )

        # 移除标签
        count = self.service.remove_tags_from_asset(
            asset=self.asset,
            tag_ids=[str(self.tag1.id)]
        )

        self.assertEqual(count, 1)

        # 验证移除
        remaining = AssetTagRelation.objects.filter(asset=self.asset).count()
        self.assertEqual(remaining, 1)

    def test_get_assets_by_tags_and(self):
        """测试按标签查询资产（AND关系）"""
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        # asset1 有两个标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag1,
            tagged_by=self.user
        )
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag2,
            tagged_by=self.user
        )

        # asset2 只有一个标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=self.tag1,
            tagged_by=self.user
        )

        # 查询同时拥有两个标签的资产
        assets = self.service.get_assets_by_tags(
            tag_ids=[str(self.tag1.id), str(self.tag2.id)],
            organization=self.org
        )

        self.assertEqual(assets.count(), 1)
        self.assertEqual(assets.first(), self.asset)

    def test_get_tag_statistics(self):
        """测试获取标签统计"""
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        # 为多个资产打标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag1,
            tagged_by=self.user
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=self.tag1,
            tagged_by=self.user
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag2,
            tagged_by=self.user
        )

        # 获取统计
        stats = self.service.get_tag_statistics(organization=self.org)

        # tag1 有2个资产
        tag1_stat = stats.get(tag_id=str(self.tag1.id))
        self.assertIsNotNone(tag1_stat)
        self.assertEqual(tag1_stat['asset_count'], 2)

        # tag2 有1个资产
        tag2_stat = stats.get(tag_id=str(self.tag2.id))
        self.assertIsNotNone(tag2_stat)
        self.assertEqual(tag2_stat['asset_count'], 1)
```

---

## API集成测试

```python
# apps/tags/tests/test_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.tags.models import TagGroup, AssetTag, AssetTagRelation
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization


class TagGroupAPITest(TestCase):
    """标签组API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_create_tag_group(self):
        """测试创建标签组"""
        response = self.client.post(
            '/api/tags/groups/',
            {
                'name': '特殊管理',
                'code': 'special_management',
                'description': '需要特殊管理的资产',
                'color': '#f56c6c',
                'icon': 'warning',
                'sort_order': 10
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], '特殊管理')

    def test_get_tag_groups(self):
        """测试获取标签组列表"""
        TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            color='#409eff',
            created_by=self.user,
        )

        response = self.client.get('/api/tags/groups/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_update_tag_group(self):
        """测试更新标签组"""
        group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            color='#409eff',
            created_by=self.user,
        )

        response = self.client.put(
            f'/api/tags/groups/{group.id}/',
            {
                'name': '使用状态（更新）',
                'description': '资产当前使用状态描述',
                'color': '#409eff',
                'sort_order': 1
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['name'], '使用状态（更新）')

    def test_delete_system_tag_group_fails(self):
        """测试删除系统标签组失败"""
        group = TagGroup.objects.create(
            organization=self.org,
            name='系统组',
            code='system_group',
            is_system=True,
            created_by=self.user,
        )

        response = self.client.delete(f'/api/tags/groups/{group.id}/')

        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error']['code'], 'SYSTEM_TAG_GROUP_CANNOT_DELETE')


class AssetTagAPITest(TestCase):
    """标签API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            color='#409eff',
            created_by=self.user,
        )

    def test_create_tag(self):
        """测试创建标签"""
        response = self.client.post(
            '/api/tags/',
            {
                'tag_group': str(self.group.id),
                'name': '在用',
                'code': 'in_use',
                'color': '#409eff',
                'description': '资产正在使用中'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], '在用')

    def test_get_tags(self):
        """测试获取标签列表"""
        AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        response = self.client.get('/api/tags/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data['data'])

    def test_get_tag_statistics(self):
        """测试获取标签统计"""
        tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset,
            tag=tag,
            tagged_by=self.user,
        )

        response = self.client.get('/api/tags/statistics/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('tag_statistics', data['data'])


class AssetTagRelationAPITest(TestCase):
    """资产标签关联API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.group = TagGroup.objects.create(
            organization=self.org,
            name='使用状态',
            code='usage_status',
            created_by=self.user,
        )

        self.tag = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='在用',
            code='in_use',
            created_by=self.user,
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            created_by=self.user,
        )

    def test_get_asset_tags(self):
        """测试获取资产标签"""
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        response = self.client.get(f'/api/assets/{self.asset.id}/tags/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']['tags']), 1)

    def test_add_tag_to_asset(self):
        """测试为资产添加标签"""
        response = self.client.post(
            f'/api/assets/{self.asset.id}/tags/',
            {
                'tag_ids': [str(self.tag.id)],
                'notes': '日常使用'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['added_count'], 1)

    def test_remove_tag_from_asset(self):
        """测试从资产移除标签"""
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        response = self.client.delete(f'/api/assets/{self.asset.id}/tags/{self.tag.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_batch_add_tags(self):
        """测试批量添加标签"""
        tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            color='#f56c6c',
            created_by=self.user,
        )

        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        response = self.client.post(
            '/api/tags/batch-add/',
            {
                'asset_ids': [str(self.asset.id), str(asset2.id)],
                'tag_ids': [str(self.tag.id), str(tag2.id)],
                'notes': '批量打标签'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['relations_created'], 4)

    def test_batch_remove_tags(self):
        """测试批量移除标签"""
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        # 为两个资产添加同一标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=self.tag,
            tagged_by=self.user,
        )

        response = self.client.post(
            '/api/tags/batch-remove/',
            {
                'asset_ids': [str(self.asset.id), str(asset2.id)],
                'tag_ids': [str(self.tag.id)]
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['summary']['relations_removed'], 2)

    def test_search_assets_by_tags_and(self):
        """测试按标签查询资产（AND）"""
        tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            color='#f56c6c',
            created_by=self.user,
        )

        # 资产1有两个标签
        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=tag2,
            tagged_by=self.user,
        )

        # 资产2只有一个标签
        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=self.tag,
            tagged_by=self.user,
        )

        # 查询同时拥有两个标签的资产
        response = self.client.post(
            '/api/assets/by-tags/',
            {
                'tag_ids': [str(self.tag.id), str(tag2.id)],
                'match_type': 'and'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['count'], 1)
        self.assertEqual(data['data']['results'][0]['id'], str(self.asset.id))

    def test_search_assets_by_tags_or(self):
        """测试按标签查询资产（OR）"""
        tag2 = AssetTag.objects.create(
            organization=self.org,
            tag_group=self.group,
            name='关键',
            code='critical',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=self.asset,
            tag=self.tag,
            tagged_by=self.user,
        )

        asset2 = Asset.objects.create(
            organization=self.org,
            asset_code='ZC002',
            asset_name='iPad',
            created_by=self.user,
        )

        AssetTagRelation.objects.create(
            organization=self.org,
            asset=asset2,
            tag=tag2,
            tagged_by=self.user,
        )

        # 查询拥有任一标签的资产
        response = self.client.post(
            '/api/assets/by-tags/',
            {
                'tag_ids': [str(self.tag.id), str(tag2.id)],
                'match_type': 'or'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['data']['count'], 2)
```

---

## 前端组件测试

```vue
<!-- src/views/tags/__tests__/TagSelector.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TagSelector from '../TagSelector.vue'

const mockTagGroups = [
  {
    id: 'group-1',
    name: '使用状态',
    color: '#409eff',
    tags: [
      { id: 'tag-1', name: '在用', color: '#409eff' },
      { id: 'tag-2', name: '闲置', color: '#909399' }
    ]
  },
  {
    id: 'group-2',
    name: '重要性',
    color: '#f56c6c',
    tags: [
      { id: 'tag-3', name: '关键', color: '#f56c6c' },
      { id: 'tag-4', name: '重要', color: '#e6a23c' }
    ]
  }
]

describe('TagSelector.vue', () => {
  it('显示标签组', () => {
    const wrapper = mount(TagSelector, {
      props: {
        tagGroups: mockTagGroups,
        modelValue: []
      },
      global: {
        stubs: {
          ElSelect: true,
          ElOption: true,
          ElOptionGroup: true
        }
      }
    })

    expect(wrapper.vm.tagGroups).toEqual(mockTagGroups)
  })

  it('选择标签', async () => {
    const wrapper = mount(TagSelector, {
      props: {
        tagGroups: mockTagGroups,
        modelValue: []
      },
      global: { stubs: { ElSelect: true } }
    })

    await wrapper.vm.handleChange(['tag-1'])

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([['tag-1']])
  })
})
</script>
```

```vue
<!-- src/views/tags/__tests__/TagFilter.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TagFilter from '../TagFilter.vue'

describe('TagFilter.vue', () => {
  it('初始化选中标签', () => {
    const wrapper = mount(TagFilter, {
      props: {
        tagGroups: mockTagGroups
      },
      global: {
        stubs: {
          ElCheckbox: true,
          ElButton: true
        }
      }
    })

    expect(wrapper.vm.selectedTags).toEqual([])
  })

  it('切换标签选择', () => {
    const wrapper = mount(TagFilter, {
      props: {
        tagGroups: mockTagGroups
      },
      global: { stubs: { ElCheckbox: true } }
    })

    wrapper.vm.handleTagChange('tag-1')
    expect(wrapper.vm.selectedTags).toContain('tag-1')

    wrapper.vm.handleTagChange('tag-1')
    expect(wrapper.vm.selectedTags).not.toContain('tag-1')
  })

  it('清空选择', () => {
    const wrapper = mount(TagFilter, {
      props: {
        tagGroups: mockTagGroups
      },
      global: { stubs: { ElButton: true } }
    })

    wrapper.vm.selectedTags = ['tag-1', 'tag-2']
    wrapper.vm.handleClear()

    expect(wrapper.vm.selectedTags).toEqual([])
    expect(wrapper.emitted('change')).toBeTruthy()
  })

  it('应用筛选', () => {
    const wrapper = mount(TagFilter, {
      props: {
        tagGroups: mockTagGroups
      },
      global: { stubs: { ElButton: true } }
    })

    wrapper.vm.selectedTags = ['tag-1', 'tag-3']
    wrapper.vm.handleApply()

    expect(wrapper.emitted('change')[0]).toEqual([['tag-1', 'tag-3']])
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_tag_e2e.py

from playwright.sync_api import Page, expect


class TestTagE2E:
    """标签管理端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        self.page.fill('input[name="username"]', 'admin')
        self.page.fill('input[name="password"]', 'admin123')
        self.page.click('button:has-text("登录")')

    def test_create_tag_group(self):
        """测试创建标签组"""
        self.page.goto('http://localhost:5173/tags/groups')
        self.page.click('button:has-text("新建标签组")')

        self.page.fill('[name="name"]', '测试标签组')
        self.page.fill('[name="code"]', 'test_group')
        self.page.fill('[name="color"]', '#409eff')
        self.page.fill('[name="description"]', '测试用标签组')

        self.page.click('button:has-text("提交")')

        self.page.wait_for_selector('.el-message--success')

    def test_create_tag(self):
        """测试创建标签"""
        self.page.goto('http://localhost:5173/tags')
        self.page.click('button:has-text("新建标签")')

        self.page.select_option('[name="tag_group"]', '使用状态')
        self.page.fill('[name="name"]', '测试标签')
        self.page.fill('[name="code"]', 'test_tag')
        self.page.fill('[name="color"]', '#67c23a')

        self.page.click('button:has-text("提交")')

        self.page.wait_for_selector('.el-message--success')

    def test_add_tag_to_asset(self):
        """测试为资产添加标签"""
        self.page.goto('http://localhost:5173/assets/asset-uuid')
        self.page.click('text=标签管理')

        self.page.click('.tag-selector .el-select')
        self.page.click('text=在用')
        self.page.click('button:has-text("添加")')

        self.page.wait_for_selector('.el-message--success')

    def test_batch_add_tags(self):
        """测试批量添加标签"""
        self.page.goto('http://localhost:5173/assets')
        self.page.click('.asset-checkbox:first-child')

        self.page.click('button:has-text("批量操作")')
        self.page.click('text=添加标签')

        self.page.click('.tag-selector .el-select')
        self.page.click('text=在用')
        self.page.click('text=关键')
        self.page.click('button:has-text("确定")')

        self.page.wait_for_selector('.el-message--success')

    def test_view_tag_statistics(self):
        """测试查看标签统计"""
        self.page.goto('http://localhost:5173/tags/statistics')

        expect(self.page.locator('.tag-chart')).to_be_visible()
        expect(self.page.locator('.tag-ranking')).to_be_visible()
```

---

## 验收标准检查清单

### 后端验收

- [ ] TagGroup模型创建、排序、软删除正常
- [ ] AssetTag模型创建、编码唯一约束正常
- [ ] AssetTagRelation关联创建、删除正常
- [ ] TagAutoRule条件规则和定时规则正常
- [ ] 软删除功能正常
- [ ] 组织隔离正常
- [ ] 审计字段自动填充

### API验收

- [ ] 标签组CRUD接口正常
- [ ] 标签CRUD接口正常
- [ ] 标签统计接口正常
- [ ] 资产标签添加/移除接口正常
- [ ] 批量添加/移除标签接口正常
- [ ] 按标签查询资产接口正常（AND/OR）
- [ ] 自动化规则接口正常
- [ ] 错误码和错误消息正确

### 前端验收

- [ ] TagSelector组件正常选择
- [ ] TagFilter组件正常筛选
- [ ] TagManager组件正常管理
- [ ] TagStatistics组件正常展示
- [ ] 标签组管理页面正常
- [ ] 标签管理页面正常

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.tags.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.tags.tests.test_models
docker-compose exec backend python manage.py test apps.tags.tests.test_services
docker-compose exec backend python manage.py test apps.tags.tests.test_api

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.tags' manage.py test apps.tags.tests
docker-compose exec backend coverage report

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```
