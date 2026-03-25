# 实施计划: 主从聚合架构闭环交付

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-master-detail-aggregate-closed-loop-solution-2026-03-16.md`
- 版本: `v1.0`
- 日期: `2026-03-16`
- 目标: 将现有主从聚合基座收口成可切换、可迁移、可验收的闭环架构

## 2. 总体策略

本计划不再以“继续补设计器细节”作为主线，而改为 4 条交付主线并行推进:

1. 协议主线: 冻结主从聚合元数据、读写协议、继承协议
2. 运行时主线: 建立 `DocumentWorkbench` 和聚合读写服务
3. 迁移主线: 完成第一批 4 类资产操作单据切换
4. 收口主线: 关闭旧入口、补齐自动化测试和交付验收

## 3. 阶段划分

## Phase 0: 闭环冻结

### 目标

把“目标架构长什么样、哪些入口必须下线、哪些能力必须统一”一次说清，避免后续边做边改目标。

### 任务

1. 评审并冻结:
   - `object_role`
   - `relation_type`
   - `inherit_*`
   - `detail_edit_mode`
2. 冻结统一读模型和写模型:
   - `context/master/details/capabilities`
   - `_row_state`
3. 冻结统一页面模型:
   - `create/edit/readonly`
4. 冻结退役原则:
   - detail 不再作为一级业务入口
   - 旧明细页仅允许短期兼容
5. 冻结 I18N 硬约束:
   - `zh-CN/en-US`
   - `translation_key`

### 交付物

1. 闭环 PRD
2. 实施计划
3. 退役边界清单

### 验收

1. 项目团队对目标架构和停做项达成一致
2. 后续迭代不再新增独立 detail 业务入口

建议工期: `1-2 人天`

---

## Phase 1: 协议收口

### 目标

把当前“已经存在的主从协议字段”正式收口成统一平台契约，并补齐缺失的查询、能力和兼容层。

### 任务

1. 统一后端 aggregate runtime payload:
   - 明确 `aggregate.detailRegions`
   - 明确 bilingual metadata
   - 明确 `relationType/detailEditMode`
2. 统一前端 aggregate types:
   - `RuntimeAggregateDetailRegion`
   - `DocumentCapability`
   - `DocumentSubmitPayload`
3. 统一 detail 对象导航策略:
   - 菜单过滤
   - 对象工作台过滤
   - 全局对象选择器过滤
4. 制定 detail 只读兼容查询策略:
   - 允许查询
   - 禁止成为主入口

### 涉及模块

- `backend/apps/system/models.py`
- `backend/apps/system/viewsets/object_router.py`
- `backend/apps/system/services/`
- `frontend/src/router/`
- `frontend/src/stores/`
- `frontend/src/types/`

### 交付物

1. 聚合协议清单
2. 运行时协议对齐
3. detail 导航策略对齐

### 验收

1. 所有第一批单据的 detail 对象都被系统视为从对象
2. 所有前端主入口都默认不暴露 detail
3. 运行时协议字段不再存在多套命名和含义冲突

建议工期: `2-3 人天`

---

## Phase 2: 统一聚合读写服务

### 目标

建立平台级 `AggregateDocumentService`，让主表和子表读写成为标准能力，而不是每个单据各写一套。

### 任务

1. 设计统一服务边界:
   - `load_document`
   - `validate_document`
   - `save_document`
   - `build_capabilities`
2. 统一事务写入协议:
   - 创建主表
   - 创建/更新/删除明细
   - 行状态处理
   - 回滚策略
3. 统一读模型返回:
   - `master`
   - `details`
   - `capabilities`
   - `workflow`
   - `timeline`
   - `audit`
4. 为第一批单据建立 concrete adapter:
   - `AssetPickup`
   - `AssetTransfer`
   - `AssetReturn`
   - `AssetLoan`

### 涉及模块

- `backend/apps/system/services/`
- `backend/apps/assets/services/`
- `backend/apps/lifecycle/services/`
- `backend/apps/system/viewsets/object_router.py`

### 交付物

1. 聚合读服务
2. 聚合写服务
3. 第一批单据 adapter

### 验收

1. 第一批单据支持统一读模型
2. 第一批单据支持统一事务保存
3. 明细保存失败时主单据可统一回滚

建议工期: `5-7 人天`

---

## Phase 3: 统一单据运行时

### 目标

把前端真正收口到 `DocumentWorkbench`，让 create/edit/readonly 三种模式都通过同一个单据页模型完成。

### 任务

1. 建立 `DocumentWorkbench`:
   - `DocumentHeader`
   - `MasterSections`
   - `DetailRegions`
   - `WorkflowPanel`
   - `TimelinePanel`
   - `AuditPanel`
2. 统一 page mode:
   - `create`
   - `edit`
   - `readonly`
3. 将 detail-region 渲染切到正式 runtime:
   - 不再只靠注入兜底
   - 不再让专用页和动态页各自拼装
4. 统一 capability 消费:
   - 主表是否可编辑
   - 子表是否可编辑
   - 是否允许提交/审批/作废

### 涉及模块

- `frontend/src/views/dynamic/`
- `frontend/src/components/common/`
- `frontend/src/components/engine/`
- `frontend/src/api/`
- `frontend/src/types/runtime.ts`

### 交付物

1. `DocumentWorkbench`
2. 聚合详情页
3. 聚合编辑页
4. 聚合新建页

### 验收

1. 第一批单据 create/edit/readonly 都统一进入聚合页
2. 主表和子表不再由多个页面模型分别处理
3. capability 决定 UI 态，不再由页面重复推导

建议工期: `6-8 人天`

---

## Phase 4: 继承引擎收口

### 目标

把权限、工作流、状态、生命周期、审计归集统一交给继承策略层，不再散在页面和单据 service 里。

### 任务

1. 建立统一 policy resolver:
   - `permission`
   - `workflow`
   - `status`
   - `lifecycle`
   - `audit`
2. 明确父对象驱动规则:
   - 父对象审批中，子表自动只读
   - 父对象不可编辑，子表自动只读
   - 子对象不能独立发起流程
   - 子对象写入父时间线
3. 统一 capability builder 输出

### 涉及模块

- `backend/apps/system/services/`
- `backend/apps/workflows/`
- `backend/apps/assets/services/`
- `backend/apps/lifecycle/services/`
- `frontend/src/composables/`

### 交付物

1. 继承策略服务
2. capability builder
3. 状态与流程联动规则

### 验收

1. 页面不再自行决定 detail 可编辑性
2. 第一批单据的工作流和状态都能驱动子表行为
3. 明细变更被归集到父单据时间线和审计流

建议工期: `4-5 人天`

---

## Phase 5: 设计器与运行时完全同构

### 目标

让设计器不只是“能设计 detail-region”，而是成为第一批单据布局的唯一配置入口。

### 任务

1. 确认 `field-section` 和 `detail-region` 是唯一正式区块
2. 统一设计器输出与运行时输入协议
3. 检查 detail-region 支持项是否与 runtime 完全同构:
   - relation
   - bilingual title
   - toolbar
   - column config
   - section preset
   - column preset
   - readonly strategy
4. 补齐布局发布和回归验证

### 涉及模块

- `frontend/src/components/designer/`
- `frontend/src/platform/layout/`
- `backend/apps/system/validators.py`
- `backend/apps/system/viewsets/object_router.py`

### 交付物

1. 同构设计器协议
2. 运行时兼容校验
3. 布局发布验证

### 验收

1. 第一批单据布局通过设计器配置即可驱动运行时
2. 不再需要在页面里额外硬编码 detail-region 布局
3. 设计器预览与运行时渲染结果一致

建议工期: `3-4 人天`

---

## Phase 6: 第一批单据整批迁移

### 目标

完成第一批 4 类资产操作单据从旧入口到新聚合入口的整批切换。

### 任务

1. 迁移 `AssetPickup / PickupItem`
2. 迁移 `AssetTransfer / TransferItem`
3. 迁移 `AssetReturn / ReturnItem`
4. 迁移 `AssetLoan / LoanItem`
5. 处理旧入口:
   - 菜单移除
   - 路由降级
   - 兼容查询保留

### 交付物

1. 4 类单据迁移完成
2. 旧入口退役清单
3. 兼容窗口说明

### 验收

1. 普通用户通过新聚合页完成全部常规操作
2. detail 对象不再作为日常业务入口
3. 主从读写、状态、流程、时间线、审计全部跑通

建议工期: `5-6 人天`

---

## Phase 7: 自动化测试与关闭切口

### 目标

把闭环变成可持续交付的能力，而不是一次性改造。

### 任务

1. 补齐后端测试:
   - 协议层
   - 聚合读写层
   - 继承策略层
2. 补齐前端测试:
   - `DocumentWorkbench`
   - detail-region runtime
   - 设计器发布链路
3. 增加 E2E 冒烟:
   - 新建单据
   - 编辑单据
   - 审批中只读
   - 只读查看
4. 增加 I18N 审核:
   - `zh-CN/en-US` parity
   - 无新增硬编码

### 交付物

1. 自动化测试矩阵
2. E2E 冒烟脚本
3. I18N 检查清单

### 验收

1. 第一批闭环能力有稳定自动化保障
2. 后续第二批单据推广可直接复用测试框架

建议工期: `3-4 人天`

## 4. 关键里程碑

| 里程碑 | 条件 | 结果 |
| --- | --- | --- |
| M1 | Phase 0-1 完成 | 协议冻结，不再新增旧模型入口 |
| M2 | Phase 2 完成 | 聚合读写服务可跑通第一批单据 |
| M3 | Phase 3-4 完成 | 统一运行时和继承引擎成型 |
| M4 | Phase 5-6 完成 | 第一批单据完成整批切换 |
| M5 | Phase 7 完成 | 闭环进入可复制推广阶段 |

## 5. 工作分工建议

最小配置建议:

1. 后端 1 人
   - 聚合读写服务
   - 继承引擎
   - 运行时协议
2. 前端 1 人
   - `DocumentWorkbench`
   - detail-region runtime
   - 设计器与运行时同构
3. 测试/联调 0.5 人
   - 回归
   - E2E
   - I18N 检查

## 6. 风险与应对

| 风险 | 说明 | 应对 |
| --- | --- | --- |
| 旧入口长期并存 | 新旧模型都能用，团队会持续拖延迁移 | 在 Phase 0 就冻结退役边界 |
| 运行时与设计器再次分叉 | 两边各自长能力 | 统一以设计器协议为布局事实来源 |
| capability 仍散在页面 | 看似迁移完成，实则规则没收口 | 强制所有可编辑性走 capability builder |
| 第一批单据差异大 | 适配工作量高 | 先抽共性协议，再由 adapter 吸收差异 |
| 多语言被再次绕过 | 快速迭代时容易写死文案 | 每阶段增加 i18n review gate |

## 7. Definition of Ready

进入开发前必须满足:

1. 闭环 PRD 已确认
2. 第一批单据样板对象已确认
3. 停做项已确认
4. 旧入口退役原则已确认

## 8. Definition of Done

当以下条件全部满足，本计划才算完成:

1. 第一批 4 类资产操作单据全部迁移到主从聚合运行时
2. 主表/子表统一读写协议已替代分散保存逻辑
3. 权限、流程、状态、生命周期继承已经由统一 policy 驱动
4. 设计器已成为第一批单据布局的唯一编辑入口
5. detail 对象不再作为主业务入口
6. 自动化测试和 E2E 已覆盖闭环主链路
7. `zh-CN/en-US` 双语约束已通过检查

## 9. 下一步建议

建议下一轮开发从 Phase 2 开始，而不是继续新增设计器局部体验。

原因:

1. 设计器 detail-region 能力已经接近可用上限
2. 当前最大缺口在统一读写协议和统一运行时
3. 如果不先收口运行时，继续增强设计器只会进一步扩大“配置能力领先于业务落地能力”的差距

推荐立即开工顺序:

1. 聚合读写服务
2. `DocumentWorkbench`
3. capability builder
4. 第一批单据迁移
