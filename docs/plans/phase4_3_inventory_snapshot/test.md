# Phase 4.3: 盘点快照和差异处理 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 差异检测测试 | pytest | DifferenceDetectionService |
| 差异处理测试 | pytest | DifferenceResolutionService |
| API测试 | pytest | 差异API |

---

## 1. 差异检测测试

```python
# tests/inventory/test_difference_detection.py

import pytest
from apps.inventory.services.difference_detection import DifferenceDetectionService
from apps.inventory.models import InventoryTask, InventorySnapshot, InventoryScan


class TestDifferenceDetectionService:
    """差异检测服务测试"""

    @pytest.fixture
    def service(self):
        return DifferenceDetectionService()

    @pytest.fixture
    def task_with_snapshots(self, db, organization, user, assets):
        """创建带快照的盘点任务"""
        task = InventoryTask.objects.create(
            organization=organization,
            task_code='PD001',
            task_name='测试盘点',
            planned_by=user,
            total_count=3
        )

        # 创建快照
        for asset in assets:
            InventorySnapshot.objects.create(
                task=task,
                asset=asset,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name
            )

        return task

    def test_detect_missing_assets(self, service, task_with_snapshots):
        """测试检测盘亏"""
        # 只扫描了部分资产
        InventoryScan.objects.create(
            task=task_with_snapshots,
            asset=task_with_snapshots.snapshots.first().asset,
            scanned_by=task_with_snapshots.planned_by,
            scan_method='qr',
            scan_status='normal'
        )

        differences = service.detect_differences(task_with_snapshots)

        # 应该有2个盘亏（3个快照 - 1个扫描）
        missing = [d for d in differences if d.difference_type == 'missing']
        assert len(missing) == 2

    def test_detect_location_mismatch(self, service, inventory_task):
        """测试检测位置不符"""
        snapshot = inventory_task.snapshots.first()
        asset = snapshot.asset

        # 扫描时位置变更
        InventoryScan.objects.create(
            task=inventory_task,
            asset=asset,
            scanned_by=inventory_task.planned_by,
            scan_method='qr',
            scan_status='location_changed',
            original_location=snapshot.location_name,
            actual_location='新位置'
        )

        differences = service.detect_differences(inventory_task)

        location_diffs = [d for d in differences if d.difference_type == 'location_mismatch']
        assert len(location_diffs) > 0
```

---

## 2. 差异处理测试

```python
# tests/inventory/test_difference_resolution.py

import pytest
from apps.inventory.services.difference_resolution import DifferenceResolutionService
from apps.inventory.models import InventoryDifference


class TestDifferenceResolutionService:
    """差异处理服务测试"""

    @pytest.fixture
    def service(self):
        return DifferenceResolutionService()

    def test_resolve_missing_asset(self, service, inventory_difference, user):
        """测试处理盘亏"""
        resolved = service.resolve_difference(
            difference=inventory_difference,
            resolution="确认丢失",
            resolved_by=user,
            update_asset=True
        )

        assert resolved.status == 'resolved'

        # 验证资产状态更新
        inventory_difference.asset.refresh_from_db()
        assert inventory_difference.asset.asset_status == 'lost'
        assert inventory_difference.asset.is_deleted is True

    def test_resolve_location_mismatch(self, service, inventory_difference, user):
        """测试处理位置不符"""
        resolved = service.resolve_difference(
            difference=inventory_difference,
            resolution="更新位置为: 301室",
            resolved_by=user,
            update_asset=True
        )

        assert resolved.status == 'resolved'
```

---

## 测试执行

```bash
pytest tests/inventory/test_difference_*.py -v
```

---

## 后续任务

1. Phase 5.1: 实现万达宝M18采购对接
2. Phase 5.2: 实现万达宝M18财务对接
