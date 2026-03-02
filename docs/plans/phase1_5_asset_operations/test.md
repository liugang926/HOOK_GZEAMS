# Phase 1.5: 资产领用/调拨/退库业务 - 测试方案

## 测试概览

| 测试类型 | 覆盖范围 | 优先级 |
|---------|---------|--------|
| 单元测试 | 服务层业务逻辑 | P0 |
| API测试 | 接口请求响应 | P0 |
| 前端组件测试 | Vue组件交互 | P1 |
| E2E测试 | 完整业务流程 | P1 |
| 性能测试 | 并发审批场景 | P2 |

---

## 1. 后端单元测试

### 1.1 领用服务测试

```python
# apps/assets/tests/test_pickup_service.py

from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.organizations.models import Department
from apps.assets.models import Asset, AssetPickup, PickupItem
from apps.assets.services.pickup_service import AssetPickupService
from django.core.exceptions import ValidationError


class AssetPickupServiceTest(TestCase):
    """资产领用服务测试"""

    def setUp(self):
        """测试数据准备"""
        self.service = AssetPickupService()

        # 创建用户
        self.applicant = User.objects.create(
            username='zhangsan',
            real_name='张三'
        )
        self.approver = User.objects.create(
            username='lisi',
            real_name='李四'
        )

        # 创建部门
        self.department = Department.objects.create(
            name='研发部',
            code='RD'
        )

        # 创建资产（闲置状态）
        self.asset1 = Asset.objects.create(
            asset_code='ZC2024010001',
            asset_name='MacBook Pro',
            asset_status='idle',
            purchase_price=12000.00
        )
        self.asset2 = Asset.objects.create(
            asset_code='ZC2024010002',
            asset_name='Dell 显示器',
            asset_status='idle',
            purchase_price=3000.00
        )

        # 创建在用资产（不能领用）
        self.asset_in_use = Asset.objects.create(
            asset_code='ZC2024010003',
            asset_name='ThinkPad',
            asset_status='in_use',
            purchase_price=8000.00
        )

    def test_create_pickup_success(self):
        """测试成功创建领用单"""
        data = {
            'department': self.department.id,
            'pickup_date': timezone.now().date(),
            'pickup_reason': '新员工入职',
            'items': [
                {'asset_id': self.asset1.id, 'quantity': 1},
                {'asset_id': self.asset2.id, 'quantity': 1}
            ]
        }

        pickup = self.service.create_pickup(data, self.applicant)

        self.assertEqual(pickup.applicant, self.applicant)
        self.assertEqual(pickup.department, self.department)
        self.assertEqual(pickup.status, 'draft')
        self.assertEqual(pickup.items.count(), 2)
        self.assertTrue(pickup.pickup_no.startswith('LY'))

    def test_create_pickup_with_in_use_asset_fails(self):
        """测试领用在用资产应失败"""
        data = {
            'department': self.department.id,
            'pickup_date': timezone.now().date(),
            'pickup_reason': '测试',
            'items': [
                {'asset_id': self.asset_in_use.id, 'quantity': 1}
            ]
        }

        with self.assertRaises(ValidationError) as context:
            self.service.create_pickup(data, self.applicant)

        self.assertTrue('已被使用' in str(context.exception))

    def test_submit_pickup(self):
        """测试提交领用单"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='draft'
        )

        result = self.service.submit_pickup(pickup.id, self.applicant)

        self.assertEqual(result.status, 'pending')

    def test_submit_pickup_by_other_user_fails(self):
        """测试非申请人提交应失败"""
        other_user = User.objects.create(username='wangwu', real_name='王五')
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='draft'
        )

        with self.assertRaises(PermissionError):
            self.service.submit_pickup(pickup.id, other_user)

    def test_approve_pickup_success(self):
        """测试审批通过"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='pending'
        )
        PickupItem.objects.create(
            pickup=pickup,
            asset=self.asset1,
            quantity=1
        )

        result = self.service.approve_pickup(
            pickup.id,
            self.approver,
            'approved',
            '同意领用'
        )

        self.assertEqual(result.status, 'approved')
        self.assertEqual(result.approved_by, self.approver)

        # 验证资产状态变更
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.asset_status, 'in_use')
        self.assertEqual(self.asset1.custodian, self.applicant)

    def test_approve_pickup_reject(self):
        """测试审批拒绝"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='pending'
        )

        result = self.service.approve_pickup(
            pickup.id,
            self.approver,
            'rejected',
            '暂不需要'
        )

        self.assertEqual(result.status, 'rejected')

        # 验证资产状态未变更
        self.asset1.refresh_from_db()
        self.assertEqual(self.asset1.asset_status, 'idle')

    def test_approve_non_pending_pickup_fails(self):
        """测试审批非待审批状态应失败"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='draft'
        )

        with self.assertRaises(ValidationError):
            self.service.approve_pickup(
                pickup.id,
                self.approver,
                'approved',
                ''
            )

    def test_complete_pickup(self):
        """测试完成领用"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='approved'
        )

        result = self.service.complete_pickup(pickup.id, self.applicant)

        self.assertEqual(result.status, 'completed')
        self.assertIsNotNone(result.completed_at)

    def test_cancel_pickup(self):
        """测试取消领用单"""
        pickup = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department,
            status='pending'
        )

        result = self.service.cancel_pickup(pickup.id, self.applicant)

        self.assertEqual(result.status, 'cancelled')

    def test_pickup_no_generation(self):
        """测试领用单号生成"""
        from datetime import datetime
        prefix = datetime.now().strftime('%Y%m')

        pickup1 = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department
        )
        pickup2 = AssetPickup.objects.create(
            applicant=self.applicant,
            department=self.department
        )

        self.assertTrue(pickup1.pickup_no.startswith(f'LY{prefix}'))
        self.assertTrue(pickup2.pickup_no.startswith(f'LY{prefix}'))
        self.assertNotEqual(pickup1.pickup_no, pickup2.pickup_no)
```

### 1.2 调拨服务测试

```python
# apps/assets/tests/test_transfer_service.py

class AssetTransferServiceTest(TestCase):
    """资产调拨服务测试"""

    def setUp(self):
        self.service = AssetTransferService()

        self.from_dept = Department.objects.create(name='研发部', code='RD')
        self.to_dept = Department.objects.create(name='市场部', code='MKT')
        self.manager1 = User.objects.create(username='mgr1', real_name='王经理')
        self.manager2 = User.objects.create(username='mgr2', real_name='赵经理')

        self.from_dept.manager = self.manager1
        self.to_dept.manager = self.manager2
        self.from_dept.save()
        self.to_dept.save()

        self.location1 = Location.objects.create(name='3楼A区')
        self.location2 = Location.objects.create(name='5楼B区')

        self.asset = Asset.objects.create(
            asset_code='ZC2024010001',
            asset_name='MacBook Pro',
            asset_status='in_use',
            department=self.from_dept,
            location=self.location1,
            purchase_price=12000.00
        )

    def test_create_transfer_success(self):
        """测试成功创建调拨单"""
        data = {
            'from_department': self.from_dept.id,
            'to_department': self.to_dept.id,
            'transfer_date': timezone.now().date(),
            'transfer_reason': '项目调整',
            'items': [
                {
                    'asset_id': self.asset.id,
                    'to_location': self.location2.id
                }
            ]
        }

        transfer = self.service.create_transfer(data, self.manager1)

        self.assertEqual(transfer.from_department, self.from_dept)
        self.assertEqual(transfer.to_department, self.to_dept)
        self.assertEqual(transfer.status, 'draft')
        self.assertTrue(transfer.transfer_no.startswith('DB'))

    def test_create_transfer_same_department_fails(self):
        """测试同一部门调拨应失败"""
        data = {
            'from_department': self.from_dept.id,
            'to_department': self.from_dept.id,
            'transfer_date': timezone.now().date(),
            'items': [{'asset_id': self.asset.id}]
        }

        with self.assertRaises(ValidationError):
            self.service.create_transfer(data, self.manager1)

    def test_create_transfer_asset_not_in_from_dept_fails(self):
        """测试调拨不属于调出部门的资产应失败"""
        other_dept = Department.objects.create(name='其他部门')
        asset_other = Asset.objects.create(
            asset_code='ZC2024010002',
            asset_name='其他资产',
            department=other_dept,
            purchase_price=5000.00
        )

        data = {
            'from_department': self.from_dept.id,
            'to_department': self.to_dept.id,
            'items': [{'asset_id': asset_other.id}]
        }

        with self.assertRaises(ValidationError):
            self.service.create_transfer(data, self.manager1)

    def test_approve_from_success(self):
        """测试调出方审批成功"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='pending'
        )

        result = self.service.approve_from(
            transfer.id,
            self.manager1,
            '同意调出'
        )

        self.assertEqual(result.status, 'out_approved')
        self.assertEqual(result.from_approved_by, self.manager1)

    def test_approve_from_by_non_manager_fails(self):
        """测试非部门负责人审批应失败"""
        other_user = User.objects.create(username='other', real_name='其他')
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='pending'
        )

        with self.assertRaises(PermissionError):
            self.service.approve_from(transfer.id, other_user)

    def test_approve_to_without_from_approval_fails(self):
        """测试未经调出方审批，调入方审批应失败"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='pending'
        )

        with self.assertRaises(ValidationError):
            self.service.approve_to(transfer.id, self.manager2)

    def test_complete_transfer(self):
        """测试完成调拨"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='approved'
        )
        TransferItem.objects.create(
            transfer=transfer,
            asset=self.asset,
            from_location=self.location1,
            to_location=self.location2
        )

        result = self.service.complete_transfer(transfer.id, self.manager1)

        self.assertEqual(result.status, 'completed')

        # 验证资产已转移
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.department, self.to_dept)
        self.assertEqual(self.asset.location, self.location2)

    def test_transfer_log_created(self):
        """测试调拨履历已创建"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='approved'
        )
        TransferItem.objects.create(
            transfer=transfer,
            asset=self.asset,
            from_location=self.location1,
            to_location=self.location2
        )

        self.service.complete_transfer(transfer.id, self.manager1)

        log = AssetTransferLog.objects.filter(
            asset=self.asset,
            transfer=transfer
        ).first()

        self.assertIsNotNone(log)
        self.assertEqual(log.from_department, self.from_dept)
        self.assertEqual(log.to_department, self.to_dept)
```

### 1.3 退库服务测试

```python
# apps/assets/tests/test_return_service.py

class AssetReturnServiceTest(TestCase):
    """资产退库服务测试"""

    def setUp(self):
        self.service = AssetReturnService()

        self.user = User.objects.create(username='zhangsan', real_name='张三')
        self.location = Location.objects.create(name='仓库A区')

        self.asset = Asset.objects.create(
            asset_code='ZC2024010001',
            asset_name='MacBook Pro',
            asset_status='in_use',
            custodian=self.user,
            purchase_price=12000.00
        )

    def test_create_return_success(self):
        """测试创建退库单成功"""
        data = {
            'return_date': timezone.now().date(),
            'return_reason': '项目结束',
            'return_location': self.location.id,
            'items': [
                {
                    'asset_id': self.asset.id,
                    'asset_status': 'idle',
                    'condition_description': '完好'
                }
            ]
        }

        asset_return = self.service.create_return(data, self.user)

        self.assertEqual(asset_return.returner, self.user)
        self.assertEqual(asset_return.status, 'pending')

    def test_create_return_asset_not_custodian_fails(self):
        """测试非保管人退库应失败"""
        other_user = User.objects.create(username='lisi', real_name='李四')

        data = {
            'return_location': self.location.id,
            'items': [{'asset_id': self.asset.id}]
        }

        with self.assertRaises(ValidationError):
            self.service.create_return(data, other_user)

    def test_confirm_return(self):
        """测试确认退库"""
        asset_return = AssetReturn.objects.create(
            returner=self.user,
            return_location=self.location,
            status='pending'
        )
        ReturnItem.objects.create(
            asset_return=asset_return,
            asset=self.asset,
            asset_status='idle'
        )

        result = self.service.confirm_return(asset_return.id, self.user)

        self.assertEqual(result.status, 'completed')

        # 验证资产状态
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'idle')
        self.assertIsNone(self.asset.custodian)
        self.assertEqual(self.asset.location, self.location)
```

### 1.4 借用服务测试

```python
# apps/assets/tests/test_loan_service.py

class AssetLoanServiceTest(TestCase):
    """资产借用服务测试"""

    def setUp(self):
        self.service = AssetLoanService()
        self.user = User.objects.create(username='zhangsan', real_name='张三')

        self.asset = Asset.objects.create(
            asset_code='ZC2024010001',
            asset_name='iPad Pro',
            asset_status='idle',
            purchase_price=6000.00
        )

    def test_create_loan_success(self):
        """测试创建借用单成功"""
        from datetime import timedelta

        borrow_date = timezone.now().date()
        return_date = borrow_date + timedelta(days=15)

        data = {
            'borrow_date': borrow_date,
            'expected_return_date': return_date,
            'loan_reason': '临时出差',
            'items': [{'asset_id': self.asset.id}]
        }

        loan = self.service.create_loan(data, self.user)

        self.assertEqual(loan.borrower, self.user)
        self.assertEqual(loan.status, 'pending')

    def test_create_loan_return_date_before_borrow_fails(self):
        """测试归还日期早于借出日期应失败"""
        borrow_date = timezone.now().date()
        return_date = borrow_date - timedelta(days=1)

        data = {
            'borrow_date': borrow_date,
            'expected_return_date': return_date,
            'items': [{'asset_id': self.asset.id}]
        }

        with self.assertRaises(ValidationError):
            self.service.create_loan(data, self.user)

    def test_create_loan_exceeds_90_days_fails(self):
        """测试借用期限超过90天应失败"""
        borrow_date = timezone.now().date()
        return_date = borrow_date + timedelta(days=91)

        data = {
            'borrow_date': borrow_date,
            'expected_return_date': return_date,
            'items': [{'asset_id': self.asset.id}]
        }

        with self.assertRaises(ValidationError):
            self.service.create_loan(data, self.user)

    def test_approve_loan(self):
        """测试审批借用单"""
        loan = AssetLoan.objects.create(
            borrower=self.user,
            expected_return_date=timezone.now().date() + timedelta(days=15),
            status='pending'
        )

        result = self.service.approve_loan(
            loan.id,
            self.user,
            'approved'
        )

        self.assertEqual(result.status, 'approved')

    def test_confirm_borrow(self):
        """测试确认借出"""
        loan = AssetLoan.objects.create(
            borrower=self.user,
            expected_return_date=timezone.now().date() + timedelta(days=15),
            status='approved'
        )
        LoanItem.objects.create(loan=loan, asset=self.asset)

        result = self.service.confirm_borrow(loan.id, self.user)

        self.assertEqual(result.status, 'borrowed')

        # 验证资产状态
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'in_use')

    def test_confirm_return(self):
        """测试确认归还"""
        loan = AssetLoan.objects.create(
            borrower=self.user,
            status='borrowed'
        )
        LoanItem.objects.create(loan=loan, asset=self.asset)

        result = self.service.confirm_return(
            loan.id,
            self.user,
            'good'
        )

        self.assertEqual(result.status, 'returned')

        # 验证资产状态
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.asset_status, 'idle')

    def test_check_overdue_loans(self):
        """测试检查逾期借用"""
        past_date = timezone.now().date() - timedelta(days=10)
        loan = AssetLoan.objects.create(
            borrower=self.user,
            expected_return_date=past_date,
            status='borrowed'
        )

        count = self.service.check_overdue_loans()

        self.assertGreater(count, 0)
        loan.refresh_from_db()
        self.assertEqual(loan.status, 'overdue')
```

---

## 2. API测试

### 2.1 领用单API测试

```python
# apps/assets/tests/test_pickup_api.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse


class PickupAPITest(APITestCase):
    """领用单API测试"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.department = Department.objects.create(name='研发部')
        self.asset = Asset.objects.create(
            asset_code='ZC001',
            asset_name='测试资产',
            asset_status='idle',
            purchase_price=10000
        )

    def test_list_pickups(self):
        """测试获取领用单列表"""
        url = reverse('asset-pickup-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)

    def test_create_pickup(self):
        """测试创建领用单"""
        url = reverse('asset-pickup-list')
        data = {
            'department': self.department.id,
            'pickup_date': '2024-06-15',
            'pickup_reason': '测试领用',
            'items': [{'asset_id': self.asset.id}]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('pickup_no', response.data)

    def test_create_pickup_invalid_asset(self):
        """测试使用无效资产创建领用单"""
        url = reverse('asset-pickup-list')
        data = {
            'department': self.department.id,
            'pickup_date': '2024-06-15',
            'pickup_reason': '测试',
            'items': [{'asset_id': 99999}]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_pickup(self):
        """测试提交领用单"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.department,
            status='draft'
        )
        url = reverse('asset-pickup-submit', kwargs={'pk': pickup.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')

    def test_approve_pickup(self):
        """测试审批领用单"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.department,
            status='pending'
        )
        PickupItem.objects.create(
            pickup=pickup,
            asset=self.asset
        )
        url = reverse('asset-pickup-approve', kwargs={'pk': pickup.id})

        response = self.client.post(url, {
            'approval': 'approved',
            'comment': '同意'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')

    def test_complete_pickup(self):
        """测试完成领用"""
        pickup = AssetPickup.objects.create(
            applicant=self.user,
            department=self.department,
            status='approved'
        )
        url = reverse('asset-pickup-complete', kwargs={'pk': pickup.id})

        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
```

### 2.2 调拨单API测试

```python
# apps/assets/tests/test_transfer_api.py

class TransferAPITest(APITestCase):
    """调拨单API测试"""

    def test_create_transfer(self):
        """测试创建调拨单"""
        from_dept = Department.objects.create(name='研发部')
        to_dept = Department.objects.create(name='市场部')

        url = reverse('asset-transfer-list')
        data = {
            'from_department': from_dept.id,
            'to_department': to_dept.id,
            'transfer_date': '2024-06-15',
            'items': [{'asset_id': self.asset.id, 'to_location': 1}]
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_approve_from(self):
        """测试调出方审批"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='pending'
        )
        url = reverse('asset-transfer-approve-from', kwargs={'pk': transfer.id})

        response = self.client.post(url, {'comment': '同意'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_approve_to(self):
        """测试调入方审批"""
        transfer = AssetTransfer.objects.create(
            from_department=self.from_dept,
            to_department=self.to_dept,
            status='out_approved'
        )
        url = reverse('asset-transfer-approve-to', kwargs={'pk': transfer.id})

        response = self.client.post(url, {'comment': '同意接收'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

---

## 3. 前端组件测试

### 3.1 领用单列表组件测试

```typescript
// src/views/assets/operations/__tests__/PickupList.test.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import PickupList from '../PickupList.vue'
import { getPickupList, cancelPickup } from '@/api/assets/pickup'

vi.mock('@/api/assets/pickup')
vi.mock('vue-router')

describe('PickupList', () => {
  let wrapper: VueWrapper

  const mockPickups = [
    {
      id: 1,
      pickup_no: 'LY20240601001',
      applicant: { id: 5, real_name: '张三' },
      department: { id: 3, name: '研发部' },
      pickup_date: '2024-06-01',
      status: 'pending',
      items_count: 2,
      created_at: '2024-06-01T10:00:00Z'
    },
    {
      id: 2,
      pickup_no: 'LY20240602001',
      applicant: { id: 6, real_name: '李四' },
      department: { id: 5, name: '市场部' },
      pickup_date: '2024-06-02',
      status: 'approved',
      items_count: 1,
      created_at: '2024-06-02T10:00:00Z'
    }
  ]

  beforeEach(() => {
    vi.mocked(getPickupList).mockResolvedValue({
      total: 2,
      page: 1,
      page_size: 20,
      items: mockPickups
    })
  })

  it('渲染领用单列表', async () => {
    wrapper = mount(PickupList)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.pickup-list').exists()).toBe(true)
  })

  it('显示领用单数据', async () => {
    wrapper = mount(PickupList)
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const tableRows = wrapper.findAll('el-table-column')
    expect(tableRows.length).toBeGreaterThan(0)
  })

  it('点击新建按钮跳转到创建页面', async () => {
    const push = vi.fn()
    vi.mocked(useRouter).mockReturnValue({ push } as any)

    wrapper = mount(PickupList)
    const createBtn = wrapper.find('[type="primary"]')
    await createBtn.trigger('click')

    expect(push).toHaveBeenCalledWith('/assets/operations/pickup/create')
  })

  it('状态过滤功能', async () => {
    wrapper = mount(PickupList)

    const statusSelect = wrapper.find('[placeholder="全部状态"]')
    await statusSelect.setValue('pending')

    expect(wrapper.vm.filterForm.status).toBe('pending')
  })

  it('取消领用单', async () => {
    vi.mocked(cancelPickup).mockResolvedValue(undefined)
    vi.spyOn(ElMessage, 'success')

    wrapper = mount(PickupList)
    wrapper.vm.handleCancel(mockPickups[0])
    await wrapper.vm.$nextTick()

    // 需要模拟 confirm dialog
    expect(cancelPickup).toHaveBeenCalledWith(1)
  })
})
```

### 3.2 领用单表单组件测试

```typescript
// src/views/assets/operations/__tests__/PickupForm.test.ts

describe('PickupForm', () => {
  it('验证必填字段', async () => {
    const wrapper = mount(PickupForm)
    const formRef = wrapper.findComponent({ ref: 'formRef' })

    const isValid = await formRef.validate()
    expect(isValid).toBe(false)
  })

  it('添加资产到明细', async () => {
    const wrapper = mount(PickupForm)
    const mockAsset = {
      id: 1,
      asset_code: 'ZC001',
      asset_name: '测试资产'
    }

    wrapper.vm.handleAssetSelect([mockAsset])

    expect(wrapper.vm.form.items).toHaveLength(1)
    expect(wrapper.vm.form.items[0].asset).toEqual(mockAsset)
  })

  it('移除明细项', async () => {
    const wrapper = mount(PickupForm)
    wrapper.vm.form.items = [
      { asset: { id: 1 }, quantity: 1, remark: '' }
    ]

    wrapper.vm.handleRemoveItem(0)

    expect(wrapper.vm.form.items).toHaveLength(0)
  })

  it('提交领用单', async () => {
    vi.mocked(createPickup).mockResolvedValue({
      pickup_no: 'LY20240615001'
    })

    const wrapper = mount(PickupForm)
    wrapper.vm.form = {
      department: 1,
      pickup_date: '2024-06-15',
      pickup_reason: '测试',
      items: [{ asset: { id: 1 }, quantity: 1 }]
    }

    await wrapper.vm.handleSubmit()

    expect(createPickup).toHaveBeenCalled()
  })
})
```

### 3.3 资产选择器测试

```typescript
// src/views/assets/operations/components/__tests__/AssetSelector.test.ts

describe('AssetSelector', () => {
  it('加载资产列表', async () => {
    vi.mocked(getAssetList).mockResolvedValue({
      total: 10,
      items: [
        { id: 1, asset_code: 'ZC001', asset_name: '资产1' },
        { id: 2, asset_code: 'ZC002', asset_name: '资产2' }
      ]
    })

    const wrapper = mount(AssetSelector, {
      props: {
        modelValue: true
      }
    })

    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.vm.tableData).toHaveLength(2)
  })

  it '排除已选资产', async () => {
    vi.mocked(getAssetList).mockResolvedValue({
      total: 3,
      items: [
        { id: 1, asset_code: 'ZC001' },
        { id: 2, asset_code: 'ZC002' },
        { id: 3, asset_code: 'ZC003' }
      ]
    })

    const wrapper = mount(AssetSelector, {
      props: {
        modelValue: true,
        excludeAssetIds: [1]
      }
    })

    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.vm.tableData).toHaveLength(2)
  })

  it('确认选择资产', async () => {
    const wrapper = mount(AssetSelector, {
      props: {
        modelValue: true
      }
    })

    wrapper.vm.selectedAssets = [{ id: 1 }]
    wrapper.vm.handleConfirm()

    expect(wrapper.emitted('confirm')).toBeTruthy()
    expect(wrapper.emitted('confirm')![0]).toEqual([[{ id: 1 }]])
  })
})
```

---

## 4. E2E测试

### 4.1 领用完整流程测试

```typescript
// e2e/assets/pickup.spec.ts

import { test, expect } from '@playwright/test'

test.describe('资产领用流程', () => {
  test.beforeEach(async ({ page }) => {
    // 登录
    await page.goto('http://localhost:5173/login')
    await page.fill('[name=username]', 'testuser')
    await page.fill('[name=password]', 'testpass123')
    await page.click('button:has-text("登录")')
    await page.waitForURL('http://localhost:5173/')
  })

  test('创建并提交领用单', async ({ page }) => {
    // 导航到领用单列表
    await page.click('text=资产领用')
    await page.waitForURL('**/assets/operations/pickup')

    // 点击新建
    await page.click('button:has-text("新建领用单")')
    await page.waitForURL('**/assets/operations/pickup/create')

    // 填写表单
    await page.selectOption('[name=department]', '研发部')
    await page.fill('[name=pickup_reason]', 'E2E测试领用')

    // 添加资产
    await page.click('button:has-text("添加资产")')
    await page.waitForSelector('.el-dialog')

    // 在资产选择器中选择资产
    await page.click('tbody tr:nth-child(1) .el-checkbox__input')
    await page.click('.el-dialog button:has-text("确定")')

    // 提交审批
    await page.click('button:has-text("提交审批")')

    // 验证成功消息
    await page.waitForSelector('text=领用单创建成功')

    // 验证跳转
    await page.waitForURL('**/assets/operations/pickup/**')
  })

  test('审批领用单', async ({ page }) => {
    // 进入待审批列表
    await page.goto('http://localhost:5173/assets/operations/pickup')
    await page.selectOption('[placeholder=全部状态]', '待审批')
    await page.waitForTimeout(500)

    // 点击审批按钮
    await page.click('tbody tr:nth-child(1) button:has-text("审批")')
    await page.waitForSelector('.el-dialog')

    // 选择同意并填写意见
    await page.click('input[value="approved"]')
    await page.fill('textarea[name=comment]', 'E2E测试审批通过')

    // 确认审批
    await page.click('.el-dialog button:has-text("确定")')

    // 验证成功消息
    await page.waitForSelector('text=审批成功')
  })

  test('完成领用单', async ({ page }) => {
    // 进入已批准列表
    await page.goto('http://localhost:5173/assets/operations/pickup')
    await page.selectOption('[placeholder=全部状态]', '已批准')
    await page.waitForTimeout(500)

    // 点击完成按钮
    await page.click('tbody tr:nth-child(1) button:has-text("完成")')

    // 确认对话框
    await page.click('.el-message-box__btns button:has-text("确认")')

    // 验证成功消息
    await page.waitForSelector('text=领用单已完成')
  })
})
```

### 4.2 调拨完整流程测试

```typescript
// e2e/assets/transfer.spec.ts

test.describe('资产调拨流程', () => {
  test('创建调拨单', async ({ page }) => {
    await page.goto('http://localhost:5173/assets/operations/transfer')
    await page.click('button:has-text("新建调拨单")')

    // 选择调出部门
    await page.click('[name=from_department]')
    await page.click('text=研发部')

    // 选择调入部门
    await page.click('[name=to_department]')
    await page.click('text=市场部')

    // 添加资产
    await page.click('button:has-text("添加资产")')
    await page.click('tbody tr:nth-child(1) .el-checkbox__input')
    await page.click('.el-dialog button:has-text("确定")')

    // 保存调拨单
    await page.click('button:has-text("保存")')
    await page.waitForSelector('text=调拨单创建成功')
  })

  test('双方审批调拨单', async ({ page }) => {
    await page.goto('http://localhost:5173/assets/operations/transfer/1')

    // 调出方审批
    await page.click('button:has-text("调出方审批")')
    await page.fill('textarea[name=comment]', '同意调出')
    await page.click('button:has-text("确定")')

    // 等待状态变更
    await page.waitForSelector('text=调出方已批准')

    // 切换用户为调入部门负责人
    // (在实际测试中需要重新登录)
  })
})
```

### 4.3 借用归还流程测试

```typescript
// e2e/assets/loan.spec.ts

test.describe('资产借用流程', () => {
  test('创建借用单并归还', async ({ page }) => {
    // 创建借用单
    await page.goto('http://localhost:5173/assets/operations/loan/create')

    await page.fill('[name=borrow_date]', '2024-06-15')
    await page.fill('[name=expected_return_date]', '2024-06-30')
    await page.fill('[name=loan_reason]', 'E2E测试借用')

    // 选择资产
    await page.click('button:has-text("选择资产")')
    await page.click('tbody tr:nth-child(1) .el-checkbox__input')
    await page.click('.el-dialog button:has-text("确定")')

    // 提交
    await page.click('button:has-text("提交审批")')
    await page.waitForSelector('text=已提交审批')

    // 审批并借出
    await page.goto('http://localhost:5173/assets/operations/loan')
    await page.click('tbody tr:nth-child(1) button:has-text("审批")')
    await page.click('input[value="approved"]')
    await page.click('button:has-text("确定")')

    // 确认借出
    await page.click('button:has-text("确认借出")')

    // 归还
    await page.click('button:has-text("确认归还")')
    await page.selectOption('[name=condition]', 'good')
    await page.click('button:has-text("确定")')

    await page.waitForSelector('text=归还成功')
  })
})
```

---

## 5. 性能测试

### 5.1 并发审批测试

```python
# apps/assets/tests/test_performance.py

from django.test import TestCase
from concurrent.futures import ThreadPoolExecutor
import time


class ConcurrentApprovalTest(TestCase):
    """并发审批性能测试"""

    def setUp(self):
        # 创建100个待审批的领用单
        self.pickups = []
        for i in range(100):
            pickup = AssetPickup.objects.create(
                applicant=User.objects.first(),
                department=Department.objects.first(),
                status='pending'
            )
            self.pickups.append(pickup)

    def test_concurrent_approval_performance(self):
        """测试并发审批性能"""
        def approve_pickup(pickup_id):
            start = time.time()
            service = AssetPickupService()
            service.approve_pickup(
                pickup_id,
                User.objects.first(),
                'approved',
                ''
            )
            return time.time() - start

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(approve_pickup, [p.id for p in self.pickups]))

        avg_time = sum(results) / len(results)
        max_time = max(results)

        # 断言平均响应时间小于500ms
        self.assertLess(avg_time, 0.5)
        # 断言最大响应时间小于2秒
        self.assertLess(max_time, 2.0)

    def test_batch_operation_performance(self):
        """测试批量操作性能"""
        service = AssetPickupService()

        start = time.time()

        # 批量获取
        result = service.get_pickup_list({
            'status': 'pending',
            'page': 1,
            'page_size': 100
        })

        elapsed = time.time() - start

        self.assertLess(elapsed, 0.3)
        self.assertEqual(len(result['items']), 100)
```

---

## 验收标准

### 功能验收

- [ ] 可以创建资产领用单
- [ ] 可以审批领用单并自动变更资产状态
- [ ] 可以创建资产调拨单
- [ ] 跨部门调拨需要双方审批
- [ ] 可以创建借用单并完成借还流程
- [ ] 退库后资产状态正确变更
- [ ] 借用逾期自动检测
- [ ] 调拨履历正确记录

### 性能验收

- [ ] 列表页面响应时间 < 500ms
- [ ] 表单提交响应时间 < 1s
- [ ] 并发审批支持10+用户同时操作
- [ ] 批量操作100条数据 < 2s

### 测试覆盖率

- [ ] 服务层单元测试覆盖率 > 80%
- [ ] API接口测试覆盖率 > 90%
- [ ] 前端组件测试覆盖率 > 70%
- [ ] E2E场景覆盖主要业务流程
