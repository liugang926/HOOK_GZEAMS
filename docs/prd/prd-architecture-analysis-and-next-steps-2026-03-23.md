# GZEAMS 项目现状全面架构分析 & 下一步开发建议 PRD

> **版本**: v1.0  
> **日期**: 2026-03-23  
> **分析范围**: 后端 21 模块 · 前端 19 视图目录 · 63 公共组件 · 29 PRD 文档 · 80+ 历史计划文档

---

## 一、项目现状总览

### 1.1 架构健康度评分

| 维度 | 评分 | 说明 |
|------|:----:|------|
| **后端基础架构** | ⭐⭐⭐⭐⭐ | BaseModel 体系完善，TenantManager / GlobalMetadataManager 双管理器成熟 |
| **低代码元数据引擎** | ⭐⭐⭐⭐ | BusinessObject / FieldDefinition / PageLayout / ObjectRelationDefinition 四大核心完备 |
| **前端组件引擎** | ⭐⭐⭐⭐ | DynamicForm / FieldRenderer / BaseListPage / BaseDetailPage 完整，63 个公共组件 |
| **统一动态路由** | ⭐⭐⭐⭐⭐ | `/objects/{code}` 统一路由已全面落地，遗留路由自动重定向 |
| **工作流引擎** | ⭐⭐⭐⭐ | 后端 6 个模型 + 5 个序列化器 + 视图集 + 服务完整，前端设计器组件就绪 |
| **盘点管理** | ⭐⭐⭐⭐ | 后端全栈实现（模型/序列化器/4 大服务），前端视图就绪 |
| **SSO 集成** | ⭐⭐⭐⭐ | 适配器模式完整，WeWork/DingTalk/Feishu 架构就绪 |
| **测试覆盖** | ⭐⭐⭐ | 后端测试文件丰富但覆盖率有待提升，前端测试框架就绪但用例不足 |
| **技术债务** | ⭐⭐ | 项目根目录杂文件多，多个临时脚本/截图未清理 |

### 1.2 代码规模统计

```
后端 (backend/apps/)
├── 21 个业务模块
├── 43 个 models.py 文件
├── assets/models.py - 1,479 行（15+ 模型）
├── system/models.py - 2,935 行（核心元数据引擎 + 字典 + 序列 + 配置）
├── lifecycle/models.py - 1,360 行（采购/入库/维修/处置全流程）
├── workflows/models/ - 6 个模型文件（定义/实例/任务/审批/日志/模板）
├── inventory/ - 全栈实现（模型 + 5 序列化器 + 4 服务 + 视图集）
└── common/ - BaseModel(137行) + managers + serializers + viewsets + filters + services

前端 (frontend/src/)
├── 19 个视图目录
├── 63 个公共组件 (components/common/)
├── 12 个引擎组件 (components/engine/)
├── 29 个 API 模块 (api/)
├── router/index.ts - 617 行统一路由配置
└── BaseListPage.vue - 42,029 字节（核心列表页）
```

---

## 二、各模块实现状态深度分析

### 2.1 模块完成度矩阵

| 模块 | 后端模型 | 序列化器 | 视图集 | 服务层 | 前端页面 | 前端 API | 测试 | 完成度 |
|------|:--------:|:--------:|:------:|:------:|:--------:|:--------:|:----:|:------:|
| **common (基类层)** | ✅ | ✅ | ✅ | ✅ | — | — | ✅ | 100% |
| **organizations** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 95% |
| **accounts** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 90% |
| **system (元数据)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 90% |
| **assets (核心资产)** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 90% |
| **consumables** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 85% |
| **lifecycle** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 85% |
| **workflows** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 80% |
| **inventory** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 80% |
| **sso** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 75% |
| **notifications** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | 70% |
| **permissions** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | 65% |
| **insurance** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | — | 60% |
| **leasing** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | — | 60% |
| **depreciation** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | — | 55% |
| **finance** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | — | 55% |
| **integration** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 70% |
| **it_assets** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | 55% |
| **software_licenses** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | 55% |
| **mobile** | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | 50% |
| **projects** | ✅ | — | — | — | — | — | — | 20% |

> ✅ = 完整实现 | ⚠️ = 部分实现 / 需补充 | — = 未实现

### 2.2 核心架构亮点

#### A. 元数据驱动引擎 — 架构成熟度极高

```
BusinessObject (2935行 system/models.py)
├── 支持 hardcoded Django 模型 + 纯元数据驱动双模式
├── 24+ 字段类型覆盖（text/number/currency/reference/formula/sub_table/qr_code...）
├── ObjectRelationDefinition 统一关系模型（direct_fk/through_line_item/derived_query）
├── ModelFieldDefinition 自动从 Django 模型导出元数据
└── GlobalMetadataManager 跨组织共享元数据
```

#### B. 统一动态路由 — 前端架构领先

```
路由模式: /objects/{code} → DynamicListPage / DynamicFormPage / DynamicDetailPage
├── 聚合文档编辑模式: AssetPickup/Transfer/Return/Loan → DynamicObjectEditForm
├── 标准编辑模式: 其他对象 → DynamicObjectDetail?action=edit
├── 遗留路由兼容层: buildLegacyObjectAliasRoutes 自动重定向
└── 生命周期路由: buildLegacyLifecycleAliasRoutes 7 个对象完整映射
```

#### C. 公共组件层 — 高度规范化

| 组件 | 大小 | 功能 |
|------|------|------|
| `BaseListPage.vue` | 42KB | 统一列表页（搜索/过滤/分页/批量/导出/列管理） |
| `BaseDetailPage.vue` | 21KB | 统一详情页（分区/编辑/审计/关联） |
| `FieldDisplay.vue` | 35KB | 统一字段显示（24+ 字段类型渲染） |
| `DynamicDetailPage.vue` | 34KB | 动态详情页（元数据驱动渲染） |
| `ActivityTimeline.vue` | 22KB | 活动时间线 |
| `RelatedObjectTable.vue` | 19KB | 关联对象表格 |

---

## 三、关键问题与技术债务

### 3.1 🔴 高优先级问题

#### P0: 项目根目录污染严重

根目录累积了 **60+ 临时文件**：

- 临时测试脚本：`check_*.spec.ts`, `verify_*.py`, `run_*.py`（20+ 个）
- 临时截图/数据导出：`*.png`, `*.json`, `*.html`（15+ 个）
- 临时修复/诊断脚本：`fix_*.py`, `inspect_*.py`（10+ 个）
- 日志/cookie 文件：`cookies.txt`, `git_log.txt`, `token_response.json`

> [!WARNING]
> 这些文件不应提交到仓库，应在 `.gitignore` 中排除或清理

#### P0: 后端多个模块缺少完整的「序列化器 → 视图集 → 服务」三层实现

以下模块有模型但三层不完整：

| 模块 | 缺失的层 |
|------|----------|
| `insurance` (保险) | 序列化器/视图集/服务层部分缺失 |
| `leasing` (租赁) | 序列化器/视图集/服务层部分缺失 |
| `depreciation` (折旧) | 序列化器/视图集/服务层部分缺失 |
| `finance` (财务) | 序列化器/视图集/服务层部分缺失 |
| `it_assets` (IT 资产) | 序列化器/视图集/服务层部分缺失 |
| `software_licenses` (软件许可) | 序列化器/视图集/服务层部分缺失 |
| `projects` (项目) | 只有模型，完全缺少其他层 |

### 3.2 🟡 中优先级问题

#### P1: 工作流引擎 ↔ 业务流程未完全打通

- 工作流后端基础架构已完整（定义/实例/任务/审批/日志），但与资产领用/调拨/采购等单据的**状态联动**尚未完全接通
- 前端工作流设计器已有框架，但**节点配置面板**（字段权限、条件表达式）的交互深度不足

#### P1: 前端 TypeScript 严格模式告警积压

- 从 `ts_errors*.txt` 等文件判断，存在大量 TypeScript 类型检查告警（多达 35,000+ 字节的错误输出）
- 前端构建产出 `dist/` 目录已存在，但 TypeScript 严格模式下的类型完整性有待提升

#### P1: 测试覆盖率不均衡

- 后端：`common`/`accounts`/`organizations`/`assets` 模块有较完善的测试（每模块 `tests/` 目录下 3-5 个测试文件）
- 后端：`insurance`/`leasing`/`finance`/`depreciation` **完全缺少测试**
- 前端：`components/__tests__`/`components/common/__tests__` 已有测试框架，但业务视图级测试极少

### 3.3 🟢 低优先级问题

- i18n 国际化：已有 `locales/` 和翻译管理 API，但部分模块的翻译 key 不完整
- API 文档：drf-spectacular 已集成但部分新模块未补充 Schema 标注
- Docker 配置：`docker-compose.yml` 和 `Dockerfile.backend` 已就绪，但缺少前端构建的生产 Dockerfile

---

## 四、下一步开发建议（分优先级）

### Sprint 0: 技术债务清理（建议 1-2 天）

| # | 任务 | 预估工时 | 影响 |
|---|------|:--------:|------|
| 1 | 清理项目根目录临时文件，更新 `.gitignore` | 2h | 代码库卫生 |
| 2 | 补全 `insurance` / `leasing` / `depreciation` / `finance` 的序列化器 + 视图集 + 服务层 | 6h | 业务闭环 |
| 3 | 解决前端 TypeScript 类型告警核心项（优先修复编译阻断性错误） | 4h | 构建稳定性 |
| 4 | 补充 `projects` 模块的完整后端三层实现 | 3h | 功能补全 |

### Sprint 1: 工作流 ↔ 业务闭环（建议 3-5 天）

> [!IMPORTANT]
> 这是提升产品可用性的最关键一步。当前工作流引擎与业务单据之间存在"最后一公里"断层。

| # | 任务 | 详情 |
|---|------|------|
| 1 | **工作流状态联动闭环** | 资产领用/调拨/采购单据提交后自动触发工作流，审批通过后自动推进单据状态 |
| 2 | **审批节点字段权限配置** | 不同审批节点控制不同字段的可见/只读/可编辑属性 |
| 3 | **条件分支规则引擎** | 基于金额/部门/资产类型等字段的自动路由条件配置 |
| 4 | **前端审批操作面板** | 在 DynamicDetailPage 内嵌审批操作区域（通过/拒绝/转发/加签） |
| 5 | **工作流实例监控看板** | 流程进度可视化，支持管理员催办/转办 |

### Sprint 2: 用户门户 (Phase 6) 闭环（建议 3-5 天）

| # | 任务 | 详情 |
|---|------|------|
| 1 | **我的资产页面** | 查看当前用户保管/使用/借用的资产列表，支持搜索和导出 |
| 2 | **我的申请页面** | 领用/调拨/采购/处置申请记录及状态跟踪 |
| 3 | **我的待办 & 通知中心** | 待审批事项 + 系统消息 + 到期提醒 |
| 4 | **Dashboard 数据看板增强** | 资产总量/分类/状态分布统计图表、待办事项摘要、近期操作 |
| 5 | **移动端 PWA 配置** | Service Worker 注册、离线缓存策略、添加到主屏幕 |

### Sprint 3: 盘点管理端到端体验（建议 3-5 天）

| # | 任务 | 详情 |
|---|------|------|
| 1 | **盘点任务向导式创建** | 分步骤选择盘点范围(部门/位置/分类)、指定盘点人、设定截止日期 |
| 2 | **移动端扫码盘点** | 二维码扫描 → 实时比对快照 → 标记差异 → 拍照取证 |
| 3 | **差异报告 & 审批** | 盘亏/盘盈/位置不符自动生成差异报告，提交审批 |
| 4 | **盘后处理闭环** | 审批通过后自动调账（盘亏标记报废/清理，盘盈建卡入库） |
| 5 | **盘点统计报表** | 盘点覆盖率、差异分布、人员效率统计 |

### Sprint 4: 质量 & 稳定性（持续性）

| # | 任务 | 详情 |
|---|------|------|
| 1 | **后端单元测试补全** | 为 insurance/leasing/finance/depreciation 补充单元测试（目标覆盖率 ≥ 70%） |
| 2 | **前端组件测试** | 核心组件 DynamicForm / BaseListPage / FieldDisplay 增加 Vitest 测试 |
| 3 | **E2E 流程测试** | 资产全生命周期闭环测试（创建 → 领用 → 调拨 → 维修 → 处置）|
| 4 | **性能基准测试** | 大数据量列表加载（10,000+ 资产）、并发审批性能 |
| 5 | **CI/CD 流水线增强** | TypeScript 检查 + 后端测试 + Lint 纳入 GitHub Actions 门禁 |

---

## 五、推荐开发路线图时间线

```
2026-03 W4    Sprint 0: 技术债务清理
              ├── 根目录清理 + .gitignore
              ├── 补全 insurance/leasing/depreciation/finance 后端三层
              └── TypeScript 核心告警修复

2026-04 W1-2  Sprint 1: 工作流 ↔ 业务闭环
              ├── 状态联动引擎
              ├── 审批字段权限
              ├── 条件分支配置
              └── 前端审批面板

2026-04 W3-4  Sprint 2: 用户门户 (Phase 6)
              ├── 我的资产 / 申请 / 待办
              ├── Dashboard 看板增强
              └── PWA 移动端配置

2026-05 W1-2  Sprint 3: 盘点管理端到端
              ├── 向导式任务创建
              ├── 移动扫码盘点
              ├── 差异报告审批
              └── 盘后处理闭环

2026-05 W3+   Sprint 4: 全面质量提升
              ├── 测试覆盖补全
              ├── 性能基准
              └── CI/CD 门禁
```

---

## 六、架构优化建议

### 6.1 短期优化（随开发推进）

| 建议 | 详情 |
|------|------|
| **统一序号生成器** | 当前各模型的 `_generate_xxx_no()` 方法有大量重复代码，应全面迁移至 `SequenceService` |
| **事件驱动完善** | 补全 Django Signals：`asset_transferred`, `inventory_confirmed`, `workflow_completed` 等事件的实际注册和监听 |
| **缓存层建设** | 高频查询元数据（BusinessObject / FieldDefinition）应通过 Redis 缓存，减少 DB 压力 |
| **前端 API 层统一** | 部分模块仍使用独立 API（如 `itAssets.ts`/`softwareLicenses.ts`），应评估迁移至 `dynamic.ts`（`createObjectClient`） |

### 6.2 中期架构演进

| 建议 | 详情 |
|------|------|
| **RBAC → ABAC 权限演进** | 当前按角色的粗粒度权限难以满足字段级/行级控制需求，建议渐进式引入 ABAC |
| **Celery 任务监控** | 引入 Flower 或自建仪表板监控异步任务执行状况 |
| **前端微应用探索** | 当系统模块超过 20+，可考虑 Module Federation 实现按需加载 |
| **数据大屏 / BI 接口** | 为管理层决策提供标准化数据接口，支持对接外部 BI 工具 |

---

## 七、总结

### 项目整体评价

GZEAMS 作为一个**元数据驱动的低代码固定资产管理平台**，在核心架构层面已达到**较高成熟度**：

- ✅ **元数据引擎**：BusinessObject + FieldDefinition + PageLayout + ObjectRelationDefinition 四大核心模型完备
- ✅ **统一动态路由**：前端已全面采用 `/objects/{code}` 模式，遗留路由优雅降级
- ✅ **公共基类体系**：BaseModel → BaseModelSerializer → BaseModelViewSet → BaseCRUDService → BaseModelFilter 五层继承规范化
- ✅ **资产全生命周期**：采购请求 → 资产入库 → 领用/调拨/借用 → 维修保养 → 处置报废 模型完整

**当前最大短板**是：
1. 工作流引擎与业务流程的"最后一公里"连接
2. 用户门户 (Phase 6) 的端到端体验尚未闭环
3. 多个扩展模块（保险/租赁/折旧/财务）后端三层实现不完整
4. 项目卫生和测试覆盖需要系统性提升

建议按照 **Sprint 0 → 1 → 2 → 3 → 4** 的顺序推进，优先清理技术债务、打通工作流闭环、完成用户门户，最后系统性提升质量和稳定性。
