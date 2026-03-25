# Phase 1.4: 资产卡片CRUD - 测试验证

## 测试策略

采用**TDD**思路，覆盖模型服务、API接口、前端组件。

---

## 单元测试

### 后端模型测试

```python
# apps/assets/tests/test_asset_model.py

from django.test import TestCase
from django.utils import timezone
from apps.assets.models import Asset, AssetCategory, Supplier, Location
from apps.organizations.models import Organization
from apps.accounts.models import User


class AssetModelTest(TestCase):
    """资产模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )
        self.user = User.objects.create_user(
            username='testuser',
            organization=self.org
        )

    def test_create_asset_minimal(self):
        """测试创建最小资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000.00,
            purchase_date=timezone.now().date()
        )

        self.assertIsNotNone(asset.asset_code)
        self.assertEqual(asset.asset_name, '测试资产')
        self.assertIsNotNone(asset.qr_code)

    def test_generate_asset_code(self):
        """测试资产编码生成"""
        asset1 = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产1',
            purchase_price=1000,
            purchase_date=timezone.now().date()
        )

        asset2 = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产2',
            purchase_price=2000,
            purchase_date=timezone.now().date()
        )

        # 编码格式: ZCYYYYMMNNNN
        self.assertTrue(asset1.asset_code.startswith('ZC'))
        self.assertTrue(asset2.asset_code.startswith('ZC'))

        # 序号递增
        seq1 = int(asset1.asset_code[-4:])
        seq2 = int(asset2.asset_code[-4:])
        self.assertEqual(seq2, seq1 + 1)

    def test_net_value_calculation(self):
        """测试净值计算"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=10000,
            accumulated_depreciation=2000,
            purchase_date=timezone.now().date()
        )

        self.assertEqual(asset.net_value, 8000)

    def test_residual_value_calculation(self):
        """测试残值计算"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=10000,
            residual_rate=5.00,
            purchase_date=timezone.now().date()
        )

        self.assertEqual(asset.residual_value, 500)

    def test_get_status_label(self):
        """测试状态标签"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date=timezone.now().date(),
            asset_status='in_use'
        )

        self.assertEqual(asset.get_status_label(), '在用')

    def test_soft_delete(self):
        """测试软删除"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date=timezone.now().date()
        )

        asset_id = asset.id
        asset.soft_delete()

        # 验证软删除
        asset.refresh_from_db()
        self.assertTrue(asset.is_deleted)

        # 验证不在正常查询中
        active_assets = Asset.objects.filter(id=asset_id, is_deleted=False)
        self.assertEqual(active_assets.count(), 0)


class LocationModelTest(TestCase):
    """存放地点模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')

    def test_location_tree(self):
        """测试地点树结构"""
        building = Location.objects.create(
            organization=self.org,
            name='总部大楼',
            location_type='building'
        )

        floor = Location.objects.create(
            organization=self.org,
            name='3楼',
            parent=building,
            location_type='floor'
        )

        room = Location.objects.create(
            organization=self.org,
            name='A区',
            parent=floor,
            location_type='area'
        )

        # 验证层级
        self.assertEqual(building.level, 0)
        self.assertEqual(floor.level, 1)
        self.assertEqual(room.level, 2)

        # 验证路径
        self.assertEqual(building.path, '总部大楼')
        self.assertEqual(floor.path, '总部大楼 / 3楼')
        self.assertEqual(room.path, '总部大楼 / 3楼 / A区')
```

### 服务层测试

```python
# apps/assets/tests/test_asset_service.py

from django.test import TestCase
from apps.assets.services.asset_service import AssetService
from apps.assets.models import Asset, AssetStatusLog
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import AssetCategory


class AssetServiceTest(TestCase):
    """资产服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')
        self.user = User.objects.create_user(
            username='testuser',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )
        self.service = AssetService()

    def test_create_asset(self):
        """测试创建资产"""
        data = {
            'asset_name': '测试资产',
            'asset_category': self.category.id,
            'purchase_price': 5000,
            'purchase_date': '2024-01-01'
        }

        asset = self.service.create_asset(data, self.user)

        self.assertEqual(asset.asset_name, '测试资产')
        self.assertEqual(asset.asset_category, self.category)
        self.assertIsNotNone(asset.asset_code)

    def test_update_asset(self):
        """测试更新资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='原名',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        updated = self.service.update_asset(asset.id, {
            'asset_name': '新名',
            'purchase_price': 2000
        })

        asset.refresh_from_db()
        self.assertEqual(asset.asset_name, '新名')
        self.assertEqual(float(asset.purchase_price), 2000)

    def test_query_with_filters(self):
        """测试带过滤的查询"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产1',
            purchase_price=1000,
            purchase_date='2024-01-01',
            asset_status='in_use'
        )
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产2',
            purchase_price=2000,
            purchase_date='2024-01-01',
            asset_status='idle'
        )

        # 按状态过滤
        result = self.service.query_assets(
            filters={'status': 'in_use'}
        )

        self.assertEqual(result['total'], 1)
        self.assertEqual(result['items'][0].asset_name, '资产1')

    def test_search_assets(self):
        """测试搜索"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='MacBook Pro',
            serial_number='SN123456',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        # 搜索名称
        result = self.service.query_assets(search='MacBook')
        self.assertEqual(result['total'], 1)

        # 搜索序列号
        result = self.service.query_assets(search='SN123')
        self.assertEqual(result['total'], 1)

    def test_change_status(self):
        """测试状态变更"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date='2024-01-01',
            asset_status='idle'
        )

        self.service.change_status(
            asset.id,
            'in_use',
            '投入使用',
            self.user
        )

        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'in_use')

        # 验证日志记录
        log = AssetStatusLog.objects.filter(asset=asset).first()
        self.assertEqual(log.old_status, 'idle')
        self.assertEqual(log.new_status, 'in_use')
        self.assertEqual(log.reason, '投入使用')

    def test_get_statistics(self):
        """测试统计"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产1',
            purchase_price=10000,
            purchase_date='2024-01-01',
            asset_status='in_use'
        )
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='资产2',
            purchase_price=5000,
            purchase_date='2024-01-01',
            asset_status='idle'
        )

        stats = self.service.get_statistics()

        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['total_value'], 15000)
```

---

## API集成测试

```python
# apps/assets/tests/test_asset_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.assets.models import Asset, AssetCategory


class AssetAPITest(TestCase):
    """资产API测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='测试组织')

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )

    def test_list_assets(self):
        """测试获取资产列表"""
        Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        response = self.client.get('/api/assets/assets/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 1)

    def test_create_asset(self):
        """测试创建资产"""
        data = {
            'asset_name': '新资产',
            'asset_category': self.category.id,
            'purchase_price': 5000,
            'purchase_date': '2024-06-15'
        }

        response = self.client.post(
            '/api/assets/assets/',
            data,
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result['asset_name'], '新资产')
        self.assertIn('asset_code', result)

    def test_get_asset_detail(self):
        """测试获取资产详情"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        response = self.client.get(f'/api/assets/assets/{asset.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('asset', data)
        self.assertIn('history', data)

    def test_update_asset(self):
        """测试更新资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='原名',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        response = self.client.put(
            f'/api/assets/assets/{asset.id}/',
            {'asset_name': '新名'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['asset_name'], '新名')

    def test_delete_asset(self):
        """测试删除资产"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='待删除',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        response = self.client.delete(f'/api/assets/assets/{asset.id}/')

        self.assertEqual(response.status_code, 204)

        # 验证软删除
        asset.refresh_from_db()
        self.assertTrue(asset.is_deleted)

    def test_get_statistics(self):
        """测试获取统计"""
        response = self.client.get('/api/assets/assets/statistics/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total', data)
        self.assertIn('by_status', data)

    def test_change_status(self):
        """测试变更状态"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date='2024-01-01',
            asset_status='idle'
        )

        response = self.client.post(
            f'/api/assets/assets/{asset.id}/change_status/',
            {'status': 'in_use', 'reason': '启用'},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'in_use')

    def test_get_qr_code(self):
        """测试获取二维码"""
        asset = Asset.objects.create(
            organization=self.org,
            asset_category=self.category,
            asset_name='测试资产',
            purchase_price=1000,
            purchase_date='2024-01-01'
        )

        response = self.client.get(f'/api/assets/assets/{asset.id}/qr_code/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
```

---

## 前端组件测试

```vue
<!-- frontend/src/views/assets/__tests__/AssetList.spec.vue -->

<script setup>
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import AssetList from '../AssetList.vue'
import * as assetApi from '@/api/assets'

// Mock API
vi.mock('@/api/assets', () => ({
  getAssetList: vi.fn(() => Promise.resolve({
    data: { total: 10, items: [], page: 1, page_size: 20 }
  })),
  getAssetStatistics: vi.fn(() => Promise.resolve({
    data: { total: 100, by_status: {}, total_value: 500000 }
  })),
  deleteAsset: vi.fn(() => Promise.resolve()),
  getAssetQRCode: vi.fn(() => Promise.resolve({ data: new Blob() }))
}))

vi.mock('@/api/assetCategory', () => ({
  getCategoryTree: vi.fn(() => Promise.resolve({ data: [] }))
}))

vi.mock('@/api/organization', () => ({
  getDepartments: vi.fn(() => Promise.resolve({ data: { results: [] } }))
}))

describe('AssetList.vue', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(AssetList, {
      global: {
        stubs: {
          ElPageHeader: true,
          ElCard: true,
          ElForm: true,
          ElFormItem: true,
          ElInput: true,
          ElSelect: true,
          ElCascader: true,
          ElTable: true,
          ElPagination: true,
          ElButton: true,
          ElTag: true,
          ElIcon: true
        }
      }
    })
  })

  it('渲染资产列表页面', () => {
    expect(wrapper.find('.asset-list').exists()).toBe(true)
  })

  it('加载资产列表', async () => {
    await wrapper.vm.fetchData()
    expect(assetApi.getAssetList).toHaveBeenCalled()
  })

  it('加载统计数据', async () => {
    await wrapper.vm.loadStatistics()
    expect(assetApi.getAssetStatistics).toHaveBeenCalled()
    expect(wrapper.vm.statistics.total).toBe(100)
  })

  it('搜索功能', async () => {
    wrapper.vm.queryForm.search = '测试'
    await wrapper.vm.handleSearch()
    expect(assetApi.getAssetList).toHaveBeenCalledWith(
      expect.objectContaining({ search: '测试' })
    )
  })

  it('重置筛选条件', () => {
    wrapper.vm.queryForm.search = '测试'
    wrapper.vm.queryForm.status = 'in_use'
    wrapper.vm.handleReset()

    expect(wrapper.vm.queryForm.search).toBe('')
    expect(wrapper.vm.queryForm.status).toBeNull()
  })

  it('格式化金额', () => {
    expect(wrapper.vm.formatMoney(1234.56)).toBe('1,234.56')
    expect(wrapper.vm.formatMoney(10000)).toBe('10,000.00')
  })

  it('获取状态标签', () => {
    expect(wrapper.vm.getStatusLabel('in_use')).toBe('在用')
    expect(wrapper.vm.getStatusLabel('idle')).toBe('闲置')
    expect(wrapper.vm.getStatusLabel('maintenance')).toBe('维修中')
  })

  it('获取状态类型', () => {
    expect(wrapper.vm.getStatusType('in_use')).toBe('success')
    expect(wrapper.vm.getStatusType('idle')).toBe('warning')
    expect(wrapper.vm.getStatusType('maintenance')).toBe('danger')
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_asset_e2e.py

from playwright.sync_api import Page, expect


class TestAssetE2E:
    """资产端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        # 登录...

    def test_create_asset_complete_flow(self):
        """测试创建资产完整流程"""
        # 1. 进入新增页面
        self.page.goto('http://localhost:5173/assets/new')

        # 2. 等待表单加载
        self.page.wait_for_selector('.asset-form')

        # 3. 填写基础信息
        self.page.fill('[name="asset_name"]', '测试笔记本')
        self.page.click('.el-cascader')
        self.page.click('text="计算机设备"')

        # 4. 切换到财务信息
        self.page.click('text="财务信息"')
        self.page.fill('[name="purchase_price"]', '5000')
        self.page.click('[name="purchase_date"]')
        self.page.click('text="15"')

        # 5. 切换到使用信息
        self.page.click('text="使用信息"')
        self.page.click('select[name="department"]')
        self.page.click('text="研发部"')

        # 6. 提交
        self.page.click('button:has-text("保存")')

        # 7. 验证成功提示
        self.page.wait_for_selector('.el-message--success')
        expect(self.page).to_have_url('http://localhost:5173/assets')

    def test_search_and_filter(self):
        """测试搜索和筛选"""
        self.page.goto('http://localhost:5173/assets')

        # 搜索
        self.page.fill('input[placeholder*="资产编码"]', 'MacBook')
        self.page.click('button:has-text("搜索")')

        # 验证搜索结果
        self.page.wait_for_selector('.el-table')

    def test_view_asset_detail(self):
        """测试查看资产详情"""
        self.page.goto('http://localhost:5173/assets')

        # 点击第一行
        self.page.click('.el-table tbody tr:first-child')

        # 验证进入详情页
        expect(self.page).to_have_url(/\/assets\/\d+/)

    def test_change_asset_status(self):
        """测试变更资产状态"""
        # 先进入编辑页面
        self.page.goto('http://localhost:5173/assets')
        self.page.click('.el-table tbody tr:first-child .el-button:has-text("编辑")')

        # 更改状态
        self.page.select_option('select[name="asset_status"]', 'maintenance')
        self.page.click('button:has-text("保存")')

        # 验证保存成功
        self.page.wait_for_selector('.el-message--success')

    def test_view_qr_code(self):
        """测试查看二维码"""
        self.page.goto('http://localhost:5173/assets')

        # 点击二维码按钮
        self.page.click('.el-table tbody tr:first-child button:has-text("二维码")')

        # 验证弹窗
        self.page.wait_for_selector('.el-dialog:has-text("资产二维码")')
        self.page.wait_for_selector('.qr-code-container img')
```

---

## 验收标准检查清单

### 后端验收

- [ ] Asset 模型完整实现
- [ ] 资产编码自动生成 (ZCYYYYMMNNNN)
- [ ] 二维码自动生成
- [ ] 净值和残值计算正确
- [ ] 软删除正常工作
- [ ] 资产服务层完整实现
- [ ] 状态变更记录日志

### API验收

- [ ] 列表API支持分页、搜索、筛选
- [ ] 创建API自动生成编码
- [ ] 更新API支持部分更新
- [ ] 删除API软删除
- [ ] 统计API返回正确数据
- [ ] 二维码API返回图片

### 前端验收

- [ ] 资产列表正确显示
- [ ] 搜索和筛选功能正常
- [ ] 新增资产表单正常
- [ ] 编辑资产表单正常
- [ ] 二维码弹窗显示正常
- [ ] 批量操作功能正常
- [ ] 统计信息正确显示

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.assets.tests

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```

---

## 性能测试

```python
# apps/assets/tests/test_performance.py

from django.test import TestCase
from apps.assets.models import Asset
from apps.assets.services.asset_service import AssetService
from apps.organizations.models import Organization
from apps.assets.models import AssetCategory


class AssetPerformanceTest(TestCase):
    """资产性能测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='计算机设备'
        )
        self.service = AssetService()

    def test_query_with_large_dataset(self):
        """测试大数据集查询性能"""
        # 创建1000条数据
        for i in range(1000):
            Asset.objects.create(
                organization=self.org,
                asset_category=self.category,
                asset_name=f'资产{i}',
                purchase_price=1000 + i,
                purchase_date='2024-01-01'
            )

        import time
        start = time.time()
        result = self.service.query_assets(page=1, page_size=20)
        elapsed = time.time() - start

        # 应在100ms内完成
        self.assertLess(elapsed, 0.1)
        self.assertEqual(len(result['items']), 20)
```
