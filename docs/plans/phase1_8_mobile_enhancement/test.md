# Phase 1.8: 移动端功能增强 - 测试计划

## 1. 测试概述

### 1.1 测试目标

- 验证离线工作模式的正确性
- 验证数据同步的完整性和一致性
- 验证冲突检测与解决机制
- 验证移动审批功能的完整性
- 验证PWA离线可用性

### 1.2 测试范围

| 模块 | 测试类型 | 优先级 |
|------|----------|--------|
| 本地数据库 | 功能、性能 | 高 |
| 数据同步 | 功能、性能、安全 | 高 |
| 冲突解决 | 功能 | 高 |
| 移动审批 | 功能、体验 | 高 |
| 设备管理 | 功能、安全 | 中 |
| PWA功能 | 功能 | 中 |

---

## 2. 后端单元测试

### 2.1 设备管理测试

**文件**: `apps/mobile/tests/test_device.py`

```python
import pytest
from django.test import TestCase
from apps.mobile.models import MobileDevice
from apps.mobile.services import DeviceService
from apps.accounts.models import User


class MobileDeviceTest(TestCase):
    """移动设备测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.org = create_test_org()

    def test_register_new_device(self):
        """测试注册新设备"""
        device_info = {
            'device_name': 'iPhone 13',
            'device_type': 'ios',
            'os_version': '16.0',
            'app_version': '1.0.0'
        }

        device = DeviceService.register_device(
            self.user,
            'device-uuid-123',
            device_info
        )

        assert device.user == self.user
        assert device.device_id == 'device-uuid-123'
        assert device.is_bound is True
        assert device.is_active is True

    def test_register_existing_device(self):
        """测试注册已存在的设备"""
        device_info = {'device_name': 'Test Device'}

        # 首次注册
        DeviceService.register_device(self.user, 'device-123', device_info)

        # 更新设备信息
        updated_info = {
            'device_name': 'Updated Device',
            'app_version': '1.0.1'
        }
        device = DeviceService.register_device(self.user, 'device-123', updated_info)

        assert device.device_name == 'Updated Device'
        assert device.app_version == '1.0.1'

    def test_unbind_device(self):
        """测试解绑设备"""
        device = DeviceService.register_device(
            self.user,
            'device-123',
            {'device_name': 'Test'}
        )

        result = DeviceService.unbind_device(self.user, 'device-123')

        assert result is True
        device.refresh_from_db()
        assert device.is_bound is False
        assert device.is_active is False

    def test_device_limit(self):
        """测试设备数量限制"""
        # 创建3个设备（达到限制）
        for i in range(3):
            DeviceService.register_device(
                self.user,
                f'device-{i}',
                {'device_name': f'Device {i}'}
            )

        # 检查是否超过限制
        assert DeviceService.check_device_limit(self.user, max_devices=3) is False

    def test_revoke_old_devices(self):
        """测试撤销旧设备"""
        # 创建5个设备
        for i in range(5):
            DeviceService.register_device(
                self.user,
                f'device-{i}',
                {'device_name': f'Device {i}'}
            )

        # 保留最近2个，撤销其他
        DeviceService.revoke_old_devices(self.user, keep_count=2)

        active_count = MobileDevice.objects.filter(
            user=self.user,
            is_bound=True
        ).count()
        assert active_count == 2
```

### 2.2 数据同步测试

**文件**: `apps/mobile/tests/test_sync.py`

```python
import pytest
from django.test import TestCase
from apps.mobile.models import OfflineData, SyncConflict
from apps.mobile.services import SyncService
from apps.accounts.models import User


class DataSyncTest(TestCase):
    """数据同步测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser')
        self.device = MobileDevice.objects.create(
            user=self.user,
            device_id='test-device',
            device_name='Test Device'
        )
        self.sync_service = SyncService(self.user, self.device)

    def test_upload_offline_data_create(self):
        """测试上传离线创建数据"""
        data_list = [{
            'table_name': 'assets.Asset',
            'record_id': 'local-1',
            'operation': 'create',
            'data': {
                'asset_no': 'ZC001',
                'asset_name': '测试资产'
            },
            'version': 1,
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'
        }]

        results = self.sync_service.upload_offline_data(data_list)

        assert results['success'] == 1
        assert results['failed'] == 0

    def test_upload_offline_data_with_conflict(self):
        """测试上传带冲突的离线数据"""
        # 先创建一条记录
        asset = create_asset(id='123', asset_no='ZC001', version=5)

        # 离线修改旧版本
        data_list = [{
            'table_name': 'assets.Asset',
            'record_id': '123',
            'operation': 'update',
            'data': {'asset_name': '修改名称'},
            'version': 3,  # 版本低于服务端
            'created_at': '2024-01-15T10:00:00Z',
            'updated_at': '2024-01-15T10:00:00Z'
        }]

        results = self.sync_service.upload_offline_data(data_list)

        assert results['conflicts'] == 1
        assert SyncConflict.objects.count() == 1

    def test_download_changes(self):
        """测试下载变更数据"""
        last_version = 1705316400
        tables = ['assets.Asset']

        changes = self.sync_service.download_changes(last_version, tables)

        assert 'assets.Asset' in changes
        assert isinstance(changes['assets.Asset'], list)

    def test_resolve_conflict_server_wins(self):
        """测试解决冲突 - 服务端优先"""
        conflict = create_sync_conflict(self.user)

        success = self.sync_service.resolve_conflict(
            conflict.id,
            'server_wins'
        )

        assert success is True
        conflict.refresh_from_db()
        assert conflict.resolution == 'server_wins'
        assert conflict.resolved_at is not None

    def test_resolve_conflict_client_wins(self):
        """测试解决冲突 - 客户端优先"""
        conflict = create_sync_conflict(self.user)

        success = self.sync_service.resolve_conflict(
            conflict.id,
            'client_wins'
        )

        assert success is True
        conflict.refresh_from_db()
        assert conflict.resolution == 'client_wins'

    def test_resolve_conflict_merge(self):
        """测试解决冲突 - 合并"""
        conflict = create_sync_conflict(self.user)
        merged_data = {
            'asset_name': '合并后的名称',
            'location': '新位置'
        }

        success = self.sync_service.resolve_conflict(
            conflict.id,
            'merge',
            merged_data
        )

        assert success is True
```

### 2.3 移动审批测试

**文件**: `apps/mobile/tests/test_approval.py`

```python
import pytest
from django.test import TestCase
from apps.mobile.services import MobileApprovalService
from apps.mobile.models import ApprovalDelegate
from apps.accounts.models import User
from apps.workflows.models import WorkflowInstance


class MobileApprovalTest(TestCase):
    """移动审批测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='approver')
        self.delegate_user = User.objects.create_user(username='delegate')
        self.workflow = create_test_workflow()

    def test_get_pending_approvals(self):
        """测试获取待审批列表"""
        # 创建待审批实例
        instance = create_workflow_instance(
            workflow=self.workflow,
            current_node='dept_approve',
            assignees=[self.user]
        )

        approvals = MobileApprovalService.get_pending_approvals(self.user)

        assert len(approvals) > 0
        assert approvals[0]['id'] == instance.id

    def test_approve_success(self):
        """测试审批同意"""
        instance = create_workflow_instance(
            workflow=self.workflow,
            current_node='dept_approve',
            assignees=[self.user]
        )

        result = MobileApprovalService.approve(
            self.user,
            instance.id,
            'approve',
            '同意'
        )

        assert result['success'] is True

    def test_approve_without_permission(self):
        """测试无权限审批"""
        other_user = User.objects.create_user(username='other')
        instance = create_workflow_instance(
            workflow=self.workflow,
            current_node='dept_approve',
            assignees=[self.user]
        )

        result = MobileApprovalService.approve(
            other_user,
            instance.id,
            'approve'
        )

        assert result['success'] is False

    def test_batch_approve(self):
        """测试批量审批"""
        instances = [
            create_workflow_instance(
                workflow=self.workflow,
                assignees=[self.user]
            ) for _ in range(3)
        ]

        result = MobileApprovalService.batch_approve(
            self.user,
            [inst.id for inst in instances],
            'approve',
            '批量同意'
        )

        assert result['success'] == 3
        assert result['failed'] == 0

    def test_delegate_approval(self):
        """测试设置审批代理"""
        from django.utils import timezone
        from datetime import timedelta

        delegate = MobileApprovalService.delegate_approval(
            self.user,
            self.delegate_user.id,
            {
                'delegate_type': 'temporary',
                'delegate_scope': 'all',
                'start_time': timezone.now(),
                'end_time': timezone.now() + timedelta(days=7),
                'reason': '出差期间'
            }
        )

        assert delegate.delegator == self.user
        assert delegate.delegate == self.delegate_user
        assert delegate.is_valid() is True

    def test_check_delegation(self):
        """测试检查代理"""
        # 设置代理
        MobileApprovalService.delegate_approval(
            self.user,
            self.delegate_user.id,
            {
                'delegate_type': 'temporary',
                'delegate_scope': 'all',
                'start_time': timezone.now()
            }
        )

        # 检查代理
        delegate = MobileApprovalService.check_delegation(self.user)

        assert delegate == self.delegate_user

    def test_delegate_expiration(self):
        """测试代理过期"""
        from django.utils import timezone
        from datetime import timedelta

        # 创建已过期的代理
        delegate = MobileApprovalService.delegate_approval(
            self.user,
            self.delegate_user.id,
            {
                'delegate_type': 'temporary',
                'start_time': timezone.now() - timedelta(days=10),
                'end_time': timezone.now() - timedelta(days=1)
            }
        )

        assert delegate.is_valid() is False
```

---

## 3. 前端组件测试

### 3.1 离线服务测试

**文件**: `src/mobile/services/__tests__/offline.service.spec.ts`

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { OfflineService } from '../offline.service'
import { db } from '@/mobile/database/schema'

describe('OfflineService', () => {
  beforeEach(async () => {
    await db.assets.clear()
    await db.inventory_scans.clear()
    await db.sync_queue.clear()
  })

  afterEach(async () => {
    await db.assets.clear()
    await db.inventory_scans.clear()
    await db.sync_queue.clear()
  })

  it('saves asset to local database', async () => {
    const asset = {
      asset_no: 'ZC001',
      asset_name: '测试资产',
      category: '电子设备',
      location: 'A区-01-01',
      status: 'normal',
      version: 1,
      updated_at: '2024-01-15T10:00:00Z'
    }

    const id = await OfflineService.saveAsset(asset)

    expect(id).toBeDefined()
    const saved = await db.assets.get(id)
    expect(saved?.asset_no).toBe('ZC001')
    expect(saved?._synced).toBe(false)
  })

  it('updates local asset', async () => {
    const asset = {
      asset_no: 'ZC001',
      asset_name: '测试资产',
      category: '电子设备',
      location: 'A区-01-01',
      status: 'normal',
      version: 1,
      updated_at: '2024-01-15T10:00:00Z'
    }

    const id = await OfflineService.saveAsset(asset)
    await OfflineService.updateAsset(id, { location: 'B区-02-02' })

    const updated = await db.assets.get(id)
    expect(updated?.location).toBe('B区-02-02')
    expect(updated?._synced).toBe(false)
  })

  it('saves inventory scan', async () => {
    const scan = {
      task_id: 'task-1',
      asset_no: 'ZC001',
      scan_time: '2024-01-15T10:30:00Z',
      location: 'A区-01-01',
      status: 'scanned'
    }

    const id = await OfflineService.saveScan(scan)

    expect(id).toBeDefined()
    const saved = await db.inventory_scans.get(id)
    expect(saved?.asset_no).toBe('ZC001')
  })

  it('gets pending sync count', async () => {
    const asset = {
      asset_no: 'ZC001',
      asset_name: '测试资产',
      category: '电子设备',
      location: 'A区-01-01',
      status: 'normal',
      version: 1,
      updated_at: '2024-01-15T10:00:00Z'
    }

    await OfflineService.saveAsset(asset)
    await OfflineService.saveScan({
      task_id: 'task-1',
      asset_no: 'ZC002',
      scan_time: '2024-01-15T10:30:00Z',
      location: 'A区-01-01',
      status: 'scanned'
    })

    const count = await OfflineService.getPendingCount()
    expect(count).toBeGreaterThan(0)
  })

  it('clears all data', async () => {
    await OfflineService.saveAsset({
      asset_no: 'ZC001',
      asset_name: '测试资产',
      category: '电子设备',
      location: 'A区-01-01',
      status: 'normal',
      version: 1,
      updated_at: '2024-01-15T10:00:00Z'
    })

    await OfflineService.clearAll()

    const count = await db.assets.count()
    expect(count).toBe(0)
  })
})
```

### 3.2 同步服务测试

**文件**: `src/mobile/services/__tests__/sync.service.spec.ts`

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SyncService } from '../sync.service'
import { api } from '@/api'

vi.mock('@/api')

describe('SyncService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('uploads offline data successfully', async () => {
    const mockResponse = {
      data: {
        success: 5,
        failed: 0,
        conflicts: 0,
        errors: [],
        server_version: 1705317000
      }
    }
    vi.mocked(api.post).mockResolvedValue(mockResponse)

    const result = await SyncService.upload()

    expect(result.success).toBe(5)
    expect(result.failed).toBe(0)
  })

  it('handles sync conflicts', async () => {
    const mockResponse = {
      data: {
        success: 3,
        failed: 0,
        conflicts: 2,
        errors: [],
        server_version: 1705317000
      }
    }
    vi.mocked(api.post).mockResolvedValue(mockResponse)

    const result = await SyncService.upload()

    expect(result.conflicts).toBe(2)
  })

  it('downloads server changes', async () => {
    const mockResponse = {
      data: {
        version: 1705317000,
        changes: {
          'assets.Asset': [
            { id: '100', asset_no: 'ZC100', asset_name: '新资产' }
          ]
        }
      }
    }
    vi.mocked(api.post).mockResolvedValue(mockResponse)

    const result = await SyncService.download()

    expect(result.version).toBe(1705317000)
    expect(result.count).toBe(1)
  })

  it('prevents concurrent sync', async () => {
    SyncService.setSyncing(true)

    await expect(SyncService.sync()).rejects.toThrow('同步正在进行中')
  })
})
```

### 3.3 审批服务测试

**文件**: `src/mobile/services/__tests__/approval.service.spec.ts`

```typescript
import { describe, it, expect, vi } from 'vitest'
import { ApprovalService } from '../approval.service'
import { api } from '@/api'

vi.mock('@/api')

describe('ApprovalService', () => {
  it('gets pending approvals', async () => {
    const mockResponse = {
      data: {
        results: [
          {
            id: 100,
            title: '资产采购申请',
            workflow_name: '采购流程',
            current_node: '部门审批',
            urgent: true
          }
        ]
      }
    }
    vi.mocked(api.get).mockResolvedValue(mockResponse)

    const approvals = await ApprovalService.getPending()

    expect(approvals.length).toBe(1)
    expect(approvals[0].title).toBe('资产采购申请')
  })

  it('approves workflow instance', async () => {
    const mockResponse = {
      data: {
        success: true,
        message: '审批成功'
      }
    }
    vi.mocked(api.post).mockResolvedValue(mockResponse)

    const result = await ApprovalService.approve(100, 'approve', '同意')

    expect(result.success).toBe(true)
  })

  it('batch approves multiple instances', async () => {
    const mockResponse = {
      data: {
        success: 3,
        failed: 0,
        errors: []
      }
    }
    vi.mocked(api.post).mockResolvedValue(mockResponse)

    const result = await ApprovalService.batchApprove(
      [100, 101, 102],
      'approve',
      '批量同意'
    )

    expect(result.success).toBe(3)
  })
})
```

---

## 4. E2E测试

### 4.1 离线工作E2E测试

**文件**: `tests/mobile/e2e/offline.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Offline Work', () => {
  test.beforeEach(async ({ page }) => {
    // 模拟离线状态
    await page.context().setOffline(true)
  })

  test('can scan asset offline', async ({ page }) => {
    await page.goto('/mobile/inventory/scan')

    // 模拟扫码
    await page.fill('[placeholder="请输入或扫描资产编号"]', 'ZC001')
    await page.click('button:has-text("确认")')

    // 验证数据保存到本地
    const scanCount = await page.evaluate(() => {
      return window.localDB.inventory_scans.count()
    })

    expect(scanCount).toBeGreaterThan(0)
  })

  test('shows offline banner when offline', async ({ page }) => {
    await page.goto('/mobile/home')

    const banner = page.locator('.offline-banner')
    await expect(banner).toBeVisible()
    await expect(banner).toContainText('离线状态')
  })

  test('syncs data when online', async ({ page }) => {
    // 先离线操作
    await page.context().setOffline(true)
    await page.goto('/mobile/inventory/scan')

    await page.fill('[placeholder="请输入或扫描资产编号"]', 'ZC001')
    await page.click('button:has-text("确认")')

    // 恢复在线
    await page.context().setOffline(false)

    // 点击同步按钮
    await page.click('.sync-indicator')

    // 验证同步成功提示
    await expect(page.locator('.van-toast')).toContainText('同步成功')
  })
})
```

### 4.2 移动审批E2E测试

**文件**: `tests/mobile/e2e/approval.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Mobile Approval', () => {
  test('shows pending approval list', async ({ page }) => {
    await page.goto('/mobile/approval')

    await expect(page.locator('text=待审批')).toBeVisible()
    await expect(page.locator('.van-cell').first()).toBeVisible()
  })

  test('approves single item', async ({ page }) => {
    await page.goto('/mobile/approval')

    // 点击第一个待审批项
    await page.click('.van-cell:first-child')

    // 点击同意按钮
    await page.click('button:has-text("同意")')

    // 输入审批意见
    await page.fill('.van-field__control', '同意申请')
    await page.click('button:has-text("确认")')

    // 验证审批成功
    await expect(page.locator('.van-toast')).toContainText('审批成功')
  })

  test('batch approves items', async ({ page }) => {
    await page.goto('/mobile/approval')

    // 选择多个项目
    await page.check('.van-checkbox:first-child')
    await page.check('.van-checkbox:nth-child(2)')

    // 点击批量同意
    await page.click('button:has-text("批量同意")')

    // 确认批量操作
    await page.click('.van-dialog__confirm:has-text("确认")')

    // 验证成功
    await expect(page.locator('.van-toast')).toContainText('成功')
  })

  test('shows approval detail with flow chart', async ({ page }) => {
    await page.goto('/mobile/approval')
    await page.click('.van-cell:first-child')

    // 验证流程图
    await expect(page.locator('.van-steps')).toBeVisible()
    await expect(page.locator('.van-step')).toHaveCount(3)
  })
})
```

### 4.3 PWA功能测试

**文件**: `tests/mobile/e2e/pwa.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('PWA Features', () => {
  test('installs service worker', async ({ page }) => {
    await page.goto('/mobile/')

    // 检查Service Worker
    const swStatus = await page.evaluate(() => {
      return navigator.serviceWorker.ready.then(() => true).catch(() => false)
    })

    expect(swStatus).toBe(true)
  })

  test('shows install prompt', async ({ page }) => {
    // 模拟安装事件
    await page.goto('/mobile/')

    const canInstall = await page.evaluate(() => {
      return window.hasOwnProperty('beforeinstallprompt')
    })

    // 验证PWA清单
    const manifest = await page.evaluate(() => {
      return fetch('/manifest.json').then(r => r.json())
    })

    expect(manifest.name).toBe('钩子固定资产')
    expect(manifest.display).toBe('standalone')
  })

  test('works offline after first load', async ({ page }) => {
    // 首次加载
    await page.goto('/mobile/')
    await page.waitForLoadState('networkidle')

    // 离线访问
    await page.context().setOffline(true)
    await page.reload()

    // 验证页面仍然可用
    await expect(page.locator('.home-page')).toBeVisible()
  })
})
```

---

## 5. 性能测试

### 5.1 本地数据库性能

```typescript
import { describe, it, expect } from 'vitest'
import { OfflineService } from '@/mobile/services/offline.service'

describe('Performance Tests', () => {
  it('inserts 1000 assets in acceptable time', async () => {
    const startTime = Date.now()

    for (let i = 0; i < 1000; i++) {
      await OfflineService.saveAsset({
        asset_no: `ZC${String(i).padStart(4, '0')}`,
        asset_name: `资产${i}`,
        category: '电子设备',
        location: 'A区',
        status: 'normal',
        version: 1,
        updated_at: new Date().toISOString()
      })
    }

    const duration = Date.now() - startTime
    expect(duration).toBeLessThan(5000) // 5秒内完成
  })

  it('queries 10000 records efficiently', async () => {
    // 先插入数据
    for (let i = 0; i < 10000; i++) {
      await db.assets.put({
        id: `asset-${i}`,
        asset_no: `ZC${String(i).padStart(4, '0')}`,
        asset_name: `资产${i}`,
        category: i % 3 === 0 ? '电子设备' : '办公家具',
        location: `A区-${Math.floor(i / 100)}`,
        status: 'normal',
        _synced: true
      })
    }

    const startTime = Date.now()
    const results = await OfflineService.getAssets()
    const duration = Date.now() - startTime

    expect(results.length).toBe(10000)
    expect(duration).toBeLessThan(1000) // 1秒内完成查询
  })
})
```

---

## 6. 网络模拟测试

```typescript
import { describe, it, expect, vi } from 'vitest'
import { SyncService } from '@/mobile/services/sync.service'

describe('Network Tests', () => {
  it('queues operations when offline', async () => {
    // 模拟离线状态
    vi.mock('@/utils/network', () => ({
      isOnline: () => false
    }))

    await OfflineService.saveAsset({
      asset_no: 'ZC001',
      asset_name: '离线资产',
      category: '电子设备',
      location: 'A区',
      status: 'normal',
      version: 1,
      updated_at: new Date().toISOString()
    })

    const queueCount = await db.sync_queue.count()
    expect(queueCount).toBe(1)
  })

  it('syncs automatically when online', async () => {
    let onlineStatus = false

    vi.mock('@/utils/network', () => ({
      isOnline: () => onlineStatus,
      onOnline: (callback) => {
        // 模拟网络恢复
        setTimeout(() => {
          onlineStatus = true
          callback()
        }, 100)
      }
    }))

    // 监听同步事件
    const syncSpy = vi.fn()
    SyncService.on('sync', syncSpy)

    // 模拟离线操作
    await OfflineService.saveAsset({
      asset_no: 'ZC001',
      asset_name: '离线资产',
      category: '电子设备',
      location: 'A区',
      status: 'normal',
      version: 1,
      updated_at: new Date().toISOString()
    })

    // 模拟网络恢复
    // ...

    // 验证自动同步
    await new Promise(resolve => setTimeout(resolve, 500))
    expect(syncSpy).toHaveBeenCalled()
  })
})
```

---

## 7. 测试执行计划

### 7.1 单元测试

| 模块 | 测试文件 | 覆盖率目标 |
|------|----------|------------|
| 本地数据库 | offline.service.spec.ts | 90% |
| 同步服务 | sync.service.spec.ts | 85% |
| 审批服务 | approval.service.spec.ts | 85% |
| 设备服务 | device.service.spec.ts | 80% |

### 7.2 集成测试

| 场景 | 测试文件 |
|------|----------|
| 离线-在线切换 | offline-switch.spec.ts |
| 数据同步 | data-sync.spec.ts |
| 冲突解决 | conflict-resolution.spec.ts |

### 7.3 E2E测试

| 场景 | 测试文件 | 设备 |
|------|----------|------|
| 离线盘点 | offline-inventory.spec.ts | 真机/模拟器 |
| 移动审批 | mobile-approval.spec.ts | 真机/模拟器 |
| PWA安装 | pwa-install.spec.ts | 真机 |

---

## 8. 测试通过标准

1. **单元测试**: 代码覆盖率 >= 85%
2. **集成测试**: 所有核心流程可正常执行
3. **E2E测试**: 真机测试通过
4. **性能测试**: 1000条数据插入 < 5秒
5. **离线测试**: 离线状态下数据可正常保存和读取
6. **同步测试**: 在线后数据可正常同步
