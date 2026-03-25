# 主从聚合架构实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-master-detail-aggregate-architecture-2026-03-14.md`
- 版本: `v1.0`
- 日期: `2026-03-14`
- 策略: `先协议、再运行时、后设计器、最后批量迁移`

## I18N Delivery Constraints

1. Every new aggregate capability must support `zh-CN` and `en-US` from the first delivery slice.
2. New runtime components, protocol payloads, and designer schema must carry either `translation_key` or bilingual metadata fields instead of single-language literals.
3. Phase 2 `DocumentWorkbench` and `DetailRegion` contracts must include bilingual labels for headers, section titles, relation titles, and toolbar actions.
4. Phase 4 layout designer work must allow authors to configure `title`, `title_en`, and `translation_key` for `field-section` and `detail-region`.
5. Acceptance for each phase must include an i18n review to ensure no new hardcoded user-facing copy was introduced.

---

## 2. 实施原则

1. 先固定平台协议，再写业务页面。
2. 先跑通一类单据，再批量复制到其它单据。
3. 先统一主表/子表保存边界，再优化交互和设计器。
4. 所有阶段必须附带自动化测试与迁移策略。
5. 旧入口可以短期保留，但新入口必须从一开始就站在正式架构上。

---

## 3. 分阶段计划

## Phase 0: 架构定版与样板收口

### 目标

锁定主从聚合协议、对象角色、关系语义、页面模型和设计器扩展范围，避免后续反复。

### 任务

1. 评审并冻结 `root/detail/reference/log` 对象角色定义。
2. 评审并冻结 `master_detail` 关系协议与默认继承规则。
3. 明确第一批样板对象：
   - `AssetPickup/PickupItem`
   - `AssetTransfer/TransferItem`
   - `AssetReturn/ReturnItem`
   - `AssetLoan/LoanItem`
4. 明确运行时公共组件边界：
   - `DocumentWorkbench`
   - `DocumentHeader`
   - `DetailRegion`
5. 明确设计器扩展边界：
   - `field-section`
   - `detail-region`

### 交付物

1. PRD 定稿
2. 数据模型草案
3. 页面模型草案
4. 设计器扩展草案

### 验收

1. 架构评审通过
2. 对象角色、关系类型、继承规则无关键争议

建议工期: `2-3 人天`

---

## Phase 1: 元数据协议落地

### 目标

让平台正式识别“主对象”和“从对象”，不再只靠菜单隐藏和局部规则维持。

### 任务

1. 扩展后端元数据模型：
   - `BusinessObject`
   - `ObjectRelationDefinition`
2. 增加字段：
   - `object_role`
   - `is_top_level_navigable`
   - `allow_standalone_query`
   - `allow_standalone_route`
   - `inherit_permissions`
   - `inherit_workflow`
   - `inherit_status`
   - `inherit_lifecycle`
   - `relation_type`
   - `detail_edit_mode`
3. 调整硬编码对象目录与同步服务，使 `*Item` 对象同步后具有明确 `detail` 语义。
4. 补充迁移脚本，将现有 `PickupItem/TransferItem/ReturnItem/LoanItem` 标记为 `detail`。
5. 调整对象查询服务、对象列表服务、菜单服务，使 `detail` 默认不作为一级导航对象。

### 涉及代码

1. `backend/apps/system/models.py`
2. `backend/apps/system/object_catalog.py`
3. `backend/apps/system/services/hardcoded_object_sync_service.py`
4. `backend/apps/system/services/business_object_service.py`
5. `frontend/src/router/menuRegistry.ts`

### 交付物

1. 元数据迁移
2. 协议字段落地
3. 同步服务和菜单逻辑调整
4. 回归测试

### 验收

1. 四个 `*Item` 对象不再出现在一级菜单。
2. 对象接口中可识别 `object_role=detail`。
3. `master_detail` 关系元数据可被查询到。

建议工期: `4-5 人天`

---

## Phase 2: 聚合运行时基础版

### 目标

建立统一的主表/子表页面运行时和统一保存协议。

### 任务

1. 后端新增聚合保存与读取协议：
   - `master`
   - `details`
   - 行状态 `_row_state`
2. 为样板对象建立统一聚合 service：
   - 创建主对象
   - 创建/更新/删除从对象
   - 同事务提交
3. 前端新增统一运行时容器：
   - `DocumentWorkbench`
   - `DetailRegion`
   - bilingual labels via `translation_key`, `title`, `title_en`
4. 实现三种页面上下文：
   - `create`
   - `edit`
   - `readonly`
5. 打通 `AssetPickup/PickupItem` 首个样板。

### 涉及代码

1. `backend/apps/assets/services/`
2. `backend/apps/system/viewsets/object_router.py`
3. `frontend/src/views/dynamic/`
4. `frontend/src/components/common/`
5. `frontend/src/api/`

### 交付物

1. 统一提交协议
2. 聚合读取协议
3. 主从统一页面壳
4. `AssetPickup` 样板可运行

### 验收

1. 领用单新建页可同时创建主表与子表。
2. 领用单编辑页可同时更新主表与子表。
3. 领用单只读页统一展示主表与子表。
4. 保存失败时主表与子表统一回滚。

建议工期: `6-8 人天`

---

## Phase 3: 主从继承规则落地

### 目标

让从对象自动继承父对象的权限、审批、状态和生命周期，不再由页面零散判断。

### 任务

1. 权限继承：
   - 从对象默认不独立授权
   - 写操作统一校验父对象权限
2. 流程继承：
   - 从对象默认不独立发起工作流
   - 父对象工作流状态驱动子表可编辑性
3. 状态继承：
   - 父对象不可编辑时子表自动只读
4. 生命周期继承：
   - 父对象作废/删除时从对象按规则级联
5. 时间线继承：
   - 从对象变更写入父对象时间线

### 涉及代码

1. `backend/apps/system/`
2. `backend/apps/workflows/`
3. `backend/apps/assets/services/`
4. `frontend/src/composables/`
5. `frontend/src/views/`

### 交付物

1. 主从继承规则实现
2. 子表可编辑性统一判定服务
3. 权限与状态回归测试

### 验收

1. 父对象进入审批中时子表自动只读。
2. 子表不能独立提交审批。
3. 子表不能绕过父对象权限独立写入。

建议工期: `4-5 人天`

---

## Phase 4: 布局设计器扩展

### 目标

使布局设计器正式支持主表区块和子表区块的统一设计。

### 任务

1. 为 `PageLayout.layout_config` 新增区块协议：
   - `field-section`
   - `detail-region`
   - `title`
   - `title_en`
   - `translation_key`
2. 设计器左侧面板增加“从对象关系”分组。
3. 支持拖入 `detail-region` 到画布。
4. 右侧属性面板支持配置：
   - 关联关系
   - 展示列
   - 工具栏
   - 编辑模式
   - 汇总规则
   - 只读策略
5. 预览态支持 `create/edit/readonly` 切换。
6. 发布后的布局能直接驱动运行时聚合页面。

### 涉及代码

1. `frontend/src/components/designer/`
2. `frontend/src/views/system/PageLayoutDesigner.vue`
3. `backend/apps/system/models.py`
4. `backend/apps/system/serializers.py`

### 交付物

1. 新区块协议
2. 设计器扩展
3. 运行时渲染适配
4. 设计器组件测试

### 验收

1. 设计器中可配置领用单的主表区和明细区。
2. 发布后运行时页面渲染结果与设计器预览一致。
3. 只读布局和编辑布局都能处理 `detail-region`。

建议工期: `6-8 人天`

---

## Phase 5: 批量迁移第一批单据

### 目标

将四类资产操作单据全部迁移到正式主从聚合架构。

### 任务

1. 迁移 `AssetPickup/PickupItem`
2. 迁移 `AssetTransfer/TransferItem`
3. 迁移 `AssetReturn/ReturnItem`
4. 迁移 `AssetLoan/LoanItem`
5. 清理旧的明细入口和过期页面逻辑
6. 保留必要的只读查询和导出能力

### 交付物

1. 四类单据全部切换
2. 旧入口兼容策略
3. 数据与页面回归测试

### 验收

1. 四类单据全部通过统一聚合页面进行新建、编辑、查看。
2. 四类明细对象不再作为普通用户顶级入口。
3. 四类单据流程、状态、时间线、审计均正常。

建议工期: `5-6 人天`

---

## Phase 6: 第二批推广与平台收敛

### 目标

将主从聚合架构推广到采购、验收、维修、报废等更多单据，并完成平台收口。

### 任务

1. 评估 `PurchaseRequest/PurchaseRequestItem`
2. 评估 `AssetReceipt/AssetReceiptItem`
3. 评估 `Maintenance/MaintenanceTask`
4. 评估 `DisposalRequest/DisposalItem`
5. 将通用能力文档化、模板化
6. 增加脚手架或快速配置模板

### 交付物

1. 第二批迁移方案
2. 平台模板
3. 复用文档

### 验收

1. 新单据接入主从聚合所需代码显著减少。
2. 设计器与运行时对主从单据的支持稳定。

建议工期: `5-7 人天`

---

## 4. 里程碑

| 里程碑 | 内容 | 结果 |
|--------|------|------|
| M1 | Phase 0-1 完成 | 平台识别主从对象 |
| M2 | Phase 2 完成 | 首个样板单据跑通 |
| M3 | Phase 3-4 完成 | 继承规则与设计器跑通 |
| M4 | Phase 5 完成 | 四类资产操作单据完成迁移 |
| M5 | Phase 6 完成 | 架构进入可复用推广阶段 |

---

## 5. 测试计划

### 5.1 后端

1. 元数据迁移测试
2. 对象角色与关系协议测试
3. 聚合保存事务测试
4. 主从继承规则测试
5. 父对象状态驱动子表只读测试

### 5.2 前端

1. 聚合页面渲染测试
2. 子表行编辑测试
3. create/edit/readonly 模式切换测试
4. 设计器 `detail-region` 组件测试

### 5.3 E2E

1. 新建领用单并新增明细
2. 编辑领用单并修改明细
3. 审批中领用单子表自动只读
4. 查看领用单只读详情
5. 四类资产操作单据全链路冒烟

---

## 6. 风险控制

1. 采用样板单据优先策略，避免一次性扩散。
2. 旧入口短期保留，按功能点逐步切换。
3. 所有元数据变更必须附迁移脚本与回归测试。
4. 设计器先只支持 `inline_table`，后续再扩 `nested_form`。
5. 平台协议冻结后再批量推广，避免边实现边改语义。

---

## 7. 资源建议

建议最小研发配置：

1. 后端 1 人，负责元数据协议、聚合服务、继承规则。
2. 前端 1 人，负责聚合运行时、子表区块、设计器扩展。
3. 测试/联调 0.5 人，负责主链路验证和回归。

建议总工期：

- P0 样板落地: `4-5 周`
- 第一批单据迁移完成: `6-8 周`

---

## 8. Definition of Done

1. 主从聚合协议已正式进入平台层。
2. 统一聚合页面已支撑首批样板单据。
3. 从对象自动继承父对象权限、审批、状态与生命周期。
4. 布局设计器已支持主表区与子表区。
5. 第一批资产操作单据已迁移完成。
6. 自动化测试覆盖主链路并稳定通过。
