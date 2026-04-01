# PRD: 记录页 / 工作台模式运行时元数据收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.49 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
Phase 7.2.48 已完成对象页首轮收敛，聚合单据页拆分为 `Summary / Form / Activity`，详情页扩展区拆分为 `Process / Activity`。但当前默认展示规则仍然散落在前端组件内部，后续对象一旦继续叠加 queue、timeline、signal、recommended actions，默认详情页仍会再次膨胀。

典型问题：
- 记录页与工作台页的默认模式没有进入 runtime metadata，无法对对象分层治理。
- 详情页和聚合单据页的默认 surface 规则写死在组件内部，无法随对象类型配置。
- 后端 runtime payload 没有明确输出记录页默认模式，前端无法稳定区分“记录页优先”与“工作台优先”对象。

### 1.2 目标
在不新增数据库 schema、不新增独立路由的前提下，将页面收敛规则推进到运行时元数据层：
- 新增 `defaultPageMode` 运行时协议，支持 `record / workspace`。
- 新增 `defaultDetailSurfaceTab` 和 `defaultDocumentSurfaceTab` 运行时协议。
- 聚合单据型对象默认回到 `record` 模式，工作台作为显式切换入口。
- 保留 URL query/hash 作为高优先级覆盖规则。
- 为后续 `surfacePriority`、列表摘要列收敛和统一页面治理打基础。

### 1.3 适用对象
- 动态详情页：`/objects/{code}/{id}`
- 聚合单据对象：`PurchaseRequest`、`AssetReceipt`、`AssetPickup`、`AssetTransfer`、`AssetReturn`、`AssetLoan`、`Maintenance`、`DisposalRequest`
- 统一 runtime layout / workbench payload

### 1.4 本阶段不做
- 不新增数据库字段。
- 不变更对象动作协议。
- 不引入 `surfacePriority` 持久化配置。
- 不改列表页信息架构。

## 2. 用户角色与权限

| 角色 | 访问记录页 | 切换工作台 | 查看活动 | 编辑表单 | 查看流程摘要 |
|------|------------|------------|----------|----------|--------------|
| 资产管理员 | 是 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 是 | 是 | 是 |
| 审批人 | 是 | 是 | 是 | 否/按字段权限 | 是 |
| 普通查看用户 | 是 | 否/按对象配置 | 是 | 否 | 是 |

说明：
- 本阶段不新增权限点，继续复用对象权限、工作流动作权限和现有字段权限。
- 页面模式切换是否可见，依赖对象是否为聚合单据以及 runtime metadata 是否开放工作台能力。

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段不新增后端业务模型，复用 `object_router_runtime_actions` 生成的 runtime payload。
- 前端仍通过统一动态对象路由和 runtime layout 渲染，不新增对象专属 URL。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库模型变更。

### 4.2 运行时元数据协议

| 字段 | 作用域 | 可选值 | 说明 |
|------|--------|--------|------|
| `defaultPageMode` | `workbench` | `record` / `workspace` | 控制聚合对象默认进入记录页还是工作台 |
| `defaultDetailSurfaceTab` | `workbench` | `process` / `activity` | 控制详情页默认 surface |
| `defaultDocumentSurfaceTab` | `workbench` | `summary` / `form` / `activity` | 控制聚合单据页默认 surface |

### 4.3 优先级规则
1. URL query/hash 优先级最高：
   - `page_mode=workspace`
   - `#detail-activity`
   - `#document-workbench-timeline`
2. runtime workbench metadata 次之。
3. 组件内部兜底默认值最低：
   - `record`
   - `process`
   - `summary`

## 5. API 接口设计

本阶段不新增 API，仅扩展统一 runtime payload 字段：

| 方法 | 接口 | 变更 |
|------|------|------|
| `GET` | `/api/system/objects/{code}/{id}/runtime/` | `workbench` 新增 `default_page_mode`、`default_detail_surface_tab`、`default_document_surface_tab` |
| `GET` | `/api/system/objects/{code}/{id}/document/?mode=readonly` | 前端根据 runtime metadata 选择首屏模式，无接口格式变更 |

错误码继续沿用统一标准：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 Runtime Contract / Resolver
- `RuntimeWorkbench` 类型增加三个默认展示字段。
- runtime contract 增加枚举校验，阻止非法 metadata 落到渲染层。
- runtime resolver 同时兼容 camelCase 和 snake_case，并补兜底值。

### 6.2 DynamicDetailPage
- 聚合对象支持 `record / workspace` 模式切换。
- 默认模式来自 `runtimeWorkbench.defaultPageMode`。
- 当 query `page_mode` 存在时，覆盖 runtime 默认值。
- 记录页模式下渲染 `CommonDynamicDetailPage`，工作台模式下渲染 `DocumentWorkbench`。

### 6.3 DocumentWorkbench
- 默认 surface 优先读取 `runtimeWorkbench.defaultDocumentSurfaceTab`。
- 未配置时保持既有规则：只读模式默认 `Summary`，编辑模式默认 `Form`。

### 6.4 DynamicFormPage
- 统一将 runtime workbench 透传给 `DocumentWorkbench`，避免聚合单据页与详情页分叉。

### 6.5 国际化
新增 i18n key：
- `common.detailWorkspace.pageModes.record`
- `common.detailWorkspace.pageModes.workspace`

## 7. 测试用例

### 7.1 前端单元测试
- runtime resolver 能正确解析三个新增字段。
- runtime contract 能拒绝非法 page mode / surface tab 值。
- `DocumentWorkbench` 可按 metadata 选择默认 surface。
- `DynamicDetailPage` 在聚合对象场景下默认进入 `record` 模式。
- `page_mode=workspace` 可覆盖 runtime 默认值。

### 7.2 后端测试
- `menu_config` 为目标对象输出 `default_page_mode` / `default_surface_tab` 配置。
- `object_router_runtime_actions` 返回新增 runtime 字段，并保留默认兜底值。

### 7.3 验收标准
- 聚合单据对象默认回归记录页模式，不再默认进入重型工作台。
- 页面默认模式与默认 surface 规则不再写死在单个组件内部。
- URL query/hash 覆盖行为不回退。
- runtime contract 能在异常 metadata 下提前阻断渲染风险。
