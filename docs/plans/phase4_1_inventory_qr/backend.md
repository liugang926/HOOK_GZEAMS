# Phase 4.1: 二维码扫描盘点 - Backend 实现文档

---

## 公共模型引用

> 本模块所有后端组件必须继承以下公共基类

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| **Filter** | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| **Service** | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一CRUD方法 |

---

## API 接口规范

---

### 统一响应格式

#### 成功响应格式

##### 单条记录响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "asset_code": "ASSET001",
        "qr_code": "QR-ASSET001-20260115",
        "scan_time": "2026-01-14T10:30:00Z",
        "location": "A区-01-01",
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

##### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/inventory/scans/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "asset_code": "ASSET001",
                "qr_code": "QR-ASSET001-20260115",
                "scan_time": "2026-01-14T10:30:00Z",
                ...
            }
        ]
    }
}
```

##### 创建/更新响应

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "asset_code": "ASSET001",
        "qr_code": "QR-ASSET001-20260115",
        ...
    }
}
```

##### 删除响应

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "删除成功"
}
```

#### 错误响应格式

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "qr_code": ["二维码不能为空"],
            "asset": ["资产不存在"]
        }
    }
}
```

### 统一错误码定义

#### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 请求数据验证失败 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `PERMISSION_DENIED` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `METHOD_NOT_ALLOWED` | 405 | 方法不允许 |
| `CONFLICT` | 409 | 资源冲突 |
| `ORGANIZATION_MISMATCH` | 403 | 组织不匹配 |
| `SOFT_DELETED` | 410 | 资源已删除 |
| `RATE_LIMIT_EXCEEDED` | 429 | 请求频率超限 |
| `SERVER_ERROR` | 500 | 服务器内部错误 |

#### 盘点模块特有错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `INVALID_QR_CODE` | 400 | 二维码格式错误 |
| `ASSET_NOT_FOUND` | 404 | 资产不存在 |
| `DUPLICATE_SCAN` | 409 | 重复扫描记录 |
| `INVENTORY_NOT_STARTED` | 400 | 盘点任务未开始 |
| `INVENTORY_COMPLETED` | 400 | 盘点任务已完成 |

### 批量操作 API 规范

#### 批量删除

```http
POST /api/inventory/scans/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

**响应 (全部成功)**

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

**响应 (部分失败)**

```http
HTTP/1.1 207 Multi-Status

{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "success": true
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "success": false,
            "error": "记录不存在"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

#### 批量恢复

```http
POST /api/inventory/scans/batch-restore/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应格式与批量删除相同**

#### 批量更新

```http
POST /api/inventory/scans/batch-update/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "location": "B区-02-02"
    }
}
```

**响应格式与批量删除相同**

### 标准 CRUD API

#### 扫描记录管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory/scans/` | 分页查询扫描记录 |
| GET | `/api/inventory/scans/{id}/` | 获取单条扫描记录详情 |
| POST | `/api/inventory/scans/` | 创建新的扫描记录 |
| PUT | `/api/inventory/scans/{id}/` | 完整更新扫描记录 |
| PATCH | `/api/inventory/scans/{id}/` | 部分更新扫描记录 |
| DELETE | `/api/inventory/scans/{id}/` | 软删除扫描记录 |
| GET | `/api/inventory/scans/deleted/` | 查询已删除的扫描记录 |
| POST | `/api/inventory/scans/{id}/restore/` | 恢复单条已删除的扫描记录 |

#### 资产二维码管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/assets/{id}/qr-code/` | 获取资产二维码图片 |
| POST | `/api/assets/{id}/generate-qr/` | 生成新的资产二维码 |
| GET | `/api/assets/qr-codes/` | 分页查询资产二维码信息 |
| POST | `/api/assets/batch-generate-qr/` | 批量生成资产二维码 |

#### 扩展操作 API

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| POST | `/api/inventory/scans/batch-scan/` | 批量上传扫描记录 |
| GET | `/api/inventory/scans/{id}/history/` | 获取扫描记录变更历史 |
| GET | `/api/inventory/scans/statistics/` | 获取扫描统计信息 |
| POST | `/api/inventory/scans/validate-qr/` | 验证二维码有效性 |

### 盘点任务相关 API

#### 盘点任务管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory/tasks/` | 分页查询盘点任务 |
| GET | `/api/inventory/tasks/{id}/` | 获取盘点任务详情 |
| POST | `/api/inventory/tasks/` | 创建新的盘点任务 |
| PUT | `/api/inventory/tasks/{id}/` | 完整更新盘点任务 |
| PATCH | `/api/inventory/tasks/{id}/` | 部分更新盘点任务 |
| POST | `/api/inventory/tasks/{id}/start/` | 开始盘点任务 |
| POST | `/api/inventory/tasks/{id}/complete/` | 完成盘点任务 |
| POST | `/api/inventory/tasks/{id}/cancel/` | 取消盘点任务 |

#### 盘点统计 API

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/inventory/tasks/{id}/statistics/` | 获取任务统计信息 |
| GET | `/api/inventory/tasks/{id}/discrepancy/` | 获取盘点差异报告 |
| POST | `/api/inventory/tasks/{id}/approve-discrepancy/` | 审批盘点差异 |
| GET | `/api/inventory/reports/summary/` | 获取盘点汇总报告 |

### 数据导入导出 API

#### 扫描记录导出

```http
POST /api/inventory/scans/export/
Content-Type: application/json

{
    "format": "xlsx",
    "filters": {
        "date_from": "2026-01-01",
        "date_to": "2026-01-31"
    },
    "options": {
        "include_qr_codes": true,
        "group_by_location": true
    }
}
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="scan_records_20260115.xlsx"

[文件内容]
```

#### 盘点报告导出

```http
POST /api/inventory/reports/export/
Content-Type: application/json

{
    "format": "pdf",
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "report_type": "comprehensive"
}
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="inventory_report_20260115.pdf"

[PDF文件内容]
```

### 移动端 API

#### 扫码上传

```http
POST /api/mobile/inventory/scan/
Content-Type: multipart/form-data

qr_code: [QR码图片或字符串]
location: "A区-01-01"
device_id: "MOB-001"
timestamp: "2026-01-15T10:30:00Z"
```

**响应**：

```http
HTTP/1.1 201 Created

{
    "success": true,
    "message": "扫描成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "asset_code": "ASSET001",
        "asset_name": "办公电脑",
        "qr_code": "QR-ASSET001-20260115",
        "scan_time": "2026-01-15T10:30:00Z",
        "status": "scanned"
    }
}
```

#### 批量扫码

```http
POST /api/mobile/inventory/batch-scan/
Content-Type: application/json

{
    "scans": [
        {
            "qr_code": "QR-ASSET001-20260115",
            "location": "A区-01-01"
        },
        {
            "qr_code": "QR-ASSET002-20260115",
            "location": "A区-01-02"
        }
    ],
    "device_id": "MOB-001"
}
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "批量扫描完成",
    "summary": {
        "total": 2,
        "succeeded": 2,
        "failed": 0
    },
    "results": [
        {
            "qr_code": "QR-ASSET001-20260115",
            "success": true,
            "asset_code": "ASSET001",
            "message": "扫描成功"
        },
        {
            "qr_code": "QR-ASSET002-20260115",
            "success": false,
            "error": "资产不存在"
        }
    ]
}
```

#### 离线同步

```http
POST /api/mobile/inventory/sync/
Content-Type: application/json

{
    "device_id": "MOB-001",
    "last_sync_time": "2026-01-15T10:00:00Z",
    "offline_scans": [...]
}
```

---

## 实现建议

### 1. 二维码生成和验证

```python
# backend/apps/inventory/utils/qr_code.py

import qrcode
import qrcode.image.styledpil
from io import BytesIO
import base64
import hashlib


class QRCodeGenerator:
    """二维码生成器"""

    def generate_asset_qr(self, asset_code, organization_code, suffix=None):
        """生成资产二维码"""
        # 构建二维码内容 (建议使用 SystemConfig 配置模板)
        # template = SystemConfig.get('QR_CODE_TEMPLATE', default='QR-{asset_code}-{org_code}')
        content = f"QR-{asset_code}-{organization_code}"
        if suffix:
            content = f"{content}-{suffix}"

        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)

        # 生成图片
        img = qr.make_image(fill_color="black", back_color="white")

        # 转换为base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "content": content,
            "qr_code": content,
            "image": f"data:image/png;base64,{qr_base64}"
        }

    def validate_qr_code(self, qr_code):
        """验证二维码格式"""
        if not qr_code:
            return False, "二维码不能为空"

        # 验证格式：QR-ASSET001-ORG2026-20260115
        parts = qr_code.split('-')
        if len(parts) != 4 or not parts[0] == 'QR':
            return False, "二维码格式错误"

        if not parts[1].startswith('ASSET'):
            return False, "无效的资产编码"

        if not parts[2].startswith('ORG'):
            return False, "无效的组织编码"

        return True, "验证通过"


class QRCodeScanner:
    """二维码扫描器"""

    def scan_from_image(self, image_file):
        """从图片文件扫描二维码"""
        try:
            # 使用第三方库扫描二维码
            import pyzbar.pyzbar as pyzbar
            from PIL import Image

            # 读取图片
            image = Image.open(image_file)

            # 扫描二维码
            barcodes = pyzbar.decode(image)

            if not barcodes:
                return None, "未检测到二维码"

            # 获取第一个二维码
            barcode = barcodes[0]
            qr_code = barcode.data.decode('utf-8')

            return qr_code, "扫描成功"
        except Exception as e:
            return None, f"扫描失败: {str(e)}"

    def batch_scan_images(self, image_files):
        """批量扫描二维码图片"""
        results = []

        for i, image_file in enumerate(image_files):
            qr_code, message = self.scan_from_image(image_file)
            results.append({
                "index": i,
                "qr_code": qr_code,
                "success": qr_code is not None,
                "message": message
            })

        return results
```

### 2. 批量扫描服务

```python
# backend/apps/inventory/services/batch_scan_service.py

from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import ScanRecord


class BatchScanService(BaseCRUDService):
    """批量扫描服务"""

    def __init__(self):
        super().__init__(ScanRecord)

    def batch_create_scans(self, scan_data, user=None):
        """批量创建扫描记录"""
        results = []
        success_count = 0
        error_count = 0

        with transaction.atomic():
            for scan in scan_data:
                try:
                    # 验证二维码
                    from apps.inventory.utils.qr_code import QRCodeGenerator
                    validator = QRCodeGenerator()
                    is_valid, message = validator.validate_qr_code(scan.get('qr_code'))

                    if not is_valid:
                        results.append({
                            "qr_code": scan.get('qr_code'),
                            "success": False,
                            "error": message,
                            "data": None
                        })
                        error_count += 1
                        continue

                    # 查找资产
                    from apps.assets.models import Asset
                    qr_content = scan['qr_code']
                    asset_code = qr_content.split('-')[1]

                    try:
                        asset = Asset.objects.get(
                            code=asset_code,
                            is_deleted=False,
                            org=user.org if user else None
                        )
                    except Asset.DoesNotExist:
                        results.append({
                            "qr_code": qr_content,
                            "success": False,
                            "error": "资产不存在",
                            "data": None
                        })
                        error_count += 1
                        continue

                    # 创建扫描记录
                    scan_record = self.create({
                        'asset': asset,
                        'qr_code': qr_content,
                        'location': scan.get('location', asset.location),
                        'scan_time': scan.get('scan_time'),
                        'scan_device': scan.get('scan_device'),
                        'scan_operator': user,
                    }, user=user)

                    results.append({
                        "qr_code": qr_content,
                        "success": True,
                        "message": "扫描成功",
                        "data": {
                            "id": scan_record.id,
                            "asset_code": asset.code,
                            "asset_name": asset.name
                        }
                    })
                    success_count += 1

                except Exception as e:
                    results.append({
                        "qr_code": scan.get('qr_code', ''),
                        "success": False,
                        "error": str(e),
                        "data": None
                    })
                    error_count += 1

        return {
            "summary": {
                "total": len(scan_data),
                "succeeded": success_count,
                "failed": error_count
            },
            "results": results
        }

    def get_scan_statistics(self, task_id=None, date_from=None, date_to=None):
        """获取扫描统计信息"""
        from django.db.models import Count, Q
        from datetime import datetime

        queryset = ScanRecord.objects.filter(is_deleted=False)

        # 过滤条件
        if task_id:
            queryset = queryset.filter(task_id=task_id)

        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            queryset = queryset.filter(created_at__date__lte=date_to)

        # 统计数据
        total_scans = queryset.count()
        unique_assets = queryset.values('asset').distinct().count()

        # 按日期统计
        daily_stats = queryset.extra(
            select={'date': 'date(created_at)'}
        ).values('date').annotate(count=Count('id')).order_by('date')

        # 按位置统计
        location_stats = queryset.values('location').annotate(
            count=Count('id'),
            assets=Count('asset', distinct=True)
        ).order_by('-count')

        return {
            "total_scans": total_scans,
            "unique_assets": unique_assets,
            "daily_statistics": list(daily_stats),
            "location_statistics": list(location_stats)
        }
```

### 3. 盘点差异处理

```python
# backend/apps/inventory/services/discrepancy_service.py

from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import DiscrepancyRecord


class DiscrepancyService(BaseCRUDService):
    """盘点差异服务"""

    def __init__(self):
        super().__init__(DiscrepancyRecord)

    def create_discrepancy(self, inventory_task, asset, expected_quantity, actual_quantity, user):
        """创建盘点差异记录"""
        from apps.inventory.models import DiscrepancyType

        # 确定差异类型 (使用 Dictionary)
        # from apps.system.services.dictionary_service import DictionaryService
        if expected_quantity > actual_quantity:
            # discrepancy_type = DictionaryService.get_item('INVENTORY_DISCREPANCY_TYPE', 'shortage')
            discrepancy_code = 'shortage'
            quantity_diff = expected_quantity - actual_quantity
        elif expected_quantity < actual_quantity:
            # discrepancy_type = DictionaryService.get_item('INVENTORY_DISCREPANCY_TYPE', 'surplus')
            discrepancy_code = 'surplus'
            quantity_diff = actual_quantity - expected_quantity
        else:
            return None  # 无差异

        # 创建差异记录
        discrepancy = self.create({
            'inventory_task': inventory_task,
            'asset': asset,
            'expected_quantity': expected_quantity,
            'actual_quantity': actual_quantity,
            'quantity_difference': quantity_diff,
            'discrepancy_type': discrepancy_type,
            'status': 'pending',
            'created_by': user,
            'org': user.org,
        }, user=user)

        return discrepancy

    def batch_create_discrepancies(self, inventory_task, scan_results, user):
        """批量创建盘点差异"""
        discrepancies = []
        success_count = 0
        error_count = 0

        # 获取预期资产列表
        expected_assets = inventory_task.assets.all()

        with transaction.atomic():
            for expected_asset in expected_assets:
                # 查找实际扫描记录
                scan_record = next(
                    (r for r in scan_results if r['asset_code'] == expected_asset.code),
                    None
                )

                try:
                    if scan_record:
                        # 已扫描，检查数量
                        expected_qty = expected_asset.quantity
                        actual_qty = scan_record.get('quantity', 1)

                        if expected_qty != actual_qty:
                            discrepancy = self.create_discrepancy(
                                inventory_task,
                                expected_asset,
                                expected_qty,
                                actual_qty,
                                user
                            )
                            if discrepancy:
                                discrepancies.append(discrepancy)
                    else:
                        # 未扫描，创建缺失差异
                        discrepancy = self.create_discrepancy(
                            inventory_task,
                            expected_asset,
                            expected_asset.quantity,
                            0,
                            user
                        )
                        if discrepancy:
                            discrepancies.append(discrepancy)

                    success_count += 1

                except Exception as e:
                    error_count += 1

        return {
            "summary": {
                "total": len(expected_assets),
                "discrepancies": len(discrepancies),
                "success": success_count,
                "errors": error_count
            },
            "discrepancies": discrepancies
        }

    def approve_discrepancy(self, discrepancy_id, approved_by, resolution_note=None):
        """审批盘点差异"""
        try:
            discrepancy = self.get(discrepancy_id)

            # 更新状态
            discrepancy.status = 'approved'
            discrepancy.approved_by = approved_by
            discrepancy.resolution_note = resolution_note
            discrepancy.resolution_time = timezone.now()
            discrepancy.org = approved_by.org
            discrepancy.save()

            # 更新资产状态（根据差异类型）
            if discrepancy.discrepancy_type.code == 'shortage':
                # 短缺：更新资产状态
                discrepancy.asset.status = 'discrepancy'
                discrepancy.asset.save()
            elif discrepancy.discrepancy_type.code == 'surplus':
                # 溢出：创建新资产记录或标记
                pass

            return True
        except Exception as e:
            return False
```

### 4. 移动端适配

```python
# backend/apps/mobile/serializers.py

from rest_framework import serializers
from apps.inventory.models import ScanRecord


class MobileScanSerializer(serializers.ModelSerializer):
    """移动端扫描序列化器"""

    class Meta:
        model = ScanRecord
        fields = [
            'id', 'asset_code', 'asset_name', 'qr_code',
            'location', 'scan_time', 'status'
        ]
        read_only_fields = ['asset_code', 'asset_name', 'qr_code']


class MobileBatchScanSerializer(serializers.Serializer):
    """移动端批量扫描序列化器"""

    scans = serializers.ListField(
        child=serializers.DictField(),
        help_text="扫描记录列表"
    )

    def validate_scans(self, value):
        """验证扫描数据"""
        if not value:
            raise serializers.ValidationError("扫描数据不能为空")

        # 验证每个扫描记录
        required_fields = ['qr_code', 'location']
        for scan in value:
            for field in required_fields:
                if field not in scan or not scan[field]:
                    raise serializers.ValidationError(
                        f"扫描记录缺少必需字段: {field}"
                    )

        return value


class MobileOfflineSyncSerializer(serializers.Serializer):
    """移动端离线同步序列化器"""

    device_id = serializers.CharField(max_length=50)
    last_sync_time = serializers.DateTimeField()
    offline_scans = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    def validate_offline_scans(self, value):
        """验证离线扫描数据"""
        if not value:
            return []

        # 验证离线数据格式
        required_fields = ['qr_code', 'location', 'timestamp']
        for scan in value:
            for field in required_fields:
                if field not in scan or not scan[field]:
                    raise serializers.ValidationError(
                        f"离线扫描记录缺少必需字段: {field}"
                    )

        return value
```

---

## 部署和监控

### 1. 扫描性能优化

```python
# backend/apps/inventory/migrations/0005_add_indexes_for_scans.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_inventorytask_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE INDEX IF NOT EXISTS idx_inventory_scanrecord_qr_code
            ON inventory_scanrecord USING gin(to_tsvector('simple', qr_code));

            CREATE INDEX IF NOT EXISTS idx_inventory_scanrecord_asset_code
            ON inventory_scanrecord (asset_id);

            CREATE INDEX IF NOT EXISTS idx_inventory_scanrecord_created_at
            ON inventory_scanrecord (created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_inventory_scanrecord_location
            ON inventory_scanrecord (location);
            """
        ),
    ]
```

### 2. 监控指标

```python
# backend/apps/inventory/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge
from django.conf import settings

# 扫描次数
INVENTORY_SCANS = Counter(
    'inventory_scans_total',
    'Total inventory scans',
    ['location', 'status']
)

# 扫描耗时
SCAN_DURATION = Histogram(
    'inventory_scan_duration_seconds',
    'Inventory scan duration',
    ['device_type']
)

# 扫描结果统计
SCAN_RESULTS = Counter(
    'inventory_scan_results_total',
    'Inventory scan results',
    ['result_type']
)

# 活跃盘点任务
ACTIVE_INVENTORY_TASKS = Gauge(
    'active_inventory_tasks',
    'Number of active inventory tasks'
)

# 盘点差异率
DISCREPANCY_RATE = Gauge(
    'inventory_discrepancy_rate',
    'Inventory discrepancy rate percentage'
)
```

### 3. 健康检查

```python
# backend/apps/inventory/health_checks.py

from django.db import connection
from redis.exceptions import RedisError
from apps.inventory.models import ScanRecord
from apps.inventory.services.scan_service import ScanService


def check_inventory_system():
    """检查库存盘点系统健康状态"""
    health_status = {
        'overall': 'healthy',
        'checks': {}
    }

    # 检查数据库连接
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    # 检查Redis连接（如果使用）
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        health_status['checks']['redis'] = 'healthy'
    except Exception as e:
        health_status['checks']['redis'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    # 检查扫描服务
    try:
        scan_service = ScanService()
        test_result = scan_service.validate_qr_code("QR-TEST-ORG2026-TESTDATE")
        health_status['checks']['scan_service'] = 'healthy'
    except Exception as e:
        health_status['checks']['scan_service'] = f'unhealthy: {str(e)}'
        health_status['overall'] = 'degraded'

    # 检查活跃任务数
    try:
        active_tasks = ScanRecord.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).count()
        health_status['checks']['recent_scans'] = active_tasks
    except Exception as e:
        health_status['checks']['recent_scans'] = f'error: {str(e)}'
        health_status['overall'] = 'degraded'

    return health_status
```

---

## 总结

### 架构特点

1. **二维码管理**：支持动态生成和验证二维码，确保资产唯一标识
2. **批量处理**：高效支持大规模资产的批量扫描和数据处理
3. **移动端适配**：针对移动场景优化，支持离线扫描和批量上传
4. **差异分析**：自动识别盘点差异，支持差异审批和状态更新
5. **性能优化**：索引优化和批量操作，确保大规模数据处理的效率

### 业务流程

1. **资产编码**：为每个资产生成唯一的二维码标识
2. **盘点任务**：创建盘点任务，确定盘点范围和时间
3. **扫码盘点**：使用移动设备扫描资产二维码，记录位置和时间
4. **差异分析**：自动比对预期和实际扫描结果，识别差异
5. **审批处理**：对盘点差异进行审批，更新资产状态

### 集成建议

1. **移动应用**：提供专业的扫码应用，支持离线操作
2. **API集成**：提供标准API，支持与其他系统集成
3. **报表系统**：生成专业的盘点报告和分析报表
4. **监控告警**：实时监控盘点状态，异常情况及时告警
