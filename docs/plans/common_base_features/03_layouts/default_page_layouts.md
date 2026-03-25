# GZEAMS 默认页面布局规范

## 文档信息

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-01-15 |
| 适用对象 | GZEAMS 系统所有业务对象 |
| 配置目标 | 定义各业务对象的默认页面结构、字段排列和区块分组 |

---

## 1. 默认布局原则

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 默认页面布局是 PageLayout 记录的默认配置（is_default=True），系统初始化时自动创建。业务对象的默认布局配置存储在 PageLayout.layout_config JSON 字段中。

### 1.1 布局设计理念

**核心理念：约定优于配置，提供合理默认值**

GZEAMS 系统为每个业务对象提供预定义的默认页面布局，这些布局遵循以下设计原则：

1. **用户友好性**：界面布局符合用户操作习惯，核心信息一目了然
2. **业务逻辑性**：字段分组与业务流程匹配，相关信息集中展示
3. **响应式设计**：支持不同屏幕尺寸，移动端和桌面端均有良好体验
4. **一致性**：相同类型业务对象的布局风格保持一致
5. **可扩展性**：默认布局可作为基础，支持通过 PageLayout 模型自定义扩展

### 1.2 默认布局层级结构

```
业务对象 (Business Object)
    │
    ├── 列表页布局 (List Layout)        - 数据浏览、筛选、批量操作
    ├── 表单页布局 (Form Layout)        - 新增/编辑数据
    ├── 详情页布局 (Detail Layout)      - 查看单条数据详情
    └── 卡片布局 (Card Layout)          - 可视化卡片展示（可选）
```

### 1.3 默认字段排列顺序规范

**标准字段优先级顺序（从高到低）：**

```
1. 核心标识字段     - code, name, no, title 等
2. 分类/类型字段    - category, type, status 等
3. 关联对象字段     - organization, department, user 等
4. 日期时间字段     - created_at, updated_at, purchase_date 等
5. 金额数值字段     - price, amount, value 等
6. 详细描述字段     - description, remark, note 等
7. 审计字段        - created_by, updated_by (通常在详情页底部)
```

### 1.4 默认区块分组规范

**标准区块定义：**

| 区块名称 | 英文标识 | 适用场景 | 字段数量建议 |
|---------|---------|----------|-------------|
| 基本信息 | basic_info | 所有业务对象 | 4-8个字段 |
| 详细信息 | detail_info | 大多数业务对象 | 6-12个字段 |
| 业务属性 | business_info | 有特定业务规则的对象 | 按需 |
| 财务信息 | financial_info | 涉及金额的对象 | 3-6个字段 |
| 时间信息 | time_info | 涉及时间维度的对象 | 3-5个字段 |
| 审计信息 | audit_info | 所有对象（详情页） | 4-6个字段 |
| 附件信息 | attachment_info | 需要附件的对象 | 按需 |
| 关联数据 | related_info | 有主从关系的对象 | 按需 |

### 1.5 默认布局配置规范

**列数配置规范：**

| 布局类型 | 默认列数 | 适用场景 |
|---------|---------|---------|
| 简单表单 | 1列 | 字段较少（<10个） |
| 标准表单 | 2列 | 大多数业务对象（推荐） |
| 复杂表单 | 3-4列 | 字段很多（>20个）且需要密集展示 |
| 详情页 | 2列 | 标准详情展示 |
| 列表页 | - | 根据业务需求定制列 |

---

## 2. 资产 (Asset) 默认布局定义

### 2.1 资产表单页布局 (Form Layout)

#### 2.1.1 标准表单模式（sections 模式）

```json
{
  "layout_type": "form",
  "title": "资产信息",
  "layout_mode": "sections",
  "label_width": "120px",
  "sections": [
    {
      "id": "section_basic",
      "title": "基本信息",
      "description": "资产的基本标识和分类信息",
      "collapsible": false,
      "columns": 2,
      "fields": [
        {
          "field": "code",
          "span": 1,
          "required": true,
          "readonly": false,
          "placeholder": "请输入资产编码",
          "validation_rules": [
            {"type": "required", "message": "资产编码不能为空"},
            {"type": "maxLength", "value": 50, "message": "资产编码不能超过50个字符"}
          ]
        },
        {
          "field": "name",
          "span": 1,
          "required": true,
          "placeholder": "请输入资产名称",
          "validation_rules": [
            {"type": "required", "message": "资产名称不能为空"},
            {"type": "maxLength", "value": 200, "message": "资产名称不能超过200个字符"}
          ]
        },
        {
          "field": "category",
          "span": 1,
          "required": true,
          "placeholder": "请选择资产分类"
        },
        {
          "field": "status",
          "span": 1,
          "readonly": true,
          "default_value": "normal"
        },
        {
          "field": "organization",
          "span": 2,
          "default_value": "@current_org",
          "readonly": true
        }
      ]
    },
    {
      "id": "section_detail",
      "title": "详细信息",
      "description": "资产的规格、品牌、型号等详细信息",
      "collapsible": true,
      "collapsed": false,
      "columns": 2,
      "fields": [
        {
          "field": "specification",
          "span": 2,
          "placeholder": "请输入规格型号",
          "label": "规格型号"
        },
        {
          "field": "brand",
          "span": 1,
          "placeholder": "请输入品牌",
          "label": "品牌"
        },
        {
          "field": "model",
          "span": 1,
          "placeholder": "请输入型号",
          "label": "型号"
        },
        {
          "field": "serial_number",
          "span": 1,
          "placeholder": "请输入序列号",
          "label": "序列号"
        },
        {
          "field": "quantity",
          "span": 1,
          "default_value": 1,
          "label": "数量"
        },
        {
          "field": "unit",
          "span": 1,
          "placeholder": "请选择单位",
          "label": "计量单位"
        },
        {
          "field": "description",
          "span": 2,
          "placeholder": "请输入资产描述",
          "label": "资产描述"
        }
      ]
    },
    {
      "id": "section_purchase",
      "title": "采购信息",
      "description": "资产的采购、供应商、价格等信息",
      "collapsible": true,
      "collapsed": true,
      "columns": 2,
      "fields": [
        {
          "field": "purchase_date",
          "span": 1,
          "placeholder": "请选择采购日期",
          "label": "采购日期"
        },
        {
          "field": "purchase_price",
          "span": 1,
          "default_value": 0,
          "placeholder": "请输入采购价格",
          "label": "采购价格",
          "validation_rules": [
            {"type": "min", "value": 0, "message": "采购价格不能小于0"}
          ]
        },
        {
          "field": "supplier",
          "span": 2,
          "placeholder": "请选择供应商",
          "label": "供应商"
        },
        {
          "field": "invoice_number",
          "span": 1,
          "placeholder": "请输入发票号",
          "label": "发票号"
        },
        {
          "field": "warranty_period",
          "span": 1,
          "placeholder": "请输入保修期（月）",
          "label": "保修期",
          "default_value": 12
        }
      ]
    },
    {
      "id": "section_location",
      "title": "存放信息",
      "description": "资产的存放位置、使用人等信息",
      "collapsible": true,
      "collapsed": true,
      "columns": 2,
      "fields": [
        {
          "field": "location",
          "span": 1,
          "placeholder": "请选择存放位置",
          "label": "存放位置"
        },
        {
          "field": "custodian",
          "span": 1,
          "placeholder": "请选择保管人",
          "label": "保管人"
        },
        {
          "field": "department",
          "span": 1,
          "placeholder": "请选择使用部门",
          "label": "使用部门"
        },
        {
          "field": "user",
          "span": 1,
          "placeholder": "请选择使用人",
          "label": "使用人"
        }
      ]
    },
    {
      "id": "section_depreciation",
      "title": "折旧信息",
      "description": "固定资产的折旧方法和计算参数",
      "collapsible": true,
      "collapsed": true,
      "columns": 2,
      "fields": [
        {
          "field": "depreciation_method",
          "span": 1,
          "default_value": "straight_line",
          "label": "折旧方法"
        },
        {
          "field": "useful_life",
          "span": 1,
          "default_value": 60,
          "label": "使用年限（月）"
        },
        {
          "field": "residual_rate",
          "span": 1,
          "default_value": 5.00,
          "label": "净残值率（%）"
        },
        {
          "field": "start_depreciation_date",
          "span": 1,
          "placeholder": "请选择开始折旧日期",
          "label": "开始折旧日期"
        }
      ],
      "visibility_rules": [
        {
          "field": "category.is_fixed_asset",
          "operator": "eq",
          "value": true
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "submit",
      "label": "提交",
      "type": "primary",
      "icon": "Check",
      "handler": "handleSubmit"
    },
    {
      "key": "reset",
      "label": "重置",
      "type": "default",
      "icon": "RefreshLeft",
      "handler": "handleReset"
    },
    {
      "key": "cancel",
      "label": "取消",
      "type": "default",
      "icon": "Close",
      "handler": "handleCancel"
    }
  ]
}
```

#### 2.1.2 标签页模式（tabs 模式）

```json
{
  "layout_type": "form",
  "title": "资产信息",
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
          "fields": ["code", "name", "category", "status", "organization"]
        },
        {
          "id": "section_detail",
          "title": "详细资料",
          "columns": 2,
          "fields": [
            "specification", "brand", "model", "serial_number",
            "quantity", "unit", "description"
          ]
        }
      ]
    },
    {
      "id": "tab_purchase",
      "title": "采购信息",
      "icon": "ShoppingCart",
      "sections": [
        {
          "id": "section_purchase",
          "title": "采购详情",
          "columns": 2,
          "fields": [
            "purchase_date", "purchase_price", "supplier",
            "invoice_number", "warranty_period"
          ]
        }
      ]
    },
    {
      "id": "tab_location",
      "title": "存放信息",
      "icon": "Location",
      "sections": [
        {
          "id": "section_location",
          "title": "位置与责任人",
          "columns": 2,
          "fields": [
            "location", "custodian", "department", "user"
          ]
        }
      ]
    },
    {
      "id": "tab_depreciation",
      "title": "折旧信息",
      "icon": "TrendCharts",
      "disabled": false,
      "sections": [
        {
          "id": "section_depreciation",
          "title": "折旧计算",
          "columns": 2,
          "fields": [
            "depreciation_method", "useful_life",
            "residual_rate", "start_depreciation_date"
          ]
        }
      ],
      "visibility_rules": [
        {
          "field": "category.is_fixed_asset",
          "operator": "eq",
          "value": true
        }
      ]
    }
  ],
  "actions": [
    {"key": "submit", "label": "提交", "type": "primary"},
    {"key": "reset", "label": "重置", "type": "default"},
    {"key": "cancel", "label": "取消", "type": "default"}
  ]
}
```

### 2.2 资产列表页布局 (List Layout)

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
      },
      {
        "key": "import",
        "label": "导入",
        "type": "warning",
        "icon": "Upload",
        "handler": "handleImport"
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
        "placeholder": "资产编码/名称/序列号"
      },
      {
        "field": "category",
        "label": "资产分类",
        "widget": "tree_select",
        "placeholder": "请选择分类"
      },
      {
        "field": "status",
        "label": "状态",
        "widget": "select",
        "placeholder": "请选择状态"
      },
      {
        "field": "organization",
        "label": "所属组织",
        "widget": "select",
        "placeholder": "请选择组织"
      },
      {
        "field": "location",
        "label": "存放位置",
        "widget": "select",
        "placeholder": "请选择位置"
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
      "width": 150,
      "field": "category.name"
    },
    {
      "prop": "specification",
      "label": "规格型号",
      "width": 150,
      "show_overflow_tooltip": true
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
          "in_use": "primary",
          "maintenance": "warning",
          "scrapped": "danger",
          "lost": "info"
        }
      }
    },
    {
      "prop": "location",
      "label": "存放位置",
      "width": 150,
      "field": "location.name"
    },
    {
      "prop": "custodian",
      "label": "保管人",
      "width": 120,
      "field": "custodian.username"
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
      "sortable": true,
      "formatter": "formatDate"
    },
    {
      "prop": "organization",
      "label": "所属组织",
      "width": 150,
      "field": "organization.name"
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 250,
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
          "key": "loan",
          "label": "借用",
          "type": "text",
          "permission": "assets.loan_asset",
          "handler": "handleLoan"
        },
        {
          "key": "transfer",
          "label": "转移",
          "type": "text",
          "permission": "assets.transfer_asset",
          "handler": "handleTransfer"
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

### 2.3 资产详情页布局 (Detail Layout)

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
          "border": true,
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
              "span": 1,
              "type": "object",
              "display_field": "name"
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
            },
            {
              "field": "specification",
              "label": "规格型号",
              "span": 1
            },
            {
              "field": "serial_number",
              "label": "序列号",
              "span": 1
            },
            {
              "field": "brand",
              "label": "品牌",
              "span": 1
            },
            {
              "field": "model",
              "label": "型号",
              "span": 1
            },
            {
              "field": "quantity",
              "label": "数量",
              "span": 1
            },
            {
              "field": "unit",
              "label": "计量单位",
              "span": 1
            },
            {
              "field": "description",
              "label": "资产描述",
              "span": 2
            }
          ]
        }
      ]
    },
    {
      "id": "tab_purchase",
      "title": "采购信息",
      "icon": "ShoppingCart",
      "sections": [
        {
          "id": "section_purchase",
          "type": "descriptions",
          "columns": 2,
          "border": true,
          "fields": [
            {
              "field": "purchase_date",
              "label": "采购日期",
              "span": 1,
              "formatter": "formatDate"
            },
            {
              "field": "purchase_price",
              "label": "采购价格",
              "span": 1,
              "formatter": "formatCurrency"
            },
            {
              "field": "supplier",
              "label": "供应商",
              "span": 1,
              "type": "object",
              "display_field": "name"
            },
            {
              "field": "invoice_number",
              "label": "发票号",
              "span": 1
            },
            {
              "field": "warranty_period",
              "label": "保修期（月）",
              "span": 1
            },
            {
              "field": "warranty_expiry_date",
              "label": "保修到期日",
              "span": 1,
              "formatter": "formatDate"
            }
          ]
        }
      ]
    },
    {
      "id": "tab_location",
      "title": "存放信息",
      "icon": "Location",
      "sections": [
        {
          "id": "section_location",
          "type": "descriptions",
          "columns": 2,
          "border": true,
          "fields": [
            {
              "field": "location",
              "label": "存放位置",
              "span": 1,
              "type": "object",
              "display_field": "name"
            },
            {
              "field": "custodian",
              "label": "保管人",
              "span": 1,
              "type": "object",
              "display_field": "username"
            },
            {
              "field": "department",
              "label": "使用部门",
              "span": 1,
              "type": "object",
              "display_field": "name"
            },
            {
              "field": "user",
              "label": "使用人",
              "span": 1,
              "type": "object",
              "display_field": "username"
            }
          ]
        }
      ]
    },
    {
      "id": "tab_depreciation",
      "title": "折旧信息",
      "icon": "TrendCharts",
      "sections": [
        {
          "id": "section_depreciation",
          "type": "descriptions",
          "columns": 2,
          "border": true,
          "fields": [
            {
              "field": "depreciation_method",
              "label": "折旧方法",
              "span": 1
            },
            {
              "field": "useful_life",
              "label": "使用年限（月）",
              "span": 1
            },
            {
              "field": "residual_rate",
              "label": "净残值率（%）",
              "span": 1
            },
            {
              "field": "start_depreciation_date",
              "label": "开始折旧日期",
              "span": 1,
              "formatter": "formatDate"
            },
            {
              "field": "current_value",
              "label": "当前净值",
              "span": 1,
              "formatter": "formatCurrency"
            },
            {
              "field": "accumulated_depreciation",
              "label": "累计折旧",
              "span": 1,
              "formatter": "formatCurrency"
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
            "display_fields": [
              {"field": "loaner", "label": "借用人"},
              {"field": "loan_date", "label": "借用日期"},
              {"field": "return_date", "label": "归还日期"},
              {"field": "status", "label": "状态", "type": "tag"}
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
        },
        {
          "id": "section_transfers",
          "title": "转移记录",
          "type": "related_list",
          "related_config": {
            "resource": "asset_transfers",
            "foreign_key": "asset",
            "display_fields": [
              {"field": "from_location", "label": "原位置"},
              {"field": "to_location", "label": "新位置"},
              {"field": "transfer_date", "label": "转移日期"},
              {"field": "status", "label": "状态", "type": "tag"}
            ],
            "limit": 5
          }
        }
      ]
    },
    {
      "id": "tab_audit",
      "title": "审计信息",
      "icon": "InfoFilled",
      "sections": [
        {
          "id": "section_audit",
          "type": "descriptions",
          "columns": 2,
          "border": true,
          "fields": [
            {
              "field": "id",
              "label": "资产ID",
              "span": 1
            },
            {
              "field": "organization",
              "label": "所属组织",
              "span": 1,
              "type": "object",
              "display_field": "name"
            },
            {
              "field": "created_at",
              "label": "创建时间",
              "span": 1,
              "formatter": "formatDateTime"
            },
            {
              "field": "created_by",
              "label": "创建人",
              "span": 1,
              "type": "object",
              "display_field": "username"
            },
            {
              "field": "updated_at",
              "label": "更新时间",
              "span": 1,
              "formatter": "formatDateTime"
            },
            {
              "field": "updated_by",
              "label": "更新人",
              "span": 1,
              "type": "object",
              "display_field": "username"
            }
          ]
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
    },
    {
      "key": "print",
      "label": "打印标签",
      "type": "default",
      "icon": "Printer",
      "handler": "handlePrint"
    },
    {
      "key": "qrcode",
      "label": "二维码",
      "type": "default",
      "icon": "QRCode",
      "handler": "handleQRCode"
    }
  ]
}
```

### 2.4 资产卡片布局 (Card Layout - 可选)

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
    "description_field": "specification",
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
        "type": "text",
        "display_field": "name"
      },
      {
        "field": "status",
        "label": "状态",
        "type": "tag",
        "tag_config": {
          "type_field": "status",
          "mapping": {
            "normal": "success",
            "maintenance": "warning"
          }
        }
      },
      {
        "field": "location",
        "label": "位置",
        "type": "text",
        "display_field": "name"
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

---

## 3. 采购申请 (ProcurementRequest) 默认布局定义

### 3.1 采购申请表单页布局

```json
{
  "layout_type": "form",
  "title": "采购申请",
  "layout_mode": "tabs",
  "tabs": [
    {
      "id": "tab_basic",
      "title": "基本信息",
      "icon": "Document",
      "sections": [
        {
          "id": "section_basic",
          "title": "申请基本信息",
          "columns": 2,
          "fields": [
            {
              "field": "request_no",
              "span": 1,
              "readonly": true,
              "label": "申请编号"
            },
            {
              "field": "request_type",
              "span": 1,
              "required": true,
              "label": "申请类型"
            },
            {
              "field": "title",
              "span": 2,
              "required": true,
              "placeholder": "请输入申请标题",
              "label": "申请标题"
            },
            {
              "field": "department",
              "span": 1,
              "required": true,
              "default_value": "@current_user_department",
              "label": "申请部门"
            },
            {
              "field": "requester",
              "span": 1,
              "required": true,
              "readonly": true,
              "default_value": "@current_user",
              "label": "申请人"
            },
            {
              "field": "request_date",
              "span": 1,
              "default_value": "@today",
              "label": "申请日期"
            },
            {
              "field": "expected_date",
              "span": 1,
              "placeholder": "请选择期望到货日期",
              "label": "期望到货日期"
            },
            {
              "field": "budget_amount",
              "span": 1,
              "placeholder": "请输入预算金额",
              "label": "预算金额"
            },
            {
              "field": "priority",
              "span": 1,
              "default_value": "normal",
              "label": "优先级"
            },
            {
              "field": "description",
              "span": 2,
              "placeholder": "请输入申请说明",
              "label": "申请说明"
            }
          ]
        }
      ]
    },
    {
      "id": "tab_items",
      "title": "采购明细",
      "icon": "List",
      "sections": [
        {
          "id": "section_items",
          "title": "采购物品清单",
          "type": "sub_table",
          "sub_object": "procurement_item",
          "foreign_key": "procurement_request",
          "columns": 2,
          "fields": [
            {
              "field": "items",
              "span": 2,
              "label": "采购明细",
              "sub_form_fields": [
                {
                  "field": "category",
                  "label": "分类",
                  "required": true,
                  "span": 6
                },
                {
                  "field": "name",
                  "label": "物品名称",
                  "required": true,
                  "span": 6
                },
                {
                  "field": "specification",
                  "label": "规格型号",
                  "span": 6
                },
                {
                  "field": "quantity",
                  "label": "数量",
                  "required": true,
                  "span": 3
                },
                {
                  "field": "unit",
                  "label": "单位",
                  "span": 3
                },
                {
                  "field": "unit_price",
                  "label": "单价",
                  "span": 3
                },
                {
                  "field": "amount",
                  "label": "金额",
                  "readonly": true,
                  "span": 3
                },
                {
                  "field": "expected_date",
                  "label": "期望到货日期",
                  "span": 6
                },
                {
                  "field": "remark",
                  "label": "备注",
                  "span": 12
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "id": "tab_approval",
      "title": "审批信息",
      "icon": "CircleCheck",
      "sections": [
        {
          "id": "section_approval",
          "title": "审批流程",
          "columns": 2,
          "fields": [
            {
              "field": "approval_status",
              "span": 1,
              "readonly": true,
              "label": "审批状态"
            },
            {
              "field": "current_approver",
              "span": 1,
              "readonly": true,
              "label": "当前审批人"
            },
            {
              "field": "approval_flow",
              "span": 2,
              "readonly": true,
              "label": "审批流程"
            }
          ]
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "submit",
      "label": "提交申请",
      "type": "primary",
      "handler": "handleSubmit"
    },
    {
      "key": "save_draft",
      "label": "保存草稿",
      "type": "default",
      "handler": "handleSaveDraft"
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

### 3.2 采购申请列表页布局

```json
{
  "layout_type": "list",
  "title": "采购申请列表",
  "icon": "ShoppingCart",
  "toolbar": {
    "actions": [
      {
        "key": "create",
        "label": "新建申请",
        "type": "primary",
        "icon": "Plus",
        "permission": "procurement.add_request",
        "handler": "handleCreate"
      },
      {
        "key": "batch_approve",
        "label": "批量审批",
        "type": "success",
        "icon": "Select",
        "permission": "procurement.approve_request",
        "handler": "handleBatchApprove"
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
    "refresh": true
  },
  "search_form": {
    "enabled": true,
    "inline": true,
    "fields": [
      {"field": "keyword", "label": "关键词", "widget": "input", "placeholder": "申请编号/标题"},
      {"field": "request_type", "label": "申请类型", "widget": "select"},
      {"field": "approval_status", "label": "审批状态", "widget": "select"},
      {"field": "department", "label": "申请部门", "widget": "select"},
      {"field": "request_date_range", "label": "申请日期", "widget": "daterange"}
    ]
  },
  "columns": [
    {"type": "selection", "width": 55, "fixed": "left"},
    {
      "prop": "request_no",
      "label": "申请编号",
      "width": 150,
      "fixed": "left",
      "sortable": true
    },
    {
      "prop": "title",
      "label": "申请标题",
      "minWidth": 200,
      "type": "link"
    },
    {
      "prop": "request_type",
      "label": "申请类型",
      "width": 120
    },
    {
      "prop": "department",
      "label": "申请部门",
      "width": 150,
      "field": "department.name"
    },
    {
      "prop": "requester",
      "label": "申请人",
      "width": 120,
      "field": "requester.username"
    },
    {
      "prop": "budget_amount",
      "label": "预算金额",
      "width": 120,
      "align": "right",
      "formatter": "formatCurrency"
    },
    {
      "prop": "approval_status",
      "label": "审批状态",
      "width": 100,
      "type": "tag",
      "tag_config": {
        "type_field": "approval_status",
        "mapping": {
          "draft": "info",
          "pending": "warning",
          "approved": "success",
          "rejected": "danger"
        }
      }
    },
    {
      "prop": "priority",
      "label": "优先级",
      "width": 100,
      "type": "tag",
      "tag_config": {
        "type_field": "priority",
        "mapping": {
          "urgent": "danger",
          "high": "warning",
          "normal": "primary",
          "low": "info"
        }
      }
    },
    {
      "prop": "request_date",
      "label": "申请日期",
      "width": 120,
      "sortable": true
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 250,
      "fixed": "right",
      "type": "action",
      "actions": [
        {"key": "view", "label": "查看", "type": "text"},
        {"key": "edit", "label": "编辑", "type": "text", "visible": "is_editable"},
        {"key": "approve", "label": "审批", "type": "text", "visible": "is_pending"},
        {"key": "delete", "label": "删除", "type": "text", "confirm": "确定要删除吗？"}
      ]
    }
  ],
  "pagination": {
    "enabled": true,
    "page_size": 20,
    "page_sizes": [10, 20, 50, 100]
  }
}
```

### 3.3 采购申请详情页布局

```json
{
  "layout_type": "detail",
  "title": "采购申请详情",
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
          "border": true,
          "fields": [
            {"field": "request_no", "label": "申请编号", "span": 1},
            {"field": "title", "label": "申请标题", "span": 1},
            {"field": "request_type", "label": "申请类型", "span": 1},
            {"field": "approval_status", "label": "审批状态", "span": 1, "type": "tag"},
            {"field": "department", "label": "申请部门", "span": 1},
            {"field": "requester", "label": "申请人", "span": 1},
            {"field": "request_date", "label": "申请日期", "span": 1},
            {"field": "expected_date", "label": "期望到货日期", "span": 1},
            {"field": "budget_amount", "label": "预算金额", "span": 1, "formatter": "formatCurrency"},
            {"field": "priority", "label": "优先级", "span": 1},
            {"field": "description", "label": "申请说明", "span": 2}
          ]
        }
      ]
    },
    {
      "id": "tab_items",
      "title": "采购明细",
      "icon": "List",
      "sections": [
        {
          "id": "section_items",
          "type": "sub_table_detail",
          "title": "采购物品清单",
          "sub_object": "procurement_item",
          "columns": [
            {"prop": "category", "label": "分类", "width": 120},
            {"prop": "name", "label": "物品名称", "minWidth": 150},
            {"prop": "specification", "label": "规格型号", "width": 150},
            {"prop": "quantity", "label": "数量", "width": 80, "align": "right"},
            {"prop": "unit", "label": "单位", "width": 80},
            {"prop": "unit_price", "label": "单价", "width": 100, "align": "right"},
            {"prop": "amount", "label": "金额", "width": 100, "align": "right"},
            {"prop": "expected_date", "label": "期望到货日期", "width": 120}
          ]
        }
      ]
    },
    {
      "id": "tab_approval",
      "title": "审批流程",
      "icon": "CircleCheck",
      "sections": [
        {
          "id": "section_approval_timeline",
          "type": "timeline",
          "title": "审批记录",
          "timeline_config": {
            "field": "approval_logs",
            "timestamp_field": "created_at",
            "content_field": "comment",
            "color_field": "action",
            "icon_field": "action"
          }
        }
      ]
    },
    {
      "id": "tab_audit",
      "title": "审计信息",
      "icon": "InfoFilled",
      "sections": [
        {
          "id": "section_audit",
          "type": "descriptions",
          "columns": 2,
          "fields": [
            {"field": "id", "label": "申请ID", "span": 1},
            {"field": "organization", "label": "所属组织", "span": 1},
            {"field": "created_at", "label": "创建时间", "span": 1},
            {"field": "created_by", "label": "创建人", "span": 1},
            {"field": "updated_at", "label": "更新时间", "span": 1},
            {"field": "updated_by", "label": "更新人", "span": 1}
          ]
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "edit",
      "label": "编辑",
      "type": "primary",
      "visible": "is_editable",
      "handler": "handleEdit"
    },
    {
      "key": "approve",
      "label": "审批",
      "type": "success",
      "visible": "is_pending",
      "handler": "handleApprove"
    },
    {
      "key": "reject",
      "label": "驳回",
      "type": "danger",
      "visible": "is_pending",
      "confirm": "确定要驳回该申请吗？",
      "handler": "handleReject"
    },
    {
      "key": "delete",
      "label": "删除",
      "type": "danger",
      "visible": "is_deletable",
      "confirm": "确定要删除该申请吗？",
      "handler": "handleDelete"
    }
  ]
}
```

---

## 4. 盘点任务 (InventoryTask) 默认布局定义

### 4.1 盘点任务表单页布局

```json
{
  "layout_type": "form",
  "title": "盘点任务",
  "layout_mode": "sections",
  "sections": [
    {
      "id": "section_basic",
      "title": "基本信息",
      "columns": 2,
      "fields": [
        {
          "field": "task_no",
          "span": 1,
          "readonly": true,
          "placeholder": "自动生成",
          "label": "任务编号"
        },
        {
          "field": "task_name",
          "span": 1,
          "required": true,
          "placeholder": "请输入任务名称",
          "label": "任务名称"
        },
        {
          "field": "task_type",
          "span": 1,
          "required": true,
          "default_value": "full",
          "label": "盘点类型"
        },
        {
          "field": "planned_date",
          "span": 1,
          "required": true,
          "placeholder": "请选择计划日期",
          "label": "计划日期"
        },
        {
          "field": "department",
          "span": 1,
          "placeholder": "请选择盘点部门",
          "label": "盘点部门"
        },
        {
          "field": "location",
          "span": 1,
          "placeholder": "请选择盘点位置",
          "label": "盘点位置"
        },
        {
          "field": "responsible_person",
          "span": 1,
          "required": true,
          "placeholder": "请选择责任人",
          "label": "责任人"
        },
        {
          "field": "status",
          "span": 1,
          "readonly": true,
          "default_value": "draft",
          "label": "状态"
        }
      ]
    },
    {
      "id": "section_range",
      "title": "盘点范围",
      "collapsible": true,
      "columns": 2,
      "fields": [
        {
          "field": "category_filter",
          "span": 2,
          "placeholder": "请选择资产分类",
          "label": "资产分类"
        },
        {
          "field": "location_filter",
          "span": 2,
          "placeholder": "请选择位置范围",
          "label": "位置范围"
        },
        {
          "field": "value_range_min",
          "span": 1,
          "placeholder": "最小价值",
          "label": "价值范围（元）"
        },
        {
          "field": "value_range_max",
          "span": 1,
          "placeholder": "最大价值",
          "label": "至"
        }
      ]
    },
    {
      "id": "section_settings",
      "title": "盘点设置",
      "collapsible": true,
      "collapsed": true,
      "columns": 2,
      "fields": [
        {
          "field": "allow_photo",
          "span": 1,
          "default_value": true,
          "label": "允许拍照"
        },
        {
          "field": "require_location",
          "span": 1,
          "default_value": true,
          "label": "验证位置"
        },
        {
          "field": "allow_batch_scan",
          "span": 1,
          "default_value": true,
          "label": "允许批量扫码"
        },
        {
          "field": "auto_difference_check",
          "span": 1,
          "default_value": true,
          "label": "自动差异检测"
        },
        {
          "field": "description",
          "span": 2,
          "placeholder": "请输入盘点说明",
          "label": "盘点说明"
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "create_snapshot",
      "label": "生成快照",
      "type": "primary",
      "handler": "handleCreateSnapshot"
    },
    {
      "key": "save",
      "label": "保存",
      "type": "default",
      "handler": "handleSave"
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

### 4.2 盘点任务列表页布局

```json
{
  "layout_type": "list",
  "title": "盘点任务列表",
  "icon": "Clipboard",
  "toolbar": {
    "actions": [
      {
        "key": "create",
        "label": "新建任务",
        "type": "primary",
        "icon": "Plus",
        "handler": "handleCreate"
      },
      {
        "key": "batch_start",
        "label": "批量开始",
        "type": "success",
        "handler": "handleBatchStart"
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
    "refresh": true
  },
  "search_form": {
    "enabled": true,
    "inline": true,
    "fields": [
      {"field": "keyword", "label": "关键词", "widget": "input", "placeholder": "任务编号/名称"},
      {"field": "task_type", "label": "盘点类型", "widget": "select"},
      {"field": "status", "label": "状态", "widget": "select"},
      {"field": "department", "label": "部门", "widget": "select"},
      {"field": "planned_date_range", "label": "计划日期", "widget": "daterange"}
    ]
  },
  "columns": [
    {"type": "selection", "width": 55, "fixed": "left"},
    {
      "prop": "task_no",
      "label": "任务编号",
      "width": 150,
      "fixed": "left",
      "sortable": true
    },
    {
      "prop": "task_name",
      "label": "任务名称",
      "minWidth": 200,
      "type": "link"
    },
    {
      "prop": "task_type",
      "label": "盘点类型",
      "width": 120
    },
    {
      "prop": "department",
      "label": "盘点部门",
      "width": 150,
      "field": "department.name"
    },
    {
      "prop": "location",
      "label": "盘点位置",
      "width": 150,
      "field": "location.name"
    },
    {
      "prop": "responsible_person",
      "label": "责任人",
      "width": 120,
      "field": "responsible_person.username"
    },
    {
      "prop": "planned_date",
      "label": "计划日期",
      "width": 120,
      "sortable": true
    },
    {
      "prop": "status",
      "label": "状态",
      "width": 100,
      "type": "tag",
      "tag_config": {
        "type_field": "status",
        "mapping": {
          "draft": "info",
          "pending": "warning",
          "in_progress": "primary",
          "completed": "success",
          "cancelled": "danger"
        }
      }
    },
    {
      "prop": "progress",
      "label": "进度",
      "width": 100,
      "type": "progress"
    },
    {
      "prop": "total_assets",
      "label": "资产总数",
      "width": 100,
      "align": "right"
    },
    {
      "prop": "scanned_count",
      "label": "已盘点",
      "width": 100,
      "align": "right"
    },
    {
      "prop": "difference_count",
      "label": "差异数",
      "width": 100,
      "align": "right"
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 300,
      "fixed": "right",
      "type": "action",
      "actions": [
        {"key": "view", "label": "查看", "type": "text"},
        {"key": "scan", "label": "扫码盘点", "type": "text", "visible": "is_scannable"},
        {"key": "difference", "label": "差异处理", "type": "text", "visible": "has_difference"},
        {"key": "complete", "label": "完成", "type": "text", "visible": "can_complete"},
        {"key": "delete", "label": "删除", "type": "text", "confirm": "确定要删除吗？"}
      ]
    }
  ],
  "pagination": {
    "enabled": true,
    "page_size": 20
  }
}
```

---

## 5. 资产借用 (AssetLoan) 默认布局定义

### 5.1 资产借用表单页布局

```json
{
  "layout_type": "form",
  "title": "资产借用",
  "layout_mode": "sections",
  "sections": [
    {
      "id": "section_basic",
      "title": "借用信息",
      "columns": 2,
      "fields": [
        {
          "field": "loan_no",
          "span": 1,
          "readonly": true,
          "label": "借用单号"
        },
        {
          "field": "loan_type",
          "span": 1,
          "required": true,
          "default_value": "borrow",
          "label": "借用类型"
        },
        {
          "field": "asset",
          "span": 2,
          "required": true,
          "placeholder": "请选择资产",
          "label": "借用资产"
        },
        {
          "field": "loaner",
          "span": 1,
          "required": true,
          "default_value": "@current_user",
          "label": "借用人"
        },
        {
          "field": "loan_date",
          "span": 1,
          "required": true,
          "default_value": "@today",
          "label": "借用日期"
        },
        {
          "field": "expected_return_date",
          "span": 1,
          "required": true,
          "placeholder": "请选择预计归还日期",
          "label": "预计归还日期"
        },
        {
          "field": "department",
          "span": 1,
          "placeholder": "请选择部门",
          "label": "使用部门"
        },
        {
          "field": "purpose",
          "span": 2,
          "placeholder": "请输入借用用途",
          "label": "借用用途"
        },
        {
          "field": "status",
          "span": 1,
          "readonly": true,
          "default_value": "pending",
          "label": "状态"
        }
      ]
    },
    {
      "id": "section_approval",
      "title": "审批信息",
      "collapsible": true,
      "columns": 2,
      "fields": [
        {
          "field": "approver",
          "span": 1,
          "placeholder": "请选择审批人",
          "label": "审批人"
        },
        {
          "field": "approval_status",
          "span": 1,
          "readonly": true,
          "label": "审批状态"
        },
        {
          "field": "approval_comment",
          "span": 2,
          "placeholder": "请输入审批意见",
          "label": "审批意见"
        }
      ]
    }
  ],
  "actions": [
    {
      "key": "submit",
      "label": "提交申请",
      "type": "primary",
      "handler": "handleSubmit"
    },
    {
      "key": "save",
      "label": "保存",
      "type": "default",
      "handler": "handleSave"
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

### 5.2 资产借用列表页布局

```json
{
  "layout_type": "list",
  "title": "借用记录列表",
  "icon": "Notebook",
  "toolbar": {
    "actions": [
      {
        "key": "create",
        "label": "新建借用",
        "type": "primary",
        "icon": "Plus",
        "handler": "handleCreate"
      },
      {
        "key": "batch_return",
        "label": "批量归还",
        "type": "success",
        "handler": "handleBatchReturn"
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
    "refresh": true
  },
  "search_form": {
    "enabled": true,
    "inline": true,
    "fields": [
      {"field": "keyword", "label": "关键词", "widget": "input", "placeholder": "借用单号/资产名称"},
      {"field": "loan_type", "label": "借用类型", "widget": "select"},
      {"field": "status", "label": "状态", "widget": "select"},
      {"field": "loaner", "label": "借用人", "widget": "select"},
      {"field": "loan_date_range", "label": "借用日期", "widget": "daterange"}
    ]
  },
  "columns": [
    {"type": "selection", "width": 55, "fixed": "left"},
    {
      "prop": "loan_no",
      "label": "借用单号",
      "width": 150,
      "fixed": "left",
      "sortable": true
    },
    {
      "prop": "asset",
      "label": "借用资产",
      "width": 200,
      "field": "asset.name"
    },
    {
      "prop": "asset.code",
      "label": "资产编码",
      "width": 150
    },
    {
      "prop": "loan_type",
      "label": "借用类型",
      "width": 100
    },
    {
      "prop": "loaner",
      "label": "借用人",
      "width": 120,
      "field": "loaner.username"
    },
    {
      "prop": "department",
      "label": "使用部门",
      "width": 150,
      "field": "department.name"
    },
    {
      "prop": "loan_date",
      "label": "借用日期",
      "width": 120,
      "sortable": true
    },
    {
      "prop": "expected_return_date",
      "label": "预计归还",
      "width": 120
    },
    {
      "prop": "return_date",
      "label": "实际归还",
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
          "pending": "warning",
          "approved": "primary",
          "borrowed": "success",
          "overdue": "danger",
          "returned": "info"
        }
      }
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 250,
      "fixed": "right",
      "type": "action",
      "actions": [
        {"key": "view", "label": "查看", "type": "text"},
        {"key": "approve", "label": "审批", "type": "text", "visible": "is_pending"},
        {"key": "return", "label": "归还", "type": "text", "visible": "can_return"},
        {"key": "renew", "label": "续借", "type": "text", "visible": "can_renew"},
        {"key": "delete", "label": "删除", "type": "text", "confirm": "确定要删除吗？"}
      ]
    }
  ],
  "pagination": {
    "enabled": true,
    "page_size": 20
  }
}
```

---

## 6. 用户 (User) 默认布局定义

### 6.1 用户表单页布局

```json
{
  "layout_type": "form",
  "title": "用户信息",
  "layout_mode": "sections",
  "sections": [
    {
      "id": "section_basic",
      "title": "基本信息",
      "columns": 2,
      "fields": [
        {
          "field": "username",
          "span": 1,
          "required": true,
          "placeholder": "请输入用户名",
          "label": "用户名"
        },
        {
          "field": "email",
          "span": 1,
          "required": true,
          "placeholder": "请输入邮箱",
          "label": "邮箱"
        },
        {
          "field": "full_name",
          "span": 1,
          "placeholder": "请输入姓名",
          "label": "姓名"
        },
        {
          "field": "phone",
          "span": 1,
          "placeholder": "请输入手机号",
          "label": "手机号"
        },
        {
          "field": "employee_no",
          "span": 1,
          "placeholder": "请输入工号",
          "label": "工号"
        },
        {
          "field": "gender",
          "span": 1,
          "label": "性别"
        }
      ]
    },
    {
      "id": "section_org",
      "title": "组织信息",
      "collapsible": true,
      "columns": 2,
      "fields": [
        {
          "field": "organization",
          "span": 1,
          "required": true,
          "placeholder": "请选择组织",
          "label": "所属组织"
        },
        {
          "field": "department",
          "span": 1,
          "placeholder": "请选择部门",
          "label": "所属部门"
        },
        {
          "field": "position",
          "span": 1,
          "placeholder": "请输入职位",
          "label": "职位"
        },
        {
          "field": "is_manager",
          "span": 1,
          "default_value": false,
          "label": "是否管理员"
        }
      ]
    },
    {
      "id": "section_security",
      "title": "安全设置",
      "collapsible": true,
      "collapsed": true,
      "columns": 2,
      "fields": [
        {
          "field": "password",
          "span": 1,
          "placeholder": "请输入密码",
          "label": "密码",
          "widget": "password"
        },
        {
          "field": "confirm_password",
          "span": 1,
          "placeholder": "请确认密码",
          "label": "确认密码",
          "widget": "password"
        },
        {
          "field": "is_active",
          "span": 1,
          "default_value": true,
          "label": "是否启用"
        },
        {
          "field": "role",
          "span": 1,
          "placeholder": "请选择角色",
          "label": "角色"
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

### 6.2 用户列表页布局

```json
{
  "layout_type": "list",
  "title": "用户列表",
  "icon": "User",
  "toolbar": {
    "actions": [
      {
        "key": "create",
        "label": "新增用户",
        "type": "primary",
        "icon": "Plus",
        "permission": "accounts.add_user",
        "handler": "handleCreate"
      },
      {
        "key": "batch_disable",
        "label": "批量禁用",
        "type": "warning",
        "handler": "handleBatchDisable"
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
    "refresh": true
  },
  "search_form": {
    "enabled": true,
    "inline": true,
    "fields": [
      {"field": "keyword", "label": "关键词", "widget": "input", "placeholder": "用户名/姓名/工号"},
      {"field": "department", "label": "部门", "widget": "select"},
      {"field": "role", "label": "角色", "widget": "select"},
      {"field": "is_active", "label": "状态", "widget": "select"}
    ]
  },
  "columns": [
    {"type": "selection", "width": 55, "fixed": "left"},
    {
      "prop": "username",
      "label": "用户名",
      "width": 120,
      "fixed": "left"
    },
    {
      "prop": "full_name",
      "label": "姓名",
      "width": 120
    },
    {
      "prop": "employee_no",
      "label": "工号",
      "width": 120
    },
    {
      "prop": "email",
      "label": "邮箱",
      "width": 180
    },
    {
      "prop": "phone",
      "label": "手机号",
      "width": 130
    },
    {
      "prop": "department",
      "label": "部门",
      "width": 150,
      "field": "department.name"
    },
    {
      "prop": "position",
      "label": "职位",
      "width": 120
    },
    {
      "prop": "role",
      "label": "角色",
      "width": 120
    },
    {
      "prop": "is_active",
      "label": "状态",
      "width": 80,
      "type": "switch"
    },
    {
      "prop": "last_login",
      "label": "最后登录",
      "width": 160,
      "formatter": "formatDateTime"
    },
    {
      "prop": "actions",
      "label": "操作",
      "width": 250,
      "fixed": "right",
      "type": "action",
      "actions": [
        {"key": "view", "label": "查看", "type": "text"},
        {"key": "edit", "label": "编辑", "type": "text"},
        {"key": "reset_password", "label": "重置密码", "type": "text"},
        {"key": "disable", "label": "禁用", "type": "text", "visible": "is_active"},
        {"key": "enable", "label": "启用", "type": "text", "visible": "!is_active"},
        {"key": "delete", "label": "删除", "type": "text", "confirm": "确定要删除该用户吗？"}
      ]
    }
  ],
  "pagination": {
    "enabled": true,
    "page_size": 20
  }
}
```

---

## 7. 默认字段配置规范

### 7.1 系统字段的默认显示规则

| 字段名 | 字段类型 | 列表显示 | 表单显示 | 详情显示 | 只读规则 | 说明 |
|-------|---------|---------|---------|---------|---------|------|
| `id` | UUID | 隐藏 | 隐藏 | 显示 | 始终只读 | 主键ID |
| `organization` | ForeignKey | 显示 | 显示 | 显示 | 表单可编辑 | 组织隔离字段 |
| `is_deleted` | Boolean | 隐藏 | 隐藏 | 可选显示 | 始终只读 | 软删除标记 |
| `deleted_at` | DateTime | 隐藏 | 隐藏 | 可选显示 | 始终只读 | 删除时间 |
| `created_at` | DateTime | 可选显示 | 隐藏 | 显示 | 始终只读 | 创建时间 |
| `updated_at` | DateTime | 可选显示 | 隐藏 | 显示 | 始终只读 | 更新时间 |
| `created_by` | ForeignKey | 可选显示 | 隐藏 | 显示 | 始终只读 | 创建人 |
| `updated_by` | ForeignKey | 隐藏 | 隐藏 | 可选显示 | 始终只读 | 更新人 |
| `custom_fields` | JSONB | 隐藏 | 动态生成 | 动态生成 | - | 自定义字段 |

### 7.2 默认必填字段列表

#### 7.2.1 资产 (Asset) 必填字段

```python
REQUIRED_FIELDS = [
    'code',           # 资产编码
    'name',           # 资产名称
    'category',       # 资产分类
]
```

#### 7.2.2 采购申请 (ProcurementRequest) 必填字段

```python
REQUIRED_FIELDS = [
    'request_type',   # 申请类型
    'title',          # 申请标题
    'department',     # 申请部门
    'requester',      # 申请人
    # items (sub-object) 至少一条记录
]
```

#### 7.2.3 盘点任务 (InventoryTask) 必填字段

```python
REQUIRED_FIELDS = [
    'task_name',           # 任务名称
    'task_type',           # 盘点类型
    'planned_date',        # 计划日期
    'responsible_person',  # 责任人
]
```

#### 7.2.4 资产借用 (AssetLoan) 必填字段

```python
REQUIRED_FIELDS = [
    'asset',                # 借用资产
    'loaner',               # 借用人
    'loan_date',            # 借用日期
    'expected_return_date', # 预计归还日期
]
```

#### 7.2.5 用户 (User) 必填字段

```python
REQUIRED_FIELDS = [
    'username',       # 用户名
    'email',          # 邮箱
    'organization',   # 所属组织
]
```

### 7.3 默认只读字段列表

| 业务对象 | 只读字段 | 只读原因 |
|---------|---------|---------|
| **Asset** | `id`, `organization`, `status`, `created_at`, `updated_at`, `created_by` | 系统自动生成或控制 |
| **ProcurementRequest** | `request_no`, `approval_status`, `current_approver` | 审批流程控制 |
| **InventoryTask** | `task_no`, `status`, `progress` | 系统自动计算 |
| **AssetLoan** | `loan_no`, `approval_status`, `status` | 审批流程控制 |
| **User** | `id`, `organization`, `last_login` | 系统自动记录 |

---

## 8. 默认操作按钮配置

### 8.1 表单页默认操作按钮

```json
{
  "form_actions": [
    {
      "key": "submit",
      "label": "提交",
      "type": "primary",
      "icon": "Check",
      "loading_key": "submitting",
      "handler": "handleSubmit",
      "visible": true,
      "disabled": false
    },
    {
      "key": "save_draft",
      "label": "保存草稿",
      "type": "default",
      "icon": "Document",
      "handler": "handleSaveDraft",
      "visible": "has_draft_feature",
      "disabled": false
    },
    {
      "key": "reset",
      "label": "重置",
      "type": "default",
      "icon": "RefreshLeft",
      "handler": "handleReset",
      "visible": true,
      "disabled": false
    },
    {
      "key": "cancel",
      "label": "取消",
      "type": "default",
      "icon": "Close",
      "handler": "handleCancel",
      "visible": true,
      "disabled": false
    }
  ]
}
```

### 8.2 列表页默认操作按钮

#### 8.2.1 工具栏按钮

```json
{
  "toolbar_actions": [
    {
      "key": "create",
      "label": "新建",
      "type": "primary",
      "icon": "Plus",
      "permission": "{app}.add_{model}",
      "handler": "handleCreate"
    },
    {
      "key": "batch_delete",
      "label": "批量删除",
      "type": "danger",
      "icon": "Delete",
      "permission": "{app}.delete_{model}",
      "confirm": "确定要删除选中的记录吗？",
      "handler": "handleBatchDelete",
      "disabled_when": "selection_count == 0"
    },
    {
      "key": "export",
      "label": "导出",
      "type": "success",
      "icon": "Download",
      "permission": "{app}.export_{model}",
      "handler": "handleExport"
    },
    {
      "key": "import",
      "label": "导入",
      "type": "warning",
      "icon": "Upload",
      "permission": "{app}.import_{model}",
      "handler": "handleImport",
      "visible": "has_import_feature"
    }
  ]
}
```

#### 8.2.2 行操作按钮

```json
{
  "row_actions": [
    {
      "key": "view",
      "label": "查看",
      "type": "text",
      "permission": "{app}.view_{model}",
      "handler": "handleView"
    },
    {
      "key": "edit",
      "label": "编辑",
      "type": "text",
      "permission": "{app}.change_{model}",
      "handler": "handleEdit",
      "visible": "is_editable"
    },
    {
      "key": "delete",
      "label": "删除",
      "type": "text",
      "permission": "{app}.delete_{model}",
      "confirm": "确定要删除该记录吗？",
      "handler": "handleDelete",
      "visible": "is_deletable"
    }
  ]
}
```

### 8.3 详情页默认操作按钮

```json
{
  "detail_actions": [
    {
      "key": "edit",
      "label": "编辑",
      "type": "primary",
      "icon": "Edit",
      "permission": "{app}.change_{model}",
      "handler": "handleEdit",
      "visible": "is_editable"
    },
    {
      "key": "delete",
      "label": "删除",
      "type": "danger",
      "icon": "Delete",
      "permission": "{app}.delete_{model}",
      "confirm": "确定要删除该记录吗？",
      "handler": "handleDelete",
      "visible": "is_deletable"
    },
    {
      "key": "print",
      "label": "打印",
      "type": "default",
      "icon": "Printer",
      "handler": "handlePrint",
      "visible": "has_print_feature"
    },
    {
      "key": "export",
      "label": "导出PDF",
      "type": "default",
      "icon": "Download",
      "handler": "handleExportPDF",
      "visible": "has_export_feature"
    }
  ]
}
```

### 8.4 批量操作默认配置

#### 8.4.1 批量删除配置

```json
{
  "batch_delete": {
    "enabled": true,
    "endpoint": "/api/{resource}/batch-delete/",
    "method": "POST",
    "confirm": {
      "title": "批量删除确认",
      "message": "确定要删除选中的 {count} 条记录吗？",
      "type": "warning"
    },
    "success_message": "成功删除 {succeeded} 条记录",
    "error_message": "删除完成，失败 {failed} 条",
    "response_format": {
      "success": true,
      "summary": {
        "total": "integer",
        "succeeded": "integer",
        "failed": "integer"
      },
      "results": [
        {
          "id": "string",
          "success": "boolean",
          "error": "string (optional)"
        }
      ]
    }
  }
}
```

#### 8.4.2 批量更新配置

```json
{
  "batch_update": {
    "enabled": true,
    "endpoint": "/api/{resource}/batch-update/",
    "method": "POST",
    "fields": ["status", "organization"],
    "success_message": "成功更新 {succeeded} 条记录",
    "error_message": "更新完成，失败 {failed} 条"
  }
}
```

#### 8.4.3 批量导出配置

```json
{
  "batch_export": {
    "enabled": true,
    "endpoint": "/api/{resource}/export/",
    "method": "POST",
    "formats": ["xlsx", "csv", "pdf"],
    "max_records": 10000,
    "async": true,
    "notification": true
  }
}
```

---

## 9. 实施指南

### 9.1 应用默认布局的步骤

#### 9.1.1 通过数据迁移创建默认布局

```python
# apps/system/migrations/0003_create_default_page_layouts.py

from django.db import migrations
import json

def create_default_asset_layouts(apps, schema_editor):
    """创建资产默认布局"""
    PageLayout = apps.get_model('system', 'PageLayout')
    BusinessObject = apps.get_model('system', 'BusinessObject')
    Organization = apps.get_model('organizations', 'Organization')

    # 获取业务对象
    asset_object = BusinessObject.objects.get(code='asset')
    org = Organization.objects.first()

    # 创建资产表单布局
    form_layout_config = {
        "layout_type": "form",
        "title": "资产信息",
        "layout_mode": "tabs",
        "tabs": [...]
    }

    PageLayout.objects.create(
        business_object=asset_object,
        layout_type='form',
        name='default_asset_form',
        description='资产默认表单布局',
        is_default=True,
        organization=org,
        layout_config=form_layout_config,
        is_published=True,
        version='1.0.0'
    )

    # 创建资产列表布局
    list_layout_config = {
        "layout_type": "list",
        "title": "资产列表",
        "toolbar": {...},
        "columns": [...]
    }

    PageLayout.objects.create(
        business_object=asset_object,
        layout_type='list',
        name='default_asset_list',
        description='资产默认列表布局',
        is_default=True,
        organization=org,
        layout_config=list_layout_config,
        is_published=True,
        version='1.0.0'
    )

class Migration(migrations.Migration):
    dependencies = [
        ('system', '0002_create_business_objects'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_asset_layouts),
    ]
```

#### 9.1.2 在前端使用默认布局

```javascript
// frontend/src/views/assets/AssetForm.vue

import { ref, onMounted } from 'vue'
import { getPageLayout } from '@/api/metadata'
import MetadataDrivenForm from '@/components/metadata/MetadataDrivenForm.vue'

export default {
  components: {
    MetadataDrivenForm
  },

  setup() {
    const layoutConfig = ref(null)
    const loading = ref(false)

    async function loadDefaultLayout() {
      loading.value = true
      try {
        const response = await getPageLayout('asset', 'form')
        if (response.success && response.data.results.length > 0) {
          // 使用默认布局
          layoutConfig.value = response.data.results[0].layout_config
        } else {
          // 使用硬编码的备用布局
          layoutConfig.value = getFallbackLayout()
        }
      } catch (error) {
        console.error('Failed to load layout:', error)
        layoutConfig.value = getFallbackLayout()
      } finally {
        loading.value = false
      }
    }

    function getFallbackLayout() {
      // 备用布局配置
      return {
        layout_type: "form",
        sections: [...]
      }
    }

    onMounted(() => {
      loadDefaultLayout()
    })

    return {
      layoutConfig,
      loading
    }
  }
}
```

### 9.2 自定义默认布局

#### 9.2.1 基于默认布局扩展

```python
# 创建自定义布局（继承默认布局）

from apps.system.models import PageLayout

# 获取默认布局
default_layout = PageLayout.objects.get(
    business_object__code='asset',
    layout_type='form',
    is_default=True
)

# 创建自定义布局（复制默认布局配置）
custom_layout = PageLayout.objects.create(
    business_object=default_layout.business_object,
    layout_type='form',
    name='custom_asset_form',
    description='自定义资产表单布局',
    organization_id=org_id,
    layout_config=default_layout.layout_config,  # 复制配置
    is_default=False,
    parent_layout=default_layout,  # 设置父布局
    version='1.0.0'
)

# 修改自定义布局配置
custom_config = custom_layout.layout_config.copy()
custom_config['sections'][0]['fields'].append({
    "field": "custom_field1",
    "span": 1,
    "label": "自定义字段"
})
custom_layout.layout_config = custom_config
custom_layout.save()
```

#### 9.2.2 覆盖默认布局

```python
# 为特定组织创建覆盖的默认布局

PageLayout.objects.create(
    business_object=asset_object,
    layout_type='form',
    name='org_custom_asset_form',
    description='组织自定义资产表单布局',
    is_default=True,  # 设为该组织的默认布局
    organization_id=org_id,
    layout_config=custom_config,
    is_published=True,
    version='1.0.0'
)
```

### 9.3 版本管理策略

#### 9.3.1 布局版本升级

```python
def upgrade_asset_layout():
    """升级资产布局到新版本"""

    # 获取当前默认布局
    current_layout = PageLayout.objects.get(
        business_object__code='asset',
        layout_type='form',
        is_default=True
    )

    # 创建新版本
    new_version = '2.0.0'
    new_layout = current_layout.create_version(new_version)

    # 修改新版本配置
    new_config = new_layout.layout_config.copy()

    # 添加新的标签页
    new_config['tabs'].append({
        "id": "tab_maintenance",
        "title": "维护记录",
        "icon": "Tools",
        "sections": [...]
    })

    new_layout.layout_config = new_config
    new_layout.is_published = False  # 先不发布
    new_layout.save()

    return new_layout
```

#### 9.3.2 版本回滚

```python
def rollback_layout_version(layout_id, target_version):
    """回滚到指定版本"""

    # 获取目标版本
    target_layout = PageLayout.objects.get(
        id=layout_id,
        version=target_version
    )

    # 创建新版本（基于目标版本）
    rollback_layout = target_layout.create_version(
        f"{target_version}-rollback-{timezone.now().strftime('%Y%m%d')}"
    )

    # 发布回滚版本
    rollback_layout.publish(user=request.user)

    return rollback_layout
```

---

## 10. 最佳实践与注意事项

### 10.1 默认布局设计原则

1. **简单优先**：默认布局应简单直观，不要包含过多高级特性
2. **渐进增强**：基础功能在默认布局中，高级功能通过自定义实现
3. **业务对齐**：布局结构应与实际业务流程匹配
4. **性能考虑**：默认布局不应包含大量复杂计算或实时数据
5. **向后兼容**：升级默认布局时应保持向后兼容性

### 10.2 字段配置注意事项

1. **必填字段谨慎设置**：只在真正必需时设置字段为必填
2. **只读字段明确原因**：文档中说明字段只读的业务原因
3. **默认值合理设置**：提供合理的默认值，减少用户输入
4. **字段顺序符合逻辑**：按照填写顺序和业务逻辑排列字段
5. **字段分组清晰**：相关字段组织在同一区块或标签页

### 10.3 性能优化建议

1. **列表分页**：列表页默认启用分页，默认每页20条
2. **懒加载**：标签页内容按需加载，避免一次性加载所有数据
3. **缓存策略**：布局配置在客户端缓存，减少API请求
4. **按需显示**：详情页的关联数据按需加载，避免N+1查询
5. **虚拟滚动**：大列表使用虚拟滚动提升性能

### 10.4 用户体验建议

1. **一致的交互**：相同操作在不同页面保持一致的交互方式
2. **清晰的反馈**：操作后提供清晰的反馈信息
3. **合理的默认值**：智能推测用户意图，设置合理默认值
4. **快捷操作**：提供常用操作的快捷方式
5. **错误提示友好**：验证失败时提供明确的错误提示和解决建议

---

## 11. 总结

本文档定义了 GZEAMS 系统各业务对象的默认页面布局规范，包括：

### 11.1 核心内容

1. **默认布局原则**：设计理念、层级结构、字段排列顺序、区块分组规范
2. **各业务对象布局**：资产、采购申请、盘点任务、资产借用、用户的完整布局配置
3. **默认字段配置**：系统字段显示规则、必填字段、只读字段列表
4. **默认操作按钮**：表单、列表、详情页的标准操作按钮配置
5. **批量操作规范**：批量删除、更新、导出的标准配置

### 11.2 实施要点

1. **数据迁移**：通过数据迁移创建默认布局
2. **前端集成**：使用 MetadataDrivenForm/List 组件渲染默认布局
3. **自定义扩展**：基于默认布局创建组织特定的自定义布局
4. **版本管理**：布局升级和回滚的最佳实践
5. **性能优化**：列表分页、懒加载、缓存策略等

### 11.3 价值体现

通过统一的默认布局规范，GZEAMS 系统能够：

1. **提升开发效率**：新业务对象可直接应用默认布局，快速上线
2. **保证用户体验**：统一的界面风格和交互方式，降低学习成本
3. **简化维护工作**：集中管理默认布局，修改一处全局生效
4. **支持灵活扩展**：在默认布局基础上自定义，满足个性化需求
5. **降低培训成本**：标准化界面，新用户快速上手

---

## 附录：参考资料

### A. 相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| PageLayout配置规范 | `./page_layout_config.md` | PageLayout模型详细配置 |
| 元数据驱动前端 | `./metadata_frontend.md` | 前端元数据驱动组件 |
| 前端公共组件 | `./frontend.md` | BaseListPage/FormPage组件 |
| 元数据驱动核心 | `./metadata_driven.md` | 元数据引擎架构 |

### B. 技术栈

- **后端**: Django 5.0, DRF, PostgreSQL JSONB
- **前端**: Vue 3 (Composition API), Element Plus, Vite
- **低代码引擎**: BusinessObject, FieldDefinition, PageLayout

### C. 版本历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-01-15 | 初始版本，定义默认布局规范 | Claude |

---

**文档结束**
