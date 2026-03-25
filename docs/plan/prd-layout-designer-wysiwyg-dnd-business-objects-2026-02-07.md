# PRD: Layout Designer WYSIWYG + Drag Reorder + Business Objects List Recovery (2026-02-07)

## 背景 / 问题陈述
- 平台定位：元素驱动（element-driven）的低代码平台，设计态（Designer）与运行态（Runtime）必须尽可能一致（WYSIWYG），否则会导致“所见非所得”，影响可交付性。
- 现状问题（P0/P1）：
- `System → Business Objects` 列表页面为空（实际 API 有数据，但前端解析不兼容）。
- `Page Layout Designer` 画布内字段无法拖拽调整顺序（缺少稳定的 reorder 能力）。
- Layout Designer 预览与对象详情页（Runtime Detail）在字段呈现上不一致（标签/布局结构差异明显）。

## 目标
- G1：`Business Objects list` 始终能看到系统硬编码对象 + 自定义对象（至少硬编码对象应稳定展示）。
- G2：Layout Designer 支持画布内字段拖拽排序：
- 同一容器内 reorder（section / tab / collapse item）。
- 允许跨容器移动字段（可选，作为加分项）。
- G3：Layout Designer 预览在“字段布局/标签呈现”层面尽量复用运行态呈现方式，显著缩小 WYSIWYG 偏差（尤其是 Element Plus 的 `el-form` / `el-form-item` 标签宽度、对齐方式、网格间距）。

## 非目标（本 PRD 不做）
- 不做完整的 Designer-Runtime 渲染管线合并（比如直接复用 `DynamicFormRenderer` 并对每个 field 注入可选中/可拖拽的 wrapper slot）。这需要引擎层提供插槽/渲染钩子，属于下一阶段。
- 不改变后端 `/api/system/business-objects/` 的返回形状（当前为 `{ hardcoded, custom }` 分组 registry），以避免破坏已有测试/调用方。后续可新增 `flat` 形态接口或 query 参数做兼容升级。
- 不实现 BusinessObjectForm 的创建/编辑完整流程（该组件目前存在 TODO API 调用缺口，属于另一个 PRD）。

## 用户故事
- US1：作为平台管理员，我打开 `Business Objects` 能立即看到对象列表（系统对象+自定义对象），并可进入字段/布局配置入口。
- US2：作为对象设计者，我在 Layout Designer 画布内可以拖拽字段调整顺序，保存后运行态页面顺序一致。
- US3：作为对象设计者，我在 Designer 看到的字段标签布局（label 宽度/对齐）与运行态接近，不再出现“设计里一套、运行里一套”。

## 需求 / 验收标准
### Business Objects
- A1：列表不为空（至少包含硬编码对象 registry）。
- A2：硬编码对象行展示“系统/自定义”类型正确（不依赖 `isHardcoded` 字段存在）。
- A3：字段数/布局数缺失时不阻塞展示（允许为空/0）。

### Layout Designer
- B1：画布内字段可拖拽排序（mouse drag，非 HTML5 原生 draggable）。
- B2：拖拽不应被输入控件“抢走”，应从 label/空白区域拖拽。
- B3：排序变更会更新 `layoutConfig` 并可被 `Save/Publish` 持久化。
- B4：预览使用 `el-form`/`el-form-item` 结构渲染字段（与运行态 `DynamicFormSection` 一致的 label 宽度与对齐）。

## 技术方案（概要）
### 1) Business Objects List 兼容分组返回
- 前端将 `/system/business-objects/` 的 `{ hardcoded, custom }` 结果扁平化为表格数据源。
- 对每条记录进行“标准化”映射：统一出 `code/name/isHardcoded/enableWorkflow/fieldCount/layoutCount/djangoModelPath` 等字段。

### 2) Layout Designer DnD（SortableJS）
- 使用 `sortablejs` 绑定到画布内每个字段容器：
- regular section：`.section-fields`
- tab：`.tab-fields`
- collapse：`.collapse-fields`
- 通过 DOM `data-container-kind` + `data-section-id/tab-id/collapse-id` 将拖拽事件映射回 `layoutConfig` 数据结构，onEnd 时更新字段数组顺序。
- 结构变化（新增 section/tab/collapse item）时重建 sortable 实例。

### 3) Designer 预览结构向 Runtime 靠拢
- Designer 画布预览改为：
- 外层 `el-form`（`label-width=120px`、`label-position=right`）
- 每个字段使用 `el-form-item` 包裹 `RuntimeFieldControl`
- 网格容器统一为 `display:grid + gap:12px + columns-*`
- 保持“选中叠层/删除按钮”等设计态能力，但字段本体渲染与运行态一致。

## 风险与缓解
- R1：Sortable 与 Vue 渲染可能产生 DOM/数据不同步。
- 缓解：onEnd 只改数据源（`layoutConfig`），依赖 Vue 重新渲染纠正 DOM；并在结构变化时重建 sortable。
- R2：跨容器移动字段时，目标容器数组可能为空或不存在。
- 缓解：在解析容器 meta 时确保数组存在（`fields ||= []`）。
- R3：Designer/Runtime 的完全一致仍有差距（比如 section header、card 风格、权限/只读规则等）。
- 缓解：本 PRD 先把“字段呈现结构”对齐；下一阶段引擎层提供 wrapper slot，实现真正的 WYSIWYG。

## 测试计划
- Build Gate：`frontend npm run build`
- E2E Gate：保留现有 `dynamic-object-detail-values` smoke，确保运行态详情页不回归。
- 手工验证：
- `System → Business Objects` 进入后表格有数据。
- Layout Designer：拖拽 reorder，保存后回到运行态页面顺序一致。

## 下一阶段（建议）
- 引擎层增加 `DynamicFormSection`/`DynamicFormRenderer` 的可插拔 wrapper：
- 允许 Designer 注入 `fieldWrapper`（用于 overlay/drag-handle/selection），让设计态与运行态真正共享同一渲染树。
- 后端提供 `GET /api/system/business-objects/flat/` 或 `?shape=flat`，返回标准化分页列表，减少前端兼容分支。

