# PageLayout 页面布局配置完整规范

## 概述

`PageLayout` 是 GZEAMS 低代码平台的核心配置模型，用于定义业务对象的页面展示结构和交互方式。通过 JSON 配置，实现无需编码即可灵活配置表单、列表、详情、卡片和仪表板等多种页面布局。

---

## 1. 后端数据模型

### 1.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 1.2 PageLayout 模型定义

**表结构定义：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | UUIDField | PK | 主键（继承自BaseModel） |
| `organization` | ForeignKey | SET_NULL, to='organizations.Organization' | 所属组织（继承自BaseModel） |
| `is_deleted` | BooleanField | default=False | 软删除标记（继承自BaseModel） |
| `deleted_at` | DateTimeField | null, blank | 删除时间（继承自BaseModel） |
| `created_at` | DateTimeField | auto_now_add | 创建时间（继承自BaseModel） |
| `updated_at` | DateTimeField | auto_now | 更新时间（继承自BaseModel） |
| `created_by` | ForeignKey | SET_NULL, to='accounts.User' | 创建人（继承自BaseModel） |
| `custom_fields` | JSONField | default=dict | 自定义字段（继承自BaseModel） |
| `business_object` | ForeignKey | CASCADE, to='system.BusinessObject' | 业务对象关联 |
| `layout_type` | CharField(20) | choices: form/list/detail/card/dashboard | 布局类型 |
| `layout_config` | JSONField | default=dict | 布局配置（JSON格式） |
| `name` | CharField(100) | not_null | 布局名称（唯一标识） |
| `description` | TextField | blank | 布局描述 |
| `is_default` | BooleanField | default=False | 是否默认布局 |
| `is_active` | BooleanField | default=True | 是否启用 |
| `is_published` | BooleanField | default=False | 是否已发布 |
| `version` | CharField(20) | default='1.0.0' | 版本号（语义化版本） |
| `parent_layout` | ForeignKey | SET_NULL, null, blank, to='self' | 父布局（用于继承和版本管理） |
| `published_at` | DateTimeField | null, blank | 发布时间 |
| `published_by` | ForeignKey | SET_NULL, null, blank, to='accounts.User' | 发布人 |

**Meta 配置：**
- `db_table`: system_page_layout
- `unique_together`: ['business_object', 'name', 'organization']
- `ordering`: ['-created_at']
- `indexes`: [business_object+layout_type, is_default+is_active, is_published]

**核心方法：**

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `publish()` | user | None | 发布布局 |
| `unpublish()` | - | None | 取消发布 |
| `create_version()` | new_version | PageLayout | 创建新版本 |

---

## 2. JSON Schema 规范

> **核心引用**:
> 本文档仅定义 PageLayout 的顶层结构。所有子组件（`FieldReference`, `SectionConfig`, `ActionConfig` 等）的详细定义请参考 [00_layout_common_models.md](./00_layout_common_models.md)。

### 2.1 完整 JSON Schema 定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PageLayout Configuration Schema",
  "type": "object",
  "required": ["layout_type"],
  "properties": {
    "layout_type": {
      "type": "string",
      "enum": ["form", "list", "detail", "card", "dashboard"],
      "description": "布局类型"
    },
    "//": "For Form Layout",
    "sections": {
      "type": "array",
      "items": { "$ref": "./00_layout_common_models.md#/definitions/SectionConfig" }
    },
    "tabs": {
      "type": "array",
      "items": { "$ref": "./00_layout_common_models.md#/definitions/TabConfig" }
    },
    
    "//": "For List Layout",
    "default_columns": {
      "type": "array",
      "items": { "$ref": "./00_layout_common_models.md#/definitions/FieldReference" }
    },
    "toolbar_actions": {
      "type": "array",
      "items": { "$ref": "./00_layout_common_models.md#/definitions/ActionConfig" }
    },
    "row_actions": {
      "type": "array",
      "items": { "$ref": "./00_layout_common_models.md#/definitions/ActionConfig" }
    }
  }
}
```

---

## 3. 区块（Section）配置详解

详细模型定义请见 `00_layout_common_models.md`。

### 3.1 区块配置示例

```json
{
  "sections": [
    {
      "id": "section_basic_info",
      "title": "基本信息",
      "description": "资产的基本信息",
      "collapsible": true,
      "default_collapsed": false, // 注意：旧版本为 collapsed
      "columns": 2,
      "items": [
        { "field_code": "code" },
        { "field_code": "name" },
        {
          "field_code": "category",
          "help_text_override": "资产大类"
        }
      ],
      "visibility_rules": [
        {
            "conditions": [
                { "field_code": "asset_type", "operator": "eq", "value": "fixed_asset" }
            ]
        }
      ]
    }
  ]
}
```

### 3.2 区块属性说明

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | string | 是 | - | 区块唯一标识 |
| `title` | string | 是 | - | 区块标题 |
| `description` | string | 否 | - | 区块描述 |
| `collapsible` | boolean | 否 | false | 是否可折叠 |
| `collapsed` | boolean | 否 | false | 默认是否折叠 |
| `border` | boolean | 否 | true | 是否显示边框 |
| `columns` | integer | 否 | 1 | 列数（1-4列） |
| `fields` | array | 是 | - | 字段列表 |
| `visibility_rules` | array | 否 | - | 显示规则 |

### 3.3 区块嵌套支持

区块支持多层嵌套，用于构建复杂的表单结构：

```json
{
  "sections": [
    {
      "id": "section_main",
      "title": "主信息",
      "columns": 2,
      "fields": [
        "code",
        "name"
      ],
      "sections": [
        {
          "id": "subsection_detail",
          "title": "详细信息",
          "columns": 1,
          "fields": ["description"]
        }
      ]
    }
  ]
}
```

---

## 4. 标签页（Tabs）配置详解

### 4.1 标签页配置示例

```json
{
  "layout_type": "form",
  "layout_mode": "tabs",
  "tabs": [
    {
      "id": "tab_basic",
      "title": "基本信息",
      "icon": "Document",
      "sections": [
        {
          "id": "section_basic",
          "title": "基本资料",
          "columns": 2,
          "fields": ["code", "name", "category"]
        }
      ]
    },
    {
      "id": "tab_detail",
      "title": "详细信息",
      "icon": "InfoFilled",
      "sections": [
        {
          "id": "section_detail",
          "title": "详细资料",
          "columns": 2,
          "fields": ["specification", "brand", "model"]
        }
      ]
    },
    {
      "id": "tab_lifecycle",
      "title": "生命周期",
      "icon": "Clock",
      "disabled": false,
      "sections": [
        {
          "id": "section_lifecycle",
          "title": "生命周期信息",
          "columns": 1,
          "fields": ["purchase_date", "warranty_date", "depreciation_rate"]
        }
      ],
      "visibility_rules": [
        {
          "field": "asset_type",
          "operator": "eq",
          "value": "fixed_asset"
        }
      ]
    }
  ]
}
```

### 4.2 标签页属性说明

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `id` | string | 是 | - | 标签页唯一标识 |
| `title` | string | 是 | - | 标签页标题 |
| `icon` | string | 否 | - | 标签页图标（Element Plus Icon） |
| `disabled` | boolean | 否 | false | 是否禁用 |
| `sections` | array | 是 | - | 区块配置数组 |
| `visibility_rules` | array | 否 | - | 显示规则 |

---

## 5. 列表布局配置详解

### 5.1 完整列表布局示例

```json
{
  "layout_type": "list",
  "title": "资产列表",
  "icon": "List",
  "toolbar": {
    "actions": [
      {
        "key": "create",
        "label": "新增资产",
        "type": "primary",
        "icon": "Plus",
        "permission": "assets.add_asset",
        "handler": "handleCreate"
      },
      {
        "key": "batch_delete",
        "label": "批量删除",
        "type": "danger",
        "icon": "Delete",
        "permission": "assets.delete_asset",
        "confirm": "确定要删除选中的资产吗？",
        "handler": "handleBatchDelete"
      },
      {
        "key": "export",
        "label": "导出",
        "type": "success",
        "icon": "Download",
        "handler": "handleExport"
      }
    ],
    "filter": true,
    "refresh": true,
    "columns": true
  },
  "search_form": {
    "enabled": true,
    "inline": true,
    "label_width": "auto",
    "fields": [
      {
        "field": "keyword",
        "label": "关键词",
        "widget": "input",
        "placeholder": "资产编码/名称"
      },
      {
        "field": "category",
        "label": "资产分类",
        "widget": "select",
        "placeholder": "请选择分类"
      },
      {
        "field": "status",
        "label": "状态",
        "widget": "select",
        "placeholder": "请选择状态"
      },
      {
        "field": "purchase_date_range",
        "label": "采购日期",
        "widget": "daterange",
        "placeholder": "选择日期范围"
      }
    ]
  },
  "columns": [
    {
      "type": "selection",
      "width": 55,
      "fixed": "left"
    },
    {
      "prop": "code",
      "label": "资产编码",
      "width": 150,
      "fixed": "left",
      "sortable": true
    },
    {
      "prop": "name",
      "label": "资产名称",
      "minWidth": 200,
      "type": "link",
      "link_config": {
        "route": "/assets/detail",
        "query": {"id": "id"}
      }
    },
    {
      "prop": "category",
      "label": "分类",
      "width": 120
    },
    {
      "prop": "status",
      "label": "状态",
      "width": 100,
      "type": "tag",
      "tag_config": {
        "type_field": "status",
        "mapping": {
          "normal": "success",
          "maintenance": "warning",
          "scrapped": "danger",
          "lost": "info"
        }
      }
    },
    {
      "prop": "image",
      "label": "图片",
      "width": 100,
      "type": "image"
    },
    {
      "prop": "purchase_price",
      "label": "采购价格",
      "width": 120,
      "align": "right",
      "formatter": "formatCurrency"
    },
    {
      "prop": "purchase_date",
      "label": "采购日期",
      "width": 120,
      "sortable": true
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 200,
      "fixed": "right",
      "type": "action",
      "actions": [
        {
          "key": "view",
          "label": "查看",
          "type": "text",
          "permission": "assets.view_asset",
          "handler": "handleView"
        },
        {
          "key": "edit",
          "label": "编辑",
          "type": "text",
          "permission": "assets.change_asset",
          "handler": "handleEdit"
        },
        {
          "key": "delete",
          "label": "删除",
          "type": "text",
          "permission": "assets.delete_asset",
          "confirm": "确定要删除该资产吗？",
          "handler": "handleDelete"
        }
      ]
    }
  ],
  "pagination": {
    "enabled": true,
    "page_size": 20,
    "page_sizes": [10, 20, 50, 100],
    "layout": "total, sizes, prev, pager, next, jumper"
  }
}
```

### 5.2 列类型详解

#### 5.2.1 普通列（text）

```json
{
  "prop": "code",
  "label": "资产编码",
  "width": 150,
  "sortable": true
}
```

#### 5.2.2 标签列（tag）

```json
{
  "prop": "status",
  "label": "状态",
  "type": "tag",
  "tag_config": {
    "type_field": "status",
    "mapping": {
      "normal": "success",
      "maintenance": "warning",
      "scrapped": "danger"
    }
  }
}
```

#### 5.2.3 图片列（image）

```json
{
  "prop": "image",
  "label": "图片",
  "type": "image",
  "width": 100,
  "height": 60
}
```

#### 5.2.4 链接列（link）

```json
{
  "prop": "name",
  "label": "资产名称",
  "type": "link",
  "link_config": {
    "route": "/assets/detail",
    "query": {"id": "id"},
    "target": "_self"
  }
}
```

#### 5.2.5 操作列（action）

```json
{
  "prop": "actions",
  "label": "操作",
  "type": "action",
  "fixed": "right",
  "actions": [
    {
      "key": "edit",
      "label": "编辑",
      "type": "primary",
      "handler": "handleEdit"
    },
    {
      "key": "delete",
      "label": "删除",
      "type": "danger",
      "confirm": "确定要删除吗？",
      "handler": "handleDelete"
    }
  ]
}
```

#### 5.2.6 自定义插槽列（slot）

```json
{
  "prop": "custom_field",
  "label": "自定义列",
  "type": "slot",
  "slot_name": "custom_column"
}
```

---

## 6. 表单布局配置详解

### 6.1 完整表单布局示例

```json
{
  "layout_type": "form",
  "title": "资产信息",
  "icon": "Edit",
  "layout_mode": "sections",
  "sections": [
    {
      "id": "section_basic",
      "title": "基本信息",
      "columns": 2,
      "collapsible": false,
      "fields": [
        {
          "field": "code",
          "span": 1,
          "required": true,
          "readonly": false,
          "placeholder": "请输入资产编码"
        },
        {
          "field": "name",
          "span": 1,
          "required": true,
          "placeholder": "请输入资产名称"
        },
        {
          "field": "category",
          "span": 2,
          "required": true,
          "placeholder": "请选择资产分类"
        },
        {
          "field": "status",
          "span": 1,
          "readonly": true
        },
        {
          "field": "organization",
          "span": 1,
          "default_value": "@current_org"
        }
      ]
    },
    {
      "id": "section_detail",
      "title": "详细信息",
      "columns": 2,
      "collapsible": true,
      "collapsed": true,
      "fields": [
        {
          "field": "specification",
          "span": 2,
          "placeholder": "请输入规格型号"
        },
        {
          "field": "brand",
          "span": 1,
          "placeholder": "请输入品牌"
        },
        {
          "field": "model",
          "span": 1,
          "placeholder": "请输入型号"
        },
        {
          "field": "description",
          "span": 2,
          "placeholder": "请输入资产描述"
        }
      ]
    },
    {
      "id": "section_purchase",
      "title": "采购信息",
      "columns": 2,
      "collapsible": true,
      "fields": [
        {
          "field": "purchase_date",
          "span": 1,
          "placeholder": "请选择采购日期"
        },
        {
          "field": "purchase_price",
          "span": 1,
          "default_value": 0,
          "validation_rules": [
            {
              "type": "min",
              "value": 0,
              "message": "采购价格不能小于0"
            }
          ]
        },
        {
          "field": "supplier",
          "span": 2,
          "placeholder": "请选择供应商"
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "submit",
      "label": "提交",
      "type": "primary",
      "handler": "handleSubmit"
    },
    {
      "key": "reset",
      "label": "重置",
      "type": "default",
      "handler": "handleReset"
    },
    {
      "key": "cancel",
      "label": "取消",
      "type": "default",
      "handler": "handleCancel"
    }
  ]
}
```

### 6.2 字段配置详解

#### 6.2.1 基础字段配置

```json
{
  "field": "code",
  "span": 1,
  "label": "资产编码",
  "required": true,
  "readonly": false,
  "placeholder": "请输入资产编码",
  "default_value": ""
}
```

#### 6.2.2 字段跨列配置

```json
{
  "field": "description",
  "span": 2,
  "label": "描述"
}
```

在2列表单中，`span: 2` 表示该字段占满整行。

#### 6.2.3 字段显示规则

```json
{
  "field": "warranty_date",
  "visibility_rules": [
    {
      "field": "asset_type",
      "operator": "eq",
      "value": "fixed_asset",
      "logic": "and"
    },
    {
      "field": "has_warranty",
      "operator": "eq",
      "value": true,
      "logic": "and"
    }
  ]
}
```

#### 6.2.4 字段验证规则

```json
{
  "field": "purchase_price",
  "validation_rules": [
    {
      "type": "required",
      "message": "采购价格不能为空"
    },
    {
      "type": "min",
      "value": 0,
      "message": "采购价格不能小于0"
    },
    {
      "type": "pattern",
      "value": "^\\d+(\\.\\d{1,2})?$",
      "message": "请输入有效的价格格式"
    }
  ]
}
```

#### 6.2.5 字段依赖配置

```json
{
  "field": "subcategory",
  "dependencies": {
    "category": {
      "field": "category",
      "trigger": "change",
      "action": "load_options",
      "api": "/api/assets/subcategories/",
      "query_param": "category_id"
    }
  }
}
```

---

## 7. 详情页布局配置详解

### 7.1 完整详情页布局示例

```json
{
  "layout_type": "detail",
  "title": "资产详情",
  "icon": "View",
  "layout_mode": "tabs",
  "tabs": [
    {
      "id": "tab_basic",
      "title": "基本信息",
      "icon": "Document",
      "sections": [
        {
          "id": "section_descriptions",
          "type": "descriptions",
          "columns": 2,
          "fields": [
            {
              "field": "code",
              "label": "资产编码"
            },
            {
              "field": "name",
              "label": "资产名称"
            },
            {
              "field": "category",
              "label": "资产分类"
            },
            {
              "field": "status",
              "label": "状态",
              "type": "tag"
            },
            {
              "field": "organization",
              "label": "所属组织"
            },
            {
              "field": "created_at",
              "label": "创建时间"
            }
          ]
        }
      ]
    },
    {
      "id": "tab_lifecycle",
      "title": "生命周期",
      "icon": "Clock",
      "sections": [
        {
          "id": "section_timeline",
          "type": "timeline",
          "timeline_config": {
            "field": "status_logs",
            "timestamp_field": "created_at",
            "content_field": "description",
            "color_field": "status",
            "icon_field": "action_type"
          }
        }
      ]
    },
    {
      "id": "tab_related",
      "title": "关联数据",
      "icon": "Connection",
      "sections": [
        {
          "id": "section_loans",
          "title": "借用记录",
          "type": "related_list",
          "related_config": {
            "resource": "asset_loans",
            "foreign_key": "asset",
            "display_fields": ["loaner", "loan_date", "return_date", "status"],
            "limit": 5
          }
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "edit",
      "label": "编辑",
      "type": "primary",
      "icon": "Edit",
      "permission": "assets.change_asset",
      "handler": "handleEdit"
    },
    {
      "key": "delete",
      "label": "删除",
      "type": "danger",
      "icon": "Delete",
      "permission": "assets.delete_asset",
      "confirm": "确定要删除该资产吗？",
      "handler": "handleDelete"
    }
  ]
}
```

### 7.2 描述列表配置

```json
{
  "type": "descriptions",
  "columns": 2,
  "border": true,
  "size": "default",
  "fields": [
    {
      "field": "code",
      "label": "资产编码",
      "span": 1
    },
    {
      "field": "name",
      "label": "资产名称",
      "span": 1
    },
    {
      "field": "category",
      "label": "资产分类",
      "span": 1
    },
    {
      "field": "status",
      "label": "状态",
      "span": 1,
      "type": "tag",
      "tag_config": {
        "type_field": "status",
        "mapping": {
          "normal": "success",
          "maintenance": "warning"
        }
      }
    }
  ]
}
```

### 7.3 时间线配置

```json
{
  "type": "timeline",
  "timeline_config": {
    "field": "status_logs",
    "timestamp_field": "created_at",
    "content_field": "description",
    "color_field": "status",
    "icon_field": "action_type",
    "color_mapping": {
      "created": "primary",
      "updated": "success",
      "deleted": "danger"
    },
    "icon_mapping": {
      "created": "Plus",
      "updated": "Edit",
      "deleted": "Delete"
    }
  }
}
```

### 7.4 关联数据展示

```json
{
  "type": "related_list",
  "title": "借用记录",
  "related_config": {
    "resource": "asset_loans",
    "foreign_key": "asset",
    "display_fields": [
      {
        "field": "loaner",
        "label": "借用人"
      },
      {
        "field": "loan_date",
        "label": "借用日期"
      },
      {
        "field": "return_date",
        "label": "归还日期"
      },
      {
        "field": "status",
        "label": "状态",
        "type": "tag"
      }
    ],
    "limit": 5,
    "actions": [
      {
        "key": "view_all",
        "label": "查看全部",
        "type": "text",
        "route": "/asset-loans",
        "query": {"asset_id": "@id"}
      }
    ]
  }
}
```

---

## 8. 仪表板布局配置详解

### 8.1 完整仪表板布局示例

```json
{
  "layout_type": "dashboard",
  "title": "资产概览",
  "icon": "DataAnalysis",
  "refresh_interval": 300,
  "layout_grid": {
    "cols": 24,
    "rows": 12,
    "row_height": 60
  },
  "widgets": [
    {
      "id": "stat_total_assets",
      "type": "stat_card",
      "title": "资产总数",
      "icon": "Box",
      "theme": "primary",
      "grid": {
        "x": 0,
        "y": 0,
        "w": 6,
        "h": 3
      },
      "data_config": {
        "api": "/api/assets/statistics/total/",
        "method": "get",
        "value_field": "count",
        "trend_field": "trend",
        "comparison_field": "last_month"
      }
    },
    {
      "id": "stat_total_value",
      "type": "stat_card",
      "title": "资产总价值",
      "icon": "Money",
      "theme": "success",
      "grid": {
        "x": 6,
        "y": 0,
        "w": 6,
        "h": 3
      },
      "data_config": {
        "api": "/api/assets/statistics/value/",
        "method": "get",
        "value_field": "total_value",
        "formatter": "formatCurrency"
      }
    },
    {
      "id": "chart_by_category",
      "type": "chart",
      "title": "资产分类分布",
      "grid": {
        "x": 0,
        "y": 3,
        "w": 12,
        "h": 6
      },
      "chart_config": {
        "type": "pie",
        "data_config": {
          "api": "/api/assets/statistics/by-category/",
          "method": "get"
        },
        "series": [
          {
            "name_field": "category_name",
            "value_field": "count"
          }
        ]
      }
    },
    {
      "id": "chart_by_status",
      "type": "chart",
      "title": "资产状态分布",
      "grid": {
        "x": 12,
        "y": 3,
        "w": 12,
        "h": 6
      },
      "chart_config": {
        "type": "bar",
        "data_config": {
          "api": "/api/assets/statistics/by-status/",
          "method": "get"
        },
        "x_axis": {
          "field": "status",
          "label": "状态"
        },
        "y_axis": {
          "field": "count",
          "label": "数量"
        }
      }
    },
    {
      "id": "recent_activities",
      "type": "list",
      "title": "最近活动",
      "grid": {
        "x": 0,
        "y": 9,
        "w": 12,
        "h": 3
      },
      "list_config": {
        "api": "/api/assets/activities/recent/",
        "method": "get",
        "limit": 5,
        "item_template": "activity_item"
      }
    }
  ]
}
```

### 8.2 卡片组件配置

```json
{
  "id": "stat_card",
  "type": "stat_card",
  "title": "资产总数",
  "icon": "Box",
  "theme": "primary",
  "grid": {
    "x": 0,
    "y": 0,
    "w": 6,
    "h": 3
  },
  "data_config": {
    "api": "/api/assets/statistics/total/",
    "method": "get",
    "value_field": "count",
    "trend_field": "trend",
    "comparison_field": "last_month",
    "formatter": "formatNumber"
  },
  "actions": [
    {
      "key": "detail",
      "label": "查看详情",
      "type": "text",
      "route": "/assets"
    }
  ]
}
```

**主题类型：**
- `primary` - 主色（蓝色）
- `success` - 成功色（绿色）
- `warning` - 警告色（橙色）
- `danger` - 危险色（红色）
- `info` - 信息色（灰色）

### 8.3 图表容器配置

```json
{
  "id": "chart_pie",
  "type": "chart",
  "title": "资产分类分布",
  "grid": {
    "x": 0,
    "y": 3,
    "w": 12,
    "h": 6
  },
  "chart_config": {
    "type": "pie",
    "library": "echarts",
    "data_config": {
      "api": "/api/assets/statistics/by-category/",
      "method": "get",
      "refresh_interval": 300
    },
    "series": [
      {
        "type": "pie",
        "name_field": "category_name",
        "value_field": "count",
        "radius": ["40%", "70%"]
      }
    ],
    "legend": {
      "show": true,
      "position": "right"
    },
    "tooltip": {
      "trigger": "item",
      "formatter": "{b}: {c} ({d}%)"
    }
  }
}
```

**支持的图表类型：**
- `line` - 折线图
- `bar` - 柱状图
- `pie` - 饼图
- `area` - 面积图
- `scatter` - 散点图
- `gauge` - 仪表盘

---

## 9. 卡片布局配置详解

### 9.1 完整卡片布局示例

```json
{
  "layout_type": "card",
  "title": "资产卡片",
  "icon": "Grid",
  "grid_config": {
    "columns": 4,
    "gap": 16,
    "responsive": {
      "xs": 1,
      "sm": 2,
      "md": 3,
      "lg": 4,
      "xl": 4
    }
  },
  "card_config": {
    "cover_field": "image",
    "title_field": "name",
    "subtitle_field": "code",
    "description_field": "description",
    "actions": [
      {
        "key": "view",
        "label": "查看",
        "type": "primary",
        "handler": "handleView"
      },
      {
        "key": "edit",
        "label": "编辑",
        "type": "default",
        "handler": "handleEdit"
      }
    ],
    "extra_fields": [
      {
        "field": "category",
        "label": "分类",
        "type": "text"
      },
      {
        "field": "status",
        "label": "状态",
        "type": "tag"
      },
      {
        "field": "purchase_price",
        "label": "价格",
        "type": "text",
        "formatter": "formatCurrency"
      }
    ]
  }
}
```

### 9.2 卡片配置属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `cover_field` | string | 封面图片字段 |
| `title_field` | string | 标题字段 |
| `subtitle_field` | string | 副标题字段 |
| `description_field` | string | 描述字段 |
| `actions` | array | 操作按钮 |
| `extra_fields` | array | 额外显示字段 |

---

## 10. API 接口设计

### 10.1 API 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/page-layouts/` | 获取布局列表 |
| GET | `/api/system/page-layouts/{id}/` | 获取布局详情 |
| POST | `/api/system/page-layouts/` | 创建布局 |
| PUT | `/api/system/page-layouts/{id}/` | 更新布局 |
| PATCH | `/api/system/page-layouts/{id}/` | 部分更新布局 |
| DELETE | `/api/system/page-layouts/{id}/` | 删除布局 |
| POST | `/api/system/page-layouts/{id}/publish/` | 发布布局 |
| POST | `/api/system/page-layouts/{id}/unpublish/` | 取消发布布局 |
| POST | `/api/system/page-layouts/{id}/set-default/` | 设为默认布局 |
| GET | `/api/system/page-layouts/by-object/{object_id}/` | 获取业务对象的布局列表 |
| GET | `/api/system/page-layouts/default/{object_id}/` | 获取业务对象的默认布局 |

### 10.2 API 请求示例

#### 10.2.1 获取布局列表

```http
GET /api/system/page-layouts/?business_object=asset&layout_type=form
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "uuid-1",
        "business_object": "asset",
        "layout_type": "form",
        "name": "default_form",
        "description": "默认表单布局",
        "is_default": true,
        "is_active": true,
        "is_published": true,
        "version": "1.0.0",
        "layout_config": {...},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### 10.2.2 创建布局

```http
POST /api/system/page-layouts/
Authorization: Bearer {token}
Content-Type: application/json

{
  "business_object": "asset",
  "layout_type": "form",
  "name": "custom_form",
  "description": "自定义表单布局",
  "layout_config": {...}
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "布局创建成功",
  "data": {
    "id": "uuid-new",
    "business_object": "asset",
    "layout_type": "form",
    "name": "custom_form",
    "layout_config": {...},
    "version": "1.0.0"
  }
}
```

#### 10.2.3 发布布局

```http
POST /api/system/page-layouts/{id}/publish/
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "message": "布局发布成功",
  "data": {
    "id": "uuid",
    "is_published": true,
    "published_at": "2024-01-15T10:30:00Z",
    "published_by": {
      "id": "user-uuid",
      "username": "admin"
    }
  }
}
```

#### 10.2.4 获取默认布局

```http
GET /api/system/page-layouts/default/{object_id}/
Authorization: Bearer {token}
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "business_object": "asset",
    "layout_type": "form",
    "name": "default_form",
    "is_default": true,
    "layout_config": {...}
  }
}
```

### 10.3 Serializer 定义

```python
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import PageLayout

class PageLayoutSerializer(BaseModelSerializer):
    """
    页面布局配置序列化器
    """
    business_object_name = serializers.CharField(
        source='business_object.name',
        read_only=True
    )

    published_by_info = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = PageLayout
        fields = BaseModelSerializer.Meta.fields + [
            'business_object',
            'business_object_name',
            'layout_type',
            'name',
            'description',
            'layout_config',
            'is_default',
            'is_active',
            'is_published',
            'version',
            'parent_layout',
            'published_at',
            'published_by',
            'published_by_info'
        ]
        read_only_fields = [
            'version',
            'published_at',
            'published_by'
        ]

    def get_published_by_info(self, obj):
        """获取发布人信息"""
        if obj.published_by:
            return {
                'id': str(obj.published_by.id),
                'username': obj.published_by.username,
                'full_name': obj.published_by.get_full_name()
            }
        return None

    def validate_layout_config(self, value):
        """验证布局配置"""
        import jsonschema
        from .schema import PAGE_LAYOUT_SCHEMA

        try:
            jsonschema.validate(
                value,
                PAGE_LAYOUT_SCHEMA[value.get('layout_type', 'form')]
            )
        except jsonschema.ValidationError as e:
            raise serializers.ValidationError(f"布局配置验证失败: {e.message}")

        return value

    def validate(self, attrs):
        """验证数据"""
        # 验证默认布局唯一性
        if attrs.get('is_default'):
            business_object = attrs.get('business_object') or self.instance.business_object
            layout_type = attrs.get('layout_type') or self.instance.layout_type

            exists = PageLayout.objects.filter(
                business_object=business_object,
                layout_type=layout_type,
                is_default=True
            ).exclude(id=self.instance.id if self.instance else None).exists()

            if exists:
                raise serializers.ValidationError(
                    "该业务对象已存在默认布局，每个布局类型只能有一个默认布局"
                )

        return attrs


class PageLayoutListSerializer(serializers.ModelSerializer):
    """
    页面布局列表序列化器（简化版）
    """
    class Meta:
        model = PageLayout
        fields = [
            'id',
            'business_object',
            'layout_type',
            'name',
            'description',
            'is_default',
            'is_active',
            'is_published',
            'version',
            'created_at',
            'updated_at'
        ]
```

### 10.4 ViewSet 定义

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.permissions.base import IsAuthenticatedOrReadOnly
from .models import PageLayout
from .serializers import (
    PageLayoutSerializer,
    PageLayoutListSerializer
)

class PageLayoutViewSet(BaseModelViewSet):
    """
    页面布局配置视图集
    """
    queryset = PageLayout.objects.select_related(
        'business_object',
        'parent_layout',
        'published_by',
        'organization'
    ).all()

    serializer_class = PageLayoutSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        """根据action选择序列化器"""
        if self.action == 'list':
            return PageLayoutListSerializer
        return PageLayoutSerializer

    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()

        # 过滤业务对象
        business_object = self.request.query_params.get('business_object')
        if business_object:
            queryset = queryset.filter(business_object__code=business_object)

        # 过滤布局类型
        layout_type = self.request.query_params.get('layout_type')
        if layout_type:
            queryset = queryset.filter(layout_type=layout_type)

        # 过滤发布状态
        is_published = self.request.query_params.get('is_published')
        if is_published is not None:
            queryset = queryset.filter(is_published=is_published.lower() == 'true')

        # 过滤默认布局
        is_default = self.request.query_params.get('is_default')
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == 'true')

        return queryset

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布布局"""
        layout = self.get_object()
        layout.publish(request.user)
        serializer = self.get_serializer(layout)
        return Response({
            'success': True,
            'message': '布局发布成功',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """取消发布布局"""
        layout = self.get_object()
        layout.unpublish()
        serializer = self.get_serializer(layout)
        return Response({
            'success': True,
            'message': '布局已取消发布',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """设为默认布局"""
        layout = self.get_object()

        # 取消其他默认布局
        PageLayout.objects.filter(
            business_object=layout.business_object,
            layout_type=layout.layout_type,
            is_default=True
        ).update(is_default=False)

        # 设置当前布局为默认
        layout.is_default = True
        layout.save()

        serializer = self.get_serializer(layout)
        return Response({
            'success': True,
            'message': '已设为默认布局',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def by_object(self, request):
        """获取业务对象的布局列表"""
        object_id = request.query_params.get('object_id')
        if not object_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '缺少object_id参数'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        layouts = self.get_queryset().filter(business_object__id=object_id)
        serializer = PageLayoutListSerializer(layouts, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def default(self, request, object_id=None):
        """获取业务对象的默认布局"""
        if not object_id:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '缺少object_id参数'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            layout = self.get_queryset().get(
                business_object__id=object_id,
                is_default=True
            )
            serializer = self.get_serializer(layout)

            return Response({
                'success': True,
                'data': serializer.data
            })
        except PageLayout.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '未找到默认布局'
                }
            }, status=status.HTTP_404_NOT_FOUND)
```

---

## 11. 前端组件实现指南

### 11.1 动态渲染引擎核心组件

#### DynamicForm.vue
```vue
<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="formRules"
    :label-width="labelWidth"
    :inline="inline"
  >
    <template v-if="layoutMode === 'tabs'">
      <el-tabs v-model="activeTab">
        <el-tab-pane
          v-for="tab in layoutConfig.tabs"
          :key="tab.id"
          :label="tab.title"
          :name="tab.id"
          :disabled="tab.disabled"
        >
          <layout-sections
            :sections="tab.sections"
            :form-data="formData"
            :form-rules="formRules"
          />
        </el-tab-pane>
      </el-tabs>
    </template>

    <template v-else>
      <layout-sections
        :sections="layoutConfig.sections"
        :form-data="formData"
        :form-rules="formRules"
      />
    </template>
  </el-form>
</template>
```

#### DynamicList.vue
```vue
<template>
  <div class="dynamic-list">
    <layout-toolbar
      :toolbar="layoutConfig.toolbar"
      @action="handleToolbarAction"
    />

    <layout-search-form
      v-if="layoutConfig.search_form?.enabled"
      :search-config="layoutConfig.search_form"
      @search="handleSearch"
      @reset="handleReset"
    />

    <el-table
      :data="tableData"
      :columns="layoutConfig.columns"
      @sort-change="handleSortChange"
    >
      <template v-for="column in layoutConfig.columns" #[column.slot_name]="scope">
        <slot :name="column.slot_name" :row="scope.row" :column="column" />
      </template>
    </el-table>

    <layout-pagination
      v-if="layoutConfig.pagination?.enabled"
      :pagination="layoutConfig.pagination"
      @page-change="handlePageChange"
    />
  </div>
</template>
```

### 11.2 字段渲染器

#### FieldRenderer.vue
```vue
<template>
  <el-form-item
    :label="fieldConfig.label || fieldLabel"
    :prop="fieldConfig.field"
    :required="fieldConfig.required"
  >
    <!-- 文本输入 -->
    <el-input
      v-if="fieldType === 'text'"
      v-model="localValue"
      :placeholder="fieldConfig.placeholder"
      :disabled="fieldConfig.readonly || fieldConfig.disabled"
      @input="handleInput"
    />

    <!-- 数字输入 -->
    <el-input-number
      v-else-if="fieldType === 'number'"
      v-model="localValue"
      :disabled="fieldConfig.readonly"
      @change="handleChange"
    />

    <!-- 选择器 -->
    <el-select
      v-else-if="fieldType === 'select'"
      v-model="localValue"
      :placeholder="fieldConfig.placeholder"
      :disabled="fieldConfig.readonly"
      @change="handleChange"
    >
      <el-option
        v-for="option in fieldConfig.options"
        :key="option.value"
        :label="option.label"
        :value="option.value"
      />
    </el-select>

    <!-- 日期选择器 -->
    <el-date-picker
      v-else-if="fieldType === 'date'"
      v-model="localValue"
      type="date"
      :placeholder="fieldConfig.placeholder"
      :disabled="fieldConfig.readonly"
      @change="handleChange"
    />

    <!-- 更多字段类型... -->
  </el-form-item>
</template>
```

---

## 12. 使用示例

### 12.1 创建资产表单布局

```python
from apps.system.models import PageLayout, BusinessObject

# 获取业务对象
asset_object = BusinessObject.objects.get(code='asset')

# 创建表单布局
form_layout = PageLayout.objects.create(
    business_object=asset_object,
    layout_type='form',
    name='asset_form',
    description='资产表单布局',
    is_default=True,
    organization_id=org_id,
    layout_config={
        "layout_type": "form",
        "layout_mode": "tabs",
        "tabs": [
            {
                "id": "tab_basic",
                "title": "基本信息",
                "icon": "Document",
                "sections": [
                    {
                        "id": "section_basic",
                        "title": "基本资料",
                        "columns": 2,
                        "fields": ["code", "name", "category", "status"]
                    }
                ]
            },
            {
                "id": "tab_detail",
                "title": "详细信息",
                "icon": "InfoFilled",
                "sections": [...]
            }
        ],
        "actions": [
            {
                "key": "submit",
                "label": "提交",
                "type": "primary",
                "handler": "handleSubmit"
            }
        ]
    }
)

# 发布布局
form_layout.publish(user=request.user)
```

### 12.2 创建资产列表布局

```python
# 创建列表布局
list_layout = PageLayout.objects.create(
    business_object=asset_object,
    layout_type='list',
    name='asset_list',
    description='资产列表布局',
    is_default=True,
    organization_id=org_id,
    layout_config={
        "layout_type": "list",
        "title": "资产列表",
        "toolbar": {
            "actions": [
                {
                    "key": "create",
                    "label": "新增资产",
                    "type": "primary",
                    "icon": "Plus",
                    "handler": "handleCreate"
                }
            ]
        },
        "columns": [
            {"prop": "code", "label": "资产编码", "width": 150},
            {"prop": "name", "label": "资产名称", "minWidth": 200},
            {"prop": "category", "label": "分类", "width": 120},
            {
                "prop": "status",
                "label": "状态",
                "type": "tag",
                "tag_config": {
                    "type_field": "status",
                    "mapping": {
                        "normal": "success",
                        "maintenance": "warning"
                    }
                }
            }
        ],
        "pagination": {
            "enabled": True,
            "page_size": 20
        }
    }
)

list_layout.publish(user=request.user)
```

---

## 13. 最佳实践

### 13.1 布局设计原则

1. **保持简单**：避免过于复杂的嵌套结构
2. **一致性**：相同业务对象的布局风格保持一致
3. **性能优化**：列表布局避免显示过多列
4. **响应式设计**：考虑不同屏幕尺寸的显示效果
5. **版本管理**：重大布局变更时创建新版本

### 13.2 字段配置建议

1. **必填字段**：明确标记必填字段，提供清晰的验证提示
2. **字段顺序**：按照业务逻辑和用户习惯排序
3. **默认值**：合理设置字段默认值，减少用户输入
4. **字段分组**：相关字段组织在同一区块或标签页
5. **显示规则**：合理使用显示规则，避免界面过于复杂

### 13.3 性能优化建议

1. **懒加载**：大列表使用虚拟滚动
2. **缓存策略**：布局配置客户端缓存
3. **按需加载**：标签页内容按需加载
4. **数据分页**：列表数据必须分页
5. **图表优化**：仪表板数据使用增量更新

---

## 14. 总结

PageLayout 是 GZEAMS 低代码平台的核心配置模型，通过 JSON 配置实现：

1. **灵活的页面布局**：支持表单、列表、详情、卡片、仪表板等多种布局类型
2. **动态渲染**：前端根据配置动态渲染页面，无需编码
3. **版本管理**：支持布局版本控制和发布流程
4. **组织隔离**：每个组织可以有自己的布局配置
5. **丰富的组件**：支持多种字段类型、图表、操作按钮等

通过合理使用 PageLayout，可以快速构建符合业务需求的固定资产管理界面，大幅提升开发效率和用户体验。
