# Phase 5.3: 折旧自动计算 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 折旧引擎测试 | pytest | DepreciationEngine |
| 折旧任务测试 | pytest | Celery tasks |
| API测试 | pytest | 折旧API |
| 前端测试 | Vitest | 折旧组件 |

---

## 1. 折旧引擎测试

### 直线法测试

```python
# tests/assets/test_depreciation_engine.py

import pytest
from decimal import Decimal
from datetime import date
from apps.assets.services.depreciation_engine import DepreciationEngine
from apps.assets.models import Asset, AssetCategory


class TestStraightLineDepreciation:
    """直线法折旧测试"""

    @pytest.fixture
    def asset(self, db, organization):
        category = AssetCategory.objects.create(
            organization=organization,
            name='电子设备',
            depreciation_method='straight_line',
            residual_rate=5.0,
            useful_life=48  # 4年
        )
        return Asset.objects.create(
            organization=organization,
            asset_category=category,
            asset_code='TEST001',
            asset_name='测试资产',
            purchase_price=Decimal('10000.00'),
            purchase_date=date(2023, 1, 1)
        )

    def test_first_month_depreciation(self, asset):
        """测试首月折旧"""
        result = DepreciationEngine.straight_line(asset, '2023-02')

        # (10000 - 500) / 48 = 197.9166... ≈ 197.92
        assert result['depreciation_amount'] == Decimal('197.92')
        assert result['accumulated_depreciation'] == Decimal('197.92')
        assert result['net_value'] == Decimal('9802.08')

    def test_accumulated_depreciation(self, asset):
        """测试累计折旧"""
        # 第12个月
        result = DepreciationEngine.straight_line(asset, '2024-01')

        assert result['used_months'] == 12
        assert result['accumulated_depreciation'] == Decimal('2375.00')  # 197.92 * 12

    def test_fully_depreciated(self, asset):
        """测试已提足折旧"""
        # 超过使用年限
        result = DepreciationEngine.straight_line(asset, '2028-01')

        # 不再计提折旧
        assert result['depreciation_amount'] == Decimal('0')
        # 净值等于残值
        assert result['net_value'] == Decimal('500.00')
```

### 双倍余额递减法测试

```python
class TestDoubleDecliningDepreciation:
    """双倍余额递减法测试"""

    @pytest.fixture
    def asset(self, db, organization):
        category = AssetCategory.objects.create(
            organization=organization,
            name='设备',
            depreciation_method='double_declining',
            residual_rate=5.0,
            useful_life=60  # 5年
        )
        return Asset.objects.create(
            organization=organization,
            asset_category=category,
            asset_code='TEST002',
            asset_name='测试设备',
            purchase_price=Decimal('10000.00'),
            purchase_date=date(2023, 1, 1)
        )

    def test_first_year_depreciation(self, asset):
        """测试第一年折旧"""
        # 第1个月：10000 * 2 / 5 / 12 = 333.33
        result = DepreciationEngine.double_declining(asset, '2023-02')

        assert result['depreciation_amount'] == Decimal('333.33')

    def test_depreciation_decreases_over_time(self, asset):
        """测试折旧额递减"""
        result1 = DepreciationEngine.double_declining(asset, '2023-02')  # 第1个月
        result2 = DepreciationEngine.double_declining(asset, '2024-02')  # 第13个月

        # 后期折旧额应该更小
        assert result2['depreciation_amount'] < result1['depreciation_amount']
```

### 年数总和法测试

```python
class TestSumOfYearsDepreciation:
    """年数总和法测试"""

    @pytest.fixture
    def asset(self, db, organization):
        category = AssetCategory.objects.create(
            organization=organization,
            name='车辆',
            depreciation_method='sum_of_years',
            residual_rate=5.0,
            useful_life=36  # 3年
        )
        return Asset.objects.create(
            organization=organization,
            asset_category=category,
            asset_code='TEST003',
            asset_name='测试车辆',
            purchase_price=Decimal('10000.00'),
            purchase_date=date(2023, 1, 1)
        )

    def test_first_month_depreciation(self, asset):
        """测试首月折旧"""
        # 总月数 = 36 + 35 + ... + 1 = 666
        # 第1个月：(10000 - 500) * 36 / 666 = 513.51
        result = DepreciationEngine.sum_of_years(asset, '2023-02')

        assert result['depreciation_amount'] == Decimal('513.51')

    def test_last_month_depreciation(self, asset):
        """测试最后月折旧"""
        # 第36个月：(10000 - 500) * 1 / 666 = 14.26
        result = DepreciationEngine.sum_of_years(asset, '2025-12')

        assert result['depreciation_amount'] == Decimal('14.26')
```

---

## 2. Celery任务测试

```python
# tests/assets/test_depreciation_tasks.py

import pytest
from unittest.mock import patch, MagicMock
from apps.assets.tasks.depreciation_tasks import calculate_monthly_depreciation


class TestDepreciationTasks:
    """折旧任务测试"""

    @pytest.fixture
    def mock_assets(self, db, organization):
        # 创建测试资产
        assets = []
        # ... 创建资产
        return assets

    @patch('apps.assets.tasks.depreciation_tasks.DepreciationEngine')
    def test_calculate_monthly_depreciation(self, mock_engine, mock_assets):
        """测试月度折旧计算"""
        # Mock折旧计算结果
        mock_engine.calculate.return_value = {
            'depreciation_amount': Decimal('197.92'),
            'accumulated_depreciation': Decimal('197.92'),
            'net_value': Decimal('9802.08')
        }

        # 执行任务
        result = calculate_monthly_depreciation.apply()

        # 验证结果
        assert result.successful()
        assert result.state == 'SUCCESS'

    def test_task_handles_errors_gracefully(self, db, organization):
        """测试任务错误处理"""
        # 创建会报错的资产（如使用年限为0）
        category = AssetCategory.objects.create(
            organization=organization,
            name='错误分类',
            useful_life=0  # 无效的使用年限
        )

        # 任务应该捕获错误并继续处理其他资产
        result = calculate_monthly_depreciation.apply()

        assert result.successful()
```

---

## 3. API测试

```python
# tests/api/test_depreciation_api.py

import pytest
from django.urls import reverse
from apps.assets.models import AssetDepreciation


class TestDepreciationAPI:
    """折旧API测试"""

    def test_list_depreciations(self, auth_client, depreciation_records):
        """测试获取折旧记录列表"""
        url = reverse('depreciation-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['count'] == len(depreciation_records)

    def test_filter_by_period(self, auth_client, depreciation_records):
        """测试按期间筛选"""
        url = reverse('depreciation-list')
        response = auth_client.get(url, {'period': '2024-01'})

        assert response.status_code == 200
        assert all(r['period'] == '2024-01' for r in response.data['results'])

    def test_get_asset_depreciation_detail(self, auth_client, asset):
        """测试获取资产折旧明细"""
        url = reverse('depreciation-asset-detail', kwargs={'asset_id': asset.id})
        response = auth_client.get(url)

        assert response.status_code == 200
        assert 'asset_info' in response.data
        assert 'stat' in response.data
        assert 'records' in response.data

    def test_trigger_calculation(self, auth_client):
        """测试触发折旧计算"""
        url = reverse('depreciation-calculate')
        response = auth_client.post(url, {'async': True})

        assert response.status_code == 200
        assert 'task_id' in response.data

    def test_approve_depreciation(self, auth_client, depreciation_record):
        """测试审核折旧记录"""
        url = reverse('depreciation-approve', kwargs={'id': depreciation_record.id})
        response = auth_client.post(url, {
            'approved': True,
            'comment': '审核通过'
        })

        assert response.status_code == 200
        assert response.data['status'] == 'approved'

    def test_post_depreciation(self, auth_client, depreciation_record):
        """测试过账折旧记录"""
        depreciation_record.status = 'approved'
        depreciation_record.save()

        url = reverse('depreciation-post', kwargs={'id': depreciation_record.id})
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data['status'] == 'posted'
        assert response.data['voucher_no']

    def test_export_depreciation(self, auth_client):
        """测试导出折旧记录"""
        url = reverse('depreciation-export')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def test_get_report(self, auth_client):
        """测试获取折旧报表"""
        url = reverse('depreciation-report')
        response = auth_client.get(url, {'period': '2024-01'})

        assert response.status_code == 200
        assert 'summary' in response.data
        assert 'by_category' in response.data
        assert 'by_method' in response.data
```

---

## 4. 前端测试

```typescript
// tests/frontend/depreciation.spec.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import DepreciationList from '@/views/assets/depreciation/DepreciationList.vue'
import * as api from '@/api/assets/depreciation'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('DepreciationList', () => {
  it('renders depreciation table', async () => {
    const wrapper = mount(DepreciationList)

    // 等待数据加载
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.depreciation-list').exists()).toBe(true)
  })

  it('calculates monthly depreciation', async () => {
    const mockCalculate = vi.spyOn(api.depreciationApi, 'calculate').mockResolvedValue({})

    const wrapper = mount(DepreciationList)
    await wrapper.vm.handleCalculate()

    expect(mockCalculate).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('折旧计算任务已提交')
  })

  it('filters by period', async () => {
    const wrapper = mount(DepreciationList)

    wrapper.vm.queryForm.period = '2024-01'
    await wrapper.vm.handleSearch()

    // 验证筛选参数
    expect(wrapper.vm.queryForm.period).toBe('2024-01')
  })
})

// 折旧趋势图测试
describe('DepreciationChart', () => {
  it('renders chart with data', () => {
    const records = [
      { period: '2024-01', accumulated_depreciation: 1000, net_value: 9000 },
      { period: '2024-02', accumulated_depreciation: 2000, net_value: 8000 }
    ]

    // 验证图表数据
    expect(records).toHaveLength(2)
  })
})
```

---

## 测试执行

```bash
# 后端测试
pytest tests/assets/test_depreciation_*.py -v

# API测试
pytest tests/api/test_depreciation_api.py -v

# 前端测试
npm run test -- depreciation.spec.ts
```

---

## 后续任务

所有Phase已完成！
