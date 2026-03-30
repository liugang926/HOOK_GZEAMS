# GZEAMS Phase Status Analysis Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-28 |
| 涉及阶段 | Phase 1.1 - Phase 7.4（前端现状复盘） |
| 作者/Agent | Codex GPT-5 |

## 一、分析概述
- 本次检查聚焦 `frontend/src/views/` 模块目录、`docs/plans/` Phase 文档、`frontend_v2.md` 与实际代码的对应关系，以及当前前端质量状态。
- 已核对的核心范围包括：`assets`、`consumables`、`inventory`、`workflow`、`system`、`integration`、`finance`、`portal`、`mobile`、`reports`、`it-assets`、`softwareLicenses`、`insurance`、`leasing`。
- 质量检查同时执行了 `npm run i18n:parity:all`、`npm run i18n:coverage:all`、`npm run typecheck:strict`、`npm run typecheck:app`，并使用 `rg` 检查 TODO/FIXME。

## 二、frontend/src/views 模块目录现状

| 模块目录 | 现状判断 | 关联 Phase |
|----------|----------|-----------|
| `assets/` | 已落地，覆盖资产台账、分类、供应商、地点、领用/调拨/归还/借用 | Phase 1.1 / 1.4 / 1.5 / 1.7 / 7.1 |
| `consumables/` | 已落地，含列表、表单、库存操作 | Phase 1.6 |
| `mobile/` | 已落地，含统一扫码与资产详情 | Phase 1.8 / 4.1 |
| `notifications/` | 已落地，含通知中心与偏好 | Phase 1.9 / 2.3 |
| `system/` | 已落地，含业务对象、字段、布局、配置、SSO、组织树 | Phase 1.2 / 1.3 / 2.1 / 2.2 / 2.4 |
| `workflow/` 与 `workflows/` | 已落地，含任务中心、审批详情、流程定义与实例 | Phase 3.1 / 3.2 |
| `inventory/` | 已落地，含任务执行、分配、差异、对账、报告 | Phase 4.1 / 4.2 / 4.3 / 4.4 / 4.5 |
| `integration/` | 已落地但路由暴露不足，含配置页、总览页、同步任务页 | Phase 5.0 / 5.1 |
| `finance/` | 部分落地，现有凭证列表/详情、折旧列表；模板管理原先缺失 | Phase 5.2 / 5.3 |
| `portal/` | 文件存在但未接入路由与语言包，仍属未交付状态 | Phase 6 |
| `reports/` | 已落地，含报表中心 | Phase 5.4 |
| `insurance/` | 已落地 | Finance extension |
| `leasing/` | 已落地 | Finance extension |
| `it-assets/` | 已落地 | Extension / implementation plans |
| `softwareLicenses/` | 已落地 | 2026-01-24 软件许可方案 |

## 三、已落地 Phase 清单

以下 Phase 至少已有对应前端页面、视图目录或静态/动态路由承载：

| Phase | 状态 | 代码证据 |
|------|------|---------|
| Phase 1.1 资产分类 | 已落地 | `frontend/src/views/assets/settings/CategoryManagement.vue` |
| Phase 1.2 / 2.4 组织管理 | 已落地 | `frontend/src/views/system/OrganizationTree.vue`、`DepartmentList.vue` |
| Phase 1.3 元数据引擎 | 已落地 | `BusinessObjectList.vue`、`FieldDefinitionList.vue`、`PageLayoutList.vue` |
| Phase 1.4 资产 CRUD | 已落地 | `AssetList.vue`、`AssetForm.vue` |
| Phase 1.5 资产作业 | 已落地 | `assets/operations/*.vue` |
| Phase 1.6 耗材 | 已落地 | `ConsumableList.vue`、`ConsumableForm.vue` |
| Phase 1.7 生命周期基础 | 已落地 | 生命周期对象通过统一 `/objects/{code}` 路由承载 |
| Phase 1.8 移动端增强 | 已落地 | `mobile/assets/AssetDetail.vue`、`mobile/scan/UnifiedScan.vue` |
| Phase 1.9 / 2.3 通知增强 | 已落地 | `NotificationCenter.vue`、`NotificationPreferences.vue` |
| Phase 2.1 / 2.2 企业微信 SSO/同步配置 | 已落地 | `SSOConfigPage.vue` |
| Phase 2.5 权限增强 | 已落地 | `PermissionManagement.vue` |
| Phase 3.1 LogicFlow | 已落地 | `admin/WorkflowEdit.vue`、`WorkflowList.vue` |
| Phase 3.2 工作流引擎 | 已落地 | `TaskCenter.vue`、`MyApprovals.vue`、`WorkflowDashboard.vue` |
| Phase 4.1 - 4.5 盘点系列 | 已落地 | `inventory/`、`inventory/reconciliation/`、`TaskExecute.vue` |
| Phase 5.0 集成框架 | 已落地 | `IntegrationConfigList.vue`、`IntegrationList.vue`、`SyncJobList.vue` |
| Phase 5.4 财务报表 | 已落地 | `ReportCenter.vue` |

## 四、待完成或与 frontend_v2 不一致的 Phase 清单

### Phase 5.1 M18 Adapter
- `frontend_v2.md` 期望有 `M18ConfigPanel.vue`、M18 专用连接配置、采购订单/资产/供应商同步入口和任务追踪。
- 实际代码只有通用集成框架页面：`IntegrationConfigList.vue`、`IntegrationList.vue`、`SyncJobList.vue`。
- 其中只有 `IntegrationConfigList.vue` 已接入路由；`IntegrationList.vue` 与 `SyncJobList.vue` 文件存在但未注册路由。
- 结论：Phase 5.1 已有通用承载层，但缺少 M18 专用入口与完整路由暴露。

### Phase 5.2 Finance Integration
- `frontend_v2.md` 输出文件要求包括 `VoucherList.vue`、`VoucherForm.vue`、`VoucherTemplateList.vue`、`VoucherDetailDialog.vue`、`EntryTable.vue`。
- 实际代码原先仅有 `VoucherList.vue`、`VoucherDetail.vue`，没有模板管理页面，且前端业务类型筛选值与后端真实值不一致。
- 本轮已补齐 `VoucherTemplateList.vue`、模板应用动作、路由入口，并修正了 `VoucherList.vue` 的业务类型与状态筛选值。
- 结论：Phase 5.2 已从“核心页面缺失”推进到“模板管理可用”，但仍缺少文档中描述的独立凭证表单页/对话框形态。

### Phase 5.3 Depreciation
- `frontend_v2.md` 输出文件要求包括折旧列表、资产折旧详情、折旧报表、折旧配置。
- 实际代码只有 `frontend/src/views/finance/DepreciationList.vue` 和 `frontend/src/views/finance/components/DepreciationGenerator.vue`。
- 未发现独立的资产折旧详情页、报表页、配置页及其路由。
- 结论：Phase 5.3 仅完成基础列表和计算入口，报表与配置前端仍待实现。

### Phase 6 User Portal
- `frontend_v2.md` 明确标注后端依赖缺失，并要求 `/portal/*` API、字段配置 API、门户首页/我的资产/我的申请/我的待办/个人中心。
- 实际代码存在 `frontend/src/views/portal/UserPortal.vue` 及 3 个 Tab 组件，但没有任何 `portal` 路由，也没有 `portal` 语言包。
- 当前 Portal 页面使用的是现有 `assetApi`、生命周期 API 与工作流 API，不是文档约定的 `/portal/*` 契约。
- 结论：Phase 6 处于“页面原型存在，但未集成、未可访问、未按 API 契约实现”的状态。

## 五、代码质量评估

### 1. TODO / FIXME
- `rg -n "TODO|FIXME" frontend/src backend/apps docs/plans` 命中多处历史遗留。
- 前端实际代码中的高相关遗留包括：
  - `frontend/src/views/consumables/ConsumableList.vue:165`
  - `frontend/src/views/assets/AssetForm.vue:210`
  - `frontend/src/views/system/components/BusinessObjectForm.vue:220`
  - `frontend/src/stores/dict.ts:12`
- 后端也仍有关键 TODO，例如 `backend/apps/finance/viewsets/__init__.py:386` 的 ERP integration comment。

### 2. 国际化覆盖率
- `npm run i18n:parity:all`：`finance.json` 已 129/129 完整对齐；全局仍有 15 个 parity issue，集中在 `common.json` 与 `menu.json`。
- `npm run i18n:coverage:all`：动态范围覆盖率为 `76.65%`，低于 95% 阈值。
- 硬编码样本主要集中在动态工作区模型和少量组件；Portal 目前完全缺少 locale 文件，属于结构性空缺。

### 3. TypeScript 类型完整性
- `npm run typecheck:app`：通过，说明应用层当前可编译。
- `npm run typecheck:strict`：失败，共 `77` 个 TS 错误。
- 错误主要集中在测试代码与测试辅助层，例如 `src/__tests__/mocks/msw-setup.ts`、`src/__tests__/unit/api/business-contract-adapters.spec.ts`、若干组件/布局测试。
- 结论：应用层类型状态可接受，测试层类型债务较重。

## 六、优先级结论
- 最高优先级未完成前端能力判定为 Phase 5.2 的“凭证模板管理”。
- 原因：Phase 5.1 已有通用集成框架承载，Phase 5.3 至少有基础列表与计算入口，而 Phase 5.2 在文档中被定义为核心财务能力，但此前前端只有 API/types、没有实际模板页面。
- 本轮继续开发选择：补齐 Phase 5.2 凭证模板管理前端。

## 七、后续建议
- 下一优先级建议补 Phase 5.3 的 `DepreciationReport` 与 `DepreciationConfig` 页面及路由。
- Phase 5.1 建议把 `IntegrationList.vue`、`SyncJobList.vue` 正式接入路由，并补 M18 专用入口。
- Phase 6 若要真正交付，至少要补齐：`portal` 路由、`portal` locale、以及 `/portal/*` API 适配层。
