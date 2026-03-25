# PRD: 生命周期跨对象动作闭环

> 版本: `v1.0`  
> 日期: `2026-03-13`  
> 作者: `System Architect`  
> 状态: `待评审`

---

## 1. 背景与问题

### 1.1 背景

GZEAMS 已经具备生命周期对象的基础模型、列表页、详情页和自定义动作接口：

- `PurchaseRequest` 支持提交、审批、完成、取消
- `AssetReceipt` 支持提交检验、记录检验结果、生成资产
- `Maintenance` 支持派工、开工、完工、验收
- `DisposalRequest` 支持提交、鉴定、审批、执行、完成
- 生命周期前端页面已在 `frontend/src/views/lifecycle/` 落地

这说明项目已经不是“是否有生命周期模块”的问题，而是“是否形成跨对象业务闭环”的问题。

### 1.2 当前核心断点

现状中跨对象动作仍然是“分散的页面按钮 + 局部 service 方法”，还没有形成统一闭环：

| 断点 | 当前现状 | 业务影响 |
|------|---------|---------|
| 采购申请 → 入库 | `PurchaseRequestDetail.vue` 仅通过路由跳转到创建验收单页并传 query 参数 | 没有统一预检查、默认值编排、重复建单防呆 |
| 入库 → 资产建卡 | `AssetReceiptService.generate_asset_cards()` 仍是 stub，仅把 `asset_generated=True` | 无真实资产卡、无来源追溯、无状态日志 |
| 生命周期动作入口 | 各页面通过 `StatusActionBar` 手工配置动作 | 同类动作分散，无法在动态详情页、列表页、门户页统一复用 |
| 状态联动 | 生命周期对象状态变化与 `Asset.asset_status` 联动不统一 | 资产状态、业务单据状态、状态日志可能脱节 |
| 可追溯性 | 资产卡缺少来源对象/来源单据行的统一追溯字段 | 无法回答“这张资产卡由哪张验收单哪一行生成” |
| 生命周期时间线 | 详情页有单据自身状态，但没有“跨对象生命周期时间线” | 用户无法一屏看到采购、入库、维修、报废的完整链路 |
| 动作可用性判断 | 每个页面自己决定按钮显示条件 | 规则重复、权限难统一、后续接入动态对象页困难 |

### 1.3 典型代码证据

- `frontend/src/views/lifecycle/PurchaseRequestDetail.vue`
  - 仅在 `approved/processing` 时显示“创建验收单”
  - 通过路由 query 预填，不是后端编排动作
- `backend/apps/lifecycle/services/receipt_service.py`
  - `generate_asset_cards()` 仍为 stub
- `backend/apps/lifecycle/services/purchase_service.py`
  - `push_to_m18()` 仍为 stub
- `frontend/src/views/lifecycle/*.vue`
  - 动作通过页面内 `workflowActions` 手工声明，未沉淀为统一动作协议

---

## 2. 目标与非目标

### 2.1 目标

本 PRD 目标是建立“生命周期跨对象动作闭环”，让生命周期对象不再是孤立 CRUD，而是形成统一的动作编排、状态联动、来源追溯和可视化闭环。

### 2.2 业务目标

1. 采购申请审批通过后，可受控地发起“创建验收单”动作。
2. 验收通过后，可真实执行“生成资产卡”，并把来源链写入资产。
3. 维修和报废流程中的资产状态变化必须统一通过生命周期编排服务更新。
4. 资产详情页与生命周期单据详情页都能展示跨对象来源和下游动作。
5. 同一套动作协议既能用于专属页面，也能用于动态对象详情页、门户页和未来消息中心。

### 2.3 非目标

1. 本阶段不重做全部生命周期 UI 风格。
2. 本阶段不实现真实 M18 采购对接，仅保留对接占位和动作编排接口。
3. 本阶段不覆盖保险、租赁等非核心生命周期对象，但设计必须可扩展。
4. 本阶段不引入新的 BPM 引擎，仅对接现有 workflow/审批能力。

---

## 3. 范围

### 3.1 对象范围

本期纳入闭环的核心对象：

- `PurchaseRequest`
- `PurchaseRequestItem`
- `AssetReceipt`
- `AssetReceiptItem`
- `Asset`
- `Maintenance`
- `MaintenancePlan`
- `MaintenanceTask`
- `DisposalRequest`
- `DisposalItem`
- `AssetStatusLog`

### 3.2 闭环范围

本期闭环链路为：

```text
PurchaseRequest
  -> AssetReceipt
  -> Asset
  -> Maintenance
  -> DisposalRequest
  -> AssetStatusLog / 生命周期时间线
```

### 3.3 动作范围

本期纳入统一协议的跨对象动作：

| 动作代码 | 来源对象 | 目标对象/效果 | 说明 |
|---------|---------|--------------|------|
| `purchase.create_receipt` | `PurchaseRequest` | 创建 `AssetReceipt` 草稿 | 基于采购申请预填验收单与明细 |
| `purchase.push_m18` | `PurchaseRequest` | 触发 M18 推送编排 | 本期保留 stub，对外统一协议 |
| `receipt.generate_assets` | `AssetReceipt` | 生成 `Asset` 记录 | 真正建卡、写入来源链与状态日志 |
| `receipt.view_generated_assets` | `AssetReceipt` | 查看生成的资产集合 | 详情页和结果页统一入口 |
| `asset.create_maintenance` | `Asset` | 创建 `Maintenance` 草稿 | 预填资产、责任人、位置等上下文 |
| `asset.create_disposal` | `Asset` | 创建 `DisposalRequest` 草稿 | 预填资产与残值上下文 |
| `maintenance.complete_and_restore_asset` | `Maintenance` | 更新资产状态为可用 | 完工/验收后状态回写 |
| `disposal.execute_and_scrap_asset` | `DisposalItem/DisposalRequest` | 更新资产状态为报废/已处置 | 同步状态日志与来源链 |

---

## 4. 用户与场景

| 角色 | 关键诉求 |
|------|---------|
| 资产管理员 | 不离开当前单据即可发起下游动作，并能看到闭环进度 |
| 审批人 | 能明确一个单据审批通过后下游将触发什么业务对象 |
| 维修人员 | 完工后能自动驱动资产状态恢复，不需要手工改多处 |
| 财务/审计 | 能追溯资产卡来源、报废执行来源和全过程状态变化 |
| 普通员工 | 在“我的申请/我的资产/我的待办”看到贯通后的业务链 |

### 4.1 典型场景

#### 场景 A: 采购申请到资产入库

1. 用户提交采购申请
2. 审批通过
3. 资产管理员在采购申请详情页点击“创建验收单”
4. 系统生成带来源追溯的验收单草稿，并复制申请明细
5. 验收通过后点击“生成资产卡”
6. 系统真实创建资产卡，记录来源单据和来源明细

#### 场景 B: 资产维修闭环

1. 用户从资产详情页点击“发起维修”
2. 系统创建维修单并预填资产上下文
3. 派工、开工、完工、验收
4. 完工/验收成功后资产状态从 `maintenance` 自动恢复为 `idle` 或 `in_use`
5. 系统写入资产状态日志和生命周期时间线

#### 场景 C: 资产报废闭环

1. 资产管理员从资产详情页点击“发起报废”
2. 系统创建带资产明细的报废申请
3. 鉴定、审批、执行
4. 执行完成后资产状态变为 `scrapped`
5. 系统写入资产状态日志，并将资产与报废单形成闭环追溯

---

## 5. 产品方案

### 5.1 统一动作协议

新增“生命周期动作协议”，后端根据对象状态、权限、来源关系返回可用动作，前端负责渲染，不再在每个页面手写一套规则。

#### 5.1.1 动作响应结构

```json
{
  "actions": [
    {
      "code": "purchase.create_receipt",
      "label": "创建验收单",
      "kind": "cross_object_create",
      "targetObjectCode": "AssetReceipt",
      "targetMode": "create",
      "enabled": true,
      "confirmRequired": false,
      "prefill": {
        "purchaseRequest": "uuid",
        "purchaseRequestNo": "PR202603001"
      },
      "reason": "",
      "priority": 100
    }
  ]
}
```

#### 5.1.2 动作类别

| 类别 | 含义 |
|------|------|
| `cross_object_create` | 跨对象创建草稿 |
| `cross_object_execute` | 触发跨对象执行逻辑 |
| `cross_object_navigate` | 查看下游记录或结果 |
| `lifecycle_transition` | 生命周期状态推进 |

### 5.2 生命周期时间线

为 `Asset` 和生命周期单据引入统一的“跨对象时间线”视图，至少包含：

- 来源单据创建
- 审批通过/拒绝
- 验收提交/验收通过
- 资产生成
- 维修发起/完成/验收
- 报废发起/鉴定/执行/完成
- 状态变更日志

### 5.3 来源追溯

对 `Asset` 新增正式追溯字段：

| 字段 | 说明 |
|------|------|
| `source_object_code` | 来源对象代码，如 `AssetReceipt` |
| `source_record_id` | 来源单据 ID |
| `source_line_object_code` | 来源明细对象代码，如 `AssetReceiptItem` |
| `source_line_id` | 来源明细 ID |
| `source_action_code` | 生成动作代码，如 `receipt.generate_assets` |

这些字段用于：

1. 在资产详情页展示“来源于哪张验收单哪一行”
2. 在验收单详情页快速查看“已生成哪些资产”
3. 在时间线和报表中进行来源统计

### 5.4 状态联动规则

#### 5.4.1 生命周期对象与资产状态映射

| 业务动作 | 资产状态变更 | 备注 |
|---------|-------------|------|
| 验收生成资产 | `pending -> idle` | 新建资产初始可用 |
| 维修开始 | `in_use/idle -> maintenance` | 开工时更新 |
| 维修验收通过 | `maintenance -> idle/in_use` | 按原状态或策略恢复 |
| 报废执行完成 | `maintenance/idle/lost -> scrapped` | 统一服务处理 |

#### 5.4.2 状态更新原则

1. 所有生命周期驱动的资产状态变化必须通过统一生命周期编排服务触发。
2. 状态变化必须同时写入 `AssetStatusLog`。
3. 状态变化必须具备来源上下文：来源对象、来源记录、动作代码、操作者。

### 5.5 前端入口策略

统一动作入口出现于以下位置：

1. 生命周期专属详情页头部
2. 动态对象详情页头部
3. 资产详情页头部
4. Portal “我的资产/我的申请”
5. 后续可扩展到通知卡片和待办中心

---

## 6. 架构设计

### 6.1 后端设计

#### 6.1.1 新增服务

| 服务 | 责任 |
|------|------|
| `LifecycleActionRegistryService` | 计算对象当前可用动作 |
| `LifecycleOrchestratorService` | 统一执行业务动作编排 |
| `AssetLifecycleStateService` | 生命周期驱动的资产状态更新、状态日志、来源追溯 |
| `LifecycleTimelineService` | 聚合跨对象时间线 |

#### 6.1.2 编排边界

现有 `purchase_service.py`、`receipt_service.py`、`maintenance_service.py`、`disposal_service.py` 保留对象内业务规则；跨对象联动统一收敛到 `LifecycleOrchestratorService`。

#### 6.1.3 关键设计原则

1. 对象内状态转换继续保留在原 service。
2. 跨对象创建/执行必须通过 Orchestrator。
3. 页面不直接拼 query 造下游单据，必须调用动作预填接口。
4. 所有动作必须返回统一动作结果结构。

### 6.2 前端设计

#### 6.2.1 新增抽象

| 组件/模块 | 责任 |
|----------|------|
| `useObjectActions()` | 获取并缓存对象动作 |
| `ObjectActionBar.vue` | 统一渲染跨对象动作 |
| `useLifecycleTimeline()` | 获取时间线数据 |
| `LifecycleTimelinePanel.vue` | 渲染跨对象时间线 |

#### 6.2.2 页面改造点

- `PurchaseRequestDetail.vue`
- `AssetReceiptDetail.vue`
- `MaintenanceDetail.vue`
- `DisposalRequestDetail.vue`
- 动态详情页控制器
- 资产详情页
- 门户页

目标是让这些页面从“手工 action 列表”切到“统一动作协议驱动”。

---

## 7. API 设计

### 7.1 动作查询 API

`GET /api/system/objects/{code}/{id}/actions/`

用途：

- 返回当前对象所有可用动作
- 根据对象状态、权限、关联关系、重复建单风险动态裁剪

### 7.2 动作执行 API

`POST /api/system/objects/{code}/{id}/actions/{action_code}/execute/`

用途：

- 执行跨对象创建/执行动作
- 返回目标对象信息、跳转信息、结果摘要

#### 7.2.1 示例响应

```json
{
  "message": "验收单草稿已创建",
  "data": {
    "targetObjectCode": "AssetReceipt",
    "targetRecordId": "uuid",
    "targetUrl": "/objects/AssetReceipt/uuid?action=edit",
    "created": true
  }
}
```

### 7.3 时间线 API

`GET /api/system/objects/{code}/{id}/timeline/`

返回聚合时间线，至少包含：

- eventCode
- eventName
- eventTime
- actor
- sourceObjectCode
- sourceRecordId
- sourceUrl
- summary

### 7.4 预填草稿策略

对于跨对象创建类动作，执行后端必须负责：

1. 建立目标对象草稿
2. 复制必要的主表字段
3. 复制必要的明细行
4. 建立来源追溯字段
5. 返回目标对象跳转地址

---

## 8. 权限与规则

### 8.1 权限规则

| 动作 | 最低角色建议 |
|------|-------------|
| 创建验收单 | 资产管理员 |
| 推送 M18 | 资产管理员 / 集成管理员 |
| 生成资产卡 | 资产管理员 |
| 发起维修 | 资产管理员 / 资产责任人 |
| 发起报废 | 资产管理员 |
| 报废执行 | 资产管理员 / 财务 |

### 8.2 防呆规则

1. 同一采购申请仅允许创建有限数量的有效验收单，避免无限重复建单。
2. 已生成资产的验收明细不可重复生成同一批资产。
3. 已报废资产不可再次发起维修。
4. 已完成报废执行的资产不可再次发起报废。
5. 动作不可用时，API 必须返回 `enabled=false` 和明确原因。

---

## 9. 非功能需求

1. 动作查询接口响应时间目标 `<300ms`
2. 时间线接口默认返回最近 50 条记录
3. 动作执行必须是事务性的
4. 所有跨对象动作必须写审计日志
5. 所有来源追溯字段必须支持索引查询

---

## 10. 验收标准

### 10.1 功能验收

| 编号 | 验收标准 |
|------|---------|
| AC-1 | 采购申请审批通过后，可通过统一动作接口创建预填的验收单草稿 |
| AC-2 | 验收单执行“生成资产卡”后，真实生成资产记录，而非仅标记 `asset_generated=True` |
| AC-3 | 新生成资产必须带来源追溯字段，能反查到来源验收单和来源明细 |
| AC-4 | 从资产详情页可发起维修单和报废申请，且系统自动预填资产上下文 |
| AC-5 | 维修开始和完成必须驱动资产状态变化并写入 `AssetStatusLog` |
| AC-6 | 报废执行完成必须驱动资产状态变为 `scrapped` 并写入 `AssetStatusLog` |
| AC-7 | 生命周期专属详情页和动态详情页都能展示统一动作栏 |
| AC-8 | 资产详情页和生命周期单据详情页都能展示跨对象时间线或来源信息 |

### 10.2 工程验收

| 编号 | 验收标准 |
|------|---------|
| TEC-1 | 新增后端单测覆盖动作可用性、动作执行、状态联动、来源追溯 |
| TEC-2 | 新增前端单测覆盖统一动作栏渲染与跳转策略 |
| TEC-3 | 新增 E2E 覆盖“采购申请 -> 验收单 -> 资产生成 -> 维修 -> 报废”主链 |
| TEC-4 | 不再在生命周期详情页内写死各页面自己的动作显示规则 |

---

## 11. 风险与缓解

| 风险 | 说明 | 缓解 |
|------|------|------|
| 历史页面已手工接动作 | 改造范围分散 | 先引入统一动作栏，逐页替换 |
| 资产状态字典规则复杂 | 生命周期与资产操作域可能冲突 | 状态变更全部收敛到 `AssetLifecycleStateService` |
| 真实建卡会触发更多约束 | 编码、分类、部门、保管人等字段可能不全 | 先定义生成策略与缺省规则，再落校验 |
| M18 仍为 stub | 无法完成外部闭环 | 本期只统一动作协议和内部状态流转 |

---

## 12. 里程碑建议

1. M1: 统一动作协议与动作栏接入
2. M2: 采购申请 -> 验收单 跨对象创建闭环
3. M3: 验收单 -> 资产建卡 真实落地
4. M4: 资产 -> 维修 / 报废 发起闭环
5. M5: 生命周期时间线与主链 E2E 回归

---

## 13. 关联文档

- `docs/plans/phase1_7_asset_lifecycle/overview.md`
- `docs/prd/prd-object-association-optimization-2026-03-10.md`
- `docs/prd/prd-document-subtable-line-items-2026-03-11.md`

