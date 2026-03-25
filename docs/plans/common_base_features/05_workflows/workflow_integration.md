# 工作流集成架构

## 任务概述

为低代码平台添加工作流集成能力，实现元数据驱动的审批流程管理，支持字段级权限控制、动态表单配置、流程可视化设计等核心功能。

---

## 1. 设计背景

### 1.1 核心需求

基于 LogicFlow 可视化流程设计器，实现以下目标：

- **元数据驱动字段权限**：工作流节点可配置每个字段的可见性、可编辑性、必填性
- **动态表单绑定**：表单字段权限根据流程实例当前节点自动调整
- **流程状态驱动业务状态**：工作流实例状态自动控制业务对象生命周期
- **审批意见管理**：支持流程节点审批意见记录与展示

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    工作流集成架构                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  配置层（Configuration）                                         │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐     │
│  │WorkflowDef   │  │FieldDefinition│  │  PageLayout      │     │
│  │流程定义JSON   │  │ wf_*权限字段  │  │ workflow_actions │     │
│  └──────────────┘  └───────────────┘  └──────────────────┘     │
│         ↓                   ↓                    ↓               │
│  运行时层（Runtime）                                              │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐     │
│  │WorkflowInst  │→│  WorkflowTask  │→│DynamicForm       │     │
│  │流程实例状态   │  │  待办任务      │  │ 字段权限动态渲染  │     │
│  └──────────────┘  └───────────────┘  └──────────────────┘     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 工作流集成数据模型定义

### 2.1 WorkflowDefinition 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | string | max=200 | 流程名称 |
| code | string | max=50, unique | 流程编码 |
| business_object_code | string | max=50 | 关联业务对象 |
| definition | JSONB | NOT NULL | LogicFlow流程定义JSON |
| version | integer | default=1 | 版本号 |
| is_active | boolean | default=True | 是否启用 |

### 2.2 WorkflowInstance 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| definition | ForeignKey | WorkflowDefinition | 流程定义 |
| business_data_id | UUID | indexed | 业务数据ID |
| status | string | max=20 | running/completed/cancelled |
| current_node_id | string | max=100 | 当前节点ID |
| initiator_id | UUID | indexed | 发起人ID |

### 2.3 WorkflowTask 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| instance | ForeignKey | WorkflowInstance | 流程实例 |
| node_id | string | max=100 | 节点ID |
| assignee_id | UUID | indexed | 处理人ID |
| status | string | max=20 | pending/approved/rejected |
| comment | text | nullable | 审批意见 |

### 2.4 FieldPermission (工作流扩展) 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| node_id | string | max=100 | 节点ID |
| field_code | string | max=50 | 字段编码 |
| permission | string | max=20 | read/write/hidden |
| required | boolean | default=False | 是否必填 |

---

## 3. 数据模型扩展

### 3.1 FieldDefinition 模型扩展

为支持工作流字段级权限控制，需添加以下字段：

```python
# backend/apps/system/models.py

class FieldDefinition(BaseModel):
    # ... 现有字段 ...

    # 工作流字段权限配置
    wf_visible = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='工作流可见性配置',
        help_text='格式: {"node_id_1": true, "node_id_2": false}'
    )
    wf_editable = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='工作流可编辑配置',
        help_text='格式: {"node_id_1": true, "node_id_2": false}'
    )
    wf_required = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='工作流必填配置',
        help_text='格式: {"node_id_1": true, "node_id_2": false}'
    )
```

**配置说明**：

- `wf_visible`: 控制字段在指定节点的可见性
- `wf_editable`: 控制字段在指定节点的可编辑性
- `wf_required`: 控制字段在指定节点的必填性
- 键名为流程节点ID（从 LogicFlow 定义中获取），值为布尔值

### 3.2 PageLayout 模型扩展

添加工作流操作按钮配置：

```python
# backend/apps/system/models.py

class PageLayout(BaseModel):
    # ... 现有字段 ...

    # 工作流操作配置
    workflow_actions = models.JSONField(
        default=list,
        blank=True,
        verbose_name='工作流操作配置',
        help_text='格式: [{"action": "approve", "label": "同意", "nodes": ["node_id_1"]}]'
    )
```

**配置格式**：

```json
[
  {
    "action": "approve",
    "label": "同意",
    "icon": "Check",
    "type": "success",
    "nodes": ["node_approve_1", "node_approve_2"],
    "require_comment": false,
    "comment_placeholder": ""
  },
  {
    "action": "reject",
    "label": "驳回",
    "icon": "Close",
    "type": "danger",
    "nodes": ["node_approve_1", "node_approve_2"],
    "require_comment": true,
    "comment_placeholder": "请输入驳回原因"
  },
  {
    "action": "return",
    "label": "退回",
    "icon": "Back",
    "type": "warning",
    "nodes": ["node_approve_2"],
    "require_comment": true,
    "comment_placeholder": "请输入退回原因",
    "allow_return_to": ["node_approve_1", "node_start"]
  }
]
```

---

## 4. 配置示例

### 4.1 采购申请单工作流配置

#### 业务场景

采购申请单需经过三级审批流程：
1. 部门主管审批（10万以下）
2. 财务审批（10万-50万）
3. 总经理审批（50万以上）

#### Step 1: 定义 BusinessObject

```python
from apps.system.models import BusinessObject

# 创建采购申请单业务对象
procurement_bo = BusinessObject.objects.create(
    code='ProcurementRequest',
    name='采购申请单',
    description='采购审批流程',
    enable_workflow=True,
    enable_version=True,
    is_active=True
)
```

#### Step 2: 配置 FieldDefinition（含工作流权限）

```python
from apps.system.models import FieldDefinition

# 1. 基本信息字段（所有节点可见，提交后只读）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='request_title',
    name='申请标题',
    field_type='text',
    is_required=True,
    is_readonly=False,
    is_visible=True,
    # 工作流权限配置
    wf_visible={
        'node_start': True,           # 发起节点可见
        'node_dept_review': True,     # 部门审批可见
        'node_finance_review': True,  # 财务审批可见
        'node_general_review': True,  # 总经理审批可见
        'node_end': True              # 结束节点可见
    },
    wf_editable={
        'node_start': True,           # 仅发起节点可编辑
        'node_dept_review': False,    # 审批节点只读
        'node_finance_review': False,
        'node_general_review': False,
        'node_end': False
    },
    wf_required={
        'node_start': True            # 发起节点必填
    },
    sort_order=1
)

# 2. 申请金额字段（不同审批节点有不同权限）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='request_amount',
    name='申请金额（元）',
    field_type='decimal',
    is_required=True,
    max_digits=12,
    decimal_places=2,
    min_value=0,
    # 工作流权限配置
    wf_visible={
        'node_start': True,
        'node_dept_review': True,
        'node_finance_review': True,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_start': True,           # 发起时可编辑
        'node_dept_review': False,    # 审批节点只读
        'node_finance_review': False,
        'node_general_review': False,
        'node_end': False
    },
    wf_required={
        'node_start': True
    },
    sort_order=2
)

# 3. 采购明细子表（发起和财务审批可编辑）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='procurement_items',
    name='采购明细',
    field_type='sub_table',
    is_required=True,
    # 子表字段配置
    options={
        'columns': [
            {'code': 'item_name', 'name': '品名', 'type': 'text', 'required': True},
            {'code': 'specification', 'name': '规格型号', 'type': 'text'},
            {'code': 'quantity', 'name': '数量', 'type': 'number', 'required': True},
            {'code': 'unit_price', 'name': '单价', 'type': 'decimal', 'required': True},
            {'code': 'total_price', 'name': '小计', 'type': 'formula', 'formula': 'quantity * unit_price'}
        ]
    },
    # 工作流权限配置
    wf_visible={
        'node_start': True,
        'node_dept_review': True,
        'node_finance_review': True,   # 财务需核对明细
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_start': True,            # 发起时可编辑
        'node_dept_review': False,
        'node_finance_review': True,   # 财务审批时可修正
        'node_general_review': False,
        'node_end': False
    },
    wf_required={
        'node_start': True,
        'node_finance_review': True    # 财务审批时必填
    },
    sort_order=3
)

# 4. 申请事由（多行文本）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='request_reason',
    name='申请事由',
    field_type='textarea',
    is_required=True,
    max_length=2000,
    wf_visible={
        'node_start': True,
        'node_dept_review': True,
        'node_finance_review': True,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_start': True,
        'node_dept_review': False,
        'node_finance_review': False,
        'node_general_review': False,
        'node_end': False
    },
    wf_required={
        'node_start': True
    },
    sort_order=4
)

# 5. 附件上传（发起时必填）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='attachments',
    name='附件',
    field_type='file',
    is_required=False,
    options={
        'max_files': 10,
        'allowed_types': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png']
    },
    wf_visible={
        'node_start': True,
        'node_dept_review': True,
        'node_finance_review': True,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_start': True,
        'node_dept_review': False,
        'node_finance_review': False,
        'node_general_review': False,
        'node_end': False
    },
    wf_required={
        'node_start': False
    },
    sort_order=5
)

# 6. 部门审批意见（仅部门审批节点可编辑）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='dept_comment',
    name='部门审批意见',
    field_type='textarea',
    is_required=False,
    max_length=1000,
    wf_visible={
        'node_start': False,           # 发起时不可见
        'node_dept_review': True,      # 部门审批时可见
        'node_finance_review': True,   # 后续节点可见（只读）
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_dept_review': True       # 仅部门审批节点可编辑
    },
    wf_required={
        'node_dept_review': True       # 部门审批必填
    },
    sort_order=6
)

# 7. 财务审批意见（仅财务审批节点可编辑）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='finance_comment',
    name='财务审批意见',
    field_type='textarea',
    is_required=False,
    max_length=1000,
    wf_visible={
        'node_dept_review': False,
        'node_finance_review': True,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_finance_review': True
    },
    wf_required={
        'node_finance_review': True
    },
    sort_order=7
)

# 8. 总经理审批意见（仅总经理审批节点可编辑）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='general_comment',
    name='总经理审批意见',
    field_type='textarea',
    is_required=False,
    max_length=1000,
    wf_visible={
        'node_dept_review': False,
        'node_finance_review': False,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_general_review': True
    },
    wf_required={
        'node_general_review': True
    },
    sort_order=8
)

# 9. 实际审批金额（财务审批填写）
FieldDefinition.objects.create(
    business_object=procurement_bo,
    code='approved_amount',
    name='核定金额',
    field_type='decimal',
    is_required=False,
    max_digits=12,
    decimal_places=2,
    wf_visible={
        'node_start': False,
        'node_dept_review': False,
        'node_finance_review': True,
        'node_general_review': True,
        'node_end': True
    },
    wf_editable={
        'node_finance_review': True
    },
    wf_required={
        'node_finance_review': True
    },
    sort_order=9
)
```

#### Step 3: 配置 PageLayout（含工作流操作）

```python
from apps.system.models import PageLayout

# 创建表单布局
form_layout = PageLayout.objects.create(
    business_object=procurement_bo,
    code='procurement_request_form',
    name='采购申请单表单',
    layout_type='form',
    layout_config={
        'sections': [
            {
                'id': 'basic_info',
                'title': '基本信息',
                'icon': 'Document',
                'fields': ['request_title', 'request_amount'],
                'column': 2
            },
            {
                'id': 'detail_info',
                'title': '采购明细',
                'icon': 'List',
                'fields': ['procurement_items'],
                'column': 1
            },
            {
                'id': 'reason_info',
                'title': '申请事由',
                'icon': 'Edit',
                'fields': ['request_reason'],
                'column': 1
            },
            {
                'id': 'attachment_info',
                'title': '附件',
                'icon': 'Paperclip',
                'fields': ['attachments'],
                'column': 1
            },
            {
                'id': 'approval_info',
                'title': '审批意见',
                'icon': 'ChatDotRound',
                'fields': ['dept_comment', 'finance_comment', 'general_comment', 'approved_amount'],
                'column': 1,
                'visible': 'workflow'  # 仅在工作流模式下显示
            }
        ]
    },
    # 工作流操作按钮配置
    workflow_actions=[
        {
            'action': 'submit',
            'label': '提交审批',
            'icon': 'Promotion',
            'type': 'primary',
            'nodes': ['node_start'],
            'require_comment': False,
            'confirm': true,
            'confirm_message': '确认提交审批？'
        },
        {
            'action': 'approve',
            'label': '同意',
            'icon': 'Select',
            'type': 'success',
            'nodes': ['node_dept_review', 'node_finance_review', 'node_general_review'],
            'require_comment': False,
            'confirm': False
        },
        {
            'action': 'reject',
            'label': '驳回',
            'icon': 'CloseBold',
            'type': 'danger',
            'nodes': ['node_dept_review', 'node_finance_review', 'node_general_review'],
            'require_comment': True,
            'comment_placeholder': '请输入驳回原因',
            'confirm': True,
            'confirm_message': '确认驳回该申请？'
        },
        {
            'action': 'return',
            'label': '退回修改',
            'icon': 'Back',
            'type': 'warning',
            'nodes': ['node_finance_review', 'node_general_review'],
            'require_comment': True,
            'comment_placeholder': '请输入退回修改原因',
            'allow_return_to': ['node_start'],  # 可退回到发起节点
            'confirm': True,
            'confirm_message': '确认退回给申请人修改？'
        }
    ]
)

# 创建列表布局
list_layout = PageLayout.objects.create(
    business_object=procurement_bo,
    code='procurement_request_list',
    name='采购申请单列表',
    layout_type='list',
    layout_config={
        'columns': [
            {'field': 'request_title', 'label': '申请标题', 'width': 200, 'fixed': True},
            {'field': 'request_amount', 'label': '申请金额', 'width': 120, 'align': 'right'},
            {'field': 'status', 'label': '状态', 'width': 100, 'align': 'center'},
            {'field': 'current_node', 'label': '当前节点', 'width': 120},
            {'field': 'created_by', 'label': '申请人', 'width': 100},
            {'field': 'created_at', 'label': '申请时间', 'width': 160}
        ],
        'page_size': 20,
        'show_row_number': True
    }
)
```

#### Step 4: 创建 WorkflowDefinition

```python
from apps.workflows.models import WorkflowDefinition
import json

# 创建流程定义（基于 LogicFlow JSON 格式）
workflow_def = WorkflowDefinition.objects.create(
    code='procurement_approval',
    name='采购审批流程',
    business_object=procurement_bo,
    definition={
        'nodes': [
            {
                'id': 'node_start',
                'type': 'start',
                'x': 100,
                'y': 100,
                'text': '发起申请'
            },
            {
                'id': 'node_dept_review',
                'type': 'approval',
                'x': 300,
                'y': 100,
                'text': '部门审批',
                'assignee_type': 'department_head',
                'approve_rule': 'any_one'  # 任一人通过即可
            },
            {
                'id': 'node_finance_review',
                'type': 'approval',
                'x': 500,
                'y': 100,
                'text': '财务审批',
                'assignee_type': 'role',
                'assignee_value': 'finance_manager',
                'approve_rule': 'any_one'
            },
            {
                'id': 'node_general_review',
                'type': 'approval',
                'x': 700,
                'y': 100,
                'text': '总经理审批',
                'assignee_type': 'role',
                'assignee_value': 'general_manager',
                'approve_rule': 'any_one',
                'condition': {  # 条件表达式：金额大于50万
                    'field': 'request_amount',
                    'operator': '>',
                    'value': 500000
                }
            },
            {
                'id': 'node_end',
                'type': 'end',
                'x': 900,
                'y': 100,
                'text': '流程结束'
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
                'target': 'node_finance_review',
                'type': 'approve'
            },
            {
                'id': 'edge_3',
                'source': 'node_finance_review',
                'target': 'node_general_review',
                'type': 'approve'
            },
            {
                'id': 'edge_4',
                'source': 'node_general_review',
                'target': 'node_end',
                'type': 'approve'
            },
            {
                'id': 'edge_5',
                'source': 'node_dept_review',
                'target': 'node_start',
                'type': 'reject'  # 驳回回发起节点
            },
            {
                'id': 'edge_6',
                'source': 'node_finance_review',
                'target': 'node_start',
                'type': 'reject'
            },
            {
                'id': 'edge_7',
                'source': 'node_finance_review',
                'target': 'node_end',
                'type': 'approve',
                'condition': {  # 金额小于等于50万，跳过总经理审批
                    'field': 'request_amount',
                    'operator': '<=',
                    'value': 500000
                }
            }
        ]
    },
    is_active=True,
    version=1
)
```

### 4.2 配置要点总结

#### 字段权限配置规则

1. **基本信息字段**：
   - 发起节点：可编辑、必填
   - 审批节点：只读

2. **审批意见字段**：
   - 发起节点：隐藏
   - 对应审批节点：可编辑、必填
   - 其他审批节点：只读

3. **条件可见字段**：
   - 根据业务条件控制显示（如：金额大于某值才显示）

#### 工作流操作配置

| 操作 | 适用节点 | 是否需意见 | 确认提示 | 说明 |
|------|---------|-----------|---------|------|
| submit | node_start | 否 | 是 | 提交审批 |
| approve | 所有审批节点 | 否 | 否 | 同意流转到下一节点 |
| reject | 所有审批节点 | 是 | 是 | 驳回到发起节点 |
| return | 指定审批节点 | 是 | 是 | 退回到指定节点修改 |

---

## 5. API 接口规范

### 5.1 获取表单配置

**接口**：`GET /api/dynamic/{code}/{id}/form-config/`

**说明**：获取业务数据实例的表单配置，包含字段权限和工作流信息

**请求参数**：
- `code`: 业务对象编码（如：ProcurementRequest）
- `id`: 数据实例ID

**响应示例**：

```json
{
  "success": true,
  "data": {
    "form_config": {
      "sections": [
        {
          "id": "basic_info",
          "title": "基本信息",
          "icon": "Document",
          "fields": ["request_title", "request_amount"],
          "column": 2
        }
      ]
    },
    "field_permissions": {
      "request_title": {
        "visible": true,
        "editable": false,
        "required": false
      },
      "request_amount": {
        "visible": true,
        "editable": false,
        "required": false
      },
      "dept_comment": {
        "visible": true,
        "editable": true,
        "required": true
      }
    },
    "workflow_info": {
      "enabled": true,
      "instance_id": "uuid-xxx",
      "current_node": "node_dept_review",
      "current_node_name": "部门审批",
      "status": "running",
      "actions": [
        {
          "action": "approve",
          "label": "同意",
          "icon": "Select",
          "type": "success",
          "require_comment": false,
          "confirm": false
        },
        {
          "action": "reject",
          "label": "驳回",
          "icon": "CloseBold",
          "type": "danger",
          "require_comment": true,
          "comment_placeholder": "请输入驳回原因",
          "confirm": true,
          "confirm_message": "确认驳回该申请？"
        }
      ]
    },
    "approval_history": [
      {
        "node_id": "node_start",
        "node_name": "发起申请",
        "assignee": {
          "id": "uuid-xxx",
          "name": "张三",
          "avatar": "/media/avatars/xxx.jpg"
        },
        "action": "submit",
        "comment": "提交采购申请",
        "created_at": "2026-01-15T10:30:00Z"
      }
    ]
  }
}
```

**后端实现**：

```python
# backend/apps/common/viewsets/metadata_driven.py

class MetadataDrivenViewSet(viewsets.ModelViewSet):
    # ... 现有代码 ...

    @action(detail=True, methods=['get'])
    def form_config(self, request, pk=None):
        """
        获取表单配置

        GET /api/dynamic/{code}/{pk}/form-config/

        返回：
        - form_config: 表单布局配置
        - field_permissions: 字段权限（基于当前工作流节点）
        - workflow_info: 工作流信息
        - approval_history: 审批历史
        """
        # 获取数据实例
        instance = self.get_object()

        # 获取表单布局
        form_layout = self.form_layout
        form_config = form_layout.layout_config if form_layout else {}

        # 获取字段权限
        field_permissions = self._get_field_permissions(instance)

        # 获取工作流信息
        workflow_info = self._get_workflow_info(instance)

        # 获取审批历史
        approval_history = self._get_approval_history(instance)

        return Response({
            'success': True,
            'data': {
                'form_config': form_config,
                'field_permissions': field_permissions,
                'workflow_info': workflow_info,
                'approval_history': approval_history
            }
        })

    def _get_field_permissions(self, instance) -> Dict:
        """
        获取字段权限（基于当前工作流节点）

        Args:
            instance: 数据实例

        Returns:
            字段权限字典
        """
        # 检查是否启用工作流
        if not self.business_object.enable_workflow:
            # 未启用工作流，使用默认权限
            return self._get_default_field_permissions()

        # 获取工作流实例
        from apps.workflows.models import WorkflowInstance

        try:
            wf_instance = WorkflowInstance.objects.get(
                business_data_id=instance.id,
                definition__business_object=self.business_object,
                status='running'
            )
            current_node = wf_instance.current_node
        except WorkflowInstance.DoesNotExist:
            # 无运行中的工作流实例
            return self._get_default_field_permissions()

        # 根据当前节点获取字段权限
        field_permissions = {}

        if self.field_definitions:
            for field_def in self.field_definitions:
                permission = {
                    'visible': self._get_field_permission(
                        field_def, current_node, 'wf_visible'
                    ),
                    'editable': self._get_field_permission(
                        field_def, current_node, 'wf_editable'
                    ),
                    'required': self._get_field_permission(
                        field_def, current_node, 'wf_required'
                    )
                }
                field_permissions[field_def.code] = permission

        return field_permissions

    def _get_field_permission(
        self,
        field_def: FieldDefinition,
        current_node: str,
        permission_type: str
    ) -> bool:
        """
        获取字段在指定节点的权限

        Args:
            field_def: 字段定义
            current_node: 当前节点ID
            permission_type: 权限类型（wf_visible/wf_editable/wf_required）

        Returns:
            权限值
        """
        # 获取权限配置
        permission_config = getattr(field_def, permission_type, {})

        if not permission_config:
            # 未配置，使用默认值
            if permission_type == 'wf_visible':
                return field_def.is_visible
            elif permission_type == 'wf_editable':
                return not field_def.is_readonly
            elif permission_type == 'wf_required':
                return field_def.is_required

        # 获取当前节点的权限
        return permission_config.get(current_node, False)

    def _get_default_field_permissions(self) -> Dict:
        """获取默认字段权限（无工作流时）"""
        field_permissions = {}

        if self.field_definitions:
            for field_def in self.field_definitions:
                permission = {
                    'visible': field_def.is_visible,
                    'editable': not field_def.is_readonly,
                    'required': field_def.is_required
                }
                field_permissions[field_def.code] = permission

        return field_permissions

    def _get_workflow_info(self, instance) -> Optional[Dict]:
        """
        获取工作流信息

        Args:
            instance: 数据实例

        Returns:
            工作流信息字典
        """
        if not self.business_object.enable_workflow:
            return None

        from apps.workflows.models import WorkflowInstance, WorkflowTask

        try:
            # 获取运行中的工作流实例
            wf_instance = WorkflowInstance.objects.get(
                business_data_id=instance.id,
                definition__business_object=self.business_object,
                status='running'
            )

            # 获取当前待办任务
            current_task = wf_instance.tasks.filter(
                status='pending'
            ).first()

            # 获取工作流操作配置
            workflow_actions = self._get_workflow_actions(wf_instance)

            return {
                'enabled': True,
                'instance_id': str(wf_instance.id),
                'definition_id': str(wf_instance.definition_id),
                'current_node': wf_instance.current_node,
                'current_node_name': current_task.node_name if current_task else '',
                'status': wf_instance.status,
                'actions': workflow_actions,
                'task_id': str(current_task.id) if current_task else None
            }

        except WorkflowInstance.DoesNotExist:
            return {
                'enabled': True,
                'status': 'not_started'
            }

    def _get_workflow_actions(self, wf_instance: WorkflowInstance) -> List[Dict]:
        """
        获取当前节点可用的工作流操作

        Args:
            wf_instance: 工作流实例

        Returns:
            操作列表
        """
        if not self.form_layout:
            return []

        # 获取工作流操作配置
        all_actions = self.form_layout.workflow_actions or []

        # 筛选当前节点可用的操作
        current_node = wf_instance.current_node
        available_actions = [
            action for action in all_actions
            if current_node in action.get('nodes', [])
        ]

        return available_actions

    def _get_approval_history(self, instance) -> List[Dict]:
        """
        获取审批历史

        Args:
            instance: 数据实例

        Returns:
            审批历史列表
        """
        if not self.business_object.enable_workflow:
            return []

        from apps.workflows.models import WorkflowInstance, WorkflowTask

        try:
            wf_instance = WorkflowInstance.objects.get(
                business_data_id=instance.id,
                definition__business_object=self.business_object
            )

            # 获取所有已完成和已驳回的任务
            tasks = wf_instance.tasks.filter(
                status__in=['completed', 'rejected']
            ).order_by('created_at')

            history = []
            for task in tasks:
                history.append({
                    'node_id': task.node_id,
                    'node_name': task.node_name,
                    'assignee': {
                        'id': str(task.assignee.id),
                        'name': task.assignee.username,
                        'avatar': getattr(task.assignee, 'avatar', None)
                    } if task.assignee else None,
                    'action': task.status,
                    'comment': task.comment,
                    'created_at': task.created_at.isoformat(),
                    'updated_at': task.updated_at.isoformat()
                })

            return history

        except WorkflowInstance.DoesNotExist:
            return []
```

### 5.2 执行工作流操作

**接口**：`POST /api/dynamic/{code}/{id}/workflow-action/`

**说明**：执行工作流操作（提交审批、同意、驳回、退回等）

**请求参数**：
```json
{
  "action": "approve",  // 操作类型：submit/approve/reject/return
  "comment": "同意该申请",  // 审批意见（某些操作必填）
  "return_to_node": "node_start"  // 退回目标节点（仅 return 操作需要）
}
```

**响应示例**：

```json
{
  "success": true,
  "message": "审批成功",
  "data": {
    "instance_id": "uuid-xxx",
    "current_node": "node_finance_review",
    "current_node_name": "财务审批",
    "status": "running",
    "next_assignees": [
      {
        "id": "uuid-xxx",
        "name": "财务经理",
        "avatar": "/media/avatars/xxx.jpg"
      }
    ]
  }
}
```

**后端实现**：

```python
# backend/apps/common/viewsets/metadata_driven.py

class MetadataDrivenViewSet(viewsets.ModelViewSet):
    # ... 现有代码 ...

    @action(detail=True, methods=['post'])
    def workflow_action(self, request, pk=None):
        """
        执行工作流操作

        POST /api/dynamic/{code}/{pk}/workflow-action/

        请求体：
        {
            "action": "approve",  // submit/approve/reject/return
            "comment": "审批意见",
            "return_to_node": "node_start"  // 仅 return 操作需要
        }

        返回：
        - instance_id: 工作流实例ID
        - current_node: 当前节点
        - status: 流程状态
        - next_assignees: 下一节点处理人列表
        """
        from apps.workflows.services import WorkflowService

        # 获取数据实例
        instance = self.get_object()

        # 获取操作参数
        action = request.data.get('action')
        comment = request.data.get('comment', '')
        return_to_node = request.data.get('return_to_node')

        # 验证操作类型
        valid_actions = ['submit', 'approve', 'reject', 'return']
        if action not in valid_actions:
            return Response({
                'success': False,
                'message': f'无效的操作类型: {action}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取工作流服务
        workflow_service = WorkflowService()

        try:
            # 执行工作流操作
            result = workflow_service.execute_action(
                instance=instance,
                user=request.user,
                action=action,
                comment=comment,
                return_to_node=return_to_node
            )

            return Response({
                'success': True,
                'message': '操作成功',
                'data': result
            })

        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'操作失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 5.3 获取工作流历史

**接口**：`GET /api/dynamic/{code}/{id}/workflow-history/`

**说明**：获取业务数据的工作流审批历史

**请求参数**：
- `code`: 业务对象编码
- `id`: 数据实例ID

**响应示例**：

```json
{
  "success": true,
  "data": {
    "workflow_instance": {
      "id": "uuid-xxx",
      "definition_name": "采购审批流程",
      "status": "running",
      "current_node": "node_finance_review",
      "started_at": "2026-01-15T10:30:00Z"
    },
    "tasks": [
      {
        "id": "uuid-xxx",
        "node_id": "node_start",
        "node_name": "发起申请",
        "assignee": {
          "id": "uuid-xxx",
          "name": "张三",
          "avatar": "/media/avatars/xxx.jpg"
        },
        "status": "completed",
        "comment": "提交采购申请",
        "created_at": "2026-01-15T10:30:00Z",
        "completed_at": "2026-01-15T10:30:05Z"
      },
      {
        "id": "uuid-xxx",
        "node_id": "node_dept_review",
        "node_name": "部门审批",
        "assignee": {
          "id": "uuid-xxx",
          "name": "李四（部门主管）",
          "avatar": "/media/avatars/xxx.jpg"
        },
        "status": "completed",
        "comment": "同意申请，采购需求合理",
        "created_at": "2026-01-15T11:00:00Z",
        "completed_at": "2026-01-15T11:05:00Z"
      },
      {
        "id": "uuid-xxx",
        "node_id": "node_finance_review",
        "node_name": "财务审批",
        "assignee": {
          "id": "uuid-xxx",
          "name": "王五（财务经理）",
          "avatar": "/media/avatars/xxx.jpg"
        },
        "status": "pending",
        "comment": "",
        "created_at": "2026-01-15T11:05:05Z",
        "completed_at": null
      }
    ],
    "flow_chart": {
      "nodes": [...],
      "edges": [...]
    }
  }
}
```

**后端实现**：

```python
# backend/apps/common/viewsets/metadata_driven.py

class MetadataDrivenViewSet(viewsets.ModelViewSet):
    # ... 现有代码 ...

    @action(detail=True, methods=['get'])
    def workflow_history(self, request, pk=None):
        """
        获取工作流历史

        GET /api/dynamic/{code}/{pk}/workflow-history/

        返回：
        - workflow_instance: 工作流实例信息
        - tasks: 任务列表（包含已完成和进行中的）
        - flow_chart: 流程图（用于前端可视化）
        """
        # 获取数据实例
        instance = self.get_object()

        # 检查是否启用工作流
        if not self.business_object.enable_workflow:
            return Response({
                'success': True,
                'data': None,
                'message': '该业务对象未启用工作流'
            })

        from apps.workflows.models import WorkflowInstance, WorkflowTask

        try:
            # 获取工作流实例
            wf_instance = WorkflowInstance.objects.get(
                business_data_id=instance.id,
                definition__business_object=self.business_object
            )

            # 获取所有任务（按时间排序）
            tasks = wf_instance.tasks.all().order_by('created_at')

            # 序列化任务列表
            tasks_data = []
            for task in tasks:
                tasks_data.append({
                    'id': str(task.id),
                    'node_id': task.node_id,
                    'node_name': task.node_name,
                    'assignee': {
                        'id': str(task.assignee.id),
                        'name': task.assignee.username,
                        'avatar': getattr(task.assignee, 'avatar', None)
                    } if task.assignee else None,
                    'status': task.status,
                    'comment': task.comment,
                    'created_at': task.created_at.isoformat(),
                    'completed_at': task.updated_at.isoformat() if task.status != 'pending' else None
                })

            # 获取流程图
            flow_chart = wf_instance.definition.definition

            return Response({
                'success': True,
                'data': {
                    'workflow_instance': {
                        'id': str(wf_instance.id),
                        'definition_name': wf_instance.definition.name,
                        'status': wf_instance.status,
                        'current_node': wf_instance.current_node,
                        'started_at': wf_instance.created_at.isoformat()
                    },
                    'tasks': tasks_data,
                    'flow_chart': flow_chart
                }
            })

        except WorkflowInstance.DoesNotExist:
            return Response({
                'success': True,
                'data': None,
                'message': '未找到工作流实例'
            })
```

---

## 6. 前端组件实现

### 6.1 工作流审批意见组件

**文件路径**：`frontend/src/components/workflow/ApprovalComment.vue`

```vue
<template>
  <div class="approval-comment">
    <!-- 审批历史时间线 -->
    <el-timeline>
      <el-timeline-item
        v-for="item in history"
        :key="item.id"
        :timestamp="formatTimestamp(item.created_at)"
        :color="getStatusColor(item.status)"
        :icon="getStatusIcon(item.status)"
      >
        <template #default>
          <div class="approval-item">
            <!-- 审批人信息 -->
            <div class="approval-header">
              <el-avatar :src="item.assignee?.avatar" :size="32">
                {{ item.assignee?.name?.charAt(0) }}
              </el-avatar>
              <div class="approval-info">
                <div class="approval-name">{{ item.assignee?.name }}</div>
                <div class="approval-node">{{ item.node_name }}</div>
              </div>
              <el-tag :type="getStatusType(item.status)" size="small">
                {{ getStatusText(item.status) }}
              </el-tag>
            </div>

            <!-- 审批意见 -->
            <div v-if="item.comment" class="approval-comment">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ item.comment }}</span>
            </div>

            <!-- 审批时间 -->
            <div v-if="item.completed_at" class="approval-time">
              完成时间: {{ formatTimestamp(item.completed_at) }}
            </div>
          </div>
        </template>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/format'

const props = defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  return formatDateTime(timestamp)
}

// 获取状态颜色
const getStatusColor = (status) => {
  const colorMap = {
    'completed': '#67c23a',
    'rejected': '#f56c6c',
    'pending': '#409eff',
    'cancelled': '#909399'
  }
  return colorMap[status] || '#409eff'
}

// 获取状态图标
const getStatusIcon = (status) => {
  // 可根据状态返回不同图标
  return null
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    'completed': 'success',
    'rejected': 'danger',
    'pending': 'primary',
    'cancelled': 'info'
  }
  return typeMap[status] || 'primary'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    'completed': '已通过',
    'rejected': '已驳回',
    'pending': '待处理',
    'cancelled': '已取消'
  }
  return textMap[status] || status
}
</script>

<style scoped lang="scss">
.approval-comment {
  padding: 20px;

  .approval-item {
    .approval-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;

      .approval-info {
        flex: 1;

        .approval-name {
          font-weight: 500;
          color: #303133;
        }

        .approval-node {
          font-size: 12px;
          color: #909399;
          margin-top: 2px;
        }
      }
    }

    .approval-comment {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 12px;
      background: #f5f7fa;
      border-radius: 4px;
      margin-top: 8px;
      font-size: 14px;
      color: #606266;

      .el-icon {
        margin-top: 2px;
        color: #909399;
      }
    }

    .approval-time {
      font-size: 12px;
      color: #909399;
      margin-top: 8px;
    }
  }
}
</style>
```

### 6.2 工作流操作按钮组件

**文件路径**：`frontend/src/components/workflow/WorkflowActions.vue`

```vue
<template>
  <div class="workflow-actions">
    <!-- 工作流操作按钮组 -->
    <el-button
      v-for="action in actions"
      :key="action.action"
      :type="action.type"
      :icon="action.icon"
      :loading="loading"
      @click="handleAction(action)"
    >
      {{ action.label }}
    </el-button>

    <!-- 审批意见弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="currentAction?.label"
      width="500px"
      :before-close="handleDialogClose"
    >
      <el-form :model="formData" label-width="80px">
        <el-form-item label="审批意见" :required="currentAction?.require_comment">
          <el-input
            v-model="formData.comment"
            type="textarea"
            :rows="4"
            :placeholder="currentAction?.comment_placeholder || '请输入审批意见'"
          />
        </el-form-item>

        <!-- 退回节点选择（仅 return 操作） -->
        <el-form-item v-if="currentAction?.action === 'return'" label="退回到" required>
          <el-select v-model="formData.return_to_node" placeholder="请选择退回节点">
            <el-option
              v-for="node in returnNodes"
              :key="node.id"
              :label="node.name"
              :value="node.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirm">
          确认{{ currentAction?.label }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 确认提示弹窗 -->
    <el-dialog
      v-model="confirmVisible"
      :title="currentAction?.label"
      width="400px"
    >
      <div class="confirm-message">
        <el-icon class="confirm-icon"><WarningFilled /></el-icon>
        <span>{{ currentAction?.confirm_message || `确认${currentAction?.label}？` }}</span>
      </div>

      <template #footer>
        <el-button @click="confirmVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleConfirmAction">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'
import { executeWorkflowAction } from '@/api/workflow'

const props = defineProps({
  actions: {
    type: Array,
    default: () => []
  },
  dataId: {
    type: [String, Number],
    required: true
  },
  businessObjectCode: {
    type: String,
    required: true
  },
  flowChart: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['success'])

// 状态
const loading = ref(false)
const dialogVisible = ref(false)
const confirmVisible = ref(false)
const currentAction = ref(null)
const formData = ref({
  comment: '',
  return_to_node: ''
})

// 计算可退回节点列表
const returnNodes = computed(() => {
  if (!currentAction.value || currentAction.value.action !== 'return') {
    return []
  }

  const allowReturnTo = currentAction.value.allow_return_to || []
  const nodes = props.flowChart.nodes || []

  return nodes
    .filter(node => allowReturnTo.includes(node.id))
    .map(node => ({
      id: node.id,
      name: node.text || node.id
    }))
})

// 处理操作按钮点击
const handleAction = (action) => {
  currentAction.value = action
  formData.value = {
    comment: '',
    return_to_node: ''
  }

  // 检查是否需要输入意见
  if (action.require_comment || action.action === 'return') {
    dialogVisible.value = true
  }
  // 检查是否需要确认
  else if (action.confirm) {
    confirmVisible.value = true
  }
  // 直接执行
  else {
    executeAction(action.action, '')
  }
}

// 处理意见弹窗确认
const handleConfirm = () => {
  // 验证必填项
  if (currentAction.value.require_comment && !formData.value.comment) {
    ElMessage.warning('请输入审批意见')
    return
  }

  if (currentAction.value.action === 'return' && !formData.value.return_to_node) {
    ElMessage.warning('请选择退回节点')
    return
  }

  dialogVisible.value = false

  // 如果需要确认提示，显示确认弹窗
  if (currentAction.value.confirm) {
    confirmVisible.value = true
  }
  // 否则直接执行
  else {
    executeAction(
      currentAction.value.action,
      formData.value.comment,
      formData.value.return_to_node
    )
  }
}

// 处理确认弹窗
const handleConfirmAction = () => {
  executeAction(
    currentAction.value.action,
    formData.value.comment,
    formData.value.return_to_node
  )
  confirmVisible.value = false
}

// 执行工作流操作
const executeAction = async (action, comment, returnToNode) => {
  loading.value = true

  try {
    const res = await executeWorkflowAction({
      businessObjectCode: props.businessObjectCode,
      dataId: props.dataId,
      action,
      comment,
      return_to_node: returnToNode
    })

    if (res.success) {
      ElMessage.success(res.message || '操作成功')
      emit('success', res.data)
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch (error) {
    ElMessage.error('操作失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 关闭弹窗
const handleDialogClose = () => {
  dialogVisible.value = false
  formData.value = {
    comment: '',
    return_to_node: ''
  }
}
</script>

<style scoped lang="scss">
.workflow-actions {
  display: flex;
  gap: 12px;
  padding: 16px 0;

  .confirm-message {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 16px;
    color: #303133;

    .confirm-icon {
      font-size: 24px;
      color: #e6a23c;
    }
  }
}
</style>
```

### 6.3 API 接口封装

**文件路径**：`frontend/src/api/workflow.js`

```javascript
import request from '@/utils/request'

/**
 * 获取表单配置（含工作流信息和字段权限）
 */
export function getFormConfig(businessObjectCode, dataId) {
  return request({
    url: `/api/dynamic/${businessObjectCode}/${dataId}/form-config/`,
    method: 'get'
  })
}

/**
 * 执行工作流操作
 */
export function executeWorkflowAction({ businessObjectCode, dataId, action, comment, return_to_node }) {
  return request({
    url: `/api/dynamic/${businessObjectCode}/${dataId}/workflow-action/`,
    method: 'post',
    data: {
      action,
      comment,
      return_to_node
    }
  })
}

/**
 * 获取工作流历史
 */
export function getWorkflowHistory(businessObjectCode, dataId) {
  return request({
    url: `/api/dynamic/${businessObjectCode}/${dataId}/workflow-history/`,
    method: 'get'
  })
}

/**
 * 获取我的待办任务列表
 */
export function getMyTasks(params) {
  return request({
    url: '/api/workflow/tasks/my/',
    method: 'get',
    params
  })
}

/**
 * 获取流程定义列表
 */
export function getWorkflowDefinitions(businessObjectCode) {
  return request({
    url: '/api/workflow/definitions/',
    method: 'get',
    params: { business_object: businessObjectCode }
  })
}
```

---

## 7. 使用示例

### 7.1 前端表单页面集成

**文件路径**：`frontend/src/views/dynamic/DynamicForm.vue`

```vue
<template>
  <div class="dynamic-form">
    <!-- 动态表单 -->
    <DynamicForm
      v-if="formConfig"
      :config="formConfig"
      :data="formData"
      :permissions="fieldPermissions"
      @submit="handleSubmit"
    />

    <!-- 工作流操作按钮 -->
    <WorkflowActions
      v-if="workflowInfo?.enabled"
      :actions="workflowInfo?.actions || []"
      :data-id="dataId"
      :business-object-code="businessObjectCode"
      :flow-chart="flowChart"
      @success="handleActionSuccess"
    />

    <!-- 审批历史 -->
    <div v-if="approvalHistory?.length" class="approval-history">
      <el-divider content-position="left">
        <el-icon><Clock /></el-icon>
        审批历史
      </el-divider>
      <ApprovalComment :history="approvalHistory" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { DynamicForm } from '@/components/engine'
import { WorkflowActions, ApprovalComment } from '@/components/workflow'
import { getFormConfig, getWorkflowHistory } from '@/api/workflow'
import { Clock } from '@element-plus/icons-vue'

const route = useRoute()
const businessObjectCode = route.params.code
const dataId = route.params.id

// 状态
const formConfig = ref(null)
const formData = ref({})
const fieldPermissions = ref({})
const workflowInfo = ref(null)
const approvalHistory = ref([])
const flowChart = ref(null)

// 加载表单配置
const loadFormConfig = async () => {
  try {
    const res = await getFormConfig(businessObjectCode, dataId)

    if (res.success) {
      formConfig.value = res.data.form_config
      fieldPermissions.value = res.data.field_permissions
      workflowInfo.value = res.data.workflow_info
      approvalHistory.value = res.data.approval_history

      // 如果有工作流，加载流程图
      if (workflowInfo.value?.enabled) {
        await loadWorkflowHistory()
      }
    }
  } catch (error) {
    console.error('加载表单配置失败:', error)
  }
}

// 加载工作流历史（含流程图）
const loadWorkflowHistory = async () => {
  try {
    const res = await getWorkflowHistory(businessObjectCode, dataId)

    if (res.success && res.data) {
      flowChart.value = res.data.flow_chart
    }
  } catch (error) {
    console.error('加载工作流历史失败:', error)
  }
}

// 处理表单提交
const handleSubmit = async (data) => {
  console.log('表单提交:', data)
}

// 处理工作流操作成功
const handleActionSuccess = (result) => {
  // 刷新表单配置和审批历史
  loadFormConfig()
}

// 初始化
onMounted(() => {
  loadFormConfig()
})
</script>

<style scoped lang="scss">
.dynamic-form {
  .approval-history {
    margin-top: 24px;
  }
}
</style>
```

---

## 8. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/system/models.py` | FieldDefinition、PageLayout 模型扩展 |
| `backend/apps/common/viewsets/metadata_driven.py` | MetadataDrivenViewSet 工作流相关接口 |
| `backend/apps/workflows/services.py` | WorkflowService 工作流执行服务 |
| `frontend/src/components/workflow/ApprovalComment.vue` | 审批意见组件 |
| `frontend/src/components/workflow/WorkflowActions.vue` | 工作流操作按钮组件 |
| `frontend/src/api/workflow.js` | 工作流API接口封装 |

---

## 9. 迁移指南

### 9.1 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations system

# 执行迁移
python manage.py migrate
```

### 9.2 现有业务对象升级

为现有业务对象启用工作流：

```python
# 1. 启用工作流
business_object = BusinessObject.objects.get(code='Asset')
business_object.enable_workflow = True
business_object.save()

# 2. 配置字段工作流权限（可选）
field_def = FieldDefinition.objects.get(code='asset_name')
field_def.wf_visible = {
    'node_start': True,
    'node_approve': True
}
field_def.wf_editable = {
    'node_start': True,
    'node_approve': False
}
field_def.save()

# 3. 配置表单工作流操作（可选）
form_layout = PageLayout.objects.get(
    business_object=business_object,
    layout_type='form'
)
form_layout.workflow_actions = [
    {
        'action': 'approve',
        'label': '同意',
        'type': 'success',
        'nodes': ['node_approve']
    }
]
form_layout.save()
```

---

## 10. 总结

本文档实现了完整的元数据驱动工作流集成方案，包括：

### 10.1 核心能力

1. **字段级权限控制**：通过 `wf_visible/wf_editable/wf_required` 配置字段在不同流程节点的权限
2. **动态表单绑定**：表单字段权限根据流程实例当前节点自动调整
3. **工作流操作配置**：通过 `PageLayout.workflow_actions` 配置流程操作按钮
4. **审批意见管理**：支持流程节点审批意见记录与展示

### 10.2 技术亮点

- **元数据驱动**：零代码配置工作流字段权限，无需编写业务代码
- **前后端分离**：前端组件化设计，后端提供标准化API接口
- **扩展性强**：支持多种审批操作（提交、同意、驳回、退回）
- **用户友好**：可视化审批历史时间线，清晰展示流程状态

### 10.3 应用场景

- 采购审批流程
- 请假审批流程
- 资产领用审批
- 费用报销审批
- 合同审批流程

通过本方案，企业可快速配置各类审批流程，实现真正的低代码工作流管理。
