# PRD: 架构演进与技术债清理 — Sprint 0 前置优化
**文档版本:** 1.0  
**日期:** 2026-03-09  
**定位:** 系统架构工程师视角  
**前置依赖:** `prd-comprehensive-architecture-analysis-2026-03-09.md`  

---

## 1. Executive Summary

本 PRD 是对 `prd-comprehensive-architecture-analysis-2026-03-09.md` 中五大架构优化方案的补充与前置条件文档。

通过对代码库的深入审计，我们发现：在执行原 PRD 提出的双模布局引擎、智能菜单注册、生命周期闭环等大型改造之前，必须先解决若干被忽视的 **结构性技术债** 和 **缺失的工程基建**。否则，后续 Sprint 的改造将建立在不稳固的地基之上。

### 核心发现

| 审计项 | 现状 | 风险等级 |
|--------|------|---------|
| 布局设计器 (`WysiwygLayoutDesigner`) | ✅ 已良好拆解为 38 个子文件，主组件仅 599 行 | 🟢 低 |
| 菜单注册表 (`menuRegistry.ts`) | ✅ 已实现 `MenuRegistryManager` 类 (133 行) | 🟢 低 |
| 路由文件 (`router/index.ts`) | ⚠️ 595 行，含大量 Legacy Alias，未接入 `MenuRegistryManager` | 🟡 中 |
| 后端 Service 层 | ⚠️ 多文件超 25KB，职责边界模糊 | 🟡 中 |
| `BaseDetailPage.vue` | ✅ 已拆解为 721 行壳体 + 6 Composables + 3 子组件 | � 低 |
| 前端性能基线 | ❌ 完全缺失 | 🔴 高 |
| i18n 纪律 | ❌ 无 ESLint 硬编码检测，存量硬编码文案 | 🟡 中 |
| 测试策略 | ✅ `platform/layout/` 有 1:1 测试覆盖 (20 test files) | 🟢 低 |

---

## 2. 架构现状深度审计结论

### 2.1 布局设计器 — 已优于预期

原分析 PRD 描述 `WysiwygLayoutDesigner.vue` 为 "127KB 的超级组件"。经代码审计，**团队已完成了出色的 Composable 拆解**：

```
WysiwygLayoutDesigner.vue          599 行 (壳体 + 模板)
├── useDesignerState.ts            (状态管理)
├── useDesignerHistory.ts          (Undo/Redo 已实现)
├── useDesignerCanvasInteractions.ts (拖拽交互)
├── useDesignerPalette.ts          (左侧面板)
├── useDesignerSelection.ts        (选择态)
├── useDesignerFieldEditing.ts     (字段编辑)
├── useDesignerPersistence.ts      (持久化)
├── useDesignerLifecycle.ts        (生命周期)
├── useDesignerPreview.ts          (预览渲染)
├── useDesignerChangePipeline.ts   (变更管道)
├── useDesignerFieldCatalog.ts     (字段目录)
├── useDesignerDragInteractions.ts (拖拽细节)
├── useDesignerResizeInteractions.ts (尺寸调整)
├── DesignerToolbar.vue            (工具栏)
├── DesignerFieldPanel.vue         (字段面板)
├── DesignerPropertyPanel.vue      (属性面板)
├── DesignerCanvas.vue             (画布)
├── DesignerCanvasSectionRenderer.vue (区块渲染器)
├── DesignerCanvasFieldRenderer.vue  (字段渲染器)
├── DesignerFieldCard.vue          (字段卡片)
├── designerTypes.ts               (类型定义)
├── designerTreeUtils.ts           (树操作)
├── designerLayoutAdapters.ts      (布局适配)
├── designerContainerUtils.ts      (容器工具)
└── ... (共 38 个文件)
```

**结论**: 原 PRD Sprint 3 中提出的"设计器升维"可直接在现有架构上进行，无需额外拆解。`useDesignerHistory.ts` 已提供 Undo/Redo 基础能力 (`canUndo`, `canRedo`, `undo`, `redo`, `push`, `maxHistory: 50`)。

### 2.2 菜单注册表 — 已具备基础

`menuRegistry.ts` 中的 `MenuRegistryManager` 已实现：
- 11 个预定义菜单分类（`asset_master`, `lifecycle`, `finance` 等）
- 基于 `menuCategory` 和 `code` 的智能分类回退
- 重复注册检测 (`registeredObjects` Set)
- `isMenuHidden` 过滤

**差距**: 该 Manager 尚未接入实际的 Sidebar 组件和 Vue Router。`router/index.ts` 仍维护 3 套硬编码路由映射：

```typescript
// router/index.ts 中的三套遗留路由表
ADDITIONAL_BUSINESS_OBJECT_ROUTES    // ~20 条
LEGACY_OBJECT_LIST_CREATE_ROUTES     // ~5 条
LEGACY_OBJECT_LIST_ONLY_ROUTES       // ~6 条
```

### 2.3 BaseDetailPage — ✅ 已完成拆解

`BaseDetailPage.vue` 已从原始 **1948 行** 成功拆解至 **721 行**（降幅 63%），采用了与 Designer 一致的 Composable + 子组件策略：

```
BaseDetailPage.vue                          721 行 (壳体 + 模板 + 骨架屏)
├── useBaseDetailPageActions.ts             143 行 (编辑/删除/保存/返回操作)
├── useBaseDetailPageFields.ts             244 行 (字段值解析/网格布局/编辑类型)
├── useBaseDetailPageRelations.ts          144 行 (反向关联获取/分组/运行时解析)
├── useBaseDetailPageSections.ts           104 行 (Section 折叠/Tab 切换/标题解析)
├── useBaseDetailPageLayout.ts              26 行 (主栏/侧边栏分流)
├── useBaseDetailPageHistory.ts             31 行 (活动历史/记录ID解析)
├── detail/
│   ├── DetailHeader.vue                   头部组件
│   ├── DetailSectionRenderer.vue          245 行 (Section 渲染 + ErrorBoundary)
│   ├── DetailRelatedManager.vue           127 行 (关联对象分组渲染)
│   └── BaseDetailPage.scss               12KB (样式独立)
```

**审计结论**: 拆解质量优秀，职责划分清晰。`DetailSectionRenderer.vue` 已内置 `ErrorBoundary` 组件实现了 Section 级错误降级，与原 PRD 4.4 提出的"Error Boundary 注入"目标部分吻合。现有测试文件 `BaseDetailPage.contract.spec.ts` 和 `BaseDetailPage.relationGroups.spec.ts` 继续有效。

### 2.4 后端 Service 层 — 职责边界待梳理

| Service 文件 | 大小 | 核心职责 |
|-------------|------|---------|
| `business_object_service.py` | 29KB / 734行 | 对象查询 + 字段元数据 + Django Model 映射 + 显示名硬编码 |
| `object_registry.py` | 27KB / 607行 | 对象注册 + 字段同步 + 缓存 + ViewSet 映射 |
| `metadata_sync_service.py` | 25KB | 元数据同步全流程 |
| `config_package_service.py` | 25KB | 配置包管理 |
| `layout_generator.py` | 23KB | 布局生成与默认布局 |

**关键风险**: `business_object_service.py` 中存在 60+ 行的 `HARDCODED_OBJECT_NAMES` 字典和 80+ 行的 `CORE_HARDCODED_MODELS` 字典，这部分数据应当迁移至数据库或配置文件。

---

## 3. Sprint 0: 前置优化方案

### 3.1 ~~功能点 1: BaseDetailPage Composable 化拆解~~ ✅ 已完成

> **状态: 已完成** — 无需 Sprint 0 额外工作

| 原目标 | 实际结果 |
|--------|---------|
| 主组件 < 500 行 | **721 行**（含 ~430 行模板/骨架屏，脚本部分已精简至 ~110 行） |
| 测试兼容 | `contract.spec.ts` + `relationGroups.spec.ts` 继续可用 |
| DynamicDetailPage 无影响 | ✅ 正常调用 composables |
| Designer 预览无回归 | ✅ 仍通过 slot 渲染 |

**遗留优化建议** (可选，不阻塞后续 Sprint):
- `BaseDetailPage.vue` 的模板区仍有 ~430 行骨架屏 HTML，未来可抽为 `DetailSkeleton.vue` 子组件进一步瘦身
- `useBaseDetailPageFields.ts` (244 行) 中的 `resolveFromObjectPath` 和 `resolveValue` 可考虑迁至 `@/utils/` 作为通用工具

### 3.2 功能点 2: 路由与菜单注册表打通

**目标**: 将已存在的 `MenuRegistryManager` 接入实际导航流，并开始清退 Legacy 路由。

**Phase A (Sprint 0)**:
1. 在应用启动时调用 `MenuRegistryManager.generateMenuTree()` 生成菜单数据
2. Sidebar 组件消费 `RegistryMenuCategory[]` 数据渲染导航
3. Legacy 路由保留为 **redirect fallback**（`redirect: to => ...`）
4. 新增 `dynamicRouteLoader.ts` 工具函数，基于 `MenuRegistryManager` 输出调用 `router.addRoute()`

**Phase B (Sprint 2 后)**:
1. 逐步删除 `ADDITIONAL_BUSINESS_OBJECT_ROUTES`, `LEGACY_OBJECT_LIST_CREATE_ROUTES`, `LEGACY_OBJECT_LIST_ONLY_ROUTES` 中的条目
2. 最终 `router/index.ts` 仅保留：认证路由、Dashboard、动态 `objects/:code/` 通配路由、系统管理路由

**验收标准**:
- [ ] Sidebar 导航由 `MenuRegistryManager` 动态生成
- [ ] 所有旧 URL 通过 redirect 仍可访问（无断链）
- [ ] `menuRegistry.test.ts` 扩展覆盖新增逻辑

### 3.3 功能点 3: 性能基线建立

**目标**: 建立可量化的前端性能指标，为后续 Sprint 的 SWR 缓存和骨架屏提供 Before/After 对比数据。

**实施方案**:

#### 3.3.1 核心指标定义

| 指标 | 采集手段 | 目标值 (Sprint 2) |
|------|---------|------------------|
| 详情页 TTI (Time to Interactive) | Lighthouse / Performance API | < 1500ms |
| 列表页 FCP (First Contentful Paint) | Lighthouse | < 800ms |
| Metadata API P95 延迟 | Django Middleware + 日志 | < 200ms |
| 设计器画布首次渲染 | Performance.mark/measure | < 2000ms |
| 字典选项 API 并发数 (单页最大) | Network 面板审计 | < 5 (引入缓存后) |

#### 3.3.2 实施步骤
1. 创建 `scripts/performance-baseline.ts` 脚本，使用 Playwright 自动化测量核心页面的 LCP/FCP/TTI
2. 在 `backend/` 中增加性能日志中间件，记录 API 响应时间的 P50/P95/P99
3. 将基线指标记录到 `docs/performance-baseline.md`
4. CI 管道中增加性能回归检测（可选）

### 3.4 功能点 4: 渐进式 i18n 纪律

**目标**: 阻止新增硬编码文案，为 Sprint 4 的存量清洗减轻负担。

**实施方案**:
1. **ESLint 规则**: 添加 `eslint-plugin-vue-i18n` 或自定义规则，检测 `<template>` 中的中文字面量
2. **CI 门禁**: 新增/修改的文件若引入新的硬编码中文字符串，CI 报 Warning（首期不阻断）
3. **开发约定**: 所有新增的 UI 组件必须使用 `t()` 函数，新增翻译键写入对应的 locale JSON

**验收标准**:
- [ ] ESLint 规则可对 `.vue` 文件中的硬编码中文发出警告
- [ ] 项目文档中增加 i18n 开发规范说明
- [ ] 现有代码的硬编码扫描报告生成（不修复，仅统计）

### 3.5 功能点 5: 后端 Service 硬编码数据外置

**目标**: 将 `business_object_service.py` 中的 `HARDCODED_OBJECT_NAMES` (60+ 行) 和 `CORE_HARDCODED_MODELS` (80+ 行) 提取到配置。

**实施方案**:
1. 创建 `backend/apps/system/config/object_definitions.py` 集中管理所有标准对象定义
2. `HARDCODED_OBJECT_NAMES` 迁移为从 `BusinessObject` 数据库记录中读取 `name`/`name_en` 字段，以数据库记录为准（fallback 到配置文件）
3. `CORE_HARDCODED_MODELS` 保留为代码注册表（因为涉及 import_string 的物理路径），但迁移到独立配置模块
4. `object_registry.py` 中的 `STANDARD_OBJECT_DEFINITIONS` 与上述统一数据源合并，消除重复定义

**验收标准**:
- [ ] `business_object_service.py` 不再包含超过 10 行的硬编码字典
- [ ] 新增标准对象时只需修改一处配置
- [ ] 所有现有 API 返回结果不变

---

## 4. 功能点 6: 测试守护策略

### 4.1 现有测试资产盘点

项目 `platform/layout/` 目录拥有罕见的 **1:1 测试覆盖率**：

| 源文件 | 测试文件 |
|--------|---------|
| `renderSchema.ts` | `renderSchema.test.ts` |
| `layoutCompiler.ts` | `layoutCompiler.test.ts` |
| `detailSchemaProjector.ts` | `detailSchemaProjector.test.ts` |
| `fieldCapabilityMatrix.ts` | `fieldCapabilityMatrix.test.ts` |
| `renderSchemaProjector.ts` | `renderSchemaProjector.test.ts` |
| `runtimeLayoutResolver.ts` | `runtimeLayoutResolver.test.ts` |
| `canvasLayout.ts` | `canvasLayout.test.ts` |
| `compactLayoutFactory.ts` | `compactLayoutFactory.test.ts` |
| `unifiedDetailField.ts` | `unifiedDetailField.test.ts` |
| `unifiedDetailSections.ts` | `unifiedDetailSections.test.ts` |
| `unifiedFieldOrder.ts` | `unifiedFieldOrder.test.ts` |
| ... | *(共 20 对)* |

**此外**: `BaseDetailPage` 拥有 `contract.spec.ts` 和 `relationGroups.spec.ts`；`BaseListPage` 拥有独立 spec；`WysiwygLayoutDesigner` 拥有 `sectionSelection.spec.ts`。

### 4.2 测试策略要求

每个后续 Sprint 的 PRD 必须附带：
1. **影响分析表**: 列出该 Sprint 修改的源文件 → 受影响的测试文件
2. **新增测试清单**: 每个新增/重构的 Composable 必须伴随 `.test.ts`
3. **CI 阻断规则**: `platform/layout/*.test.ts` 和 `BaseDetailPage.*.spec.ts` 加入 CI blocking pipeline

---

## 5. 功能点 7: Feature Flag 机制

### 5.1 问题

大规模架构改造不可能一次性全量上线。新旧渲染路径需要灰度切换能力。

### 5.2 方案

**后端**: 在 Django Settings 中增加 Feature Flag 字典：

```python
# settings.py
FEATURE_FLAGS = {
    'USE_DYNAMIC_MENU': False,        # Sprint 0 Phase A → True
    'ENABLE_DUAL_MODE_LAYOUT': False,  # Sprint 2 → True
    'ENABLE_SWR_CACHE': False,         # Sprint 1 → True
    'ENABLE_ACTIVITY_TIMELINE': False,  # Sprint 3 → True
}
```

**前端**: 通过 `/api/system/feature-flags/` 端点下发，存入 Pinia store，供组件条件渲染：

```typescript
// useFeatureFlags.ts
const flags = useFeatureFlagStore()

if (flags.isEnabled('USE_DYNAMIC_MENU')) {
  // 使用 MenuRegistryManager 动态菜单
} else {
  // 使用旧的硬编码菜单
}
```

**验收标准**:
- [ ] Feature Flag 支持运行时切换（修改 Django Settings 或数据库后无需重新部署前端）
- [ ] 所有 Sprint 1-4 的新功能均通过 Feature Flag 控制

---

## 6. 与原 PRD Sprint 路线图的关系

本 PRD 插入在原路线图 **Sprint 1 之前**，作为前置条件：

```
[Sprint 0] 本文档 (前置优化)
    ├── BaseDetailPage 拆解            ← 为 Sprint 2 Tab 重组铺路
    ├── 路由 × 菜单注册表打通 Phase A  ← 为 Sprint 2 动态菜单铺路
    ├── 性能基线建立                    ← 为 Sprint 1 SWR/骨架屏提供量化对比
    ├── i18n 纪律启动                   ← 减轻 Sprint 4 存量清洗压力
    ├── 后端硬编码外置                  ← 为全栈元数据统一做准备
    ├── 测试守护策略                    ← 全程保护
    └── Feature Flag 机制              ← 全程保护
         │
[Sprint 1] 前端韧性与 SWR 缓存 (原 PRD 4.4)
[Sprint 2] 双态布局与关联优化 (原 PRD 4.1 + 4.2)
[Sprint 3] 设计器升维与 SubTable (原 PRD 4.3)
[Sprint 4] i18n 存量清洗与白标 (原 PRD 4.5)
```

---

## 7. 验证计划

### 自动化验证
- `npm run build` 零错误
- `npm run test` 全部通过 (含 platform/layout 20 个测试文件)
- 后端 `python manage.py test` 通过
- ESLint i18n 规则对新文件生效

### 手动验证
- 在开发环境中确认 Sidebar 菜单可由 `MenuRegistryManager` 动态生成
- 详情页渲染无视觉回归
- 设计器功能（拖拽、保存、预览、Undo/Redo）无回归
- Feature Flag 切换后新旧逻辑均正常
