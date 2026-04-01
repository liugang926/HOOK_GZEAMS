# PRD: Process Summary Surface 收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.51 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
Phase 7.2.48 至 Phase 7.2.50 已经把对象页拆成 `record / workspace` 两种模式，并通过 `surfacePriority` 约束默认记录页只保留 `primary / context` 信息层。

但当前记录页内部仍存在三个并行的流程摘要 surface：
- hero stats
- closure summary
- closed-loop navigation

这会继续造成两个问题：
- 同一条状态、阶段、blocker、跳转信息被分散在多个卡片里，用户需要反复扫视页面。
- 记录页虽然减载了，但流程信息仍没有形成单一主面，和 Salesforce 式“记录页主摘要 + 分页内容”还有偏差。

### 1.2 目标
新增统一 `Process Summary` surface，承接默认记录页中的流程摘要信息：
- 用一个面板统一显示阶段、owner、completion、blocker、最近原因信号和闭环导航。
- 将 hero 的流程型 stats 下沉到 `Process Summary`，只保留必要的记录头部信息。
- 默认记录页不再同时并列 `ClosureStatusPanel` 和 `ClosedLoopNavigationCard`。

### 1.3 适用对象
- 资产主对象：`Asset`
- 资产项目：`AssetProject`
- 生命周期与操作单据：`PurchaseRequest`、`AssetReceipt`、`Maintenance`、`DisposalRequest`、`AssetPickup`、`AssetTransfer`、`AssetReturn`、`AssetLoan`
- 其他已接入 detail navigation / closure summary 的动态对象

### 1.4 本阶段不做
- 不修改后端数据模型
- 不调整对象动作协议
- 不改 aggregate document 的 header / summary cards
- 不新增后台元数据配置 UI

## 2. 用户角色与权限

| 角色 | 查看记录页 | 查看流程摘要 | 查看关联导航 | 执行动作 |
|------|------------|--------------|--------------|----------|
| 资产管理员 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 是 | 是 |
| 审批人 | 是 | 是 | 按流程权限 | 按流程权限 |
| 普通查看用户 | 是 | 是 | 按对象权限 | 否 |

说明：
- 本阶段不新增权限点。
- `Process Summary` 仅整合既有可见信息，不绕开对象或动作权限。

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段无后端 schema 变更，属于详情页 runtime surface 收敛。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库 schema 变更。

### 4.2 前端运行时协议

| 字段 | 位置 | 说明 |
|------|------|------|
| `detailHeroStats` | detail workspace view model | 记录头部轻量 stat 集合 |
| `processSummaryStats` | detail workspace view model | 流程摘要 stat 集合 |
| `closureRows` | detail workspace view model | 统一 closure / signal 行数据 |
| `navigationSection` | detail workspace view model | 流程导航 section |

### 4.3 展示规则
1. 默认记录页的流程摘要统一进入 `Process Summary` 面板。
2. hero 不再承担流程型 stats 的主展示职责。
3. 只要对象存在流程 stats、closure rows 或 navigation items，就显示 `Process Summary`。
4. `Process Summary` 可以同时承载 blocker 提示和跳转动作。

## 5. API 接口设计

本阶段不新增接口，不修改动态对象路由。

沿用既有接口：
- `GET /api/objects/{code}/{id}/`
- `GET /api/system/objects/{code}/{id}/runtime/`

错误码继续沿用：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 ProcessSummaryPanel
- 新增统一面板组件。
- 负责渲染 stats、closure rows、navigation items、blocker tips。
- 导航按钮继续通过事件向上抛出，复用 detail page 既有跳转逻辑。

### 6.2 Dynamic Detail Workspace
- 将旧 `heroStats` 拆成 `detailHeroStats` 与 `processSummaryStats`。
- `detailHeroStats` 仅保留头部必要信息。
- `processSummaryStats` 承担流程型状态摘要。

### 6.3 DynamicDetailPage
- 用 `ProcessSummaryPanel` 替换 `ClosureStatusPanel + ClosedLoopNavigationCard` 的并列布局。
- 记录页存在流程摘要时优先渲染统一 process surface。
- 保持 activity hash 导航和 detail navigation 事件处理兼容。

### 6.4 国际化
- 在 `common.json` 中补齐 `processSummary` 相关标题、眉标和提示语。

## 7. 测试用例

### 7.1 前端
- `ProcessSummaryPanel` 同时渲染 stats、closure rows、navigation actions
- `ProcessSummaryPanel` 在无内容时隐藏
- `useDynamicDetailWorkspace` 将 hero stats 与 process summary stats 正确拆分
- `DynamicDetailPage` 在记录页中渲染统一 process summary surface，并继续支持 detail navigation

### 7.2 验收标准
- 默认记录页不再并列出现 closure card 和 closed-loop navigation card
- 记录头部明显减载
- 流程摘要、最近原因信号和关联导航可以在一个 surface 中完成浏览与跳转
