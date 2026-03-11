# PRD: 单据对象子表关联资产信息架构演进与优化

> **版本**: v1.0  
> **日期**: 2026-03-11  
> **作者**: System Architect  
> **状态**: 待评审

---

## 1. 背景与深度源码分析

### 1.1 需求背景
在新一代资产管理系统 (NEWSEAMS) 中，资产相关的业务动作（如领用、调拨、借用、归还）均以“单据 (Document/Order)”的形式流转。
目前，系统针对这些单据对象实现了与资产的关联，但展示形式和底层定义大多复用了通用的“相关列表 (Related List)”机制。业务线提出反馈：单据对象应当将关联入单的资产信息，以“子表 (Sub-table / Line Items)”的形式强聚合展示，而非散落在相关的 Tab 页内。

### 1.2 源码现状剖析
经过深度走查项目的核心底层数据模型库 `apps/assets/models.py` 与元数据驱动层 `apps/system/models.py`，现状如下：

**1. 单据数据表设计已天然具备“主子表”物理结构：**
在数据库设计层面，所有的核心业务单据已经非常规范地遵从了 `Header -> LineItem -> Asset` 的结构：
- **领用单 (AssetPickup)**拥有独立的明细表 **PickupItem**，通过 `ForeignKey` 指向 `AssetPickup` (`on_delete=CASCADE`) 并通过 `ForeignKey` 指向 `Asset` (`on_delete=PROTECT`)。
- **调拨单 (AssetTransfer)**对应 **TransferItem**。
- **借用单 (AssetLoan)**对应 **LoanItem**。
- **归还单 (AssetReturn)**对应 **ReturnItem**。

**2. 元数据驱动层 `ObjectRelationDefinition` 的支撑现状：**
系统平台基座的《对象关系定义表》目前已具备了表示子表概念的基础模型字段：
- 关系种类 (`relation_kind`): 已经支持 `through_line_item` 与 `direct_fk`。
- 展示层级 (`display_tier`): 定义了 `L1 (Line Item)`, `L2 (Business Related)`, `L3 (Extended Related)` 三层结构。

**3. 结语：**
项目后端的数据库建模其实是非常超前且成熟的，**物理外键和模型设计上已经完全是标准的单据表头-表体结构**。
核心痛点在于：由于早期敏捷迭代阶段的界面自动化渲染逻辑，前端把 `ThroughLineItem` 级别的关系当成了普通的 `direct_fk` 级相关数据（L2），降级统一放置在了详情页的“相关 (Related Tab)”中。

---

## 2. 核心结论与建议

> **核心结论：是的，所有单据对象（AssetPickup, AssetTransfer, AssetLoan, AssetReturn 等）都必须实施此“内嵌子表”升级。**

**为什么？**
1. **业务本质决定**：单据表头（申请人、审批流、时间）和单据表体（资产条目）是不可分割的“强生命周期绑定”整体。
2. **用户心智要求**：在业财一体化的成熟软件（如 Salesforce / SAP）中，“单据 + 行项目”是在同一屏内直接展示并提供“增减行”操作的，把它收起到相关 Tab 会造成操作的割裂。

---

## 3. 架构优化方案 (PRD)

本次优化**不涉及大的后端表结构改造**，重点在**元数据关系提权**与**前端展示引擎升级**。

### 3.1 元数据改造 (Metadata Adjustments)
- 针对所有的单据行项目对象（如对 `AssetPickup` 而言的 `PickupItem`）：
  - 维持 `ObjectRelationDefinition.relation_kind = 'through_line_item'`。
  - **关键改动**：将其 `ObjectRelationDefinition.display_tier` 必须全部设置为 `L1` (Line Item / Inline Detail)。
  - **展现模式**：`display_mode` 设置为 `inline_editable`（在草稿态允许行内编辑增删）或 `inline_readonly`（审批中或已结案态只能查看）。

### 3.2 详情页前端引擎升级 (BaseDetailPage & MainTabs)
- 拦截引擎的数据分发：在 `useBaseDetailPageRelations.ts` 中，拦截抓取回来的关联关系清单。
- 如果遍历发现存在 `display_tier == 'L1'` 的关系：
  - **不放入** 右侧的 / 下方的“Related”大 Tab 中。
  - **提取入** “Details Tab” (表头摘要信息) 的正下方。
- 引入新的展示组件 `InlineLineItemTabs.vue` (或类似实现)，将该 L1 关系渲染为一个宽表（Grid）。该表需紧贴单据的属性区块展示。

### 3.3 子表操作交互进化 (Interactive UX)
- **批量挑库 Drawer**：针对单据子表提供专业的 `[+ 批量添加资产]` 的动作按钮。点击后不是跳转出去，而是从右侧抽屉弹出一个可搜索、可多选的“台账资产选择器”，选中确认后一键拉入单据内嵌子表中。
- **行状态与动作联动**：如果是调拨明细（TransferItem），允许用户在行项目子表中，除了展示资产信息，还有专门拉出一列显示该行资产的特有表单字段（例如：`to_location` 目标位置），实现真正的“一单行内填报”。

---

## 4. 验收标准与测试用例 (Acceptance Criteria)

### 4.1 数据定义验收
- [ ] 系统内置生成或脚本刷新的 `ObjectRelationDefinition` 数据中，`parent_object='AssetPickup'`, `target_object='Asset'` (中间表 `PickupItem`) 的关联记录，其 `display_tier` 字段值严格等于 `L1`。
- [ ] 后端动态 API `getRelations()` 接口的返回值中，上述记录的 payload 里能正确输出 `display_tier: 'L1'`。

### 4.2 视图呈现验收
- [ ] 用户进入处于“草稿”状态的【领用单】详情页，此时“概览 (Details)” Tab 的下半部分应直接内嵌渲染出“领用明细表”的宽版 Grid，而不是必须切换到“相关 (Related)” Tab 才看得到。
- [ ] 用户进入处于“草稿”状态的【领用单】，点击明细表上方的 `[新增明细]`，预期不进行整页路由跳转，而是能够在当前页（通过 Dialog 或 Drawer 或行内行）选择所需的库存资产。
- [ ] 用户切换到该【领用单】的“相关 (Related)” Tab时，原先在里面的“领用明细”不应该再次出现（排重）。

### 4.3 普适性验收
- [ ] 针对【调拨单 AssetTransfer】打开详情页验证，同样能在核心信息的下方找到内嵌的“调拨明细子表”。
- [ ] 针对【借用单 AssetLoan】打开详情页验证同样适用。
- [ ] 针对【归还单 AssetReturn】打开详情页验证同样适用。

### 4.4 状态权限验收 (只读性)
- [ ] 进入一张状态为 **"已完成 (completed)"** 的【领用单】，其内嵌明细表中不能提供 `新增明细` 按钮。
- [ ] 内嵌明细表中的数据行，不能提供 `移除/删除` 按钮。仅供通过 `inline_readonly` 模式查阅。

---
*注：具体前端组件的开发与 CSS 适配，依据现阶段 Designer 模式进行平滑对接，尽量复用现有 Table 渲染基础设施。*
