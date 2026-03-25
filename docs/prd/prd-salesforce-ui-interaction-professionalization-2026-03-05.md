# GZEAMS 核心系统交互体验与专业化提升 PRD (深度评估版)

**文档状态**: 草稿
**作者**: Frontend UX Architect
**日期**: 2026-03-05
**对标产品体系**: Salesforce Lightning Design System (SLDS), ServiceNow, Workday

## 1. 深度基建现状与差距分析 (Gap Analysis)

在第一轮浅层评估的基础上，我们对 `src/router`、`src/utils/cacheWrapper.ts`、`src/components/engine` 及全局样式 `src/styles` 进行了深度代码分析。目前 GZEAMS 底层引擎极其完善，但在向世界级企业软件 (World-Class Enterprise SaaS) 演进的过程中，以下交互和视觉架构仍然存在明显断层：

### 1.1 状态管理与感知速度 (SWR & Optimistic UI)
*   **当前实现**：拥有非常优秀的 `withSWR` 缓存封装和 IndexedDB 持久化。但是，在 UI 层面缺乏**乐观更新 (Optimistic UI Updates)**。
*   **Salesforce 标杆**：在列表页或详情页修改状态时，UI 会**立即**变化，后台并发请求。若请求失败，则安静回滚并提示。当前 GZEAMS 仍依赖于 Spinner 阻塞用户操作。
*   **改进方向**：在 List View 的 Batch Actions 和 Inline Edit 中全面推行乐观 UI 模式。

### 1.2 路由机制与沉浸式体验 (Navigation & Context)
*   **当前实现**：动态路由 (`DynamicListPage`, `DynamicFormPage`) 结构清晰。但页面跳转为传统的整页切换 (Full Page Transition)。
*   **Salesforce 标杆**：极度依赖 Console Navigation 模式（基于 Tab 的多开工作台）或深度使用 Right Panel Drawer（右滑抽屉）来处理子级对象的查看和新建，**坚决不打断用户当前的工作流上下文**。
*   **改进方向**：对于 Reference 字段的新建、子表记录的快速查看，将路由跳转 (`target="_blank"`) 改造为 Slider Drawer (侧滑面板) 层叠显示。

### 1.3 数据录入：脏状态与微交互 (Dirty State & Inline Validation)
*   **当前实现**：表单组件 (`DynamicForm`) 验证是在 Submit 时集中拦截或单个 Field 失焦时触发红色文本，且页面切换尚未发现严密的脏数据守卫机制 (Dirty State Guard)。
*   **Salesforce 标杆**：
    *   页面未保存离开时，具有强烈的防抖保护和全局底部浮动 Save Toolbar。
    *   字段级编辑拥有“撤销(Undo)”小图标，允许回滚单个字段的修改。
*   **改进方向**：引入统一的表单脏状态管理 (`isDirty` flag)，详情页进入内联编辑后，底部弹出浮层栏，包含保存和取消。

### 1.4 复杂字段的高级展示 (Advanced Field Rendering)
*   **当前实现**：`ReferenceField` 已经具备了非常高级的形态（支持 Hover Card Popover 和 Lookup Dialog），这是极为正确的方向。但在视觉表现上仍然略显生硬（基于标准 Element Plus 样式）。
*   **Salesforce 标杆**：Reference 悬浮面板包含更丰富的元数据图表，相关状态以鲜艳的 Pill (药丸标签) 展现；图像附件字段支持瀑布流预览。
*   **改进方向**：升级 `ReferenceField` 的 Hover Card，注入微小骨架动画；升级 `SubTableField`，支持高密度的 Spreadsheet 风格输入。

### 1.5 可访问性 (A11y) 与键盘导航 (Keyboard Navigation)
*   **当前实现**：依赖 Element Plus 基础的 `tabindex`。
*   **Salesforce 标杆**：对高频核心业务对象 (如 Finance/Inventory) 支持极其硬核的键盘操作：J/K 上下选择行，Enter 原地进入编辑，Esc 退出编辑，Ctrl+S 全局保存。
*   **改进方向**：在 `BaseListPage` 和 `SubTableField` 中引入高级快捷键域 (Hotkey Scopes)，满足财务和库管的盲打诉求。

---

## 2. 核心体验重构方案 (Actionable Evolution Plan)

### Plan A: "Comfy vs Compact" 信息密度收束体系 (全局)
**目标:** 解决目前页面空间利用率低的问题。
*   **规范化 Tokens (`src/styles/tokens.scss`)**:
    *   增加 `--gzeams-density-multiplier`。
    *   Compact 模式下，表格行高设定为 `32px` (标准为 `48px`或 `40px`)。
    *   输入框高度从 `32px` 降至 `28px`，字体收束至 `13px`。
*   **落地点**: 用户偏好设置 (User Preferences Store) 提供切换选项，影响整站 CSS Var 注入。

### Plan B: Context Drawer 沉浸式引擎 (路由层)
**目标:** 保持业务上下文不断裂，减少新开 Browser Tab。
*   **拦截创建行为**: 当用户在 Reference Field 或 Select 下拉框点击“新建记录”时，不再 `window.open('/objects/xxx/create')`。
*   **弹出设计**: 调用全局共享的 `DynamicFormDrawer` 组件，从右侧滑出 (`width: 600px` 或 `800px`)。保存后，自动将新生成的 ID 逆向填充(Back-fill) 到原字段并触发校验。

### Plan C: 矩阵式 Sub-Table 急速录入 (组件层)
**目标:** 子表明细需要达到类似 Excel 的录入光速。
*   重写 `SubTableField.vue` 的交互基座，剔除每行末尾繁杂的操作按钮。
*   引入 `DataGrid` 模式：用户可以直接在表格单元格点击激活输入，支持 Tab 键自动横向/折行移动焦点。
*   底部提供一个常驻的 `+ Add Row` 幽灵按钮 (Ghost button)。

### Plan D: 智能骨架与平滑过渡 (微交互层)
**目标:** 彻底消灭页面“抖动”与“白屏 Spinner”。
*   在 `app.vue` 或 `router` 的 `beforeEach` 中捕获首次加载。
*   利用 `DynamicDetailPage` 的 Schema 先验设定，在获取到真实 JSON 数据前，直接利用 Layout Engine 绘制与最终页面结构 **100% 结构对齐**的骨架屏 (Skeleton layout)。

---

## 3. 实施优先级排期 (Sprint Backlog Ranking)

| 阶段 / 史诗 (Epic) | 特性描述 | 预估成本 | 业务价值/NPS提升 |
| :--- | :--- | :--- | :--- |
| **Phase 1: 视觉专业化基石** | 1. 落地 Compact/Comfy 密度切换主题系统<br>2. BaseListPage 列表密度的响应式调整 | 1周 | 高 (立竿见影的专业感提升) |
| **Phase 2: 沉浸式上下文流** | 1. 全局 Context Drawer (右滑抽屉新建)<br>2. Reference Hover Card 增加平滑进场动画 | 1.5周 | 极高 (避免弹跳，保持专注) |
| **Phase 3: 键盘与防呆机制** | 1. 表单全局脏状态管理与退出拦截 (Dirty Guard)<br>2. 页面底部 Floating Save Bar (内联编辑/表单保存) | 1.5周 | 极高 (防止数据丢失风险) |
| **Phase 4: "Excel 化"与骨架屏**| 1. SubTableField (明细表) 升级为 DataGrid 光速录入<br>2. 基于 Schema 投影的 100% 对齐 Skeleton | 2周 | 高 (突破数据输入效率瓶颈) |

## 4. 结论与下一步
GZEAMS 的前端由于采用了严谨的 Schema 解析器（如 `runtimeLayoutResolver`、`renderSchemaProjector` 支持），进行上述“骨架屏渲染”和“行内快速录入”具有得天独厚的优势。我们不需要重构业务代码，而是通过改写底层 `engine` 和 `layout` 渲染器，即可让全平台的数百个 Business Object **全量自动升级** 至 Salesforce Lightning 级别的人机交互体验。
