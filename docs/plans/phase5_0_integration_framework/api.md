# Phase 5.0: 通用ERP集成框架 - API接口定义

## 公共模型引用

本模块所有后端组件均继承自公共基类，自动获得组织隔离、软删除、审计字段、批量操作等标准功能。

| 组件类型 | 基类 |
|---------|------|
| Model | BaseModel |
| Serializer | BaseModelSerializer |
| ViewSet | BaseModelViewSetWithBatch |
| Service | BaseCRUDService |
| Filter | BaseModelFilter |

---

## 接口概览

| 方法 | 路径 | 说明 |
|------|------|------|
| 集成配置 | | |
| GET | `/api/integration/configs/` | 获取集成配置列表 |
| POST | `/api/integration/configs/` | 创建集成配置 |
| GET | `/api/integration/configs/{id}/` | 获取配置详情 |
| PUT | `/api/integration/configs/{id}/` | 更新集成配置 |
| DELETE | `/api/integration/configs/{id}/` | 删除集成配置 |
| POST | `/api/integration/configs/{id}/test/` | 测试连接 |
| 同步任务 | | |
| GET | `/api/integration/sync-tasks/` | 获取同步任务列表 |
| GET | `/api/integration/sync-tasks/{id}/` | 获取任务详情 |
| POST | `/api/integration/configs/{id}/sync/` | 触发手动同步 |
| POST | `/api/integration/sync-tasks/{id}/cancel/` | 取消同步任务 |
| 集成日志 | | |
| GET | `/api/integration/logs/` | 获取集成日志 |
| GET | `/api/integration/logs/{id}/` | 获取日志详情 |
| 数据映射 | | |
| GET | `/api/integration/mappings/` | 获取映射模板列表 |
| POST | `/api/integration/mappings/` | 创建映射模板 |
| GET | `/api/integration/mappings/{id}/` | 获取映射详情 |
| PUT | `/api/integration/mappings/{id}/` | 更新映射模板 |
| DELETE | `/api/integration/mappings/{id}/` | 删除映射模板 |
| 系统信息 | | |
| GET | `/api/integration/supported-systems/` | 获取支持的系统列表 |
| GET | `/api/integration/supported-modules/` | 获取支持的模块列表 |

---

## 1. 集成配置

### GET /api/integration/configs/

获取集成配置列表

**请求参数：**

```json
{
  "system_type": "m18",          // 系统类型（可选）
  "is_enabled": true,            // 是否启用（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "count": 3,
        "results": [
    {
      "id": "uuid",
      "organization": {
        "id": "uuid",
        "name": "示例公司"
      },
      "system_type": "m18",
      "system_name": "生产环境M18",
      "enabled_modules": ["procurement", "finance"],
      "sync_config": {
        "auto_sync": true,
        "sync_interval": 60
      },
      "is_enabled": true,
      "health_status": "healthy",
      "last_health_check_at": "2024-01-15T10:00:00Z",
      "last_sync_at": "2024-01-15T09:30:00Z",
      "last_sync_status": "success",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /api/integration/configs/

创建集成配置

**请求体：**

```json
{
  "system_type": "m18",
  "system_name": "生产环境M18",
  "connection_config": {
    "api_url": "http://m18.example.com/M18/api/",
    "api_key": "your-api-key",
    "username": "admin",
    "password": "encrypted-password",
    "timeout": 30
  },
  "enabled_modules": ["procurement", "finance"],
  "sync_config": {
    "auto_sync": true,
    "sync_interval": 60
  },
  "is_enabled": true
}
```

**响应数据：**

```json
{
    "success": true,
    "message": "集成配置创建成功",
    "data": {
        "id": "uuid",
        "system_type": "m18",
        "system_name": "生产环境M18",
        "is_enabled": true,
        "health_status": "unhealthy",
        "created_at": "2024-01-15T10:00:00Z"
    }
}
```

### POST /api/integration/configs/{id}/test/

测试连接

**请求体：** 无

**响应数据：**

```json
{
    "success": true,
    "message": "连接测试成功",
    "data": {
        "response_time_ms": 156,
        "details": {
            "api_version": "v2.0",
            "server_time": "2024-01-15T10:00:00Z",
            "authenticated_user": "admin"
        }
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "CONNECTION_FAILED",
        "message": "连接测试失败",
        "details": {
            "error": "API认证失败"
        }
    }
}
```

---

## 2. 同步任务

### GET /api/integration/sync-tasks/

获取同步任务列表

**请求参数：**

```json
{
  "config_id": "uuid",           // 配置ID（可选）
  "system_type": "m18",          // 系统类型（可选）
  "module_type": "procurement",  // 模块类型（可选）
  "status": "success",           // 状态（可选）
  "date_from": "2024-01-01",     // 开始日期（可选）
  "date_to": "2024-01-31",       // 结束日期（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
    "success": true,
    "data": {
        "count": 50,
        "next": "https://api.example.com/api/integration/sync-tasks/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "task_id": "sync_task_123456",
                "config": {
                    "id": "uuid",
                    "system_type": "m18",
                    "system_name": "生产环境M18"
                },
                "module_type": "procurement",
                "direction": "pull",
                "business_type": "purchase_order",
                "status": "success",
                "total_count": 100,
                "success_count": 98,
                "failed_count": 2,
                "error_summary": [
                    {
                        "business_id": "PO123",
                        "error": "数据格式错误"
                    },
                    {
                        "business_id": "PO124",
                        "error": "供应商不存在"
                    }
                ],
                "started_at": "2024-01-15T09:00:00Z",
                "completed_at": "2024-01-15T09:02:30Z",
                "duration_ms": 150000,
                "created_at": "2024-01-15T09:00:00Z"
            }
        ]
    }
}
```

### GET /api/integration/sync-tasks/{id}/

获取任务详情（含执行日志）

**响应数据：**

```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "task_id": "sync_task_123456",
        "config": {...},
        "module_type": "procurement",
        "direction": "pull",
        "business_type": "purchase_order",
        "sync_params": {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        },
        "status": "success",
        "total_count": 100,
        "success_count": 98,
        "failed_count": 2,
        "error_summary": [...],
        "started_at": "2024-01-15T09:00:00Z",
        "completed_at": "2024-01-15T09:02:30Z",
        "duration_ms": 150000,
        "logs": [
            {
                "id": "uuid",
                "request_method": "GET",
                "request_url": "/po/purchaseOrder",
                "status_code": 200,
                "success": true,
                "duration_ms": 523
            }
        ]
    }
}
```

### POST /api/integration/configs/{id}/sync/

触发手动同步

**请求体：**

```json
{
  "module_type": "procurement",     // 模块类型
  "business_type": "purchase_order", // 业务类型
  "direction": "pull",               // 同步方向
  "sync_params": {                   // 同步参数
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "async": true                      // 是否异步执行
}
```

**响应数据（异步）：**

```json
{
    "success": true,
    "message": "同步任务已创建",
    "data": {
        "task_id": "sync_task_123456",
        "celery_task_id": "celery-task-id",
        "status": "pending"
    }
}
```

**响应数据（同步）：**

```json
{
    "success": true,
    "message": "同步完成",
    "data": {
        "task_id": "sync_task_123456",
        "status": "success",
        "total": 100,
        "succeeded": 98,
        "failed": 2,
        "errors": [...]
    }
}
```

**错误响应：**

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "同步参数验证失败",
        "details": {
            "start_date": ["开始日期不能晚于结束日期"]
        }
    }
}
```

---

## 3. 集成日志

### GET /api/integration/logs/

获取集成API调用日志

**请求参数：**

```json
{
  "sync_task_id": "uuid",        // 关联任务ID（可选）
  "system_type": "m18",          // 系统类型（可选）
  "integration_type": "m18_po",  // 集成类型（可选）
  "action": "pull",              // 操作类型（可选）
  "success": true,               // 是否成功（可选）
  "date_from": "2024-01-01",     // 开始日期（可选）
  "page": 1,
  "size": 50
}
```

**响应数据：**

```json
{
    "success": true,
    "data": {
        "count": 500,
        "next": "https://api.example.com/api/integration/logs/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "sync_task": {
                    "id": "uuid",
                    "task_id": "sync_task_123456"
                },
                "system_type": "m18",
                "integration_type": "m18_po",
                "action": "pull",
                "request_method": "GET",
                "request_url": "GET /po/purchaseOrder",
                "request_headers": {
                    "Content-Type": "application/json",
                    "X-API-Key": "***"
                },
                "request_body": {},
                "status_code": 200,
                "response_body": {
                    "data": [...]
                },
                "success": true,
                "duration_ms": 523,
                "business_type": "purchase_order",
                "business_id": "PO123",
                "external_id": "PO_M18_123",
                "created_at": "2024-01-15T09:00:00Z"
            }
        ]
    }
}
```

---

## 4. 数据映射

### GET /api/integration/mappings/

获取映射模板列表

**请求参数：**

```json
{
  "system_type": "m18",          // 系统类型（可选）
  "business_type": "purchase_order", // 业务类型（可选）
  "is_active": true,             // 是否启用（可选）
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
    "success": true,
    "data": {
        "count": 10,
        "next": "https://api.example.com/api/integration/mappings/?page=2",
        "previous": null,
        "results": [
            {
                "id": "uuid",
                "organization": {
                    "id": "uuid",
                    "name": "示例公司"
                },
                "system_type": "m18",
                "business_type": "purchase_order",
                "template_name": "M18采购订单映射",
                "field_mappings": {
                    "po_code": "poNo",
                    "supplier_name": "supplier.name",
                    "order_date": "orderDate",
                    "total_amount": "totalAmount",
                    "items": "lineItems"
                },
                "value_mappings": {
                    "status": {
                        "draft": "1",
                        "submitted": "2",
                        "approved": "3"
                    }
                },
                "transform_rules": [
                    {
                        "field": "order_date",
                        "type": "date_format",
                        "from_format": "YYYY-MM-DD",
                        "to_format": "YYYYMMDD"
                    }
                ],
                "is_active": true,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
    }
}
```

### POST /api/integration/mappings/

创建映射模板

**请求体：**

```json
{
  "system_type": "m18",
  "business_type": "purchase_order",
  "template_name": "M18采购订单映射",
  "field_mappings": {
    "po_code": "poNo",
    "supplier_name": "supplier.name"
  },
  "value_mappings": {
    "status": {
      "draft": "1"
    }
  },
  "transform_rules": [],
  "is_active": true
}
```

---

## 5. 系统信息

### GET /api/integration/supported-systems/

获取支持的系统列表

**响应数据：**

```json
{
  "systems": [
    {
      "value": "m18",
      "label": "万达宝M18",
      "logo": "/static/images/integration/m18.png",
      "description": "万达宝ERP系统",
      "supported_modules": ["procurement", "finance", "inventory"],
      "connection_fields": [
        {
          "name": "api_url",
          "label": "API地址",
          "type": "url",
          "required": true
        },
        {
          "name": "api_key",
          "label": "API密钥",
          "type": "password",
          "required": true
        }
      ]
    },
    {
      "value": "sap",
      "label": "SAP",
      "logo": "/static/images/integration/sap.png",
      "description": "SAP ERP系统",
      "supported_modules": ["procurement", "finance", "inventory", "hr"],
      "connection_fields": [
        {
          "name": "host",
          "label": "主机地址",
          "type": "text",
          "required": true
        },
        {
          "name": "client",
          "label": "客户端",
          "type": "text",
          "required": true
        }
      ]
    }
  ]
}
```

### GET /api/integration/supported-modules/

获取支持的模块列表

**响应数据：**

```json
{
  "modules": [
    {
      "value": "procurement",
      "label": "采购管理",
      "description": "采购订单、收货单等",
      "business_types": ["purchase_order", "goods_receipt", "supplier"]
    },
    {
      "value": "finance",
      "label": "财务核算",
      "description": "财务凭证、科目等",
      "business_types": ["voucher", "account", "depreciation"]
    },
    {
      "value": "inventory",
      "label": "库存管理",
      "description": "库存出入库、盘点等",
      "business_types": ["stock_in", "stock_out", "inventory_count"]
    }
  ]
}
```

---

## Serializers

```python
# apps/integration/serializers.py

from rest_framework import serializers
from apps.integration.models import (
    IntegrationConfig, IntegrationSyncTask,
    IntegrationLog, DataMappingTemplate
)


class IntegrationConfigSerializer(serializers.ModelSerializer):
    """集成配置序列化器"""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)
    health_status_display = serializers.CharField(source='get_health_status_display', read_only=True)

    class Meta:
        model = IntegrationConfig
        fields = [
            'id', 'organization', 'system_type', 'system_type_display',
            'system_name', 'connection_config', 'enabled_modules',
            'sync_config', 'is_enabled', 'health_status',
            'health_status_display', 'last_sync_at', 'last_sync_status',
            'last_health_check_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['organization']

    def create(self, validated_data):
        validated_data['organization'] = self.context['request'].user.organization
        return super().create(validated_data)


class IntegrationSyncTaskSerializer(serializers.ModelSerializer):
    """同步任务序列化器"""

    config = IntegrationConfigSerializer(read_only=True)
    module_type_display = serializers.CharField(source='get_module_type_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = IntegrationSyncTask
        fields = '__all__'


class IntegrationLogSerializer(serializers.ModelSerializer):
    """集成日志序列化器"""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)

    class Meta:
        model = IntegrationLog
        fields = '__all__'


class DataMappingTemplateSerializer(serializers.ModelSerializer):
    """数据映射模板序列化器"""

    system_type_display = serializers.CharField(source='get_system_type_display', read_only=True)

    class Meta:
        model = DataMappingTemplate
        fields = '__all__'

    def create(self, validated_data):
        validated_data['organization'] = self.context['request'].user.organization
        return super().create(validated_data)
```

---

## 后续任务

1. Phase 5.1: 实现万达宝M18适配器（基于通用框架）
2. Phase 5.2: 实现财务凭证集成（基于通用框架）
3. 扩展其他ERP适配器
