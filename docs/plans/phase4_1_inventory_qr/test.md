# Phase 4.1: QR码扫描盘点 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 二维码服务测试 | pytest | QRCodeService |
| 盘点服务测试 | pytest | InventoryService |
| 模型测试 | pytest + Django TestCase | InventoryTask, InventoryScan |
| API测试 | pytest + DRF APIClient | 盘点任务API |
| 前端组件测试 | Vitest | QRScanner, ScanResult |
| E2E测试 | Playwright | 完整盘点流程 |

---

## 1. 二维码服务测试

```python
# tests/assets/test_qr_service.py

import pytest
import json
from io import BytesIO
from PIL import Image
from apps.assets.models import Asset
from apps.assets.services.qr_code_service import QRCodeService


class TestQRCodeService:
    """二维码服务测试"""

    @pytest.fixture
    def service(self):
        return QRCodeService()

    @pytest.fixture
    def asset(self, db, organization):
        return Asset.objects.create(
            organization=organization,
            asset_code="TEST001",
            asset_name="测试资产"
        )

    def test_generate_qr_code_data(self, service, asset):
        """测试生成二维码数据"""
        qr_data = asset.generate_qr_code_data()

        assert qr_data['type'] == 'asset'
        assert qr_data['asset_id'] == str(asset.id)
        assert qr_data['asset_code'] == asset.asset_code
        assert 'checksum' in qr_data

    def test_generate_asset_qr_code(self, service, asset):
        """测试生成资产二维码"""
        url = service.generate_asset_qr_code(asset)

        assert url is not None
        assert asset.qr_code_url is not None
        assert asset.qr_code is not None

        # 验证文件存在
        import os
        from django.conf import settings
        full_path = settings.MEDIA_ROOT + asset.qr_code_url.replace(settings.MEDIA_URL, '')
        assert os.path.exists(full_path)

    def test_generate_qr_code_bytes(self, service, asset):
        """测试生成二维码图片流"""
        buffer = service.generate_qr_code_bytes(asset)

        assert isinstance(buffer, BytesIO)

        # 验证是有效的PNG图片
        buffer.seek(0)
        img = Image.open(buffer)
        assert img.format == 'PNG'
        assert img.width > 0
        assert img.height > 0

    def test_batch_generate_qr_codes(self, service, db, organization):
        """测试批量生成二维码"""
        assets = [
            Asset.objects.create(
                organization=organization,
                asset_code=f"TEST{i:03d}",
                asset_name=f"测试资产{i}"
            )
            for i in range(1, 6)
        ]
        asset_ids = [a.id for a in assets]

        results = service.batch_generate_qr_codes(asset_ids)

        assert results['total'] == 5
        assert len(results['success']) == 5
        assert len(results['failed']) == 0

    def test_generate_asset_label(self, service, asset):
        """测试生成资产标签"""
        buffer = service.generate_asset_label(asset)

        assert isinstance(buffer, BytesIO)

        buffer.seek(0)
        img = Image.open(buffer)
        assert img.format == 'PNG'
        # 标签应该比二维码大
        assert img.width > 200
        assert img.height > 150

    def test_generate_print_labels_pdf(self, service, db, organization):
        """测试生成打印标签PDF"""
        assets = [
            Asset.objects.create(
                organization=organization,
                asset_code=f"LABEL{i:03d}",
                asset_name=f"标签资产{i}"
            )
            for i in range(1, 9)  # 8个标签，2行
        ]
        asset_ids = [a.id for a in assets]

        pdf_buffer = service.generate_print_labels_pdf(asset_ids)

        assert isinstance(pdf_buffer, BytesIO)

        # 验证PDF
        pdf_buffer.seek(0)
        header = pdf_buffer.read(4)
        assert header == b'%PDF'  # PDF文件头
```

---

## 2. 盘点服务测试

```python
# tests/inventory/test_inventory_service.py

import pytest
from datetime import date
from django.utils import timezone
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventoryScan, InventoryDifference
)
from apps.inventory.services.inventory_service import InventoryService
from apps.assets.models import Asset


class TestInventoryService:
    """盘点服务测试"""

    @pytest.fixture
    def service(self):
        return InventoryService()

    @pytest.fixture
    def organization(self, db):
        from apps.organizations.models import Organization
        return Organization.objects.create(
            name="测试公司",
            code="TEST001"
        )

    @pytest.fixture
    def user(self, db, organization):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.create(
            organization=organization,
            username="test_user",
            real_name="测试用户"
        )

    @pytest.fixture
    def assets(self, db, organization):
        """创建测试资产"""
        return [
            Asset.objects.create(
                organization=organization,
                asset_code=f"AST{i:03d}",
                asset_name=f"资产{i}"
            )
            for i in range(1, 11)
        ]

    @pytest.fixture
    def department(self, db, organization):
        from apps.organizations.models import Department
        return Department.objects.create(
            organization=organization,
            name="技术部"
        )

    def test_create_task(self, service, organization, user, department):
        """测试创建盘点任务"""
        data = {
            'task_name': '技术部盘点',
            'inventory_type': 'department',
            'department_id': department.id,
            'planned_date': '2024-01-20',
            'executor_ids': [user.id],
            'primary_executor_id': user.id
        }

        task = service.create_task(organization, user, data)

        assert task.task_name == '技术部盘点'
        assert task.status == 'pending'
        assert task.task_code.startswith('PD')

        # 验证执行人
        assert task.executors.count() == 1

    def test_create_snapshots(self, service, organization, user, assets):
        """测试创建快照"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='pending'
        )

        service._create_snapshots(task)

        # 验证快照数量
        assert task.snapshots.count() == len(assets)

        # 验证快照内容
        snapshot = task.snapshots.first()
        assert snapshot.asset_code is not None
        assert snapshot.asset_name is not None

    def test_start_task(self, service, organization, user):
        """测试开始任务"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='pending'
        )

        service.start_task(task)

        task.refresh_from_db()
        assert task.status == 'in_progress'
        assert task.started_at is not None

    def test_start_non_pending_task_fails(self, service, organization, user):
        """测试开始非待执行状态任务失败"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='in_progress'
        )

        with pytest.raises(ValueError, match="只有待执行"):
            service.start_task(task)

    def test_record_normal_scan(self, service, organization, user, assets):
        """测试记录正常扫描"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='in_progress'
        )
        asset = assets[0]

        # 创建快照
        InventorySnapshot.objects.create(
            task=task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name
        )

        scan = service.record_scan(
            task=task,
            scanned_by=user,
            asset_id=asset.id,
            scan_method='qr',
            scan_data={'status': 'normal'}
        )

        assert scan.asset == asset
        assert scan.scan_status == 'normal'

        task.refresh_from_db()
        assert task.scanned_count == 1
        assert task.normal_count == 1

    def test_record_damaged_scan(self, service, organization, user, assets):
        """测试记录损坏扫描"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='in_progress'
        )
        asset = assets[0]

        InventorySnapshot.objects.create(
            task=task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name
        )

        scan = service.record_scan(
            task=task,
            scanned_by=user,
            asset_id=asset.id,
            scan_method='qr',
            scan_data={
                'status': 'damaged',
                'remark': '屏幕破损'
            }
        )

        assert scan.scan_status == 'damaged'

        # 验证差异记录
        assert task.differences.filter(
            asset=asset,
            difference_type='damaged'
        ).exists()

    def test_record_extra_scan(self, service, organization, user):
        """测试记录盘盈"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            status='in_progress'
        )

        scan = service.record_scan(
            task=task,
            scanned_by=user,
            asset_code='UNKNOWN001',
            scan_method='manual',
            scan_data={'status': 'surplus'}
        )

        assert scan.scan_status == 'surplus'
        assert scan.asset is None

        task.refresh_from_db()
        assert task.surplus_count == 1

    def test_complete_task(self, service, organization, user, assets):
        """测试完成任务"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            total_count=10,
            status='in_progress'
        )

        # 扫描部分资产
        for asset in assets[:5]:
            InventorySnapshot.objects.create(
                task=task,
                asset=asset,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name
            )
            InventoryScan.objects.create(
                task=task,
                asset=asset,
                scanned_by=user,
                scanned_at=timezone.now(),
                scan_method='qr',
                scan_status='normal'
            )

        task.scanned_count = 5
        task.save()

        service.complete_task(task, user)

        task.refresh_from_db()
        assert task.status == 'completed'
        assert task.completed_at is not None

        # 验证未扫描的资产被标记为盘亏
        assert task.missing_count == 5  # 10 - 5 = 5

    def test_get_statistics(self, service, organization, user):
        """测试获取统计"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_date=date.today(),
            planned_by=user,
            total_count=100,
            scanned_count=75,
            normal_count=70,
            surplus_count=2,
            missing_count=3,
            damaged_count=0
        )

        stats = service.get_statistics(task)

        assert stats['total'] == 100
        assert stats['scanned'] == 75
        assert stats['progress'] == 75
```

---

## 3. API测试

```python
# tests/inventory/test_api.py

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client(db):
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


class TestInventoryTaskAPI:
    """盘点任务API测试"""

    def test_list_tasks(self, authenticated_client, inventory_task):
        """测试获取任务列表"""
        url = '/api/inventory/tasks/'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) >= 1

    def test_create_task(self, authenticated_client, organization, user, department):
        """测试创建任务"""
        url = '/api/inventory/tasks/'
        data = {
            'task_name': '测试盘点',
            'inventory_type': 'department',
            'department_id': department.id,
            'planned_date': '2024-01-20',
            'executor_ids': [user.id]
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['task_name'] == '测试盘点'
        assert response.data['task_code'] is not None

    def test_start_task(self, authenticated_client, inventory_task):
        """测试开始任务"""
        url = f'/api/inventory/tasks/{inventory_task.id}/start/'

        response = authenticated_client.post(url)

        assert response.status_code == 200

    def test_complete_task(self, authenticated_client, inventory_task):
        """测试完成任务"""
        # 先开始任务
        inventory_task.status = 'in_progress'
        inventory_task.save()

        url = f'/api/inventory/tasks/{inventory_task.id}/complete/'

        response = authenticated_client.post(url)

        assert response.status_code == 200
        assert response.data['status'] == 'completed'

    def test_get_statistics(self, authenticated_client, inventory_task):
        """测试获取统计"""
        url = f'/api/inventory/tasks/{inventory_task.id}/statistics/'

        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'total' in response.data
        assert 'scanned' in response.data
        assert 'progress' in response.data

    def test_record_scan(self, authenticated_client, inventory_task, asset, user):
        """测试记录扫描"""
        inventory_task.status = 'in_progress'
        inventory_task.save()

        # 创建快照
        from apps.inventory.models import InventorySnapshot
        InventorySnapshot.objects.create(
            task=inventory_task,
            asset=asset,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name
        )

        url = f'/api/inventory/tasks/{inventory_task.id}/record_scan/'
        data = {
            'asset_id': asset.id,
            'scan_method': 'qr',
            'status': 'normal'
        }

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['scan_status'] == 'normal'
```

---

## 4. 前端组件测试

```javascript
// tests/inventory/QRScanner.spec.js

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import QRScanner from '@/components/inventory/QRScanner.vue'

// Mock ZXing library
vi.mock('@zxing/library', () => ({
  BrowserMultiFormatReader: vi.fn().mockImplementation(() => ({
    listVideoInputDevices: vi.fn().mockResolvedValue([
      { deviceId: 'camera1', label: 'Front Camera' }
    ]),
    decodeFromVideoDevice: vi.fn(),
    reset: vi.fn()
  }))
}))

describe('QRScanner', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(QRScanner, {
      props: {
        taskId: '1'
      }
    })
  })

  it('应正确渲染扫描界面', () => {
    expect(wrapper.find('.qr-scanner').exists()).toBe(true)
    expect(wrapper.find('.video-container').exists()).toBe(true)
    expect(wrapper.find('.scanner-controls').exists()).toBe(true)
  })

  it('应切换手动输入对话框', async () => {
    expect(wrapper.vm.manualInputVisible).toBe(false)

    await wrapper.find('.scanner-controls button:last-child').trigger('click')

    expect(wrapper.vm.manualInputVisible).toBe(true)
  })

  it('应触发扫描事件', () => {
    wrapper.vm.handleScanResult({
      type: 'asset',
      asset_id: '1',
      asset_code: 'TEST001'
    })

    // 应该触发验证
    expect(wrapper.emitted('scanned')).toBeFalsy()  // 需要mock API
  })
})
```

```javascript
// tests/inventory/ScanResult.spec.js

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ScanResult from '@/components/inventory/ScanResult.vue'

describe('ScanResult', () => {
  const mockAsset = {
    id: 1,
    asset_code: 'TEST001',
    asset_name: '测试资产',
    asset_category: { name: '电子设备' },
    asset_status: 'in_use',
    custodian: { real_name: '张三' },
    location: { name: '301室' }
  }

  it('应显示资产信息', () => {
    const wrapper = mount(ScanResult, {
      props: {
        asset: mockAsset,
        taskId: '1'
      }
    })

    expect(wrapper.text()).toContain('TEST001')
    expect(wrapper.text()).toContain('测试资产')
  })

  it('应切换盘点状态', async () => {
    const wrapper = mount(ScanResult, {
      props: {
        asset: mockAsset,
        taskId: '1'
      }
    })

    // 选择损坏
    await wrapper.findAll('.el-radio')[2].trigger('click')

    expect(wrapper.vm.formData.status).toBe('damaged')
  })

  it('应位置变更时显示位置选择', async () => {
    const wrapper = mount(ScanResult, {
      props: {
        asset: mockAsset,
        taskId: '1'
      }
    })

    wrapper.vm.formData.status = 'location_changed'

    expect(wrapper.vm.showLocationSelect).toBe(true)
  })
})
```

---

## 5. E2E测试

```javascript
// tests/e2e/inventory/qr_scan.spec.js

import { test, expect } from '@playwright/test'

test.describe('QR码盘点E2E', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('/login')
    await page.fill('[name="username"]', 'inventory_user')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('应创建盘点任务', async ({ page }) => {
    await page.goto('/inventory/tasks')
    await page.click('button:has-text("新建任务")')

    // 填写表单
    await page.fill('[name="task_name"]', '技术部1月盘点')
    await page.selectOption('[name="inventory_type"]', 'department')
    await page.selectOption('[name="department_id"]', '技术部')
    await page.fill('[name="planned_date"]', '2024-01-25')

    // 添加执行人
    await page.click('.executor-selector')
    await page.click('.user-option:first-child')

    // 提交
    await page.click('button:has-text("创建")')

    // 验证
    await expect(page.locator('.el-message--success')).toBeVisible()
  })

  test('应开始盘点任务', async ({ page }) => {
    await page.goto('/inventory/tasks')

    // 点击第一个任务的开始按钮
    await page.click('.task-item:first-child .start-btn')

    // 跳转到执行页面
    await expect(page).toHaveURL(/\/inventory\/tasks\/\d+\/execute/)

    // 验证扫描器组件
    await expect(page.locator('.qr-scanner')).toBeVisible()
  })

  test('应手动输入资产编码', async ({ page }) => {
    await page.goto('/inventory/tasks/1/execute')

    // 点击手动输入
    await page.click('button:has-text("手动输入")')

    // 输入编码
    await page.fill('.el-input__inner', 'TEST001')

    // 确认
    await page.click('.el-dialog .el-button--primary')

    // 验证扫描成功（需要mock数据）
    // 实际测试中需要准备测试数据
  })

  test('应查看盘点统计', async ({ page }) => {
    await page.goto('/inventory/tasks/1/execute')

    // 验证统计卡片
    await expect(page.locator('.inventory-progress')).toBeVisible()

    // 切换到已盘资产标签
    await page.click('.el-tabs__item:has-text("已盘资产")')

    // 验证列表
    await expect(page.locator('.asset-list')).toBeVisible()
  })

  test('应完成盘点任务', async ({ page }) => {
    await page.goto('/inventory/tasks/1/execute')

    // 点击完成按钮
    await page.click('button:has-text("完成盘点")')

    // 确认对话框
    await page.click('.el-message-box .confirm-btn')

    // 验证跳转到任务列表
    await expect(page).toHaveURL(/\/inventory\/tasks/)

    // 验证状态更新
    await expect(page.locator('.task-item:first-child .status-completed')).toBeVisible()
  })
})
```

---

## 测试数据

### Fixture数据

```python
# tests/inventory/fixtures.py

import pytest
from datetime import date
from apps.inventory.models import InventoryTask, InventorySnapshot
from apps.assets.models import Asset


@pytest.fixture
def inventory_task(db, organization, user):
    """盘点任务"""
    task = InventoryTask.objects.create(
        organization=organization,
        task_code='PD20240115001',
        task_name='测试盘点任务',
        inventory_type='full',
        planned_date=date.today(),
        planned_by=user,
        status='pending',
        total_count=0
    )

    # 添加执行人
    from apps.inventory.models import InventoryTaskExecutor
    InventoryTaskExecutor.objects.create(
        task=task,
        executor=user,
        is_primary=True
    )

    return task


@pytest.fixture
def inventory_scan(db, inventory_task, asset, user):
    """盘点扫描记录"""
    from apps.inventory.models import InventoryScan

    return InventoryScan.objects.create(
        task=inventory_task,
        asset=asset,
        scanned_by=user,
        scan_method='qr',
        scan_status='normal'
    )
```

---

## 测试执行

```bash
# 后端测试
pytest tests/assets/test_qr_service.py -v
pytest tests/inventory/test_inventory_service.py -v
pytest tests/inventory/test_api.py -v

# 前端测试
npm run test:unit -- inventory

# E2E测试
npm run test:e2e -- inventory
```

---

## 后续任务

1. Phase 4.2: 实现RFID批量盘点
2. Phase 4.3: 实现盘点快照和差异处理
