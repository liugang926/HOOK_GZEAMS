# Phase 4.5: 盘点业务链条 - 测试计划

## 1. 测试概述

### 1.1 测试范围

| 模块 | 测试内容 |
|------|----------|
| 差异认定 | 差异分析、差异认定、批量操作 |
| 差异处理 | 处理单创建、审批流程、执行处理 |
| 资产调账 | 调账记录、调账执行、调账回滚 |
| 盘点报告 | 报告生成、报告审批、报告导出 |

### 1.2 测试策略

| 测试类型 | 工具/框架 | 覆盖范围 |
|----------|-----------|----------|
| 单元测试 | pytest | 模型方法、服务层逻辑 |
| API测试 | pytest + requests | REST API接口 |
| 集成测试 | pytest + factory_boy | 完整业务流程 |
| E2E测试 | Playwright | 用户操作流程 |

---

## 2. 单元测试

### 2.1 差异分析服务测试

```python
# apps/inventory/tests/test_difference_service.py

import pytest
from apps.inventory.services import DifferenceAnalysisService
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventorySnapshotItem,
    InventoryDifference, ScanRecord
)


@pytest.mark.django_db
class TestDifferenceAnalysisService:
    """差异分析服务测试"""

    def test_analyze_loss_differences(self, completed_task_with_snapshot):
        """测试分析盘亏差异"""
        task = completed_task_with_snapshot

        # 模拟扫描记录（部分资产未扫描）
        differences = DifferenceAnalysisService.analyze_task_differences(task.id)

        # 验证盘亏差异被识别
        loss_diffs = [d for d in differences if d.difference_type == 'loss']
        assert len(loss_diffs) > 0

    def test_analyze_surplus_differences(self, completed_task):
        """测试分析盘盈差异"""
        task = completed_task

        # 添加额外的扫描记录（不在快照中的资产）
        asset = Asset.objects.create(
            asset_no="ZC2024999999",
            asset_name="额外资产",
            org=task.org,
        )
        ScanRecord.objects.create(
            task=task,
            asset=asset,
            location_id=1,
            scan_time=timezone.now(),
            org=task.org,
        )

        differences = DifferenceAnalysisService.analyze_task_differences(task.id)

        # 验证盘盈差异被识别
        surplus_diffs = [d for d in differences if d.difference_type == 'surplus']
        assert len(surplus_diffs) > 0

    def test_analyze_location_mismatch(self, completed_task):
        """测试分析位置不符"""
        task = completed_task
        snapshot = InventorySnapshot.objects.get(task=task)

        # 获取一个快照明细
        snapshot_item = snapshot.items.first()

        # 扫描到不同位置
        ScanRecord.objects.create(
            task=task,
            asset=snapshot_item.asset,
            location_id=snapshot_item.location_id + 1,
            scan_time=timezone.now(),
            org=task.org,
        )

        differences = DifferenceAnalysisService.analyze_task_differences(task.id)

        # 验证位置不符差异被识别
        location_diffs = [
            d for d in differences
            if d.difference_type == 'location_mismatch'
        ]
        assert len(location_diffs) > 0

    def test_no_differences_when_perfect_scan(self, completed_task):
        """测试完全扫描时无差异"""
        task = completed_task
        snapshot = InventorySnapshot.objects.get(task=task)

        # 扫描所有快照资产到正确位置
        for item in snapshot.items.all():
            ScanRecord.objects.get_or_create(
                task=task,
                asset=item.asset,
                defaults={
                    'location_id': item.location_id,
                    'scan_time': timezone.now(),
                    'org': task.org,
                }
            )

        differences = DifferenceAnalysisService.analyze_task_differences(task.id)

        # 应该没有差异
        assert len(differences) == 0
```

### 2.2 差异认定服务测试

```python
# apps/inventory/tests/test_confirmation_service.py

@pytest.mark.django_db
class TestDifferenceConfirmationService:
    """差异认定服务测试"""

    def test_confirm_difference(self, pending_difference, user):
        """测试认定差异"""
        from apps.inventory.services import DifferenceConfirmationService

        data = {
            'confirmation_note': '确认盘亏',
            'responsible_user_id': user.id,
            'responsible_department_id': user.department_id,
        }

        result = DifferenceConfirmationService.confirm_difference(
            pending_difference.id, user, data
        )

        assert result.status == 'confirmed'
        assert result.confirmed_by == user
        assert result.responsible_user == user

    def test_batch_confirm_differences(self, pending_differences, user):
        """测试批量认定"""
        from apps.inventory.services import DifferenceConfirmationService

        diff_ids = [d.id for d in pending_differences]
        data = {
            'confirmation_note': '批量认定',
            'responsible_user_id': user.id,
        }

        count = DifferenceConfirmationService.batch_confirm(diff_ids, user, data)

        assert count == len(diff_ids)

        # 验证状态更新
        for diff in pending_differences:
            diff.refresh_from_db()
            assert diff.status == 'confirmed'

    def test_get_approval_level_for_small_loss(self, small_loss_difference):
        """测试小额盘亏的审批级别"""
        from apps.inventory.services import DifferenceConfirmationService

        level = DifferenceConfirmationService.get_approval_level(small_loss_difference)

        assert level == 1  # 只需资产管理员审批

    def test_get_approval_level_for_large_loss(self, large_loss_difference):
        """测试大额盘亏的审批级别"""
        from apps.inventory.services import DifferenceConfirmationService

        level = DifferenceConfirmationService.get_approval_level(large_loss_difference)

        assert level >= 2  # 需要更高级别审批

    def test_get_approval_level_for_location_mismatch(self, location_mismatch_difference):
        """测试位置不符的审批级别"""
        from apps.inventory.services import DifferenceConfirmationService

        level = DifferenceConfirmationService.get_approval_level(location_mismatch_difference)

        assert level == 1  # 位置调整只需一级审批
```

### 2.3 差异处理服务测试

```python
# apps/inventory/tests/test_resolution_service.py

@pytest.mark.django_db
class TestDifferenceResolutionService:
    """差异处理服务测试"""

    def test_create_resolution(self, task, confirmed_differences, user):
        """测试创建处理单"""
        from apps.inventory.services import DifferenceResolutionService

        diff_ids = [d.id for d in confirmed_differences]
        data = {
            'task_id': task.id,
            'action': 'adjust_account',
            'description': '批量调整账面',
            'difference_ids': diff_ids,
        }

        resolution = DifferenceResolutionService.create_resolution(user, task.id, data)

        assert resolution.status == 'draft'
        assert resolution.action == 'adjust_account'
        assert resolution.differences.count() == len(diff_ids)

    def test_submit_resolution(self, draft_resolution):
        """测试提交处理"""
        from apps.inventory.services import DifferenceResolutionService

        result = DifferenceResolutionService.submit_resolution(draft_resolution.id)

        assert result.status == 'submitted'
        assert result.current_approver is not None

    def test_approve_resolution(self, submitted_resolution, approver):
        """测试审批通过"""
        from apps.inventory.services import DifferenceResolutionService

        result = DifferenceResolutionService.approve_resolution(
            submitted_resolution.id,
            approver,
            approved=True,
            note='同意'
        )

        assert result.status in ['approved', 'completed']
        assert result.approved_by == approver

        # 验证差异状态更新
        for diff in result.differences.all():
            assert diff.status in ['resolved', 'processing']

    def test_reject_resolution(self, submitted_resolution, approver):
        """测试审批拒绝"""
        from apps.inventory.services import DifferenceResolutionService

        result = DifferenceResolutionService.approve_resolution(
            submitted_resolution.id,
            approver,
            approved=False,
            note='处理方案不当'
        )

        assert result.status == 'rejected'
        assert result.approval_note == '处理方案不当'

    def test_execute_adjust_account_action(self, resolution_with_location_mismatch):
        """测试执行调账处理"""
        from apps.inventory.services.difference_service import DifferenceResolutionService

        # 模拟审批通过后执行
        resolution = resolution_with_location_mismatch
        resolution.status = 'approved'
        resolution.approved_by = resolution.current_approver
        resolution.save()

        DifferenceResolutionService._execute_resolution(resolution)

        # 验证调账记录生成
        assert resolution.adjustments.count() > 0

        # 验证资产位置已更新
        for diff in resolution.differences.all():
            if diff.difference_type == 'location_mismatch':
                diff.asset.refresh_from_db()
                assert diff.asset.location == diff.actual_location
```

### 2.4 资产调账服务测试

```python
# apps/inventory/tests/test_adjustment_service.py

@pytest.mark.django_db
class TestAssetAdjustmentService:
    """资产调账服务测试"""

    def test_adjust_location(self, location_mismatch_difference, resolution):
        """测试位置调整"""
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        original_location = location_mismatch_difference.asset.location

        AssetAdjustmentService.adjust_asset_from_difference(
            location_mismatch_difference, resolution
        )

        # 验证调账记录
        assert location_mismatch_difference.adjustment is not None
        adjustment = location_mismatch_difference.adjustment
        assert adjustment.adjustment_type == 'location'
        assert adjustment.status == 'completed'

        # 验证资产位置已更新
        location_mismatch_difference.asset.refresh_from_db()
        assert location_mismatch_difference.asset.location == location_mismatch_difference.actual_location
        assert location_mismatch_difference.asset.location != original_location

    def test_adjust_status(self, status_mismatch_difference, resolution):
        """测试状态调整"""
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        original_status = status_mismatch_difference.asset.status

        AssetAdjustmentService.adjust_asset_from_difference(
            status_mismatch_difference, resolution
        )

        # 验证资产状态已更新
        status_mismatch_difference.asset.refresh_from_db()
        assert status_mismatch_difference.asset.status == status_mismatch_difference.actual_status
        assert status_mismatch_difference.asset.status != original_status

    def test_record_new_asset(self, surplus_difference, resolution):
        """测试补录新资产"""
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        asset = surplus_difference.asset
        asset.is_in_inventory = False
        asset.save()

        AssetAdjustmentService.record_new_asset(surplus_difference, resolution)

        # 验证资产已入账
        asset.refresh_from_db()
        assert asset.is_in_inventory is True
        assert asset.location == surplus_difference.actual_location

    def test_write_off_asset(self, loss_difference, resolution):
        """测试资产报损"""
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        asset = loss_difference.asset
        original_status = asset.status

        AssetAdjustmentService.write_off_asset(loss_difference, resolution)

        # 验证资产状态已更新为丢失
        asset.refresh_from_db()
        assert asset.status == 'lost'
        assert asset.is_in_inventory is False

    def test_rollback_adjustment(self, completed_adjustment, user):
        """测试回滚调账"""
        from apps.inventory.services.adjustment_service import AssetAdjustmentService

        adjustment = completed_adjustment
        asset = adjustment.asset
        before_value = adjustment.before_value

        AssetAdjustmentService.rollback_adjustment(adjustment.id, user, '需要回滚')

        # 验证调账已回滚
        adjustment.refresh_from_db()
        assert adjustment.status == 'rolled_back'

        # 验证资产已恢复
        asset.refresh_from_db()
        if before_value.get('location_id'):
            assert asset.location_id == before_value['location_id']
        if before_value.get('status'):
            assert asset.status == before_value['status']
```

### 2.5 盘点报告服务测试

```python
# apps/inventory/tests/test_report_service.py

@pytest.mark.django_db
class TestInventoryReportService:
    """盘点报告服务测试"""

    def test_generate_report(self, completed_task, user):
        """测试生成报告"""
        from apps.inventory.services import InventoryReportService

        report = InventoryReportService.generate_report(completed_task.id, user)

        assert report.status == 'draft'
        assert report.task == completed_task
        assert report.generated_by == user
        assert report.report_data is not None

    def test_report_data_structure(self, report_with_data):
        """测试报告数据结构"""
        data = report_with_data.report_data

        # 验证必需字段
        assert 'summary' in data
        assert 'differences_by_type' in data
        assert 'differences_by_department' in data

        # 验证summary字段
        summary = data['summary']
        assert 'total_assets' in summary
        assert 'scanned_assets' in summary
        assert 'difference_count' in summary
        assert 'scan_rate' in summary

    def test_submit_report_for_approval(self, draft_report):
        """测试提交报告审批"""
        from apps.inventory.services import InventoryReportService

        result = InventoryReportService.submit_report(draft_report.id)

        assert result.status == 'pending_approval'
        assert result.current_approver is not None

    def test_approve_report_first_level(self, pending_approval_report, approver):
        """测试第一级审批"""
        from apps.inventory.services import InventoryReportService

        result = InventoryReportService.approve_report(
            pending_approval_report.id,
            approver,
            'approved',
            '同意'
        )

        assert result.status == 'pending_approval'  # 还需要更多审批

        # 验证审批记录
        assert result.approvals.count() == 1

    def test_approve_report_final_level(self, pending_final_report, approver):
        """测试最后一级审批"""
        from apps.inventory.services import InventoryReportService

        result = InventoryReportService.approve_report(
            pending_final_report.id,
            approver,
            'approved',
            '最终批准'
        )

        assert result.status == 'approved'
        assert result.current_approver is None

    def test_reject_report(self, pending_approval_report, approver):
        """测试拒绝报告"""
        from apps.inventory.services import InventoryReportService

        result = InventoryReportService.approve_report(
            pending_approval_report.id,
            approver,
            'rejected',
            '数据有误，请修改'
        )

        assert result.status == 'rejected'
        assert result.current_approver is None

    def test_export_report_to_pdf(self, approved_report):
        """测试导出PDF"""
        from apps.inventory.services import InventoryReportService

        # 模拟导出
        result = InventoryReportService.export_report(approved_report.id, 'pdf')

        assert result is not None
        # 实际测试中可以验证PDF文件生成

    def test_export_report_to_excel(self, approved_report):
        """测试导出Excel"""
        from apps.inventory.services import InventoryReportService

        result = InventoryReportService.export_report(approved_report.id, 'excel')

        assert result is not None
```

---

## 3. API集成测试

### 3.1 差异API测试

```python
# apps/inventory/tests/test_difference_api.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestDifferenceAPI:
    """差异API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_differences(self, api_client, differences):
        """测试获取差异列表"""
        url = reverse('difference-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= len(differences)

    def test_filter_by_status(self, api_client, differences):
        """测试按状态筛选"""
        url = reverse('difference-list')
        response = api_client.get(url, {'status': 'pending'})

        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['status'] == 'pending'

    def test_filter_by_type(self, api_client, differences):
        """测试按类型筛选"""
        url = reverse('difference-list')
        response = api_client.get(url, {'difference_type': 'loss'})

        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['difference_type'] == 'loss'

    def test_retrieve_difference(self, api_client, difference):
        """测试获取差异详情"""
        url = reverse('difference-detail', kwargs={'pk': difference.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == difference.id

    def test_confirm_difference(self, api_client, pending_difference, user):
        """测试认定差异"""
        url = reverse('difference-confirm', kwargs={'pk': pending_difference.id})
        data = {
            'confirmation_note': '确认盘亏',
            'responsible_user_id': user.id,
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'confirmed'

    def test_batch_confirm_differences(self, api_client, pending_differences, user):
        """测试批量认定"""
        url = reverse('difference-batch-confirm')
        diff_ids = [d.id for d in pending_differences]
        data = {
            'difference_ids': diff_ids,
            'confirmation_note': '批量认定',
            'responsible_user_id': user.id,
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success_count'] == len(diff_ids)

    def test_analyze_differences(self, api_client, completed_task):
        """测试重新分析差异"""
        url = reverse('difference-analyze')
        data = {'task_id': completed_task.id}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
```

### 3.2 处理API测试

```python
# apps/inventory/tests/test_resolution_api.py

@pytest.mark.django_db
class TestResolutionAPI:
    """处理API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_resolutions(self, api_client, resolutions):
        """测试获取处理单列表"""
        url = reverse('resolution-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_resolution(self, api_client, task, confirmed_differences):
        """测试创建处理单"""
        url = reverse('resolution-list')
        diff_ids = [d.id for d in confirmed_differences]
        data = {
            'task_id': task.id,
            'action': 'adjust_account',
            'description': '批量调整',
            'difference_ids': diff_ids,
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_submit_resolution(self, api_client, draft_resolution):
        """测试提交处理"""
        url = reverse('resolution-submit', kwargs={'pk': draft_resolution.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'submitted'

    def test_approve_resolution(self, api_client, submitted_resolution, approver):
        """测试审批处理"""
        api_client.force_authenticate(user=approver)

        url = reverse('resolution-approve', kwargs={'pk': submitted_resolution.id})
        data = {'approved': True, 'note': '同意'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] in ['approved', 'completed']
```

### 3.3 报告API测试

```python
# apps/inventory/tests/test_report_api.py

@pytest.mark.django_db
class TestReportAPI:
    """报告API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_reports(self, api_client, reports):
        """测试获取报告列表"""
        url = reverse('report-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_generate_report(self, api_client, completed_task):
        """测试生成报告"""
        url = reverse('report-generate')
        data = {'task_id': completed_task.id}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_submit_report(self, api_client, draft_report):
        """测试提交报告"""
        url = reverse('report-submit', kwargs={'pk': draft_report.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'pending_approval'

    def test_approve_report(self, api_client, pending_approval_report, approver):
        """测试审批报告"""
        api_client.force_authenticate(user=approver)

        url = reverse('report-approve', kwargs={'pk': pending_approval_report.id})
        data = {'action': 'approved', 'opinion': '同意'}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_export_report_pdf(self, api_client, approved_report):
        """测试导出PDF"""
        url = reverse('report-export', kwargs={'pk': approved_report.id})

        response = api_client.get(url, {'format': 'pdf'})

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
```

---

## 4. 集成测试

### 4.1 完整差异处理流程

```python
# apps/inventory/tests/test_integration.py

@pytest.mark.django_db
class TestFullDifferenceWorkflow:
    """完整差异处理流程测试"""

    def test_complete_workflow_from_scan_to_resolution(self, org, user):
        """测试从扫描到处理的完整流程"""
        from apps.inventory.services import (
            DifferenceAnalysisService,
            DifferenceConfirmationService,
            DifferenceResolutionService,
        )

        # 1. 创建并完成盘点任务
        task = InventoryTaskFactory.create(org=org, status='in_progress')
        snapshot = InventorySnapshotFactory.create(task=task)

        # 2. 执行扫描（有差异）
        # ... 模拟扫描操作 ...

        # 3. 完成盘点
        task.status = 'completed'
        task.save()

        # 4. 分析差异
        differences = DifferenceAnalysisService.analyze_task_differences(task.id)
        assert len(differences) > 0

        # 5. 认定差异
        for diff in differences:
            DifferenceConfirmationService.confirm_difference(
                diff.id, user,
                {'confirmation_note': '确认', 'responsible_user_id': user.id}
            )

        # 6. 创建处理单
        confirmed_diffs = InventoryDifference.objects.filter(
            task=task, status='confirmed'
        )
        resolution = DifferenceResolutionService.create_resolution(
            user, task.id,
            {
                'action': 'adjust_account',
                'description': '批量调整',
                'difference_ids': list(confirmed_diffs.values_list('id', flat=True)),
            }
        )

        # 7. 提交审批
        resolution = DifferenceResolutionService.submit_resolution(resolution.id)

        # 8. 审批通过
        approver = UserFactory.create(org=org, is_admin=True)
        resolution = DifferenceResolutionService.approve_resolution(
            resolution.id, approver, approved=True, note='同意'
        )

        # 9. 验证处理完成
        assert resolution.status == 'completed'

        # 10. 验证资产已调整
        for diff in confirmed_diffs:
            diff.refresh_from_db()
            assert diff.status == 'resolved'
            assert diff.adjustment is not None
```

---

## 5. E2E测试

### 5.1 差异处理完整流程

```python
# tests/e2e/test_difference_flow.py

from playwright.sync_api import Page, expect


class TestDifferenceFlowE2E:
    """差异处理端到端测试"""

    def test_complete_difference_workflow(self, page: Page, login_url):
        """测试完整差异处理流程"""

        # 1. 登录
        page.goto(login_url)
        page.fill('#username', 'testuser')
        page.fill('#password', 'password')
        page.click('#login-btn')

        # 2. 进入差异管理页面
        page.goto('http://localhost:8080/inventory/reconciliation/difference')
        expect(page).to_have_title('差异管理')

        # 3. 查看差异列表
        expect(page.locator('.el-table__body')).to_be_visible()

        # 4. 认定差异
        page.click('text=认定')
        page.fill('[placeholder="请输入认定意见"]', '确认盘亏')
        page.click('.user-picker')
        page.click('text=张三')
        page.click('text=确认认定')

        # 5. 验证状态变更
        expect(page.locator('.el-tag--success')).to_contain_text('已认定')

        # 6. 创建处理单
        page.click('text=新建处理单')
        page.select_option('#action', 'adjust_account')
        page.fill('#description', '批量调整账面')
        page.click('text=保存')
        page.click('text=提交审批')

        # 7. 验证提交成功
        expect(page.locator('.el-message--success')).to_be_visible()

        # 8. 审批处理
        page.click('text=审批')
        page.click('text=同意')
        page.click('text=确认')

        # 9. 验证处理完成
        expect(page.locator('.el-tag--success')).to_contain_text('已完成')
```

### 5.2 报告生成与审批流程

```python
class TestReportFlowE2E:
    """报告流程端到端测试"""

    def test_generate_and_approve_report(self, page: Page, login_url):
        """测试报告生成与审批"""

        # 1. 登录
        page.goto(login_url)
        # ... 登录代码 ...

        # 2. 进入报告列表
        page.goto('http://localhost:8080/inventory/reconciliation/report')

        # 3. 生成报告
        page.click('text=生成报告')
        page.select_option('#task_id', 'PD2024010001')
        page.click('text=确认生成')

        # 4. 查看报告详情
        page.click('.el-table__row .el-button--text:has-text("查看")')

        # 5. 验证报告内容
        expect(page.locator('.report-summary')).to_be_visible()
        expect(page.locator('.difference-chart')).to_be_visible()

        # 6. 提交审批
        page.click('text=提交审批')

        # 7. 切换到审批人账号
        # ... 切换账号代码 ...

        # 8. 审批报告
        page.click('text=审批')
        page.fill('textarea', '盘点结果确认无误')
        page.click('text=同意')

        # 9. 验证审批完成
        expect(page.locator('.el-tag--success')).to_contain_text('已批准')

        # 10. 导出报告
        page.click('text=导出PDF')
        # 验证下载
```

---

## 6. 性能测试

```python
# tests/performance/test_reconciliation_performance.py

@pytest.mark.django_db
@pytest.mark.performance
class TestReconciliationPerformance:
    """性能测试"""

    def test_large_scale_difference_analysis(self, large_task):
        """测试大规模差异分析性能"""
        from apps.inventory.services import DifferenceAnalysisService
        import time

        # 大任务：1000+资产
        start_time = time.time()
        differences = DifferenceAnalysisService.analyze_task_differences(large_task.id)
        elapsed = time.time() - start_time

        # 验证性能：分析应在30秒内完成
        assert elapsed < 30
        assert len(differences) > 0

    def test_batch_confirm_performance(self, many_pending_differences):
        """测试批量认定性能"""
        from apps.inventory.services import DifferenceConfirmationService
        import time

        diff_ids = [d.id for d in many_pending_differences[:100]]  # 100条
        user = many_pending_differences[0].task.manager

        start_time = time.time()
        count = DifferenceConfirmationService.batch_confirm(
            diff_ids, user,
            {'confirmation_note': '批量', 'responsible_user_id': user.id}
        )
        elapsed = time.time() - start_time

        assert count == 100
        assert elapsed < 10  # 100条应在10秒内完成

    def test_report_generation_performance(self, task_with_many_differences):
        """测试报告生成性能"""
        from apps.inventory.services import InventoryReportService
        import time

        start_time = time.time()
        report = InventoryReportService.generate_report(
            task_with_many_differences.id,
            task_with_many_differences.manager
        )
        elapsed = time.time() - start_time

        assert report.report_data is not None
        assert elapsed < 15  # 报告生成应在15秒内完成
```

---

## 7. Fixtures配置

```python
# apps/inventory/tests/conftest.py

import pytest
from django.utils import timezone
from apps.inventory.models import (
    InventoryTask, InventorySnapshot, InventorySnapshotItem,
    InventoryDifference, DifferenceResolution
)
from apps.organizations.models import Department, Location
from apps.assets.models import Asset, AssetCategory


@pytest.fixture
def location(org):
    return Location.objects.create(
        name="A栋301",
        code="A301",
        org=org,
    )


@pytest.fixture
def another_location(org):
    return Location.objects.create(
        name="A栋302",
        code="A302",
        org=org,
    )


@pytest.fixture
def asset_category(org):
    return AssetCategory.objects.create(
        name="电子设备",
        code="IT",
        org=org,
    )


@pytest.fixture
def asset(org, asset_category, location):
    return Asset.objects.create(
        asset_no="ZC2024010001",
        asset_name="笔记本电脑",
        category=asset_category,
        location=location,
        status="in_use",
        original_value=5000,
        org=org,
    )


@pytest.fixture
def inventory_task(org, user, department):
    return InventoryTask.objects.create(
        task_no="PD2024010001",
        task_name="2024年1月盘点",
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timezone.timedelta(days=7),
        manager=user,
        org=org,
    )


@pytest.fixture
def inventory_snapshot(inventory_task):
    return InventorySnapshot.objects.create(
        task=inventory_task,
        snapshot_date=timezone.now().date(),
        org=inventory_task.org,
    )


@pytest.fixture
def snapshot_item(inventory_snapshot, asset, location):
    return InventorySnapshotItem.objects.create(
        snapshot=inventory_snapshot,
        asset=asset,
        location=location,
        status="in_use",
        original_value=asset.original_value,
        org=inventory_snapshot.org,
    )


@pytest.fixture
def pending_difference(inventory_task, asset, location):
    return InventoryDifference.objects.create(
        task=inventory_task,
        difference_type='loss',
        status='pending',
        asset=asset,
        account_location=location,
        account_status='in_use',
        description='测试差异',
        org=inventory_task.org,
    )


@pytest.fixture
def confirmed_difference(pending_difference, user):
    pending_difference.status = 'confirmed'
    pending_difference.confirmed_by = user
    pending_difference.confirmed_at = timezone.now()
    pending_difference.responsible_user = user
    pending_difference.save()
    return pending_difference


@pytest.fixture
def location_mismatch_difference(inventory_task, asset, location, another_location):
    return InventoryDifference.objects.create(
        task=inventory_task,
        difference_type='location_mismatch',
        status='confirmed',
        asset=asset,
        account_location=location,
        actual_location=another_location,
        description='位置不符',
        org=inventory_task.org,
    )


@pytest.fixture
def small_loss_difference(inventory_task, asset, location):
    return InventoryDifference.objects.create(
        task=inventory_task,
        difference_type='loss',
        status='pending',
        asset=asset,
        account_location=location,
        account_value=5000,  # < 10000
        description='小额盘亏',
        org=inventory_task.org,
    )


@pytest.fixture
def large_loss_difference(inventory_task, asset, location):
    return InventoryDifference.objects.create(
        task=inventory_task,
        difference_type='loss',
        status='pending',
        asset=asset,
        account_location=location,
        account_value=50000,  # > 10000
        description='大额盘亏',
        org=inventory_task.org,
    )
```

---

## 8. 测试执行

```bash
# 运行所有盘点业务链条测试
pytest apps/inventory/tests/

# 运行特定测试文件
pytest apps/inventory/tests/test_difference_service.py

# 运行API测试
pytest apps/inventory/tests/test_*_api.py

# 运行集成测试
pytest apps/inventory/tests/test_integration.py

# 运行E2E测试
pytest tests/e2e/test_difference_flow.py

# 运行性能测试
pytest apps/inventory/tests/ -m performance

# 生成覆盖率报告
pytest --cov=apps.inventory --cov-report=html apps/inventory/tests/
```
