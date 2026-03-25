# 从对象/主从关系布局规范

## 目录
1. [从对象概述](#1-从对象概述)
2. [FieldDefinition 从对象字段类型](#2-fielddefinition-从对象字段类型)
3. [主从表布局配置](#3-主从表布局配置)
4. [嵌套表单布局](#4-嵌套表单布局)
5. [子表组件实现](#5-子表组件实现)
6. [主从数据提交处理](#6-主从数据提交处理)
7. [嵌套表单组件实现](#7-嵌套表单组件实现)
8. [常见主从场景布局示例](#8-常见主从场景布局示例)
9. [从对象权限控制](#9-从对象权限控制)
10. [性能优化](#10-性能优化)

---

## 1. 从对象概述

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 从对象是独立的业务模型，继承 BaseModel，通过外键关联主对象。从对象布局配置在 PageLayout JSON 中作为特殊字段类型（sub_object）处理。

### 1.1 定义
**从对象（Sub-Object）**是指依附于主对象（Master Object）存在的子表/明细数据，形成一对多的主从关系。从对象不能独立存在，必须关联到主对象记录。

### 1.2 核心特征
- **依附性**：从对象记录必须关联到主对象记录（外键约束）
- **级联性**：主对象删除时，从对象记录同步软删除
- **生命周期**：从对象生命周期与主对象绑定
- **组织隔离**：从对象继承主对象的组织隔离（`organization`字段）

### 1.3 典型业务场景

| 主对象 | 从对象 | 业务场景 |
|--------|--------|----------|
| Asset（资产） | MaintenanceRecord（维护记录） | 资产维护历史管理 |
| ProcurementRequest（采购申请） | ProcurementItem（采购明细） | 采购单明细录入 |
| InventoryTask（盘点任务） | InventoryItem（盘点明细） | 盘点结果录入 |
| AssetLoan（资产借用） | LoanItem（借用明细） | 批量借用资产 |
| User（用户） | Contact（联系方式） | 用户多联系方式管理 |

### 1.4 数据模型规范

#### ✅ 从对象 Model 必须继承 BaseModel
```python
from apps.common.models import BaseModel

class ProcurementItem(BaseModel):
    """采购明细（从对象）"""
    procurement = models.ForeignKey(
        'procurement.ProcurementRequest',
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='采购申请'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='procurement_items',
        verbose_name='资产'
    )
    quantity = models.IntegerField(default=1, verbose_name='数量')
    estimated_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='预估单价'
    )
    # 自动继承字段：org, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

    class Meta:
        db_table = 'procurement_items'
        verbose_name = '采购明细'
        verbose_name_plural = '采购明细'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.procurement.code} - {self.asset.name}"

    def soft_delete(self, *args, **kwargs):
        """级联软删除：主对象删除时，从对象同步软删除"""
        super().soft_delete(*args, **kwargs)
```

---

## 2. FieldDefinition 从对象字段类型

### 2.1 扩展字段类型枚举

```python
# apps/system/models.py

class FieldDefinition(BaseModel):
    """字段定义模型"""

    FIELD_TYPE_CHOICES = [
        # 基础字段类型
        ('text', '文本'),
        ('textarea', '多行文本'),
        ('number', '数字'),
        ('decimal', '金额'),
        ('date', '日期'),
        ('datetime', '日期时间'),
        ('boolean', '布尔值'),
        ('select', '下拉选择'),
        ('radio', '单选'),
        ('checkbox', '多选'),
        ('user', '用户选择器'),
        ('department', '部门选择器'),
        ('asset', '资产选择器'),
        ('location', '位置选择器'),

        # 高级字段类型
        ('file', '文件上传'),
        ('image', '图片上传'),
        ('formula', '公式字段'),
        ('reference', '关联字段'),

        # ✅ 主从关系字段类型（新增）
        ('subtable', '子表/从对象'),  # 子表格（可编辑表格）
        ('subform', '嵌套表单'),      # 嵌套表单（内联表单）
    ]

    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        verbose_name='字段类型'
    )

    # 子表专用配置
    sub_object_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='从对象编码',
        help_text='关联的从对象编码，如 procurement_item'
    )

    sub_table_columns = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='子表列配置',
        help_text='子表显示的列及顺序配置'
    )

    allow_inline_edit = models.BooleanField(
        default=True,
        verbose_name='允许内联编辑'
    )

    show_summary_row = models.BooleanField(
        default=False,
        verbose_name='显示合计行'
    )

    summary_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name='合计字段',
        help_text='需要计算合计的字段code列表'
    )

    min_rows = models.IntegerField(
        default=0,
        verbose_name='最小行数',
        help_text='子表最少需要添加的行数'
    )

    max_rows = models.IntegerField(
        default=100,
        verbose_name='最大行数',
        help_text='子表最多允许添加的行数'
    )

    # 嵌套表单专用配置
    form_layout_code = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='表单布局编码',
        help_text='嵌套表单使用的布局配置编码'
    )

    allow_multiple = models.BooleanField(
        default=True,
        verbose_name='允许多条记录'
    )

    class Meta:
        db_table = 'system_field_definitions'
        verbose_name = '字段定义'
        verbose_name_plural = '字段定义'
```

### 2.2 子表列配置示例

```json
{
  "columns": [
    {
      "field": "asset",
      "label": "资产名称",
      "width": "200px",
      "editable": true,
      "required": true,
      "component": "asset-selector"
    },
    {
      "field": "quantity",
      "label": "数量",
      "width": "100px",
      "editable": true,
      "required": true,
      "component": "number-input",
      "validation": {
        "min": 1,
        "max": 999
      }
    },
    {
      "field": "estimated_price",
      "label": "预估单价",
      "width": "120px",
      "editable": true,
      "required": true,
      "component": "decimal-input",
      "validation": {
        "min": 0
      }
    },
    {
      "field": "subtotal",
      "label": "小计",
      "width": "120px",
      "editable": false,
      "component": "formula",
      "formula": "quantity * estimated_price"
    },
    {
      "field": "actions",
      "label": "操作",
      "width": "80px",
      "fixed": "right"
    }
  ],
  "row_actions": ["edit", "delete"],
  "toolbar_actions": ["add", "batch_delete", "import"]
}
```

---

## 3. 主从表布局配置

### 3.1 完整 JSON 配置示例

```json
{
  "layout_code": "procurement_request_detail",
  "layout_name": "采购申请详情页布局",
  "business_object": "procurement_request",
  "type": "detail",
  "version": "1.0.0",

  "main_layout": {
    "sections": [
      {
        "id": "basic_info",
        "title": "基本信息",
        "columns": 2,
        "fields": [
          {
            "field": "code",
            "label": "申请编号",
            "span": 1,
            "readonly": true
          },
          {
            "field": "request_date",
            "label": "申请日期",
            "span": 1,
            "required": true
          },
          {
            "field": "department",
            "label": "申请部门",
            "span": 1,
            "required": true
          },
          {
            "field": "requester",
            "label": "申请人",
            "span": 1,
            "required": true
          },
          {
            "field": "total_amount",
            "label": "总金额",
            "span": 1,
            "readonly": true,
            "component": "decimal-display"
          },
          {
            "field": "status",
            "label": "状态",
            "span": 1,
            "readonly": true,
            "component": "status-badge"
          }
        ]
      },
      {
        "id": "approval_info",
        "title": "审批信息",
        "columns": 1,
        "fields": [
          {
            "field": "approval_notes",
            "label": "审批意见",
            "span": 1,
            "component": "textarea"
          }
        ],
        "visibility": "expression",
        "condition": "status in ['pending_approval', 'approved', 'rejected']"
      }
    ]
  },

  "sub_layouts": [
    {
      "id": "procurement_items",
      "title": "采购明细",
      "field_type": "subtable",
      "sub_object_code": "procurement_item",
      "relation_field": "procurement",

      "table_config": {
        "columns": [
          {
            "field": "asset",
            "label": "资产名称",
            "width": "200px",
            "editable": true,
            "required": true
          },
          {
            "field": "specification",
            "label": "规格型号",
            "width": "150px",
            "editable": true,
            "required": false
          },
          {
            "field": "quantity",
            "label": "数量",
            "width": "100px",
            "editable": true,
            "required": true,
            "validation": {
              "min": 1,
              "max": 9999
            }
          },
          {
            "field": "unit",
            "label": "单位",
            "width": "80px",
            "editable": true,
            "required": true,
            "component": "select",
            "options": ["台", "套", "件", "个", "箱"]
          },
          {
            "field": "estimated_price",
            "label": "预估单价",
            "width": "120px",
            "editable": true,
            "required": true,
            "component": "decimal-input"
          },
          {
            "field": "subtotal",
            "label": "小计",
            "width": "120px",
            "editable": false,
            "component": "formula",
            "formula": "quantity * estimated_price"
          },
          {
            "field": "remark",
            "label": "备注",
            "width": "200px",
            "editable": true,
            "component": "textarea"
          },
          {
            "field": "actions",
            "label": "操作",
            "width": "100px",
            "fixed": "right",
            "actions": ["edit", "delete"]
          }
        ],

        "table_settings": {
          "stripe": true,
          "border": true,
          "highlight_current_row": true,
          "show_header": true,
          "empty_text": "暂无采购明细，请添加"

        },

        "toolbar": {
          "show": true,
          "actions": [
            {
              "type": "add",
              "label": "添加明细",
              "icon": "Plus",
              "position": "left"
            },
            {
              "type": "batch_delete",
              "label": "批量删除",
              "icon": "Delete",
              "position": "left",
              "confirm": true,
              "confirm_text": "确定要删除选中的明细吗？"
            },
            {
              "type": "import",
              "label": "导入",
              "icon": "Upload",
              "position": "right"
            },
            {
              "type": "export",
              "label": "导出",
              "icon": "Download",
              "position": "right"
            }
          ]
        },

        "pagination": {
          "show": false,
          "page_size": 20
        },

        "summary_row": {
          "show": true,
          "fields": [
            {
              "field": "quantity",
              "label": "合计",
              "aggregation": "sum"
            },
            {
              "field": "subtotal",
              "label": "总金额",
              "aggregation": "sum",
              "prefix": "¥"
            }
          ]
        },

        "validation": {
          "min_rows": 1,
          "max_rows": 100,
          "required_message": "至少需要添加一条采购明细"
        },

        "form_config": {
          "mode": "inline",  # inline | dialog | drawer
          "dialog_width": "600px",
          "auto_save": false
        }
      }
    }
  ],

  "form_rules": {
    "procurement_items": {
      "validator": "customProcurementItemsValidator",
      "trigger": "blur",
      "message": "采购明细验证失败"
    }
  }
}
```

### 3.2 PageLayout 模型扩展

```python
# apps/system/models.py

class PageLayout(BaseModel):
    """页面布局配置"""

    LAYOUT_TYPE_CHOICES = [
        ('form', '表单布局'),
        ('list', '列表布局'),
        ('detail', '详情布局'),
        ('subtable', '子表布局'),
        ('subform', '嵌套表单布局'),
    ]

    layout_type = models.CharField(
        max_length=20,
        choices=LAYOUT_TYPE_CHOICES,
        verbose_name='布局类型'
    )

    # 主从关系配置
    parent_layout = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_layouts',
        verbose_name='父布局'
    )

    relation_field = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='关联字段',
        help_text='从对象关联主对象的字段名称'
    )

    layout_config = models.JSONField(
        default=dict,
        verbose_name='布局配置',
        help_text='完整的布局配置JSON'
    )

    class Meta:
        db_table = 'system_page_layouts'
        verbose_name = '页面布局'
        verbose_name_plural = '页面布局'
```

---

## 4. 嵌套表单布局

### 4.1 内联表单配置

```json
{
  "sub_layouts": [
    {
      "id": "maintenance_records",
      "title": "维护记录",
      "field_type": "subform",
      "sub_object_code": "maintenance_record",
      "relation_field": "asset",

      "form_config": {
        "mode": "inline",
        "layout": "horizontal",
        "label_width": "120px",
        "columns": 2,

        "sections": [
          {
            "id": "record_info",
            "fields": [
              {
                "field": "maintenance_date",
                "label": "维护日期",
                "span": 1,
                "required": true,
                "component": "date-picker"
              },
              {
                "field": "maintenance_type",
                "label": "维护类型",
                "span": 1,
                "required": true,
                "component": "select",
                "options": [
                  {"value": "routine", "label": "日常保养"},
                  {"value": "repair", "label": "故障维修"},
                  {"value": "upgrade", "label": "升级改造"}
                ]
              },
              {
                "field": "maintenance_person",
                "label": "维护人员",
                "span": 1,
                "required": true,
                "component": "user-selector"
              },
              {
                "field": "cost",
                "label": "维护费用",
                "span": 1,
                "required": false,
                "component": "decimal-input"
              },
              {
                "field": "description",
                "label": "维护内容",
                "span": 2,
                "required": true,
                "component": "textarea",
                "rows": 3
              }
            ]
          }
        ]
      },

      "list_config": {
        "display_mode": "card",  # card | table | list
        "card_fields": [
          "maintenance_date",
          "maintenance_type",
          "maintenance_person",
          "cost"
        ],
        "show_actions": true,
        "actions": ["edit", "delete", "view"]
      },

      "toolbar": {
        "show": true,
        "actions": [
          {
            "type": "add",
            "label": "添加维护记录",
            "icon": "Plus"
          }
        ]
      },

      "allow_multiple": true,
      "max_items": 50
    }
  ]
}
```

### 4.2 弹窗表单配置

```json
{
  "sub_layouts": [
    {
      "id": "contact_info",
      "title": "联系方式",
      "field_type": "subform",
      "sub_object_code": "contact",
      "relation_field": "user",

      "form_config": {
        "mode": "dialog",
        "dialog_title": "添加联系方式",
        "dialog_width": "500px",
        "layout": "vertical",

        "sections": [
          {
            "id": "contact_details",
            "fields": [
              {
                "field": "contact_type",
                "label": "联系方式类型",
                "span": 1,
                "required": true,
                "component": "select",
                "options": [
                  {"value": "mobile", "label": "手机号码"},
                  {"value": "email", "label": "电子邮箱"},
                  {"value": "wechat", "label": "微信"},
                  {"value": "phone", "label": "固定电话"}
                ]
              },
              {
                "field": "contact_value",
                "label": "联系方式",
                "span": 1,
                "required": true,
                "component": "text-input"
              },
              {
                "field": "is_primary",
                "label": "是否主要",
                "span": 1,
                "component": "switch"
              },
              {
                "field": "remark",
                "label": "备注",
                "span": 1,
                "component": "textarea",
                "rows": 2
              }
            ]
          }
        ]
      },

      "list_config": {
        "display_mode": "list",
        "list_item_template": "contact_item",
        "show_actions": true
      },

      "validation": {
        "unique_contact_type": true,
        "max_primary_contacts": 1
      }
    }
  ]
}
```

### 4.3 抽屉表单配置

```json
{
  "sub_layouts": [
    {
      "id": "asset_attachments",
      "title": "资产附件",
      "field_type": "subform",
      "sub_object_code": "asset_attachment",
      "relation_field": "asset",

      "form_config": {
        "mode": "drawer",
        "drawer_title": "上传附件",
        "drawer_width": "600px",
        "direction": "rtl",  # rtl | ltr

        "sections": [
          {
            "id": "attachment_info",
            "fields": [
              {
                "field": "file_name",
                "label": "文件名称",
                "span": 1,
                "required": true
              },
              {
                "field": "file_type",
                "label": "文件类型",
                "span": 1,
                "required": true,
                "component": "select",
                "options": [
                  {"value": "manual", "label": "使用手册"},
                  {"value": "certificate", "label": "合格证书"},
                  {"value": "warranty", "label": "保修卡"},
                  {"value": "invoice", "label": "发票"},
                  {"value": "other", "label": "其他"}
                ]
              },
              {
                "field": "file",
                "label": "上传文件",
                "span": 2,
                "required": true,
                "component": "file-upload",
                "accept": ".pdf,.doc,.docx,.jpg,.png"
              },
              {
                "field": "description",
                "label": "说明",
                "span": 2,
                "component": "textarea"
              }
            ]
          }
        ]
      },

      "list_config": {
        "display_mode": "table",
        "columns": [
          "file_name",
          "file_type",
          "uploaded_at",
          "actions"
        ]
      }
    }
  ]
}
```

---

## 5. 子表组件实现

### 5.1 SubTableField.vue 完整实现

```vue
<template>
  <div class="sub-table-field">
    <div class="sub-table-header">
      <div class="title">
        <el-icon><Files /></el-icon>
        <span>{{ layoutConfig.title || '子表' }}</span>
        <el-tag v-if="required" type="danger" size="small">必填</el-tag>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar" v-if="layoutConfig.toolbar?.show">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleAdd"
          :disabled="disabled || isMaxRows"
          size="small"
        >
          添加{{ layoutConfig.title }}
        </el-button>

        <el-button
          v-if="layoutConfig.toolbar?.actions?.find(a => a.type === 'batch_delete')"
          :icon="Delete"
          @click="handleBatchDelete"
          :disabled="selectedRows.length === 0"
          size="small"
        >
          批量删除
        </el-button>

        <el-button
          v-if="layoutConfig.toolbar?.actions?.find(a => a.type === 'import')"
          :icon="Upload"
          @click="handleImport"
          size="small"
        >
          导入
        </el-button>

        <el-button
          v-if="layoutConfig.toolbar?.actions?.find(a => a.type === 'export')"
          :icon="Download"
          @click="handleExport"
          size="small"
        >
          导出
        </el-button>
      </div>
    </div>

    <!-- 表格主体 -->
    <el-table
      ref="tableRef"
      :data="tableData"
      :stripe="layoutConfig.table_settings?.stripe"
      :border="layoutConfig.table_settings?.border"
      :height="tableHeight"
      style="width: 100%"
      @selection-change="handleSelectionChange"
      v-loading="loading"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="layoutConfig.toolbar?.actions?.find(a => a.type === 'batch_delete')"
        type="selection"
        width="55"
      />

      <!-- 序号列 -->
      <el-table-column
        type="index"
        label="序号"
        width="60"
        v-if="layoutConfig.table_settings?.show_index"
      />

      <!-- 动态列配置 -->
      <el-table-column
        v-for="column in layoutConfig.columns"
        :key="column.field"
        :prop="column.field"
        :label="column.label"
        :width="column.width"
        :min-width="column.min_width"
        :fixed="column.fixed"
        :align="column.align || 'center'"
      >

        <template #default="{ row, $index }">
          <!-- 公式字段（只读） -->
          <template v-if="column.component === 'formula'">
            <span class="formula-cell">
              {{ calculateFormula(row, column.formula) }}
            </span>
          </template>

          <!-- 只读字段 -->
          <template v-else-if="!column.editable || disabled">
            <span :class="`cell-${column.field}`">
              {{ formatCellValue(row[column.field], column) }}
            </span>
          </template>

          <!-- 可编辑字段 -->
          <template v-else>
            <!-- 文本输入 -->
            <el-input
              v-if="column.component === 'text-input'"
              v-model="row[column.field]"
              size="small"
              :placeholder="`请输入${column.label}`"
              @blur="validateCell(row, column, $index)"
            />

            <!-- 数字输入 -->
            <el-input-number
              v-else-if="column.component === 'number-input'"
              v-model="row[column.field]"
              size="small"
              :min="column.validation?.min"
              :max="column.validation?.max"
              :precision="0"
              @change="handleCellChange(row, column, $index)"
            />

            <!-- 金额输入 -->
            <el-input-number
              v-else-if="column.component === 'decimal-input'"
              v-model="row[column.field]"
              size="small"
              :min="column.validation?.min || 0"
              :precision="2"
              :precision="2"
              @change="handleCellChange(row, column, $index)"
            />

            <!-- 下拉选择 -->
            <el-select
              v-else-if="column.component === 'select'"
              v-model="row[column.field]"
              size="small"
              :placeholder="`请选择${column.label}`"
              @change="handleCellChange(row, column, $index)"
            >
              <el-option
                v-for="option in column.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>

            <!-- 资产选择器 -->
            <AssetSelector
              v-else-if="column.component === 'asset-selector'"
              v-model="row[column.field]"
              :disabled="disabled"
              size="small"
              @change="handleAssetChange(row, $index)"
            />

            <!-- 用户选择器 -->
            <UserSelector
              v-else-if="column.component === 'user-selector'"
              v-model="row[column.field]"
              :disabled="disabled"
              size="small"
            />

            <!-- 部门选择器 -->
            <DeptSelector
              v-else-if="column.component === 'department-selector'"
              v-model="row[column.field]"
              :disabled="disabled"
              size="small"
            />

            <!-- 日期选择器 -->
            <el-date-picker
              v-else-if="column.component === 'date-picker'"
              v-model="row[column.field]"
              type="date"
              size="small"
              value-format="YYYY-MM-DD"
              @change="handleCellChange(row, column, $index)"
            />

            <!-- 默认文本输入 -->
            <el-input
              v-else
              v-model="row[column.field]"
              size="small"
              @blur="validateCell(row, column, $index)"
            />
          </template>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column
        v-if="layoutConfig.row_actions?.length"
        label="操作"
        :width="actionColumnWidth"
        fixed="right"
      >
        <template #default="{ row, $index }">
          <el-button
            v-if="layoutConfig.row_actions?.includes('edit')"
            type="primary"
            link
            size="small"
            @click="handleEdit(row, $index)"
          >
            编辑
          </el-button>
          <el-button
            v-if="layoutConfig.row_actions?.includes('delete')"
            type="danger"
            link
            size="small"
            @click="handleDelete(row, $index)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>

      <!-- 合计行 -->
      <template #footer v-if="layoutConfig.summary_row?.show">
        <div class="summary-row">
          <span
            v-for="summaryField in layoutConfig.summary_row.fields"
            :key="summaryField.field"
            class="summary-item"
          >
            <strong>{{ summaryField.label }}:</strong>
            <span>{{ summaryField.prefix || '' }}{{ calculateSummary(summaryField) }}</span>
          </span>
        </div>
      </template>
    </el-table>

    <!-- 分页（如果需要） -->
    <el-pagination
      v-if="layoutConfig.pagination?.show"
      v-model:current-page="pagination.currentPage"
      v-model:page-size="pagination.pageSize"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      :total="totalRows"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- 验证错误提示 -->
    <div v-if="errorMessage" class="error-message">
      <el-icon color="#f56c6c"><Warning /></el-icon>
      <span>{{ errorMessage }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Plus, Delete, Upload, Download, Files, Warning } from '@element-plus/icons-vue'
import AssetSelector from '@/components/common/AssetSelector.vue'
import UserSelector from '@/components/common/UserSelector.vue'
import DeptSelector from '@/components/common/DeptSelector.vue'

// Props
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  layoutConfig: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  parentRecord: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change', 'validate'])

// Refs
const tableRef = ref(null)
const tableData = ref([])
const selectedRows = ref([])
const loading = ref(false)
const errorMessage = ref('')
const pagination = ref({
  currentPage: 1,
  pageSize: 20
})

// Computed
const totalRows = computed(() => tableData.value.length)

const isMaxRows = computed(() => {
  const maxRows = props.layoutConfig.validation?.max_rows || 100
  return tableData.value.length >= maxRows
})

const isMinRows = computed(() => {
  const minRows = props.layoutConfig.validation?.min_rows || 0
  return tableData.value.length >= minRows
})

const actionColumnWidth = computed(() => {
  const actions = props.layoutConfig.row_actions || []
  return actions.length * 60 + 20
})

const tableHeight = computed(() => {
  return props.layoutConfig.table_settings?.height || 'auto'
})

// Watchers
watch(() => props.modelValue, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(tableData.value)) {
    tableData.value = [...newVal]
  }
}, { deep: true, immediate: true })

watch(tableData, (newVal) => {
  emit('update:modelValue', newVal)
  emit('change', newVal)
  calculateFormulas()
}, { deep: true })

// Methods
const handleAdd = () => {
  const newRow = createEmptyRow()
  tableData.value.push(newRow)
  validateMinRows()
}

const createEmptyRow = () => {
  const row = {
    _id: Date.now() + Math.random(), // 临时ID
    _isNew: true
  }

  // 初始化所有字段为null或默认值
  props.layoutConfig.columns.forEach(column => {
    if (column.field !== 'actions') {
      row[column.field] = column.default_value || null
    }
  })

  return row
}

const handleEdit = (row, index) => {
  // 如果是dialog模式，打开编辑弹窗
  if (props.layoutConfig.form_config?.mode === 'dialog') {
    // TODO: 打开编辑弹窗
  }
}

const handleDelete = (row, index) => {
  tableData.value.splice(index, 1)
  validateMinRows()
}

const handleBatchDelete = () => {
  const selectedIds = selectedRows.value.map(row => row._id)
  tableData.value = tableData.value.filter(row => !selectedIds.includes(row._id))
  selectedRows.value = []
  validateMinRows()
}

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleCellChange = (row, column, index) => {
  // 触发公式重新计算
  calculateFormulas()

  // 触发自定义验证
  validateCell(row, column, index)

  // 触发change事件
  emit('change', tableData.value)
}

const handleAssetChange = (row, index) => {
  // 资产选择后，自动填充其他字段
  if (row.asset && props.layoutConfig.auto_fill_fields) {
    props.layoutConfig.auto_fill_fields.forEach(fieldConfig => {
      if (fieldConfig.source === 'asset') {
        row[fieldConfig.target] = row.asset[fieldConfig.source_field]
      }
    })
  }
}

const validateCell = (row, column, index) => {
  if (column.required && !row[column.field]) {
    errorMessage.value = `第${index + 1}行${column.label}不能为空`
    return false
  }

  if (column.validation) {
    const value = row[column.field]

    if (column.validation.min !== undefined && value < column.validation.min) {
      errorMessage.value = `第${index + 1}行${column.label}不能小于${column.validation.min}`
      return false
    }

    if (column.validation.max !== undefined && value > column.validation.max) {
      errorMessage.value = `第${index + 1}行${column.label}不能大于${column.validation.max}`
      return false
    }
  }

  errorMessage.value = ''
  return true
}

const validateMinRows = () => {
  if (!isMinRows.value) {
    errorMessage.value = props.layoutConfig.validation?.required_message || '至少需要添加一条记录'
    return false
  }
  errorMessage.value = ''
  return true
}

const calculateFormula = (row, formula) => {
  try {
    // 简单公式计算，可以使用eval或更安全的公式引擎
    // 这里使用简单的替换和计算
    let expression = formula

    // 替换字段名为实际值
    Object.keys(row).forEach(key => {
      const value = row[key] || 0
      expression = expression.replace(new RegExp(`\\b${key}\\b`, 'g'), value)
    })

    // 安全计算（实际项目中应使用更安全的公式引擎）
    return new Function('return ' + expression)()
  } catch (error) {
    console.error('公式计算错误:', error)
    return 0
  }
}

const calculateFormulas = () => {
  // 计算所有公式列
  tableData.value.forEach(row => {
    props.layoutConfig.columns.forEach(column => {
      if (column.component === 'formula') {
        row[column.field] = calculateFormula(row, column.formula)
      }
    })
  })
}

const calculateSummary = (summaryField) => {
  const field = summaryField.field
  const aggregation = summaryField.aggregation

  if (aggregation === 'sum') {
    return tableData.value.reduce((sum, row) => {
      return sum + (parseFloat(row[field]) || 0)
    }, 0).toFixed(2)
  } else if (aggregation === 'avg') {
    const sum = tableData.value.reduce((s, row) => {
      return s + (parseFloat(row[field]) || 0)
    }, 0)
    return (sum / tableData.value.length).toFixed(2)
  } else if (aggregation === 'count') {
    return tableData.value.filter(row => row[field]).length
  }

  return ''
}

const formatCellValue = (value, column) => {
  if (value === null || value === undefined) {
    return '-'
  }

  if (column.component === 'decimal-input' || column.component === 'formula') {
    return parseFloat(value).toFixed(2)
  }

  return value
}

const handleImport = () => {
  // TODO: 实现导入功能
}

const handleExport = () => {
  // TODO: 实现导出功能
}

const handleSizeChange = (size) => {
  pagination.value.pageSize = size
}

const handleCurrentChange = (page) => {
  pagination.value.currentPage = page
}

// 对外暴露的验证方法
const validate = () => {
  let isValid = true

  // 验证最小行数
  if (!validateMinRows()) {
    isValid = false
  }

  // 验证必填字段
  tableData.value.forEach((row, index) => {
    props.layoutConfig.columns.forEach(column => {
      if (column.required && !row[column.field]) {
        errorMessage.value = `第${index + 1}行${column.label}不能为空`
        isValid = false
      }
    })
  })

  emit('validate', isValid)
  return isValid
}

// 生命周期
onMounted(() => {
  calculateFormulas()
})

// 暴露方法
defineExpose({
  validate,
  tableData
})
</script>

<style scoped lang="scss">
.sub-table-field {
  width: 100%;

  .sub-table-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #333;
    }

    .toolbar {
      display: flex;
      gap: 8px;
    }
  }

  .formula-cell {
    font-weight: 500;
    color: #409eff;
  }

  .summary-row {
    display: flex;
    gap: 24px;
    padding: 12px;
    background-color: #f5f7fa;
    font-size: 14px;

    .summary-item {
      display: flex;
      gap: 8px;

      strong {
        color: #606266;
      }

      span {
        color: #303133;
        font-weight: 500;
      }
    }
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    color: #f56c6c;
    font-size: 12px;
  }
}
</style>
```

---

## 6. 主从数据提交处理

### 6.1 后端 Serializer 处理

```python
# apps/procurement/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import ProcurementRequest, ProcurementItem

class ProcurementItemSerializer(BaseModelSerializer):
    """采购明细序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = ProcurementItem
        fields = BaseModelSerializer.Meta.fields + [
            'procurement',
            'asset',
            'quantity',
            'unit',
            'estimated_price',
            'subtotal',
            'specification',
            'remark'
        ]
        read_only_fields = ['subtotal']

    def validate(self, attrs):
        """
        验证采购明细数据
        """
        quantity = attrs.get('quantity')
        estimated_price = attrs.get('estimated_price')

        if quantity and estimated_price:
            # 自动计算小计
            attrs['subtotal'] = quantity * estimated_price

        return attrs


class ProcurementRequestSerializer(BaseModelSerializer):
    """采购申请序列化器（主从关系）"""

    # 嵌套序列化从对象
    items = ProcurementItemSerializer(
        many=True,
        required=False,
        source='procurement_items'
    )

    # 计算总金额
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = ProcurementRequest
        fields = BaseModelSerializer.Meta.fields + [
            'code',
            'request_date',
            'department',
            'requester',
            'total_amount',
            'status',
            'approval_notes',
            'items',  # 从对象数据
        ]

    def validate(self, attrs):
        """
        验证主从数据
        """
        items = attrs.get('procurement_items', [])

        # 验证至少有一条明细
        if not items:
            raise serializers.ValidationError({
                'items': '至少需要添加一条采购明细'
            })

        # 验证明细数据
        for index, item in enumerate(items):
            if not item.get('asset'):
                raise serializers.ValidationError({
                    f'items.{index}.asset': '资产不能为空'
                })

            if not item.get('quantity') or item['quantity'] <= 0:
                raise serializers.ValidationError({
                    f'items.{index}.quantity': '数量必须大于0'
                })

            if not item.get('estimated_price') or item['estimated_price'] <= 0:
                raise serializers.ValidationError({
                    f'items.{index}.estimated_price': '预估单价必须大于0'
                })

        return attrs

    def create(self, validated_data):
        """
        创建主从记录
        """
        # 提取从对象数据
        items_data = validated_data.pop('procurement_items', [])

        # 创建主对象
        procurement = ProcurementRequest.objects.create(**validated_data)

        # 批量创建从对象
        items_to_create = []
        for item_data in items_data:
            item_data['procurement'] = procurement
            items_to_create.append(ProcurementItem(**item_data))

        # 批量插入（性能优化）
        ProcurementItem.objects.bulk_create(items_to_create)

        # 重新计算总金额
        procurement.total_amount = sum(
            item.subtotal for item in items_to_create
        )
        procurement.save()

        return procurement

    def update(self, instance, validated_data):
        """
        更新主从记录
        """
        # 提取从对象数据
        items_data = validated_data.pop('procurement_items', [])

        # 更新主对象
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 处理从对象：采用全量更新策略
        # 1. 获取现有从对象ID列表
        existing_item_ids = [
            item.id for item in instance.procurement_items.all()
        ]

        # 2. 获取提交数据中的ID列表
        submitted_item_ids = [
            item.get('id') for item in items_data if item.get('id')
        ]

        # 3. 删除不在提交数据中的从对象（软删除）
        items_to_delete = set(existing_item_ids) - set(submitted_item_ids)
        if items_to_delete:
            ProcurementItem.objects.filter(
                id__in=items_to_delete
            ).soft_delete()

        # 4. 创建或更新从对象
        for item_data in items_data:
            item_id = item_data.get('id')

            if item_id:
                # 更新现有记录
                item = ProcurementItem.objects.get(id=item_id)
                for attr, value in item_data.items():
                    if attr != 'id':
                        setattr(item, attr, value)
                item.save()
            else:
                # 创建新记录
                item_data['procurement'] = instance
                ProcurementItem.objects.create(**item_data)

        # 重新计算总金额
        instance.total_amount = instance.procurement_items.aggregate(
            total=models.Sum('subtotal')
        )['total'] or 0
        instance.save()

        return instance
```

### 6.2 Service 层处理

```python
# apps/procurement/services/procurement_service.py

from apps.common.services.base_crud import BaseCRUDService
from .models import ProcurementRequest, ProcurementItem
from .serializers import ProcurementRequestSerializer

class ProcurementService(BaseCRUDService):
    """采购申请服务"""

    def __init__(self):
        super().__init__(ProcurementRequest)
        self.serializer_class = ProcurementRequestSerializer

    def create_with_items(self, data, user=None):
        """
        创建采购申请及明细（带组织隔离）
        """
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid():
            return {
                'success': False,
                'errors': serializer.errors
            }

        # 自动设置组织
        if user and 'organization' not in data:
            data['organization'] = user.organization

        # 创建记录
        instance = serializer.save()

        return {
            'success': True,
            'data': self.serializer_class(instance).data
        }

    def update_with_items(self, instance_id, data, user=None):
        """
        更新采购申请及明细
        """
        instance = self.get(instance_id)

        if not instance:
            return {
                'success': False,
                'error': '记录不存在'
            }

        # 权限检查
        if user and instance.organization != user.organization:
            return {
                'success': False,
                'error': '无权操作此记录'
            }

        serializer = self.serializer_class(
            instance,
            data=data,
            partial=True
        )

        if not serializer.is_valid():
            return {
                'success': False,
                'errors': serializer.errors
            }

        instance = serializer.save()

        return {
            'success': True,
            'data': self.serializer_class(instance).data
        }

    def delete_with_items(self, instance_id, user=None):
        """
        删除采购申请及明细（级联软删除）
        """
        instance = self.get(instance_id)

        if not instance:
            return {
                'success': False,
                'error': '记录不存在'
            }

        # 权限检查
        if user and instance.organization != user.organization:
            return {
                'success': False,
                'error': '无权操作此记录'
            }

        # 软删除主对象（从对象会通过数据库CASCADE自动软删除）
        instance.soft_delete()

        return {
            'success': True,
            'message': '删除成功'
        }

    def get_detail_with_items(self, instance_id, user=None):
        """
        获取采购申请详情（包含明细）
        """
        instance = self.get(instance_id)

        if not instance:
            return {
                'success': False,
                'error': '记录不存在'
            }

        # 权限检查
        if user and instance.organization != user.organization:
            return {
                'success': False,
                'error': '无权查看此记录'
            }

        serializer = self.serializer_class(instance)

        return {
            'success': True,
            'data': serializer.data
        }
```

### 6.3 ViewSet 处理

```python
# apps/procurement/viewsets.py

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from .services.procurement_service import ProcurementService
from .serializers import ProcurementRequestSerializer

class ProcurementRequestViewSet(BaseModelViewSet):
    """采购申请视图集"""

    queryset = ProcurementRequest.objects.all()
    serializer_class = ProcurementRequestSerializer
    service = ProcurementService()

    def create(self, request, *args, **kwargs):
        """
        创建采购申请（包含明细）
        """
        result = self.service.create_with_items(
            data=request.data,
            user=request.user
        )

        if result['success']:
            return Response(BaseResponse.success(
                data=result['data'],
                message='采购申请创建成功'
            ), status=status.HTTP_201_CREATED)
        else:
            return Response(BaseResponse.error(
                message='创建失败',
                details=result.get('errors')
            ), status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        更新采购申请（包含明细）
        """
        instance_id = kwargs.get('pk')

        result = self.service.update_with_items(
            instance_id=instance_id,
            data=request.data,
            user=request.user
        )

        if result['success']:
            return Response(BaseResponse.success(
                data=result['data'],
                message='采购申请更新成功'
            ))
        else:
            return Response(BaseResponse.error(
                message=result.get('error', '更新失败'),
                details=result.get('errors')
            ), status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        """
        获取采购申请详情（包含明细）
        """
        instance_id = kwargs.get('pk')

        result = self.service.get_detail_with_items(
            instance_id=instance_id,
            user=request.user
        )

        if result['success']:
            return Response(BaseResponse.success(
                data=result['data']
            ))
        else:
            return Response(BaseResponse.error(
                message=result['error']
            ), status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """
        获取采购申请的明细列表
        """
        instance = self.get_object()

        # 权限检查
        if instance.organization != request.user.organization:
            return Response(BaseResponse.error(
                message='无权查看此记录'
            ), status=status.HTTP_403_FORBIDDEN)

        items = instance.procurement_items.all()
        serializer = ProcurementItemSerializer(items, many=True)

        return Response(BaseResponse.success(
            data=serializer.data
        ))

    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)')
    def update_item(self, request, pk=None, item_id=None):
        """
        更新单个明细行
        """
        instance = self.get_object()

        # 权限检查
        if instance.organization != request.user.organization:
            return Response(BaseResponse.error(
                message='无权操作此记录'
            ), status=status.HTTP_403_FORBIDDEN)

        try:
            item = instance.procurement_items.get(id=item_id)
        except ProcurementItem.DoesNotExist:
            return Response(BaseResponse.error(
                message='明细记录不存在'
            ), status=status.HTTP_404_NOT_FOUND)

        serializer = ProcurementItemSerializer(
            item,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            # 重新计算总金额
            instance.total_amount = instance.procurement_items.aggregate(
                total=models.Sum('subtotal')
            )['total'] or 0
            instance.save()

            return Response(BaseResponse.success(
                data=serializer.data,
                message='明细更新成功'
            ))
        else:
            return Response(BaseResponse.error(
                message='更新失败',
                details=serializer.errors
            ), status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='items/(?P<item_id>[^/.]+)/delete')
    def delete_item(self, request, pk=None, item_id=None):
        """
        删除单个明细行
        """
        instance = self.get_object()

        # 权限检查
        if instance.organization != request.user.organization:
            return Response(BaseResponse.error(
                message='无权操作此记录'
            ), status=status.HTTP_403_FORBIDDEN)

        try:
            item = instance.procurement_items.get(id=item_id)
        except ProcurementItem.DoesNotExist:
            return Response(BaseResponse.error(
                message='明细记录不存在'
            ), status=status.HTTP_404_NOT_FOUND)

        # 软删除明细
        item.soft_delete()

        # 重新计算总金额
        instance.total_amount = instance.procurement_items.aggregate(
            total=models.Sum('subtotal')
        )['total'] or 0
        instance.save()

        return Response(BaseResponse.success(
            message='明细删除成功'
        ))
```

---

## 7. 嵌套表单组件实现

### 7.1 SubFormField.vue 完整实现

```vue
<template>
  <div class="sub-form-field">
    <div class="sub-form-header">
      <div class="title">
        <el-icon><Document /></el-icon>
        <span>{{ layoutConfig.title || '嵌套表单' }}</span>
        <el-tag v-if="required" type="danger" size="small">必填</el-tag>
      </div>

      <!-- 工具栏 -->
      <div class="toolbar" v-if="layoutConfig.toolbar?.show">
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleAdd"
          :disabled="disabled || isMaxItems"
          size="small"
        >
          添加{{ layoutConfig.title }}
        </el-button>
      </div>
    </div>

    <!-- 表单列表 -->
    <div class="sub-form-list">
      <!-- 卡片显示模式 -->
      <template v-if="layoutConfig.list_config?.display_mode === 'card'">
        <el-row :gutter="16">
          <el-col
            v-for="(item, index) in formData"
            :key="item._id || item.id"
            :span="24"
          >
            <el-card class="form-card" shadow="hover">
              <!-- 卡片头部 -->
              <template #header>
                <div class="card-header">
                  <span>{{ getCardTitle(item, index) }}</span>
                  <div class="card-actions">
                    <el-button
                      v-if="layoutConfig.list_config?.show_actions"
                      type="primary"
                      link
                      size="small"
                      @click="handleEdit(item, index)"
                    >
                      编辑
                    </el-button>
                    <el-button
                      v-if="layoutConfig.list_config?.show_actions"
                      type="danger"
                      link
                      size="small"
                      @click="handleDelete(index)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
              </template>

              <!-- 卡片内容 -->
              <div class="card-content">
                <SubFormRender
                  :form-config="layoutConfig.form_config"
                  :form-data="item"
                  :disabled="disabled"
                  @change="(field, value) => handleFieldChange(item, index, field, value)"
                />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <!-- 表格显示模式 -->
      <template v-else-if="layoutConfig.list_config?.display_mode === 'table'">
        <el-table
          :data="formData"
          border
          stripe
          style="width: 100%"
        >
          <el-table-column
            v-for="column in layoutConfig.list_config?.columns || []"
            :key="column"
            :prop="column"
            :label="getFieldLabel(column)"
          />

          <el-table-column
            v-if="layoutConfig.list_config?.show_actions"
            label="操作"
            width="150"
            fixed="right"
          >
            <template #default="{ row, $index }">
              <el-button
                type="primary"
                link
                size="small"
                @click="handleEdit(row, $index)"
              >
                编辑
              </el-button>
              <el-button
                type="danger"
                link
                size="small"
                @click="handleDelete($index)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>

      <!-- 列表显示模式 -->
      <template v-else>
        <div
          v-for="(item, index) in formData"
          :key="item._id || item.id"
          class="list-item"
        >
          <div class="list-item-header">
            <span class="list-item-title">{{ getListItemTitle(item, index) }}</span>
            <div class="list-item-actions">
              <el-button
                v-if="layoutConfig.list_config?.show_actions"
                type="primary"
                link
                size="small"
                @click="handleEdit(item, index)"
              >
                编辑
              </el-button>
              <el-button
                v-if="layoutConfig.list_config?.show_actions"
                type="danger"
                link
                size="small"
                @click="handleDelete(index)"
              >
                删除
              </el-button>
            </div>
          </div>

          <div class="list-item-content">
            <SubFormRender
              :form-config="layoutConfig.form_config"
              :form-data="item"
              :disabled="disabled"
              @change="(field, value) => handleFieldChange(item, index, field, value)"
            />
          </div>
        </div>
      </template>
    </div>

    <!-- 添加/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="layoutConfig.form_config?.dialog_width || '600px'"
      :close-on-click-modal="false"
    >
      <SubFormRender
        ref="formRenderRef"
        :form-config="layoutConfig.form_config"
        :form-data="currentFormData"
        :disabled="false"
        @change="handleFormFieldChange"
      />

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>

    <!-- 抽屉编辑模式 -->
    <el-drawer
      v-model="drawerVisible"
      :title="layoutConfig.form_config?.drawer_title || '编辑'"
      :size="layoutConfig.form_config?.drawer_width || '600px'"
      :direction="layoutConfig.form_config?.direction || 'rtl'"
    >
      <SubFormRender
        ref="drawerFormRenderRef"
        :form-config="layoutConfig.form_config"
        :form-data="currentFormData"
        :disabled="false"
        @change="handleFormFieldChange"
      />

      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" @click="handleDrawerSave">确定</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Document, Plus } from '@element-plus/icons-vue'
import SubFormRender from './SubFormRender.vue'

// Props
const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  layoutConfig: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'change', 'validate'])

// Refs
const formData = ref([])
const dialogVisible = ref(false)
const drawerVisible = ref(false)
const currentFormData = ref({})
const currentEditIndex = ref(-1)
const formRenderRef = ref(null)
const drawerFormRenderRef = ref(null)

// Computed
const isMaxItems = computed(() => {
  const maxItems = props.layoutConfig.max_items || 50
  return formData.value.length >= maxItems
})

const dialogTitle = computed(() => {
  return currentEditIndex.value >= 0
    ? `编辑${props.layoutConfig.title}`
    : `添加${props.layoutConfig.title}`
})

// Watchers
watch(() => props.modelValue, (newVal) => {
  if (JSON.stringify(newVal) !== JSON.stringify(formData.value)) {
    formData.value = [...newVal]
  }
}, { deep: true, immediate: true })

watch(formData, (newVal) => {
  emit('update:modelValue', newVal)
  emit('change', newVal)
}, { deep: true })

// Methods
const handleAdd = () => {
  currentEditIndex.value = -1
  currentFormData.value = createEmptyForm()

  const mode = props.layoutConfig.form_config?.mode || 'dialog'

  if (mode === 'dialog') {
    dialogVisible.value = true
  } else if (mode === 'drawer') {
    drawerVisible.value = true
  }
}

const createEmptyForm = () => {
  const form = {
    _id: Date.now() + Math.random(),
    _isNew: true
  }

  // 初始化所有字段为null
  if (props.layoutConfig.form_config?.sections) {
    props.layoutConfig.form_config.sections.forEach(section => {
      section.fields.forEach(field => {
        if (!form[field.field]) {
          form[field.field] = field.default_value || null
        }
      })
    })
  }

  return form
}

const handleEdit = (item, index) => {
  currentEditIndex.value = index
  currentFormData.value = { ...item }

  const mode = props.layoutConfig.form_config?.mode || 'dialog'

  if (mode === 'dialog') {
    dialogVisible.value = true
  } else if (mode === 'drawer') {
    drawerVisible.value = true
  }
}

const handleDelete = (index) => {
  formData.value.splice(index, 1)
}

const handleSave = () => {
  // 验证表单
  if (formRenderRef.value && !formRenderRef.value.validate()) {
    return
  }

  if (currentEditIndex.value >= 0) {
    // 更新现有记录
    formData.value[currentEditIndex.value] = {
      ...formData.value[currentEditIndex.value],
      ...currentFormData.value
    }
  } else {
    // 添加新记录
    formData.value.push(currentFormData.value)
  }

  dialogVisible.value = false
}

const handleDrawerSave = () => {
  // 验证表单
  if (drawerFormRenderRef.value && !drawerFormRenderRef.value.validate()) {
    return
  }

  if (currentEditIndex.value >= 0) {
    // 更新现有记录
    formData.value[currentEditIndex.value] = {
      ...formData.value[currentEditIndex.value],
      ...currentFormData.value
    }
  } else {
    // 添加新记录
    formData.value.push(currentFormData.value)
  }

  drawerVisible.value = false
}

const handleFieldChange = (item, index, field, value) => {
  item[field] = value
  emit('change', formData.value)
}

const handleFormFieldChange = (field, value) => {
  currentFormData.value[field] = value
}

const getCardTitle = (item, index) => {
  // 根据配置生成卡片标题
  const titleField = props.layoutConfig.list_config?.card_title_field
  if (titleField && item[titleField]) {
    return item[titleField]
  }

  return `${props.layoutConfig.title} #${index + 1}`
}

const getListItemTitle = (item, index) => {
  return getCardTitle(item, index)
}

const getFieldLabel = (field) => {
  // 查找字段标签
  if (props.layoutConfig.form_config?.sections) {
    for (const section of props.layoutConfig.form_config.sections) {
      const fieldConfig = section.fields.find(f => f.field === field)
      if (fieldConfig) {
        return fieldConfig.label
      }
    }
  }

  return field
}

const validate = () => {
  let isValid = true

  // TODO: 实现表单验证逻辑

  emit('validate', isValid)
  return isValid
}

// 暴露方法
defineExpose({
  validate,
  formData
})
</script>

<style scoped lang="scss">
.sub-form-field {
  width: 100%;

  .sub-form-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;

    .title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      font-weight: 500;
      color: #333;
    }

    .toolbar {
      display: flex;
      gap: 8px;
    }
  }

  .sub-form-list {
    .form-card {
      margin-bottom: 16px;

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .card-actions {
          display: flex;
          gap: 8px;
        }
      }

      .card-content {
        padding: 0;
      }
    }

    .list-item {
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      padding: 16px;
      margin-bottom: 16px;

      .list-item-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .list-item-title {
          font-weight: 500;
          color: #333;
        }

        .list-item-actions {
          display: flex;
          gap: 8px;
        }
      }

      .list-item-content {
        padding: 0;
      }
    }
  }
}
</style>
```

### 7.2 SubFormRender.vue（表单渲染器）

```vue
<template>
  <el-form
    ref="formRef"
    :model="formData"
    :label-width="formConfig.label_width || '120px'"
    :layout="formConfig.layout || 'horizontal'"
  >
    <template
      v-for="section in formConfig.sections"
      :key="section.id"
    >
      <el-divider v-if="section.title">{{ section.title }}</el-divider>

      <el-row :gutter="16">
        <el-col
          v-for="field in section.fields"
          :key="field.field"
          :span="field.span || 1"
        >
          <el-form-item
            :label="field.label"
            :prop="field.field"
            :required="field.required"
          >
            <!-- 动态字段渲染 -->
            <FieldRenderer
              :field="field"
              :model-value="formData[field.field]"
              :disabled="disabled"
              @update:model-value="handleFieldValueChange(field.field, $event)"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </template>
  </el-form>
</template>

<script setup>
import { ref, watch } from 'vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

// Props
const props = defineProps({
  formConfig: {
    type: Object,
    required: true
  },
  formData: {
    type: Object,
    required: true
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['change'])

// Refs
const formRef = ref(null)

// Methods
const handleFieldValueChange = (field, value) => {
  emit('change', field, value)
}

const validate = () => {
  return formRef.value?.validate() ?? true
}

const resetFields = () => {
  formRef.value?.resetFields()
}

// 暴露方法
defineExpose({
  validate,
  resetFields
})
</script>
```

---

## 8. 常见主从场景布局示例

### 8.1 采购单 + 采购明细

```json
{
  "layout_code": "procurement_request_full",
  "layout_name": "采购申请完整布局",
  "business_object": "procurement_request",
  "type": "form",

  "main_layout": {
    "sections": [
      {
        "id": "basic_info",
        "title": "基本信息",
        "columns": 2,
        "fields": [
          {"field": "code", "label": "申请编号", "span": 1, "readonly": true},
          {"field": "request_date", "label": "申请日期", "span": 1, "required": true},
          {"field": "department", "label": "申请部门", "span": 1, "required": true},
          {"field": "requester", "label": "申请人", "span": 1, "required": true},
          {"field": "total_amount", "label": "总金额", "span": 1, "readonly": true},
          {"field": "status", "label": "状态", "span": 1, "readonly": true}
        ]
      }
    ]
  },

  "sub_layouts": [
    {
      "id": "procurement_items",
      "title": "采购明细",
      "field_type": "subtable",
      "sub_object_code": "procurement_item",

      "table_config": {
        "columns": [
          {"field": "asset", "label": "资产名称", "width": "200px", "editable": true, "required": true},
          {"field": "quantity", "label": "数量", "width": "100px", "editable": true, "required": true},
          {"field": "estimated_price", "label": "预估单价", "width": "120px", "editable": true, "required": true},
          {"field": "subtotal", "label": "小计", "width": "120px", "editable": false, "formula": "quantity * estimated_price"}
        ],
        "summary_row": {
          "show": true,
          "fields": [
            {"field": "quantity", "label": "合计", "aggregation": "sum"},
            {"field": "subtotal", "label": "总金额", "aggregation": "sum"}
          ]
        }
      }
    }
  ]
}
```

### 8.2 资产 + 维护记录

```json
{
  "layout_code": "asset_maintenance_records",
  "layout_name": "资产维护记录布局",
  "business_object": "asset",
  "type": "detail",

  "main_layout": {
    "sections": [
      {
        "id": "asset_info",
        "title": "资产信息",
        "columns": 2,
        "fields": [
          {"field": "code", "label": "资产编号", "span": 1},
          {"field": "name", "label": "资产名称", "span": 1},
          {"field": "category", "label": "资产类别", "span": 1},
          {"field": "status", "label": "资产状态", "span": 1}
        ]
      }
    ]
  },

  "sub_layouts": [
    {
      "id": "maintenance_records",
      "title": "维护记录",
      "field_type": "subform",
      "sub_object_code": "maintenance_record",

      "form_config": {
        "mode": "inline",
        "sections": [
          {
            "id": "record_info",
            "fields": [
              {"field": "maintenance_date", "label": "维护日期", "span": 1, "required": true},
              {"field": "maintenance_type", "label": "维护类型", "span": 1, "required": true},
              {"field": "maintenance_person", "label": "维护人员", "span": 1, "required": true},
              {"field": "cost", "label": "维护费用", "span": 1},
              {"field": "description", "label": "维护内容", "span": 2, "required": true}
            ]
          }
        ]
      },

      "list_config": {
        "display_mode": "card",
        "card_fields": ["maintenance_date", "maintenance_type", "maintenance_person", "cost"]
      }
    }
  ]
}
```

### 8.3 用户 + 联系方式

```json
{
  "layout_code": "user_contact_info",
  "layout_name": "用户联系方式布局",
  "business_object": "user",
  "type": "form",

  "main_layout": {
    "sections": [
      {
        "id": "basic_info",
        "title": "基本信息",
        "columns": 2,
        "fields": [
          {"field": "username", "label": "用户名", "span": 1},
          {"field": "real_name", "label": "真实姓名", "span": 1},
          {"field": "email", "label": "邮箱", "span": 1},
          {"field": "phone", "label": "手机号", "span": 1}
        ]
      }
    ]
  },

  "sub_layouts": [
    {
      "id": "contact_info",
      "title": "联系方式",
      "field_type": "subform",
      "sub_object_code": "contact",

      "form_config": {
        "mode": "dialog",
        "dialog_title": "添加联系方式",
        "dialog_width": "500px",
        "sections": [
          {
            "id": "contact_details",
            "fields": [
              {"field": "contact_type", "label": "联系方式类型", "span": 1, "required": true},
              {"field": "contact_value", "label": "联系方式", "span": 1, "required": true},
              {"field": "is_primary", "label": "是否主要", "span": 1}
            ]
          }
        ]
      },

      "list_config": {
        "display_mode": "list"
      },

      "validation": {
        "unique_contact_type": true,
        "max_primary_contacts": 1
      }
    }
  ]
}
```

---

## 9. 从对象权限控制

### 9.1 权限定义

```python
# apps/common/permissions.py

from rest_framework import permissions

class SubObjectPermission(permissions.BasePermission):
    """
    从对象权限控制
    - 继承主对象的组织隔离
    - 支持细粒度权限控制（view, add, edit, delete, export）
    """

    def has_permission(self, request, view):
        """
        检查用户是否有访问从对象的权限
        """
        # 检查主对象权限
        if not hasattr(view, 'parent_object'):
            return False

        parent = view.parent_object

        # 组织隔离检查
        if parent.organization != request.user.organization:
            return False

        # 根据操作类型检查权限
        if request.method in permissions.SAFE_METHODS:
            # 查看、列表操作
            perm_code = f'{view.parent_object._meta.model_name}.view_{view.basename}'
        elif request.method == 'POST':
            # 添加操作
            perm_code = f'{view.parent_object._meta.model_name}.add_{view.basename}'
        elif request.method in ['PUT', 'PATCH']:
            # 编辑操作
            perm_code = f'{view.parent_object._meta.model_name}.change_{view.basename}'
        elif request.method == 'DELETE':
            # 删除操作
            perm_code = f'{view.parent_object._meta.model_name}.delete_{view.basename}'
        else:
            return False

        return request.user.has_perm(perm_code)

    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有操作特定从对象记录的权限
        """
        # 组织隔离检查
        if obj.organization != request.user.organization:
            return False

        # 通过主对象检查权限
        parent = getattr(obj, view.relation_field)

        if parent.organization != request.user.organization:
            return False

        return True
```

### 9.2 ViewSet 权限配置

```python
# apps/procurement/viewsets.py

from rest_framework.decorators import action
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.permissions import SubObjectPermission

class ProcurementItemViewSet(BaseModelViewSet):
    """采购明细视图集"""

    queryset = ProcurementItem.objects.all()
    serializer_class = ProcurementItemSerializer
    permission_classes = [SubObjectPermission]

    def get_queryset(self):
        """
        获取查询集（自动应用主对象过滤）
        """
        # 获取主对象ID
        procurement_id = self.request.query_params.get('procurement_id')

        if not procurement_id:
            return ProcurementItem.objects.none()

        # 只返回属于该主对象的从对象记录
        queryset = ProcurementItem.objects.filter(
            procurement_id=procurement_id
        )

        # 应用组织隔离
        queryset = queryset.filter(
            organization=self.request.user.organization
        )

        return queryset

    def perform_create(self, serializer):
        """
        创建从对象记录时自动设置主对象和组织
        """
        # 获取主对象
        procurement_id = self.request.data.get('procurement')

        try:
            procurement = ProcurementRequest.objects.get(id=procurement_id)

            # 权限检查
            if procurement.organization != self.request.user.organization:
                raise PermissionError('无权操作此记录')

            # 保存记录
            serializer.save(
                organization=procurement.organization,
                created_by=self.request.user
            )
        except ProcurementRequest.DoesNotExist:
            raise PermissionError('主对象不存在')
```

### 9.3 前端权限控制

```javascript
// frontend/src/utils/permission.js

/**
 * 检查从对象权限
 * @param {string} parentModel - 主对象模型名
 * @param {string} subObjectCode - 从对象编码
 * @param {string} action - 操作类型：view, add, edit, delete, export
 * @returns {boolean}
 */
export function hasSubObjectPermission(parentModel, subObjectCode, action) {
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const permissions = user.permissions || []

  const permCode = `${parentModel}.${action}_${subObjectCode}`
  return permissions.includes(permCode)
}

/**
 * 从对象权限指令
 */
export const subObjectPermission = {
  mounted(el, binding) {
    const { parentModel, subObjectCode, action } = binding.value
    const hasPermission = hasSubObjectPermission(parentModel, subObjectCode, action)

    if (!hasPermission) {
      el.style.display = 'none'
    }
  }
}
```

---

## 10. 性能优化

### 10.1 虚拟滚动

```vue
<!-- SubTableVirtualScroll.vue -->
<template>
  <div class="virtual-scroll-table" :style="{ height: tableHeight }">
    <div class="table-header" ref="headerRef">
      <el-table
        :data="[{}]"
        :height="headerHeight"
        :show-header="true"
        :hide-single-row="true"
      >
        <el-table-column
          v-for="column in columns"
          :key="column.field"
          :prop="column.field"
          :label="column.label"
          :width="column.width"
          :fixed="column.fixed"
        />
      </el-table>
    </div>

    <div class="table-body" ref="bodyRef" @scroll="handleScroll">
      <div class="table-content" :style="{ height: totalHeight + 'px' }">
        <div
          class="table-rows"
          :style="{ transform: `translateY(${offsetY}px)` }"
        >
          <div
            v-for="row in visibleData"
            :key="row._id"
            class="table-row"
            :style="{ height: rowHeight + 'px' }"
          >
            <!-- 行内容渲染 -->
          </div>
        </div>
      </div>
    </div>

    <div class="table-footer">
      <!-- 合计行 -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  data: Array,
  columns: Array,
  rowHeight: {
    type: Number,
    default: 50
  },
  visibleRows: {
    type: Number,
    default: 20
  },
  tableHeight: {
    type: String,
    default: '500px'
  }
})

const headerRef = ref(null)
const bodyRef = ref(null)
const scrollTop = ref(0)

const totalHeight = computed(() => props.data.length * props.rowHeight)
const startIndex = computed(() => Math.floor(scrollTop.value / props.rowHeight))
const endIndex = computed(() => Math.min(
  startIndex.value + props.visibleRows,
  props.data.length
))
const offsetY = computed(() => startIndex.value * props.rowHeight)

const visibleData = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value)
})

const handleScroll = (e) => {
  scrollTop.value = e.target.scrollTop
}

onMounted(() => {
  // 初始化
})
</script>
```

### 10.2 懒加载

```javascript
// frontend/src/composables/useLazyLoad.js

import { ref } from 'vue'

export function useLazyLoad(fetchFunction, options = {}) {
  const {
    pageSize = 20,
    initialPage = 1
  } = options

  const data = ref([])
  const loading = ref(false)
  const currentPage = ref(initialPage)
  const hasMore = ref(true)

  const loadMore = async () => {
    if (loading.value || !hasMore.value) {
      return
    }

    loading.value = true

    try {
      const response = await fetchFunction({
        page: currentPage.value,
        page_size: pageSize
      })

      if (response.results) {
        data.value.push(...response.results)

        if (response.results.length < pageSize) {
          hasMore.value = false
        } else {
          currentPage.value++
        }
      }
    } catch (error) {
      console.error('加载失败:', error)
    } finally {
      loading.value = false
    }
  }

  const reset = () => {
    data.value = []
    currentPage.value = initialPage
    hasMore.value = true
  }

  return {
    data,
    loading,
    hasMore,
    loadMore,
    reset
  }
}
```

### 10.3 批量操作优化

```python
# apps/common/services/batch_service.py

from django.db import transaction
from apps.common.models import BaseModel

class BatchOperationService:
    """批量操作服务（性能优化）"""

    @staticmethod
    @transaction.atomic
    def batch_create(model_class, data_list, user=None):
        """
        批量创建记录（使用 bulk_create 优化性能）
        """
        if not data_list:
            return []

        instances = []
        for data in data_list:
            if user and 'created_by' not in data:
                data['created_by'] = user

            instances.append(model_class(**data))

        # 批量创建（性能提升显著）
        created_instances = model_class.objects.bulk_create(
            instances,
            batch_size=500
        )

        return created_instances

    @staticmethod
    @transaction.atomic
    def batch_update(model_class, ids, update_data, user=None):
        """
        批量更新记录（使用 bulk_update 优化性能）
        """
        if not ids:
            return 0

        instances = list(model_class.objects.filter(
            id__in=ids,
            is_deleted=False
        ))

        if not instances:
            return 0

        # 更新每个实例的字段
        for instance in instances:
            for field, value in update_data.items():
                setattr(instance, field, value)

            if user:
                instance.updated_by = user

        # 批量更新
        updated_count = model_class.objects.bulk_update(
            instances,
            list(update_data.keys()),
            batch_size=500
        )

        return updated_count

    @staticmethod
    @transaction.atomic
    def batch_soft_delete(model_class, ids, user=None):
        """
        批量软删除记录
        """
        if not ids:
            return 0

        # 使用 update 直接批量更新（性能最优）
        update_data = {
            'is_deleted': True,
            'deleted_at': timezone.now()
        }

        if user:
            update_data['deleted_by'] = user

        deleted_count = model_class.objects.filter(
            id__in=ids,
            is_deleted=False
        ).update(**update_data)

        return deleted_count
```

### 10.4 缓存策略

```python
# apps/common/cache/sub_object_cache.py

from django.core.cache import cache
from django.conf import settings

class SubObjectCache:
    """从对象缓存管理"""

    @staticmethod
    def get_cache_key(parent_model, parent_id, sub_object_code):
        """
        生成缓存键
        """
        return f"sub_object:{parent_model}:{parent_id}:{sub_object_code}"

    @staticmethod
    def get(parent_model, parent_id, sub_object_code):
        """
        获取缓存的从对象数据
        """
        cache_key = SubObjectCache.get_cache_key(
            parent_model,
            parent_id,
            sub_object_code
        )

        return cache.get(cache_key)

    @staticmethod
    def set(parent_model, parent_id, sub_object_code, data, timeout=None):
        """
        设置缓存
        """
        cache_key = SubObjectCache.get_cache_key(
            parent_model,
            parent_id,
            sub_object_code
        )

        timeout = timeout or settings.CACHE_TIMEOUT
        cache.set(cache_key, data, timeout)

    @staticmethod
    def delete(parent_model, parent_id, sub_object_code):
        """
        删除缓存
        """
        cache_key = SubObjectCache.get_cache_key(
            parent_model,
            parent_id,
            sub_object_code
        )

        cache.delete(cache_key)

    @staticmethod
    def invalidate_parent(parent_model, parent_id):
        """
        失效主对象的所有从对象缓存
        """
        # 使用通配符删除（需要配置缓存后端支持）
        pattern = f"sub_object:{parent_model}:{parent_id}:*"
        cache.delete_pattern(pattern)
```

---

## 附录

### A. 完整的从对象字段类型定义

```python
FIELD_TYPE_CHOICES = [
    # 基础字段类型
    ('text', '文本'),
    ('textarea', '多行文本'),
    ('number', '数字'),
    ('decimal', '金额'),
    ('date', '日期'),
    ('datetime', '日期时间'),
    ('boolean', '布尔值'),
    ('select', '下拉选择'),
    ('radio', '单选'),
    ('checkbox', '多选'),
    ('user', '用户选择器'),
    ('department', '部门选择器'),
    ('asset', '资产选择器'),
    ('location', '位置选择器'),

    # 高级字段类型
    ('file', '文件上传'),
    ('image', '图片上传'),
    ('formula', '公式字段'),
    ('reference', '关联字段'),

    # 主从关系字段类型
    ('subtable', '子表/从对象'),  # 子表格（可编辑表格）
    ('subform', '嵌套表单'),      # 嵌套表单（内联表单）
]
```

### B. 数据库迁移示例

```python
# Generate with: python manage.py makemigrations

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('system', '0002_datatemplate_organization_and_more'),
        ('procurement', '0002_procurementrequest_organization_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fielddefinition',
            name='sub_object_code',
            field=models.CharField(
                blank=True,
                help_text='关联的从对象编码，如 procurement_item',
                max_length=50,
                null=True,
                verbose_name='从对象编码'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='sub_table_columns',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='子表显示的列及顺序配置',
                verbose_name='子表列配置'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='allow_inline_edit',
            field=models.BooleanField(
                default=True,
                verbose_name='允许内联编辑'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='show_summary_row',
            field=models.BooleanField(
                default=False,
                verbose_name='显示合计行'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='summary_fields',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='需要计算合计的字段code列表',
                verbose_name='合计字段'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='min_rows',
            field=models.IntegerField(
                default=0,
                help_text='子表最少需要添加的行数',
                verbose_name='最小行数'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='max_rows',
            field=models.IntegerField(
                default=100,
                help_text='子表最多允许添加的行数',
                verbose_name='最大行数'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='form_layout_code',
            field=models.CharField(
                blank=True,
                help_text='嵌套表单使用的布局配置编码',
                max_length=50,
                null=True,
                verbose_name='表单布局编码'
            ),
        ),
        migrations.AddField(
            model_name='fielddefinition',
            name='allow_multiple',
            field=models.BooleanField(
                default=True,
                verbose_name='允许多条记录'
            ),
        ),
    ]
```

---

## 总结

本文档详细定义了 GZEAMS 平台的从对象/主从关系布局规范，涵盖：

1. **核心概念**：从对象定义、业务场景、数据模型规范
2. **字段类型扩展**：subtable、subform 字段类型及配置
3. **布局配置**：主从表布局、嵌套表单布局的完整 JSON 配置
4. **组件实现**：SubTableField.vue、SubFormField.vue 完整实现
5. **后端处理**：Serializer、Service、ViewSet 的主从数据处理
6. **权限控制**：从对象的细粒度权限控制
7. **性能优化**：虚拟滚动、懒加载、批量操作、缓存策略
8. **实践示例**：采购单、维护记录、联系方式的完整布局配置

所有实现均遵循 GZEAMS 核心架构规范：
- ✅ BaseModel 继承（组织隔离 + 软删除 + 审计字段）
- ✅ BaseCRUDService 统一数据处理
- ✅ 多组织数据隔离
- ✅ 统一 API 响应格式
- ✅ 标准错误处理

通过本文档的规范，可以实现灵活、高性能的主从关系业务场景支持。
