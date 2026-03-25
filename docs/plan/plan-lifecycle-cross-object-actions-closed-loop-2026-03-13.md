# 生命周期跨对象动作闭环实施计划（执行版）

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-lifecycle-cross-object-actions-closed-loop-2026-03-13.md`
- 计划版本: `v1.0`
- 日期: `2026-03-13`
- 迭代策略: `5 个阶段，先统一动作协议，再补真实建卡与状态闭环`

## 2. 实施原则

1. 统一动作协议先行，避免继续在页面层复制状态判断。
2. 先打通主链路：采购申请 -> 验收单 -> 资产 -> 维修/报废。
3. 所有跨对象动作必须由后端编排，前端只负责展示和跳转。
4. 每个阶段必须附带单测或 E2E，不接受“只有按钮没有闭环”。

## 3. 分阶段执行

### Phase 1: 动作协议与基础编排（预计 4 个工作日）

#### 3.1 目标

建立统一动作查询和执行协议，让生命周期页面、动态详情页、资产详情页可以复用。

#### 3.2 任务拆解

1. 新增后端动作注册服务：
   - `backend/apps/lifecycle/services/lifecycle_action_registry_service.py`
   - `backend/apps/lifecycle/services/lifecycle_orchestrator_service.py`
2. 在对象路由或生命周期域新增动作查询/执行接口：
   - `GET /api/system/objects/{code}/{id}/actions/`
   - `POST /api/system/objects/{code}/{id}/actions/{action_code}/execute/`
3. 第一批支持动作：
   - `purchase.create_receipt`
   - `receipt.generate_assets`
   - `asset.create_maintenance`
   - `asset.create_disposal`
4. 统一动作 DTO 与错误码。
5. 为动作可用性增加权限与状态判断。

#### 3.3 交付件

1. 动作注册服务与编排服务。
2. 动作查询/执行 API。
3. 动作 DTO 契约文档与后端单测。

#### 3.4 验收

1. 任意生命周期详情页可通过统一 API 获取动作列表。
2. 不可用动作返回明确原因。
3. 页面层不再手工维护第一批跨对象动作是否显示。

---

### Phase 2: 采购申请 -> 验收单 草稿编排闭环（预计 3 个工作日）

#### 3.5 目标

把“创建验收单”从前端路由跳转改成后端统一编排。

#### 3.6 任务拆解

1. 实现 `purchase.create_receipt`：
   - 检查采购申请状态是否允许创建
   - 创建 `AssetReceipt` 草稿
   - 复制主表关键字段
   - 复制 `PurchaseRequestItem` 到 `AssetReceiptItem`
   - 写入来源追溯信息到验收单 `custom_fields` 或正式字段
2. 前端改造：
   - `PurchaseRequestDetail.vue` 改用统一动作栏
   - 创建成功后跳转至新建的验收单详情/编辑页
3. 增加重复建单防呆与消息提示。

#### 3.7 交付件

1. 采购到验收的编排实现。
2. 采购申请详情页动作改造。
3. 后端/前端测试。

#### 3.8 验收

1. 采购申请审批通过后可一键创建验收单草稿。
2. 验收单草稿明细与采购申请明细一致。
3. 不再依赖路由 query 做核心预填。

---

### Phase 3: 验收单 -> 资产建卡真实落地（预计 5 个工作日）

#### 3.9 目标

替换 `AssetReceiptService.generate_asset_cards()` 的 stub，实现真实建卡与来源追溯。

#### 3.10 任务拆解

1. 给 `Asset` 增加来源追溯字段：
   - `source_object_code`
   - `source_record_id`
   - `source_line_object_code`
   - `source_line_id`
   - `source_action_code`
2. 实现真实建卡逻辑：
   - 根据 `qualified_quantity` 批量创建资产
   - 衍生资产编码生成策略
   - 自动填充分类、采购信息、来源信息
3. 在建卡完成时统一写入：
   - 资产初始状态
   - `AssetStatusLog`
   - 验收明细生成标记
4. 增加查看生成资产结果页或快捷跳转。

#### 3.11 交付件

1. `receipt.generate_assets` 真实实现。
2. 资产来源追溯字段与迁移。
3. 验收详情页查看生成资产入口。

#### 3.12 验收

1. 验收通过后能真实生成资产卡。
2. 资产详情页可反查来源验收单与明细。
3. 重复执行不会重复生成同一批资产。

---

### Phase 4: 资产 -> 维修 / 报废 发起闭环与状态回写（预计 5 个工作日）

#### 3.13 目标

将资产作为生命周期动作入口，并统一回写状态。

#### 3.14 任务拆解

1. 实现 `asset.create_maintenance`
   - 从资产详情创建维修单草稿
   - 预填资产、位置、责任人、优先级上下文
2. 实现 `asset.create_disposal`
   - 从资产详情创建报废申请草稿
   - 自动生成 `DisposalItem`
3. 新增 `AssetLifecycleStateService`
   - 维修开工时更新资产为 `maintenance`
   - 维修验收通过时恢复资产状态
   - 报废执行完成时更新资产为 `scrapped`
   - 所有变更统一写 `AssetStatusLog`
4. 前端改造：
   - 资产详情页接入统一动作栏
   - 生命周期详情页移除对应的页面级硬编码动作

#### 3.15 交付件

1. 资产发起维修/报废闭环。
2. 生命周期状态回写服务。
3. 资产详情页与生命周期详情页动作统一。

#### 3.16 验收

1. 从资产详情页可直接发起维修/报废草稿。
2. 维修和报废过程能驱动资产状态变化。
3. `AssetStatusLog` 具备来源动作上下文。

---

### Phase 5: 生命周期时间线、门户接入与回归（预计 4 个工作日）

#### 3.17 目标

把闭环结果真正展示出来，并用自动化测试守住主链。

#### 3.18 任务拆解

1. 新增时间线聚合服务：
   - `LifecycleTimelineService`
2. 新增时间线接口：
   - `GET /api/system/objects/{code}/{id}/timeline/`
3. 前端新增：
   - `LifecycleTimelinePanel.vue`
   - `useObjectActions.ts`
   - `ObjectActionBar.vue`
4. 接入页面：
   - 生命周期详情页
   - 动态详情页
   - 资产详情页
   - `UserPortal.vue` 的“我的申请/我的资产”
5. 自动化测试：
   - 后端集成测试
   - 前端组件测试
   - E2E 主链路测试

#### 3.19 验收

1. 生命周期主链可通过时间线查看全过程。
2. 门户页可见下游动作或下游结果链接。
3. 主链路 E2E 测试稳定通过。

## 4. 代码级任务清单

### 后端

1. `backend/apps/lifecycle/services/purchase_service.py`
   - 收口跨对象动作到 Orchestrator 调用点
2. `backend/apps/lifecycle/services/receipt_service.py`
   - 替换真实建卡逻辑
3. `backend/apps/lifecycle/services/maintenance_service.py`
   - 接入资产状态回写
4. `backend/apps/lifecycle/services/disposal_service.py`
   - 接入报废执行后的资产状态回写
5. `backend/apps/lifecycle/services/`
   - 新增动作注册、编排、时间线服务
6. `backend/apps/system/viewsets/object_router.py` 或生命周期 viewset
   - 新增动作/时间线接口
7. `backend/apps/assets/models.py`
   - 增加来源追溯字段
8. `backend/apps/assets/services/asset_service.py`
   - 与生命周期状态服务对齐

### 前端

1. `frontend/src/views/lifecycle/PurchaseRequestDetail.vue`
2. `frontend/src/views/lifecycle/AssetReceiptDetail.vue`
3. `frontend/src/views/lifecycle/MaintenanceDetail.vue`
4. `frontend/src/views/lifecycle/DisposalRequestDetail.vue`
5. `frontend/src/views/assets/AssetDetail.vue`
6. `frontend/src/views/dynamic/useDynamicDetailController.ts`
7. `frontend/src/views/portal/UserPortal.vue`
8. `frontend/src/components/common/`
   - 新增 `ObjectActionBar.vue`
   - 新增 `LifecycleTimelinePanel.vue`
9. `frontend/src/composables/`
   - 新增 `useObjectActions.ts`
   - 新增 `useLifecycleTimeline.ts`
10. `frontend/src/api/`
   - 补动作与时间线 API 客户端

## 5. 测试计划

### 5.1 后端单测

1. 动作可用性判断
2. 采购申请创建验收单草稿
3. 验收单真实建卡
4. 资产状态回写与状态日志写入
5. 报废执行完成联动
6. 时间线聚合正确性

### 5.2 前端单测

1. `ObjectActionBar` 动作排序、禁用原因、执行跳转
2. `LifecycleTimelinePanel` 数据渲染
3. 动态详情页动作接入

### 5.3 E2E

1. `PurchaseRequest -> AssetReceipt`
2. `AssetReceipt -> Asset`
3. `Asset -> Maintenance -> AssetStatusLog`
4. `Asset -> DisposalRequest -> scrapped`
5. 门户页查看我的申请与我的资产链路

## 6. 风险控制

1. 每个阶段结束后执行一次对象状态矩阵对账。
2. 所有跨对象动作必须在 PR 中附测试。
3. 动作协议发布前，先保留旧页面逻辑作为短期 fallback；单页切换后再清理。
4. 真正切换到统一动作栏前，先在生命周期详情页灰度接入。

## 7. 完成定义（Definition of Done）

1. 生命周期主链路跨对象动作统一通过后端动作协议暴露。
2. 验收建卡从 stub 升级为真实建卡。
3. 维修和报废状态能够统一回写资产状态和状态日志。
4. 生命周期详情页、资产详情页、动态详情页动作入口一致。
5. 生命周期主链路自动化测试通过。

