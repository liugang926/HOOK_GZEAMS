# NEWSEAMS 全局架构深度分析与 Salesforce 对标优化 PRD

## 1. 文档信息
- **版本**: 1.0
- **日期**: 2026-03-09
- **定位**: 高级系统架构师与低代码平台专家视角
- **目标**: 对现有 `GZEAMS/NEWSEAMS` 项目在全栈视角（Django 后端与 Vue3 前端）进行全景扫描，深度对标 Salesforce Lightning Platform 架构理念，梳理系统架构优势、瓶颈以及亟需优化的领域，并提出架构演进与产品功能完善的战略级 PRD。

---

## 2. 核心架构现状总结 (Current Architecture Overview)
通过代码库深度扫描，系统当前已建立起一套具备商业化潜力的元数据驱动（Metadata-driven）多态业务对象引擎：

### 2.1 后端架构 (The Backend Data Engine)
- **核心模式**: 采用“混合物理与动态元数据架构”。由 `apps.system` 作为底座，21 个业务 Apps (如 assets, lifecycle, inventory 等) 围绕其运作。
- **配置底座**: 
  - `BusinessObject`: 控制对象的基类属性与行为特性（流程、软删除等）。
  - `FieldDefinition`: 支持 30+ 种丰富数据类型（含有 `formula`, `sub_table`, `reference` 以及基于 JSON 扩展和引用关系定义的特殊字段）。
  - `ObjectRelationDefinition`: 实现 `direct_fk` (直接关联)、`through_line_item` (通过中间表单据关联) 与 `derived_query` (派生查询) 的关系网。
- **运行时调度**: 大量底层 Service (如 `layout_generator.py`, `rule_engine.py`, `metadata_sync_service.py`, `relation_query_service.py`) 负责在运行时完成配置到数据的投影。

### 2.2 前端架构 (The Frontend Render Pipeline)
- **核心技术栈**: Vue 3 + Element Plus + Pinia + i18n。
- **引擎区 (Engine/Platform)**:
  - `platform/layout`: 拥有严密的渲染模型管道 (`renderSchema.ts`, `layoutCompiler.ts`, `detailSchemaProjector.ts`)，控制着字段按权限、规则、上下文组装成前端渲染态。
  - `fieldRegistry.ts`: Mapper 了后端 30 多种字段类型到对应的底层渲染 Vue 组件。
- **页面视图 (Common Views)**: 
  - `BaseDetailPage` (达到 2000+ lines 的超级详情页驱动引擎)。
  - `BaseListPage` (拥有复杂查询与动态列能力的列表屏)。
  - `WysiwygLayoutDesigner` (127KB 的所见即所得核心表单/页面流式布局器)。

---

## 3. Salesforce 架构基准对标分析 (Salesforce Benchmarking)

Salesforce Lightning Platform 的核心精髓在于：**极度抽象的数据定义**、**统一且无处不在的关系图谱**、**双态 UI 组件 (Lightning App Builder)**，以及**声明式的极简扩展**。

对比现行系统，我们的完成度与差距如下：

### 3.1 元数据 (Metadata & Schema)
- **Salesforce**: Custom Objects 与 Standard Objects 一视同仁；字段拥有完备的 Security (FLS) 和依赖关系配置。
- **NEWSEAMS 现状**: 已经实现了惊艳的 `BusinessObject` 统一包装，硬编码的 Django Model 通过 `ModelFieldDefinition` 与纯动态配置对齐。
- **✅ 架构亮点**: 保留物理表 (性能) 与 JSON 扩展 (灵活性) 的“双螺旋”引擎设计，十分超前。
- **🔴 核心差距**: 字段级权限 (Field-Level Security, FLS) 和记录级权限 (Row-Level Security/Sharing Rules) 尚未与 `PageLayout` 及 `renderSchema` 深度熔合；大量翻译与基础文本仍硬编码于前端而非依赖 Metadata Definition 下发。

### 3.2 关系与闭环 (Relationships & Closed-Loop)
- **Salesforce**: Master-Detail 与 Lookup 关系天然附带 Roll-up Summary，所有对象默认双向打通相关列表 (Related Lists)。
- **NEWSEAMS 现状**: 最新 PRD (`prd-object-relation-closed-loop-2026-03-05.md`) 证实，通过 `ObjectRelationDefinition` 和三种查询机制的引入，关系路由开始走向正轨。
- **🔴 核心差距**: `BaseDetailPage` 在 UI 等级上仍将关联关系简单以表格的形式堆积在页面**最底端**，缺乏 Salesforce 那种 Tab 隔离理念以及全局快速悬浮 (Hover Card) 和紧凑型 (Compact) 相关列表展示。对于长生命周期链路（采购->领用->维修->报废），可视化时间轴轴溯追踪尚未组件化打通。

### 3.3 布局与 UI 组装引擎 (Lightning App Builder / Designer)
- **Salesforce**: 页面区分 Record Page (巨型详情 + Tabs) 和 Compact Layout (缩微/新建页面)。组件可以随意按条件显示。
- **NEWSEAMS 现状**: 现存 `WysiwygLayoutDesigner` 极其重型，承担了所有绘制，但尚未有效区分 Mode A (全量详情展示) 与 Mode B (侧滑抽屉/创建向导的紧凑展示)。
- **🔴 核心差距**: 
  - 缺乏“双模式”的渲染解耦 (详见 `prd-salesforce-ui-architecture-phase6-2026-03-06.md`)。
  - 画布设计时缺乏健壮的撤销/动作还原机制 ("Undo/Redo") 和防止脏崩的本地草稿箱持久化。

---

## 4. 全局性优化调整方案与 PRD 纲要

基于以上对标，规划以下五大针对性优化与演进 PRD。

### 4.1 架构级一：重塑布局引擎与双模显示 (Dual-Mode Layouts)
*引用背景：解决单一表单在“查看”、“长记录编辑”与“弹窗抽屉快速新建”中的视觉不匹配。*
- **功能点 1: 拆分 Detail 与 Compact Layouts**
  - Schema 扩展：在 `PageLayout` 或渲染合约中增加 `layout_type` 枚举 (`Detail` / `Compact` / `QuickAction`)。
  - UI 改装：`WysiwygLayoutDesigner` 头部支持切换画布视口。Compact 模式禁用 Tabs/Accordions，限制为纯 1-2 列表格形态，用于诸如 `ContextDrawer.vue` 和新建模型中。
- **功能点 2: 详情页的多顶级 Tab 重组**
  - 改造 `BaseDetailPage`：剥离底部强追加的 `related-objects-section`。
  - 将画布默认升级为“详情 (Details)”与“相关 (Related)” 两大顶级平行 Tab 布局。
  - 当展示“相关”Tab 时，将当前 `ReverseRelationField` 以卡片（Cards 具备 5 条显示阈值及 View All）呈现，而非直铺全量 table。

### 4.2 架构级二：自动化菜单与智能对象注册表 (Smart Registry & Menu)
*引用背景：对象增多导致路由 `router/index.ts` 膨胀以及运维困难。*
- **功能点 1: 去中心化菜单编排**
  - 根据应用内的 `menuRegistry.ts`，基于 `BusinessObject` 上的 `menu_category` 和 `is_menu_hidden` 标识，系统启动时动态组装 Vue Router 树和左侧导航栏。
  - 实现防重叠注册 (Strict Singularity)，消除遗留的“多处别名”黑科技。
- **功能点 2: 渐进式多语言加载管道 (i18n Pipeline)**
  - 设计所有前端视图的文案抽离。当 `fields API` 发送元数据时，后端必须支持并优先通过 `_en` 或对应的用户 Profile 字典键返回 `label`/`placeholder`。
  - 前端渲染侧的 Formatters（时区、数字金额、日期）重构成根据浏览器文化或用户 `Context` 动态输出。

### 4.3 架构级三：相关联对象生命周期闭环展示增强 (Lifecycle Connectivity)
*引用背景：从“找资产”到“看资产的一生”。*
- **功能点 1: SubTable 组件的通用下沉**
  - 不仅在详情单据中呈现列表，更需要在 `DynamicFormPage` 级支持 SubTable (类似于采购单加减多行资产明细) 的交互式输入与直接校验，完成主从表同步提交。
- **功能点 2: Activity Timeline (追踪可视化视图)**
  - 在资产对象、维护单等对象的侧边栏 (Sidebar Column)，利用一个组件去归集其相关的所有生命周期变更日志 (如 `ActionLog` 与状态迁移记录)，打通 `Asset` 到 `DisposalRequest` 等操作链路，使用类似于 Salesforce 活动时间线的形式。

### 4.4 架构级四：极致前端韧性与SWR缓存 (Resilience & Caching)
*引用背景：复杂的重计算布局配置不可有“单点白屏击穿系统”。*
- **功能点 1: 细粒度 Error Boundary 注入**
  - 对于所有基于 `fieldRegistry` 动态 import 的表单组件以及 `RelatedObjectTable` 组件，采用 Vue 3 全局与局部 `onErrorCaptured` 拦截并降级为一个报错组件外壳，保证页面的主框架绝对不挂。
- **功能点 2: SWR (Stale-While-Revalidate) 数据与字典缓存**
  - 大量选项字段（数据字典）以及 Object Definitions 转移至基于 Pinia/本地 IndexedDB 的缓存代理请求。避免一个有 N 个引用类型的编辑框引发多条瀑布式并发字典查询。
- **功能点 3: 布局设计器的 Undo/Redo 状态机**
  - 在 `WysiwygLayoutDesigner` 的内部状态引流到基于 Immutable state 的操作历史库，保障拖拽设计复杂的大表单具有回滚安全网和数据防抖落盘能力。

### 4.5 架构级五：交互顺滑度与高级易用性 (Professional Ergonomics)
- **功能点 1: 全局无障碍与焦点捕获 (Focus Trap & A11y)**
  - 侧滑抽屉与 `Dialog` 弹出时自动剥夺底层 DOM 活动能力，实现键盘 `Tab` 流的严格内循环。快捷键矩阵 (Ctrl+S 等) 下沉为 Standard Hotkeys。
- **功能点 2: 骨架屏占位 (Skeleton Placement)**
  - 彻底淘汰全屏 `v-loading` 和 Spinners 导致的用户迷失与页面闪烁（CLS）。数据请求阶段使用严格依据布局配置动态渲染出等比、分区的骨架屏，提升业务级的心理感知速度。

---

## 5. 路线图执行建议 (Implementation Roadmap)

作为一套极其庞大的框架重整任务，推进必须严格分期：

1. **Sprint 1 (地基加固): 前端韧性与 SWR 缓存机制引入**
   - 优先实施 Error Boundary 拦截，重构字典层和 Schema 层的缓存请求管道。
   - 实现无缝骨架屏 (Skeleton Law)。
2. **Sprint 2 (视图再造): 双态布局与关联优化**
   - 梳理后端关系网（`ObjectRelationDefinition`），推进 `BaseDetailPage` 的主视窗重构：顶部主从两级 Tab，关联表切为 Card 结构。
   - 更新系统菜单管理器实现动态注入。
3. **Sprint 3 (超级表单体验): 设计器升维与 SubTable**
   - 给所见即所得编辑器加入高难度 Undo/Redo 时间回溯；为运行态带来通用的 SubTable 填报能力和活动时间线能力。
4. **Sprint 4 (企业化抛光): i18n 多语言管道贯通与样式白标** 
   - 彻底脱离硬编码，打通主题 Tokens 并接通翻译池系统。
