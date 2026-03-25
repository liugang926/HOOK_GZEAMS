# 详情页关联对象(Related Objects) UI排版优化 PRD

## 1. 现状分析 (Current State)
经分析当前 `BaseDetailPage.vue` 的实现，我们发现在页面主体区域（Main Column 和 Sidebar Column）渲染完毕，并且显示完审计信息（Audit Info）之后，才在页面的**最底部**统一追加渲染 `related-objects-section`（相关对象）。

**存在的问题：**
* **无限滚动与信息层级深**：当对象的字段很多（详情很长）或者页面具有多个复杂区块时，用户必须滚动到最底部才能看到相关对象（如相关联系人、相关的工单等）。
* **空间利用率低**：详情区和相关区是上下堆叠的，这与现代企业级软件的高效排版理念相违背。
* **专业性欠缺**：大型CRM系统（如Salesforce, Dynamics 365）很少采用底部平铺关联表格的做法，因为这会导致操作效率极其低下。

## 2. Salesforce 成功经验参考 (Salesforce Reference)
在构建企业级详情页（Record Page）时，Salesforce Lightning Experience 提供了一种极其专业的标准范式：

1. **高亮面板 (Highlights Panel)**：顶部固定的关键字段和核心操作按钮。（目前项目已实现类似功能的 `record-profile-header`）
2. **多标签页主栏 (Tabbed Main Column)**：主体区域默认是一个巨大的 Tab 组件。通常包含两个核心标签页：
   * **相关 (Related)**：默认或次级标签，专门展示与当前对象相关联的其他对象列表（Related Lists）。
   * **详情 (Details)**：专门展示当前对象的全量字段（通过多个可折叠的 Sections 进行组织）。
3. **右侧边栏 (Right Sidebar)**：放置高频交互组件（如活动时间线 Activity Timeline）或者被标记为需要快捷查看的“关键相关列表”（Compact Related Lists）。

**使用标签页(Tabs)并排显示的优势：**
* 极大地缩短了页面的视觉长度。
* 信息的分类更符合用户心智模型（“看本体” vs “看关系”）。

## 3. 详细调整方案 (Adjustment Plan)

为了达到资深专业级水准并且贴近 Salesforce 的体验，建议对 `BaseDetailPage.vue` 及布局规范进行以下重构：

### 3.1 引入顶级 Tab 布局机制
在 `BaseDetailPage.vue` 的 `main-column` 中引入顶级的页面模式切换：
* **模式定义**：将现有的“详情区块集合 (`mainSections`)”放入名为**“详情”**的 Tab 内；将原底部的“关联对象区块集合 (`groupedReverseRelationSections`)”放入名为**“相关”**的 Tab 内。
* **UI交互**：当用户进入详情页时，他们可以清晰地在“详情”和“相关”之间切换，而无需进行深度滚动。

### 3.2 细化“相关列表” (Related Lists) 的渲染模式
Salesforce 中关联对象的展示在不同区域有不同的渲染尺寸，我们需要引入该机制：
* **主侧栏分流**：由于项目已经引入了 `has-sidebar` 的概念，底层数据结构 (`ReverseRelationField`) 应当增加 `position` 或 `layoutType` 属性。
* **标准模式 (Standard)**：在“相关” Tab 中，相关表格以完整宽度的卡片 (Card) 显示。
* **紧凑模式 (Compact)**：如果某些相关对象（比如“关联附件”、“项目小组成员”）被配置渲染在 Sidebar（侧边栏）中，则应使用紧凑型表格（只展示前2-3列），并提供“查看全部 (View All)”的底部链接。

### 3.3 相关对象卡片 (Card) 的视觉升级
不再使用简单的标题加一个平铺的 Element Plus Table，而是采用标准卡片结构：
* **Header**: 左侧为图标 + 标题（伴随记录总数 Badge，例如 `联系人 (5)`），右侧为操作按钮区（如“新建”、“关联”按钮）。
* **Body**: 默认只显示前 5-10 条记录（高度限制）。
* **Footer**: 统一的“查看全部”链接。

### 3.4 示例级骨架改造 (Pseudocode / HTML Structure)
改造后的 `BaseDetailPage.vue` 主体部分大致结构如下：

```html
<div class="detail-layout-container" :class="{ 'has-sidebar': sidebarSections.length > 0 }">
  <!-- Main Column -->
  <div class="main-column">
    <el-tabs v-model="activeMainTab" class="record-main-tabs">
      
      <!-- 标签页 1：详情 -->
      <el-tab-pane label="详情 (Details)" name="details">
        <div class="detail-sections">
           <!-- 渲染原来的 mainSections 里的字段区 -->
        </div>
      </el-tab-pane>

      <!-- 标签页 2：相关 -->
      <el-tab-pane label="相关 (Related)" name="related">
        <div class="related-objects-section">
           <!-- 渲染各个 RelatedObject 组成的 Card 列表 -->
        </div>
      </el-tab-pane>

    </el-tabs>
  </div>

  <!-- Sidebar Column -->
  <div v-if="sidebarSections.length > 0 || sidebarRelations.length > 0" class="sidebar-column">
      <!-- 渲染原有的侧边栏字段区 -->
      <!-- 渲染分配给侧边栏的 紧凑型关联对象列表 (Compact Related Lists) -->
  </div>
</div>
```

## 4. 布局设计器 (Layout Designer) 适配方案

要实现上述 Salesforce 风格的排版，现有的 WYSIWYG 页面布局设计器 (`WysiwygLayoutDesigner.vue`) 也必须进行相应的体验升级和底层数据结构适配：

### 4.1 左侧组件面板扩展 (Palette Expansion)
* **新增“相关对象”组件组 (Related Objects Group)**：
  在左侧拖拽面板除了现有的“基础字段”之外，应该额外请求该对象挂载的 `ReverseRelations` 元数据，将其列为可拖拽的独立块。
* **组件类型区分**：将这些块识别为特殊的 FieldType 或组件类型（如 `@related_list`），允许它们被拖入画布。

### 4.2 画布渲染支持 (Canvas Rendering)
* **全局 Tab 容器化**：画布默认可以开启“启用详细信息级 Tab”选项。开启后，画布不再是一个扁平的流式容器，而是预置好的“详情”与“相关”双 Tab 布局（或自由新增 Tab）。
* **相关列表占位符 (Placeholder)**：当相关列表被拖入主栏（例如“相关”Tab）时，渲染一个占据 24 列宽度的标准化 Card 骨架图；如果拖入侧边栏，则渲染为紧凑型骨架图。
* **规则互斥**：普通详细字段不允许拖入“相关”Tab；相关列表也不建议和普通字段在同一个流式 Row 内混合排版（强制换行铺满）。

### 4.3 属性面板增强 (Property Editor)
当选中画布中的“相关列表”模块时，右侧的 `SectionPropertyEditor` 或 `FieldPropertyEditor` 应该显示专属配置：
* **显示模式 (Display Mode)**：标准表格模式 (Standard Table) / 紧凑模式 (Compact List)。
* **最大显示行数 (Max Rows)**：默认 5 条。
* **操作按钮映射**：是否显示“新建”、“批量操作”等。

### 4.4 默认布局 (Default Layout) 回退机制适配
在许多情况下，用户并未针对某个业务对象配置过**显式**的 `LayoutConfig`（即 `WysiwygLayoutDesigner` 未曾保存过数据）。此时系统会进入默认的元数据加载流（Fallback），如 `DynamicDetailPage.vue` 所述。为了让默认布局也显得专业：
* **动态 Tab 注入**：当解析器发现当前对象没有任何显式布局，但拥有 `runtimeReverseRelationFields` (关联对象) 时，在内存中动态构建一个根级别的 Tab 组件。
* **分流逻辑**：将所有的 `editableFields` 投影到“详情” Tab 中；将所有的 `ReverseRelationFields` 投影到“相关” Tab 中。
* **默认渲染模式**：在未配置的情况下，所有的关联表格均以“标准表格 (Standard Table)”模式展示。

## 5. 底层关系架构的优化建议 (Architectural Recommendations)

为了更好地支撑上述专业级的 UI 排版，当前基于 `ObjectRelationDefinition` 的前端动态数据拉取体系在后端及全栈架构层面，建议做以下深度增强：

### 5.1 数据模型与元数据一致性（Schema Consistency）
既然我们在元数据表中记录了 `target_fk_field`，它就是对物理模型的一个弱映射。
* **一致性校验 (Health Check)**：在核心服务层增加探测器机制，定时或在服务启动时验证 `target_object_code` 对应的实体模型中是否依然真实存在该外键。
* **防呆保护 (Guardrails)**：如果通过动态模型配置中心删除某个字段，底层应捕获该动作，并验证是否有相应的 `ObjectRelationDefinition` 依赖它，实行级联禁用或阻断。

### 5.2 深度索引与性能防御（Performance & Indexing）
随着“相关明细”、“关联附件”等大量表数据的增加，动态过滤 `target_fk_field = parent_id` 可能成为性能瓶颈。
* **强制外键索引 (Mandatory FK Indexing)**：凡是承担着关联查找角色（Lookup field）的字段，模型层都必须确保存在物理层的 `db_index=True`。
* **防雪崩与预聚合**：后续在提供 Tab 或 Card 的徽标数（Badge Count）时，应避免触发全表扫描。对于高频场景建议在父对象中引入 Counter Cache（计数器缓存）机制。

### 5.3 多对多与“幽灵”中间表（Through Tables & Many-to-Many）
* **穿透视图 (Through Projection)**：针对配置中已有的 `relation_kind='through_line_item'`，UI 渲染时不应该让用户去“浏览并点开中间表”，而是由 RelationQueryService 负责将真正的 Target Model 数据 Join 投射并拉平下发，在前端卡片层直接展示目标记录。

### 5.4 权限穿透与数据隔离（Row-Level Security / Scoping）
* **对象级权限网关过滤**：不要将所有的反向关联一股脑透传给前端页面。后端在 `get_relations()` 接口中，必须结合当前登录人的 RBAC 权限（例如：用户没有针对某目标相关表的读取权限）。如果用户不可读，直接从 Relation 列表中剔除，防止前端渲染出错报 403。

### 5.5 生命周期级联（Lifecycle Cascading）
区别弱引用（Lookup）和强从属（Master-Detail）。
* **引入级联标识**：在关系定义中扩展是否涉及级联删除的属性。在双 Tab 布局中，如果用户选择删除当前记录，系统应当能够借此感知此行为将一并消灭多少强关联的明细数据，从而给出致命警告提醒。

## 6. 实施建议与优先级 (Implementation Roadmap)
2. **(Phase 2 - 中优) 卡片视觉翻新**：修改 `RelatedObjectTable.vue`，增加 Card 的外观包装，使其顶部具备专业 CRM 的汇总信息并限制默认展示行数。
3. **(Phase 3 - 长期) 布局解析器升级**：修改 `detailSchemaProjector` 或类似编排引擎，允许元数据配置关联关系的所处分栏（Main / Sidebar）。
