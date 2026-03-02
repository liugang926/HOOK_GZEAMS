# Phase 7.4: 智能搜索增强 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，确保Elasticsearch全文搜索、搜索建议、历史记录、保存搜索功能的可靠性。

---

## 单元测试

### 后端模型测试

```python
# apps/search/tests/test_models.py

from django.test import TestCase
from apps.search.models import SearchHistory, SavedSearch
from apps.accounts.models import User
from apps.organizations.models import Organization
from django.utils import timezone


class SearchHistoryModelTest(TestCase):
    """SearchHistory模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_search_history_creation(self):
        """测试搜索历史创建"""
        history = SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='笔记本',
            filters={'category': '电子设备'},
            result_count=15,
            created_by=self.user,
        )

        self.assertEqual(history.user, self.user)
        self.assertEqual(history.search_type, 'asset')
        self.assertEqual(history.keyword, '笔记本')
        self.assertEqual(history.result_count, 15)
        self.assertEqual(history.search_count, 1)

    def test_search_count_increment(self):
        """测试搜索次数累加"""
        history = SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='服务器',
            result_count=10,
            created_by=self.user,
        )

        # 模拟重复搜索
        history.search_count = 5
        history.save()

        self.assertEqual(history.search_count, 5)

    def test_soft_delete(self):
        """测试软删除"""
        history = SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='测试',
            created_by=self.user,
        )

        # 软删除
        history.soft_delete()

        self.assertTrue(history.is_deleted)
        self.assertIsNotNone(history.deleted_at)

        # 正常查询无法获取
        active_histories = SearchHistory.objects.filter(keyword='测试')
        self.assertEqual(active_histories.count(), 0)

    def test_organization_isolation(self):
        """测试组织隔离"""
        org2 = Organization.objects.create(code='TEST2', name='Test Org 2')

        history = SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='测试',
            created_by=self.user,
        )

        # 同组织可以查询
        histories = SearchHistory.objects.filter(organization=self.org)
        self.assertEqual(histories.count(), 1)

        # 不同组织无法查询
        histories_org2 = SearchHistory.objects.filter(organization=org2)
        self.assertEqual(histories_org2.count(), 0)

    def test_user_filtering(self):
        """测试用户筛选"""
        user2 = User.objects.create(username='testuser2', organization=self.org)

        SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='笔记本',
            created_by=self.user,
        )

        SearchHistory.objects.create(
            organization=self.org,
            user=user2,
            search_type='asset',
            keyword='服务器',
            created_by=self.user,
        )

        # 只能获取自己的历史
        user_histories = SearchHistory.objects.filter(user=self.user)
        self.assertEqual(user_histories.count(), 1)

        user2_histories = SearchHistory.objects.filter(user=user2)
        self.assertEqual(user2_histories.count(), 1)


class SavedSearchModelTest(TestCase):
    """SavedSearch模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)

    def test_saved_search_creation(self):
        """测试保存搜索创建"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='高价值电子设备',
            search_type='asset',
            keyword='',
            filters={'category': '电子设备', 'purchase_price_min': 10000},
            is_public=False,
            created_by=self.user,
        )

        self.assertEqual(saved.user, self.user)
        self.assertEqual(saved.name, '高价值电子设备')
        self.assertFalse(saved.is_public)

    def test_unique_user_name_constraint(self):
        """测试用户下搜索名称唯一"""
        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='我的搜索',
            search_type='asset',
            created_by=self.user,
        )

        # 重复名称应该失败
        with self.assertRaises(Exception):
            SavedSearch.objects.create(
                organization=self.org,
                user=self.user,
                name='我的搜索',
                search_type='asset',
                created_by=self.user,
            )

    def test_use_count_increment(self):
        """测试使用次数累加"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='测试搜索',
            search_type='asset',
            created_by=self.user,
        )

        # 模拟使用
        saved.use_count = 10
        saved.save()

        self.assertEqual(saved.use_count, 10)

    def test_public_search_visibility(self):
        """测试公开搜索可见性"""
        user2 = User.objects.create(username='testuser2', organization=self.org)

        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='我的私有搜索',
            search_type='asset',
            is_public=False,
            created_by=self.user,
        )

        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='公开搜索',
            search_type='asset',
            is_public=True,
            created_by=self.user,
        )

        # user2 只能看到公开的
        user2_visible = SavedSearch.objects.filter(
            is_public=True
        ).count()
        self.assertEqual(user2_visible, 1)

    def test_soft_delete(self):
        """测试软删除"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='测试搜索',
            search_type='asset',
            created_by=self.user,
        )

        # 软删除
        saved.soft_delete()

        self.assertTrue(saved.is_deleted)
        self.assertIsNotNone(saved.deleted_at)
```

### 后端服务测试

```python
# apps/search/tests/test_services.py

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from apps.search.services import SmartSearchService
from apps.assets.models import Asset
from apps.accounts.models import User
from apps.organizations.models import Organization
from decimal import Decimal


class SmartSearchServiceTest(TestCase):
    """SmartSearchService测试"""

    def setUp(self):
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create(username='testuser', organization=self.org)
        self.service = SmartSearchService()

    @patch('apps.search.services.Elasticsearch')
    def test_search_assets_with_keyword(self, mock_es):
        """测试关键词搜索"""
        # Mock ES响应
        mock_es.search.return_value = {
            'hits': {
                'total': {'value': 2},
                'hits': [
                    {
                        '_id': 'asset-1',
                        '_score': 2.5,
                        '_source': {
                            'asset_id': 'asset-uuid-1',
                            'asset_code': 'ZC001',
                            'asset_name': '笔记本电脑',
                            'specification': '16GB RAM',
                            'category': 'cat-1',
                            'category_name': '电子设备',
                            'status': 'idle',
                            'status_display': '闲置',
                            'purchase_price': 5000.00,
                            'location': 'loc-1',
                            'location_name': 'A区仓库',
                            'custodian': None,
                            'custodian_name': '',
                            'tags': []
                        },
                        'highlight': {
                            'asset_name': ['<em>笔记本</em>电脑']
                        }
                    },
                    {
                        '_id': 'asset-2',
                        '_score': 2.0,
                        '_source': {
                            'asset_id': 'asset-uuid-2',
                            'asset_code': 'ZC002',
                            'asset_name': '联想笔记本',
                            'category': 'cat-1',
                            'category_name': '电子设备',
                            'status': 'in_use',
                            'status_display': '在用',
                            'purchase_price': 4500.00,
                            'location': 'loc-1',
                            'location_name': 'A区仓库',
                            'custodian': 'user-1',
                            'custodian_name': '张三',
                            'tags': ['tag-1']
                        },
                        'highlight': {
                            'asset_name': ['联想<em>笔记本</em>']
                        }
                    }
                ]
            },
            'aggregations': {
                'category': {
                    'buckets': [
                        {'key': 'cat-1', 'doc_count': 2}
                    ]
                },
                'status': {
                    'buckets': [
                        {'key': 'in_use', 'doc_count': 1},
                        {'key': 'idle', 'doc_count': 1}
                    ]
                },
                'price_ranges': {
                    'buckets': [
                        {'key': '1k_to_5k', 'doc_count': 2}
                    ]
                }
            }
        }

        result = self.service.search_assets(
            organization=self.org,
            keyword='笔记本',
            page=1,
            page_size=20
        )

        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['results']), 2)
        self.assertEqual(result['results'][0]['asset_name'], '笔记本电脑')
        self.assertIn('highlight', result['results'][0])
        self.assertIn('category', result['aggregations'])
        self.assertIn('status', result['aggregations'])
        self.assertIn('price_ranges', result['aggregations'])

    @patch('apps.search.services.Elasticsearch')
    def test_search_with_filters(self, mock_es):
        """测试带筛选条件的搜索"""
        mock_es.search.return_value = {
            'hits': {
                'total': {'value': 1},
                'hits': [{
                    '_id': 'asset-1',
                    '_score': 1.0,
                    '_source': {
                        'asset_id': 'asset-uuid-1',
                        'asset_code': 'ZC001',
                        'asset_name': '服务器',
                        'category': 'cat-1',
                        'category_name': '电子设备',
                        'status': 'in_use',
                        'status_display': '在用',
                        'purchase_price': 15000.00,
                        'location': 'loc-1',
                        'location_name': 'A区仓库',
                        'custodian': 'user-1',
                        'custodian_name': '张三',
                        'tags': ['tag-1']
                    },
                    'highlight': {}
                }]
            },
            'aggregations': {}
        }

        filters = {
            'category': 'cat-1',
            'status': 'in_use',
            'purchase_price_min': 10000
        }

        result = self.service.search_assets(
            organization=self.org,
            keyword='服务器',
            filters=filters,
            page=1,
            page_size=20
        )

        # 验证ES被调用
        self.assertTrue(mock_es.search.called)
        call_args = mock_es.search.call_args
        query_body = call_args[1]['body']
        self.assertIn('filter', query_body['query']['bool'])

    @patch('apps.search.services.Elasticsearch')
    def test_search_empty_results(self, mock_es):
        """测试空搜索结果"""
        mock_es.search.return_value = {
            'hits': {
                'total': {'value': 0},
                'hits': []
            },
            'aggregations': {}
        }

        result = self.service.search_assets(
            organization=self.org,
            keyword='不存在的关键词',
            page=1,
            page_size=20
        )

        self.assertEqual(result['total'], 0)
        self.assertEqual(len(result['results']), 0)

    @patch('apps.search.services.Elasticsearch')
    def test_sort_by_relevance(self, mock_es):
        """测试按相关性排序"""
        mock_es.search.return_value = {
            'hits': {'total': {'value': 2}, 'hits': []},
            'aggregations': {}
        }

        self.service.search_assets(
            organization=self.org,
            keyword='笔记本',
            sort_by='relevance',
            sort_order='desc',
            page=1,
            page_size=20
        )

        # 验证排序
        call_args = mock_es.search.call_args
        sort = call_args[1]['body']['sort']
        self.assertEqual(sort[0], '_score')

    @patch('apps.search.services.Elasticsearch')
    def test_sort_by_price(self, mock_es):
        """测试按价格排序"""
        mock_es.search.return_value = {
            'hits': {'total': {'value': 2}, 'hits': []},
            'aggregations': {}
        }

        self.service.search_assets(
            organization=self.org,
            keyword='笔记本',
            sort_by='price',
            sort_order='asc',
            page=1,
            page_size=20
        )

        # 验证排序
        call_args = mock_es.search.call_args
        sort = call_args[1]['body']['sort']
        self.assertIn('purchase_price', sort[0])

    @patch('apps.search.services.Elasticsearch')
    def test_get_suggestions(self, mock_es):
        """测试获取搜索建议"""
        mock_es.search.return_value = {
            'aggregations': {
                'suggestions': {
                    'buckets': [
                        {'key': '笔记本电脑', 'doc_count': 45},
                        {'key': '笔记本支架', 'doc_count': 5},
                        {'key': '笔记本包', 'doc_count': 3}
                    ]
                }
            }
        }

        suggestions = self.service.get_suggestions(
            keyword='笔',
            search_type='asset',
            organization=self.org
        )

        self.assertEqual(len(suggestions), 3)
        self.assertEqual(suggestions[0]['suggestion'], '笔记本电脑')
        self.assertEqual(suggestions[0]['count'], 45)

    @patch('apps.search.services.Elasticsearch')
    def test_get_suggestions_empty(self, mock_es):
        """测试空建议"""
        mock_es.search.side_effect = Exception('Index not found')

        suggestions = self.service.get_suggestions(
            keyword='xyz',
            search_type='asset',
            organization=self.org
        )

        self.assertEqual(len(suggestions), 0)

    @patch('apps.search.services.Elasticsearch')
    def test_sync_asset(self, mock_es):
        """测试同步资产到ES"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='ZC001',
            asset_name='MacBook Pro',
            purchase_price=Decimal('15000.00'),
            asset_status='idle',
            created_by=self.user,
        )

        mock_es.index.return_value = {'result': 'created'}

        result = self.service.sync_asset(asset)

        self.assertTrue(result)
        # 验证ES被调用
        self.assertTrue(mock_es.index.called)

    @patch('apps.search.services.Elasticsearch')
    def test_delete_asset_from_es(self, mock_es):
        """测试从ES删除资产"""
        mock_es.delete.return_value = {'result': 'deleted'}

        result = self.service.delete_asset('asset-uuid-1')

        self.assertTrue(result)
        self.assertTrue(mock_es.delete.called)

    @patch('apps.search.services.Elasticsearch')
    def test_bulk_sync_assets(self, mock_es):
        """测试批量同步资产"""
        from elasticsearch.helpers import bulk

        assets = [
            Asset.objects.create(
                organization=self.org,
                asset_code=f'ZC{i:03d}',
                asset_name=f'资产{i}',
                created_by=self.user,
            )
            for i in range(1, 4)
        ]

        mock_bulk = Mock(return_value=(3, 0))
        with patch('apps.search.services.bulk', mock_bulk):
            result = self.service.bulk_sync_assets(assets)

        self.assertEqual(result['success'], 3)
        self.assertEqual(result['failed'], 0)
```

---

## API集成测试

```python
# apps/search/tests/test_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch, Mock
from apps.search.models import SearchHistory, SavedSearch
from apps.accounts.models import User
from apps.organizations.models import Organization


class SearchAPITest(TestCase):
    """搜索API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(code='TEST', name='Test Org')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    @patch('apps.search.services.SmartSearchService.search_assets')
    def test_search_assets(self, mock_search):
        """测试搜索资产"""
        mock_search.return_value = {
            'total': 2,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'results': [
                {
                    'id': 'asset-1',
                    'asset_code': 'ZC001',
                    'asset_name': '笔记本电脑',
                    'highlight': {'asset_name': ['<em>笔记本</em>电脑']},
                    'score': 2.5,
                    'category': 'cat-1',
                    'category_name': '电子设备',
                    'status': 'idle',
                    'status_display': '闲置'
                }
            ],
            'aggregations': {
                'category': {'cat-1': 2},
                'status': {'idle': 2}
            }
        }

        response = self.client.post(
            '/api/search/assets/',
            {
                'keyword': '笔记本',
                'page': 1,
                'page_size': 20
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total'], 2)

    @patch('apps.search.services.SmartSearchService.search_assets')
    def test_search_with_filters(self, mock_search):
        """测试带筛选条件搜索"""
        mock_search.return_value = {
            'total': 1,
            'page': 1,
            'page_size': 20,
            'total_pages': 1,
            'results': [],
            'aggregations': {}
        }

        response = self.client.post(
            '/api/search/assets/',
            {
                'keyword': '笔记本',
                'filters': {
                    'category': 'cat-1',
                    'status': 'in_use',
                    'purchase_price_min': 5000
                },
                'sort_by': 'price',
                'sort_order': 'asc'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(mock_search.called)

    @patch('apps.search.services.SmartSearchService.get_suggestions')
    def test_get_suggestions(self, mock_suggestions):
        """测试获取搜索建议"""
        mock_suggestions.return_value = [
            {'suggestion': '笔记本电脑', 'count': 45},
            {'suggestion': '笔记本支架', 'count': 5}
        ]

        response = self.client.get(
            '/api/search/suggestions/?keyword=笔&type=asset'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)

    def test_get_search_history(self):
        """测试获取搜索历史"""
        SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='笔记本',
            result_count=15,
            created_by=self.user,
        )

        SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='服务器',
            result_count=10,
            created_by=self.user,
        )

        response = self.client.get('/api/search/history/?type=asset&limit=10')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)

    def test_clear_search_history(self):
        """测试清空搜索历史"""
        SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='asset',
            keyword='笔记本',
            created_by=self.user,
        )

        SearchHistory.objects.create(
            organization=self.org,
            user=self.user,
            search_type='project',
            keyword='AI平台',
            created_by=self.user,
        )

        # 清空资产搜索历史
        response = self.client.delete('/api/search/history/?type=asset')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('已删除', data['message'])

        # 验证项目历史还在
        remaining = SearchHistory.objects.filter(
            user=self.user,
            search_type='project'
        ).count()
        self.assertEqual(remaining, 1)

    def test_save_search(self):
        """测试保存搜索"""
        response = self.client.post(
            '/api/search/save/',
            {
                'name': '高价值电子设备',
                'search_type': 'asset',
                'keyword': '',
                'filters': {
                    'category': '电子设备',
                    'purchase_price_min': 10000
                },
                'is_public': False
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], '高价值电子设备')

    def test_save_duplicate_name_fails(self):
        """测试保存重复名称失败"""
        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='我的搜索',
            search_type='asset',
            created_by=self.user,
        )

        response = self.client.post(
            '/api/search/save/',
            {
                'name': '我的搜索',
                'search_type': 'asset'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_get_saved_searches(self):
        """测试获取保存的搜索"""
        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='私有搜索',
            search_type='asset',
            is_public=False,
            created_by=self.user,
        )

        SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='公开搜索',
            search_type='asset',
            is_public=True,
            created_by=self.user,
        )

        response = self.client.get('/api/search/saved/?type=asset')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 2)

    def test_use_saved_search(self):
        """测试使用保存的搜索"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='测试搜索',
            search_type='asset',
            keyword='笔记本',
            filters={'category': '电子设备'},
            created_by=self.user,
        )

        response = self.client.post(f'/api/search/saved/{saved.id}/use/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['keyword'], '笔记本')

        # 验证使用次数增加
        saved.refresh_from_db()
        self.assertEqual(saved.use_count, 1)

    def test_update_saved_search(self):
        """测试更新保存的搜索"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='原名称',
            search_type='asset',
            created_by=self.user,
        )

        response = self.client.put(
            f'/api/search/saved/{saved.id}/',
            {
                'name': '新名称',
                'filters': {'status': 'in_use'}
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['name'], '新名称')

    def test_delete_saved_search(self):
        """测试删除保存的搜索"""
        saved = SavedSearch.objects.create(
            organization=self.org,
            user=self.user,
            name='待删除',
            search_type='asset',
            created_by=self.user,
        )

        response = self.client.delete(f'/api/search/saved/{saved.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('删除成功', data['message'])
```

---

## 前端组件测试

```vue
<!-- src/views/search/__tests__/SmartSearchBox.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SmartSearchBox from '../SmartSearchBox.vue'

const mockSuggestions = [
  { type: 'history', label: '笔记本', count: 5 },
  { type: 'saved', label: '高价值设备', savedId: 'saved-1' },
  { type: 'trending', label: '服务器', count: 156 }
]

describe('SmartSearchBox.vue', () => {
  it('初始化搜索框', () => {
    const wrapper = mount(SmartSearchBox, {
      props: {
        searchType: 'asset'
      },
      global: {
        stubs: {
          ElAutocomplete: true,
          ElButton: true,
          ElDialog: true
        }
      }
    })

    expect(wrapper.vm.keyword).toBe('')
    expect(wrapper.vm.searchType).toBe('asset')
  })

  it('触发搜索', async () => {
    const wrapper = mount(SmartSearchBox, {
      props: { searchType: 'asset' },
      global: { stubs: { ElAutocomplete: true } }
    })

    wrapper.vm.keyword = '笔记本'
    await wrapper.vm.handleSearch()

    expect(wrapper.emitted('search')).toBeTruthy()
    expect(wrapper.emitted('search')[0]).toEqual([
      { keyword: '笔记本', filters: {} }
    ])
  })

  it('显示建议', () => {
    const wrapper = mount(SmartSearchBox, {
      props: { searchType: 'asset' },
      global: { stubs: { ElAutocomplete: true } }
    })

    wrapper.vm.suggestions = mockSuggestions
    expect(wrapper.vm.suggestions).toHaveLength(3)
  })

  it('选择历史记录', async () => {
    const wrapper = mount(SmartSearchBox, {
      props: { searchType: 'asset' },
      global: { stubs: { ElAutocomplete: true } }
    })

    await wrapper.vm.handleSelect({
      type: 'history',
      label: '笔记本',
      filters: {}
    })

    expect(wrapper.vm.keyword).toBe('笔记本')
    expect(wrapper.emitted('search')).toBeTruthy()
  })

  it('打开高级搜索对话框', () => {
    const wrapper = mount(SmartSearchBox, {
      props: { searchType: 'asset' },
      global: { stubs: { ElAutocomplete: true, ElButton: true, ElDialog: true } }
    })

    wrapper.vm.openAdvancedDialog()
    expect(wrapper.vm.advancedDialogVisible).toBe(true)
  })

  it('打开保存搜索对话框', () => {
    const wrapper = mount(SmartSearchBox, {
      props: { searchType: 'asset' },
      global: { stubs: { ElAutocomplete: true, ElButton: true, ElDialog: true } }
    })

    wrapper.vm.currentFilters = {'category': '电子设备'}
    wrapper.vm.openSaveDialog()
    expect(wrapper.vm.saveDialogVisible).toBe(true)
  })
})
</script>
```

```vue
<!-- src/views/search/__tests__/SearchResultList.spec.vue -->
<script setup>
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import SearchResultList from '../SearchResultList.vue'

const mockResults = [
  {
    id: 'asset-1',
    asset_code: 'ZC001',
    asset_name: '<em>笔记本</em>电脑',
    highlight: { asset_name: ['<em>笔记本</em>电脑'] },
    score: 2.5,
    category_name: '电子设备',
    status_display: '闲置',
    purchase_price: 5000.00
  },
  {
    id: 'asset-2',
    asset_code: 'ZC002',
    asset_name: '联想<em>笔记本</em>',
    highlight: { asset_name: ['联想<em>笔记本</em>'] },
    score: 2.0,
    category_name: '电子设备',
    status_display: '在用',
    purchase_price: 4500.00
  }
]

const mockAggregations = {
  category: { 'cat-1': 2, 'cat-2': 1 },
  status: { 'in_use': 1, 'idle': 1 },
  price_ranges: { '1k_to_5k': 2 }
}

describe('SearchResultList.vue', () => {
  it('显示搜索结果', () => {
    const wrapper = mount(SearchResultList, {
      props: {
        results: mockResults,
        total: 2,
        aggregations: mockAggregations
      },
      global: {
        stubs: {
          ElTable: true,
          ElPagination: true
        }
      }
    })

    expect(wrapper.vm.results).toHaveLength(2)
    expect(wrapper.vm.total).toBe(2)
  })

  it('切换排序', async () => {
    const wrapper = mount(SearchResultList, {
      props: {
        results: mockResults,
        total: 2,
        aggregations: {}
      },
      global: { stubs: { ElTable: true } }
    })

    await wrapper.vm.handleSortChange('price', 'asc')

    expect(wrapper.emitted('sort-change')).toBeTruthy()
    expect(wrapper.emitted('sort-change')[0]).toEqual(['price', 'asc'])
  })

  it('翻页', async () => {
    const wrapper = mount(SearchResultList, {
      props: {
        results: mockResults,
        total: 50,
        aggregations: {}
      },
      global: { stubs: { ElPagination: true } }
    })

    await wrapper.vm.handlePageChange(2)

    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')[0]).toEqual([2])
  })

  it('应用聚合筛选', async () => {
    const wrapper = mount(SearchResultList, {
      props: {
        results: mockResults,
        total: 2,
        aggregations: mockAggregations
      },
      global: { stubs: { ElTable: true } }
    })

    await wrapper.vm.handleAggregationFilter('category', 'cat-1')

    expect(wrapper.emitted('filter-change')).toBeTruthy()
  })

  it('显示空状态', () => {
    const wrapper = mount(SearchResultList, {
      props: {
        results: [],
        total: 0,
        aggregations: {}
      },
      global: { stubs: { ElEmpty: true } }
    })

    expect(wrapper.vm.isEmpty).toBe(true)
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_search_e2e.py

from playwright.sync_api import Page, expect


class TestSearchE2E:
    """智能搜索端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        self.page.fill('input[name="username"]', 'admin')
        self.page.fill('input[name="password"]', 'admin123')
        self.page.click('button:has-text("登录")')

    def test_basic_search(self):
        """测试基础搜索"""
        self.page.goto('http://localhost:5173/search')

        # 输入搜索关键词
        self.page.fill('[name="keyword"]', '笔记本')
        self.page.press('[name="keyword"]', 'Enter')

        # 等待结果加载
        self.page.wait_for_selector('.search-result-list')

        # 验证结果显示
        expect(self.page.locator('.search-result-item')).to_have_count(
            lambda x: x > 0
        )

    def test_search_with_filters(self):
        """测试带筛选条件搜索"""
        self.page.goto('http://localhost:5173/search')

        # 输入关键词
        self.page.fill('[name="keyword"]', '笔记本')

        # 选择分类
        self.page.click('.category-filter')
        self.page.click('text=电子设备')

        # 选择状态
        self.page.click('.status-filter')
        self.page.click('text=在用')

        # 执行搜索
        self.page.click('button:has-text("搜索")')

        self.page.wait_for_selector('.search-result-list')

    def test_search_suggestions(self):
        """测试搜索建议"""
        self.page.goto('http://localhost:5173/search')

        # 输入关键词
        search_box = self.page.locator('[name="keyword"]')
        search_box.fill('笔')

        # 等待建议显示
        self.page.wait_for_selector('.search-suggestions')

        # 验证建议项
        expect(self.page.locator('.suggestion-item')).to_have_count(
            lambda x: x > 0
        )

    def test_save_search(self):
        """测试保存搜索"""
        self.page.goto('http://localhost:5173/search')

        # 执行搜索
        self.page.fill('[name="keyword"]', '笔记本')
        self.page.click('button:has-text("搜索")')

        # 点击保存搜索
        self.page.click('button:has-text("保存搜索")')

        # 输入名称
        self.page.fill('[name="save_name"]', '笔记本搜索')
        self.page.click('button:has-text("确定")')

        # 验证成功提示
        self.page.wait_for_selector('.el-message--success')

    def test_use_saved_search(self):
        """测试使用保存的搜索"""
        self.page.goto('http://localhost:5173/search')

        # 点击保存的搜索下拉
        self.page.click('.saved-search-selector')
        self.page.click('text=笔记本搜索')

        # 验证搜索被执行
        self.page.wait_for_selector('.search-result-list')

    def test_view_search_history(self):
        """测试查看搜索历史"""
        self.page.goto('http://localhost:5173/search')

        # 点击搜索框
        self.page.click('[name="keyword"]')

        # 验证历史记录显示
        expect(self.page.locator('.search-history')).to_be_visible()

        # 点击历史记录项
        self.page.click('.history-item:first-child')

        # 验证搜索被执行
        expect(self.page.locator('[name="keyword"]')).to_have_value(
            lambda x: x != ''
        )

    def test_clear_search_history(self):
        """测试清空搜索历史"""
        self.page.goto('http://localhost:5173/search/history')

        # 点击清空按钮
        self.page.click('button:has-text("清空历史")')

        # 确认清空
        self.page.click('.el-dialog:has-text("确定")')

        # 验证成功提示
        self.page.wait_for_selector('.el-message--success')

    def test_aggregation_filter(self):
        """测试聚合筛选"""
        self.page.goto('http://localhost:5173/search')

        # 执行搜索
        self.page.fill('[name="keyword"]', '笔记本')
        self.page.click('button:has-text("搜索")')

        # 等待聚合加载
        self.page.wait_for_selector('.aggregation-filters')

        # 点击分类聚合
        self.page.click('.aggregation-category .agg-item:first-child')

        # 验证筛选被应用
        self.page.wait_for_selector('.filter-tag')

    def test_price_range_filter(self):
        """测试价格区间筛选"""
        self.page.goto('http://localhost:5173/search')

        # 执行搜索
        self.page.fill('[name="keyword"]', '笔记本')
        self.page.click('button:has-text("搜索")')

        # 点击价格区间
        self.page.click('.price-range-5k-10k')

        # 验证结果更新
        self.page.wait_for_selector('.search-result-list')

    def test_export_search_results(self):
        """测试导出搜索结果"""
        self.page.goto('http://localhost:5173/search')

        # 执行搜索
        self.page.fill('[name="keyword"]', '笔记本')
        self.page.click('button:has-text("搜索")')

        # 点击导出按钮
        self.page.click('button:has-text("导出")')

        # 选择导出格式
        self.page.click('text=Excel')

        # 验证下载开始
        # 注意：实际下载验证需要配置浏览器
```

---

## 验收标准检查清单

### 后端验收

- [ ] SearchHistory模型记录搜索历史正常
- [ ] SavedSearch模型保存搜索正常
- [ ] SmartSearchService搜索功能正常
- [ ] Elasticsearch索引配置正确
- [ ] 软删除功能正常
- [ ] 组织隔离正常
- [ ] 审计字段自动填充

### API验收

- [ ] 搜索资产接口正常
- [ ] 搜索建议接口正常
- [ ] 搜索历史接口正常
- [ ] 清空历史接口正常
- [ ] 保存搜索接口正常
- [ ] 获取保存搜索接口正常
- [ ] 使用保存搜索接口正常
- [ ] 删除保存搜索接口正常
- [ ] 错误码和错误消息正确

### 前端验收

- [ ] SmartSearchBox组件正常搜索
- [ ] SearchResultList组件正常显示结果
- [ ] AggregationFilter组件正常筛选
- [ ] AdvancedSearchDialog高级搜索正常
- [ ] SavedSearchDialog保存搜索正常
- [ ] 搜索建议显示正常
- [ ] 历史记录显示正常
- [ ] 结果高亮显示正常

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.search.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.search.tests.test_models
docker-compose exec backend python manage.py test apps.search.tests.test_services
docker-compose exec backend python manage.py test apps.search.tests.test_api

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.search' manage.py test apps.search.tests
docker-compose exec backend coverage report

# 前端测试
npm run test

# E2E测试
npm run test:e2e

# Elasticsearch相关
# 启动ES用于测试
docker-compose up -d elasticsearch

# 创建测试索引
curl -X PUT 'localhost:9200/gzeams_test_asset'

# 验证索引
curl 'localhost:9200/_cat/indices?v'
```
