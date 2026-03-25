# PRD: 主从聚合架构与统一单据运行时

## 1. 文档信息

- 版本: `v1.0`
- 日期: `2026-03-14`
- 作者: `System Architect`
- 状态: `Draft`
- 关联文档:
  - `docs/prd/prd-document-subtable-line-items-2026-03-11.md`
  - `docs/prd/prd-layout-designer-enhancement-2026-03-11.md`
  - `docs/prd/prd-lifecycle-cross-object-actions-closed-loop-2026-03-13.md`

## I18N Guardrails

This architecture treats internationalization as a platform-level requirement.

1. Do not hardcode new user-facing copy in Vue components, layout configs, protocol defaults, or generated metadata.
2. Master objects, detail objects, relations, sections, and detail regions must support:
   - `translation_key`
   - `name` / `title` for `zh-CN`
   - `name_en` / `title_en` for `en-US`
3. Runtime label resolution priority must be:
   - locale bundle via `translation_key`
   - bilingual metadata for the active locale
   - stable object code fallback
4. Layout designer output must store bilingual metadata for `field-section` and `detail-region`; it must not persist single-language literals as the only label source.
5. Protocol enum values such as `object_role`, `relation_type`, and `detail_edit_mode` are stable codes, not UI labels.

---

## 2. 背景与结论

当前项目已经具备较强的元数据平台基础，包括：

- `BusinessObject` 统一对象元数据
- `ObjectRelationDefinition` 统一对象关系
- `PageLayout` 统一布局配置
- `FieldDefinition.sub_table` 与前端 `SubTable` 渲染能力
- `WysiwygLayoutDesigner` 可视化布局设计器

但“单据头 + 单据行”的抽象仍然停留在“普通对象 + 关系 + 菜单隐藏”的拼接模式，导致以下问题：

1. 单据行对象在领域上依附父单据，但在平台上又被视为一级对象。
2. 菜单、对象工作台、详情页、权限、审批、状态流转都没有统一遵守主从边界。
3. 新建、编辑、只读三种页面对主表和子表的处理逻辑分散，后续每个业务单据都需要重复实现。
4. 布局设计器当前主要面向“字段布局”，还没有正式支持“主表区 + 子表区”的统一设计。

本 PRD 的结论是：

- 项目应正式引入 `Master-Detail` 主从聚合架构。
- 主对象为聚合根，从对象为聚合内子实体。
- 从对象默认继承父对象的生命周期、权限、审批、状态和导航策略。
- 新建、编辑、只读统一收口为一套“聚合页面运行时模型”。
- 布局设计器升级为同时支持主表区块与子表区块。

---

## 3. 目标与非目标

### 3.1 目标

1. 定义统一的主从聚合元数据协议，覆盖对象角色、继承策略、关系语义与导航规则。
2. 为 `AssetPickup/PickupItem`、`AssetTransfer/TransferItem`、`AssetReturn/ReturnItem`、`AssetLoan/LoanItem` 建立正式的主从聚合模型。
3. 建立统一的单据运行时页面模型，支持主表与子表在新建、编辑、只读三种模式下的公共处理。
4. 建立统一的子表运行时协议，支持行新增、行编辑、行删除、只读展示、汇总、导入导出与校验。
5. 升级布局设计器，使其能够设计“字段区块”和“子表区块”。
6. 为后续采购、验收、维修、报废、保险、租赁等单据提供统一复用的架构底座。

### 3.2 非目标

1. 本期不重写全部动态页面，只为单据型对象补齐聚合能力。
2. 本期不重构全部对象类型，仅重点引入 `master_detail` 协议与聚合运行时。
3. 本期不构建新的规则引擎，子表行为优先复用现有元数据、权限、工作流、状态日志机制。
4. 本期不一次性迁移所有业务模块，先以资产操作单据为首批样板。

---

## 4. 关键问题

### 4.1 当前抽象问题

| 问题 | 现状 | 长期影响 |
|------|------|----------|
| 对象角色混淆 | 单据行与主对象均作为一级 `BusinessObject` 处理 | 菜单、权限、流程、页面模型持续泄漏 |
| 主从页面模型缺失 | 主表与子表在 create/edit/readonly 逻辑分散 | 每个单据重复开发 |
| 继承规则缺失 | 从对象是否继承父对象流程、权限、状态无统一协议 | 容易形成特例和行为不一致 |
| 设计器抽象不足 | 设计器主要关注字段，不关注聚合区块 | 后续布局定制无法平台化 |
| 写入边界不清晰 | 子表既可能通过父对象保存，也可能被独立暴露 | 聚合一致性和事务边界不稳 |

### 4.2 典型错误现象

1. 领用单明细出现独立页面和菜单。
2. 子表对象被误当作一级业务对象进行导航。
3. 主表详情页与子表展示页之间信息断裂。
4. 父单据审批态与子表是否可编辑缺少统一约束。

---

## 5. 核心设计原则

1. 聚合根优先：单据型业务以主对象作为唯一业务入口。
2. 默认继承：从对象默认继承父对象生命周期、权限、审批、状态。
3. 少量覆盖：允许从对象在查询、展示、导出等能力上做显式覆盖。
4. 运行时统一：create/edit/readonly 共用一套页面模型与数据协议。
5. 设计即运行：布局设计器的区块模型应与运行时区块模型一致。
6. 平台优先：优先形成平台协议，不做只适配一个单据的局部修补。

---

## 6. 术语定义

### 6.1 对象角色

- `root`: 聚合根对象，可独立菜单、流程、权限、状态机、动作。
- `detail`: 聚合内从对象，默认依附某个 `root`。
- `reference`: 主数据或引用对象，如资产、供应商、部门。
- `log`: 日志、快照、审计对象，通常不作为业务入口。

### 6.2 关系类型

- `master_detail`: 主从聚合关系，从对象完全依附父对象。
- `lookup`: 普通引用关系，可独立存在。
- `derived_query`: 派生关联，只用于查询或展示。

### 6.3 页面上下文

- `create`: 新建主单及子表。
- `edit`: 编辑主单及子表。
- `readonly`: 查看主单及子表，不允许业务编辑。

---

## 7. 目标方案

## 7.1 元数据模型增强

在现有 `BusinessObject` 与 `ObjectRelationDefinition` 之上，新增正式主从协议字段。

### 7.1.1 BusinessObject 扩展建议

| 字段 | 类型 | 含义 |
|------|------|------|
| `object_role` | string | `root/detail/reference/log` |
| `is_top_level_navigable` | boolean | 是否允许作为一级导航对象 |
| `allow_standalone_query` | boolean | 是否允许独立只读查询 |
| `allow_standalone_route` | boolean | 是否允许独立对象页路由 |
| `inherit_permissions` | boolean | 是否继承父对象权限 |
| `inherit_workflow` | boolean | 是否继承父对象工作流 |
| `inherit_status` | boolean | 是否继承父对象状态上下文 |
| `inherit_lifecycle` | boolean | 是否继承父对象生命周期约束 |

### 7.1.2 ObjectRelationDefinition 扩展建议

| 字段 | 类型 | 含义 |
|------|------|------|
| `relation_type` | string | `master_detail/lookup/derived_query` |
| `detail_edit_mode` | string | `inline_table/nested_form/readonly_table` |
| `cascade_soft_delete` | boolean | 父对象软删除时是否级联 |
| `detail_toolbar_config` | json | 子表工具栏配置 |
| `detail_summary_rules` | json | 汇总规则 |
| `detail_validation_rules` | json | 子表级校验规则 |

### 7.1.3 默认继承策略

当 `relation_type=master_detail` 且目标对象 `object_role=detail` 时，平台默认行为如下：

1. 不生成一级菜单。
2. 不进入普通对象工作台。
3. 写操作默认只能通过父对象提交。
4. 权限校验默认沿用父对象。
5. 工作流动作只挂在父对象。
6. 子表编辑能力默认取决于父对象状态与页面上下文。
7. 时间线与审计默认归集到父对象主时间线。

---

## 7.2 统一单据运行时模型

引入统一运行时页面容器：`DocumentWorkbench`。

### 7.2.1 页面结构

```text
DocumentWorkbench
├── DocumentHeader
├── MasterSections
├── DetailRegions
├── WorkflowPanel
├── TimelinePanel
└── AuditPanel
```

### 7.2.2 三种页面模式

| 模式 | 主表 | 子表 | 动作 |
|------|------|------|------|
| `create` | 可编辑 | 可新增/编辑/删除 | 保存、提交草稿 |
| `edit` | 按状态和权限可编辑 | 按父对象状态决定是否可编辑 | 保存、提交、撤回、作废 |
| `readonly` | 只读 | 只读 | 查看流程、时间线、导出 |

### 7.2.3 统一提交协议

```json
{
  "master": {
    "department_id": "uuid",
    "pickup_date": "2026-03-14",
    "pickup_reason": "办公领用"
  },
  "details": {
    "pickup_items": {
      "rows": [
        {
          "_row_state": "new",
          "asset_id": "uuid-1",
          "quantity": 1,
          "remark": ""
        },
        {
          "id": "row-uuid-2",
          "_row_state": "updated",
          "quantity": 2
        },
        {
          "id": "row-uuid-3",
          "_row_state": "deleted"
        }
      ]
    }
  }
}
```

### 7.2.4 统一返回协议

```json
{
  "context": {
    "page_mode": "edit",
    "object_code": "AssetPickup",
    "record_id": "uuid"
  },
  "master": {
    "id": "uuid",
    "pickup_no": "LY202603001",
    "status": "draft"
  },
  "details": {
    "pickup_items": {
      "editable": true,
      "row_count": 2,
      "rows": []
    }
  },
  "capabilities": {
    "can_edit_master": true,
    "can_edit_details": true,
    "can_submit": true
  }
}
```

---

## 7.3 统一子表运行时模型

引入统一子表区块协议：`DetailRegion`。

### 7.3.1 DetailRegion 元数据

| 字段 | 类型 | 含义 |
|------|------|------|
| `relation_code` | string | 关系编码 |
| `title` | string | 区块标题 |
| `title_en` | string | 英文区块标题 |
| `translation_key` | string | 统一翻译键 |
| `renderer` | string | `inline_table/nested_form/readonly_table` |
| `columns` | array | 展示列配置 |
| `row_actions` | array | 行级动作 |
| `toolbar_actions` | array | 区块工具栏动作 |
| `allow_import` | boolean | 是否允许导入 |
| `allow_export` | boolean | 是否允许导出 |
| `summary_rules` | array | 汇总规则 |
| `editable_when` | json | 依赖父对象状态的编辑条件 |

### 7.3.2 行状态协议

- `_row_state=new`
- `_row_state=updated`
- `_row_state=deleted`
- `_row_state=unchanged`

### 7.3.3 统一行为

1. 行新增：默认追加到底部。
2. 行编辑：默认行内编辑。
3. 行删除：默认逻辑删除标记，提交时统一处理。
4. 行校验：提交前统一执行子表字段校验与业务校验。
5. 行汇总：由 `summary_rules` 决定页脚展示。

---

## 7.4 布局设计器扩展模型

### 7.4.1 新增区块类型

在 `PageLayout.layout_config` 中新增两类一等公民区块：

- `field-section`
- `detail-region`

示例：

```json
{
  "mode": "edit",
  "sections": [
    {
      "id": "basic_info",
      "type": "field-section",
      "title": "基本信息",
      "title_en": "Basic Information",
      "translation_key": "layout.sections.asset_pickup.basic_info",
      "fields": ["pickup_date", "department", "pickup_reason"]
    },
    {
      "id": "pickup_items",
      "type": "detail-region",
      "title": "领用明细",
      "title_en": "Pickup Items",
      "translation_key": "layout.sections.asset_pickup.pickup_items",
      "relation_code": "pickup_items",
      "renderer": "inline_table",
      "toolbar_actions": ["add_row", "import", "batch_delete"],
      "columns": [
        { "field": "asset", "width": 260 },
        { "field": "quantity", "width": 120 },
        { "field": "remark", "width": 240 }
      ]
    }
  ]
}
```

### 7.4.2 设计器交互要求

1. 左侧面板区分“主表字段”和“子表关系”。
2. 关系可拖入画布，生成 `detail-region`。
3. 右侧属性面板支持编辑：
   - 关联关系
   - 展示列
   - 行编辑模式
   - 工具栏动作
   - 汇总规则
   - 只读策略
4. 预览模式支持 `create/edit/readonly` 切换。
5. 设计器渲染结果与运行时区块渲染协议一致。

---

## 8. 产品需求

## 8.1 FR-1 主从聚合对象协议

### 描述

系统应能将业务对象正式区分为 `root/detail/reference/log` 四类，并支持 `master_detail` 关系的默认继承行为。

### 验收标准

1. `PickupItem/TransferItem/ReturnItem/LoanItem` 可被标记为 `detail`。
2. `AssetPickup/AssetTransfer/AssetReturn/AssetLoan` 可被标记为 `root`。
3. `detail` 对象默认不可作为一级导航对象。
4. `master_detail` 关系可定义父对象与从对象的写入边界与展示模式。

## 8.2 FR-2 统一聚合页面

### 描述

系统应提供一套同时支持主表与子表的统一单据页面运行时，覆盖新建、编辑、只读三种模式。

### 验收标准

1. 新建页可同时录入主表和子表。
2. 编辑页可按父对象状态决定主表和子表可编辑性。
3. 只读页可统一展示主表、子表、流程、时间线和审计。
4. 同一单据类型不再需要单独维护“主表页”和“明细对象页”两套业务入口。

## 8.3 FR-3 统一子表区块

### 描述

系统应提供统一的子表区块渲染与交互协议，用于单据行录入、展示、校验与汇总。

### 验收标准

1. 子表区块支持行新增、行编辑、行删除。
2. 子表区块支持只读模式。
3. 子表区块支持列配置、汇总、导入、导出。
4. 子表区块支持与父对象状态联动的只读策略。

## 8.4 FR-4 设计器支持主从布局

### 描述

布局设计器应支持设计“主表区”和“子表区”，并与运行时共享同一配置协议。

### 验收标准

1. 设计器中可将关系拖入画布生成 `detail-region`。
2. 设计器中可配置子表列、工具栏、只读策略、汇总规则。
3. 发布后的布局在运行时可直接生效。

## 8.5 FR-5 主从继承规则

### 描述

系统应在 `master_detail` 场景下自动继承父对象流程、权限、状态与生命周期约束。

### 验收标准

1. 从对象默认不独立发起工作流。
2. 从对象默认不独立授权。
3. 父对象处于不可编辑状态时，从对象自动只读。
4. 父对象删除或作废时，从对象按规则级联失效。

---

## 9. 首批覆盖范围

### 9.1 第一批样板对象

| 主对象 | 从对象 | 优先级 |
|--------|--------|--------|
| `AssetPickup` | `PickupItem` | P0 |
| `AssetTransfer` | `TransferItem` | P0 |
| `AssetReturn` | `ReturnItem` | P0 |
| `AssetLoan` | `LoanItem` | P0 |

### 9.2 第二批候选对象

| 主对象 | 从对象 |
|--------|--------|
| `PurchaseRequest` | `PurchaseRequestItem` |
| `AssetReceipt` | `AssetReceiptItem` |
| `Maintenance` | `MaintenanceTask` |
| `DisposalRequest` | `DisposalItem` |

---

## 10. 技术边界与兼容策略

1. 原有 `BusinessObject`、`ObjectRelationDefinition`、`PageLayout` 不推倒重做，以增量字段和增量协议方式扩展。
2. 原有 `sub_table` 字段类型保留，但逐步从“字段内嵌定义”过渡为“关系驱动的 detail-region”。
3. 原有子表对象可暂时保留只读查询能力，避免影响导出、统计和排障。
4. 在迁移完成前，允许旧页面与新聚合页面并存，但主业务入口最终应切换到新聚合页面。

---

## 11. 风险与应对

| 风险 | 说明 | 应对 |
|------|------|------|
| 抽象过重 | 一次性改造范围大 | 先以 4 个资产操作单据为样板 |
| 旧逻辑耦合 | 现有动态页和专用页并存 | 采用灰度切换与兼容层 |
| 设计器复杂度提升 | `detail-region` 增加设计复杂度 | 先做 `inline_table` 一种基础渲染器 |
| 数据兼容性 | 旧对象仍被当作普通对象使用 | 通过迁移脚本补全对象角色与导航配置 |
| 测试成本上升 | 主从页面组合增多 | 优先补充主链路集成测试与 E2E |

---

## 12. 成功标准

1. 资产操作类单据全部迁移到正式主从聚合模型。
2. `*Item` 明细对象不再作为顶级业务入口暴露给普通用户。
3. 新建、编辑、只读三种页面基于统一聚合运行时渲染。
4. 布局设计器可正式配置单据的主表区与子表区。
5. 后续新增单据头/单据行对象时，不再需要重复搭建独立页面模型。

---

## 13. Definition of Done

1. 主从聚合元数据协议已落库并被运行时识别。
2. 四个资产操作单据已切换到统一聚合页面。
3. 子表编辑、只读、汇总、导入导出具备统一协议。
4. 布局设计器已支持 `detail-region` 配置与发布。
5. 主从继承规则已在权限、流程、状态和生命周期上生效。
6. 关键链路自动化测试通过。
