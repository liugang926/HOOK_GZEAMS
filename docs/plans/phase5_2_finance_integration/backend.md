# Phase 5.2: 财务凭证集成 - 后端实现

## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤 |

---

## 1. 功能概述与业务场景

### 1.1 业务背景

财务凭证集成模块负责将固定资产相关业务操作自动转换为财务凭证,并推送到ERP财务系统,实现资产全生命周期与财务核算的无缝集成。

### 1.2 核心业务场景

| 业务类型 | 凭证类型 | 会计分录示例 | 触发时机 |
|---------|---------|-------------|---------|
| 资产购入 | 记账凭证 | 借：固定资产 借：应交税费-进项税 贷：应付账款/银行存款 | 资产验收入库后 |
| 资产折旧 | 记账凭证 | 借：管理费用/销售费用/制造费用-折旧费 贷：累计折旧 | 月末折旧计提后 |
| 资产处置 | 记账凭证 | 借：固定资产清理 借：累计折旧 贷：固定资产 | 资产报废/出售时 |
| 资产调拨 | 转账凭证 | 借：固定资产-调入部门 贷：固定资产-调出部门 | 跨组织调拨完成 |

### 1.3 业务价值

- **自动化**：自动生成凭证,减少人工操作和错误
- **一致性**：保证资产账与财务账的一致性
- **合规性**：满足企业会计准则和审计要求
- **可追溯**：完整记录业务到凭证的映射关系

---

## 2. 用户角色与权限

### 2.1 角色定义

| 角色 | 说明 | 主要权限 |
|------|------|---------|
| 财务主管 | 负责凭证审核 | 查看、审核、驳回凭证 |
| 财务专员 | 负责凭证管理 | 查看、生成、修改、推送凭证 |
| 资产管理员 | 资产业务操作 | 查看关联的资产凭证 |
| 系统管理员 | 系统配置维护 | 凭证模板配置、科目映射配置 |

### 2.2 权限矩阵

| 操作 | 财务主管 | 财务专员 | 资产管理员 | 系统管理员 |
|------|---------|---------|-----------|-----------|
| 查看凭证列表 | ✅ | ✅ | ✅ (仅关联) | ✅ |
| 生成凭证 | ❌ | ✅ | ❌ | ❌ |
| 修改凭证(未推送) | ✅ | ✅ | ❌ | ❌ |
| 审核凭证 | ✅ | ❌ | ❌ | ❌ |
| 推送ERP | ✅ | ✅ | ❌ | ❌ |
| 配置模板 | ❌ | ❌ | ❌ | ✅ |
| 配置科目映射 | ❌ | ❌ | ❌ | ✅ |

---

## 3. 公共模型引用

### 3.1 后端基类引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一 CRUD 方法 |

### 3.2 代码结构

```
backend/apps/finance/
├── __init__.py
├── models.py                 # 继承 BaseModel
│   ├── VoucherTemplate       # 凭证模板
│   ├── Voucher               # 凭证记录
│   ├── VoucherEntry          # 凭证分录
│   ├── AccountMapping        # 科目映射
│   └── IntegrationLog        # 集成日志
├── serializers.py            # 继承 BaseModelSerializer
├── viewsets.py               # 继承 BaseModelViewSetWithBatch
├── filters.py                # 继承 BaseModelFilter
├── services/
│   ├── __init__.py
│   ├── base_crud.py          # 继承 BaseCRUDService
│   ├── voucher_service.py    # 凭证业务服务
│   └── erp_integration.py    # ERP集成服务
└── urls.py
```

---

## 4. 数据模型设计

### 4.1 VoucherTemplate(凭证模板)

**继承**: `BaseModel`

```python
from apps.common.models import BaseModel
from django.db import models

class VoucherTemplate(BaseModel):
    """凭证模板配置"""

    # 基础字段
    template_code = models.CharField(max_length=50, unique=True, verbose_name='模板代码')
    template_name = models.CharField(max_length=200, verbose_name='模板名称')

    # 业务关联
    business_type = models.CharField(max_length=50, verbose_name='业务类型',
        choices=[
            ('asset_purchase', '资产购入'),
            ('asset_depreciation', '资产折旧'),
            ('asset_disposal', '资产处置'),
            ('asset_transfer', '资产调拨'),
        ])

    # 凭证配置
    voucher_type = models.CharField(max_length=20, verbose_name='凭证类型',
        choices=[
            ('record', '记账凭证'),
            ('receipt', '收款凭证'),
            ('payment', '付款凭证'),
            ('transfer', '转账凭证'),
        ])

    # 分录模板(JSONB字段,存储在custom_fields中)
    # 结构：[{"direction": "debit/credit", "account_code": "科目代码",
    #         "amount_formula": "金额公式", "description_template": "摘要模板"}]
    entry_templates = models.JSONField(default=dict, verbose_name='分录模板')

    # 是否启用
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'finance_voucher_template'
        verbose_name = '凭证模板'
        verbose_name_plural = '凭证模板'
        ordering = ['template_code']
```

### 4.2 Voucher(凭证记录)

**继承**: `BaseModel`

```python
class Voucher(BaseModel):
    """财务凭证记录"""

    # 凭证标识
    voucher_no = models.CharField(max_length=50, unique=True, verbose_name='凭证号')
    voucher_date = models.DateField(verbose_name='凭证日期')

    # 业务关联
    business_type = models.CharField(max_length=50, verbose_name='业务类型')
    business_id = models.CharField(max_length=100, verbose_name='业务单据ID')
    business_no = models.CharField(max_length=100, verbose_name='业务单据号')

    # 凭证类型
    voucher_type = models.CharField(max_length=20, verbose_name='凭证类型',
        choices=[
            ('record', '记账凭证'),
            ('receipt', '收款凭证'),
            ('payment', '付款凭证'),
            ('transfer', '转账凭证'),
        ])

    # 金额信息
    debit_amount = models.DecimalField(max_digits=18, decimal_places=2,
                                      default=0, verbose_name='借方金额')
    credit_amount = models.DecimalField(max_digits=18, decimal_places=2,
                                       default=0, verbose_name='贷方金额')

    # 分录数量
    entry_count = models.IntegerField(default=0, verbose_name='分录数量')

    # 推送状态
    push_status = models.CharField(max_length=20, verbose_name='推送状态',
        choices=[
            ('pending', '待推送'),
            ('pushed', '已推送'),
            ('failed', '推送失败'),
            ('acknowledged', '已确认'),
        ],
        default='pending')

    erp_voucher_no = models.CharField(max_length=100, blank=True, null=True,
                                     verbose_name='ERP凭证号')
    push_time = models.DateTimeField(blank=True, null=True, verbose_name='推送时间')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')

    # 审核状态
    approval_status = models.CharField(max_length=20, verbose_name='审核状态',
        choices=[
            ('draft', '草稿'),
            ('submitted', '已提交'),
            ('approved', '已审核'),
            ('rejected', '已驳回'),
        ],
        default='draft')

    approved_by = models.ForeignKey('accounts.User', on=models.SET_NULL,
                                   null=True, blank=True,
                                   related_name='approved_vouchers',
                                   verbose_name='审核人')
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name='审核时间')
    approval_remarks = models.TextField(blank=True, null=True, verbose_name='审核备注')

    class Meta:
        db_table = 'finance_voucher'
        verbose_name = '财务凭证'
        verbose_name_plural = '财务凭证'
        ordering = ['-voucher_date', '-created_at']
        indexes = [
            models.Index(fields=['business_type', 'business_id']),
            models.Index(fields=['voucher_date']),
            models.Index(fields=['push_status']),
            models.Index(fields=['approval_status']),
        ]
```

### 4.3 VoucherEntry(凭证分录)

**继承**: `BaseModel`

```python
class VoucherEntry(BaseModel):
    """凭证分录明细"""

    # 关联凭证
    voucher = models.ForeignKey('Voucher', on=models.CASCADE,
                               related_name='entries', verbose_name='凭证')

    # 分录序号
    line_no = models.IntegerField(verbose_name='分录序号')

    # 方向
    direction = models.CharField(max_length=10, verbose_name='方向',
        choices=[
            ('debit', '借方'),
            ('credit', '贷方'),
        ])

    # 科目信息
    account_code = models.CharField(max_length=50, verbose_name='科目代码')
    account_name = models.CharField(max_length=200, verbose_name='科目名称')

    # 金额
    amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name='金额')

    # 摘要
    description = models.TextField(verbose_name='摘要')

    # 辅助核算(JSONB)
    auxiliary = models.JSONField(default=dict, verbose_name='辅助核算')
    # 结构：{"department": "部门", "project": "项目", "asset": "资产"}

    class Meta:
        db_table = 'finance_voucher_entry'
        verbose_name = '凭证分录'
        verbose_name_plural = '凭证分录'
        ordering = ['voucher', 'line_no']
        unique_together = [['voucher', 'line_no']]
```

### 4.4 AccountMapping(科目映射)

**继承**: `BaseModel`

```python
class AccountMapping(BaseModel):
    """资产科目映射配置"""

    # 映射类型
    mapping_type = models.CharField(max_length=50, verbose_name='映射类型',
        choices=[
            ('asset_category', '资产分类'),
            ('department', '部门'),
            ('depreciation', '折旧费用'),
        ])

    # 映射键
    mapping_key = models.CharField(max_length=100, verbose_name='映射键')
    # 例如：资产分类ID、部门ID

    # 科目信息
    account_code = models.CharField(max_length=50, verbose_name='科目代码')
    account_name = models.CharField(max_length=200, verbose_name='科目名称')

    # 辅助核算
    auxiliary_type = models.CharField(max_length=50, blank=True, verbose_name='辅助核算类型')

    # 是否启用
    is_active = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'finance_account_mapping'
        verbose_name = '科目映射'
        verbose_name_plural = '科目映射'
        unique_together = [['mapping_type', 'mapping_key', 'account_code']]
        indexes = [
            models.Index(fields=['mapping_type', 'mapping_key']),
        ]
```

### 4.5 IntegrationLog(集成日志)

**继承**: `BaseModel`

```python
class IntegrationLog(BaseModel):
    """ERP集成日志"""

    # 日志类型
    log_type = models.CharField(max_length=50, verbose_name='日志类型',
        choices=[
            ('voucher_push', '凭证推送'),
            ('voucher_query', '凭证查询'),
            ('account_sync', '科目同步'),
        ])

    # 关联对象
    voucher = models.ForeignKey('Voucher', on_models.SET_NULL,
                               null=True, blank=True,
                               related_name='integration_logs',
                               verbose_name='关联凭证')

    # 请求信息
    request_url = models.TextField(verbose_name='请求URL')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_headers = models.JSONField(verbose_name='请求头')
    request_body = models.JSONField(verbose_name='请求体')

    # 响应信息
    response_status = models.IntegerField(verbose_name='响应状态码')
    response_headers = models.JSONField(verbose_name='响应头')
    response_body = models.JSONField(verbose_name='响应体')

    # 执行信息
    execution_time = models.FloatField(verbose_name='执行时长(秒)')
    status = models.CharField(max_length=20, verbose_name='状态',
        choices=[
            ('success', '成功'),
            ('failed', '失败'),
            ('timeout', '超时'),
        ])

    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')

    # 重试信息
    retry_count = models.IntegerField(default=0, verbose_name='重试次数')
    last_retry_at = models.DateTimeField(blank=True, null=True, verbose_name='最后重试时间')

    class Meta:
        db_table = 'finance_integration_log'
        verbose_name = '集成日志'
        verbose_name_plural = '集成日志'
        ordering = ['-created_at']
```

---

## 5. API接口设计

### 5.1 统一响应格式

所有API接口均遵循以下统一响应格式：

#### 成功响应格式

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "code": "VT001",
        "name": "资产购入凭证模板",
        "organization": {...},
        "created_at": "2026-01-15T10:30:00Z",
        "created_by": {...}
    }
}
```

#### 列表响应格式（分页）

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/finance/voucher-templates/?page=2",
        "previous": null,
        "results": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "VT001",
                "name": "资产购入凭证模板",
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
            "template_code": ["该字段不能为空"],
            "business_type": ["选择一个有效的业务类型"]
        }
    }
}
```

### 5.2 统一错误码定义

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
| `VOUCHER_GENERATION_ERROR` | 400 | 凭证生成失败 |
| `ERP_CONNECTION_ERROR` | 503 | ERP连接失败 |
| `VOUCHER_APPROVAL_ERROR` | 400 | 凭证审核失败 |

### 5.3 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

所有财务凭证相关的模型（Voucher、VoucherEntry、VoucherTemplate、AccountMapping、IntegrationLog）均继承自BaseModel，因此自动获得以下标准端点：

**凭证模板标准端点**：
- `GET /api/finance/voucher-templates/` - 列表查询（分页、过滤、搜索）
- `GET /api/finance/voucher-templates/{id}/` - 获取单条记录
- `POST /api/finance/voucher-templates/` - 创建新记录
- `PUT /api/finance/voucher-templates/{id}/` - 完整更新
- `PATCH /api/finance/voucher-templates/{id}/` - 部分更新
- `DELETE /api/finance/voucher-templates/{id}/` - 软删除
- `GET /api/finance/voucher-templates/deleted/` - 查看已删除记录
- `POST /api/finance/voucher-templates/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/finance/voucher-templates/batch-delete/` - 批量软删除
- `POST /api/finance/voucher-templates/batch-restore/` - 批量恢复
- `POST /api/finance/voucher-templates/batch-update/` - 批量更新

**凭证记录标准端点**：
- `GET /api/finance/vouchers/` - 列表查询（分页、过滤、搜索）
- `GET /api/finance/vouchers/{id}/` - 获取单条记录
- `POST /api/finance/vouchers/` - 创建新记录
- `PUT /api/finance/vouchers/{id}/` - 完整更新
- `PATCH /api/finance/vouchers/{id}/` - 部分更新
- `DELETE /api/finance/vouchers/{id}/` - 软删除
- `GET /api/finance/vouchers/deleted/` - 查看已删除记录
- `POST /api/finance/vouchers/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/finance/vouchers/batch-delete/` - 批量软删除
- `POST /api/finance/vouchers/batch-restore/` - 批量恢复
- `POST /api/finance/vouchers/batch-update/` - 批量更新

**科目映射标准端点**：
- `GET /api/finance/account-mappings/` - 列表查询
- `GET /api/finance/account-mappings/{id}/` - 获取单条记录
- 以及其他标准CRUD和批量操作端点

**集成日志标准端点**：
- `GET /api/finance/integration-logs/` - 列表查询（支持按时间范围、状态、凭证过滤）
- 以及其他标准CRUD和批量操作端点

### 5.4 批量操作 API 规范

#### 5.4.1 批量删除凭证

```http
POST /api/finance/vouchers/batch-delete/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001",
        "550e8400-e29b-41d4-a716-446655440002"
    ]
}
```

**响应（全部成功）**

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

**响应（部分失败）**

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
            "error": "凭证已推送，不能删除"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440002",
            "success": true
        }
    ]
}
```

#### 5.4.2 批量推送凭证

```http
POST /api/finance/vouchers/batch-push/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ]
}
```

**响应格式与批量删除相同**

#### 5.4.3 批量更新凭证状态

```http
POST /api/finance/vouchers/batch-update/
Content-Type: application/json

{
    "ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "550e8400-e29b-41d4-a716-446655440001"
    ],
    "data": {
        "status": "approved",
        "approval_remarks": "批量审核通过"
    }
}
```

**响应格式与批量删除相同**

### 5.2 自定义端点

#### 5.2.1 凭证生成

```http
POST /api/finance/vouchers/generate/
Content-Type: application/json

{
    "business_type": "asset_purchase",
    "business_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**响应**:
```json
{
    "success": true,
    "message": "凭证生成成功",
    "data": {
        "id": "voucher-uuid",
        "voucher_no": "PZ20240115001",
        "entry_count": 3,
        "debit_amount": 15000.00,
        "credit_amount": 15000.00
    }
}
```

**错误响应示例**：
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "凭证数据验证失败",
        "details": {
            "business_id": ["资产不存在"]
        }
    }
}
```

#### 5.2.2 推送ERP

```http
POST /api/finance/vouchers/{id}/push/
```

**响应**:
```json
{
    "success": true,
    "message": "凭证推送成功",
    "data": {
        "erp_voucher_no": "ERP-PZ20240115001",
        "push_time": "2026-01-15T10:30:00Z"
    }
}
```

#### 5.2.3 批量推送

```http
POST /api/finance/vouchers/batch-push/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

**响应**:
```json
{
    "success": true,
    "message": "批量推送完成",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": false, "error": "ERP连接失败"}
    ]
}
```

#### 5.2.4 凭证审核

```http
POST /api/finance/vouchers/{id}/approve/
Content-Type: application/json

{
    "action": "approve",
    "remarks": "审核通过"
}
```

#### 5.2.5 科目映射查询

```http
GET /api/finance/account-mappings/query/
Query: ?mapping_type=asset_category&mapping_key=category-id
```

---

## 6. 错误处理机制

### 6.1 凭证推送异常处理

#### ERP连接失败
- **异常场景**：网络中断、ERP服务不可用、认证失败
- **处理策略**：
  - 自动重试机制（最多3次，间隔30秒）
  - 降级处理：本地存储凭证数据，待网络恢复后重试
  - 告警通知：通过邮件/短信通知管理员
  - 详细日志记录：完整的请求/响应/错误信息

#### 凭证格式验证失败
- **异常场景**：数据类型错误、字段缺失、格式不符合ERP要求
- **处理策略**：
  - 实时验证：生成凭证时进行格式校验
  - 错误反馈：返回具体的错误字段和修改建议
  - 自动修复：对常见格式问题进行自动修正（如日期格式）
  - 审批流程：允许在特殊情况下手动审批跳过验证

#### 科目映射失败
- **异常场景**：科目不存在、科目代码无效、映射规则冲突
- **处理策略**：
  - 映射检查：生成凭证前验证科目有效性
  - 默认科目：配置默认科目作为后备方案
  - 人工干预：提供手动选择科目的选项
  - 映射日志：记录所有映射操作便于排查

### 6.2 补偿机制

#### 推送失败记录待重试队列
- **失败记录存储**：所有推送失败的凭证记录到 `Voucher` 表的 `push_status='failed'`
- **重试队列**：使用 Celery 定时任务每5分钟扫描失败记录并重试
- **重试策略**：
  - 指数退避：每次重试间隔递增（30s, 60s, 120s）
  - 最大重试次数：3次
  - 重试间隔：超过时间限制的凭证优先重试

#### 支持手动重新推送
- **手动重试接口**：
  ```http
  POST /api/finance/vouchers/{id}/retry-push/
  ```
- **批量重试**：
  ```http
  POST /api/finance/vouchers/batch-retry/
  {
    "ids": ["uuid1", "uuid2"],
    "force_retry": false  // 是否强制重试（忽略验证）
  }
  ```
- **重试记录**：每次重试都记录到 `IntegrationLog` 中

#### 完整的操作日志
- **日志记录范围**：
  - 凭证生成操作
  - 推送尝试记录
  - 重试操作
  - 错误详细信息
  - 用户操作历史
- **日志查询**：
  - 按时间范围查询
  - 按状态筛选（成功/失败/重试中）
  - 按操作人筛选
  - 导出功能

### 6.3 异常处理实现

#### 服务层异常处理
```python
# apps/assets/services/erp_integration.py

from django.core.exceptions import ValidationError
from apps.common.handlers.exceptions import BaseExceptionHandler
from apps.finance.models import Voucher, IntegrationLog

class ERPIntegrationService(BaseCRUDService):
    """ERP集成服务 - 继承公共基类并添加异常处理"""

    def push_voucher_to_erp(self, voucher_id: str, force_retry: bool = False):
        """推送凭证到ERP"""
        voucher = self.get(voucher_id)

        try:
            # 1. 验证凭证状态
            if not force_retry and voucher.push_status == 'pushed':
                raise ValueError("凭证已推送，无需重复推送")

            # 2. 构建ERP请求数据
            erp_request = self._build_erp_request(voucher)

            # 3. 发送请求到ERP
            erp_response = self._call_erp_api(erp_request)

            # 4. 处理响应
            self._handle_erp_response(voucher, erp_response)

            return {
                'success': True,
                'erp_voucher_no': erp_response.get('voucher_no'),
                'message': '凭证推送成功'
            }

        except ValidationError as e:
            # 验证错误
            voucher.push_status = 'failed'
            voucher.error_message = f"数据验证失败: {str(e)}"
            voucher.save()

            # 记录日志
            self._log_integration(voucher, 'voucher_push', str(e), 400)

            raise ValueError(f"凭证数据验证失败: {str(e)}")

        except ConnectionError as e:
            # 连接错误
            if voucher.push_status != 'failed':
                voucher.push_status = 'failed'
                voucher.error_message = f"ERP连接失败: {str(e)}"
                voucher.save()

            # 加入重试队列
            self._schedule_retry(voucher_id)

            raise ConnectionError(f"无法连接到ERP系统: {str(e)}")

        except Exception as e:
            # 其他错误
            voucher.push_status = 'failed'
            voucher.error_message = f"推送失败: {str(e)}"
            voucher.save()

            # 记录日志
            self._log_integration(voucher, 'voucher_push', str(e), 500)

            raise

    def _schedule_retry(self, voucher_id: str):
        """安排重试"""
        from celery import shared_task

        @shared_task(bind=True, max_retries=3)
        def retry_push_voucher(self, voucher_id):
            try:
                self.push_voucher_to_erp(voucher_id)
            except Exception as e:
                if self.request.retries < self.max_retries:
                    raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
                raise

        retry_push_voucher.delay(voucher_id)

    def _log_integration(self, voucher, log_type, error_message, status_code):
        """记录集成日志"""
        IntegrationLog.objects.create(
            voucher=voucher,
            log_type=log_type,
            request_url=f"{settings.ERP_API_BASE_URL}/vouchers",
            request_method="POST",
            request_body=self._build_erp_request(voucher),
            response_status=status_code,
            response_body={"error": error_message},
            execution_time=0,
            status='failed' if status_code >= 400 else 'success',
            error_message=error_message
        )
```

#### API层异常处理
```python
# apps/assets/views.py (扩展)

from rest_framework.exceptions import ValidationError
from apps.common.handlers.exceptions import BaseExceptionHandler

class AssetDepreciationViewSet(BaseModelViewSetWithBatch):
    """扩展ViewSet添加异常处理"""

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核通过折旧"""
        try:
            voucher_no = request.data.get('voucher_no')
            depreciation = self.service.approve_depreciation(pk, request.user, voucher_no)

            # 尝试推送ERP（如果配置了自动推送）
            if settings.ERP_AUTO_PUSH_ENABLED:
                try:
                    from apps.assets.services.erp_integration import ERPIntegrationService
                    erp_service = ERPIntegrationService()
                    erp_service.push_voucher_to_erp(str(depreciation.voucher.id))
                except Exception as e:
                    # ERP推送失败不影响折旧审核
                    logger.warning(f"ERP推送失败，但折旧已审核: {str(e)}")

            serializer = self.get_serializer(depreciation)
            return Response(serializer.data)

        except ValueError as e:
            # 业务逻辑错误
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # 其他错误
            logger.error(f"审核折旧时发生错误: {str(e)}", exc_info=True)
            return Response(
                {'detail': '系统内部错误'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

#### Celery任务异常处理
```python
# apps/assets/tasks/depreciation_tasks.py

from celery import shared_task
from celery.exceptions import Retry
from django.utils import timezone
from apps.assets.services.depreciation_service import DepreciationService
from apps.finance.models import Voucher
from notifications.services import NotificationService

logger = get_task_logger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def calculate_monthly_depreciation_task(self, period=None):
    """月度折旧计算任务 - 增强异常处理"""
    try:
        if not period:
            period = timezone.now().strftime('%Y-%m')

        service = DepreciationService()
        result = service.batch_calculate_period(period)

        # 检查是否有失败的资产
        if result['failed'] > 0:
            # 发送告警通知
            notification_service = NotificationService()
            notification_service.send_system_notification(
                title="折旧计算部分失败",
                content=f"期间 {period} 的折旧计算完成，但 {result['failed']} 项资产计算失败",
                level='warning'
            )

        logger.info(f"折旧计算完成: {result}")
        return result

    except ConnectionError as e:
        # 数据库连接错误，重试
        logger.error(f"数据库连接错误: {str(e)}")
        raise self.retry(exc=e, countdown=30)

    except Exception as e:
        # 其他错误
        logger.error(f"折旧计算失败: {str(e)}", exc_info=True)

        # 发送严重错误通知
        notification_service = NotificationService()
        notification_service.send_system_notification(
            title="折旧计算严重错误",
            content=f"期间 {period} 的折旧计算失败: {str(e)}",
            level='error'
        )

        # 不重试严重错误
        if self.request.retries >= self.max_retries:
            raise

        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
```

---

## 7. 前端组件设计

### 6.1 公共组件引用

#### 页面组件
- **列表页**: 使用 `BaseListPage` + `useListPage`
- **表单页**: 使用 `BaseFormPage` + `useFormPage`
- **详情页**: 使用 `BaseDetailPage`

#### 布局组件
- **标签页**: 使用 `DynamicTabs`(参考 `tab_configuration.md`)
- **区块容器**: 使用 `SectionBlock`(参考 `section_block_layout.md`)

#### 列表字段显示管理(推荐)
- **列配置**: 使用 `ColumnManager` + `useColumnConfig`(参考 `list_column_configuration.md`)

### 6.2 前端代码结构

```
frontend/src/views/finance/
├── VoucherList.vue           # 凭证列表页
├── VoucherDetail.vue         # 凭证详情页
├── VoucherForm.vue           # 凭证编辑页
├── TemplateList.vue          # 模板列表页
├── TemplateForm.vue          # 模板配置页
└── AccountMapping.vue        # 科目映射配置

frontend/src/api/
└── finance.js                # 财务模块API
```

### 6.3 核心页面设计

#### 6.3.1 VoucherList.vue(凭证列表)

**功能**:
- 凭证列表展示(支持多条件筛选)
- 批量推送操作
- 凭证状态筛选(草稿/已审核/已推送)
- 业务类型筛选
- 推送状态筛选

**列配置**:
```javascript
const columns = [
    { prop: 'voucher_no', label: '凭证号', width: 150 },
    { prop: 'voucher_date', label: '凭证日期', width: 120 },
    { prop: 'business_type_display', label: '业务类型', width: 120 },
    { prop: 'business_no', label: '业务单据号', width: 150 },
    { prop: 'debit_amount', label: '借方金额', width: 120, align: 'right' },
    { prop: 'credit_amount', label: '贷方金额', width: 120, align: 'right' },
    { prop: 'approval_status_display', label: '审核状态', width: 100 },
    { prop: 'push_status_display', label: '推送状态', width: 100 },
    { prop: 'actions', label: '操作', width: 200, slot: true, fixed: 'right' }
]
```

#### 6.3.2 VoucherDetail.vue(凭证详情)

**功能**:
- 凭证基本信息展示
- 分录明细表格
- 推送历史记录
- 操作按钮(审核/推送/查看ERP凭证)

**布局**:
```vue
<template>
    <BaseDetailPage :fetch-method="fetchVoucher" :id="voucherId">
        <!-- 基本信息区块 -->
        <SectionBlock title="基本信息">
            <el-descriptions :column="3" border>
                <el-descriptions-item label="凭证号">{{ voucher.voucher_no }}</el-descriptions-item>
                <el-descriptions-item label="凭证日期">{{ voucher.voucher_date }}</el-descriptions-item>
                <el-descriptions-item label="凭证类型">{{ voucher.voucher_type_display }}</el-descriptions-item>
                <el-descriptions-item label="业务类型">{{ voucher.business_type_display }}</el-descriptions-item>
                <el-descriptions-item label="业务单据号">{{ voucher.business_no }}</el-descriptions-item>
                <el-descriptions-item label="借方金额">{{ voucher.debit_amount }}</el-descriptions-item>
            </el-descriptions>
        </SectionBlock>

        <!-- 分录明细区块 -->
        <SectionBlock title="分录明细">
            <el-table :data="voucher.entries" border>
                <el-table-column prop="line_no" label="序号" width="80" />
                <el-table-column prop="direction_display" label="方向" width="100" />
                <el-table-column prop="account_code" label="科目代码" width="150" />
                <el-table-column prop="account_name" label="科目名称" width="200" />
                <el-table-column prop="amount" label="金额" width="150" align="right" />
                <el-table-column prop="description" label="摘要" min-width="300" />
            </el-table>
        </SectionBlock>

        <!-- 推送历史 -->
        <SectionBlock title="推送历史">
            <el-timeline>
                <el-timeline-item v-for="log in pushLogs" :key="log.id">
                    {{ log.created_at }} - {{ log.status_display }} - {{ log.remarks }}
                </el-timeline-item>
            </el-timeline>
        </SectionBlock>
    </BaseDetailPage>
</template>
```

---

## 7. 测试用例

### 7.1 模型测试

```python
from apps.finance.models import Voucher, VoucherTemplate, VoucherEntry
from apps.finance.services.voucher_service import VoucherService

def test_voucher_template_creation():
    """测试凭证模板创建"""
    template = VoucherTemplate.objects.create(
        template_code='ASSET_PURCHASE',
        template_name='资产购入凭证模板',
        business_type='asset_purchase',
        voucher_type='record',
        entry_templates=[{
            "direction": "debit",
            "account_code": "1601",
            "amount_formula": "purchase_price",
            "description_template": "购入{{asset_name}}"
        }]
    )
    assert template.template_code == 'ASSET_PURCHASE'
    assert template.organization is not None  # 组织隔离

def test_voucher_generation():
    """测试凭证生成"""
    service = VoucherService()
    voucher = service.generate_voucher(
        business_type='asset_purchase',
        business_id='asset-uuid'
    )
    assert voucher.voucher_no.startswith('PZ')
    assert voucher.debit_amount == voucher.credit_amount  # 借贷平衡

def test_voucher_organization_isolation():
    """测试组织隔离"""
    org1_vouchers = Voucher.objects.filter(organization_id=org1_id)
    org2_vouchers = Voucher.objects.filter(organization_id=org2_id)
    assert org1_vouchers.count() != org2_vouchers.count()
```

### 7.2 API测试

```python
from rest_framework.test import APITestCase

class VoucherAPITest(APITestCase):
    """凭证API测试"""

    def test_generate_voucher(self):
        """测试生成凭证API"""
        url = '/api/finance/vouchers/generate/'
        data = {
            'business_type': 'asset_purchase',
            'business_id': 'asset-uuid'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])

    def test_push_voucher(self):
        """测试推送凭证API"""
        voucher = Voucher.objects.create(...)
        url = f'/api/finance/vouchers/{voucher.id}/push/'
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['push_status'], 'pushed')

    def test_batch_push(self):
        """测试批量推送API"""
        url = '/api/finance/vouchers/batch-push/'
        data = {'ids': [voucher1.id, voucher2.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.data['data'])
```

### 7.3 服务层测试

```python
def test_voucher_service_calculate_balance():
    """测试借贷平衡计算"""
    service = VoucherService()

    # 资产购入凭证
    entries = [
        {'direction': 'debit', 'amount': 15000},
        {'direction': 'debit', 'amount': 1950},
        {'direction': 'credit', 'amount': 16950}
    ]

    is_balanced = service.check_balance(entries)
    assert is_balanced is True

def test_account_mapping_service():
    """测试科目映射服务"""
    from apps.finance.services.account_mapping_service import AccountMappingService

    service = AccountMappingService()
    account = service.get_account(
        mapping_type='asset_category',
        mapping_key='computer-category-id'
    )

    assert account is not None
    assert account['account_code'] == '1602'  # 固定资产-通用设备
```

---

## 8. 实施计划

| 阶段 | 任务 | 工作量 | 依赖 |
|------|------|-------|------|
| 1 | 数据模型实现 | 2天 | 无 |
| 2 | 凭证模板配置界面 | 3天 | 模型完成 |
| 3 | 凭证生成服务 | 3天 | 模板配置完成 |
| 4 | 科目映射服务 | 2天 | 无 |
| 5 | ERP集成接口 | 3天 | 凭证生成完成 |
| 6 | 前端界面开发 | 4天 | 后端API完成 |
| 7 | 测试与调优 | 2天 | 全部完成 |

---

## 9. 相关文档

| 文档 | 说明 |
|------|------|
| [prd_writing_guide.md](../../common_base_features/prd_writing_guide.md) | PRD编写指南 |
| [backend.md](../../common_base_features/backend.md) | 后端公共模型 |
| [api.md](../../common_base_features/api.md) | API规范 |
| [frontend.md](../../common_base_features/frontend.md) | 前端公共组件 |
| [phase5_0_integration_framework/overview.md](../phase5_0_integration_framework/overview.md) | 集成框架总览 |
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