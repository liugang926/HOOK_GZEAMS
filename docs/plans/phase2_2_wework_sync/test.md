# Phase 2.2: 企业微信通讯录同步 - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 同步服务、Celery任务 | P0 |
| API测试 | 同步接口 | P0 |
| 集成测试 | 企业微信API交互 | P1 |
| E2E测试 | 前端同步流程 | P1 |

---

## 1. 后端单元测试

### 1.1 同步服务测试

```python
# apps/sso/tests/test_sync_service.py

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from apps.sso.models import WeWorkConfig, SyncLog, UserMapping
from apps.sso.services.wework_sync_service import WeWorkSyncService
from apps.organizations.models import Department
from apps.accounts.models import User


class WeWorkSyncServiceTest(TestCase):
    """企业微信同步服务测试"""

    def setUp(self):
        from apps.organizations.models import Organization

        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        self.service = WeWorkSyncService(self.config)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    def test_sync_departments_create_new(self, mock_get_depts):
        """测试同步部门 - 创建新部门"""
        mock_get_depts.return_value = [
            {
                'id': 1,
                'name': '技术部',
                'parentid': 0,
                'order': 1
            },
            {
                'id': 2,
                'name': '产品部',
                'parentid': 0,
                'order': 2
            }
        ]

        stats = self.service.sync_departments()

        # 验证统计数据
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['created'], 2)
        self.assertEqual(stats['updated'], 0)

        # 验证部门已创建
        self.assertEqual(Department.objects.count(), 2)
        tech_dept = Department.objects.get(wework_dept_id='1')
        self.assertEqual(tech_dept.name, '技术部')

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    def test_sync_departments_update_existing(self, mock_get_depts):
        """测试同步部门 - 更新现有部门"""
        # 先创建部门
        dept = Department.objects.create(
            organization=self.organization,
            name='技术部',
            wework_dept_id='1',
            wework_parent_id=0
        )

        # 模拟API返回更新后的名称
        mock_get_depts.return_value = [
            {
                'id': 1,
                'name': '技术研发部',
                'parentid': 0,
                'order': 1
            }
        ]

        stats = self.service.sync_departments()

        # 验证统计数据
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['created'], 0)
        self.assertEqual(stats['updated'], 1)

        # 验证部门已更新
        dept.refresh_from_db()
        self.assertEqual(dept.name, '技术研发部')

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_sync_users_create_new(self, mock_get_users, mock_get_depts):
        """测试同步用户 - 创建新用户"""
        mock_get_depts.return_value = [
            {'id': 1, 'name': '技术部', 'parentid': 0}
        ]

        mock_get_users.return_value = [
            {
                'userid': 'zhangsan',
                'name': '张三',
                'mobile': '13800138000',
                'email': 'zhangsan@example.com',
                'department': [1],
                'avatar': 'http://example.com/avatar.jpg'
            }
        ]

        stats = self.service.sync_users()

        # 验证统计数据
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['created'], 1)
        self.assertEqual(stats['updated'], 0)

        # 验证用户已创建
        user = User.objects.get(username='ww_zhangsan')
        self.assertEqual(user.real_name, '张三')
        self.assertEqual(user.mobile, '13800138000')

        # 验证用户映射已创建
        mapping = UserMapping.objects.get(
            platform='wework',
            platform_userid='zhangsan'
        )
        self.assertEqual(mapping.system_user, user)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_sync_users_update_existing(self, mock_get_users, mock_get_depts):
        """测试同步用户 - 更新现有用户"""
        # 先创建用户和映射
        user = User.objects.create(
            username='ww_zhangsan',
            real_name='张三',
            organization=self.organization
        )
        UserMapping.objects.create(
            platform='wework',
            platform_userid='zhangsan',
            system_user=user
        )

        mock_get_depts.return_value = [
            {'id': 1, 'name': '技术部', 'parentid': 0}
        ]

        # 模拟API返回更新后的信息
        mock_get_users.return_value = [
            {
                'userid': 'zhangsan',
                'name': '张三丰',
                'mobile': '13900139000',
                'email': 'zhangsanfeng@example.com',
                'department': [1]
            }
        ]

        stats = self.service.sync_users()

        # 验证统计数据
        self.assertEqual(stats['total'], 1)
        self.assertEqual(stats['created'], 0)
        self.assertEqual(stats['updated'], 1)

        # 验证用户已更新
        user.refresh_from_db()
        self.assertEqual(user.real_name, '张三丰')
        self.assertEqual(user.mobile, '13900139000')

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_sync_user_departments(self, mock_get_users, mock_get_depts):
        """测试同步用户部门关系"""
        # 创建部门
        dept1 = Department.objects.create(
            organization=self.organization,
            name='技术部',
            wework_dept_id='1'
        )
        dept2 = Department.objects.create(
            organization=self.organization,
            name='产品部',
            wework_dept_id='2'
        )

        mock_get_depts.return_value = [
            {'id': 1, 'name': '技术部', 'parentid': 0}
        ]

        mock_get_users.return_value = [
            {
                'userid': 'zhangsan',
                'name': '张三',
                'department': [1, 2]  # 用户同时属于两个部门
            }
        ]

        self.service.sync_users()

        # 验证用户部门关系
        user = User.objects.get(username='ww_zhangsan')
        self.assertEqual(user.departments.count(), 2)
        self.assertIn(dept1, user.departments.all())
        self.assertIn(dept2, user.departments.all())

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_full_sync(self, mock_get_users, mock_get_depts):
        """测试全量同步"""
        mock_get_depts.return_value = [
            {'id': 1, 'name': '技术部', 'parentid': 0}
        ]

        mock_get_users.return_value = [
            {
                'userid': 'zhangsan',
                'name': '张三',
                'department': [1]
            }
        ]

        log = self.service.full_sync()

        # 验证同步日志
        self.assertEqual(log.sync_type, 'full')
        self.assertEqual(log.status, 'success')
        self.assertEqual(log.total_count, 2)  # 1部门 + 1用户
        self.assertEqual(log.created_count, 3)  # 1部门 + 1用户 + 1映射
        self.assertIsNotNone(log.finished_at)

    def test_full_sync_failure_handling(self):
        """测试同步失败处理"""
        with patch.object(
            self.service,
            'sync_departments',
            side_effect=Exception('API调用失败')
        ):
            log = self.service.full_sync()

            # 验证失败状态记录
            self.assertEqual(log.status, 'failed')
            self.assertIn('API调用失败', log.error_message)
            self.assertIsNotNone(log.finished_at)

    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_list')
    @patch('apps.sso.adapters.wework_adapter.WeWorkAdapter.get_department_users')
    def test_partial_sync_with_errors(self, mock_get_users, mock_get_depts):
        """测试部分成功（有错误但继续处理）"""
        mock_get_depts.return_value = [
            {'id': 1, 'name': '技术部', 'parentid': 0}
        ]

        # 第一个用户正常，第二个用户会触发错误
        mock_get_users.return_value = [
            {
                'userid': 'zhangsan',
                'name': '张三',
                'department': [1]
            },
            {
                'userid': 'lisi',
                'name': '',  # 空名称会导致验证错误
                'department': [1]
            }
        ]

        # 模拟用户模型验证错误
        with patch('apps.accounts.models.User.objects.create') as mock_create:
            mock_create.side_effect = [
                Mock(id=1, username='ww_zhangsan'),
                ValidationError({'real_name': ['此字段不能为空']})
            ]

            log = self.service.full_sync()

            # 验证部分成功状态
            self.assertEqual(log.status, 'failed')
            self.assertGreater(log.failed_count, 0)
            self.assertGreater(len(log.error_details.get('errors', [])), 0)
```

### 1.2 Celery任务测试

```python
# apps/sso/tests/test_tasks.py

from django.test import TestCase
from unittest.mock import patch, Mock
from apps.sso.tasks import sync_wework_contacts, sync_all_orgs_wework
from apps.sso.models import WeWorkConfig, SyncLog
from apps.organizations.models import Organization


class SyncTasksTest(TestCase):
    """Celery同步任务测试"""

    def setUp(self):
        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        self.config = WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

    @patch('apps.sso.tasks.cache')
    @patch('apps.sso.tasks.WeWorkSyncService')
    def test_sync_wework_contacts_success(self, mock_service_class, mock_cache):
        """测试同步任务成功"""
        mock_cache.get.return_value = False

        # 模拟同步服务
        mock_service = Mock()
        mock_service.full_sync.return_value = Mock(
            id=1,
            status='success',
            total_count=10,
            created_count=5,
            updated_count=5,
            failed_count=0
        )
        mock_service_class.return_value = mock_service

        result = sync_wework_contacts(self.organization.id)

        # 验证返回结果
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['sync_log_id'], 1)

        # 验证锁已释放
        mock_cache.delete.assert_called_once()

    @patch('apps.sso.tasks.cache')
    def test_sync_wework_contacts_duplicate(self, mock_cache):
        """测试重复任务被阻止"""
        mock_cache.get.return_value = True  # 已有任务运行中

        result = sync_wework_contacts(self.organization.id)

        # 验证返回状态
        self.assertEqual(result['status'], 'duplicate')

        # 验证未创建新任务
        self.assertEqual(SyncLog.objects.filter(status='running').count(), 0)

    @patch('apps.sso.tasks.cache')
    @patch('apps.sso.tasks.sync_wework_contacts.delay')
    def test_sync_all_orgs_wework(self, mock_delay, mock_cache):
        """测试同步所有组织"""
        mock_cache.get.return_value = False
        mock_delay.return_value = Mock(id='task-123')

        # 创建多个组织的配置
        org2 = Organization.objects.create(name='企业2', code='ORG2')
        WeWork.objects.create(
            organization=org2,
            corp_id='ww789',
            corp_name='企业2',
            agent_id=1000002,
            agent_secret='secret2',
            is_enabled=True
        )

        result = sync_all_orgs_wework()

        # 验证为两个组织都启动了任务
        self.assertEqual(len(result), 2)
        self.assertTrue(mock_delay.call_count >= 2)
```

---

## 2. API测试

```python
# apps/sso/tests/test_sync_api.py

from rest_framework.test import APITestCase
from django.urls import reverse
from apps.sso.models import WeWorkConfig, SyncLog
from apps.organizations.models import Organization


class SyncAPITest(APITestCase):
    """同步API测试"""

    def setUp(self):
        self.organization = Organization.objects.create(
            name='测试企业',
            code='TEST'
        )

        # 创建测试用户
        from apps.accounts.models import User
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            organization=self.organization
        )

        self.client.force_authenticate(user=self.user)

    def test_get_config_enabled(self):
        """测试获取已启用的配置"""
        WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        url = reverse('sync-config')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['enabled'])
        self.assertEqual(response.data['corp_name'], '测试企业')

    def test_get_config_disabled(self):
        """测试获取未启用的配置"""
        url = reverse('sync-config')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['enabled'])

    @patch('apps.sso.api.sync.sync_wework_contacts.delay')
    def test_trigger_sync(self, mock_delay):
        """测试触发同步"""
        WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        mock_delay.return_value = Mock(id='task-123')

        url = reverse('sync-trigger')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['task_id'], 'task-123')
        mock_delay.assert_called_once()

    @patch('apps.sso.api.sync.sync_wework_contacts.delay')
    def test_trigger_sync_when_running(self, mock_delay):
        """测试同步中再次触发"""
        WeWorkConfig.objects.create(
            organization=self.organization,
            corp_id='ww123456',
            corp_name='测试企业',
            agent_id=1000001,
            agent_secret='test_secret',
            is_enabled=True
        )

        # 创建运行中的日志
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='running'
        )

        url = reverse('sync-trigger')
        response = self.client.post(url)

        self.assertEqual(response.status_code, 409)
        self.assertIn('已有同步任务', response.data['error'])

    def test_get_sync_logs(self):
        """测试获取同步日志"""
        # 创建测试日志
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='success',
            total_count=10,
            created_count=5,
            updated_count=5
        )

        url = reverse('sync-logs')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sync_type'], 'full')

    def test_get_sync_status(self):
        """测试获取同步状态"""
        SyncLog.objects.create(
            organization=self.organization,
            sync_type='full',
            status='success',
            total_count=10,
            created_count=5,
            updated_count=5
        )

        url = reverse('sync-status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('stats', response.data)
```

---

## 3. 前端组件测试

```typescript
// src/views/admin/__tests__/SyncManagement.spec.ts

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import SyncManagement from '../SyncManagement.vue'
import * as api from '@/api/sso'

vi.mock('@/api/sso')
vi.mock('vue-router')

describe('SyncManagement', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('加载时获取同步状态和日志', async () => {
    vi.mocked(api.getSyncStatus).mockResolvedValue({
      enabled: true,
      status: 'success',
      last_sync_time: '2024-01-15T10:30:00Z',
      corp_name: '测试企业',
      stats: { total: 10, created: 5, updated: 5, failed: 0 }
    })

    vi.mocked(api.getSyncLogs).mockResolvedValue([
      {
        id: 1,
        sync_type: 'full',
        status: 'success',
        created_at: '2024-01-15T10:30:00Z',
        total_count: 10,
        created_count: 5,
        updated_count: 5,
        failed_count: 0
      }
    ])

    const wrapper = mount(SyncManagement)
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(api.getSyncStatus).toHaveBeenCalledOnce()
    expect(api.getSyncLogs).toHaveBeenCalledOnce()
  })

  it('点击立即同步触发同步任务', async () => {
    vi.mocked(api.getSyncStatus).mockResolvedValue({
      enabled: true,
      status: 'never_synced',
      last_sync_time: null,
      corp_name: '测试企业',
      stats: { total: 0, created: 0, updated: 0, failed: 0 }
    })

    vi.mocked(api.getSyncLogs).mockResolvedValue([])
    vi.mocked(api.triggerSync).mockResolvedValue({
      task_id: 'task-123',
      message: '同步任务已启动'
    })

    const wrapper = mount(SyncManagement)
    await new Promise(resolve => setTimeout(resolve, 100))

    // 触发同步
    await wrapper.vm.handleSync('full')

    expect(api.triggerSync).toHaveBeenCalledWith({ sync_type: 'full' })
  })

  it('同步失败显示错误提示', async () => {
    vi.mocked(api.getSyncStatus).mockResolvedValue({
      enabled: true,
      status: 'never_synced',
      last_sync_time: null,
      corp_name: '测试企业'
    })

    vi.mocked(api.getSyncLogs).mockResolvedValue([])
    vi.mocked(api.triggerSync).mockRejectedValue({
      response: { data: { error: '企业微信未配置' } }
    })

    const wrapper = mount(SyncManagement)
    const messageSpy = vi.spyOn(ElMessage, 'error')

    await wrapper.vm.handleSync('full')
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(messageSpy).toHaveBeenCalledWith('企业微信未配置')
  })
})

describe('SyncStatus', () => {
  it('显示正确的同步状态标签', () => {
    const statuses = [
      { status: 'success', type: 'success', label: '同步成功' },
      { status: 'failed', type: 'danger', label: '同步失败' },
      { status: 'running', type: 'warning', label: '同步中' },
      { status: 'never_synced', type: 'info', label: '从未同步' }
    ]

    statuses.forEach(({ status, type, label }) => {
      const wrapper = mount(SyncStatus, {
        props: {
          status: {
            enabled: true,
            status,
            last_sync_time: null,
            corp_name: '测试企业'
          }
        }
      })

      expect(wrapper.vm.statusType).toBe(type)
      expect(wrapper.vm.statusLabel).toBe(label)
    })
  })
})
```

---

## 4. E2E测试

```typescript
// e2e/admin/sync-management.spec.ts

import { test, expect } from '@playwright/test'

test.describe('同步管理', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('input[placeholder*="用户名"]', 'admin')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button:has-text("登录")')
    await page.waitForURL('/')
  })

  test('显示同步状态', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/sync')

    // 验证同步状态卡片显示
    await expect(page.locator('.sync-status')).toBeVisible()

    // 验证统计卡片显示
    await expect(page.locator('.sync-stats')).toBeVisible()
  })

  test('手动触发同步', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/sync')

    // 点击立即同步按钮
    await page.click('button:has-text("立即同步")')

    // 验证同步任务已启动提示
    await expect(page.locator('.el-message--success')).toBeVisible()

    // 验证进度弹窗显示
    await expect(page.locator('.sync-progress-dialog')).toBeVisible()
  })

  test('查看同步日志', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/sync')

    // 滚动到日志列表
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // 验证日志表格显示
    await expect(page.locator('.sync-logs .el-table')).toBeVisible()

    // 点击详情按钮
    await page.click('.sync-logs .el-table .el-button:has-text("详情")')

    // 验证详情弹窗显示
    await expect(page.locator('.sync-log-detail-dialog')).toBeVisible()
  })

  test('刷新同步状态', async ({ page }) => {
    await page.goto('http://localhost:5173/admin/sync')

    // 点击刷新按钮
    await page.click('.sync-status .el-icon.is-loading')

    // 验证loading状态
    await expect(page.locator('.sync-status .el-button.is-loading')).toBeVisible()
  })
})
```

---

## 验收标准

### 功能验收

- [ ] 可以获取同步配置状态
- [ ] 可以手动触发全量同步
- [ ] 可以手动触发部门同步
- [ ] 可以手动触发用户同步
- [ ] 同步日志正确记录
- [ ] 同步统计数据准确
- [ ] 部门层级关系正确
- [ ] 用户部门关系正确
- [ ] 同步中的任务不可重复触发
- [ ] 同步失败有错误提示

### 性能验收

- [ ] 同步100个部门耗时 < 30秒
- [ ] 同步1000个用户耗时 < 2分钟
- [ ] 前端轮询不影响性能

### 测试覆盖率

- [ ] 同步服务测试覆盖率 > 80%
- [ ] Celery任务测试覆盖率 > 70%
- [ ] API测试覆盖率 > 90%

---

## 后续任务

1. Phase 2.3: 实现企业微信消息推送通知测试
