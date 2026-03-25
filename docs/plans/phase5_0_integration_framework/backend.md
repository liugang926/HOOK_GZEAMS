# Phase 5.0: 通用ERP集成框架 - 后端实现

## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤 |

---

## 功能概述与业务场景

### 业务背景

HOOK GZEAMS固定资产管理系统需要与多种外部ERP系统进行集成，实现数据的双向同步和业务流程的无缝对接。通用集成框架采用适配器模式，提供统一的接口对接多种ERP系统（万达宝M18、SAP、金蝶、用友等），支持灵活的数据映射配置、任务调度管理、完整的日志审计和连接健康监控。

### 核心业务场景

| 场景 | 说明 | 优先级 |
|------|------|--------|
| 采购订单同步 | 从外部ERP系统拉取采购订单数据到资产系统 | P0 |
| 收货单同步 | 同步收货单据并自动创建资产卡片 | P0 |
| 供应商主数据同步 | 同步供应商基础信息 | P1 |
| 财务凭证推送 | 将资产折旧数据推送到ERP财务模块 | P1 |
| 组织架构同步 | 同步组织架构和部门信息 | P2 |

### 支持的外部系统

| 系统 | 系统类型 | 支持模块 | 实施优先级 |
|------|----------|----------|-----------|
| 万达宝M18 | m18 | 采购、财务、库存 | Phase 5.1 |
| SAP | sap | 采购、财务 | Phase 5.3+ |
| 金蝶 | kingdee | 财务 | Phase 5.3+ |
| 用友 | yonyou | 财务 | Phase 5.3+ |
| Oracle EBS | oracle | 全模块 | Phase 5.3+ |
| Odoo | odoo | 全模块 | Phase 5.3+ |

---

## 用户角色与权限

### 角色定义

| 角色 | 权限范围 | 说明 |
|------|----------|------|
| 系统管理员 | 全部权限 | 配置集成、管理映射、查看所有日志 |
| 集成管理员 | 集成配置权限 | 创建和管理集成配置、映射模板 |
| 业务用户 | 只读权限 | 查看同步任务状态、同步日志 |
| 审计员 | 日志查看 | 查看完整的集成审计日志 |

### 权限矩阵

| 操作 | 系统管理员 | 集成管理员 | 业务用户 | 审计员 |
|------|-----------|-----------|---------|--------|
| 创建集成配置 | ✅ | ✅ | ❌ | ❌ |
| 修改集成配置 | ✅ | ✅ | ❌ | ❌ |
| 删除集成配置 | ✅ | ❌ | ❌ | ❌ |
| 测试连接 | ✅ | ✅ | ❌ | ❌ |
| 触发同步 | ✅ | ✅ | ❌ | ❌ |
| 查看任务 | ✅ | ✅ | ✅ | ✅ |
| 查看日志 | ✅ | ✅ | ✅ | ✅ |
| 管理映射模板 | ✅ | ✅ | ❌ | ❌ |

---

## 公共模型引用声明

**本模块严格遵循GZEAMS公共基类架构规范，所有核心组件均继承相应的公共基类。**

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| **Model** | BaseModel | apps.common.models.BaseModel | 组织隔离(organization)、软删除(is_deleted+deleted_at)、审计字段(created_at+updated_at+created_by)、动态字段(custom_fields JSONB) |
| **Serializer** | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化(id/org/is_deleted/deleted_at/created_at/updated_at/created_by/custom_fields)、嵌套用户信息 |
| **ViewSet** | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织自动过滤、软删除处理、批量操作(batch-delete/batch-restore/batch-update)、恢复功能、审计字段自动设置 |
| **Service** | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD接口(create/update/delete/restore/get/query/paginate)、自动组织隔离、批量操作支持 |
| **Filter** | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤(created_at_from/to/updated_at_from/to)、创建人过滤、软删除状态过滤 |

### 基类使用示例

```python
# 示例：集成配置模型
class IntegrationConfig(BaseModel):
    """继承BaseModel，自动获得完整的组织隔离、软删除、审计功能"""
    system_type = models.CharField(...)
    # 自动继承：organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

# 示例：集成配置序列化器
class IntegrationConfigSerializer(BaseModelSerializer):
    """继承BaseModelSerializer，自动序列化所有公共字段"""
    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = BaseModelSerializer.Meta.fields + ['system_type', 'config_name']
        # 自动包含：id, organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

# 示例：集成配置视图集
class IntegrationConfigViewSet(BaseModelViewSetWithBatch):
    """继承BaseModelViewSetWithBatch，自动获得批量操作能力"""
    queryset = IntegrationConfig.objects.all()
    serializer_class = IntegrationConfigSerializer
    # 自动获得：组织过滤、软删除、batch-delete/batch-restore/batch-update、恢复功能
```

---

## 数据模型设计

### 1. 核心常量定义

```python
# backend/apps/integration/constants.py

from django.db import models

class IntegrationSystemType(models.TextChoices):
    """集成系统类型枚举"""
    M18 = 'm18', '万达宝M18'
    SAP = 'sap', 'SAP'
    KINGDEE = 'kingdee', '金蝶'
    YONYOU = 'yonyou', '用友'
    ORACLE = 'oracle', 'Oracle EBS'
    ODOO = 'odoo', 'Odoo'

class IntegrationModuleType(models.TextChoices):
    """集成模块类型枚举"""
    PROCUREMENT = 'procurement', '采购管理'
    FINANCE = 'finance', '财务核算'
    INVENTORY = 'inventory', '库存管理'
    HR = 'hr', '人力资源'
    CRM = 'crm', '客户关系'

class SyncDirection(models.TextChoices):
    """同步方向枚举"""
    PULL = 'pull', '拉取(第三方→本系统)'
    PUSH = 'push', '推送(本系统→第三方)'
    BIDIRECTIONAL = 'bidirectional', '双向同步'

class SyncStatus(models.TextChoices):
    """同步状态枚举"""
    PENDING = 'pending', '待执行'
    RUNNING = 'running', '执行中'
    SUCCESS = 'success', '成功'
    PARTIAL_SUCCESS = 'partial_success', '部分成功'
    FAILED = 'failed', '失败'
    CANCELLED = 'cancelled', '已取消'
```

### 2. 集成配置模型

```python
# backend/apps/integration/models.py

from django.db import models
from apps.common.models import BaseModel
from django.contrib.postgres.fields import JSONField


class IntegrationConfig(BaseModel):
    """通用集成配置模型

    继承BaseModel，自动获得：
    - organization: 多组织数据隔离
    - is_deleted, deleted_at: 软删除机制
    - created_at, updated_at, created_by: 完整审计日志
    - custom_fields: 动态扩展字段(JSONB)
    """

    class Meta:
        db_table = 'integration_config'
        verbose_name = '集成配置'
        verbose_name_plural = '集成配置'
        ordering = ['-created_at']
        unique_together = [['organization', 'system_type']]

    # ==================== 基础配置 ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.choices,
        verbose_name='系统类型',
        help_text='外部ERP系统类型'
    )

    system_name = models.CharField(
        max_length=100,
        verbose_name='系统名称',
        help_text='自定义名称，如"生产环境M18"'
    )

    # ==================== 连接配置 ====================

    connection_config = JSONField(
        default=dict,
        verbose_name='连接配置',
        help_text='存储API地址、认证信息等，结构由各适配器定义'
    )

    # ==================== 模块配置 ====================

    enabled_modules = JSONField(
        default=list,
        verbose_name='启用模块',
        help_text='启用的集成模块列表，如["procurement", "finance"]'
    )

    # ==================== 同步配置 ====================

    sync_config = JSONField(
        default=dict,
        verbose_name='同步配置',
        help_text='同步间隔、自动同步等配置'
    )

    # ==================== 数据映射配置 ====================

    mapping_config = JSONField(
        default=dict,
        verbose_name='数据映射配置',
        help_text='字段映射关系配置'
    )

    # ==================== 状态管理 ====================

    is_enabled = models.BooleanField(
        default=True,
        verbose_name='是否启用',
        db_index=True
    )

    last_sync_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后同步时间'
    )

    last_sync_status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
        verbose_name='最后同步状态'
    )

    # ==================== 健康监控 ====================

    health_status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', '健康'),
            ('degraded', '降级'),
            ('unhealthy', '不可用'),
        ],
        default='unhealthy',
        verbose_name='健康状态',
        db_index=True
    )

    last_health_check_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后健康检查时间'
    )

    def __str__(self):
        return f"{self.organization.name} - {self.get_system_type_display()}"
```

### 3. 同步任务模型

```python
class IntegrationSyncTask(BaseModel):
    """集成同步任务模型

    继承BaseModel，记录每次同步执行的详细信息
    """

    class Meta:
        db_table = 'integration_sync_task'
        verbose_name = '同步任务'
        verbose_name_plural = '同步任务'
        ordering = ['-created_at']

    # ==================== 关联关系 ====================

    config = models.ForeignKey(
        IntegrationConfig,
        on_delete=models.CASCADE,
        related_name='sync_tasks',
        verbose_name='集成配置'
    )

    # ==================== 任务标识 ====================

    task_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='任务ID',
        help_text='全局唯一任务标识'
    )

    # ==================== 同步信息 ====================

    module_type = models.CharField(
        max_length=20,
        choices=IntegrationModuleType.choices,
        verbose_name='模块类型'
    )

    direction = models.CharField(
        max_length=20,
        choices=SyncDirection.choices,
        verbose_name='同步方向'
    )

    business_type = models.CharField(
        max_length=50,
        verbose_name='业务类型',
        help_text='如purchase_order, voucher等'
    )

    # ==================== 执行参数 ====================

    sync_params = JSONField(
        default=dict,
        verbose_name='同步参数',
        help_text='本次同步的执行参数'
    )

    # ==================== 执行状态 ====================

    status = models.CharField(
        max_length=20,
        choices=SyncStatus.choices,
        default=SyncStatus.PENDING,
        verbose_name='状态',
        db_index=True
    )

    # ==================== 执行结果统计 ====================

    total_count = models.IntegerField(
        default=0,
        verbose_name='总数'
    )

    success_count = models.IntegerField(
        default=0,
        verbose_name='成功数'
    )

    failed_count = models.IntegerField(
        default=0,
        verbose_name='失败数'
    )

    error_summary = JSONField(
        default=list,
        verbose_name='错误汇总',
        help_text='记录失败的详细信息'
    )

    # ==================== 执行时间 ====================

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始时间',
        db_index=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='完成时间',
        db_index=True
    )

    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='执行时长(毫秒)'
    )

    # ==================== Celery任务关联 ====================

    celery_task_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Celery任务ID',
        help_text='关联的Celery异步任务ID'
    )
```

### 4. 集成日志模型

```python
class IntegrationLog(BaseModel):
    """集成日志模型

    继承BaseModel，详细记录每次API调用的完整信息
    """

    class Meta:
        db_table = 'integration_log'
        verbose_name = '集成日志'
        verbose_name_plural = '集成日志'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'system_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['success']),
            models.Index(fields=['-created_at']),
        ]

    # ==================== 关联关系 ====================

    sync_task = models.ForeignKey(
        IntegrationSyncTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        verbose_name='同步任务'
    )

    # ==================== 集成标识 ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.choices,
        verbose_name='系统类型'
    )

    integration_type = models.CharField(
        max_length=50,
        verbose_name='集成类型',
        help_text='如m18_po, sap_fi等'
    )

    # ==================== 请求信息 ====================

    action = models.CharField(
        max_length=20,
        choices=SyncDirection.choices,
        verbose_name='操作类型'
    )

    request_method = models.CharField(
        max_length=10,
        verbose_name='请求方法',
        help_text='GET, POST, PUT, DELETE等'
    )

    request_url = models.TextField(
        verbose_name='请求URL'
    )

    request_headers = JSONField(
        default=dict,
        verbose_name='请求头'
    )

    request_body = JSONField(
        default=dict,
        verbose_name='请求体'
    )

    # ==================== 响应信息 ====================

    status_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='HTTP状态码'
    )

    response_body = JSONField(
        default=dict,
        verbose_name='响应体'
    )

    response_headers = JSONField(
        default=dict,
        verbose_name='响应头'
    )

    # ==================== 执行结果 ====================

    success = models.BooleanField(
        default=False,
        verbose_name='是否成功',
        db_index=True
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='错误信息'
    )

    # ==================== 执行时间 ====================

    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='执行时长(毫秒)'
    )

    # ==================== 业务关联 ====================

    business_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='业务类型'
    )

    business_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='业务ID'
    )

    external_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='外部系统ID'
    )
```

### 5. 数据映射模板模型

```python
class DataMappingTemplate(BaseModel):
    """数据映射模板模型

    继承BaseModel，定义本系统与外部系统之间的数据映射关系
    """

    class Meta:
        db_table = 'data_mapping_template'
        verbose_name = '数据映射模板'
        verbose_name_plural = '数据映射模板'
        unique_together = [['organization', 'system_type', 'business_type']]

    # ==================== 基础配置 ====================

    system_type = models.CharField(
        max_length=20,
        choices=IntegrationSystemType.choices,
        verbose_name='系统类型'
    )

    business_type = models.CharField(
        max_length=50,
        verbose_name='业务类型',
        help_text='如purchase_order, asset, voucher等'
    )

    template_name = models.CharField(
        max_length=100,
        verbose_name='模板名称'
    )

    # ==================== 映射配置 ====================

    field_mappings = JSONField(
        default=dict,
        verbose_name='字段映射',
        help_text='格式: {"local_field": "external_field", ...}'
    )

    value_mappings = JSONField(
        default=dict,
        verbose_name='值映射',
        help_text='格式: {"field_name": {"local_value": "external_value"}}'
    )

    transform_rules = JSONField(
        default=list,
        verbose_name='转换规则',
        help_text='数据转换规则列表'
    )

    # ==================== 状态管理 ====================

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    def __str__(self):
        return f"{self.get_system_type_display()} - {self.business_type} - {self.template_name}"
```

### 6. 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations integration

# 执行迁移
python manage.py migrate integration

# 验证迁移
python manage.py showmigrations integration
```

---

## API接口设计

### 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

详见 `common_base_features/api.md` 中的标准 API 规范。

所有集成配置相关的 CRUD 操作自动获得以下标准端点：

**标准 CRUD 端点**：
- `GET /api/integration/configs/` - 列表查询（分页、过滤、搜索）
- `GET /api/integration/configs/{id}/` - 获取单条记录
- `POST /api/integration/configs/` - 创建新记录
- `PUT /api/integration/configs/{id}/` - 完整更新
- `PATCH /api/integration/configs/{id}/` - 部分更新
- `DELETE /api/integration/configs/{id}/` - 软删除
- `GET /api/integration/configs/deleted/` - 查看已删除记录
- `POST /api/integration/configs/{id}/restore/` - 恢复已删除记录

**批量操作端点**（继承 BatchOperationMixin）：
- `POST /api/integration/configs/batch-delete/` - 批量软删除
- `POST /api/integration/configs/batch-restore/` - 批量恢复
- `POST /api/integration/configs/batch-update/` - 批量更新

**标准响应格式**：
- 成功响应：`{success: true, message: "...", data: {...}}`
- 列表响应：`{success: true, data: {count, next, previous, results}}`
- 错误响应：`{success: false, error: {code, message, details}}`
- 批量操作响应：`{success/failed, message, summary: {total, succeeded, failed}, results: [...]}`

**标准错误码**：
- `VALIDATION_ERROR` (400) - 请求数据验证失败
- `UNAUTHORIZED` (401) - 未授权访问
- `PERMISSION_DENIED` (403) - 权限不足
- `NOT_FOUND` (404) - 资源不存在
- `ORGANIZATION_MISMATCH` (403) - 组织不匹配
- `SOFT_DELETED` (410) - 资源已删除
- `SERVER_ERROR` (500) - 服务器内部错误

### 1. 集成配置管理API

#### 1.1 创建集成配置

```http
POST /api/integration/configs/
Content-Type: application/json

{
    "system_type": "m18",
    "system_name": "万达宝M18生产环境",
    "is_enabled": true,
    "connection_config": {
        "api_url": "https://m18.example.com/api",
        "api_key": "your_api_key",
        "client_id": "GZEAMS",
        "username": "admin",
        "password": "encrypted_password"
    },
    "enabled_modules": ["procurement", "finance"],
    "sync_config": {
        "auto_sync": true,
        "sync_interval": 3600,
        "retry_times": 3
    },
    "mapping_config": {}
}
```

**响应示例**：

```json
{
    "success": true,
    "message": "创建成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "organization": {
            "id": "org-uuid",
            "name": "示例组织"
        },
        "system_type": "m18",
        "system_name": "万达宝M18生产环境",
        "is_enabled": true,
        "connection_config": {...},
        "enabled_modules": ["procurement", "finance"],
        "sync_config": {...},
        "mapping_config": {},
        "health_status": "unhealthy",
        "last_sync_at": null,
        "last_sync_status": "pending",
        "is_deleted": false,
        "deleted_at": null,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "created_by": {
            "id": "user-uuid",
            "username": "admin"
        },
        "custom_fields": {}
    }
}
```

#### 1.2 测试连接

```http
POST /api/integration/configs/{id}/test_connection/
```

**响应示例：**

```json
{
    "success": true,
    "message": "连接成功",
    "data": {
        "response_time_ms": 245,
        "details": {
            "company_name": "示例公司",
            "api_version": "2.0",
            "server_time": "2024-01-15T10:30:00Z"
        }
    }
}
```

#### 1.3 健康检查

```http
POST /api/integration/configs/{id}/health_check/
```

#### 1.4 批量操作（继承自BatchOperationMixin）

**批量操作响应格式**（全部成功）：

```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

**批量操作响应格式**（部分失败）：

```json
{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": false, "error": "记录不存在"},
        {"id": "uuid3", "success": true}
    ]
}
```

### 2. 同步任务管理API

#### 2.1 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

同步任务同样继承自 `BaseModelViewSetWithBatch`，自动获得以下标准端点：

**标准 CRUD 端点**：
- `GET /api/integration/sync-tasks/` - 列表查询（分页、过滤、搜索）
- `GET /api/integration/sync-tasks/{id}/` - 获取单条记录
- `POST /api/integration/sync-tasks/` - 创建新记录
- `PUT /api/integration/sync-tasks/{id}/` - 完整更新
- `PATCH /api/integration/sync-tasks/{id}/` - 部分更新
- `DELETE /api/integration/sync-tasks/{id}/` - 软删除
- `GET /api/integration/sync-tasks/deleted/` - 查看已删除记录
- `POST /api/integration/sync-tasks/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/integration/sync-tasks/batch-delete/` - 批量软删除
- `POST /api/integration/sync-tasks/batch-restore/` - 批量恢复
- `POST /api/integration/sync-tasks/batch-update/` - 批量更新

#### 2.2 查询同步任务

```http
GET /api/integration/sync-tasks/?status=running&module_type=procurement&page=1&page_size=20
```

**支持的过滤参数：**
- `config`: 集成配置ID
- `module_type`: 模块类型
- `direction`: 同步方向
- `business_type`: 业务类型
- `status`: 任务状态
- `started_at_from`: 开始时间起始
- `started_at_to`: 开始时间结束
- `completed_at_from`: 完成时间起始
- `completed_at_to`: 完成时间结束
- 以及BaseModelFilter的公共过滤参数（created_at_from/to, created_by等）

#### 2.2 取消任务

```http
POST /api/integration/sync-tasks/{task_id}/cancel/
```

#### 2.3 重试失败任务

```http
POST /api/integration/sync-tasks/{task_id}/retry/
```

### 3. 集成日志查询API

#### 3.1 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

集成日志同样继承自 `BaseModelViewSetWithBatch`，自动获得以下标准端点：

**标准 CRUD 端点**：
- `GET /api/integration/logs/` - 列表查询（分页、过滤、搜索）
- `GET /api/integration/logs/{id}/` - 获取单条记录
- `POST /api/integration/logs/` - 创建新记录
- `PUT /api/integration/logs/{id}/` - 完整更新
- `PATCH /api/integration/logs/{id}/` - 部分更新
- `DELETE /api/integration/logs/{id}/` - 软删除
- `GET /api/integration/logs/deleted/` - 查看已删除记录
- `POST /api/integration/logs/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/integration/logs/batch-delete/` - 批量软删除
- `POST /api/integration/logs/batch-restore/` - 批量恢复
- `POST /api/integration/logs/batch-update/` - 批量更新

#### 3.2 查询日志

```http
GET /api/integration/logs/?system_type=m18&success=false&created_at_from=2024-01-01
```

**支持的过滤参数：**
- `sync_task`: 同步任务ID
- `system_type`: 系统类型
- `action`: 操作类型
- `success`: 是否成功
- `status_code`: HTTP状态码
- `status_code_from/to`: 状态码范围
- `duration_ms`: 执行时长
- `duration_ms_from/to`: 时长范围
- 以及BaseModelFilter的公共过滤参数

#### 3.2 日志统计

```http
GET /api/integration/logs/statistics/
```

**响应示例**：

```json
{
    "success": true,
    "data": {
        "total": 1000,
        "success": 950,
        "failed": 50,
        "by_system": [
            {"system_type": "m18", "count": 800},
            {"system_type": "sap", "count": 200}
        ],
        "by_action": [
            {"action": "pull", "count": 700},
            {"action": "push", "count": 300}
        ]
    }
}
```

**错误响应示例**：

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "system_type": ["不支持的系统类型"]
        }
    }
}
```

---

## 前端组件设计

### 1. 集成配置管理页面

#### 1.1 集成配置列表

**路由：** `/integration/configs`

**组件位置：** `frontend/src/views/integration/IntegrationConfigList.vue`

**功能特性：**
- 展示所有集成配置（自动组织隔离）
- 支持按系统类型、启用状态、健康状态过滤
- 实时显示健康状态和最后同步时间
- 操作按钮：编辑、删除（软删除）、测试连接、健康检查、手动触发同步

**关键字段显示：**
- 系统图标（根据system_type）
- 系统名称
- 健康状态（健康/降级/不可用）
- 最后同步时间
- 最后同步状态

#### 1.2 集成配置表单

**路由：** `/integration/configs/:id`

**组件位置：** `frontend/src/views/integration/IntegrationConfigForm.vue`

**功能特性：**
- 动态表单：根据system_type显示不同的连接配置字段
- 密码字段加密显示
- 测试连接按钮（实时验证配置）
- 模块启用配置（多选框）
- 同步配置（自动同步开关、同步间隔）

**表单验证：**
- API地址格式验证
- 认证信息完整性验证
- 同步间隔数值范围验证

#### 1.3 数据映射配置

**路由：** `/integration/configs/:id/mappings`

**组件位置：** `frontend/src/views/integration/DataMappingConfig.vue`

**功能特性：**
- 可视化字段映射编辑器
- 支持拖拽式字段映射
- 值转换规则配置
- 映射模板保存和复用
- 测试映射（输入示例数据查看转换结果）

### 2. 同步任务监控页面

#### 2.1 任务列表

**路由：** `/integration/tasks`

**组件位置：** `frontend/src/views/integration/SyncTaskList.vue`

**功能特性：**
- 实时任务状态更新（WebSocket推送）
- 进度条显示执行进度
- 任务详情查看（包含错误汇总）
- 失败任务重试按钮
- 执行中任务取消按钮

**状态标识：**
- 待执行：灰色
- 执行中：蓝色动画
- 成功：绿色
- 部分成功：橙色
- 失败：红色
- 已取消：灰色

#### 2.2 任务详情

**路由：** `/integration/tasks/:taskId`

**组件位置：** `frontend/src/views/integration/SyncTaskDetail.vue`

**功能特性：**
- 任务基本信息
- 执行参数展示
- 执行结果统计（总数、成功数、失败数）
- 错误详情列表（可折叠）
- 关联日志列表（分页）
- 执行时间轴

### 3. 集成日志查询页面

#### 3.1 日志列表

**路由：** `/integration/logs`

**组件位置：** `frontend/src/views/integration/IntegrationLogList.vue`

**功能特性：**
- 高级过滤面板（系统类型、操作类型、成功/失败、时间范围）
- 日志详情抽屉（点击行展开）
- 请求/响应JSON高亮显示
- 执行时长分布图表
- 成功率趋势图表
- 导出日志（CSV/Excel）

#### 3.2 日志详情

**组件位置：** `frontend/src/components/integration/LogDetailDrawer.vue`

**显示内容：**
- 请求信息（方法、URL、Headers、Body）
- 响应信息（状态码、Headers、Body）
- 执行统计（时长、成功/失败）
- 业务关联信息
- 错误堆栈（如果失败）

### 4. 通用组件

#### 4.1 健康状态徽章

**组件位置：** `frontend/src/components/integration/HealthStatusBadge.vue`

```vue
<template>
  <el-badge :value="status" :type="badgeType" />
</template>

<script>
export default {
  props: {
    status: {
      type: String,
      required: true
    }
  },
  computed: {
    badgeType() {
      const map = {
        healthy: 'success',
        degraded: 'warning',
        unhealthy: 'danger'
      }
      return map[this.status] || 'info'
    }
  }
}
</script>
```

#### 4.2 同步状态指示器

**组件位置：** `frontend/src/components/integration/SyncStatusIndicator.vue`

**功能：**
- 显示同步状态图标和文本
- 执行中状态显示旋转动画
- 点击可查看任务详情

---

## 测试用例

### 1. 模型测试

```python
# backend/apps/integration/tests/test_models.py

import pytest
from django.utils import timezone
from apps.integration.models import IntegrationConfig, IntegrationSyncTask, IntegrationLog
from apps.organizations.models import Organization
from apps.accounts.models import User


@pytest.mark.django_db
class TestIntegrationConfigModel:
    """集成配置模型测试"""

    def test_create_config(self, organization, user):
        """测试创建集成配置"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user,
            connection_config={
                'api_url': 'https://test.m18.com/api',
                'username': 'test'
            }
        )

        assert config.organization == organization
        assert config.system_type == 'm18'
        assert config.health_status == 'unhealthy'
        assert config.is_deleted is False
        assert config.created_at is not None

    def test_organization_isolation(self, org1, org2, user):
        """测试组织隔离"""
        # org1创建配置
        config1 = IntegrationConfig.objects.create(
            organization=org1,
            system_type='m18',
            system_name='Org1 M18',
            created_by=user
        )

        # org2创建配置
        config2 = IntegrationConfig.objects.create(
            organization=org2,
            system_type='sap',
            system_name='Org2 SAP',
            created_by=user
        )

        # 切换到org1上下文
        from apps.common.models import set_current_organization
        set_current_organization(org1)

        # 只能看到org1的配置
        configs = IntegrationConfig.objects.all()
        assert config1 in configs
        assert config2 not in configs

    def test_soft_delete(self, organization, user):
        """测试软删除"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user
        )
        config_id = config.id

        # 软删除
        config.soft_delete()

        # 普通查询找不到
        assert not IntegrationConfig.objects.filter(id=config_id).exists()

        # 使用all_objects可以找到
        assert IntegrationConfig.all_objects.filter(id=config_id).exists()

        # 恢复
        config.restore()
        assert IntegrationConfig.objects.filter(id=config_id).exists()


@pytest.mark.django_db
class TestIntegrationSyncTaskModel:
    """同步任务模型测试"""

    def test_create_sync_task(self, organization, user, integration_config):
        """测试创建同步任务"""
        task = IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-001',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            created_by=user
        )

        assert task.status == 'pending'
        assert task.total_count == 0
        assert task.success_count == 0
        assert task.failed_count == 0

    def test_task_execution_flow(self, organization, user, integration_config):
        """测试任务执行流程"""
        task = IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-002',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            created_by=user
        )

        # 更新为执行中
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()

        # 模拟执行完成
        task.status = 'success'
        task.completed_at = timezone.now()
        task.total_count = 100
        task.success_count = 95
        task.failed_count = 5
        task.duration_ms = 5000
        task.save()

        # 验证
        updated_task = IntegrationSyncTask.objects.get(id=task.id)
        assert updated_task.status == 'success'
        assert updated_task.duration_ms == 5000
        assert updated_task.completed_at is not None


@pytest.mark.django_db
class TestIntegrationLogModel:
    """集成日志模型测试"""

    def test_create_log(self, organization, user, integration_config, sync_task):
        """测试创建日志"""
        log = IntegrationLog.objects.create(
            organization=organization,
            sync_task=sync_task,
            system_type='m18',
            integration_type='m18_po',
            action='pull',
            request_method='GET',
            request_url='https://m18.test.com/api/po',
            request_headers={'Authorization': 'Bearer token'},
            status_code=200,
            response_body={'data': []},
            success=True,
            duration_ms=250,
            created_by=user
        )

        assert log.success is True
        assert log.status_code == 200
        assert log.duration_ms == 250
```

### 2. 服务层测试

```python
# backend/apps/integration/tests/test_services.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.services.config_service import IntegrationConfigService
from apps.integration.services.sync_service import IntegrationSyncService


@pytest.mark.django_db
class TestIntegrationConfigService:
    """集成配置服务测试"""

    def test_create_config(self, organization, user):
        """测试创建配置"""
        service = IntegrationConfigService(organization, user)

        config_data = {
            'system_type': 'm18',
            'system_name': '测试M18',
            'connection_config': {'api_url': 'https://test.com'}
        }

        config = service.create(config_data)

        assert config.system_type == 'm18'
        assert config.organization == organization
        assert config.created_by == user

    def test_get_enabled_configs(self, organization, user):
        """测试获取启用的配置"""
        service = IntegrationConfigService(organization, user)

        # 创建多个配置
        for i in range(3):
            IntegrationConfig.objects.create(
                organization=organization,
                system_type='m18',
                system_name=f'测试M18-{i}',
                is_enabled=(i < 2),  # 前两个启用
                created_by=user
            )

        # 获取启用的配置
        enabled_configs = service.get_enabled_configs()

        assert len(enabled_configs) == 2
        assert all(c.is_enabled for c in enabled_configs)

    @patch('apps.integration.factory.AdapterFactory.create')
    def test_test_connection(self, mock_adapter_factory, organization, user):
        """测试连接功能"""
        # Mock适配器
        mock_adapter = Mock()
        mock_adapter.test_connection.return_value = {
            'success': True,
            'message': '连接成功',
            'response_time_ms': 100
        }
        mock_adapter_factory.return_value = mock_adapter

        # 创建配置
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user
        )

        # 测试连接
        service = IntegrationConfigService(organization, user)
        result = service.test_connection(config)

        assert result['success'] is True
        assert result['response_time_ms'] == 100


@pytest.mark.django_db
class TestIntegrationSyncService:
    """同步服务测试"""

    def test_create_sync_task(self, organization, user, integration_config):
        """测试创建同步任务"""
        service = IntegrationSyncService(organization, user)

        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            sync_params={'start_date': '2024-01-01'}
        )

        assert task.config == integration_config
        assert task.module_type == 'procurement'
        assert task.direction == 'pull'
        assert task.status == 'pending'

    def test_execute_sync_success(self, organization, user, integration_config):
        """测试执行同步（成功场景）"""
        service = IntegrationSyncService(organization, user)

        # 创建任务
        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order'
        )

        # Mock同步函数
        def mock_sync_func():
            return {
                'total': 100,
                'success': 95,
                'failed': 5,
                'errors': []
            }

        # 执行同步
        result = service.execute_sync(task, mock_sync_func)

        assert result['status'] == 'partial_success'
        assert result['total'] == 100
        assert result['success'] == 95

    def test_execute_sync_failure(self, organization, user, integration_config):
        """测试执行同步（失败场景）"""
        service = IntegrationSyncService(organization, user)

        # 创建任务
        task = service.create_sync_task(
            config=integration_config,
            module_type='procurement',
            direction='pull',
            business_type='purchase_order'
        )

        # Mock抛出异常的同步函数
        def mock_sync_func():
            raise Exception("网络连接失败")

        # 执行同步
        result = service.execute_sync(task, mock_sync_func)

        assert result['status'] == 'failed'
        assert len(result['errors']) > 0
```

### 3. API测试

```python
# backend/apps/integration/tests/test_api.py

import pytest
from django.urls import reverse
from rest_framework import status
from apps.integration.models import IntegrationConfig, IntegrationSyncTask


@pytest.mark.django_db
class TestIntegrationConfigAPI:
    """集成配置API测试"""

    def test_create_config_api(self, auth_client, organization):
        """测试创建配置API"""
        url = reverse('integration-config-list')

        data = {
            'system_type': 'm18',
            'system_name': '测试M18',
            'connection_config': {
                'api_url': 'https://test.com'
            }
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert response.data['data']['system_type'] == 'm18'

    def test_list_configs_api(self, auth_client, organization, user):
        """测试查询配置列表API"""
        # 创建测试数据
        IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user
        )

        url = reverse('integration-config-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert len(response.data['data']['results']) == 1

    def test_batch_delete_api(self, auth_client, organization, user):
        """测试批量删除API"""
        # 创建多个配置
        configs = [
            IntegrationConfig.objects.create(
                organization=organization,
                system_type='m18',
                system_name=f'测试M18-{i}',
                created_by=user
            )
            for i in range(3)
        ]

        url = reverse('integration-config-batch-delete')
        data = {
            'ids': [str(c.id) for c in configs]
        }

        response = auth_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['summary']['succeeded'] == 3

        # 验证软删除
        for config in configs:
            config.refresh_from_db()
            assert config.is_deleted is True


@pytest.mark.django_db
class TestIntegrationSyncTaskAPI:
    """同步任务API测试"""

    def test_list_tasks_api(self, auth_client, organization, user, integration_config):
        """测试查询任务列表API"""
        # 创建测试任务
        IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-001',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            created_by=user
        )

        url = reverse('integration-sync-task-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']['results']) == 1

    def test_cancel_task_api(self, auth_client, organization, user, integration_config):
        """测试取消任务API"""
        # 创建待执行的任务
        task = IntegrationSyncTask.objects.create(
            organization=organization,
            config=integration_config,
            task_id='test-task-002',
            module_type='procurement',
            direction='pull',
            business_type='purchase_order',
            status='pending',
            created_by=user
        )

        url = reverse('integration-sync-task-cancel', kwargs={'task_id': task.task_id})
        response = auth_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # 验证状态已更新
        task.refresh_from_db()
        assert task.status == 'cancelled'


@pytest.mark.django_db
class TestIntegrationLogAPI:
    """集成日志API测试"""

    def test_list_logs_api(self, auth_client, organization, user):
        """测试查询日志列表API"""
        url = reverse('integration-log-list')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_log_statistics_api(self, auth_client, organization):
        """测试日志统计API"""
        url = reverse('integration-log-statistics')
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data['data']
        assert 'success' in response.data['data']
        assert 'failed' in response.data['data']
```

### 4. 适配器测试

```python
# backend/apps/integration/tests/test_adapters.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.adapters.base import BaseIntegrationAdapter
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
class TestBaseIntegrationAdapter:
    """适配器基类测试"""

    def test_adapter_initialization(self, organization, user):
        """测试适配器初始化"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            connection_config={'api_url': 'https://test.com'},
            created_by=user
        )

        # 创建测试适配器
        class TestAdapter(BaseIntegrationAdapter):
            adapter_type = 'test'
            adapter_name = '测试适配器'

            def test_connection(self):
                return {'success': True}

            def get_auth_headers(self):
                return {'Content-Type': 'application/json'}

            def pull_data(self, business_type, params=None):
                return []

            def push_data(self, business_type, data):
                return {}

        adapter = TestAdapter(config)

        assert adapter.config == config
        assert adapter.organization == organization
        assert adapter.connection_config['api_url'] == 'https://test.com'

    def test_map_to_local(self, organization, user):
        """测试数据映射到本地格式"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user
        )

        # 创建映射模板
        DataMappingTemplate.objects.create(
            organization=organization,
            system_type='m18',
            business_type='purchase_order',
            template_name='测试映射',
            field_mappings={
                'local_code': 'externalCode',
                'local_name': 'externalName'
            },
            value_mappings={
                'status': {
                    '1': 'draft',
                    '2': 'approved'
                }
            }
        )

        # 创建适配器
        class TestAdapter(BaseIntegrationAdapter):
            adapter_type = 'test'
            adapter_name = '测试适配器'

            def test_connection(self):
                return {'success': True}

            def get_auth_headers(self):
                return {}

            def pull_data(self, business_type, params=None):
                return []

            def push_data(self, business_type, data):
                return {}

        adapter = TestAdapter(config)

        # 测试映射
        external_data = {
            'externalCode': 'PO001',
            'externalName': '测试订单',
            'status': '1'
        }

        local_data = adapter.map_to_local('purchase_order', external_data)

        assert local_data['local_code'] == 'PO001'
        assert local_data['local_name'] == '测试订单'
        assert local_data['status'] == 'draft'
```

---

## 后续任务

1. **Phase 5.1**: 实现万达宝M18适配器（基于通用框架）
   - M18 OAuth2认证
   - 采购订单同步
   - 收货单同步
   - 供应商主数据同步

2. **Phase 5.2**: 实现财务凭证集成（基于通用框架）
   - 凭证格式定义
   - 折旧数据推送
   - 凭证状态同步

3. **扩展其他ERP适配器**（Phase 5.3+）
   - SAP适配器
   - 金蝶适配器
   - 用友适配器
   - Oracle EBS适配器
   - Odoo适配器

---

## 附录：公共基类优势总结

### A.1 代码一致性

通过使用公共基类，集成框架的所有组件遵循统一的代码规范：

| 组件类型 | 基类 | 自动获得的功能 |
|---------|------|---------------|
| **Model** | `BaseModel` | 多组织隔离、软删除、审计日志、动态字段 |
| **Serializer** | `BaseModelSerializer` | 公共字段序列化、审计信息、动态字段支持 |
| **ViewSet** | `BaseModelViewSetWithBatch` | 组织隔离、软删除、批量操作、恢复功能 |
| **Service** | `BaseCRUDService` | 统一CRUD接口、组织过滤、分页查询 |
| **Filter** | `BaseModelFilter` | 时间范围过滤、创建人过滤、状态过滤 |

### A.2 开发效率提升

**传统方式 vs 基类方式**：

```python
# 传统方式：需要手动实现所有功能
class IntegrationConfigSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    organization = OrganizationSerializer()
    is_deleted = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    # ... 需要手动编写20+行代码

    class Meta:
        model = IntegrationConfig
        fields = ['id', 'organization', ...]  # 需要列举所有字段

# 基类方式：仅需5行代码
class IntegrationConfigSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = IntegrationConfig
        fields = BaseModelSerializer.Meta.fields + ['system_type', 'system_name']
```

**代码量减少**：约 **60-80%** 的样板代码被消除

### A.3 功能统一性

所有继承基类的组件自动获得相同的行为：

1. **组织隔离**：无需手动过滤，自动生效
2. **软删除**：删除操作自动转为软删除
3. **审计日志**：创建人、创建时间自动记录
4. **批量操作**：统一的批量删除/恢复/更新接口
5. **异常处理**：统一的异常捕获和日志记录

### A.4 可维护性提升

```python
# 示例：修改软删除逻辑只需改一处
# apps/common/models.py

class BaseModel(models.Model):
    def soft_delete(self):
        """只需修改这一处，所有子类自动生效"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by_id = get_current_user_id()
        self.save()

# 影响：IntegrationConfig、IntegrationSyncTask、IntegrationLog等
# 所有继承BaseModel的模型都自动获得新的软删除逻辑
```

### A.5 扩展性保障

添加新功能时，只需在基类中实现一次：

```python
# 示例：添加全局搜索功能
# apps/common/services/base_crud.py

class BaseCRUDService:
    def global_search(self, keyword: str) -> QuerySet:
        """新增全局搜索方法"""
        # 所有继承的服务类自动获得此功能
        return self.query(search=keyword, search_fields=self._get_search_fields())

# 影响：
# - IntegrationConfigService 自动获得 global_search()
# - IntegrationSyncService 自动获得 global_search()
# - 未来新增的 Service 类也会自动获得此功能
```

---

**文档版本**: v3.0 (基于公共基类架构重构)
**最后更新**: 2026-01-15
**维护者**: GZEAMS开发团队
**审核状态**: 待审核
