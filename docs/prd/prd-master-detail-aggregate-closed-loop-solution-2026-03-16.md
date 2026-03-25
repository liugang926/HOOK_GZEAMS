# PRD: 主从聚合架构闭环方案

## 1. 文档信息

- 版本: `v1.0`
- 日期: `2026-03-16`
- 状态: `Draft`
- 作者: `System Architect`
- 关联文档:
  - `docs/prd/prd-master-detail-aggregate-architecture-2026-03-14.md`
  - `docs/plan/plan-master-detail-aggregate-architecture-2026-03-14.md`
  - `docs/prd/prd-lifecycle-cross-object-actions-closed-loop-2026-03-13.md`

## 2. 执行摘要

当前项目已经完成了主从聚合架构的一部分关键基座，包括:

- 平台元数据已经能区分 `root/detail/reference/log`
- `master_detail` 关系与 `detail_edit_mode` 已进入后端协议
- 一级菜单已经能自动过滤 `detail` 对象
- 布局设计器已经正式支持 `detail-region`
- 设计器已经具备 detail-region 模板、列级 preset、区块级 preset、预览 overlay、左侧 palette 分组和键盘交互

但这些能力目前仍然更接近“多块能力都已出现”，而不是“整条单据链已经闭环”。主要问题不再是“有没有 detail-region”，而是:

1. 主从聚合协议还没有成为单据运行时的唯一事实来源。
2. 主表/子表读写、权限、工作流、状态、时间线、审计还没有全部收口到统一聚合服务。
3. 动态页、专用页、设计器、对象路由仍有一部分并行模型。
4. 第一批资产操作单据还没有完成从旧入口到新聚合入口的整批切换。

本方案的目标不是继续按点优化，而是将现有成果收口为一个正式的闭环架构:

- 一个主从聚合元数据协议
- 一个统一单据运行时
- 一个统一主表/子表读写协议
- 一个统一继承引擎
- 一个统一设计器协议
- 一套明确的迁移和退役策略

## 3. 为什么不再继续零散优化

### 3.1 当前风险

如果继续沿着“发现一个点补一个点”的方式推进，会出现以下长期问题:

| 问题 | 当前表现 | 长期后果 |
| --- | --- | --- |
| 运行时事实来源分裂 | 动态页、专用页、设计器、对象页对 detail 的处理不完全一致 | 后续单据持续复制逻辑 |
| 继承规则分散 | 部分能力走页面判断，部分能力走对象协议 | 权限、流程、状态容易跑偏 |
| 迁移边界不清 | 旧入口仍保留，新入口不断增强 | 最终无法真正收口 |
| 设计器与业务页脱节 | 设计器能力越来越强，但未成为唯一布局来源 | 平台化收益无法兑现 |
| 测试边界不清 | 当前多为局部用例 | 大规模回归时容易出现跨层缺口 |

### 3.2 方案对比

| 方案 | 描述 | 结论 |
| --- | --- | --- |
| A. 继续局部优化 | 看到缺口就继续补菜单、设计器、详情页体验 | 不推荐，只会让模型更分散 |
| B. 仅隐藏明细对象 | 保持明细仍是普通对象，只从 UI 隐藏 | 只能止血，不能形成聚合边界 |
| C. 正式主从聚合闭环 | 让 `master_detail` 成为平台协议，运行时/设计器/继承/迁移全部围绕它收口 | 推荐 |

本 PRD 选择方案 C。

## 4. 当前基线评估

### 4.1 已经具备的能力

#### 平台协议层

当前平台已经有正式的主从语义字段:

- `BusinessObject.object_role`
- `BusinessObject.is_top_level_navigable`
- `BusinessObject.allow_standalone_query`
- `BusinessObject.allow_standalone_route`
- `BusinessObject.inherit_permissions`
- `BusinessObject.inherit_workflow`
- `BusinessObject.inherit_status`
- `BusinessObject.inherit_lifecycle`
- `ObjectRelationDefinition.relation_type`
- `ObjectRelationDefinition.detail_edit_mode`

这说明“主从聚合”已经不再只是概念，而是已经进入数据模型。

#### 运行时协议层

对象运行时已经能返回 aggregate 相关 payload，包含:

- `aggregate.detailRegions`
- `relationType`
- `detailEditMode`
- detail-region 的标题、多语言和工具栏配置

这说明运行时已经具备“从对象不是普通字段，而是一级区块”的能力。

#### 导航层

前端菜单已经识别:

- `isTopLevelNavigable === false`
- `objectRole === 'detail'`

detail 对象默认不会再作为一级菜单暴露。

#### 设计器层

布局设计器已经进入较成熟状态:

- `detail-region` 已成为正式 section 类型
- 可从 aggregate 关系中选择从表区块
- 支持区块模板、列模板、区块级和列级 preset
- 支持 hover/focus 临时预览
- 支持 palette 分组、默认模板、次级模板菜单
- 支持键盘交互和中英文字段

这说明设计器已经不是短板，反而已经接近平台级能力。

### 4.2 还没有闭环的部分

尽管基座已经到位，但闭环仍未形成，主要缺口有 6 类。

#### Gap 1: 还没有一个真正统一的单据运行时壳

当前 `detail-region` 已经能注入到动态页和设计器预览，但还没有真正形成“所有主从单据统一走 DocumentWorkbench”。

表现:

- 动态页仍有自动注入和兼容逻辑
- 专用单据页仍保留自己的渲染路径
- 聚合页的 header、动作、工作流、时间线、审计还未全部统一挂载

#### Gap 2: 还没有平台级统一的主表/子表读写协议

当前 detail-region 主要在布局和渲染层成熟，但“主表 + 子表一起读取、提交、回滚”的统一协议还没有成为所有单据的标准实现。

表现:

- 还没有一个正式的 `master/details/_row_state` 读写契约全面接管第一批单据
- 主从提交事务和行级状态机还没有完全平台化
- 不同单据仍可能在 service 层各自维护明细保存逻辑

#### Gap 3: 继承规则还没有收口成统一引擎

元数据里已经有 `inherit_*` 字段，但“是否可编辑、是否可提交、是否可发起流程、是否写入父时间线”还没有完全形成统一 policy service。

表现:

- 部分规则仍靠页面态判断
- 部分规则仍散在各单据 service
- 工作流、权限、状态、生命周期没有统一的决策入口

#### Gap 4: 迁移边界还不清晰

虽然 detail 已不进菜单，但旧的专用页、旧的明细入口、旧的兼容查询入口还没有系统性定义为“保留多久、何时下线、如何切换”。

#### Gap 5: 设计器协议和单据运行时协议还没有完全同构

设计器已经很强，但它还没有正式成为“单据聚合布局的唯一编辑入口”。

表现:

- 设计器配置和运行时渲染大体一致，但尚未对主从单据完全收口
- 区块模板、列模板、权限只读态和运行时 capability 还未完全以同一协议闭环

#### Gap 6: 缺少明确的 Definition of Done

到目前为止，更多是阶段性能力完成，而不是“第一批单据已完成整批迁移并切断旧入口”的产品化完成态。

## 5. 目标闭环

### 5.1 目标结论

主从聚合架构的闭环目标定义为:

1. `master_detail` 成为平台正式协议，而不是局部约定。
2. 单据类对象的 create/edit/readonly 统一走聚合运行时。
3. 主表和子表通过同一读写协议处理。
4. 子对象默认继承父对象的权限、流程、状态、生命周期和审计归集。
5. 设计器成为主从单据布局的唯一配置入口。
6. 第一批单据完成切换后，旧的明细入口不再作为主业务入口存在。

### 5.2 闭环后的系统形态

```text
Master-Detail Aggregate Platform
├─ Metadata Contract
│  ├─ object_role
│  ├─ relation_type=master_detail
│  ├─ inheritance policy
│  └─ i18n metadata
├─ Runtime Contract
│  ├─ aggregate runtime payload
│  ├─ document read model
│  ├─ document submit model
│  └─ capabilities model
├─ Aggregate Engine
│  ├─ read service
│  ├─ write service
│  ├─ inheritance policy resolver
│  └─ audit/timeline aggregator
├─ Designer Contract
│  ├─ field-section
│  ├─ detail-region
│  ├─ section presets
│  └─ column presets
└─ Migration Layer
   ├─ first batch document migration
   ├─ legacy route compatibility
   └─ deprecation plan
```

## 6. 产品范围

### 6.1 首批闭环范围

P0 范围:

- `AssetPickup / PickupItem`
- `AssetTransfer / TransferItem`
- `AssetReturn / ReturnItem`
- `AssetLoan / LoanItem`

这些对象必须完成整批切换，而不是只挑部分页面升级。

### 6.2 第二批推广范围

P1 范围:

- `PurchaseRequest / PurchaseRequestItem`
- `AssetReceipt / AssetReceiptItem`
- `Maintenance / MaintenanceTask`
- `DisposalRequest / DisposalItem`

### 6.3 不在本次闭环内的内容

- 非单据型纯主数据对象
- 非 `master_detail` 的普通 lookup 关系
- 新一代规则引擎重构
- 所有对象的一次性统一迁移

## 7. 核心方案

### 7.1 统一元数据协议

所有单据头行结构统一遵循以下协议:

#### 对象角色

- `root`: 聚合根，可独立菜单、动作、权限、工作流、状态机
- `detail`: 聚合内从对象，默认不作为一级导航入口
- `reference`: 主数据或引用对象
- `log`: 日志、快照、审计对象

#### 关系语义

- `master_detail`: 完全从属关系
- `lookup`: 普通引用关系
- `derived_query`: 只读派生关系

#### 主从默认继承

当 `relation_type=master_detail` 且目标对象 `object_role=detail` 时，平台默认启用:

1. 继承父对象权限
2. 继承父对象工作流上下文
3. 继承父对象可编辑状态
4. 继承父对象生命周期约束
5. 归集到父对象时间线和审计流
6. 不作为一级业务导航入口

### 7.2 统一运行时协议

#### 读模型

统一读模型必须包含:

- `context`
- `master`
- `details`
- `capabilities`
- `workflow`
- `timeline`
- `audit`

示意:

```json
{
  "context": {
    "objectCode": "AssetPickup",
    "recordId": "uuid",
    "pageMode": "edit"
  },
  "master": {},
  "details": {
    "pickup_items": {
      "editable": true,
      "detailEditMode": "inline_table",
      "rows": []
    }
  },
  "capabilities": {
    "canEditMaster": true,
    "canEditDetails": true,
    "canSubmit": true,
    "canApprove": false
  }
}
```

#### 写模型

统一写模型必须包含:

- `master`
- `details`
- 明细行 `_row_state`

示意:

```json
{
  "master": {},
  "details": {
    "pickup_items": {
      "rows": [
        { "_row_state": "new" },
        { "id": "1", "_row_state": "updated" },
        { "id": "2", "_row_state": "deleted" }
      ]
    }
  }
}
```

#### 能力模型

所有只读/可编辑/可审批行为统一走 capability 计算，不再由页面自行拼装。

### 7.3 统一单据运行时

引入正式的 `DocumentWorkbench` 作为单据唯一运行时壳，包含:

- `DocumentHeader`
- `MasterSections`
- `DetailRegions`
- `WorkflowPanel`
- `TimelinePanel`
- `AuditPanel`

模式统一为:

- `create`
- `edit`
- `readonly`

页面切换只改 mode，不改页面模型。

### 7.4 统一继承引擎

引入平台级 policy resolver，负责:

- `PermissionInheritanceResolver`
- `WorkflowInheritanceResolver`
- `StatusInheritanceResolver`
- `LifecycleInheritanceResolver`
- `AuditAggregationResolver`

要求:

1. 页面不再自行判断 detail 是否可编辑
2. 单据 service 不再重复实现主从继承判断
3. capability 计算必须来自统一 policy

### 7.5 统一设计器协议

设计器层正式收口到两类区块:

- `field-section`
- `detail-region`

detail-region 必须支持:

- 双语标题和 `translation_key`
- relation 选择
- 工具栏配置
- 列配置
- 列级 preset
- 区块级 preset
- 主从模板 palette
- 预览 overlay

设计器不是附属能力，而是主从单据布局的唯一配置入口。

### 7.6 统一迁移策略

迁移必须遵循:

1. 先冻结协议
2. 再构建统一运行时
3. 再迁移第一批单据
4. 再关闭旧入口

不允许边迁移边继续扩散新的旧模型入口。

## 8. I18N 约束

多语言不是后补项，必须是闭环方案的硬约束。

### 8.1 必须遵守

1. 新增用户可见文案不得直接硬编码在 Vue 组件中。
2. 新增对象、关系、区块、模板、列 preset 必须同时提供 `zh-CN` 和 `en-US`。
3. 运行时标题解析优先级必须是:
   - `translation_key`
   - 当前语言 metadata
   - 稳定 code
4. 设计器保存出的配置不得只保存单语标题。

### 8.2 必须覆盖的对象

- object title
- relation title
- section title
- detail-region title
- toolbar action
- preset label
- preset description

## 9. 停止做什么 / 开始做什么

### 9.1 Stop Doing

从本方案批准开始，不再新增以下模式:

1. 不再为新的 `*Item` 对象创建一级菜单入口
2. 不再为新的 `*Item` 对象创建独立审批入口
3. 不再为新的 `*Item` 对象创建独立授权模型
4. 不再为每个单据单独复制主表/子表保存逻辑
5. 不再在设计器和运行时代码中新增单语硬编码文案

### 9.2 Start Doing

1. 所有头行单据统一按 `master_detail` 建模
2. 所有头行单据统一走 `DocumentWorkbench`
3. 主从读写统一走聚合提交协议
4. 主从权限、流程、状态统一走 inheritance policy
5. 布局统一通过 `field-section + detail-region` 配置

## 10. 验收标准

### 10.1 平台层验收

1. `detail` 对象不再作为普通业务入口暴露
2. `master_detail` 关系可被运行时、设计器、菜单、能力模型共同识别
3. 统一 capability 计算可控制主表/子表可编辑性

### 10.2 单据层验收

1. 第一批 4 类资产操作单据全部迁移到统一聚合页
2. `create/edit/readonly` 三种模式均可同时处理主表和子表
3. 工作流、状态、时间线、审计都对齐到聚合根
4. 明细对象不再需要单独作为业务页来完成日常操作

### 10.3 设计器验收

1. 设计器可完整配置主表区和明细区
2. 设计器发布后的布局可直接驱动运行时
3. detail-region 模板、列模板、预览能力全部可用

### 10.4 交付层验收

1. 第一批单据完成整批切换
2. 旧入口有明确兼容窗口和退役计划
3. 自动化测试覆盖主链路

## 11. Definition of Done

当且仅当以下条件全部满足，才认为主从聚合架构完成第一阶段闭环:

1. 主从元数据协议已经冻结并成为平台事实来源
2. `DocumentWorkbench` 已成为第一批头行单据的唯一主运行时
3. 主表/子表统一读写协议已落地并跑通事务保存
4. 主从权限、工作流、状态、生命周期继承已由统一 policy 生效
5. 设计器已成为第一批头行单据布局的唯一配置入口
6. 第一批 4 类资产操作单据已经切换到新模型
7. 旧的明细业务入口已完成下线或降级为兼容只读入口
8. `zh-CN/en-US` 双语要求已在运行时和设计器全链路满足
9. 自动化测试覆盖协议层、运行时层、设计器层、E2E 主链路

## 12. 推荐决策

建议从今天起将“主从聚合闭环”作为该项目单据平台化的最高优先级，不再继续把资源投在零散体验补丁上。

推荐执行顺序:

1. 冻结闭环目标和退役边界
2. 完成统一运行时和统一继承引擎
3. 完成第一批 4 类单据整批切换
4. 用同一协议推广到采购、验收、维修、报废

这条路线的关键不是“再做一个更强的设计器”，而是让现有设计器、现有元数据、现有动态运行时最终指向同一个单据平台协议。
