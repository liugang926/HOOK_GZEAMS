# 钩子固定资产 (GZEAMS) - 技术架构规范

> **版本**: 1.0.0
> **最后更新**: 2025-01-14
> **状态**: 生产就绪

本文档定义了 GZEAMS 平台的核心技术架构规范，所有开发必须严格遵守。

---

## 目录

1. [架构原则](#1-架构原则)
2. [事件驱动架构](#2-事件驱动架构)
3. [API 标准 (OpenAPI 3.0)](#3-api-标准-openapi-30)
4. [多租户数据隔离](#4-多租户数据隔离)
5. [异步任务架构](#5-异步任务架构)
6. [工作流引擎集成](#6-工作流引擎集成)
7. [前端架构规范](#7-前端架构规范)
8. [安全规范](#8-安全规范)

---

## 1. 架构原则

### 1.1 核心设计原则

| 原则 | 说明 | 强制性 |
|-----|------|-------|
| **业务与流程分离** | 业务代码只管"干活"，流程引擎负责"指挥" | ✅ 强制 |
| **事件驱动解耦** | 业务层 emit 事件，监听器处理副作用 | ✅ 强制 |
| **多租户默认隔离** | 数据访问自动过滤租户，无需手动编写 filter | ✅ 强制 |
| **API 文档即代码** | 使用 drf-spectacular 自动生成 OpenAPI 文档 | ✅ 强制 |
| **异步任务分级** | 关键操作走高优先级队列，耗时操作走低优先级队列 | ✅ 强制 |
| **字段命名统一** | 后端 snake_case，前端 camelCase，自动转换 | ✅ 强制 |

### 1.2 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                        │
│  Vue 3 + Element Plus + LogicFlow (可视化流程设计器)             │
└─────────────────────────────┬───────────────────────────────────┘
                              │ OpenAPI 3.0 (Swagger)
┌─────────────────────────────▼───────────────────────────────────┐
│                         API 网关层 (Gateway)                      │
│  drf-spectacular (自动文档) + Request/Response 拦截器           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                        业务层 (Business)                         │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │ Inventory     │  │ Asset         │  │ Workflow      │       │
│  │ Service       │  │ Service       │  │ Service       │       │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘       │
│          │ emit events      │ emit events          │              │
└──────────┼──────────────────┼──────────────────┼────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│          │     事件总线 (Event Bus) - Django Signals            │
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐      │
│  │ Workflow      │  │ Notification  │  │ Audit         │      │
│  │ Listener      │  │ Listener      │  │ Listener      │      │
│  └───────────────┘  └───────────────┘  └───────────────┘      │
└─────────────────────────────────────────────────────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│          │                  │                      │              │
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐     │
│  │ SpiffWorkflow │  │ Redis Pub/Sub │  │ Celery        │     │
│  │ (BPMN 引擎)   │  │ (消息队列)     │  │ (异步任务)     │     │
│  └───────────────┘  └───────────────┘  └───────┬───────┘     │
│                                                   │            │
│                                        ┌──────────▼────────┐   │
│                                        │  Priority Queues  │   │
│                                        │  High / Low       │   │
│                                        └───────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
           │                  │                      │
┌──────────┼──────────────────┼──────────────────┼────────────────┐
│          │                  │                      │              │
│  ┌───────▼───────┐  ┌──────▼────────┐  ┌──────▼─────────┐     │
│  │ PostgreSQL    │  │ Redis         │  │ MinIO / S3    │     │
│  │ (主数据库)    │  │ (缓存/队列)    │  │ (文件存储)     │     │
│  └───────────────┘  └───────────────┘  └───────────────┘     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          多租户中间件 (TenantMiddleware)               │   │
│  │  自动注入 current_company + Manager 默认过滤             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 事件驱动架构

### 2.1 设计目标

**问题**: 当前设计中，业务服务直接调用工作流引擎，导致耦合过紧。

```python
# ❌ 当前设计 (耦合)
class DifferenceConfirmationService:
    def confirm_difference(self, difference_id, confirmer, data):
        # ... 业务逻辑 ...
        # 直接调用工作流 - 耦合!
        WorkflowService.start_process(context)
        NotificationService.send_feishu(...)
        AuditLogService.log(...)
```

**解决方案**: 引入事件驱动机制，业务层只负责 emit 事件。

```python
# ✅ 改进设计 (解耦)
class DifferenceConfirmationService:
    def confirm_difference(self, difference_id, confirmer, data):
        # ... 业务逻辑 ...
        # 只发出事件，不关心谁监听
        inventory_confirmed.send(
            sender=self.__class__,
            difference_id=difference_id,
            confirmer=confirmer
        )
```

### 2.2 事件定义规范

#### 2.2.1 核心事件清单

| 事件名称 | 发送者 | 触发时机 | 携带数据 |
|---------|-------|---------|---------|
| `inventory_confirmed` | `DifferenceConfirmationService` | 差异认定完成 | `difference_id`, `confirmer`, `resolution_method` |
| `inventory_snapshot_created` | `SnapshotService` | 盘点快照生成 | `task_id`, `asset_count` |
| `workflow_completed` | `WorkflowService` | 工作流审批完成 | `instance_id`, `final_action` |
| `workflow_rejected` | `WorkflowService` | 工作流审批拒绝 | `instance_id`, `reason` |
| `asset_adjusted` | `AssetAdjustmentService` | 资产调账完成 | `adjustment_id`, `asset_id`, `before`, `after` |
| `user_scanned_qr` | `ScanningService` | 用户扫码 | `user_id`, `qr_code`, `location_id` |

#### 2.2.2 事件定义文件

```python
# apps/core/events.py

from django.dispatch import Signal

# ============================================================================
# 盘点模块事件 (Inventory Events)
# ============================================================================

inventory_confirmed = Signal(
    providing_args=['difference_id', 'confirmer', 'resolution_method']
)
"""
差异认定完成事件
Args:
    difference_id: 差异记录ID
    confirmer: 认定人用户对象
    resolution_method: 处理方式
"""

inventory_snapshot_created = Signal(
    providing_args=['task_id', 'asset_count', 'created_by']
)
"""
盘点快照创建完成事件
Args:
    task_id: 盘点任务ID
    asset_count: 资产数量
    created_by: 创建人
"""

inventory_task_completed = Signal(
    providing_args=['task_id', 'scanned_count', 'difference_count']
)
"""
盘点任务完成事件
Args:
    task_id: 任务ID
    scanned_count: 已扫描数量
    difference_count: 差异数量
"""

# ============================================================================
# 工作流事件 (Workflow Events)
# ============================================================================

workflow_completed = Signal(
    providing_args=['instance_id', 'business_object', 'business_id', 'final_action']
)
"""
工作流审批完成事件
Args:
    instance_id: 流程实例ID
    business_object: 业务对象类型
    business_id: 业务数据ID
    final_action: 最终操作 (approved/rejected)
"""

workflow_task_created = Signal(
    providing_args=['instance_id', 'task_id', 'task_name', 'assignees']
)
"""
工作流任务创建事件
Args:
    instance_id: 流程实例ID
    task_id: 任务ID
    task_name: 任务名称
    assignees: 审批人ID列表
"""

# ============================================================================
# 资产模块事件 (Asset Events)
# ============================================================================

asset_adjusted = Signal(
    providing_args=['adjustment_id', 'asset_id', 'adjustment_type', 'before', 'after']
)
"""
资产调账完成事件
Args:
    adjustment_id: 调账记录ID
    asset_id: 资产ID
    adjustment_type: 调账类型
    before: 调账前值
    after: 调账后值
"""

asset_created = Signal(
    providing_args=['asset_id', 'asset_code', 'created_by']
)
"""
资产创建事件
Args:
    asset_id: 资产ID
    asset_code: 资产编码
    created_by: 创建人
"""

# ============================================================================
# 用户操作事件 (User Action Events)
# ============================================================================

user_logged_in = Signal(
    providing_args=['user_id', 'ip_address', 'user_agent']
)
"""
用户登录事件
"""

user_scanned_qr = Signal(
    providing_args=['user_id', 'qr_code', 'location_id', 'scan_time']
)
"""
用户扫码事件
Args:
    user_id: 用户ID
    qr_code: 二维码内容
    location_id: 位置ID
    scan_time: 扫描时间
"""
```

### 2.3 监听器实现规范

#### 2.3.1 监听器文件结构

```
backend/apps/
├── core/
│   ├── events.py          # 事件定义
│   └── listeners/         # 监听器目录
│       ├── __init__.py
│       ├── workflow.py    # 工作流相关监听器
│       ├── notification.py # 通知相关监听器
│       ├── audit.py       # 审计日志监听器
│       └── statistics.py  # 统计相关监听器
```

#### 2.3.2 监听器实现示例

```python
# apps/core/listeners/workflow.py

from django.db import transaction
from apps.core.events import inventory_confirmed
from apps.workflows.services.workflow_adapter import WorkflowService
from apps.workflows.services.workflow_context import WorkflowContext


@receiver(inventory_confirmed)
def start_inventory_approval_workflow(sender, difference_id, confirmer, **kwargs):
    """
    差异认定完成后，自动启动审批工作流
    """
    from apps.inventory.models import InventoryDifference

    difference = InventoryDifference.objects.get(id=difference_id)

    # 构建流程上下文
    context = WorkflowContext(
        definition_code='inventory_difference_approval',
        business_object='inventory_difference',
        business_id=str(difference.id),
        business_no=f"DIFF-{difference.id}",
        variables={
            'difference_type': difference.difference_type,
            'amount': float(difference.account_value or 0),
        },
        initiator_id=str(confirmer.id),
    )

    # 启动工作流
    service = WorkflowService()
    instance = service.start_process(context)

    # 更新差异记录的流程实例ID
    difference.process_instance_id = str(instance.id)
    difference.save()
```

```python
# apps/core/listeners/notification.py

from django.dispatch import receiver
from apps.core.events import workflow_task_created
from apps.notifications.services import FeishuNotificationService


@receiver(workflow_task_created)
def notify_approver_on_task_created(sender, instance_id, task_id, task_name, assignees, **kwargs):
    """
    工作流任务创建时，发送飞书通知给审批人
    """
    for assignee_id in assignees:
        FeishuNotificationService.send_approval_notification(
            user_id=assignee_id,
            task_name=task_name,
            instance_id=instance_id,
        )
```

```python
# apps/core/listeners/audit.py

from django.dispatch import receiver
from apps.core.events import (
    inventory_confirmed,
    asset_adjusted,
    user_scanned_qr,
)
from apps.audit.services import AuditLogService


@receiver(inventory_confirmed)
def log_inventory_confirmation(sender, difference_id, confirmer, **kwargs):
    """记录差异认定审计日志"""
    AuditLogService.log_action(
        action='inventory_confirmed',
        actor=confirmer,
        object_id=difference_id,
        details=kwargs
    )


@receiver(asset_adjusted)
def log_asset_adjustment(sender, adjustment_id, asset_id, **kwargs):
    """记录资产调账审计日志"""
    AuditLogService.log_action(
        action='asset_adjusted',
        object_id=adjustment_id,
        related_object_id=asset_id,
        details=kwargs
    )


@receiver(user_scanned_qr)
def log_qr_scan(sender, user_id, qr_code, **kwargs):
    """记录扫码操作审计日志"""
    AuditLogService.log_action(
        action='qr_scan',
        actor_id=user_id,
        details={'qr_code': qr_code, **kwargs}
    )
```

```python
# apps/core/listeners/statistics.py

from django.dispatch import receiver
from apps.core.events import inventory_task_completed
from apps.statistics.services import RealTimeStatsService


@receiver(inventory_task_completed)
def update_inventory_statistics(sender, task_id, scanned_count, difference_count, **kwargs):
    """盘点任务完成后，更新实时统计数据"""
    RealTimeStatsService.update_task_completion_stats(
        task_id=task_id,
        scanned_count=scanned_count,
        difference_count=difference_count
    )
```

### 2.4 事件总线配置

```python
# backend/settings/events.py

# Django Signals 默认是同步的，对于关键路径上的事件，建议使用异步
from django.dispatch import receiver

# 如果需要异步事件处理，可以使用 django-async-signals
# 或者将监听器逻辑投递到 Celery 任务队列

# 配置示例
ASYNC_SIGNALS = [
    'core.events.workflow_task_created',      # 通知可以异步
    'core.events.inventory_snapshot_created', # 快照后处理可以异步
    'core.events.user_scanned_qr',            # 扫码统计可以异步
]
```

---

## 3. API 标准 (OpenAPI 3.0)

### 3.1 drf-spectacular 配置

#### 3.1.1 安装依赖

```bash
# requirements.txt
drf-spectacular[pydantic]==0.27.0
```

#### 3.1.2 Django REST Framework 配置

```python
# backend/settings/rest_framework.py

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Spectacular 配置
SPECTACULAR_SETTINGS = {
    'TITLE': '钩子固定资产 API',
    'DESCRIPTION': '企业级固定资产低代码管理平台 API 文档',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVE_PUBLIC': True,  # 生产环境建议设为 False，通过 Nginx 提供静态文件
    'SERVERS': [
        {'url': 'http://localhost:8001', 'description': '本地开发环境'},
        {'url': 'https://api.gzeams.com', 'description': '生产环境'},
    ],
    'TAGS': [
        {'name': 'inventory', 'description': '盘点管理'},
        {'name': 'assets', 'description': '资产管理'},
        {'name': 'workflows', 'description': '工作流'},
        {'name': 'organizations', 'description': '组织架构'},
        {'name': 'users', 'description': '用户管理'},
    ],
    'SCHEMA_PATH_PREFIX': '/api',
    'COMPONENT_SPLIT_REQUEST': True,
    'POSTPROCESSING_HOOKS': [
        'apps.openapi.hooks.enum_choices_as_enums',
        'apps.openapi.hooks.remove_summary_response_descriptions',
    ],
}
```

#### 3.1.3 自定义 Schema 扩展

```python
# apps/openapi/hooks.py

from drf_spectacular.plumbing import (
    build_choice_description,
    build_basic_type,
)
from drf_spectacular.utils import extend_schema, OpenApiParameter


def enum_choices_as_enums(result, generator, **kwargs):
    """
    将 Django Model 的 choices 字段转换为 OpenAPI Enum
    """
    pass


def remove_summary_response_descriptions(result, generator, **kwargs):
    """
    移除响应中的冗余描述
    """
    pass
```

### 3.2 API 文档自动生成

#### 3.2.1 URL 配置

```python
# backend/api/urls.py

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # API 文档端点
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

#### 3.2.2 视图 Schema 装饰器

```python
# apps/inventory/views.py

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import serializers


class DifferenceConfirmRequestSerializer(serializers.Serializer):
    """差异认定请求"""
    resolution_method = serializers.ChoiceField(
        choices=['adjustment', 'write_off', 'transfer', 'ignore']
    )
    confirmation_note = serializers.CharField(required=False, allow_blank=True)


class DifferenceConfirmResponseSerializer(serializers.Serializer):
    """差异认定响应"""
    difference_id = serializers.UUIDField()
    status = serializers.CharField()
    process_instance_id = serializers.UUIDField()


@extend_schema(
    tags=['inventory'],
    summary='认定盘点差异',
    description='认定差异并启动审批工作流',
    request=DifferenceConfirmRequestSerializer,
    responses={200: DifferenceConfirmResponseSerializer},
    parameters=[
        OpenApiParameter(
            name='X-Custom-Header',
            type=str,
            location=OpenApiParameter.HEADER,
            description='自定义请求头'
        )
    ]
)
@action(detail=True, methods=['post'])
def confirm(self, request, pk=None):
    """
    认定盘点差异

    操作说明:
    1. 验证差异状态
    2. 更新认定信息
    3. 发出 inventory_confirmed 事件
    4. 返回处理结果
    """
    # ... 实现代码 ...
```

### 3.3 API 命名规范

#### 3.3.1 URL 设计规范

```
# RESTful 资源命名
GET    /api/inventory/tasks/           # 列表
POST   /api/inventory/tasks/           # 创建
GET    /api/inventory/tasks/{id}/      # 详情
PUT    /api/inventory/tasks/{id}/      # 更新
PATCH  /api/inventory/tasks/{id}/      # 部分更新
DELETE /api/inventory/tasks/{id}/      # 删除

# 自定义动作 (使用动词)
POST   /api/inventory/tasks/{id}/start/        # 开始盘点
POST   /api/inventory/tasks/{id}/submit/       # 提交盘点
POST   /api/inventory/tasks/{id}/analyze/      # 差异分析
POST   /api/inventory/tasks/{id}/complete/     # 完成盘点

# 嵌套资源
GET    /api/inventory/tasks/{id}/items/        # 获取任务明细
GET    /api/inventory/tasks/{id}/differences/  # 获取任务差异
```

#### 3.3.2 响应格式规范

```python
# 成功响应 (200 OK)
{
    "id": "uuid",
    "task_no": "PD20250114001",
    "status": "in_progress",
    "created_at": "2025-01-14T10:30:00Z",
    "updated_at": "2025-01-14T11:30:00Z"
}

# 错误响应 (4xx/5xx)
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "task_no": ["该单号已存在"]
        }
    }
}

# 列表响应 (带分页)
{
    "count": 100,
    "next": "/api/inventory/tasks/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## 4. 多租户数据隔离

### 4.1 租户中间件

#### 4.1.1 问题说明

```python
# ❌ 当前问题：每个 Service 都要手动过滤
class InventoryService:
    def get_tasks(self, user):
        # 容易忘记！
        return InventoryTask.objects.filter(company=user.company)

class AssetService:
    def get_assets(self, user):
        # 容易写错！
        return Asset.objects.filter(company=user.company)
```

#### 4.1.2 解决方案：TenantMiddleware + TenantManager

```python
# apps/tenants/middleware.py

class TenantMiddleware:
    """
    多租户中间件

    功能:
    1. 从 JWT Token 中提取 company_id
    2. 将 current_company 注入到 request 对象
    3. 激活租户过滤
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 从 JWT 中提取公司ID
        company_id = self._extract_company_from_token(request)

        if company_id:
            # 获取或验证公司
            from apps.tenants.models import Company
            try:
                company = Company.objects.get(id=company_id, is_active=True)
                request.tenant = company
                request.tenant_id = str(company.id)

                # 激活租户过滤
                from apps.tenants.managers import activate_tenant
                activate_tenant(company.id)
            except Company.DoesNotExist:
                return JsonResponse(
                    {'error': 'Invalid company'},
                    status=403
                )

        response = self.get_response(request)

        # 清除租户上下文
        from apps.tenants.managers import deactivate_tenant
        deactivate_tenant()

        return response

    def _extract_company_from_token(self, request):
        """从 JWT Token 中提取公司ID"""
        # JWT payload: {"user_id": "...", "company_id": "..."}
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            access_token = AccessToken(token)
            return access_token.get('company_id')
        except Exception:
            return None
```

### 4.2 TenantManager 实现

```python
# apps/common/managers.py

from django.db import models
from threading import local

_tenant_storage = local()


def get_current_tenant_id():
    """获取当前租户ID"""
    return getattr(_tenant_storage, 'tenant_id', None)


def activate_tenant(tenant_id):
    """激活租户过滤"""
    _tenant_storage.tenant_id = str(tenant_id)


def deactivate_tenant():
    """清除租户过滤"""
    if hasattr(_tenant_storage, 'tenant_id'):
        delattr(_tenant_storage, 'tenant_id')


class TenantManager(models.Manager):
    """
    租户感知管理器

    所有查询自动添加 company 过滤
    """

    def get_queryset(self):
        qs = super().get_queryset()

        # 检查模型是否有 company 字段
        model = self.model
        if hasattr(model, 'company'):
            tenant_id = get_current_tenant_id()
            if tenant_id:
                qs = qs.filter(company_id=tenant_id)

        return qs


class TenantedModel(models.Model):
    """
    需要租户隔离的模型基类

    自动关联 company 并使用 TenantManager
    """
    company = models.ForeignKey(
        'tenants.Company',
        on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class_name)s_set',
        verbose_name='所属公司'
    )

    objects = TenantManager()

    class Meta:
        abstract = True
```

### 4.3 模型使用示例

```python
# apps/inventory/models.py

from apps.common.models import BaseModel, TenantedModel


class InventoryTask(TenantedModel, BaseModel):
    """
    盘点任务

    继承 TenantedModel 自动获得:
    - company 字段
    - 自动过滤的 TenantManager
    """
    task_no = models.CharField(max_length=50, verbose_name='盘点单号')
    # ... 其他字段 ...


# 使用时无需手动过滤
class InventoryService:
    def get_tasks(self):
        # ✅ 自动过滤当前租户的数据
        return InventoryTask.objects.all()

    def get_task(self, task_id):
        # ✅ 自动过滤，防止跨租户访问
        return InventoryTask.objects.get(id=task_id)
```

### 4.4 安全检查

```python
# apps/tenants/checks.py

from django.core.exceptions import PermissionDenied


def require_tenant(func):
    """
    装饰器：确保视图在租户上下文中执行
    """
    def wrapper(*args, **kwargs):
        from apps.common.managers import get_current_tenant_id
        tenant_id = get_current_tenant_id()

        if not tenant_id:
            raise PermissionDenied("No tenant context")

        return func(*args, **kwargs)
    return wrapper


class TenantAPIView(generics.GenericAPIView):
    """
    自动检查租户的 API View 基类
    """
    def check_permissions(self, request):
        super().check_permissions(request)

        # 检查租户
        if not hasattr(request, 'tenant'):
            self.permission_denied(request)

        # 检查对象所有权
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            if hasattr(obj, 'company') and obj.company_id != request.tenant.id:
                self.permission_denied(request)
```

---

## 5. 异步任务架构

### 5.1 Celery 优先级队列设计

#### 5.1.1 问题说明

```
┌─────────────────────────────────────────────────────────────┐
│ 问题: 所有任务共用一个队列，导致关键操作被阻塞               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [高优先级] 工作流审批响应 <─阻塞─ [低优先级] 生成10万条快照   │
│                                                             │
│  结果: 用户点击审批按钮，等待5秒后才响应，体验极差           │
└─────────────────────────────────────────────────────────────┘
```

#### 5.1.2 解决方案：优先级队列

```python
# backend/settings/celery.py

from celery import Celery

app = Celery('gzeams')

# 配置多个队列
app.conf.update(
    # ========================================
    # 队列定义 (按优先级)
    # ========================================
    task_queues={
        # 高优先级队列 - 关键业务操作
        'high': {
            'exchange': 'high',
            'routing_key': 'high',
            'queue_arguments': {
                'x-max-priority': 10,  # RabbitMQ 优先级支持
            }
        },
        # 默认队列 - 常规业务操作
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        # 低优先级队列 - 耗时操作
        'low': {
            'exchange': 'low',
            'routing_key': 'low',
        },
    },

    # ========================================
    # 任务路由 (按类型分配队列)
    # ========================================
    task_routes={
        # 高优先级: 工作流相关
        'apps.workflows.tasks.*': {'queue': 'high'},
        'apps.notifications.tasks.send_approval_notification': {'queue': 'high'},

        # 高优先级: 扫码实时反馈
        'apps.inventory.tasks.process_scan_result': {'queue': 'high'},

        # 默认: 常规任务
        'apps.inventory.tasks.*': {'queue': 'default'},
        'apps.assets.tasks.*': {'queue': 'default'},

        # 低优先级: 耗时操作
        'apps.inventory.tasks.generate_snapshot': {'queue': 'low'},
        'apps.reports.tasks.export_large_excel': {'queue': 'low'},
        'apps.statistics.tasks.update_dashboard_stats': {'queue': 'low'},
    },

    # ========================================
    # Worker 配置
    # ========================================
    worker_prefetch_multiplier=1,  # 高优先级任务不预取
    task_acks_late=True,           # 任务完成后才确认
    worker_max_tasks_per_child=100,  # 防止内存泄漏
)
```

### 5.2 任务优先级规范

#### 5.2.1 优先级分类

| 优先级 | 队列 | 响应时间 | 任务类型 | 示例 |
|-------|------|---------|---------|------|
| **P0 - 实时** | `high` | < 100ms | 用户交互等待 | 扫码反馈、审批提交 |
| **P1 - 高** | `high` | < 1s | 关键业务操作 | 工作流流转、重要通知 |
| **P2 - 中** | `default` | < 5s | 常规业务操作 | 数据同步、报表生成 |
| **P3 - 低** | `low` | 分钟级 | 后台任务 | 快照生成、大数据导出 |

#### 5.2.2 任务装饰器

```python
# apps/core/decorators.py

from functools import wraps
from celery import shared_task
from celery.exceptions import Ignore
import time


def celery_task(queue='default', priority=5, **options):
    """
    统一的 Celery 任务装饰器

    Args:
        queue: 队列名称 (high/default/low)
        priority: 优先级 (0-10, 数字越小优先级越高)
    """
    def decorator(func):
        @shared_task(
            queue=queue,
            priority=priority,
            **options
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ========================================
# 快捷装饰器
# ========================================

def real_time_task(func):
    """实时任务 (高优先级)"""
    return celery_task(queue='high', priority=0)(func)


def high_priority_task(func):
    """高优先级任务"""
    return celery_task(queue='high', priority=3)(func)


def normal_task(func):
    """常规任务"""
    return celery_task(queue='default', priority=5)(func)


def background_task(func):
    """后台任务 (低优先级)"""
    return celery_task(queue='low', priority=8)(func)
```

### 5.3 任务实现示例

```python
# apps/inventory/tasks.py

from apps.core.decorators import real_time_task, background_task
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


# ========================================
# 高优先级任务 (P0 - 实时)
# ========================================

@real_time_task
def process_scan_result(user_id, qr_code, location_id):
    """
    处理扫码结果 (实时)

    用户扫码后需要立即反馈，不能被其他任务阻塞
    """
    from apps.inventory.services.scanning import ScanningService

    result = ScanningService.process_qr_code(qr_code, user_id, location_id)
    return result


@shared_task(queue='high', priority=1)
def complete_workflow_task(instance_id, task_id, user_id, action, comment):
    """
    完成工作流任务 (高优先级)

    审批操作需要快速响应
    """
    from apps.workflows.services.workflow_adapter import WorkflowService

    service = WorkflowService()
    result = service.complete_user_task(
        instance_id=instance_id,
        task_id=task_id,
        user_id=user_id,
        action=action,
        comment=comment
    )
    return result


# ========================================
# 常规任务 (P2 - 中)
# ========================================

@normal_task
def sync_inventory_difference(difference_id):
    """
    同步差异数据到统计服务
    """
    from apps.statistics.services import StatisticsService

    StatisticsService.sync_difference(difference_id)
    return {'status': 'synced'}


# ========================================
# 后台任务 (P3 - 低)
# ========================================

@background_task
def generate_inventory_snapshot(task_id):
    """
    生成盘点快照 (低优先级)

    耗时操作，可能处理数十万条数据
    """
    from apps.inventory.services.snapshot import SnapshotService

    try:
        snapshot = SnapshotService.create_snapshot(task_id)
        logger.info(f"Snapshot created for task {task_id}: {snapshot.id}")
        return {'snapshot_id': str(snapshot.id)}
    except Exception as e:
        logger.error(f"Snapshot creation failed for task {task_id}: {e}")
        raise


@background_task
def export_inventory_report(task_id, report_type, user_id):
    """
    导出盘点报告 (低优先级)

    生成 Excel/PDF 可能耗时较长
    """
    from apps.reports.services import ReportExportService

    file_url = ReportExportService.export_report(task_id, report_type)

    # 导出完成后发送通知
    from apps.core.events import report_export_completed
    report_export_completed.send(
        sender='InventoryReportService',
        task_id=task_id,
        user_id=user_id,
        file_url=file_url
    )

    return {'file_url': file_url}


@background_task
def update_dashboard_stats(company_id):
    """
    更新大屏统计数据 (低优先级)

    定期执行的全量统计
    """
    from apps.statistics.services import DashboardStatsService

    DashboardStatsService.recalculate_all(company_id)
    return {'status': 'updated'}
```

### 5.4 Worker 部署配置

```bash
# ========================================
# Worker 进程分配建议
# ========================================

# 高优先级 Worker (处理关键操作)
celery -A gzeams worker -Q:high -c4 --loglevel=info -n high-worker@%h

# 默认 Worker (处理常规操作)
celery -A gzeams worker -Q:default -c2 --loglevel=info -n default-worker@%h

# 低优先级 Worker (处理耗时操作)
celery -A gzeams worker -Q:low -c2 --loglevel=info -n low-worker@%h

# Beat Worker (处理定时任务)
celery -A gzeams beat --loglevel=info -n beat-worker@%h
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  celery-high:
    build: ./backend
    command: celery -A gzeams worker -Q:high -c4 --loglevel=info
    deploy:
      replicas: 2
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery-default:
    build: ./backend
    command: celery -A gzeams worker -Q:default -c2 --loglevel=info
    deploy:
      replicas: 1

  celery-low:
    build: ./backend
    command: celery -A gzeams worker -Q:low -c1 --loglevel=info
    deploy:
      replicas: 1

  celery-beat:
    build: ./backend
    command: celery -A gzeams beat --loglevel=info
```

---

## 6. 工作流引擎集成

### 6.1 SpiffWorkflow 集成规范

已在 Phase 3.2 中详细定义，核心要点：

1. **流程定义存储**: `WorkflowDefinition.bpmn_xml`
2. **流程实例**: `WorkflowInstance.workflow_data` (序列化状态)
3. **用户任务**: `UserTask` 模型
4. **适配器接口**: `WorkflowService.start_process()`, `complete_user_task()`
5. **审批人解析**: `ApproverResolver` (user/role/leader/expression)

### 6.2 事件驱动集成

```python
# 工作流事件发出者
class WorkflowService:
    def complete_user_task(self, ...):
        # ... 完成任务逻辑 ...

        # 发出事件，而非直接调用
        workflow_task_completed.send(
            sender=self.__class__,
            instance_id=instance.id,
            task_id=task_id,
            action=action
        )
```

---

## 7. 前端架构规范

### 7.1 技术栈

| 技术 | 版本 | 用途 |
|-----|------|------|
| Vue | 3.4+ | 前端框架 |
| Vite | 5.0+ | 构建工具 |
| Element Plus | Latest | UI 组件库 |
| LogicFlow | Latest | BPMN 流程设计器 |
| Pinia | Latest | 状态管理 |
| Axios | Latest | HTTP 客户端 |

### 7.2 字段命名转换

```javascript
// src/utils/transform.js

// 后端 snake_case -> 前端 camelCase
export function toCamelCase(str) {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

export function objectToCamelCase(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return obj.map(objectToCamelCase)

  return Object.keys(obj).reduce((acc, key) => {
    acc[toCamelCase(key)] = objectToCamelCase(obj[key])
    return acc
  }, {})
}

// 前端 camelCase -> 后端 snake_case
export function toSnakeCase(str) {
  return str.replace(/([A-Z])/g, '_$1').toLowerCase()
}

export function objectToSnakeCase(obj) {
  if (obj === null || typeof obj !== 'object') return obj
  if (Array.isArray(obj)) return obj.map(objectToSnakeCase)

  return Object.keys(obj).reduce((acc, key) => {
    acc[toSnakeCase(key)] = objectToSnakeCase(obj[key])
    return acc
  }, {})
}
```

### 7.3 API 客户端配置

```javascript
// src/api/index.js

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { objectToCamelCase, objectToSnakeCase } from '@/utils/transform'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // camelCase -> snake_case
  if (config.data) config.data = objectToSnakeCase(config.data)
  if (config.params) config.params = objectToSnakeCase(config.params)
  return config
})

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // snake_case -> camelCase
    return objectToCamelCase(response.data)
  },
  (error) => {
    // 统一错误处理
    const message = error.response?.data?.error?.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)
```

---

## 8. 安全规范

### 8.1 认证授权

| 安全项 | 实现方式 |
|-------|---------|
| 认证 | JWT (django-rest-framework-simplejwt) |
| 授权 | RBAC (Role-Based Access Control) |
| 多租户隔离 | TenantMiddleware + TenantManager |
| API 访问 | API Key + Rate Limiting |

### 8.2 数据安全

| 安全项 | 实现方式 |
|-------|---------|
| 敏感字段加密 | `django-fernet-fields` |
| 操作审计 | 完整的审计日志 |
| SQL 注入防护 | ORM 参数化查询 |
| XSS 防护 | DRF Serializer 自动转义 |

### 8.3 依赖安全

```bash
# 定期检查依赖漏洞
pip install safety
safety check --json

# 或使用 pip-audit
pip install pip-audit
pip-audit
```

---

## 附录

### A. 技术选型对比

| 需求 | 方案 A (选择) | 方案 B (备选) | 选择理由 |
|-----|--------------|--------------|---------|
| BPMN 引擎 | SpiffWorkflow | Activiti/Camunda | 轻量级，Python 原生 |
| API 文档 | drf-spectacular | drf-yasg | 更好的 OpenAPI 3.0 支持 |
| 任务队列 | Celery + Redis | RQ | 更成熟的优先级队列支持 |
| 流程设计器 | LogicFlow | bpmn.js | 国产，中文文档完善 |

### B. 参考资源

- [SpiffWorkflow 文档](https://spiffworkflow.readthedocs.io/)
- [drf-spectacular 文档](https://drf-spectacular.readthedocs.io/)
- [Celery 文档](https://docs.celeryproject.org/)
- [LogicFlow 文档](https://site.logic-flow.cn/)

### C. 版本历史

| 版本 | 日期 | 变更说明 |
|-----|------|---------|
| 1.0.0 | 2025-01-14 | 初始版本，包含事件驱动、OpenAPI、多租户、异步任务架构 |
