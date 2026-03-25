# Phase 3.2: 工作流执行引擎 - Backend 实现文档

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

### 统一响应格式

#### 成功响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "process_instance_id": "pi-001",
        "status": "running",
        "current_node": "approve_node",
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

#### 列表响应（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/process-instances/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "process_instance_id": "pi-001",
                "status": "running",
                ...
            }
        ]
    }
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
            "process_definition": ["流程定义不存在"],
            "business_data": ["业务数据格式错误"]
        }
    }
}
```

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
        "process_instance_id": "pi-001",
        "process_definition_id": "550e8400-e29b-41d4-a716-446655440001",
        "business_key": "ORDER-2026001",
        "status": "running",
        "current_node": "approve_node",
        "current_task_id": "task-001",
        "variables": {
            "amount": 1000.00,
            "priority": "high"
        },
        "organization": {...},
        "started_at": "2026-01-14T10:30:00Z",
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
        "next": "https://api.example.com/api/process-instances/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "process_instance_id": "pi-001",
                "business_key": "ORDER-2026001",
                "status": "running",
                "current_node": "approve_node",
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
        "process_instance_id": "pi-001",
        "status": "started",
        "current_node": "start_node",
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
            "process_definition": ["流程定义不存在"],
            "business_data": ["业务数据格式错误"],
            "variables": ["变量必须是JSON格式"]
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

#### 工作流引擎特有错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `PROCESS_DEFINITION_NOT_FOUND` | 404 | 流程定义不存在 |
| `PROCESS_INSTANCE_NOT_FOUND` | 404 | 流程实例不存在 |
| `INVALID_PROCESS_STATUS` | 400 | 无效的流程状态 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 |
| `INVALID_TASK_STATUS` | 400 | 无效的任务状态 |
| `INVALID_TRANSITION` | 400 | 无效的状态转换 |
| `VARIABLE_UPDATE_FAILED` | 400 | 变量更新失败 |
| `PROCESS_TERMINATED` | 400 | 流程已终止 |
| `PROCESS_COMPLETED` | 400 | 流程已完成 |
| `NO_ACTIVE_NODE` | 400 | 当前没有活跃节点 |

---

## API接口规范

### 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

### 标准 CRUD API

#### 流程实例管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-instances/` | 分页查询流程实例 |
| GET | `/api/process-instances/{id}/` | 获取单个流程实例详情 |
| POST | `/api/process-instances/` | 创建新的流程实例 |
| PUT | `/api/process-instances/{id}/` | 完整更新流程实例 |
| PATCH | `/api/process-instances/{id}/` | 部分更新流程实例 |
| DELETE | `/api/process-instances/{id}/` | 软删除流程实例 |
| GET | `/api/process-instances/deleted/` | 查询已删除的流程实例 |
| POST | `/api/process-instances/{id}/restore/` | 恢复单个已删除的流程实例 |

#### 流程实例生命周期管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| POST | `/api/process-instances/{id}/start/` | 启动流程实例 |
| POST | `/api/process-instances/{id}/pause/` | 暂停流程实例 |
| POST | `/api/process-instances/{id}/resume/` | 恢复流程实例 |
| POST | `/api/process-instances/{id}/complete/` | 完成流程实例 |
| POST | `/api/process-instances/{id}/terminate/` | 终止流程实例 |
| POST | `/api/process-instances/{id}/cancel/` | 取消流程实例 |

#### 变量管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-instances/{id}/variables/` | 获取流程实例变量 |
| POST | `/api/process-instances/{id}/variables/` | 设置流程变量 |
| PUT | `/api/process-instances/{id}/variables/` | 批量更新流程变量 |
| DELETE | `/api/process-instances/{id}/variables/{key}/` | 删除流程变量 |

#### 扩展操作 API

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-instances/{id}/history/` | 获取流程实例变更历史 |
| GET | `/api/process-instances/{id}/diagram/` | 获取流程实例当前进度图 |
| GET | `/api/process-instances/{id}/statistics/` | 获取流程实例统计信息 |
| GET | `/api/process-instances/search/` | 高级搜索流程实例 |
| POST | `/api/process-instances/{id}/reassign/` | 重新分配当前任务 |

### 任务管理 API

#### 任务查询

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/tasks/` | 分页查询任务列表 |
| GET | `/api/tasks/{id}/` | 获取单个任务详情 |
| POST | `/api/tasks/claim/` | 认领任务 |
| POST | `/api/tasks/{id}/complete/` | 完成任务 |
| POST | `/api/tasks/{id}/reject/` | 驳回任务 |
| POST | `/api/tasks/{id}/delegate/` | 委派任务 |

#### 批量任务操作

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/tasks/pending/` | 查询待处理任务 |
| GET | `/api/tasks/assigned/` | 查询已分配任务 |
| GET | `/api/tasks/completed/` | 查询已完成任务 |
| POST | `/api/tasks/batch-complete/` | 批量完成任务 |

### 监控统计 API

#### 流程统计

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/statistics/processes/` | 流程运行统计 |
| GET | `/api/statistics/processes/{definition_id}/` | 特定流程定义的统计 |
| GET | `/api/statistics/tasks/` | 任务处理统计 |
| GET | `/api/statistics/efficiency/` | 流程效率分析 |

#### 历史记录查询

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/history/processes/` | 查询流程历史 |
| GET | `/api/history/processes/{id}/` | 查询流程历史详情 |
| GET | `/api/history/tasks/` | 查询任务历史 |

---

## 代码实现示例

### 流程实例序列化器

```python
# backend/apps/workflows/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.workflows.models import ProcessInstance, Task


class ProcessInstanceSerializer(BaseModelSerializer):
    """流程实例序列化器"""

    business_key = serializers.CharField(required=False, allow_blank=True)
    variables = serializers.JSONField(required=False)
    process_definition_id = serializers.UUIDField()

    class Meta(BaseModelSerializer.Meta):
        model = ProcessInstance
        fields = BaseModelSerializer.Meta.fields + [
            'process_definition_id', 'business_key', 'variables',
            'status', 'current_node', 'current_task_id'
        ]

    def create(self, validated_data):
        """创建流程实例"""
        import uuid
        from apps.workflows.services.process_service import ProcessService

        # 提取流程定义ID
        process_definition_id = validated_data.pop('process_definition_id')
        variables = validated_data.pop('variables', {})

        # 生成业务键
        business_key = validated_data.get('business_key', f"PI-{uuid.uuid4().hex[:8]}")

        # 启动流程
        service = ProcessService()
        result = service.start_process(
            process_definition_id=process_definition_id,
            business_key=business_key,
            variables=variables,
            user=self.context['request'].user
        )

        if not result['success']:
            raise serializers.ValidationError(result['error'])

        # 返回创建的实例
        instance = result['data']
        validated_data['id'] = instance.id
        validated_data['process_instance_id'] = instance.process_instance_id
        validated_data['status'] = instance.status

        return super().create(validated_data)


class TaskSerializer(BaseModelSerializer):
    """任务序列化器"""

    process_instance_id = serializers.UUIDField(read_only=True)
    assignee = serializers.CharField(source='assignee.username', read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Task
        fields = BaseModelSerializer.Meta.fields + [
            'process_instance_id', 'task_name', 'task_type',
            'assignee', 'created_by', 'due_date', 'priority'
        ]


class TaskCompleteSerializer(serializers.Serializer):
    """任务完成序列化器"""

    variables = serializers.JSONField(required=False)
    comments = serializers.CharField(required=False, allow_blank=True)
    next_assignee = serializers.UUIDField(required=False)
```

### 流程服务类

```python
# backend/apps/workflows/services/process_service.py

import uuid
from datetime import datetime
from django.db import transaction
from apps.common.services.base_crud import BaseCRUDService
from apps.workflows.models import ProcessInstance, Task, ProcessDefinition


class ProcessService(BaseCRUDService):
    """流程服务"""

    def __init__(self):
        super().__init__(ProcessInstance)

    def start_process(self, process_definition_id, business_key=None, variables=None, user=None):
        """启动流程实例"""
        try:
            # 获取流程定义
            from apps.workflows.models import ProcessDefinition
            definition = ProcessDefinition.objects.get(
                id=process_definition_id,
                is_deleted=False,
                status='published'
            )

            # 生成流程实例ID
            process_instance_id = f"PI-{uuid.uuid4().hex[:12]}"

            # 创建流程实例
            with transaction.atomic():
                instance = ProcessInstance.objects.create(
                    process_definition=definition,
                    process_instance_id=process_instance_id,
                    business_key=business_key or f"ORDER-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    status='started',
                    started_by=user,
                    organization=user.org if user else None
                )

                # 设置初始变量
                if variables:
                    instance.variables = variables
                    instance.save()

                # 记录历史
                self._process_history(
                    instance=instance,
                    action='start',
                    node='start_node',
                    old_status=None,
                    new_status='started',
                    user=user
                )

                # 执行流程引擎
                self._execute_engine(instance)

            return {
                'success': True,
                'data': instance,
                'message': '流程启动成功'
            }

        except ProcessDefinition.DoesNotExist:
            return {
                'success': False,
                'error': '流程定义不存在或未发布',
                'code': 'PROCESS_DEFINITION_NOT_FOUND'
            }

    def complete_task(self, task_id, variables=None, comments=None, user=None):
        """完成任务"""
        try:
            # 获取任务
            task = Task.objects.get(id=task_id, is_deleted=False)

            # 验证任务权限
            if task.assignee != user and not user.is_superuser:
                return {
                    'success': False,
                    'error': '无权限处理该任务',
                    'code': 'PERMISSION_DENIED'
                }

            # 获取流程实例
            instance = task.process_instance

            # 更新任务状态
            task.status = 'completed'
            task.completed_at = datetime.now()
            task.completed_by = user
            task.comments = comments
            task.save()

            # 设置变量
            if variables:
                instance.variables.update(variables)
                instance.save()

            # 执行流程引擎
            self._execute_engine(instance)

            return {
                'success': True,
                'data': instance,
                'message': '任务完成成功'
            }

        except Task.DoesNotExist:
            return {
                'success': False,
                'error': '任务不存在',
                'code': 'TASK_NOT_FOUND'
            }

    def terminate_process(self, instance_id, reason=None, user=None):
        """终止流程"""
        try:
            instance = self.get(instance_id)

            # 验证流程状态
            if instance.status in ['completed', 'terminated']:
                return {
                    'success': False,
                    'error': '流程已经结束，无法终止',
                    'code': 'INVALID_PROCESS_STATUS'
                }

            # 更新流程状态
            old_status = instance.status
            instance.status = 'terminated'
            instance.terminated_at = datetime.now()
            instance.terminated_by = user
            instance.termination_reason = reason
            instance.save()

            # 记录历史
            self._process_history(
                instance=instance,
                action='terminate',
                node=None,
                old_status=old_status,
                new_status='terminated',
                user=user
            )

            # 终止所有活跃任务
            from apps.workflows.models import Task
            Task.objects.filter(
                process_instance=instance,
                status='pending'
            ).update(
                status='terminated',
                terminated_at=datetime.now(),
                terminated_by=user
            )

            return {
                'success': True,
                'message': '流程终止成功'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'code': 'SERVER_ERROR'
            }

    def get_statistics(self, process_definition_id=None, date_from=None, date_to=None):
        """获取流程统计信息"""
        from django.db.models import Count, Avg
        from django.db.models.functions import TruncDay

        queryset = ProcessInstance.objects.filter(is_deleted=False)

        # 过滤条件
        if process_definition_id:
            queryset = queryset.filter(process_definition_id=process_definition_id)

        if date_from:
            queryset = queryset.filter(started_at__gte=date_from)

        if date_to:
            queryset = queryset.filter(started_at__lte=date_to)

        # 基础统计
        total_count = queryset.count()
        status_counts = queryset.values('status').annotate(count=Count('id'))

        # 按天统计
        daily_stats = queryset.annotate(
            day=TruncDay('started_at')
        ).values('day').annotate(
            count=Count('id'),
            avg_duration=Avg(
                'completed_at' - 'started_at'
            )
        ).order_by('day')

        # 平均处理时间
        completed_instances = queryset.filter(status='completed')
        avg_duration = None
        if completed_instances.exists():
            avg_duration = completed_instances.aggregate(
                avg=Avg('completed_at' - 'started_at')
            )['avg']

        return {
            'total_count': total_count,
            'status_distribution': list(status_counts),
            'daily_statistics': list(daily_stats),
            'average_duration': avg_duration,
            'success_rate': 0 if total_count == 0 else
                (queryset.filter(status='completed').count() / total_count * 100)
        }

    def _execute_engine(self, instance):
        """执行流程引擎"""
        from apps.workflows.engine import WorkflowEngine

        engine = WorkflowEngine()
        engine.execute(instance)

    def _process_history(self, instance, action, node, old_status, new_status, user):
        """记录流程历史"""
        from apps.workflows.models import ProcessHistory

        ProcessHistory.objects.create(
            process_instance=instance,
            action=action,
            node=node,
            old_status=old_status,
            new_status=new_status,
            user=user,
            organization=user.org if user else None
        )
```

---

## 监控和日志

### 流程监控指标

```python
# backend/apps/workflows/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 流程实例统计
PROCESS_INSTANCES = Gauge(
    'process_instances_total',
    'Total process instances',
    ['status', 'definition']
)

PROCESS_OPERATIONS = Counter(
    'process_operations_total',
    'Total process operations',
    ['operation', 'status']
)

PROCESS_DURATION = Histogram(
    'process_duration_seconds',
    'Process execution duration',
    ['definition', 'status']
)

TASK_OPERATIONS = Counter(
    'task_operations_total',
    'Total task operations',
    ['operation', 'status']
)

TASK_DURATION = Histogram(
    'task_duration_seconds',
    'Task processing duration',
    ['type', 'priority']
)
```

### 性能优化

```python
# backend/apps/workflows/migrations/0005_add_indexes_for_performance.py

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0004_alter_processinstance_options_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE INDEX IF NOT EXISTS idx_workflows_processinstance_status
            ON workflows_processinstance (status);

            CREATE INDEX IF NOT EXISTS idx_workflows_processinstance_process_definition
            ON workflows_processinstance (process_definition_id);

            CREATE INDEX IF NOT EXISTS idx_workflows_processinstance_business_key
            ON workflows_processinstance (business_key);

            CREATE INDEX IF NOT EXISTS idx_workflows_processinstance_created_at
            ON workflows_processinstance (created_at DESC);

            CREATE INDEX IF NOT EXISTS idx_workflows_task_assignee
            ON workflows_task (assignee_id);

            CREATE INDEX IF NOT EXISTS idx_workflows_task_status
            ON workflows_task (status);

            CREATE INDEX IF NOT EXISTS idx_workflows_task_process_instance
            ON workflows_task (process_instance_id);
            """
        ),
    ]
```

---

## 总结

### 架构特点

1. **流程引擎集成**：基于LogicFlow的执行引擎，支持复杂的业务流程
2. **任务管理**：完整的任务生命周期管理，支持认领、完成、驳回等操作
3. **变量管理**：流程变量机制，支持动态数据传递
4. **历史记录**：完整的流程执行历史和审计日志
5. **性能优化**：针对大规模流程执行的性能优化
6. **监控统计**：实时监控和统计流程运行状态

### 技术亮点

1. **流程执行引擎**：基于LogicFlow的完整流程执行引擎
2. **异步任务处理**：支持异步任务和回调机制
3. **事务管理**：确保流程执行的数据一致性
4. **状态机管理**：精确的流程状态转换控制
5. **并发控制**：处理流程执行的并发场景

### 集成建议

1. **前端集成**：实时流程状态展示和任务处理界面
2. **消息队列**：集成Celery处理异步任务
3. **缓存优化**：Redis缓存流程定义和实例信息
4. **监控告警**：流程异常和超时监控
5. **权限集成**：与RBAC系统集成控制任务访问权限

---
