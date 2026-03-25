# GZEAMS 业务工作区收敛 Phase 1 PRD

## 文档信息
| 字段 | 说明 |
|------|------|
| 功能名称 | 业务工作区收敛 Phase 1 |
| 功能代码 | `business_workspace_convergence_phase1` |
| 文档版本 | 1.0.0 |
| 创建日期 | 2026-03-20 |
| 维护人 | Codex |
| 审核状态 | 草稿 |

## 1. 功能概述与业务场景

### 1.1 业务背景

GZEAMS 当前已经具备成熟的动态对象工作区能力：

1. 后端已提供 `/api/system/objects/{code}/` 统一对象入口。
2. 前端已具备 `DynamicListPage`、`DynamicFormPage`、`DynamicDetailPage`。
3. 财务、保险、租赁等域仍保留一批专页模式，形成“统一工作区 + 专属页面”混合架构。
4. 文档约束要求存在 `BaseFormPage`，但当前代码库尚未真正落地该基座组件。

### 1.2 当前痛点

| 现状 | 问题 | 影响 |
|------|------|------|
| 动态工作区已可支撑多数业务对象 | 剩余专页仍单独维护交互与状态 | 新模块开发成本高、体验不一致 |
| `BaseDetailPage` 已存在 | `BaseFormPage` 缺失 | 表单交互标准无法统一 |
| 财务已有异步推送、日志、重试能力 | 前端仍以专页承载，未融入统一对象工作区 | 后续保险、租赁复制风险高 |
| legacy route alias 仍然较多 | 无法清晰区分“过渡入口”和“正式入口” | 路由、菜单、测试复杂度增加 |

### 1.3 目标

本阶段目标不是再新增一个大业务域，而是完成平台收敛：

1. 补齐前端 `BaseFormPage` 基座。
2. 为动态对象工作区补充“扩展面板/扩展动作/异步状态指示”运行时契约。
3. 以 `FinanceVoucher` 作为试点，将财务对象优先纳入统一工作区。
4. 明确 legacy route alias 的治理策略，为保险、租赁等后续迁移铺路。

### 1.4 本次实现范围

#### 1.4.1 范围内

1. `BaseFormPage` 组件与表单标准行为落地。
2. 动态对象 runtime 响应扩展 `workbench` 配置。
3. 动态详情页支持扩展面板与异步任务状态区。
4. 财务凭证对象首批迁移到统一工作区。
5. 路由别名治理与回归测试补齐。

#### 1.4.2 不在本期范围内

1. 真实 ERP 适配器联调。
2. 保险、租赁、IT 资产全量迁移。
3. Elasticsearch 接入。
4. 新业务域建模，如资产项目或资产标签。

## 2. 用户角色与权限

| 用户角色 | 使用场景 | 核心权限 |
|---------|---------|----------|
| 系统管理员 | 配置对象工作区、维护布局与菜单 | 查看/编辑工作区配置、发布布局 |
| 财务管理员 | 查看、审批、推送财务凭证 | 查看列表/详情、执行对象动作、查看集成日志 |
| 业务管理员 | 维护对象页面结构与动作 | 管理 `BusinessObject`、`PageLayout`、动作配置 |
| 普通业务用户 | 使用统一工作区处理业务对象 | 按对象权限查看/新增/编辑/执行动作 |
| QA/测试人员 | 验证路由、工作区、动作、日志一致性 | 访问测试环境、执行回归场景 |

### 2.1 权限矩阵

| 功能 | 系统管理员 | 财务管理员 | 业务管理员 | 普通用户 |
|------|------------|------------|------------|----------|
| 查看对象工作区 runtime | ✅ | ✅ | ✅ | ✅ |
| 编辑布局 / workbench 配置 | ✅ | ❌ | ✅ | ❌ |
| 执行凭证推送 / 重试动作 | ✅ | ✅ | 视授权 | ❌ |
| 查看集成日志面板 | ✅ | ✅ | ✅ | 视对象授权 |
| 路由别名治理与发布 | ✅ | ❌ | ✅ | ❌ |

## 3. 公共模型引用声明

### 3.1 公共模型引用

| 组件类型 | 基类/能力 | 引用路径 | 自动获得功能 |
|---------|-----------|---------|-------------|
| Metadata Model | `BaseModel` + `GlobalMetadataManager` | `apps.common.models.BaseModel` / `apps.common.managers.GlobalMetadataManager` | 元数据共享、软删除、审计字段 |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、引用字段归一化 |
| CRUD ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间范围、创建人、删除状态过滤 |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 能力 |
| Framework Exception | `ObjectRouterViewSet` 扩展 | `apps.system.viewsets.object_router.ObjectRouterViewSet` | 统一对象路由、runtime、actions、relations |

### 3.2 本期适用说明

1. 本期优先复用现有 `BusinessObject`、`PageLayout`、`UserColumnPreference` 等模型，不新增独立业务表。
2. 动态对象工作区属于平台框架层，本期通过扩展 `ObjectRouterViewSet` 与 runtime 组装逻辑实现，不额外创建业务 CRUD ViewSet。
3. 财务试点对象仍通过统一对象路由提供主交互入口，保留 legacy route alias 仅用于过渡。

## 4. 数据模型设计

### 4.1 总体设计原则

1. 不新增新的顶层业务表，优先扩展现有元数据模型。
2. 工作区行为统一由 `BusinessObject` + `PageLayout.layout_config` 描述。
3. 扩展配置必须可被 runtime 接口直接消费，避免前端硬编码对象特殊判断。

### 4.2 元数据扩展点

#### 4.2.1 `BusinessObject` 扩展字段约定

通过 `menu_config` / `actions` / 运行时组装补充以下语义：

| 配置项 | 类型 | 说明 |
|------|------|------|
| `workspace_mode` | string | `standard` / `extended` |
| `legacy_aliases` | string[] | 该对象仍需兼容的旧路由路径 |
| `primary_entry_route` | string | 正式入口路由，统一为 `/objects/{code}` |
| `async_indicators` | object[] | 详情页需要轮询或状态徽标的异步任务定义 |

#### 4.2.2 `PageLayout.layout_config.workbench`

在布局配置中补充 `workbench` 节点：

```json
{
  "workbench": {
    "toolbar": {
      "primaryActions": [],
      "secondaryActions": []
    },
    "detailPanels": [
      {
        "code": "integration_logs",
        "title": "Integration Logs",
        "component": "integration-log-table",
        "dataSource": {
          "type": "panel",
          "panelCode": "integration_logs"
        }
      }
    ],
    "asyncIndicators": [
      {
        "code": "voucher_push",
        "type": "sync-task",
        "taskIdField": "latestSyncTaskId"
      }
    ]
  }
}
```

### 4.3 运行时响应模型

`GET /api/system/objects/{code}/runtime/` 返回值新增：

| 字段 | 类型 | 说明 |
|------|------|------|
| `workbench` | object | 工作区扩展配置 |
| `workbench.toolbar` | object | 工具栏动作定义 |
| `workbench.detailPanels` | array | 详情扩展面板定义 |
| `workbench.asyncIndicators` | array | 异步任务指示器定义 |
| `workbench.legacyAliases` | array | 旧路由别名信息 |

## 5. API 接口设计

### 5.1 统一原则

1. 所有对象主 CRUD 仍统一走 `/api/system/objects/{code}/`。
2. 工作区扩展信息从 runtime 获取，不再让前端页面自行散落定义。
3. 面板数据必须遵循统一响应格式。

### 5.2 运行时接口

#### 5.2.1 获取对象工作区运行时配置

```http
GET /api/system/objects/{code}/runtime/?mode=list
GET /api/system/objects/{code}/runtime/?mode=readonly
GET /api/system/objects/{code}/runtime/?mode=edit
```

成功响应：

```json
{
  "success": true,
  "data": {
    "objectCode": "FinanceVoucher",
    "mode": "readonly",
    "permissions": {
      "view": true,
      "change": true
    },
    "layout": {},
    "workbench": {
      "toolbar": {},
      "detailPanels": [],
      "asyncIndicators": [],
      "legacyAliases": ["/finance/vouchers"]
    }
  }
}
```

### 5.3 面板数据接口

#### 5.3.1 获取详情扩展面板数据

```http
GET /api/system/objects/{code}/{id}/panels/{panel_code}/
```

说明：

1. 用于详情扩展面板，例如财务凭证的集成日志、同步状态、统计摘要。
2. `panel_code` 必须来自 runtime 的 `workbench.detailPanels` 配置。

成功响应：

```json
{
  "success": true,
  "data": {
    "panelCode": "integration_logs",
    "title": "Integration Logs",
    "items": []
  }
}
```

#### 5.3.2 扩展面板动作接口

```http
POST /api/system/objects/{code}/{id}/panels/{panel_code}/actions/{action_code}/
```

用途：

1. 面板内刷新、重试、重新拉取、重新生成等动作。
2. 返回格式与对象动作保持一致。

### 5.4 对象动作接口

继续复用现有对象动作：

```http
GET /api/system/objects/{code}/{id}/actions/
POST /api/system/objects/{code}/{id}/actions/{action_code}/execute/
```

本期要求：

1. FinanceVoucher 的“推送 ERP”“重试推送”统一通过对象动作暴露。
2. 动态详情页动作栏与 runtime `workbench.toolbar` 保持一致。

### 5.5 错误码

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 配置或请求参数错误 |
| `UNAUTHORIZED` | 401 | 未认证 |
| `PERMISSION_DENIED` | 403 | 无对象或面板权限 |
| `NOT_FOUND` | 404 | 对象/记录/面板不存在 |
| `CONFLICT` | 409 | 重复发布、别名冲突 |
| `SERVER_ERROR` | 500 | runtime 组装或面板数据异常 |

## 6. 前端组件设计

### 6.1 公共组件引用

| 组件类型 | 使用组件 | 引用路径 | 说明 |
|---------|---------|---------|------|
| 列表页 | `BaseListPage` | `@/components/common/BaseListPage.vue` | 统一列表骨架 |
| 表单页 | `BaseFormPage` | `@/components/common/BaseFormPage.vue` | 本期新增，统一表单行为 |
| 详情页 | `BaseDetailPage` | `@/components/common/BaseDetailPage.vue` | 统一详情骨架 |
| 动态列表页 | `DynamicListPage` | `@/views/dynamic/DynamicListPage.vue` | 统一对象列表入口 |
| 动态表单页 | `DynamicFormPage` | `@/views/dynamic/DynamicFormPage.vue` | 统一对象表单入口 |
| 动态详情页 | `DynamicDetailPage` | `@/views/dynamic/DynamicDetailPage.vue` | 统一对象详情入口 |
| 面板宿主 | `ObjectWorkbenchPanelHost` | `@/components/common/ObjectWorkbenchPanelHost.vue` | 本期新增，渲染 runtime 面板 |
| 异步状态徽标 | `SyncTaskStatusBadge` | `@/components/finance/SyncTaskStatusBadge.vue` | 财务试点复用 |

### 6.2 必用 Hooks / Composables

| Hook | 引用路径 | 用途 |
|------|---------|------|
| `useObjectWorkbench` | `@/composables/useObjectWorkbench.ts` | 解析 runtime workbench 配置 |
| `useSyncTaskPolling` | `@/composables/useSyncTaskPolling.ts` | 异步任务状态轮询 |
| `useFormPage` | `@/composables/useFormPage.ts` | 本期从 engine hooks 标准化迁移 |
| `useListPage` | `@/composables/useListPage.ts` | 统一列表交互 |

### 6.3 页面级改造要求

1. `DynamicFormPage` 使用 `BaseFormPage` 承载通用提交/取消/校验行为。
2. `DynamicDetailPage` 新增 runtime 扩展面板区，不再为 FinanceVoucher 单独维护专页逻辑。
3. 财务列表/详情 legacy 页面保留短期跳转壳，正式入口统一跳至 `/objects/FinanceVoucher`。
4. 路由元信息、菜单入口、面包屑统一以对象工作区为准。

## 7. 测试用例

### 7.1 后端测试

| 测试项 | 类型 | 说明 |
|------|------|------|
| runtime workbench 契约 | 单元测试 | 验证 `workbench` 字段结构与默认值 |
| panel 数据权限控制 | 接口测试 | 验证面板访问遵循对象权限与组织隔离 |
| FinanceVoucher 动作统一暴露 | 接口测试 | 验证推送/重试动作仍可通过统一对象动作执行 |
| legacy alias 与正式入口一致性 | 集成测试 | 验证旧入口跳转后行为一致 |

### 7.2 前端测试

| 测试项 | 类型 | 说明 |
|------|------|------|
| `BaseFormPage` 提交/取消/校验 | 单元测试 | 验证基座表单行为 |
| `DynamicDetailPage` 面板渲染 | 单元测试 | 根据 runtime 渲染 detail panels |
| `useObjectWorkbench` | 单元测试 | 解析 toolbar/panel/indicator 配置 |
| FinanceVoucher 工作区回归 | E2E | 列表、详情、动作、日志面板、重试流程 |

## 8. 实施计划

### 8.1 里程碑

| 里程碑 | 目标 | 周期 |
|------|------|------|
| M1 基座补齐 | `BaseFormPage`、`useFormPage/useListPage` 标准化、runtime workbench schema | 4-5 天 |
| M2 财务试点迁移 | FinanceVoucher 列表/详情/动作/面板纳入统一工作区 | 5-7 天 |
| M3 路由治理与回归 | legacy alias 清单治理、测试补齐、文档更新 | 3-4 天 |

### 8.2 任务拆解

#### M1 基座补齐

1. 新建 `frontend/src/components/common/BaseFormPage.vue`。
2. 将 `useFormPage`、`useListPage` 从 `components/engine/hooks/` 标准化迁移到 `composables/`。
3. 扩展 runtime assembler，输出 `workbench` 节点。
4. 定义 detail panel / async indicator 的默认空配置。

#### M2 财务试点迁移

1. 为 `FinanceVoucher` 补充 runtime workbench 配置。
2. 将集成日志、同步状态徽标改造成 detail panel。
3. 将“推送 ERP”“重试推送”统一注册为对象动作。
4. 将 `/finance/vouchers` 入口调整为 alias/redirect。

#### M3 路由治理与回归

1. 补齐 `router/index.ts` 中 alias 与正式入口映射清单。
2. 增加工作区面板回归测试。
3. 更新相关 PRD、报告与 quick reference。

### 8.3 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| runtime schema 改动影响现有动态页面 | 页面回归风险高 | 为 `workbench` 提供兼容默认值，先做财务试点 |
| legacy 页面与工作区并存一段时间 | 菜单与路由可能混乱 | 统一通过 alias registry 管理，逐批收口 |
| 财务页面存在专属交互 | 迁移难度高于普通对象 | 先支持 panel/indicator/action 三类扩展，不一次性泛化所有能力 |
| 当前环境缺依赖，验证链不完整 | 无法立即执行全量校验 | 纳入 M1 前置任务：补齐依赖安装与最小验证脚本 |

## 9. 验收标准

1. `BaseFormPage` 在代码库中正式落地，并被动态表单页复用。
2. `GET /api/system/objects/{code}/runtime/` 能稳定返回 `workbench` 配置。
3. FinanceVoucher 正式入口改为 `/objects/FinanceVoucher`，列表/详情主要交互不丢失。
4. 集成日志与同步状态不再依赖财务专页硬编码。
5. legacy route alias 有明确清单、跳转策略和回归测试。
