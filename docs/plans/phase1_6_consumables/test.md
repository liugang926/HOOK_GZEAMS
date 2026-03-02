# Phase 1.6: 低值易耗品/办公用品管理 - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 模型、服务层 | P0 |
| API测试 | 接口请求响应 | P0 |
| 前端组件测试 | Vue组件交互 | P1 |
| E2E测试 | 完整业务流程 | P1 |

---

## 1. 后端单元测试

### 1.1 耗材模型测试

```python
# apps/consumables/tests/test_models.py

from django.test import TestCase
from apps.consumables.models import Consumable, ConsumableCategory, ConsumableStock
from apps.accounts.models import User


class ConsumableModelTest(TestCase):
    """耗材模型测试"""

    def setUp(self):
        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            unit='包'
        )

        self.consumable = Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=50,
            available_stock=50,
            min_stock=20,
            max_stock=100,
            average_price=25.00
        )

    def test_consumable_str(self):
        """测试字符串表示"""
        self.assertEqual(str(self.consumable), 'HC001 - A4打印纸')

    def test_check_stock_status_normal(self):
        """测试库存状态检查-正常"""
        self.consumable.available_stock = 50
        self.consumable.check_stock_status()
        self.assertEqual(self.consumable.status, 'normal')

    def test_check_stock_status_low(self):
        """测试库存状态检查-低库存"""
        self.consumable.available_stock = 15
        self.consumable.check_stock_status()
        self.assertEqual(self.consumable.status, 'low_stock')

    def test_check_stock_status_out(self):
        """测试库存状态检查-缺货"""
        self.consumable.available_stock = 0
        self.consumable.check_stock_status()
        self.assertEqual(self.consumable.status, 'out_of_stock')

    def test_update_stock_increase(self):
        """测试库存增加"""
        user = User.objects.create(username='test')
        before_stock = self.consumable.current_stock

        self.consumable.update_stock(
            quantity=10,
            transaction_type='purchase',
            source_type='Test',
            source_id='1',
            source_no='TEST001',
            handler=user
        )

        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, before_stock + 10)

        # 验证库存流水记录
        log = ConsumableStock.objects.filter(
            consumable=self.consumable,
            transaction_type='purchase'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity, 10)

    def test_update_stock_decrease(self):
        """测试库存减少"""
        user = User.objects.create(username='test')
        before_stock = self.consumable.current_stock

        self.consumable.update_stock(
            quantity=-10,
            transaction_type='issue',
            source_type='Test',
            source_id='1',
            source_no='TEST001',
            handler=user
        )

        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, before_stock - 10)


class ConsumableCategoryTest(TestCase):
    """耗材分类测试"""

    def test_category_full_name(self):
        """测试分类完整名称"""
        parent = ConsumableCategory.objects.create(
            code='OFFICE',
            name='办公用品'
        )
        child = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            parent=parent
        )

        self.assertEqual(child.full_name, '办公用品 > 纸张类')

    def test_category_path_on_save(self):
        """测试分类路径保存"""
        parent = ConsumableCategory.objects.create(
            code='OFFICE',
            name='办公用品'
        )
        child = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            parent=parent
        )

        self.assertIn(str(parent.id), child.path)
        self.assertEqual(child.level, 2)
```

### 1.2 采购服务测试

```python
# apps/consumables/tests/test_purchase_service.py

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.consumables.models import Consumable, ConsumableCategory, ConsumablePurchase
from apps.consumables.services.purchase_service import ConsumablePurchaseService
from apps.accounts.models import User


class ConsumablePurchaseServiceTest(TestCase):
    """耗材采购服务测试"""

    def setUp(self):
        self.service = ConsumablePurchaseService()
        self.user = User.objects.create(username='purchaser', real_name='采购员')

        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            unit='包'
        )

        self.consumable = Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=20,
            available_stock=20,
            average_price=25.00
        )

    def test_create_purchase_success(self):
        """测试成功创建采购单"""
        from apps.assets.models import Supplier
        supplier = Supplier.objects.create(name='晨光文具')

        data = {
            'supplier': supplier.id,
            'purchase_date': '2024-06-15',
            'purchase_type': 'regular',
            'items': [
                {
                    'consumable_id': self.consumable.id,
                    'order_quantity': 50,
                    'received_quantity': 50,
                    'unit_price': 25.00
                }
            ]
        }

        purchase = self.service.create_purchase(data, self.user)

        self.assertEqual(purchase.applicant, self.user)
        self.assertEqual(purchase.status, 'draft')
        self.assertTrue(purchase.purchase_no.startswith('HC'))
        self.assertEqual(purchase.items.count(), 1)

    def test_create_purchase_empty_items_fails(self):
        """测试创建空明细采购单应失败"""
        from apps.assets.models import Supplier
        supplier = Supplier.objects.create(name='晨光文具')

        data = {
            'supplier': supplier.id,
            'items': []
        }

        with self.assertRaises(ValidationError):
            self.service.create_purchase(data, self.user)

    def test_submit_purchase(self):
        """测试提交采购单"""
        from apps.assets.models import Supplier
        supplier = Supplier.objects.create(name='晨光文具')

        purchase = ConsumablePurchase.objects.create(
            supplier=supplier,
            applicant=self.user,
            status='draft'
        )

        result = self.service.submit_purchase(purchase.id, self.user)

        self.assertEqual(result.status, 'submitted')

    def test_submit_purchase_by_other_user_fails(self):
        """测试非申请人提交应失败"""
        from apps.assets.models import Supplier
        other_user = User.objects.create(username='other')

        supplier = Supplier.objects.create(name='晨光文具')

        purchase = ConsumablePurchase.objects.create(
            supplier=supplier,
            applicant=self.user,
            status='draft'
        )

        with self.assertRaises(ValidationError):
            self.service.submit_purchase(purchase.id, other_user)

    def test_approve_purchase(self):
        """测试审批通过"""
        from apps.assets.models import Supplier
        manager = User.objects.create(username='manager', real_name='经理')
        supplier = Supplier.objects.create(name='晨光文具')

        purchase = ConsumablePurchase.objects.create(
            supplier=supplier,
            applicant=self.user,
            status='submitted'
        )

        result = self.service.approve_purchase(
            purchase.id,
            manager,
            'approved'
        )

        self.assertEqual(result.status, 'approved')
        self.assertEqual(result.approved_by, manager)

    def test_confirm_receipt(self):
        """测试确认入库"""
        from apps.assets.models import Supplier
        supplier = Supplier.objects.create(name='晨光文具')

        purchase = ConsumablePurchase.objects.create(
            supplier=supplier,
            applicant=self.user,
            status='approved'
        )

        from apps.consumables.models import ConsumablePurchaseItem
        ConsumablePurchaseItem.objects.create(
            purchase=purchase,
            consumable=self.consumable,
            order_quantity=50,
            received_quantity=50,
            unit_price=25.00
        )

        result = self.service.confirm_receipt(purchase.id, self.user)

        self.assertEqual(result.status, 'received')

        # 验证库存更新
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, 70)

    def test_confirm_receipt_non_approved_fails(self):
        """测试非审批状态不能入库"""
        from apps.assets.models import Supplier
        supplier = Supplier.objects.create(name='晨光文具')

        purchase = ConsumablePurchase.objects.create(
            supplier=supplier,
            applicant=self.user,
            status='submitted'
        )

        with self.assertRaises(ValueError):
            self.service.confirm_receipt(purchase.id, self.user)

    def test_calculate_average_price(self):
        """测试加权平均价计算"""
        # 当前库存20个，平均价25
        # 新增50个，单价26
        new_price = self.consumable.average_price

        purchase = ConsumablePurchase()
        calculated = purchase._calculate_average_price(
            self.consumable,
            26.00,
            50
        )

        # (20 * 25 + 50 * 26) / 70 = 1750 / 70 ≈ 25.71
        expected = (20 * 25.00 + 50 * 26.00) / 70
        self.assertAlmostEqual(float(calculated), expected, places=2)
```

### 1.3 领用服务测试

```python
# apps/consumables/tests/test_issue_service.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.consumables.models import Consumable, ConsumableCategory, ConsumableIssue
from apps.consumables.services.issue_service import ConsumableIssueService
from apps.accounts.models import User
from apps.organizations.models import Department


class ConsumableIssueServiceTest(TestCase):
    """耗材领用服务测试"""

    def setUp(self):
        self.service = ConsumableIssueService()
        self.user = User.objects.create(username='applicant', real_name='申请人')

        self.department = Department.objects.create(name='研发部')

        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            unit='包'
        )

        self.consumable = Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=50,
            available_stock=50,
            min_stock=20,
            average_price=25.00
        )

    def test_create_issue_success(self):
        """测试成功创建领用单"""
        data = {
            'issue_date': '2024-06-15',
            'issue_type': 'department',
            'department': self.department.id,
            'purpose': '项目使用',
            'items': [
                {
                    'consumable_id': self.consumable.id,
                    'quantity': 10
                }
            ]
        }

        issue = self.service.create_issue(data, self.user)

        self.assertEqual(issue.applicant, self.user)
        self.assertEqual(issue.status, 'draft')
        self.assertTrue(issue.issue_no.startswith('HCL'))
        self.assertEqual(issue.items.count(), 1)

    def test_create_issue_insufficient_stock_fails(self):
        """测试库存不足创建领用单应失败"""
        data = {
            'department': self.department.id,
            'purpose': '测试',
            'items': [
                {
                    'consumable_id': self.consumable.id,
                    'quantity': 100  # 超过库存
                }
            ]
        }

        with self.assertRaises(ValidationError) as context:
            self.service.create_issue(data, self.user)

        self.assertIn('库存不足', str(context.exception))

    def test_approve_issue(self):
        """测试审批领用单"""
        manager = User.objects.create(username='manager')

        issue = ConsumableIssue.objects.create(
            applicant=self.user,
            department=self.department,
            status='submitted'
        )

        result = self.service.approve_issue(
            issue.id,
            manager,
            'approved'
        )

        self.assertEqual(result.status, 'approved')

    def test_confirm_issue(self):
        """测试确认发放"""
        manager = User.objects.create(username='manager')

        issue = ConsumableIssue.objects.create(
            applicant=self.user,
            department=self.department,
            status='approved'
        )

        from apps.consumables.models import ConsumableIssueItem
        ConsumableIssueItem.objects.create(
            issue=issue,
            consumable=self.consumable,
            quantity=10
        )

        result = self.service.confirm_issue(issue.id, manager)

        self.assertEqual(result.status, 'issued')

        # 验证库存扣减
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.available_stock, 40)

    def test_confirm_issue_insufficient_stock_fails(self):
        """测试库存不足不能发放"""
        manager = User.objects.create(username='manager')

        issue = ConsumableIssue.objects.create(
            applicant=self.user,
            department=self.department,
            status='approved'
        )

        from apps.consumables.models import ConsumableIssueItem
        ConsumableIssueItem.objects.create(
            issue=issue,
            consumable=self.consumable,
            quantity=100  # 超过库存
        )

        with self.assertRaises(ValidationError):
            self.service.confirm_issue(issue.id, manager)
```

### 1.4 库存预警服务测试

```python
# apps/consumables/tests/test_alert_service.py

from django.test import TestCase
from apps.consumables.models import Consumable, ConsumableCategory
from apps.consumables.services.alert_service import StockAlertService


class StockAlertServiceTest(TestCase):
    """库存预警服务测试"""

    def setUp(self):
        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            unit='包'
        )

        # 正常库存
        self.consumable_normal = Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=80,
            available_stock=80,
            min_stock=20,
            max_stock=100,
            status='normal'
        )

        # 低库存
        self.consumable_low = Consumable.objects.create(
            code='HC002',
            name='签字笔',
            category=self.category,
            unit='支',
            current_stock=5,
            available_stock=5,
            min_stock=50,
            status='low_stock'
        )

        # 缺货
        self.consumable_out = Consumable.objects.create(
            code='HC003',
            name='文件夹',
            category=self.category,
            unit='个',
            current_stock=0,
            available_stock=0,
            min_stock=20,
            status='out_of_stock'
        )

    def test_check_all_low_stock(self):
        """测试检查所有低库存"""
        service = StockAlertService()
        result = service.check_all_low_stock()

        self.assertTrue(result['has_alert'])
        self.assertEqual(result['total_categories'], 1)
        self.assertEqual(len(result['alerts']), 1)
        self.assertEqual(len(result['alerts'][0]['items']), 2)

    def test_check_all_low_stock_empty(self):
        """测试无低库存时检查"""
        self.consumable_low.delete()
        self.consumable_out.delete()

        service = StockAlertService()
        result = service.check_all_low_stock()

        self.assertFalse(result['has_alert'])
        self.assertEqual(len(result['items']), 0)
```

---

## 2. API测试

```python
# apps/consumables/tests/test_api.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


class ConsumableAPITest(APITestCase):
    """耗材API测试"""

    def setUp(self):
        from apps.accounts.models import User
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        from apps.consumables.models import ConsumableCategory
        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类',
            unit='包'
        )

    def test_list_consumables(self):
        """测试获取耗材列表"""
        url = reverse('consumable-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)

    def test_create_consumable(self):
        """测试创建耗材"""
        url = reverse('consumable-list')
        data = {
            'code': 'HC001',
            'name': 'A4打印纸',
            'category': self.category.id,
            'unit': '包',
            'min_stock': 20,
            'max_stock': 100
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)

    def test_stock_summary(self):
        """测试获取库存汇总"""
        from apps.consumables.models import Consumable
        Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=50,
            average_price=25.00
        )

        url = reverse('consumable-stock-summary')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('by_category', response.data)

    def test_low_stock_alert(self):
        """测试获取低库存列表"""
        from apps.consumables.models import Consumable
        Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category,
            unit='包',
            current_stock=5,
            available_stock=5,
            min_stock=20,
            status='low_stock'
        )

        url = reverse('stock-alert-low-stock')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


class PurchaseAPITest(APITestCase):
    """采购单API测试"""

    def setUp(self):
        from apps.accounts.models import User
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        from apps.assets.models import Supplier
        self.supplier = Supplier.objects.create(name='晨光文具')

        from apps.consumables.models import ConsumableCategory
        self.category = ConsumableCategory.objects.create(
            code='PAPER',
            name='纸张类'
        )

        self.consumable = Consumable.objects.create(
            code='HC001',
            name='A4打印纸',
            category=self.category
        )

    def test_create_purchase(self):
        """测试创建采购单"""
        url = reverse('consumable-purchase-list')
        data = {
            'supplier': self.supplier.id,
            'purchase_type': 'regular',
            'items': [
                {
                    'consumable_id': self.consumable.id,
                    'order_quantity': 50,
                    'received_quantity': 50,
                    'unit_price': 25.00
                }
            ]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_purchase(self):
        """测试提交采购单"""
        from apps.consumables.models import ConsumablePurchase
        purchase = ConsumablePurchase.objects.create(
            supplier=self.supplier,
            applicant=self.user,
            status='draft'
        )

        url = reverse('consumable-purchase-submit', kwargs={'pk': purchase.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approve_purchase(self):
        """测试审批采购单"""
        from apps.consumables.models import ConsumablePurchase
        purchase = ConsumablePurchase.objects.create(
            supplier=self.supplier,
            applicant=self.user,
            status='submitted'
        )

        url = reverse('consumable-purchase-approve', kwargs={'pk': purchase.id})
        response = self.client.post(url, {'approval': 'approved'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_receipt(self):
        """测试确认入库"""
        from apps.consumables.models import ConsumablePurchase, ConsumablePurchaseItem
        purchase = ConsumablePurchase.objects.create(
            supplier=self.supplier,
            applicant=self.user,
            status='approved'
        )
        ConsumablePurchaseItem.objects.create(
            purchase=purchase,
            consumable=self.consumable,
            order_quantity=50,
            received_quantity=50,
            unit_price=25.00
        )

        url = reverse('consumable-purchase-confirm-receipt', kwargs={'pk': purchase.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证库存更新
        self.consumable.refresh_from_db()
        self.assertEqual(self.consumable.current_stock, 50)
```

---

## 3. 前端组件测试

```typescript
// src/views/consumables/__tests__/ConsumableList.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import ConsumableList from '../ConsumableList.vue'
import { getConsumables, getStockSummary } from '@/api/consumables'

vi.mock('@/api/consumables')

describe('ConsumableList', () => {
  it('渲染耗材列表', async () => {
    vi.mocked(getConsumables).mockResolvedValue({
      total: 2,
      items: [
        {
          id: 1,
          code: 'HC001',
          name: 'A4打印纸',
          category: { id: 1, name: '纸张类' },
          available_stock: 50,
          max_stock: 100,
          average_price: 25,
          status: 'normal'
        }
      ]
    })

    vi.mocked(getStockSummary).mockResolvedValue({
      total_items: 1,
      total_value: 1250,
      total_low_stock: 0,
      total_out_of_stock: 0
    })

    const wrapper = mount(ConsumableList)
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.find('.consumable-list').exists()).toBe(true)
  })

  it('显示库存统计', async () => {
    vi.mocked(getStockSummary).mockResolvedValue({
      total_items: 100,
      total_value: 50000,
      total_low_stock: 5,
      total_out_of_stock: 2
    })

    const wrapper = mount(ConsumableList)
    await new Promise(resolve => setTimeout(resolve, 100))

    // 验证统计卡片渲染
    expect(wrapper.text()).toContain('100')
    expect(wrapper.text()).toContain('50000')
  })
})
```

---

## 4. E2E测试

```typescript
// e2e/consumables/purchase.spec.ts

import { test, expect } from '@playwright/test'

test.describe('耗材采购流程', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/login')
    await page.fill('[name=username]', 'testuser')
    await page.fill('[name=password]', 'testpass123')
    await page.click('button:has-text("登录")')
  })

  test('创建采购单并入库', async ({ page }) => {
    // 进入采购单列表
    await page.goto('http://localhost:5173/consumables/purchase')
    await page.click('button:has-text("新建采购单")')

    // 填写基础信息
    await page.selectOption('[name=supplier]', '晨光文具')
    await page.selectOption('[name=purchase_type]', 'regular')

    // 添加耗材
    await page.click('button:has-text("添加耗材")')
    await page.click('tbody tr:nth-child(1) .el-checkbox__input')
    await page.click('.el-dialog button:has-text("确定")')

    // 设置数量和单价
    await page.fill('input[aria-label="订购数量"]', '50')
    await page.fill('input[aria-label="单价"]', '25')

    // 提交
    await page.click('button:has-text("创建采购单")')
    await page.waitForSelector('text=采购单创建成功')

    // 审批
    await page.click('button:has-text("审批")')
    await page.click('input[value="approved"]')
    await page.click('.el-dialog button:has-text("确定")')

    // 入库
    await page.click('button:has-text("确认入库")')
    await page.waitForSelector('text=入库成功')

    // 验证库存更新
    await page.goto('http://localhost:5173/consumables')
    await page.waitForSelector('text=50')
  })
})

test.describe('耗材领用流程', () => {
  test('创建并完成领用', async ({ page }) => {
    await page.goto('http://localhost:5173/consumables/issue/create')

    // 填写表单
    await page.fill('[name=issue_date]', '2024-06-15')
    await page.selectOption('[name=issue_type]', 'department')
    await page.selectOption('[name=department]', '研发部')
    await page.fill('[name=purpose]', '项目使用')

    // 添加耗材
    await page.click('button:has-text("添加耗材")')
    await page.click('tbody tr:nth-child(1) .el-checkbox__input')
    await page.click('.el-dialog button:has-text("确定")')

    // 设置数量
    await page.fill('input[aria-label="领用数量"]', '10')

    // 提交
    await page.click('button:has-text("提交领用")')
    await page.waitForSelector('text=领用单已提交')

    // 审批
    await page.goto('http://localhost:5173/consumables/issue')
    await page.click('tbody tr:nth-child(1) button:has-text("审批")')
    await page.click('input[value="approved"]')
    await page.click('.el-dialog button:has-text("确定")')

    // 发放
    await page.click('button:has-text("确认发放")')
    await page.waitForSelector('text=发放成功')

    // 验证库存扣减
    await page.goto('http://localhost:5173/consumables')
    const stockText = await page.textContent('tbody tr:nth-child(1)')
    expect(parseInt(stockText || '0')).toBeLessThan(50)
  })
})
```

---

## 验收标准

### 功能验收

- [ ] 可以创建耗材分类和档案
- [ ] 采购入库后自动更新库存
- [ ] 领用出库时自动检查库存
- [ ] 库存不足时自动预警
- [ ] 可以查看库存流水
- [ ] 支持盘点功能
- [ ] 支持退库功能
- [ ] 加权平均价格计算正确

### 性能验收

- [ ] 列表页面响应时间 < 500ms
- [ ] 库存汇总计算 < 1s
- [ ] 批量更新库存 < 2s

### 测试覆盖率

- [ ] 模型测试覆盖率 > 80%
- [ ] 服务层测试覆盖率 > 80%
- [ ] API接口测试覆盖率 > 90%
