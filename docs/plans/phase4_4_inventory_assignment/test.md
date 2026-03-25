# Phase 4.4: 盘点任务分配与执行 - 测试计划

## 概述

定义盘点任务分配与执行功能的测试用例，包括分配服务、进度跟踪、用户端执行等测试。

---

## 1. 测试概述

### 1.1 测试目标

- 验证盘点任务分配功能
- 验证进度跟踪准确性
- 验证用户端执行流程
- 验证结果汇总正确性

### 1.2 测试范围

| 模块 | 测试类型 | 优先级 |
|------|----------|--------|
| 分配服务 | 单元、集成 | 高 |
| 进度跟踪 | 单元 | 高 |
| 用户端执行 | 集成、E2E | 高 |
| 结果汇总 | 单元 | 中 |

---

## 2. 单元测试

### 2.1 分配服务测试

**文件**: `apps/inventory/tests/test_assignment.py`

```python
import pytest
from django.test import TestCase
from apps.inventory.models import InventoryTask, InventoryAssignment
from apps.inventory.services.assignment import AssignmentService


class AssignmentServiceTest(TestCase):
    """盘点分配服务测试"""

    def setUp(self):
        self.task = InventoryTask.objects.create(
            task_no='PD2024001',
            inventory_type='full',
            department=self.dept
        )
        self.assets = [create_asset() for _ in range(100)]
        self.users = [create_user(username=f'user{i}') for i in range(5)]

    def test_assign_by_location(self):
        """测试按位置分配"""
        assignments = AssignmentService.assign_by_location(
            task=self.task,
            location_assignments=[
                {'executor': self.users[0], 'location': 'A区'},
                {'executor': self.users[1], 'location': 'B区'},
            ]
        )

        assert len(assignments) == 2
        assert assignments[0].assign_mode == 'location'
        assert assignments[0].executor == self.users[0]

    def test_assign_by_category(self):
        """测试按分类分配"""
        category = create_asset_category(code='01', name='电子设备')
        assets = create_assets(category=category, count=50)

        assignments = AssignmentService.assign_by_category(
            task=self.task,
            category_assignments=[
                {'executor': self.users[0], 'category_id': category.id}
            ]
        )

        assert assignments[0].asset_count == 50

    def test_assign_by_custodian(self):
        """测试按保管人分配（自我盘点）"""
        custodians = [create_user(username=f'custodian{i}') for i in range(10)]

        for custodian in custodians:
            create_asset(custodian=custodian)

        assignments = AssignmentService.assign_by_custodian(
            task=self.task,
            custodians=custodians
        )

        assert len(assignments) == 10
        for assignment in assignments:
            assert assignment.executor == assignment.custodian

    def test_assign_evenly(self):
        """测试平均分配"""
        # 100个资产，5个人，每人20个
        assignments = AssignmentService.assign_evenly(
            task=self.task,
            executors=self.users,
            assets=self.assets
        )

        assert len(assignments) == 5
        for assignment in assignments:
            assert assignment.asset_count == 20

    def test_custom_assignment(self):
        """测试自定义分配"""
        selected_assets = self.assets[:30]

        assignment = InventoryAssignment.objects.create(
            task=self.task,
            executor=self.users[0],
            assign_mode='custom',
            asset_count=30
        )
        assignment.assets.set(selected_assets)

        assert assignment.asset_count == 30
        assert assignment.assets.count() == 30

    def test_delete_assignment(self):
        """测试删除分配"""
        assignment = InventoryAssignment.objects.create(
            task=self.task,
            executor=self.users[0],
            assign_mode='location',
            asset_count=20
        )

        AssignmentService.delete_assignment(assignment.id)

        assert not InventoryAssignment.objects.filter(
            id=assignment.id
        ).exists()
```

### 2.2 进度跟踪测试

```python
class ProgressTrackingTest(TestCase):
    """进度跟踪测试"""

    def test_get_assignment_progress(self):
        """测试获取分配进度"""
        task = InventoryTask.objects.create(task_no='PD2024001')
        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=self.user,
            asset_count=100,
            scanned_count=50
        )

        progress = AssignmentService.get_progress(assignment.id)

        assert progress['total'] == 100
        assert progress['scanned'] == 50
        assert progress['percentage'] == 50

    def test_get_task_progress(self):
        """测试获取任务总进度"""
        task = InventoryTask.objects.create(task_no='PD2024001')

        for i in range(5):
            InventoryAssignment.objects.create(
                task=task,
                executor=create_user(username=f'user{i}'),
                asset_count=100,
                scanned_count=50 * (i + 1)  # 50, 100, 150, 200, 250
            )

        progress = AssignmentService.get_task_progress(task.id)

        assert progress['total_assets'] == 500
        assert progress['scanned_count'] == 750  # 注意scanned_count可超过total
        assert progress['completion_rate'] == 100  # 至少扫描一遍算完成

    def test_overdue_assignments(self):
        """测试逾期未完成的分配"""
        task = InventoryTask.objects.create(
            task_no='PD2024001',
            end_date=date.today() - timedelta(days=1)
        )

        assignment = InventoryAssignment.objects.create(
            task=task,
            executor=self.user,
            asset_count=100,
            status='pending'  # 未完成
        )

        overdue = AssignmentService.get_overdue_assignments(task.id)

        assert len(overdue) == 1
        assert overdue[0].id == assignment.id
```

---

## 3. API 测试

**文件**: `apps/inventory/tests/test_assignment_api.py`

```python
class AssignmentAPITest(TestCase):
    """分配API测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        self.task = InventoryTask.objects.create(task_no='PD2024001')

    def test_create_assignment(self):
        """测试创建分配"""
        url = reverse('inventory-assignment-create')
        data = {
            'task_id': self.task.id,
            'assign_mode': 'location',
            'assignments': [
                {'executor_id': self.user.id, 'location': 'A区'}
            ]
        }

        response = self.client.post(url, data)

        assert response.status_code == 201
        assert InventoryAssignment.objects.filter(
            task=self.task,
            executor=self.user
        ).exists()

    def test_get_task_assignments(self):
        """测试获取任务分配列表"""
        InventoryAssignment.objects.create(
            task=self.task,
            executor=self.user,
            asset_count=100
        )

        url = reverse('inventory-task-assignments', args=[self.task.id])
        response = self.client.get(url)

        assert response.status_code == 200
        assert response.data['count'] >= 1

    def test_get_my_assignments(self):
        """测试获取我的分配"""
        InventoryAssignment.objects.create(
            task=self.task,
            executor=self.user,
            asset_count=100
        )

        url = reverse('inventory-my-assignments')
        response = self.client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) >= 1

    def test_submit_assignment(self):
        """测试提交分配"""
        assignment = InventoryAssignment.objects.create(
            task=self.task,
            executor=self.user,
            asset_count=100,
            scanned_count=100
        )

        url = reverse('inventory-assignment-submit', args=[assignment.id])
        data = {'comment': '盘点完成'}
        response = self.client.post(url, data)

        assert response.status_code == 200

        assignment.refresh_from_db()
        assert assignment.status == 'submitted'
```

---

## 4. 集成测试

### 4.1 完整分配流程

```python
class AssignmentFlowTest(TestCase):
    """分配流程集成测试"""

    def test_full_assignment_flow(self):
        """测试完整分配流程"""
        # 1. 创建盘点任务
        task = InventoryTask.objects.create(
            task_no='PD2024001',
            inventory_type='full'
        )

        # 2. 添加资产到任务
        assets = create_assets(count=100)
        task.assets.set(assets)

        # 3. 按位置分配
        users = [create_user(username=f'user{i}') for i in range(5)]
        locations = ['A区', 'B区', 'C区', 'D区', 'E区']

        assignments = AssignmentService.assign_by_location(
            task=task,
            location_assignments=[
                {'executor': users[i], 'location': locations[i]}
                for i in range(5)
            ]
        )

        # 4. 验证分配结果
        assert len(assignments) == 5

        # 5. 模拟执行人盘点
        for i, assignment in enumerate(assignments):
            scanned_count = random.randint(15, 25)

            for j in range(scanned_count):
                asset = assignment.assets.all()[j]
                InventoryScan.objects.create(
                    task=task,
                    assignment=assignment,
                    asset=asset,
                    scanned_by=users[i]
                )

            assignment.scanned_count = scanned_count
            assignment.save()

        # 6. 提交分配
        for assignment in assignments:
            AssignmentService.submit_assignment(
                assignment.id,
                comment='盘点完成'
            )

        # 7. 验证任务状态
        task.refresh_from_db()
        assert task.status == 'completed'

    def test_partial_completion_flow(self):
        """测试部分完成流程"""
        task = InventoryTask.objects.create(task_no='PD2024001')

        # 创建3个分配，只完成2个
        users = [create_user(username=f'user{i}') for i in range(3)]

        for user in users:
            InventoryAssignment.objects.create(
                task=task,
                executor=user,
                asset_count=50,
                status='completed' if user != users[2] else 'pending'
            )

        # 任务应该仍为进行中
        progress = AssignmentService.get_task_progress(task.id)
        assert progress['completion_rate'] < 100
        assert task.status == 'in_progress'
```

---

## 5. 前端测试

### 5.1 组件测试

```javascript
// assignments.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AssignmentList from '@/views/inventory/AssignmentList.vue'

describe('AssignmentList', () => {
  it('should display assignments correctly', async () => {
    const wrapper = mount(AssignmentList, {
      props: {
        taskId: 1
      }
    })

    await wrapper.vm.loadAssignments()

    expect(wrapper.findAll('.assignment-item').length).toBeGreaterThan(0)
  })

  it('should show progress bar correctly', () => {
    const wrapper = mount(AssignmentList, {
      props: {
        assignments: [
          {
            executor_name: '张三',
            asset_count: 100,
            scanned_count: 50
          }
        ]
      }
    })

    const progress = wrapper.find('.progress-bar')
    expect(progress.attributes('style')).toContain('width: 50%')
  })
})
```

---

## 6. E2E测试

```javascript
// e2e/inventory.spec.js
import { test, expect } from '@playwright/test'

test.describe('Inventory Assignment E2E', () => {
  test('admin creates and monitors assignments', async ({ page }) => {
    await page.goto('/inventory/tasks/1/assignments')

    // 创建分配
    await page.click('button:text("创建分配")')
    await page.selectOption('assign_mode', 'location')
    await page.click('button:text("确定")')

    // 验证分配创建成功
    await expect(page.locator('.assignment-item')).toHaveCount(
      greaterThan(0)
    )

    // 查看进度
    const progress = page.locator('.progress-summary')
    await expect(progress).toContainText('总进度')
  })

  test('executor completes assigned task', async ({ page }) => {
    await page.goto('/inventory/my-assignments')

    // 点击任务
    await page.click('.assignment-item:first-child')

    // 扫码盘点
    await page.click('button:text("扫码盘点")')
    await page.fill('input[placeholder="请扫描或输入"]', 'ZC001')
    await page.press('Enter')

    // 验证扫描成功
    await expect(page.locator('.scanned-count')).toHaveText('1')

    // 提交
    await page.click('button:text("提交盘点")')
    await expect(page).toHaveURL(/.*my-assignments.*/)
  })
})
```

---

## 7. 性能测试

```python
class PerformanceTest(TestCase):
    """性能测试"""

    def test_large_scale_assignment(self):
        """测试大规模分配性能"""
        task = InventoryTask.objects.create(task_no='PD2024001')

        # 10000个资产，100个执行人
        assets = create_assets(count=10000)
        users = [create_user(username=f'user{i}') for i in range(100)]

        import time
        start_time = time.time()

        assignments = AssignmentService.assign_evenly(
            task=task,
            executors=users,
            assets=assets
        )

        duration = time.time() - start_time

        assert len(assignments) == 100
        assert duration < 30  # 30秒内完成

    def test_progress_query_performance(self):
        """测试进度查询性能"""
        task = InventoryTask.objects.create(task_no='PD2024001')

        # 创建100个分配
        for i in range(100):
            InventoryAssignment.objects.create(
                task=task,
                executor=create_user(username=f'user{i}'),
                asset_count=100,
                scanned_count=i
            )

        import time
        start_time = time.time()

        progress = AssignmentService.get_task_progress(task.id)

        duration = time.time() - start_time

        assert duration < 1  # 1秒内完成查询
```

---

## 8. 测试通过标准

1. **单元测试**: 代码覆盖率 >= 90%
2. **集成测试**: 核心流程正常运行
3. **API测试**: 所有接口正常响应
4. **E2E测试**: 关键用户场景可正常执行
5. **性能测试**: 大规模分配在30秒内完成
