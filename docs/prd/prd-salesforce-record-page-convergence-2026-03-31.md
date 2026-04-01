# PRD: Salesforce 风格对象页收敛 Phase 1

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.48 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
当前对象详情页和聚合单据页已经承载了闭环摘要、动作、SLA、流程状态、活动时间线、推荐动作、导航和批量工具等大量能力，但默认页面的信息层级失控，偏离了 Salesforce 风格“记录页优先、流程工作台次级展开”的交互理念。

典型问题：
- 默认详情页首屏堆叠过多一级卡片，用户难以识别主信息与次信息。
- 聚合单据页把摘要、表单、活动、导航、批量工具同时摊平展示，导致页面扫描成本过高。
- 活动时间线和流程摘要与主表单并列出现，破坏记录页主路径。

### 1.2 目标
在不新增后端 schema、不新增后端 API 的前提下，完成第一阶段对象页收敛：
- 默认记录页回归“主摘要 + 分层展开”。
- 聚合单据页拆分为 `Summary / Form / Activity` 三个一级 surface。
- 详情页扩展区域拆分为 `Process / Activity` 两个一级 surface。
- 保持现有闭环能力、动作能力、原因信号能力不丢失。
- 支持 hash 直达活动区域，兼容既有信号跳转链接。

### 1.3 适用对象
- 统一动态详情页：`/objects/{code}/{id}`
- 聚合单据页：`AssetPickup`、`AssetTransfer`、`AssetReturn`、`AssetLoan`、`PurchaseRequest`、`AssetReceipt`、`DisposalRequest`

### 1.4 本阶段不做
- 不新增数据库字段。
- 不新增对象动作协议。
- 不改动闭环计算逻辑。
- 不扩展列表页摘要列。
- 不引入 metadata 持久化的 `surfacePriority/defaultPageMode` 配置项，留作后续 Phase 2。

## 2. 用户角色与权限

| 角色 | 查看记录页 | 查看流程摘要 | 执行动作 | 编辑表单 | 查看活动 |
|------|------------|--------------|----------|----------|----------|
| 资产管理员 | 是 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 按对象权限 | 是 | 是 |
| 审批人 | 是 | 是 | 按流程权限 | 否/按字段权限 | 是 |
| 普通查看用户 | 是 | 是 | 否 | 否 | 是 |

说明：
- 本阶段不新增权限点，继续复用对象元数据权限、运行时权限和工作流动作权限。
- 仅调整页面分层和默认展示顺序。

## 3. 公共模型引用声明

| 组件类型 | 基类/能力 | 引用路径 | 自动获得功能 |
|---------|-----------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段不新增后端对象模型，仅复用现有动态对象路由、聚合单据契约、闭环摘要与 SLA 摘要能力。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库表结构变更，无 Django Model 变更。

### 4.2 前端视图状态

| 状态名 | 范围 | 值 | 说明 |
|--------|------|----|------|
| `activeDetailSurfaceTab` | 动态详情页 | `process` / `activity` | 控制详情扩展区域显示 |
| `activeSurfaceTab` | 聚合单据页 | `summary` / `form` / `activity` | 控制聚合单据工作台显示 |

### 4.3 后续预留元数据字段
后续阶段建议增加如下 runtime metadata 能力，但不在本阶段落库：
- `defaultPageMode`: `record` / `workspace`
- `surfacePriority`: `primary` / `context` / `related` / `activity`
- `defaultSurfaceTab`

## 5. API 接口设计

本阶段不新增接口，仅复用既有统一接口：

| 方法 | 接口 | 用途 |
|------|------|------|
| `GET` | `/api/system/objects/{code}/{id}/` | 记录基础详情 |
| `GET` | `/api/system/objects/{code}/{id}/document/?mode=readonly` | 聚合单据统一载荷 |
| `GET` | `/api/system/objects/{code}/{id}/sla/` | 对象级 SLA 摘要 |
| `GET` | `/api/system/objects/{code}/{id}/closure/` | 对象级闭环摘要 |
| `GET` | `/api/system/objects/{code}/{id}/actions/` | 对象统一动作列表 |
| `POST` | `/api/system/objects/{code}/{id}/actions/{action_code}/execute/` | 执行动作 |

错误码继续沿用统一标准：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 DynamicDetailPage
- 保留 Hero、主详情壳层和侧边摘要。
- 将 `after-sections` 收敛为 `Process / Activity` 两个页签。
- `Process` 承载生命周期摘要、workbench summary、queue、closure、SLA、推荐动作、闭环导航和自定义 panel。
- `Activity` 承载对象级活动时间线。
- 当 URL hash 为 `#detail-activity` 时，自动切换到 `Activity` 页签。

### 6.2 DocumentWorkbench
- Header 保持动作、状态和 capability 标签。
- Summary 页签承载流程进度、阶段摘要、原因信号摘要、记录摘要、流程摘要、闭环导航、批量工具。
- Form 页签承载主表单。
- Activity 页签承载审计摘要、最近流程活动、完整活动时间线。
- 当 URL hash 为 `#document-workbench-timeline` 时，自动切换到 `Activity` 页签。
- 编辑态默认优先落在 `Form`，只读态默认优先落在 `Summary`。

### 6.3 国际化
新增 i18n key：
- `common.detailWorkspace.tabs.process`
- `common.detailWorkspace.tabs.activity`
- `common.documentWorkbench.tabs.summary`
- `common.documentWorkbench.tabs.form`
- `common.documentWorkbench.tabs.activity`

## 7. 测试用例

### 7.1 前端单元测试
- `DocumentWorkbench` 只读模式默认落在 `Summary`
- `DocumentWorkbench` 编辑模式默认落在 `Form`
- `DocumentWorkbench` 在 `#document-workbench-timeline` hash 下自动切到 `Activity`
- `DynamicDetailPage` 在 `#detail-activity` hash 下自动切到 `Activity`
- 既有动作、导航和时间线渲染不回退

### 7.2 回归验证
- locale JSON 合法性校验
- 详情页闭环导航和 related record 跳转不回退
- 聚合单据动作透传和 `action-success` 事件不回退

### 7.3 验收标准
- 默认详情页和聚合单据页不再纵向堆叠所有扩展信息
- 活动类内容从首屏主路径下沉到独立 surface
- 现有 hash 跳转仍可直达对应活动视图
- 不新增后端变更，不影响既有闭环数据结构
