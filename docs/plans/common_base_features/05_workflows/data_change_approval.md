# 已审核单据编辑后的数据流转设计

## 设计概述

本文档定义了已审核完成的单据在被编辑后的数据流转机制，确保变更的审批可控、历史可追溯、数据一致性。

### 核心策略

| 决策点 | 选择方案 | 说明 |
|--------|----------|------|
| 数据处理 | **变更记录** | 原始数据不变，创建增量变更记录，审批通过后才应用 |
| 展示逻辑 | **对比显示** | 同时显示原始数据和新数据，差异高亮标注 |
| 编辑范围 | **全部字段可编辑** | 所有字段都可以编辑，但需要走完整的变更审批流程 |
| 生效时机 | **审批完成生效** | 最后一个审批节点通过后，变更立即生效，替换原始数据 |
| 并发处理 | **独占模式** | 同一单据同时只能有一个变更草稿，必须完成或取消后才能创建新的变更 |
| 驳回处理 | **保留归档** | 驳回后变更记录保留为「已驳回」状态归档，重新编辑会创建新的变更记录 |

---

## 1. 架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    变更记录架构                                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     DynamicData（原始数据）                      │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │ id: uuid-001                                            │    │    │
│  │  │ business_object: ProcurementRequest                      │    │    │
│  │  │ custom_fields: {amount: 100000, reason: "原采购理由"}   │    │    │
│  │  │ status: "completed"                                      │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↑                                          │
│                              │ has_one                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              DataChangeRecord（变更记录）                        │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │ id: uuid-002                                            │    │    │
│  │  │ original_data: {amount: 100000, ...}                    │    │    │
│  │  │ changed_fields: {amount: 150000, reason: "新理由"}      │    │    │
│  │  │ change_type: "update"                                    │    │    │
│  │  │ status: "pending_approval"                              │    │    │
│  │  │ workflow_instance_id: uuid-wf-01                         │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              ↑                                          │
│                              │ has_many                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │           DataChangeLog（字段级变更明细）                         │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │ field_code: "amount"                                    │    │    │
│  │  │ old_value: 100000                                       │    │    │
│  │  │ new_value: 150000                                       │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  │  ┌─────────────────────────────────────────────────────────┐    │    │
│  │  │ field_code: "reason"                                    │    │    │
│  │  │ old_value: "原采购理由"                                 │    │    │
│  │  │ new_value: "新理由"                                     │    │    │
│  │  └─────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.2 状态流转图

```
                    ┌─────────────┐
                    │    draft    │  创建变更记录
                    └──────┬──────┘
                           │ submit_for_approval()
                           ▼
                ┌─────────────────────┐
                │ pending_approval    │  审批中（独占锁定）
                └──────────┬──────────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
         approve        reject        cancel
            │              │              │
            ▼              ▼              ▼
    ┌─────────────┐ ┌─────────┐ ┌─────────┐
    │   approved  │ │ rejected│ │cancelled│
    └──────┬──────┘ └────┬────┘ └────┬────┘
           │             │            │
      apply()       保留归档      释放锁定
           │
           ▼
    ┌─────────────┐
    │   applied   │  变更已生效
    └─────────────┘
```

---

## 2. 数据变更审批数据模型定义

### 2.1 DataChangeRecord 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_object | ForeignKey | BusinessObject | 业务对象 |
| original_data_id | UUID | indexed | 原始数据ID |
| change_type | string | max=20 | update/correction/adjustment/cancellation |
| status | string | max=20 | draft/pending_approval/approved/rejected/cancelled/applied |
| original_data | JSONB | NOT NULL | 原始数据快照 |
| changed_fields | JSONB | NOT NULL | 变更字段 |
| new_data | JSONB | NOT NULL | 变更后完整数据 |
| change_reason | text | NOT NULL | 变更原因 |
| attachments | JSONB | default=list | 附件 |
| workflow_instance | ForeignKey | WorkflowInstance | nullable |
| applied_at | datetime | nullable | 生效时间 |
| applied_by | ForeignKey | User | nullable | 生效操作人 |
| is_locked | boolean | default=True | 是否锁定 |

### 2.2 DataChangeLog 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| change_record | ForeignKey | DataChangeRecord | 变更记录 |
| field_code | string | max=100 | 字段编码 |
| field_name | string | max=200 | 字段名称 |
| action | string | max=20 | field_changed/field_added/field_removed |
| old_value | JSONB | nullable | 原始值 |
| new_value | JSONB | nullable | 新值 |
| old_value_display | text | blank=True | 原始值展示 |
| new_value_display | text | blank=True | 新值展示 |
| is_critical | boolean | default=False | 是否关键字段 |

---

## 3. 数据模型设计

### 3.3 DataChangeRecord 模型实现

```python
# backend/apps/system/models.py

class DataChangeRecord(BaseModel):
    """
    数据变更记录模型

    记录已审核单据的变更请求，支持：
    - 审批流程集成
    - 变更历史追溯
    - 原始数据与变更数据对比
    """

    CHANGE_TYPE_CHOICES = [
        ('update', '更新'),
        ('correction', '更正'),
        ('adjustment', '调整'),
        ('cancellation', '作废'),
    ]

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('pending_approval', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('cancelled', '已取消'),
        ('applied', '已生效'),
    ]

    # 关联原始数据
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='change_records',
        verbose_name='业务对象'
    )
    original_data_id = models.IntegerField(
        verbose_name='原始数据ID'
    )

    # 变更类型
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        default='update',
        verbose_name='变更类型'
    )

    # 变更状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 原始数据快照（审批时用于对比）
    original_data = models.JSONField(
        default=dict,
        verbose_name='原始数据快照'
    )

    # 变更字段（只包含发生变更的字段）
    changed_fields = models.JSONField(
        default=dict,
        verbose_name='变更字段'
    )

    # 完整的新数据（用于审批通过后替换）
    new_data = models.JSONField(
        default=dict,
        verbose_name='变更后完整数据'
    )

    # 变更原因（必填）
    change_reason = models.TextField(
        verbose_name='变更原因'
    )

    # 附件（支持上传说明文档）
    attachments = models.JSONField(
        default=list,
        blank=True,
        verbose_name='附件'
    )

    # 工作流集成
    workflow_instance = models.ForeignKey(
        'workflows.WorkflowInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_records',
        verbose_name='工作流实例'
    )

    # 生效时间（审批通过后设置）
    applied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='生效时间'
    )

    # 生效执行人
    applied_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applied_changes',
        verbose_name='生效操作人'
    )

    # 独占锁（确保同一单据只有一个待审批变更）
    is_locked = models.BooleanField(
        default=True,
        verbose_name='是否锁定'
    )

    class Meta:
        db_table = 'system_data_change_record'
        verbose_name = '数据变更记录'
        verbose_name_plural = '数据变更记录'
        indexes = [
            models.Index(fields=['business_object', 'original_data_id']),
            models.Index(fields=['status']),
            models.Index(fields=['is_locked']),
            models.Index(fields=['created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['business_object', 'original_data_id'],
                condition=Q(status__in=['draft', 'pending_approval']),
                name='unique_pending_change'
            )
        ]

    def __str__(self):
        return f"{self.business_object.name} 变更记录 #{self.id}"
```

### 3.4 DataChangeLog 模型实现

```python
# backend/apps/system/models.py

class DataChangeLog(BaseModel):
    """
    数据变更明细日志

    记录字段级别的变更，用于：
    - 变更历史追溯
    - 审计报告生成
    - 前端差异对比展示
    """

    ACTION_CHOICES = [
        ('field_changed', '字段变更'),
        ('field_added', '字段新增'),
        ('field_removed', '字段删除'),
    ]

    # 关联变更记录
    change_record = models.ForeignKey(
        'DataChangeRecord',
        on_delete=models.CASCADE,
        related_name='change_logs',
        verbose_name='变更记录'
    )

    # 字段信息
    field_code = models.CharField(
        max_length=100,
        verbose_name='字段编码'
    )
    field_name = models.CharField(
        max_length=200,
        verbose_name='字段名称'
    )

    # 变更动作
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='field_changed',
        verbose_name='变更动作'
    )

    # 变更值
    old_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='原始值'
    )
    new_value = models.JSONField(
        null=True,
        blank=True,
        verbose_name='新值'
    )

    # 值的文本表示（用于展示）
    old_value_display = models.TextField(
        blank=True,
        verbose_name='原始值展示'
    )
    new_value_display = models.TextField(
        blank=True,
        verbose_name='新值展示'
    )

    # 是否关键字段（影响审批流程）
    is_critical = models.BooleanField(
        default=False,
        verbose_name='是否关键字段'
    )

    class Meta:
        db_table = 'system_data_change_log'
        verbose_name = '数据变更明细'
        verbose_name_plural = '数据变更明细'
        indexes = [
            models.Index(fields=['change_record']),
            models.Index(fields=['field_code']),
            models.Index(fields=['is_critical']),
        ]

    def __str__(self):
        return f"{self.field_name}: {self.old_value_display} → {self.new_value_display}"
```

---

## 4. 服务层设计

### 4.1 DataChangeService

```python
# backend/apps/system/services/data_change.py

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.utils import timezone
from apps.system.models import (
    BusinessObject,
    DynamicData,
    DataChangeRecord,
    DataChangeLog,
    FieldDefinition
)
from apps.workflows.models import WorkflowInstance, WorkflowDefinition
from apps.workflows.services import WorkflowService


class DataChangeService:
    """
    数据变更服务

    处理已审核单据的编辑变更流程：
    - 创建变更记录
    - 生成字段级变更明细
    - 启动审批流程
    - 应用变更到原始数据
    """

    def __init__(self, business_object_code: str):
        """
        初始化服务

        Args:
            business_object_code: 业务对象编码
        """
        self.business_object = BusinessObject.objects.get(
            code=business_object_code,
            is_active=True
        )
        self.field_definitions = FieldDefinition.objects.filter(
            business_object=self.business_object,
            is_active=True
        )

    @transaction.atomic
    def create_change_record(
        self,
        original_data_id: int,
        new_data: Dict[str, Any],
        change_reason: str,
        change_type: str = 'update',
        user=None,
        attachments: List[str] = None
    ) -> DataChangeRecord:
        """
        创建变更记录

        Args:
            original_data_id: 原始数据ID
            new_data: 变更后的完整数据
            change_reason: 变更原因
            change_type: 变更类型
            user: 操作用户
            attachments: 附件列表

        Returns:
            DataChangeRecord: 创建的变更记录
        """
        # 1. 获取原始数据
        try:
            original_data = DynamicData.objects.get(
                id=original_data_id,
                business_object=self.business_object
            )
        except DynamicData.DoesNotExist:
            raise ValidationError(f"原始数据不存在: {original_data_id}")

        # 2. 检查是否已有待审批的变更记录（独占模式）
        pending_change = DataChangeRecord.objects.filter(
            business_object=self.business_object,
            original_data_id=original_data_id,
            status__in=['draft', 'pending_approval']
        ).first()

        if pending_change:
            raise ValidationError(
                f"该单据已有待审批的变更记录（#{pending_change.id}），"
                f"请等待当前变更完成后再创建新变更"
            )

        # 3. 计算变更字段
        original_fields = original_data.custom_fields or {}
        changed_fields = self._calculate_changes(
            original_fields,
            new_data
        )

        if not changed_fields:
            raise ValidationError("没有检测到任何变更")

        # 4. 创建变更记录
        change_record = DataChangeRecord.objects.create(
            business_object=self.business_object,
            original_data_id=original_data_id,
            change_type=change_type,
            status='draft',
            original_data=original_fields,
            changed_fields=changed_fields,
            new_data=new_data,
            change_reason=change_reason,
            attachments=attachments or [],
            created_by=user
        )

        # 5. 生成字段级变更明细
        self._create_change_logs(change_record, original_fields, new_data)

        return change_record

    def _calculate_changes(
        self,
        original: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算变更字段

        只返回发生变更的字段
        """
        changes = {}

        for key, new_value in new_data.items():
            old_value = original.get(key)

            # 值不同或原始不存在该字段
            if old_value != new_value:
                changes[key] = new_value

        return changes

    def _create_change_logs(
        self,
        change_record: DataChangeRecord,
        original_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ) -> None:
        """
        创建字段级变更明细
        """
        changed_fields = change_record.changed_fields
        field_def_map = {
            fd.code: fd
            for fd in self.field_definitions
        }

        for field_code, new_value in changed_fields.items():
            field_def = field_def_map.get(field_code)
            if not field_def:
                continue

            old_value = original_data.get(field_code)

            # 生成展示值
            old_display = self._format_display_value(field_def, old_value)
            new_display = self._format_display_value(field_def, new_value)

            DataChangeLog.objects.create(
                change_record=change_record,
                field_code=field_code,
                field_name=field_def.name,
                action='field_changed',
                old_value=old_value,
                new_value=new_value,
                old_value_display=old_display,
                new_value_display=new_display,
                is_critical=field_def.is_required or field_def.is_readonly
            )

    def _format_display_value(
        self,
        field_def: FieldDefinition,
        value: Any
    ) -> str:
        """
        格式化字段值的展示文本
        """
        if value is None:
            return '(空)'

        if field_def.field_type == 'reference':
            # 引用字段，显示关联对象的名称
            return self._get_reference_display(value)

        if field_def.field_type == 'user':
            return self._get_user_display(value)

        if field_def.field_type == 'department':
            return self._get_department_display(value)

        if field_def.field_type == 'file':
            if isinstance(value, list):
                return f"{len(value)} 个文件"
            return value

        if field_def.field_type == 'select':
            options = field_def.options or {}
            return options.get(str(value), value)

        return str(value)

    @transaction.atomic
    def submit_for_approval(
        self,
        change_record_id: int,
        user=None
    ) -> Dict[str, Any]:
        """
        提交变更审批

        Args:
            change_record_id: 变更记录ID
            user: 操作用户

        Returns:
            审批信息
        """
        change_record = DataChangeRecord.objects.get(id=change_record_id)

        if change_record.status != 'draft':
            raise ValidationError(f"只有草稿状态的变更记录可以提交审批")

        # 启动工作流
        workflow_service = WorkflowService()
        workflow_result = workflow_service.start_workflow(
            business_object_code=self.business_object.code,
            business_data_id=change_record_id,
            workflow_type='data_change',
            user=user
        )

        # 更新变更记录状态
        change_record.status = 'pending_approval'
        change_record.workflow_instance_id = workflow_result['instance_id']
        change_record.save()

        return {
            'change_record_id': change_record.id,
            'workflow_instance_id': workflow_result['instance_id'],
            'current_node': workflow_result['current_node'],
            'status': 'pending_approval'
        }

    @transaction.atomic
    def apply_change(
        self,
        change_record_id: int,
        user=None
    ) -> DynamicData:
        """
        应用变更到原始数据

        审批通过后调用
        """
        change_record = DataChangeRecord.objects.get(id=change_record_id)

        if change_record.status != 'approved':
            raise ValidationError("只有已通过审批的变更记录才能应用")

        # 获取原始数据
        original_data = DynamicData.objects.get(
            id=change_record.original_data_id
        )

        # 备份原始数据到历史表
        self._archive_original_data(original_data, change_record)

        # 应用新数据
        original_data.custom_fields = change_record.new_data
        original_data.updated_by = user
        original_data.save()

        # 更新变更记录
        change_record.status = 'applied'
        change_record.applied_at = timezone.now()
        change_record.applied_by = user
        change_record.is_locked = False
        change_record.save()

        return original_data

    def _archive_original_data(
        self,
        original_data: DynamicData,
        change_record: DataChangeRecord
    ) -> None:
        """
        归档原始数据
        """
        # 可以创建一个 DataChangeHistory 模型存储完整历史
        # 或使用现有的审计日志机制
        pass

    def get_change_diff(
        self,
        change_record_id: int
    ) -> Dict[str, Any]:
        """
        获取变更对比数据

        用于前端差异展示
        """
        change_record = DataChangeRecord.objects.get(id=change_record_id)
        change_logs = change_record.change_logs.all()

        return {
            'change_record': {
                'id': change_record.id,
                'change_type': change_record.change_type,
                'status': change_record.status,
                'change_reason': change_record.change_reason,
                'created_at': change_record.created_at.isoformat(),
                'created_by': {
                    'id': change_record.created_by.id,
                    'name': change_record.created_by.username
                } if change_record.created_by else None
            },
            'original_data': change_record.original_data,
            'new_data': change_record.new_data,
            'changes': [
                {
                    'field_code': log.field_code,
                    'field_name': log.field_name,
                    'old_value': log.old_value,
                    'new_value': log.new_value,
                    'old_display': log.old_value_display,
                    'new_display': log.new_value_display,
                    'is_critical': log.is_critical
                }
                for log in change_logs
            ]
        }
```

---

## 5. API 接口设计

### 5.1 创建变更记录

**接口**：`POST /api/dynamic/{code}/{id}/change/`

**请求体**：
```json
{
  "new_data": {
    "request_title": "变更后的标题",
    "request_amount": 150000,
    "request_reason": "变更后的理由"
  },
  "change_reason": "市场价格调整，需要增加采购金额",
  "change_type": "adjustment",
  "attachments": ["file_id_1", "file_id_2"]
}
```

**响应**：
```json
{
  "success": true,
  "data": {
    "change_record_id": "uuid-002",
    "status": "draft",
    "changed_fields": {
      "request_amount": 150000,
      "request_reason": "变更后的理由"
    },
    "message": "变更记录创建成功，请提交审批"
  }
}
```

### 5.2 提交变更审批

**接口**：`POST /api/dynamic/{code}/change/{change_id}/submit/`

**响应**：
```json
{
  "success": true,
  "data": {
    "change_record_id": "uuid-002",
    "workflow_instance_id": "uuid-wf-01",
    "current_node": "node_change_review",
    "current_node_name": "变更审批",
    "status": "pending_approval"
  }
}
```

### 5.3 获取变更对比

**接口**：`GET /api/dynamic/{code}/change/{change_id}/diff/`

**响应**：
```json
{
  "success": true,
  "data": {
    "change_record": {
      "id": "uuid-002",
      "change_type": "adjustment",
      "status": "pending_approval",
      "change_reason": "市场价格调整，需要增加采购金额",
      "created_at": "2026-01-15T14:30:00Z"
    },
    "changes": [
      {
        "field_code": "request_amount",
        "field_name": "申请金额",
        "old_value": 100000,
        "new_value": 150000,
        "old_display": "100,000.00",
        "new_display": "150,000.00",
        "is_critical": true
      },
      {
        "field_code": "request_reason",
        "field_name": "申请事由",
        "old_value": "原采购理由",
        "new_value": "变更后的理由",
        "old_display": "原采购理由",
        "new_display": "变更后的理由",
        "is_critical": true
      }
    ]
  }
}
```

### 5.4 获取单据的变更历史

**接口**：`GET /api/dynamic/{code}/{id}/changes/`

**响应**：
```json
{
  "success": true,
  "data": {
    "total": 2,
    "changes": [
      {
        "id": "uuid-002",
        "change_type": "adjustment",
        "status": "pending_approval",
        "change_reason": "市场价格调整",
        "created_at": "2026-01-15T14:30:00Z",
        "created_by": "张三",
        "applied_at": null
      },
      {
        "id": "uuid-001",
        "change_type": "update",
        "status": "applied",
        "change_reason": "初次修正",
        "created_at": "2026-01-10T10:00:00Z",
        "created_by": "李四",
        "applied_at": "2026-01-10T15:30:00Z"
      }
    ]
  }
}
```

---

## 6. 工作流集成

### 6.1 变更审批流程定义

```python
# 变更审批工作流配置示例

CHANGE_APPROVAL_WORKFLOW = {
    'code': 'data_change_approval',
    'name': '数据变更审批流程',
    'business_object': 'DataChange',
    'definition': {
        'nodes': [
            {
                'id': 'node_start',
                'type': 'start',
                'text': '发起变更',
                'x': 100,
                'y': 100
            },
            {
                'id': 'node_dept_review',
                'type': 'approval',
                'text': '部门主管审批',
                'x': 300,
                'y': 100,
                'assignee_type': 'department_head',
                'approve_rule': 'any_one',
                'timeout': 72
            },
            {
                'id': 'node_data_owner_review',
                'type': 'approval',
                'text': '数据管理员审批',
                'x': 500,
                'y': 100,
                'assignee_type': 'role',
                'assignee_value': 'data_admin',
                'approve_rule': 'any_one'
            },
            {
                'id': 'node_auto_apply',
                'type': 'auto_task',
                'text': '自动应用变更',
                'x': 700,
                'y': 100,
                'handler': 'apply_data_change'
            },
            {
                'id': 'node_end',
                'type': 'end',
                'text': '流程结束',
                'x': 900,
                'y': 100
            },
            {
                'id': 'node_rejected',
                'type': 'end',
                'text': '已驳回',
                'x': 500,
                'y': 250,
                'end_type': 'rejected'
            }
        ],
        'edges': [
            {
                'id': 'edge_1',
                'source': 'node_start',
                'target': 'node_dept_review',
                'type': 'default'
            },
            {
                'id': 'edge_2',
                'source': 'node_dept_review',
                'target': 'node_data_owner_review',
                'type': 'approve'
            },
            {
                'id': 'edge_3',
                'source': 'node_dept_review',
                'target': 'node_rejected',
                'type': 'reject'
            },
            {
                'id': 'edge_4',
                'source': 'node_data_owner_review',
                'target': 'node_auto_apply',
                'type': 'approve'
            },
            {
                'id': 'edge_5',
                'source': 'node_data_owner_review',
                'target': 'node_rejected',
                'type': 'reject'
            },
            {
                'id': 'edge_6',
                'source': 'node_auto_apply',
                'target': 'node_end',
                'type': 'default'
            }
        ]
    }
}
```

### 6.2 工作流回调处理

```python
# backend/apps/workflows/handlers.py

from typing import Dict, Any
from apps.system.services.data_change import DataChangeService


class WorkflowCallbackHandler:
    """
    工作流回调处理器

    处理工作流节点完成后的回调操作
    """

    @staticmethod
    def on_change_approved(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        变更审批通过后的回调

        Args:
            context: 工作流上下文
                - business_data_id: 变更记录ID
                - workflow_instance_id: 工作流实例ID

        Returns:
            处理结果
        """
        change_record_id = context['business_data_id']

        # 应用变更到原始数据
        service = DataChangeService('DataChange')
        try:
            updated_data = service.apply_change(
                change_record_id=change_record_id,
                user=context.get('user')
            )

            return {
                'success': True,
                'message': '变更已应用',
                'data_id': updated_data.id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'应用变更失败: {str(e)}'
            }

    @staticmethod
    def on_change_rejected(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        变更审批驳回后的回调

        将变更记录状态标记为已驳回，保留归档
        """
        from apps.system.models import DataChangeRecord

        change_record_id = context['business_data_id']

        change_record = DataChangeRecord.objects.get(id=change_record_id)
        change_record.status = 'rejected'
        change_record.is_locked = False  # 释放锁，允许创建新变更
        change_record.save()

        return {
            'success': True,
            'message': '变更已驳回，记录已归档'
        }

    @staticmethod
    def on_change_cancelled(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        变更取消后的回调
        """
        from apps.system.models import DataChangeRecord

        change_record_id = context['business_data_id']

        change_record = DataChangeRecord.objects.get(id=change_record_id)
        change_record.status = 'cancelled'
        change_record.is_locked = False
        change_record.save()

        return {
            'success': True,
            'message': '变更已取消'
        }


# 注册回调处理器
WORKFLOW_CALLBACKS = {
    'data_change_approval': {
        'on_completed': WorkflowCallbackHandler.on_change_approved,
        'on_rejected': WorkflowCallbackHandler.on_change_rejected,
        'on_cancelled': WorkflowCallbackHandler.on_change_cancelled
    }
}
```

---

## 7. 前端组件设计

### 7.1 变更对比组件

**文件路径**：`frontend/src/components/common/ChangeDiffViewer.vue`

```vue
<template>
  <div class="change-diff-viewer">
    <el-alert
      v-if="hasCriticalChanges"
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        该变更包含关键字段修改，请仔细核对
      </template>
    </el-alert>

    <div class="diff-header">
      <h4>变更对比</h4>
      <div class="change-meta">
        <el-tag :type="statusType">{{ changeRecord.status }}</el-tag>
        <span class="change-time">{{ formatTime(changeRecord.created_at) }}</span>
        <span class="change-user">{{ changeRecord.created_by?.name }}</span>
      </div>
    </div>

    <div class="diff-reason">
      <label>变更原因：</label>
      <p>{{ changeRecord.change_reason }}</p>
    </div>

    <div class="diff-list">
      <div
        v-for="change in changes"
        :key="change.field_code"
        class="diff-item"
        :class="{ 'is-critical': change.is_critical }"
      >
        <div class="field-name">
          <el-icon v-if="change.is_critical" class="critical-icon">
            <Warning />
          </el-icon>
          {{ change.field_name }}
        </div>

        <div class="field-values">
          <div class="value-old">
            <span class="value-label">原值</span>
            <del class="value-text">{{ change.old_display || '(空)' }}</del>
          </div>

          <el-icon class="arrow-icon"><Right /></el-icon>

          <div class="value-new">
            <span class="value-label">新值</span>
            <ins class="value-text">{{ change.new_display || '(空)' }}</ins>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Warning, Right } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  changeRecord: {
    type: Object,
    required: true
  },
  changes: {
    type: Array,
    required: true
  }
})

const hasCriticalChanges = computed(() => {
  return props.changes.some(c => c.is_critical)
})

const statusType = computed(() => {
  const statusMap = {
    'draft': 'info',
    'pending_approval': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'applied': 'success'
  }
  return statusMap[props.changeRecord.status] || 'info'
})

const formatTime = (time) => formatDateTime(time)
</script>
```

---

## 8. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/system/models.py` | DataChangeRecord、DataChangeLog 模型 |
| `backend/apps/system/services/data_change.py` | DataChangeService 服务 |
| `backend/apps/workflows/handlers.py` | WorkflowCallbackHandler 回调处理 |
| `backend/apps/common/viewsets/data_change.py` | DataChangeViewSet 视图 |
| `frontend/src/components/common/ChangeDiffViewer.vue` | 变更对比组件 |
| `frontend/src/components/common/ChangeForm.vue` | 变更表单组件 |
| `frontend/src/api/data-change.js` | 变更API接口封装 |

---

## 9. 迁移指南

### 9.1 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations system

# 执行迁移
python manage.py migrate
```

### 9.2 创建变更审批流程

```python
from apps.workflows.models import WorkflowDefinition

# 创建变更审批流程定义
WorkflowDefinition.objects.create(
    code='data_change_approval',
    name='数据变更审批流程',
    business_object=BusinessObject.objects.get(code='DataChange'),
    definition=CHANGE_APPROVAL_WORKFLOW['definition'],
    is_active=True,
    version=1
)
```
