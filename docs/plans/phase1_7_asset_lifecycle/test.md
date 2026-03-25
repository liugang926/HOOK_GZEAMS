# Phase 1.7: 资产生命周期管理 - 测试计划

## 1. 测试概述

### 1.1 测试范围

| 模块 | 测试内容 |
|------|----------|
| 采购申请 | 申请创建、审批流程、M18集成 |
| 资产入库 | 验收单创建、验收流程、资产卡片生成 |
| 维护保养 | 维修单流程、保养计划、保养任务 |
| 报废处置 | 报废申请、技术鉴定、处置执行 |

### 1.2 测试策略

| 测试类型 | 工具/框架 | 覆盖范围 |
|----------|-----------|----------|
| 单元测试 | pytest | 模型方法、服务层逻辑 |
| API测试 | pytest + requests | REST API接口 |
| 集成测试 | pytest + faker | 模块间集成、M18适配 |
| E2E测试 | Selenium/Playwright | 完整业务流程 |

---

## 2. 单元测试

### 2.1 采购申请模型测试

```python
# apps/lifecycle/tests/test_purchase_models.py

import pytest
from django.utils import timezone
from apps.lifecycle.models import PurchaseRequest, PurchaseRequestItem
from apps.accounts.models import User
from apps.organizations.models import Department


@pytest.mark.django_db
class TestPurchaseRequestModel:
    """采购申请模型测试"""

    def test_create_purchase_request(self, user, department):
        """测试创建采购申请"""
        request = PurchaseRequest.objects.create(
            request_no="PR2024010001",
            applicant=user,
            department=department,
            request_date=timezone.now().date(),
            expected_date=timezone.now().date() + timezone.timedelta(days=30),
            reason="新增开发人员需要配置电脑",
            budget_amount=50000,
            org=user.org,
            created_by=user,
        )

        assert request.request_no == "PR2024010001"
        assert request.status == "draft"
        assert request.applicant == user
        assert request.department == department

    def test_purchase_request_status_transition(self, purchase_request):
        """测试状态流转"""
        assert purchase_request.status == "draft"

        # 提交
        purchase_request.status = "submitted"
        purchase_request.save()
        assert purchase_request.status == "submitted"

        # 审批通过
        purchase_request.status = "approved"
        purchase_request.approved_at = timezone.now()
        purchase_request.save()
        assert purchase_request.status == "approved"

    def test_calculate_total_amount(self, purchase_request_with_items):
        """测试计算总金额"""
        total = purchase_request_with_items.items.aggregate(
            total=models.Sum('total_amount')
        )['total']
        assert total == 45000

    def test_generate_request_no(self, purchase_request_service):
        """测试生成申请单号"""
        no1 = purchase_request_service.generate_request_no()
        no2 = purchase_request_service.generate_request_no()

        assert no1.startswith("PR")
        assert no2.startswith("PR")
        # 序号应递增
        seq1 = int(no1[-4:])
        seq2 = int(no2[-4:])
        assert seq2 == seq1 + 1


@pytest.mark.django_db
class TestPurchaseRequestItemModel:
    """采购申请明细模型测试"""

    def test_create_item(self, purchase_request, asset_category):
        """测试创建明细"""
        item = PurchaseRequestItem.objects.create(
            purchase_request=purchase_request,
            sequence=1,
            asset_category=asset_category,
            item_name="笔记本电脑",
            specification="ThinkPad X1 Carbon",
            quantity=10,
            unit="台",
            unit_price=4500,
            total_amount=45000,
            org=purchase_request.org,
        )

        assert item.purchase_request == purchase_request
        assert item.total_amount == item.quantity * item.unit_price

    def test_item_sequence_auto_increment(self, purchase_request):
        """测试序号自动递增"""
        item1 = PurchaseRequestItem.objects.create(
            purchase_request=purchase_request,
            sequence=1,
            asset_category_id=1,
            item_name="Item 1",
            quantity=1,
            unit="台",
            unit_price=100,
            total_amount=100,
            org=purchase_request.org,
        )

        item2 = PurchaseRequestItem.objects.create(
            purchase_request=purchase_request,
            sequence=2,
            asset_category_id=1,
            item_name="Item 2",
            quantity=1,
            unit="台",
            unit_price=200,
            total_amount=200,
            org=purchase_request.org,
        )

        assert item2.sequence > item1.sequence
```

### 2.2 资产入库模型测试

```python
# apps/lifecycle/tests/test_receipt_models.py

@pytest.mark.django_db
class TestAssetReceiptModel:
    """资产验收单模型测试"""

    def test_create_receipt(self, user, purchase_request):
        """测试创建验收单"""
        receipt = AssetReceipt.objects.create(
            receipt_no="RC2024010001",
            purchase_request=purchase_request,
            receipt_date=timezone.now().date(),
            receipt_type="purchase",
            supplier="联想代理商",
            delivery_no="DN20240115001",
            receiver=user,
            org=user.org,
            created_by=user,
        )

        assert receipt.receipt_no == "RC2024010001"
        assert receipt.status == "draft"
        assert receipt.purchase_request == purchase_request

    def test_receipt_inspection_pass(self, asset_receipt):
        """测试验收通过"""
        asset_receipt.status = "passed"
        asset_receipt.inspection_result = "验收合格"
        asset_receipt.passed_at = timezone.now()
        asset_receipt.save()

        assert asset_receipt.status == "passed"
        assert asset_receipt.passed_at is not None

    def test_receipt_item_calculate_quantities(self, asset_receipt_item):
        """测试数量计算"""
        # 不合格数量 = 实收数量 - 合格数量
        defective = asset_receipt_item.received_quantity - asset_receipt_item.qualified_quantity
        assert asset_receipt_item.defective_quantity == defective

    def test_generate_assets_from_receipt(self, asset_receipt_with_items):
        """测试从验收单生成资产卡片"""
        from apps.lifecycle.services.receipt_service import AssetReceiptService

        # 验收通过
        asset_receipt_with_items.status = "passed"
        asset_receipt_with_items.save()

        # 生成资产
        AssetReceiptService._generate_assets_from_receipt(asset_receipt_with_items)

        # 验证资产生成
        for item in asset_receipt_with_items.items.all():
            if item.qualified_quantity > 0:
                assert item.asset_generated is True
                # 验证生成的资产数量
                generated_count = item.asset_set.count()
                assert generated_count == item.qualified_quantity
```

### 2.3 维护保养模型测试

```python
# apps/lifecycle/tests/test_maintenance_models.py

@pytest.mark.django_db
class TestMaintenanceModel:
    """维修记录模型测试"""

    def test_create_maintenance(self, user, asset):
        """测试创建维修申请"""
        maintenance = Maintenance.objects.create(
            maintenance_no="MT2024010001",
            asset=asset,
            reporter=user,
            report_time=timezone.now(),
            fault_description="无法开机",
            priority="normal",
            org=asset.org,
            created_by=user,
        )

        assert maintenance.maintenance_no == "MT2024010001"
        assert maintenance.status == "reported"
        assert maintenance.asset.status == "maintenance"  # 资产状态变更

    def test_maintenance_assign(self, maintenance, technician):
        """测试派单"""
        maintenance.technician = technician
        maintenance.status = "assigned"
        maintenance.assigned_at = timezone.now()
        maintenance.save()

        assert maintenance.technician == technician
        assert maintenance.status == "assigned"

    def test_maintenance_complete(self, maintenance):
        """测试完成维修"""
        maintenance.status = "completed"
        maintenance.start_time = timezone.now() - timezone.timedelta(hours=2)
        maintenance.end_time = timezone.now()
        maintenance.work_hours = 2.0
        maintenance.labor_cost = 100
        maintenance.material_cost = 50
        maintenance.total_cost = 150
        maintenance.save()

        assert maintenance.total_cost == maintenance.labor_cost + maintenance.material_cost

        # 验证资产状态恢复
        asset = maintenance.asset
        asset.status = "in_use"
        asset.save()

    def test_calculate_maintenance_no(self, maintenance_service):
        """测试生成维修单号"""
        no1 = maintenance_service.generate_maintenance_no()
        no2 = maintenance_service.generate_maintenance_no()

        assert no1.startswith("MT")
        assert no2.startswith("MT")
        seq1 = int(no1[-4:])
        seq2 = int(no2[-4:])
        assert seq2 == seq1 + 1


@pytest.mark.django_db
class TestMaintenancePlanModel:
    """保养计划模型测试"""

    def test_create_maintenance_plan(self, user, asset_category):
        """测试创建保养计划"""
        plan = MaintenancePlan.objects.create(
            plan_name="空调季度保养",
            plan_code="MP001",
            cycle_type="quarterly",
            cycle_value=1,
            start_date=timezone.now().date(),
            maintenance_content="清洗滤网、检查制冷剂",
            estimated_hours=2.0,
            org=user.org,
            created_by=user,
        )

        plan.asset_categories.add(asset_category)

        assert plan.status == "active"
        assert plan.cycle_type == "quarterly"

    def test_generate_maintenance_tasks(self, maintenance_plan, asset):
        """测试生成保养任务"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        # 添加资产到计划
        maintenance_plan.assets.add(asset)

        # 生成任务
        MaintenanceService.generate_maintenance_tasks()

        # 验证任务生成
        tasks = MaintenanceTask.objects.filter(plan=maintenance_plan, asset=asset)
        assert tasks.exists()

    def test_maintenance_task_status(self, maintenance_task):
        """测试任务状态流转"""
        assert maintenance_task.status == "pending"

        # 执行中
        maintenance_task.status = "in_progress"
        maintenance_task.start_time = timezone.now()
        maintenance_task.save()

        # 完成
        maintenance_task.status = "completed"
        maintenance_task.end_time = timezone.now()
        maintenance_task.save()

        assert maintenance_task.status == "completed"
```

### 2.4 报废处置模型测试

```python
# apps/lifecycle/tests/test_disposal_models.py

@pytest.mark.django_db
class TestDisposalRequestModel:
    """报废申请模型测试"""

    def test_create_disposal_request(self, user, department):
        """测试创建报废申请"""
        request = DisposalRequest.objects.create(
            request_no="DS2024010001",
            applicant=user,
            department=department,
            request_date=timezone.now().date(),
            disposal_type="scrap",
            disposal_reason="使用年限到期",
            reason_type="expired",
            org=user.org,
            created_by=user,
        )

        assert request.request_no == "DS2024010001"
        assert request.status == "draft"
        assert request.disposal_type == "scrap"

    def test_disposal_status_flow(self, disposal_request):
        """测试状态流转"""
        # 提交鉴定
        disposal_request.status = "appraising"
        disposal_request.save()

        # 审批通过
        disposal_request.status = "approved"
        disposal_request.save()

        # 执行处置
        disposal_request.status = "executing"
        disposal_request.save()

        # 完成
        disposal_request.status = "completed"
        disposal_request.save()

        assert disposal_request.status == "completed"


@pytest.mark.django_db
class TestDisposalItemModel:
    """报废明细模型测试"""

    def test_create_disposal_item(self, disposal_request, asset):
        """测试创建报废明细"""
        item = DisposalItem.objects.create(
            disposal_request=disposal_request,
            sequence=1,
            asset=asset,
            original_value=asset.original_value,
            accumulated_depreciation=asset.accumulated_depreciation,
            net_value=asset.net_value,
            org=disposal_request.org,
        )

        assert item.asset == asset
        assert item.net_value == asset.net_value

    def test_disposal_appraisal(self, disposal_item, user):
        """测试技术鉴定"""
        disposal_item.appraisal_result = "设备老化严重，建议报废"
        disposal_item.residual_value = 0
        disposal_item.appraised_by = user
        disposal_item.appraised_at = timezone.now()
        disposal_item.save()

        assert disposal_item.appraised_by == user
        assert disposal_item.residual_value == 0

    def test_disposal_execute(self, disposal_item):
        """测试执行处置"""
        disposal_item.disposal_executed = True
        disposal_item.executed_at = timezone.now()
        disposal_item.actual_residual_value = 0
        disposal_item.save()

        # 验证资产状态
        asset = disposal_item.asset
        asset.status = "disposed"
        asset.disposal_date = timezone.now().date()
        asset.save()

        assert disposal_item.disposal_executed is True
        assert asset.status == "disposed"
```

---

## 3. 服务层测试

### 3.1 采购申请服务测试

```python
# apps/lifecycle/tests/test_purchase_service.py

@pytest.mark.django_db
class TestPurchaseRequestService:
    """采购申请服务测试"""

    def test_create_purchase_request_with_items(self, user, department, asset_category):
        """测试创建采购申请及明细"""
        from apps.lifecycle.services.purchase_service import PurchaseRequestService

        data = {
            "department_id": department.id,
            "request_date": timezone.now().date(),
            "expected_date": timezone.now().date() + timezone.timedelta(days=30),
            "reason": "新增开发人员",
            "budget_amount": 50000,
            "items": [
                {
                    "asset_category_id": asset_category.id,
                    "item_name": "笔记本电脑",
                    "specification": "ThinkPad X1",
                    "quantity": 10,
                    "unit": "台",
                    "unit_price": 4500,
                }
            ]
        }

        request = PurchaseRequestService.create_purchase_request(user, data)

        assert request.status == "draft"
        assert request.items.count() == 1
        assert request.items.first().total_amount == 45000

    def test_submit_for_approval(self, purchase_request):
        """测试提交审批"""
        from apps.lifecycle.services.purchase_service import PurchaseRequestService

        # Mock workflow
        with patch('apps.lifecycle.services.purchase_service.WorkflowService') as mock_workflow:
            PurchaseRequestService.submit_for_approval(purchase_request.id)

            purchase_request.refresh_from_db()
            assert purchase_request.status == "submitted"
            mock_workflow.start_workflow.assert_called_once()

    def test_approve_request(self, purchase_request, approver):
        """测试审批通过"""
        from apps.lifecycle.services.purchase_service import PurchaseRequestService

        with patch('apps.lifecycle.services.purchase_service.push_purchase_to_m18') as mock_push:
            PurchaseRequestService.approve_request(
                purchase_request.id,
                approver,
                approved=True,
                comment="同意"
            )

            purchase_request.refresh_from_db()
            assert purchase_request.status == "approved"
            assert purchase_request.approved_by == approver
            mock_push.delay.assert_called_once_with(purchase_request.id)

    def test_reject_request(self, purchase_request, approver):
        """测试审批拒绝"""
        from apps.lifecycle.services.purchase_service import PurchaseRequestService

        PurchaseRequestService.approve_request(
            purchase_request.id,
            approver,
            approved=False,
            comment="预算不足"
        )

        purchase_request.refresh_from_db()
        assert purchase_request.status == "rejected"

    def test_sync_m18_status(self, purchase_request):
        """测试M18状态同步"""
        from apps.lifecycle.services.purchase_service import PurchaseRequestService

        PurchaseRequestService.sync_m18_status(
            purchase_request.id,
            m18_status="completed",
            m18_order_no="PO2024010001"
        )

        purchase_request.refresh_from_db()
        assert purchase_request.m18_purchase_order_no == "PO2024010001"
        assert purchase_request.m18_sync_status == "completed"
        assert purchase_request.status == "completed"
```

### 3.2 资产入库服务测试

```python
# apps/lifecycle/tests/test_receipt_service.py

@pytest.mark.django_db
class TestAssetReceiptService:
    """资产入库服务测试"""

    def test_create_receipt_with_items(self, user, purchase_request, asset_category):
        """测试创建验收单"""
        from apps.lifecycle.services.receipt_service import AssetReceiptService

        data = {
            "receipt_date": timezone.now().date(),
            "receipt_type": "purchase",
            "purchase_request_id": purchase_request.id,
            "supplier": "联想代理商",
            "items": [
                {
                    "asset_category_id": asset_category.id,
                    "item_name": "笔记本电脑",
                    "specification": "ThinkPad X1",
                    "ordered_quantity": 10,
                    "received_quantity": 10,
                    "unit_price": 4500,
                }
            ]
        }

        receipt = AssetReceiptService.create_receipt(user, data)

        assert receipt.receipt_no.startswith("RC")
        assert receipt.items.count() == 1

    def test_pass_inspection(self, asset_receipt, inspector):
        """测试验收通过"""
        from apps.lifecycle.services.receipt_service import AssetReceiptService

        with patch.object(
            AssetReceiptService,
            '_generate_assets_from_receipt'
        ) as mock_generate:
            result = AssetReceiptService.pass_inspection(
                asset_receipt.id,
                inspector,
                "验收合格"
            )

            assert result.status == "passed"
            assert result.inspector == inspector
            mock_generate.assert_called_once_with(asset_receipt)

    def test_reject_inspection(self, asset_receipt, inspector):
        """测试验收不通过"""
        from apps.lifecycle.services.receipt_service import AssetReceiptService

        result = AssetReceiptService.reject_inspection(
            asset_receipt.id,
            inspector,
            "货物损坏"
        )

        assert result.status == "rejected"
        assert result.inspector == inspector

    @patch('apps.assets.services.AssetService.create_asset_from_receipt')
    def test_generate_assets_from_receipt(self, mock_create, asset_receipt_with_items):
        """测试生成资产卡片"""
        from apps.lifecycle.services.receipt_service import AssetReceiptService

        AssetReceiptService._generate_assets_from_receipt(asset_receipt_with_items)

        # 验证每个合格数量都调用创建资产
        for item in asset_receipt_with_items.items.all():
            if item.qualified_quantity > 0:
                assert mock_create.call_count >= item.qualified_quantity
```

### 3.3 维护保养服务测试

```python
# apps/lifecycle/tests/test_maintenance_service.py

@pytest.mark.django_db
class TestMaintenanceService:
    """维护保养服务测试"""

    def test_create_maintenance_request(self, user, asset):
        """测试创建维修申请"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        data = {
            "asset_id": asset.id,
            "fault_description": "无法开机",
            "priority": "normal"
        }

        maintenance = MaintenanceService.create_maintenance_request(user, data)

        assert maintenance.maintenance_no.startswith("MT")
        assert maintenance.asset == asset
        assert maintenance.status == "reported"

    def test_assign_technician(self, maintenance, technician):
        """测试派单"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        result = MaintenanceService.assign_technician(maintenance.id, technician.id)

        assert result.status == "assigned"
        assert result.technician == technician

    def test_complete_maintenance(self, maintenance):
        """测试完成维修"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        data = {
            "start_time": timezone.now() - timezone.timedelta(hours=2),
            "work_hours": 2.0,
            "fault_cause": "电源损坏",
            "repair_method": "更换电源",
            "labor_cost": 100,
            "material_cost": 50,
            "other_cost": 0
        }

        result = MaintenanceService.complete_maintenance(maintenance.id, data)

        assert result.status == "processing"
        assert result.total_cost == 150

    def test_create_maintenance_plan(self, user, asset_category):
        """测试创建保养计划"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        data = {
            "plan_name": "空调季度保养",
            "cycle_type": "quarterly",
            "cycle_value": 1,
            "start_date": timezone.now().date(),
            "maintenance_content": "清洗滤网",
            "estimated_hours": 2.0,
            "asset_category_ids": [asset_category.id]
        }

        plan = MaintenanceService.create_maintenance_plan(user, data)

        assert plan.status == "active"
        assert plan.cycle_type == "quarterly"

    @patch('apps.lifecycle.services.maintenance_service.MaintenanceTask.objects.create')
    def test_generate_maintenance_tasks(self, mock_create, maintenance_plan):
        """测试生成保养任务"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        MaintenanceService.generate_maintenance_tasks()

        # 验证任务被创建（实际实现会根据计划生成）
        # 这里需要根据具体实现调整断言
```

---

## 4. API集成测试

### 4.1 采购申请API测试

```python
# apps/lifecycle/tests/test_purchase_api.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


@pytest.mark.django_db
class TestPurchaseRequestAPI:
    """采购申请API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_purchase_requests(self, api_client, purchase_request):
        """测试获取采购申请列表"""
        url = reverse('purchase-request-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1

    def test_create_purchase_request(self, api_client, user, department, asset_category):
        """测试创建采购申请"""
        url = reverse('purchase-request-list')
        data = {
            "department_id": department.id,
            "request_date": timezone.now().date().isoformat(),
            "expected_date": (timezone.now().date() + timezone.timedelta(days=30)).isoformat(),
            "reason": "新增开发人员",
            "items": [
                {
                    "asset_category_id": asset_category.id,
                    "item_name": "笔记本电脑",
                    "quantity": 10,
                    "unit_price": 4500,
                }
            ]
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['request_no'].startswith('PR')

    def test_retrieve_purchase_request(self, api_client, purchase_request):
        """测试获取采购申请详情"""
        url = reverse('purchase-request-detail', kwargs={'pk': purchase_request.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == purchase_request.id

    def test_update_purchase_request(self, api_client, purchase_request):
        """测试更新采购申请"""
        url = reverse('purchase-request-detail', kwargs={'pk': purchase_request.id})
        data = {
            "reason": "更新后的原因"
        }

        response = api_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_submit_purchase_request(self, api_client, purchase_request):
        """测试提交采购申请"""
        url = reverse('purchase-request-submit', kwargs={'pk': purchase_request.id})
        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'submitted'

    def test_approve_purchase_request(self, api_client, purchase_request, approver):
        """测试审批采购申请"""
        api_client.force_authenticate(user=approver)

        purchase_request.status = 'submitted'
        purchase_request.save()

        url = reverse('purchase-request-approve', kwargs={'pk': purchase_request.id})
        data = {"approved": True, "comment": "同意"}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'approved'

    def test_delete_purchase_request(self, api_client, purchase_request):
        """测试删除采购申请"""
        url = reverse('purchase-request-detail', kwargs={'pk': purchase_request.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_filter_by_status(self, api_client, purchase_request):
        """测试按状态筛选"""
        url = reverse('purchase-request-list')
        response = api_client.get(url, {'status': 'draft'})

        assert response.status_code == status.HTTP_200_OK
        for item in response.data['results']:
            assert item['status'] == 'draft'

    def test_filter_by_department(self, api_client, purchase_request, department):
        """测试按部门筛选"""
        url = reverse('purchase-request-list')
        response = api_client.get(url, {'department_id': department.id})

        assert response.status_code == status.HTTP_200_OK
```

### 4.2 资产入库API测试

```python
# apps/lifecycle/tests/test_receipt_api.py

@pytest.mark.django_db
class TestAssetReceiptAPI:
    """资产入库API测试"""

    @pytest.fixture
    def api_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    def test_list_receipts(self, api_client, asset_receipt):
        """测试获取验收单列表"""
        url = reverse('asset-receipt-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_receipt(self, api_client, user, purchase_request, asset_category):
        """测试创建验收单"""
        url = reverse('asset-receipt-list')
        data = {
            "receipt_date": timezone.now().date().isoformat(),
            "receipt_type": "purchase",
            "purchase_request_id": purchase_request.id,
            "supplier": "联想代理商",
            "items": [
                {
                    "asset_category_id": asset_category.id,
                    "item_name": "笔记本电脑",
                    "ordered_quantity": 10,
                    "received_quantity": 10,
                    "unit_price": 4500,
                }
            ]
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_pass_inspection(self, api_client, asset_receipt):
        """测试验收通过"""
        asset_receipt.status = 'submitted'
        asset_receipt.save()

        url = reverse('asset-receipt-pass-inspection', kwargs={'pk': asset_receipt.id})
        data = {"inspection_result": "验收合格"}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'passed'

    def test_reject_inspection(self, api_client, asset_receipt):
        """测试验收不通过"""
        url = reverse('asset-receipt-reject-inspection', kwargs={'pk': asset_receipt.id})
        data = {"reason": "货物损坏"}

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'rejected'
```

---

## 5. E2E测试

### 5.1 采购申请完整流程

```python
# tests/e2e/test_purchase_flow.py

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytest


class TestPurchaseFlowE2E:
    """采购申请端到端测试"""

    @pytest.fixture
    def browser(self):
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_complete_purchase_flow(self, browser, login_url):
        """测试完整的采购流程"""

        # 1. 登录
        browser.get(login_url)
        browser.find_element(By.ID, 'username').send_keys('testuser')
        browser.find_element(By.ID, 'password').send_keys('password')
        browser.find_element(By.ID, 'login-btn').click()

        # 2. 进入采购申请页面
        browser.get('http://localhost:8080/lifecycle/purchase')
        assert '采购申请' in browser.title

        # 3. 点击新建
        browser.find_element(By.XPATH, '//button[contains(text(), "新建申请")]').click()

        # 4. 填写表单
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.NAME, 'department_id'))
        )
        browser.find_element(By.NAME, 'department_id').click()
        browser.find_element(By.XPATH, '//li[contains(text(), "研发部")]').click()

        browser.find_element(By.NAME, 'reason').send_keys('新增开发人员需要配置电脑')

        # 添加明细
        browser.find_element(By.XPATH, '//button[contains(text(), "添加明细")]').click()
        browser.find_element(By.NAME, 'items-0-item_name').send_keys('笔记本电脑')
        browser.find_element(By.NAME, 'items-0-quantity').send_keys('10')
        browser.find_element(By.NAME, 'items-0-unit_price').send_keys('4500')

        # 5. 保存草稿
        browser.find_element(By.XPATH, '//button[contains(text(), "保存草稿")]').click()
        assert '保存成功' in browser.page_source

        # 6. 提交审批
        browser.find_element(By.XPATH, '//button[contains(text(), "提交审批")]').click()
        browser.switch_to.alert.accept()

        # 7. 验证状态变更
        WebDriverWait(browser, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'el-tag'),
                '已提交'
            )
        )

        # 8. 登出
        browser.find_element(By.CLASS_NAME, 'user-dropdown').click()
        browser.find_element(By.XPATH, '//a[contains(text(), "退出登录")]').click()
```

### 5.2 维修申请完整流程

```python
# tests/e2e/test_maintenance_flow.py

class TestMaintenanceFlowE2E:
    """维修申请端到端测试"""

    @pytest.fixture
    def browser(self):
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()

    def test_complete_maintenance_flow(self, browser, login_url):
        """测试完整的维修流程"""

        # 1. 登录并进入维修管理页面
        browser.get(login_url)
        # ... 登录代码 ...

        browser.get('http://localhost:8080/lifecycle/maintenance')

        # 2. 创建报修
        browser.find_element(By.XPATH, '//button[contains(text(), "报修")]').click()

        # 3. 填写报修信息
        browser.find_element(By.NAME, 'asset_id').click()
        browser.find_element(By.XPATH, '//li[contains(text(), "笔记本电脑")]').click()

        browser.find_element(By.NAME, 'fault_description').send_keys(
            '无法开机，电源指示灯不亮'
        )

        # 选择优先级
        browser.find_element(By.XPATH, '//input[@value="urgent"]').click()

        # 上传故障照片
        browser.find_element(By.CSS_SELECTOR, 'input[type="file"]').send_keys(
            '/path/to/test/photo.jpg'
        )

        # 4. 提交报修
        browser.find_element(By.XPATH, '//button[contains(text(), "提交报修")]').click()

        # 5. 验证报修成功
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'el-message--success'))
        )

        # 6. 验证维修单显示在列表中
        assert '无法开机' in browser.page_source
```

---

## 6. 性能测试

### 6.1 并发测试

```python
# tests/performance/test_concurrent.py

import pytest
from concurrent.futures import ThreadPoolExecutor
from apps.lifecycle.services.purchase_service import PurchaseRequestService


@pytest.mark.django_db
@pytest.mark.performance
class TestConcurrentOperations:
    """并发操作性能测试"""

    def test_concurrent_purchase_request_creation(self, user, department, asset_category):
        """测试并发创建采购申请"""

        def create_request(index):
            data = {
                "department_id": department.id,
                "request_date": timezone.now().date(),
                "expected_date": timezone.now().date(),
                "reason": f"并发测试-{index}",
                "items": [{
                    "asset_category_id": asset_category.id,
                    "item_name": f"物品-{index}",
                    "quantity": 1,
                    "unit_price": 100,
                }]
            }
            return PurchaseRequestService.create_purchase_request(user, data)

        # 并发创建100个申请
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_request, i) for i in range(100)]
            results = [f.result() for f in futures]

        assert len(results) == 100
        # 验证申请单号唯一
        request_nos = [r.request_no for r in results]
        assert len(request_nos) == len(set(request_nos))

    def test_concurrent_maintenance_task_generation(self, maintenance_plan):
        """测试并发生成保养任务"""
        from apps.lifecycle.services.maintenance_service import MaintenanceService

        def generate_tasks():
            return MaintenanceService.generate_maintenance_tasks()

        # 并发生成任务
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_tasks) for _ in range(10)]
            results = [f.result() for f in futures]

        # 验证没有重复任务
        # 具体验证逻辑根据实现调整
```

---

## 7. Fixtures配置

```python
# apps/lifecycle/tests/conftest.py

import pytest
from django.utils import timezone
from apps.accounts.models import User
from apps.organizations.models import Department
from apps.assets.models import AssetCategory, Asset
from apps.lifecycle.models import (
    PurchaseRequest, PurchaseRequestItem,
    AssetReceipt, AssetReceiptItem,
    Maintenance, MaintenancePlan, MaintenanceTask,
    DisposalRequest, DisposalItem
)


@pytest.fixture
def department(org):
    return Department.objects.create(
        name="研发部",
        code="RD",
        org=org,
    )


@pytest.fixture
def user(org, department):
    return User.objects.create_user(
        username="testuser",
        password="password",
        org=org,
        department=department,
    )


@pytest.fixture
def approver(org, department):
    return User.objects.create_user(
        username="approver",
        password="password",
        org=org,
        department=department,
        is_admin=True,
    )


@pytest.fixture
def asset_category(org):
    return AssetCategory.objects.create(
        name="电子设备",
        code="IT",
        org=org,
    )


@pytest.fixture
def asset(org, asset_category, department):
    return Asset.objects.create(
        asset_no="ZC2024010001",
        asset_name="笔记本电脑",
        category=asset_category,
        department=department,
        original_value=5000,
        org=org,
    )


@pytest.fixture
def purchase_request(user, department):
    return PurchaseRequest.objects.create(
        request_no="PR2024010001",
        applicant=user,
        department=department,
        request_date=timezone.now().date(),
        expected_date=timezone.now().date() + timezone.timedelta(days=30),
        reason="测试申请",
        org=user.org,
        created_by=user,
    )


@pytest.fixture
def purchase_request_with_items(purchase_request, asset_category):
    PurchaseRequestItem.objects.create(
        purchase_request=purchase_request,
        sequence=1,
        asset_category=asset_category,
        item_name="笔记本电脑",
        specification="ThinkPad X1",
        quantity=10,
        unit="台",
        unit_price=4500,
        total_amount=45000,
        org=purchase_request.org,
    )
    return purchase_request


@pytest.fixture
def asset_receipt(user, purchase_request):
    return AssetReceipt.objects.create(
        receipt_no="RC2024010001",
        purchase_request=purchase_request,
        receipt_date=timezone.now().date(),
        supplier="联想代理商",
        receiver=user,
        org=user.org,
        created_by=user,
    )


@pytest.fixture
def maintenance(user, asset):
    return Maintenance.objects.create(
        maintenance_no="MT2024010001",
        asset=asset,
        reporter=user,
        report_time=timezone.now(),
        fault_description="测试故障",
        org=asset.org,
        created_by=user,
    )


@pytest.fixture
def disposal_request(user, department):
    return DisposalRequest.objects.create(
        request_no="DS2024010001",
        applicant=user,
        department=department,
        request_date=timezone.now().date(),
        disposal_type="scrap",
        disposal_reason="测试报废",
        org=user.org,
        created_by=user,
    )


@pytest.fixture
def disposal_item(disposal_request, asset):
    return DisposalItem.objects.create(
        disposal_request=disposal_request,
        sequence=1,
        asset=asset,
        original_value=asset.original_value,
        accumulated_depreciation=asset.accumulated_depreciation,
        net_value=asset.net_value,
        org=disposal_request.org,
    )
```

---

## 8. 测试执行

```bash
# 运行所有生命周期模块测试
pytest apps/lifecycle/tests/

# 运行特定测试文件
pytest apps/lifecycle/tests/test_purchase_models.py

# 运行特定测试类
pytest apps/lifecycle/tests/test_purchase_service.py::TestPurchaseRequestService

# 生成覆盖率报告
pytest --cov=apps/lifecycle --cov-report=html apps/lifecycle/tests/

# 运行性能测试
pytest apps/lifecycle/tests/ -m performance

# 运行E2E测试
pytest tests/e2e/ -m e2e
```
