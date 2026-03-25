# 对象关联闭环实施计划（执行版）

## 1. 计划信息
- 关联 PRD: `docs/prd/prd-object-relation-closed-loop-2026-03-05.md`
- 计划版本: `v1.1`
- 日期: `2026-03-05`
- 迭代策略: `4 个阶段，资产域 + IT资产域优先，完成后推广到全对象`

## 2. 实施原则
1. 统一关系协议先行：先建关系定义与查询引擎，再改前端。
2. 一次性去硬编码：项目未生产，不保留双轨长期兼容。
3. 先修闭环主链：资产/IT资产 <- 操作单据与运维对象 <- 生命周期状态。
4. 每阶段必须带测试与验收脚本。

## 3. 分阶段执行

### Phase 1: 关系引擎后端落地（预计 5 个工作日）

#### 3.1 任务拆解
1. 新增 `ObjectRelationDefinition` 模型与迁移。
2. 新增关系服务 `RelationQueryService`：支持 `direct_fk`、`through_line_item`、`derived_query`。
3. 新增 API：
   - `GET /system/objects/{code}/relations/`
   - `GET /system/objects/{code}/{id}/related/{relation_code}/`
4. 在启动同步流程注入默认关系定义：
   - Asset -> AssetPickup（through PickupItem）
   - Asset -> AssetTransfer（through TransferItem）
   - Asset -> AssetReturn（through ReturnItem）
   - Asset -> AssetLoan（through LoanItem）
   - Asset -> DisposalRequest（through DisposalItem）
   - Asset -> Maintenance（direct）
   - ITAsset -> Asset（direct）
   - ITAsset -> ITMaintenanceRecord（derived_query by asset_id）
   - ITAsset -> ConfigurationChange（derived_query by asset_id）
   - ITAsset -> ITLicenseAllocation（derived_query by asset_id）
5. 为 through 关联明细表补复合索引（父单据 + 资产）。

#### 3.2 交付件
1. 关系模型与迁移文件。
2. 关系 API 与单元测试。
3. 资产域 + IT资产域默认关系 seed。

#### 3.3 验收
1. 资产任意 ID 可正确返回关联单据头列表。
2. IT资产任意 ID 可正确返回维护/变更/许可证分配列表。
3. 不再依赖 `AssetPickup?asset=...` 这类错误过滤。

---

### Phase 2: 前端关系展示统一（预计 5 个工作日）

#### 3.4 任务拆解
1. 改造 `RelatedObjectTable.vue`：
   - 输入参数从 `reverseRelationField` 切换为 `relationCode`。
   - 数据请求改为 `/related/{relationCode}`。
2. 改造 `BaseDetailPage.vue` / `DynamicDetailPage.vue`：
   - 关系数据来源统一为 `relations` 元数据。
   - 移除对象特化硬编码关系推断逻辑。
3. 改造布局设计器关系卡片 schema：
   - 绑定 `relation_code`。
   - 保留并统一现有 canvas/grid 放置能力。
4. 更新 i18n 文案与关系卡片标题策略（对象名 + 计数）。

#### 3.5 交付件
1. 统一关系渲染组件。
2. 关系元数据到 UI 的单向数据流。
3. 前端单元测试（direct + through + derived_query 各 1 组以上）。

#### 3.6 验收
1. 资产详情页稳定展示领用/调拨/归还/借用/报废/维修。
2. IT资产详情页稳定展示维护/配置变更/许可证分配。
3. 设计器关系卡片与运行时显示一致。

---

### Phase 3: 生命周期状态闭环补齐（预计 5 个工作日）

#### 3.7 任务拆解
1. 实现 `AssetReceiptService.generate_asset_cards` 真实建卡。
2. 新增资产来源追溯字段与写入逻辑：
   - `source_object_code` / `source_record_id` / `source_line_id`。
3. 报废执行完成时统一更新资产状态与状态日志。
4. 抽象 `AssetLifecycleService` 管理状态变更入口。

#### 3.8 交付件
1. 入库建卡真实实现。
2. 报废状态闭环。
3. 资产状态变更服务层抽象。

#### 3.9 验收
1. 资产可追溯来源单据和明细。
2. 报废完成后资产状态必为 `scrapped` 且有状态日志。

---

### Phase 4: 全量回归与推广（预计 5 个工作日）

#### 3.10 任务拆解
1. 补齐跨模块关系定义（保险、租赁、折旧、财务等）。
2. 增加 API 集成测试与 E2E 场景：
   - 资产详情关系卡片
   - IT资产详情关系卡片
   - 通过关系卡跳转单据详情
   - 布局设计器发布后关系卡位置一致
3. 编写运维脚本：关系定义健康检查（模型字段、对象码、索引）。
4. 编写开发规范：新增对象必须声明关系定义。

#### 3.11 验收
1. 资产域 + IT资产域核心链路自动化测试通过率 100%。
2. 回归过程中无“关系数据为空但接口成功”假阳性。

## 4. 任务清单（按代码目录）

### 后端
1. `backend/apps/system/models.py`：关系定义模型。
2. `backend/apps/system/migrations/*`：新迁移。
3. `backend/apps/system/services/`：关系查询服务与注册同步。
4. `backend/apps/system/viewsets/object_router.py`：relations/related API。
5. `backend/apps/assets/services/`：生命周期状态更新汇聚。
6. `backend/apps/lifecycle/services/receipt_service.py`：建卡真实实现。
7. `backend/apps/lifecycle/services/disposal_service.py`：报废状态闭环。

### 前端
1. `frontend/src/components/common/RelatedObjectTable.vue`：关系查询协议改造。
2. `frontend/src/components/common/BaseDetailPage.vue`：关系组件接入。
3. `frontend/src/components/common/DynamicDetailPage.vue`：关系元数据映射。
4. `frontend/src/components/designer/WysiwygLayoutDesigner.vue`：关系卡 schema。
5. `frontend/src/api/system/businessObject.ts`：关系 API 客户端。

## 5. 测试计划
1. 后端单测：关系查询 direct/through/derived、空关系、非法关系码、分页与排序。
2. 后端集成：资产详情与 IT资产详情关联数据准确性。
3. 前端单测：`RelatedObjectTable` 请求协议与列渲染。
4. E2E：
   - 资产详情 -> 关系卡 -> 单据详情跳转
   - IT资产详情 -> 关系卡 -> 记录详情跳转
   - 布局设计器保存关系卡位置 -> 运行时一致
   - 入库生成资产 -> 资产追溯来源

## 6. 进度与风险控制
1. 每阶段结束执行一次“关系矩阵对账”，比对模型关系与关系定义是否一致。
2. 每次新增对象必须在 PR 中同步关系定义与测试。
3. 若出现性能瓶颈，优先对 through 中间表加索引并下推分页。

## 7. 完成定义（Definition of Done）
1. 资产域 + IT资产域关系闭环在 API 与 UI 均完成。
2. 生命周期关键流程（入库、报废）形成可追溯状态闭环。
3. 关系展示不再包含对象级硬编码反向字段假设。
