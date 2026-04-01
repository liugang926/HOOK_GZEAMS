# PRD: Aggregate Document Process Summary 收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.52 |
| 作者/Agent | Codex |

## 1. 功能概述与业务场景

### 1.1 背景
Phase 7.2.51 已经将动态对象默认记录页中的流程摘要收敛到统一 `Process Summary` surface，但聚合单据工作台的 summary surface 仍然保留着多块并列结构：
- header signal banner
- workflow progress card
- stage insights card
- signal summary card
- closed-loop navigation card

这导致记录页和单据页再次出现两套展示协议，违背“Salesforce 风格记录页 / 工作台同源信息架构”的目标。

### 1.2 目标
将 aggregate document 的流程摘要能力也并入统一 `Process Summary` 协议：
- 用一个面板承接 workflow progress、stage metrics、latest signal、related navigation
- 去掉 header 中重复的 signal banner
- 让 aggregate document summary surface 与 dynamic detail record surface 使用同一组件和同一数据形状

### 1.3 适用对象
- `PurchaseRequest`
- `AssetReceipt`
- `DisposalRequest`
- `AssetPickup`
- `AssetTransfer`
- `AssetReturn`
- `AssetLoan`
- 其他已接入 aggregate document workbench 的单据对象

### 1.4 本阶段不做
- 不新增后端接口
- 不调整 aggregate document payload schema
- 不修改 batch tools、record info、workflow info 的次级卡片
- 不改 activity / timeline surface

## 2. 用户角色与权限

| 角色 | 查看单据页 | 查看流程摘要 | 查看关联导航 | 执行动作 |
|------|------------|--------------|--------------|----------|
| 资产管理员 | 是 | 是 | 是 | 是 |
| 单据经办人 | 是 | 是 | 是 | 是 |
| 审批人 | 是 | 是 | 按流程权限 | 按流程权限 |
| 普通查看用户 | 是 | 是 | 按对象权限 | 否 |

说明：
- 本阶段不新增权限点。
- `Process Summary` 仅收敛展示，不绕过原有动作和对象权限。

## 3. 公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | BaseModelSerializer | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | `apps.common.filters.base.BaseModelFilter` | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |

补充说明：
- 本阶段无后端 schema 变更，属于前端运行时汇总逻辑收敛。

## 4. 数据模型设计

### 4.1 持久化模型
本阶段无数据库 schema 变更。

### 4.2 前端运行时协议

| 字段 | 位置 | 说明 |
|------|------|------|
| `processSummaryStats` | document workbench state | 阶段指标汇总后的 stats 集合 |
| `processSummaryRows` | document workbench state | workflow progress 与 latest signal 的统一 rows |
| `navigationSection` | document workbench state | 关联单据导航 |

### 4.3 展示规则
1. aggregate document 的 `Summary` 面板优先展示统一 `Process Summary`。
2. `Process Summary` 中允许同时展示：
   - 阶段指标 stats
   - workflow progress row
   - latest signal rows
   - related navigation actions
3. header 不再重复展示 latest signal banner。
4. `Record`、`Workflow`、`Batch Tools` 保持为次级信息区块。

## 5. API 接口设计

本阶段不新增接口，继续沿用：
- `GET /api/system/objects/{code}/{id}/runtime/`
- `GET /api/aggregate-documents/{code}/{id}/`

错误码继续沿用：
- `VALIDATION_ERROR`
- `PERMISSION_DENIED`
- `NOT_FOUND`
- `SERVER_ERROR`

## 6. 前端组件设计

### 6.1 Document Workbench View Model
- 新增 `buildDocumentWorkbenchProcessSummaryStats`
- 新增 `buildDocumentWorkbenchProcessSummaryRows`
- 将 stage rows、workflow progress、latest signal 组合为统一 process summary 输入

### 6.2 useDocumentWorkbenchState
- 暴露 `processSummaryStats`
- 暴露 `processSummaryRows`
- 保持旧 `recordRows / workflowRows / auditRows` 兼容

### 6.3 DocumentWorkbench
- 复用 `ProcessSummaryPanel`
- 删除 header signal banner
- 删除 summary surface 中独立的 `workflow progress / stage insights / signal summary / navigation` 卡片
- 保留 record / workflow / batch tools 次级卡片

## 7. 测试用例

### 7.1 前端
- view model 能生成 document process summary stats
- view model 能生成 workflow progress + latest signal rows
- `DocumentWorkbench` 的 summary surface 渲染统一 `Process Summary`
- `DocumentWorkbench` 不再渲染 header signal banner

### 7.2 验收标准
- aggregate document 的流程摘要不再分散在多个卡片中
- `DocumentWorkbench` 与 detail page 的流程摘要展示协议一致
- record / workflow / batch tools 不受影响
