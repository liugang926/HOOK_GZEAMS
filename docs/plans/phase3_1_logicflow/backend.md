# Phase 3.1: LogicFlow 可视化流程设计 - Backend 实现文档

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
        "name": "采购审批流程",
        "definition": {...},
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
        "next": "https://api.example.com/api/process-definitions/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "采购审批流程",
                ...
            }
        ]
    }
}
```

#### 创建/更新响应

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "采购审批流程",
        "definition": {...},
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...}
    }
}
```

#### 删除响应

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
            "name": ["流程名称不能为空"],
            "definition": ["流程定义格式错误"]
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
        "name": "采购审批流程",
        "code": "PROCUREMENT_APPROVAL",
        "definition": {
            "nodes": [...],
            "edges": [...],
            "grid": {...},
            "properties": {...}
        },
        "status": "published",
        "version": "1.0",
        "organization": {...},
        "created_at": "2026-01-14T10:30:00Z",
        "created_by": {...},
        "updated_at": "2026-01-14T10:30:00Z"
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
        "next": "https://api.example.com/api/process-definitions/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "采购审批流程",
                "code": "PROCUREMENT_APPROVAL",
                "status": "published",
                "version": "1.0",
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
        "name": "采购审批流程",
        "code": "PROCUREMENT_APPROVAL",
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
            "name": ["流程名称不能为空"],
            "definition": ["流程定义格式错误"],
            "definition.nodes": ["节点ID不能重复"],
            "definition.edges": ["边的源节点和目标节点不能相同"]
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

#### LogicFlow特有错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `INVALID_FLOW_DEFINITION` | 400 | 流程定义格式错误 |
| `DUPLICATE_FLOW_CODE` | 409 | 流程编码重复 |
| `INVALID_NODE_TYPE` | 400 | 节点类型不支持 |
| `INVALID_NODE_CONNECTION` | 400 | 节点连接关系错误 |
| `FLOW_ALREADY_PUBLISHED` | 409 | 流程已发布，无法修改 |
| `FLOW_NOT_PUBLISHED` | 400 | 流程未发布，无法执行 |

### 批量操作 API 规范

#### 批量删除

```http
POST /api/process-definitions/batch-delete/
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
            "error": "流程定义不存在"
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
POST /api/process-definitions/batch-restore/
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
POST /api/process-definitions/batch-update/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "status": "archived"
    }
}
```

**响应格式与批量删除相同**

### 标准 CRUD API

#### 流程定义管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/` | 分页查询流程定义 |
| GET | `/api/process-definitions/{id}/` | 获取单个流程定义详情 |
| POST | `/api/process-definitions/` | 创建新的流程定义 |
| PUT | `/api/process-definitions/{id}/` | 完整更新流程定义 |
| PATCH | `/api/process-definitions/{id}/` | 部分更新流程定义 |
| DELETE | `/api/process-definitions/{id}/` | 软删除流程定义 |
| GET | `/api/process-definitions/deleted/` | 查询已删除的流程定义 |
| POST | `/api/process-definitions/{id}/restore/` | 恢复单个已删除的流程定义 |

#### 流程版本管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/{id}/versions/` | 获取流程定义所有版本 |
| POST | `/api/process-definitions/{id}/duplicate/` | 复制流程定义为新版本 |
| PUT | `/api/process-definitions/{id}/publish/` | 发布流程定义版本 |

#### 流程模板管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/templates/` | 分页查询流程模板 |
| POST | `/api/process-definitions/templates/` | 创建流程模板 |
| GET | `/api/process-definitions/templates/{id}/` | 获取流程模板详情 |
| PUT | `/api/process-definitions/templates/{id}/` | 更新流程模板 |
| DELETE | `/api/process-definitions/templates/{id}/` | 删除流程模板 |
| POST | `/api/process-definitions/templates/{id}/apply/` | 应用模板创建流程定义 |

#### 扩展操作 API

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/{id}/history/` | 获取流程定义变更历史 |
| GET | `/api/process-definitions/{id}/validate/` | 验证流程定义语法 |
| POST | `/api/process-definitions/{id}/deploy/` | 部署流程定义 |
| POST | `/api/process-definitions/{id}/undeploy/` | 取消部署流程定义 |
| GET | `/api/process-definitions/search/` | 高级搜索流程定义 |
| GET | `/api/process-definitions/categories/` | 获取流程分类列表 |

### 流程设计器 API

#### 节点类型管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/nodes/types/` | 获取所有支持的节点类型 |
| GET | `/api/process-definitions/nodes/types/{type}/config/` | 获取节点类型的配置模板 |
| GET | `/api/process-definitions/nodes/default-config/` | 获取节点默认配置 |

#### 连线规则管理

| HTTP 方法 | 端点 | 说明 |
|-----------|------|------|
| GET | `/api/process-definitions/rules/connections/` | 获取节点连接规则 |
| GET | `/api/process-definitions/rules/validations/` | 获取流程验证规则 |
| POST | `/api/process-definitions/rules/validate-connection/` | 验证节点连接是否合法 |

### 数据导入导出 API

#### 流程定义导出

```http
POST /api/process-definitions/export/
Content-Type: application/json

{
    "format": "json",
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "options": {
        "include_versions": true,
        "include_history": false
    }
}
```

**响应**：

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Disposition: attachment; filename="process_definitions_export_20260115.json"

{
    "definitions": [...],
    "metadata": {
        "export_time": "2026-01-15T10:30:00Z",
        "version": "1.0"
    }
}
```

#### 流程定义导入

```http
POST /api/process-definitions/import/
Content-Type: application/json

{
    "file_content": {...},
    "options": {
        "skip_errors": true,
        "update_existing": false,
        "auto_assign_code": true
    }
}
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "message": "导入任务已创建",
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "processing",
        "estimated_time": 30
    }
}
```

#### 查询导入状态

```http
GET /api/process-definitions/import/{task_id}/status/
```

**响应**：

```http
HTTP/1.1 200 OK

{
    "success": true,
    "data": {
        "task_id": "import-task-uuid-xxx",
        "status": "completed",
        "progress": 100,
        "summary": {
            "total": 5,
            "succeeded": 4,
            "failed": 1,
            "skipped": 0
        },
        "errors": [
            {
                "definition_name": "测试流程",
                "error": "流程编码重复",
                "details": "流程编码 TEST001 已存在"
            }
        ]
    }
}
```

---

## 代码实现示例

### 流程定义序列化器

```python
# backend/apps/workflows/serializers.py

from rest_framework import serializers
from apps.workflows.models import FlowDefinition
from apps.common.serializers.base import BaseModelSerializer


class FlowDefinitionSerializer(BaseModelSerializer):
    """流程定义序列化器"""

    definition = serializers.JSONField()
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta(BaseModelSerializer.Meta):
        model = FlowDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'definition', 'description',
            'status', 'version', 'tags', 'category'
        ]

    def validate_definition(self, value):
        """验证流程定义"""
        validator = FlowDefinitionValidator()
        is_valid, errors = validator.validate_definition(value)

        if not is_valid:
            raise serializers.ValidationError({
                'definition': errors
            })

        return value

    def create(self, validated_data):
        """创建流程定义，自动生成编码"""
        if 'code' not in validated_data:
            generator = FlowCodeGenerator()
            validated_data['code'] = generator.generate_code(
                validated_data['name'],
                validated_data['organization'].code
            )

        return super().create(validated_data)


class FlowDefinitionDetailSerializer(FlowDefinitionSerializer):
    """流程定义详情序列化器"""

    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta(FlowDefinitionSerializer.Meta):
        fields = FlowDefinitionSerializer.Meta.fields + [
            'created_by_name', 'updated_by_name'
        ]
```

### 流程定义视图集

```python
# backend/apps/workflows/viewsets.py

from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.workflows.models import FlowDefinition
from apps.workflows.serializers import (
    FlowDefinitionSerializer,
    FlowDefinitionDetailSerializer
)
from apps.workflows.services.flow_validation import FlowDefinitionValidator


class FlowDefinitionViewSet(BaseModelViewSetWithBatch):
    """流程定义视图集"""

    queryset = FlowDefinition.objects.filter(is_deleted=False)
    serializer_class = FlowDefinitionSerializer
    filterset_fields = ['status', 'category', 'created_by']
    search_fields = ['name', 'code', 'description']

    def get_serializer_class(self):
        """获取序列化器类"""
        if self.action == 'retrieve':
            return FlowDefinitionDetailSerializer
        return FlowDefinitionSerializer

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """验证流程定义"""
        flow_definition = self.get_object()

        try:
            validator = FlowDefinitionValidator()
            definition = flow_definition.definition

            is_valid, errors = validator.validate_definition(definition)

            if is_valid:
                return Response({
                    'success': True,
                    'message': '流程定义验证通过'
                })
            else:
                return Response({
                    'success': False,
                    'message': '流程定义验证失败',
                    'errors': errors
                }, status=400)

        except Exception as e:
            return Response({
                'success': False,
                'message': '验证过程中发生错误',
                'error': str(e)
            }, status=500)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布流程定义"""
        flow_definition = self.get_object()

        if flow_definition.status == 'published':
            return Response({
                'success': False,
                'message': '流程已经发布'
            }, status=400)

        # 更新状态
        flow_definition.status = 'published'
        flow_definition.published_at = timezone.now()
        flow_definition.published_by = request.user
        flow_definition.save()

        return Response({
            'success': True,
            'message': '流程发布成功'
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """复制流程定义"""
        flow_definition = self.get_object()

        # 创建新版本
        new_definition = FlowDefinition.objects.create(
            name=f"{flow_definition.name} (副本)",
            code=flow_definition.code,  # 临时编码，会在保存时重新生成
            definition=flow_definition.definition,
            description=flow_definition.description,
            status='draft',
            version=flow_definition.version,
            created_by=request.user,
            organization=flow_definition.organization
        )

        return Response({
            'success': True,
            'message': '流程复制成功',
            'data': FlowDefinitionSerializer(new_definition).data
        })

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取流程分类列表"""
        categories = self.queryset.values_list('category', flat=True).distinct()

        return Response({
            'success': True,
            'data': {
                'categories': list(categories)
            }
        })
```

### 导入导出服务

```python
# backend/apps/workflows/services/import_export.py

import json
import uuid
from datetime import datetime
from django.core.files.base import ContentFile
from django.db import transaction
from apps.workflows.models import FlowDefinition, FlowTemplate
from apps.common.services.base_crud import BaseCRUDService


class FlowImportExportService(BaseCRUDService):
    """流程导入导出服务"""

    def __init__(self):
        super().__init__(FlowDefinition)

    def export_definitions(self, definition_ids=None, include_versions=False, include_history=False):
        """导出流程定义"""
        definitions = []

        if definition_ids:
            definitions = self.model_class.objects.filter(
                id__in=definition_ids,
                is_deleted=False
            )
        else:
            definitions = self.model_class.objects.filter(
                is_deleted=False
            ).order_by('created_at')

        export_data = {
            'definitions': [],
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'version': '1.0',
                'total_definitions': len(definitions),
                'include_versions': include_versions,
                'include_history': include_history
            }
        }

        for definition in definitions:
            definition_data = {
                'id': str(definition.id),
                'name': definition.name,
                'code': definition.code,
                'definition': definition.definition,
                'description': definition.description,
                'status': definition.status,
                'version': definition.version,
                'category': definition.category,
                'tags': definition.tags,
                'organization': {
                    'id': str(definition.organization.id),
                    'name': definition.organization.name,
                    'code': definition.organization.code
                },
                'created_at': definition.created_at.isoformat(),
                'created_by': {
                    'id': str(definition.created_by.id),
                    'username': definition.created_by.username,
                    'name': definition.created_by.get_full_name()
                }
            }

            if include_versions:
                # 包含历史版本
                versions = self.model_class.objects.filter(
                    code=definition.code,
                    is_deleted=False
                ).order_by('-version')

                definition_data['versions'] = [
                    {
                        'version': v.version,
                        'definition': v.definition,
                        'status': v.status,
                        'created_at': v.created_at.isoformat()
                    } for v in versions
                ]

            export_data['definitions'].append(definition_data)

        return export_data

    def import_definitions(self, import_data, skip_errors=True, update_existing=False, auto_assign_code=False):
        """导入流程定义"""
        results = {
            'summary': {
                'total': len(import_data['definitions']),
                'succeeded': 0,
                'failed': 0,
                'skipped': 0
            },
            'results': [],
            'errors': []
        }

        with transaction.atomic():
            for definition_data in import_data['definitions']:
                try:
                    # 检查编码是否重复
                    existing = self.model_class.objects.filter(
                        code=definition_data['code'],
                        is_deleted=False
                    ).first()

                    if existing and not update_existing:
                        results['skipped'] += 1
                        results['results'].append({
                            'definition_code': definition_data['code'],
                            'success': False,
                            'message': '流程编码已存在且不允许更新'
                        })
                        continue

                    # 处理导入
                    if existing and update_existing:
                        # 更新现有定义
                        existing.name = definition_data['name']
                        existing.definition = definition_data['definition']
                        existing.description = definition_data['description']
                        existing.status = definition_data['status']
                        existing.version = definition_data['version']
                        existing.updated_by = import_user
                        existing.save()

                        results['succeeded'] += 1
                        results['results'].append({
                            'definition_code': definition_data['code'],
                            'success': True,
                            'message': '流程定义更新成功',
                            'definition_id': str(existing.id)
                        })
                    else:
                        # 创建新定义
                        definition = self.model_class.objects.create(
                            code=definition_data['code'],
                            name=definition_data['name'],
                            definition=definition_data['definition'],
                            description=definition_data['description'],
                            status=definition_data['status'],
                            version=definition_data['version'],
                            category=definition_data.get('category'),
                            tags=definition_data.get('tags', []),
                            created_by=import_user,
                            organization=import_user.org
                        )

                        results['succeeded'] += 1
                        results['results'].append({
                            'definition_code': definition_data['code'],
                            'success': True,
                            'message': '流程定义导入成功',
                            'definition_id': str(definition.id)
                        })

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'definition_code': definition_data.get('code', 'unknown'),
                        'error': str(e)
                    })

                    if not skip_errors:
                        raise

        return results
```

---

## 监控和日志

### 流程监控指标

```python
# backend/apps/workflows/monitoring/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# 流程定义统计
FLOW_DEFINITIONS = Gauge(
    'workflow_definitions_total',
    'Total workflow definitions',
    ['status', 'category']
)

FLOW_OPERATIONS = Counter(
    'workflow_operations_total',
    'Total workflow operations',
    ['operation', 'status']
)

FLOW_VALIDATION_DURATION = Histogram(
    'workflow_validation_duration_seconds',
    'Workflow validation duration'
)

FLOW_IMPORT_DURATION = Histogram(
    'workflow_import_duration_seconds',
    'Workflow import duration',
    ['size']
)

FLOW_EXPORT_DURATION = Histogram(
    'workflow_export_duration_seconds',
    'Workflow export duration',
    ['format']
)
```

### 操作日志

```python
# backend/apps/workflows/models.py

from django.db import models
from django.contrib.auth import get_user_model
from apps.common.models import BaseModel

User = get_user_model()


class FlowOperationLog(BaseModel):
    """流程操作日志"""

    OPERATION_CHOICES = [
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('publish', '发布'),
        ('unpublish', '取消发布'),
        ('duplicate', '复制'),
        ('import', '导入'),
        ('export', '导出'),
        ('validate', '验证'),
    ]

    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    flow_definition = models.ForeignKey(
        'FlowDefinition',
        on_delete=models.CASCADE,
        related_name='operation_logs'
    )
    details = models.JSONField(default=dict, help_text="操作详情")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'workflow_operation_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['operation', 'created_at']),
            models.Index(fields=['flow_definition', 'created_at']),
        ]
```

---

## 总结

### 架构特点

1. **可视化流程设计**：基于LogicFlow的拖拽式流程设计器
2. **标准化流程定义**：支持BPMN 2.0标准，兼容主流流程引擎
3. **版本管理**：完整的流程版本控制，支持历史回滚
4. **模板复用**：流程模板系统，提高流程设计效率
5. **导入导出**：标准化流程定义的导入导出功能
6. **验证机制**：严格的流程定义验证，确保流程正确性

### 技术亮点

1. **流程验证引擎**：完整的语法和语义验证
2. **自动编码生成**：基于业务规则的流程编码自动生成
3. **批量操作支持**：高效的流程批量导入导出
4. **实时验证**：设计过程中的实时验证反馈
5. **性能优化**：针对大规模流程定义的性能优化

### 集成建议

1. **前端集成**：LogicFlow可视化设计器集成
2. **版本控制系统**：与Git或其他版本系统集成
3. **流程引擎**：支持与Camunda、Activiti等流程引擎集成
4. **监控告警**：流程定义变更监控和异常告警
5. **权限管理**：细粒度的流程设计权限控制

### 工作流实例管理 API

#### 流程实例启动

```http
POST /api/workflow/instances/
Content-Type: application/json

{
    "process_definition_id": "550e8400-e29b-41d4-a716-446655440000",
    "business_data": {
        "asset_id": "asset-uuid-123",
        "requester": "user-uuid-456",
        "request_reason": "资产申请"
    },
    "variables": {
        "priority": "high",
        "urgent": false
    }
}
```

#### 查询流程实例

```http
GET /api/workflow/instances/?status=running&process_definition_id=550e8400-e29b-41d4-a716-446655440000
```

#### 查询任务列表

```http
GET /api/workflow/tasks/?assignee=current-user&status=pending
```

#### 完成任务

```http
POST /api/workflow/tasks/{task_id}/complete/
Content-Type: application/json

{
    "variables": {
        "approved": true,
        "comments": "审批通过"
    }
}
```

#### 获取流程历史

```http
GET /api/workflow/instances/{instance_id}/history/
```

### 流程图设计 API

#### 获取流程图设计配置

```http
GET /api/workflow/designer/config/
```

#### 保存流程设计

```http
POST /api/workflow/designer/save/
Content-Type: application/json

{
    "process_id": "550e8400-e29b-41d4-a716-446655440000",
    "flow_data": {
        "nodes": [...],
        "edges": [...],
        "viewport": {...}
    }
}
```

#### 导入/导出流程设计

```http
POST /api/workflow/designer/export/
Content-Type: application/json

{
    "process_ids": ["id1", "id2"],
    "format": "json"
}
```

```http
POST /api/workflow/designer/import/
Content-Type: application/json

{
    "file": "imported-flow.json",
    "overwrite_existing": false
}
```

---
