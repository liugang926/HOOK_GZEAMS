# Phase 4.4: 盘点任务分配与执行 - API接口定义

## 公共模型引用

本模块后端组件继承以下公共基类：

| 组件类型 | 基类 | 自动获得功能 |
|---------|------|-------------|
| Model | BaseModel | 组织隔离、软删除、审计字段 |
| Serializer | BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作端点 |

---

## 接口概览

### 管理端API（任务分配与追踪）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/inventory/tasks/{id}/create-assignments/` | 创建盘点分配 |
| POST | `/api/inventory/tasks/{id}/auto-assign-template/` | 使用模板自动分配 |
| POST | `/api/inventory/tasks/{id}/auto-assign-rules/` | 按规则自动分配 |
| POST | `/api/inventory/tasks/{id}/assign-custodian/` | 按保管人分配（自盘） |
| POST | `/api/inventory/tasks/{id}/assign-random/` | 随机盲抽分配 |
| GET | `/api/inventory/tasks/{id}/assignments/` | 获取任务的所有分配 |
| GET | `/api/inventory/tasks/{id}/progress/` | 获取任务进度统计 |
| POST | `/api/inventory/assignments/{id}/remind/` | 催办执行人 |
| GET | `/api/inventory/tasks/{id}/effective-rules/` | 获取生效的规则 |
| GET | `/api/inventory/tasks/{id}/custodian-preview/` | 预览保管人分配 |
| GET | `/api/inventory/tasks/{id}/unassigned-assets/` | 获取未分配资产 |

### 用户端API（任务执行）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/my/tasks/` | 获取我的盘点任务 |
| GET | `/api/inventory/my/today/` | 获取今日任务汇总 |
| GET | `/api/inventory/my/pending-assets/` | 获取待盘点资产 |
| GET | `/api/inventory/my/scanned-assets/` | 获取已盘点资产 |
| POST | `/api/inventory/my/start/` | 开始盘点 |
| POST | `/api/inventory/my/complete/` | 完成盘点 |
| POST | `/api/inventory/my/record-scan/` | 记录扫描结果 |
| POST | `/api/inventory/my/parse-qr/` | 解析二维码 |
| GET | `/api/inventory/my/asset-by-code/{code}/` | 根据编码获取资产 |
| GET | `/api/inventory/my/check-assignment/` | 检查资产是否在分配范围内 |

### 模板管理API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/assignment-templates/` | 获取模板列表 |
| POST | `/api/inventory/assignment-templates/` | 创建模板 |
| PUT | `/api/inventory/assignment-templates/{id}/` | 更新模板 |
| DELETE | `/api/inventory/assignment-templates/{id}/` | 删除模板 |

### 查看权限管理API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/tasks/{id}/view-config/` | 获取查看配置 |
| PUT | `/api/inventory/tasks/{id}/view-config/` | 更新查看配置 |
| GET | `/api/inventory/tasks/{id}/viewers/` | 获取查看者列表 |
| POST | `/api/inventory/tasks/{id}/viewers/` | 添加查看者 |
| DELETE | `/api/inventory/tasks/{id}/viewers/` | 移除查看者 |
| GET | `/api/inventory/tasks/{id}/my-permission/` | 获取我的查看权限 |
| GET | `/api/inventory/tasks/{id}/view-logs/` | 获取查看日志 |

---

## 1. 创建盘点分配

### POST /api/inventory/tasks/{id}/create-assignments/

创建盘点分配

**请求体：**

```json
{
  "assignments": [
    {
      "executor_id": "user-uuid",
      "mode": "region",
      "scope_config": {
        "location_ids": [1, 2, 3]
      },
      "instruction": "请盘点A区资产"
    },
    {
      "executor_id": "user-uuid-2",
      "mode": "category",
      "scope_config": {
        "category_ids": [10, 11]
      },
      "instruction": "请盘点IT设备"
    }
  ],
  "clear_existing": true
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "盘点分配创建成功",
  "data": [
    {
      "id": "assignment-uuid",
      "task_id": "task-uuid",
      "executor_id": "user-uuid",
      "executor_name": "张三",
      "mode": "region",
      "scope_config": {"location_ids": [1, 2, 3]},
      "total_assigned": 50,
      "completed_count": 0,
      "status": "pending",
      "assigned_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

## 2. 使用模板自动分配

### POST /api/inventory/tasks/{id}/auto-assign-template/

使用模板自动分配

**请求体：**

```json
{
  "template_id": "template-uuid"
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "模板分配成功",
  "data": [
    {
      "id": "assignment-uuid",
      "executor_id": "user-uuid",
      "executor_name": "张三",
      "mode": "custodian",
      "total_assigned": 30,
      "status": "pending"
    }
  ]
}
```

---

## 3. 按保管人分配（自盘模式）

### POST /api/inventory/tasks/{id}/assign-custodian/

按保管人分配，每个人盘点自己名下的资产

**请求体：** 无

**响应数据：**

```json
{
  "success": true,
  "message": "保管人分配成功",
  "data": [
    {
      "id": "assignment-uuid",
      "executor_id": "user-uuid",
      "executor_name": "张三",
      "mode": "custodian",
      "total_assigned": 10,
      "status": "pending",
      "instruction": "请盘点您名下的资产"
    }
  ]
}
```

---

## 4. 随机盲抽分配

### POST /api/inventory/tasks/{id}/assign-random/

随机盲抽分配

**请求体：**

```json
{
  "executor_ids": ["user-1", "user-2", "user-3"],
  "distribute_type": "even",
  "per_executor": null
}
```

或指定每人数量：

```json
{
  "executor_ids": ["user-1", "user-2"],
  "distribute_type": "fixed",
  "per_executor": 50
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "随机分配成功",
  "data": [
    {
      "id": "assignment-uuid",
      "executor_id": "user-1",
      "mode": "random",
      "total_assigned": 50,
      "status": "pending"
    }
  ]
}
```

---

## 5. 获取任务进度统计

### GET /api/inventory/tasks/{id}/progress/

获取任务进度统计

**响应数据：**

```json
{
  "success": true,
  "message": "获取任务进度统计成功",
  "data": {
    "overall": {
      "total": 500,
      "scanned": 350,
      "normal": 320,
      "extra": 5,
      "missing": 25,
      "damaged": 5,
      "progress": 70
    },
    "assignments": [
      {
        "id": "assignment-uuid",
        "executor_id": "user-uuid",
        "executor_name": "张三",
        "executor_avatar": "http://...",
        "mode": "region",
        "mode_display": "区域分配",
        "total_assigned": 100,
        "completed_count": 80,
        "missing_count": 10,
        "extra_count": 0,
        "status": "in_progress",
        "status_display": "执行中",
        "progress": 80,
        "deadline_at": "2024-01-20T18:00:00Z"
      }
    ],
    "stats_by_mode": [
      {
        "mode": "custodian",
        "mode_display": "保管人分配",
        "count": 5,
        "total_assigned": 150,
        "completed": 120
      }
    ]
  }
}
```

---

## 6. 催办执行人

### POST /api/inventory/assignments/{id}/remind/

催办执行人

**请求体：** 无

**响应数据：**

```json
{
  "success": true,
  "message": "催办通知已发送",
  "data": {
    "assignment_id": "assignment-uuid",
    "reminded_at": "2024-01-15T10:00:00Z"
  }
}
```

---

## 7. 获取我的盘点任务（用户端）

### GET /api/inventory/my/tasks/

获取我的盘点任务

**请求参数：**

```json
{
  "status": "pending"  // 可选: pending/in_progress/completed
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "获取我的盘点任务成功",
  "data": [
    {
      "id": "assignment-uuid",
      "task_code": "PD2024001",
      "task_name": "1月全盘点",
      "mode": "custodian",
      "mode_display": "保管人分配",
      "total_assigned": 10,
      "completed_count": 3,
      "missing_count": 0,
      "extra_count": 0,
      "status": "in_progress",
      "status_display": "执行中",
      "progress": 30,
      "deadline_at": "2024-01-20T18:00:00Z",
      "is_overdue": false,
      "instruction": "请盘点您名下的资产"
    }
  ]
}
```

---

## 8. 获取今日任务汇总

### GET /api/inventory/my/today/

获取今日盘点任务汇总

**响应数据：**

```json
{
  "success": true,
  "message": "获取今日任务汇总成功",
  "data": {
    "total_count": 3,
    "total_assets": 50,
    "completed_assets": 15,
    "assignments": [
      {
        "task_code": "PD2024001",
        "task_name": "1月全盘点",
        "assignment_id": "assignment-uuid",
        "total": 30,
        "completed": 10,
        "progress": 33,
        "deadline": "2024-01-20T18:00:00Z"
      }
    ]
  }
}
```

---

## 9. 获取待盘点资产

### GET /api/inventory/my/pending-assets/

获取待盘点资产

**请求参数：**

```json
{
  "assignment_id": "assignment-uuid"
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "获取待盘点资产成功",
  "data": [
    {
      "snapshot_id": "snapshot-uuid",
      "asset_id": "asset-uuid",
      "asset_code": "ZC001",
      "asset_name": "笔记本电脑",
      "location": "301室",
      "custodian": "张三",
      "expected_status": "in_use"
    }
  ]
}
```

---

## 10. 记录扫描结果

### POST /api/inventory/my/record-scan/

记录扫描结果

**请求体：**

```json
{
  "task_id": "task-uuid",
  "assignment_id": "assignment-uuid",
  "asset_id": "asset-uuid",
  "scan_method": "qr",
  "status": "normal",
  "actual_location": "",
  "remark": ""
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "扫描记录成功",
  "data": {
    "id": "scan-uuid",
    "scan_time": "2024-01-15T10:30:00Z"
  }
}
```

---

## 11. 分配模板

### POST /api/inventory/assignment-templates/

创建分配模板

**请求体：**

```json
{
  "template_name": "IT部门自盘模板",
  "rules": [
    {
      "mode": "category",
      "condition": {"category_ids": [10, 11, 12]},
      "executor_type": "department",
      "executor_value": "dept-it"
    }
  ],
  "default_instruction": "请按规范完成盘点"
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "模板创建成功",
  "data": {
    "id": "template-uuid",
    "template_name": "IT部门自盘模板",
    "rules": [...],
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

---

## 12. 获取查看配置

### GET /api/inventory/tasks/{id}/view-config/

获取盘点任务的查看配置

**响应数据：**

```json
{
  "success": true,
  "message": "获取查看配置成功",
  "data": {
    "id": "config-uuid",
    "allow_department_leader": true,
    "department_leader_scope": "department_assets",
    "allow_asset_admin": false,
    "remark": ""
  }
}
```

### PUT /api/inventory/tasks/{id}/view-config/

更新查看配置

**请求体：**

```json
{
  "allow_department_leader": true,
  "department_leader_scope": "department_assets",
  "allow_asset_admin": false,
  "remark": "备注说明"
}
```

**响应数据：**
```json
{
  "success": true,
  "message": "更新查看配置成功",
  "data": {
    "id": "config-uuid",
    "allow_department_leader": true,
    "department_leader_scope": "department_assets",
    "allow_asset_admin": false,
    "remark": "备注说明"
  }
}
```

---

## 13. 查看者管理

### GET /api/inventory/tasks/{id}/viewers/

获取查看者列表

**请求参数：**

```json
{
  "source": "department_leader"  // 可选: manual/department_leader/role
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "获取查看者列表成功",
  "data": [
    {
      "id": "viewer-uuid",
      "viewer_id": "user-uuid",
      "viewer_name": "张三",
      "viewer_avatar": "http://...",
      "source": "manual",
      "source_display": "手动指定",
      "scope": "all",
      "scope_display": "全部资产",
      "remark": "财务总监"
    }
  ]
}
```

### POST /api/inventory/tasks/{id}/viewers/

添加查看者

**请求体：**

```json
{
  "viewer_ids": ["user-1", "user-2"],
  "scope": "all",
  "scope_config": {},
  "remark": "说明"
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "查看者添加成功",
  "data": [
    {
      "id": "viewer-uuid",
      "viewer_id": "user-1",
      "viewer_name": "张三",
      "source": "manual",
      "scope": "all"
    }
  ]
}
```

### DELETE /api/inventory/tasks/{id}/viewers/

移除查看者

**请求体：**

```json
{
  "viewer_ids": ["user-1", "user-2"]
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "查看者移除成功",
  "data": {
    "deleted_count": 2
  }
}
```

---

## 14. 获取我的查看权限

### GET /api/inventory/tasks/{id}/my-permission/

获取当前用户对任务的查看权限

**响应数据：**

```json
{
  "success": true,
  "message": "获取我的查看权限成功",
  "data": {
    "can_view": true,
    "permission_source": "部门负责人",
    "viewable_count": 10,
    "total_count": 50,
    "scope": "本部门",
    "config": {
      "allow_department_leader": true,
      "allow_asset_admin": false
    }
  }
}
```

无权限时：

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "无查看权限"
  }
}
```

---

## 15. 获取查看日志

### GET /api/inventory/tasks/{id}/view-logs/

获取任务的查看日志

**请求参数：**

```json
{
  "viewer_id": "user-uuid",  // 可选
  "page": 1,
  "size": 20
}
```

**响应数据：**

```json
{
  "success": true,
  "message": "获取查看日志成功",
  "data": {
    "count": 100,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "log-uuid",
        "viewer_name": "张三",
        "view_method": "web",
        "view_method_display": "网页",
        "viewed_at": "2024-01-15T10:30:00Z",
        "ip_address": "192.168.1.100"
      }
    ]
  }
}
```

---

## Serializers

```python
# apps/inventory/serializers/assignment.py

from rest_framework import serializers
from apps.inventory.models import (
    InventoryAssignment, InventoryAssignmentTemplate
)


class InventoryAssignmentSerializer(serializers.ModelSerializer):
    """盘点分配序列化器"""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    executor_name = serializers.CharField(source='executor.real_name', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.IntegerField(read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = InventoryAssignment
        fields = [
            'id', 'task', 'task_code', 'task_name',
            'executor', 'executor_name',
            'mode', 'mode_display',
            'scope_config',
            'total_assigned', 'completed_count',
            'missing_count', 'extra_count',
            'status', 'status_display',
            'progress', 'is_overdue',
            'assigned_at', 'started_at', 'completed_at', 'deadline_at',
            'instruction'
        ]

    def get_is_overdue(self, obj):
        if obj.deadline_at and obj.status in ['pending', 'in_progress']:
            from django.utils import timezone
            return timezone.now() > obj.deadline_at
        return False


class MyAssignmentSerializer(serializers.ModelSerializer):
    """用户端我的任务序列化器"""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    progress = serializers.IntegerField(read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = InventoryAssignment
        fields = [
            'id', 'task_code', 'task_name',
            'mode', 'mode_display',
            'total_assigned', 'completed_count',
            'status', 'status_display',
            'progress', 'is_overdue',
            'deadline_at', 'instruction'
        ]

    def get_is_overdue(self, obj):
        if obj.deadline_at and obj.status in ['pending', 'in_progress']:
            from django.utils import timezone
            return timezone.now() > obj.deadline_at
        return False


class InventoryAssignmentTemplateSerializer(serializers.ModelSerializer):
    """分配模板序列化器"""

    class Meta:
        model = InventoryAssignmentTemplate
        fields = '__all__'


class InventoryTaskViewerSerializer(serializers.ModelSerializer):
    """查看者序列化器"""
    viewer_name = serializers.CharField(source='viewer.real_name', read_only=True)
    viewer_avatar = serializers.ImageField(source='viewer.avatar', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)

    class Meta:
        model = InventoryTaskViewer
        fields = [
            'id', 'viewer', 'viewer_id', 'viewer_name', 'viewer_avatar',
            'source', 'source_display', 'scope', 'scope_display',
            'scope_config', 'remark'
        ]


class InventoryTaskViewConfigSerializer(serializers.ModelSerializer):
    """查看配置序列化器"""
    department_leader_scope_display = serializers.CharField(
        source='get_department_leader_scope_display', read_only=True
    )

    class Meta:
        model = InventoryTaskViewConfig
        fields = [
            'id', 'allow_department_leader', 'department_leader_scope',
            'department_leader_scope_display', 'allow_asset_admin', 'remark'
        ]


class InventoryViewLogSerializer(serializers.ModelSerializer):
    """查看日志序列化器"""
    viewer_name = serializers.CharField(source='viewer.real_name', read_only=True)
    view_method_display = serializers.CharField(source='get_view_method_display', read_only=True)
    viewed_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = InventoryViewLog
        fields = [
            'id', 'viewer_name', 'view_method', 'view_method_display',
            'viewed_at', 'ip_address'
        ]
```

---

## 后续任务

所有Phase已完成！
