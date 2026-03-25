# GZEAMS 当前现状分析报告

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-20 |
| 作者/Agent | Codex |
| 分析范围 | 后端 `backend/apps/`、前端 `frontend/src/`、路由与核心文档 |
| 分析方式 | 代码静态盘点 + 关键文件抽样审阅 + 本地命令可执行性验证 |

## 一、实施概述

### 1.1 当前代码规模

| 维度 | 数值 | 说明 |
|------|------|------|
| Django Apps | 20 个 | 已覆盖资产、组织、系统、工作流、盘点、财务、集成等核心域 |
| 后端代码文件 | 547 个 | 不含 migration |
| 后端代码行数 | 145,979 行 | 含业务代码与测试 |
| 后端测试行数 | 35,463 行 | 说明后端已进入稳定化阶段 |
| 前端应用文件 | 614 个 | `.vue/.ts/.js` |
| 前端应用行数 | 130,927 行 | 动态工作区、设计器、系统页已较完整 |
| 前端测试文件 | 189 个 | `vitest` + Playwright 相关测试资产已存在 |
| 前端测试行数 | 28,108 行 | 与旧报告相比已明显增加 |

### 1.2 已落地的强能力

1. 后端公共基座完整。`BaseModel`、`BaseModelSerializer`、`BaseModelViewSet`、`BaseResponse`、多组织上下文解析都已具备平台级复用能力。
2. 动态对象路由成熟。`ObjectRouterViewSet` 已成为真正的统一入口，支持 CRUD、metadata、runtime、relations、actions、aggregate document、batch 操作。
3. 前端动态工作区成型。`DynamicListPage`、`DynamicFormPage`、`DynamicDetailPage` 已与动态 API、runtime layout、对象关系导航打通。
4. 财务与集成闭环已具雏形。异步推送、`IntegrationLog`、`IntegrationSyncTask`、失败告警与重试机制已存在，不再是纯概念设计。
5. 测试资产不薄弱。系统模块、动态对象路由、关系/动作/运行时契约、前端动态页面与布局回归都有实际测试文件支撑。

### 1.3 当前关键约束

| 约束项 | 现状 | 影响 |
|------|------|------|
| 本地 Django 运行环境 | `python3 backend/manage.py check` 因缺少 `django` 依赖失败 | 无法在当前工作区直接做后端运行时校验 |
| 前端依赖安装 | `npm run typecheck:strict` 因缺少 `vue-tsc` 失败 | 无法在当前工作区直接做前端类型校验 |
| 文档与实际代码同步 | 多份历史报告仍停留在早期判断 | 容易误导后续排期 |

## 二、与 PRD / 架构规则对应关系

| 规则/目标 | 当前状态 | 结论 |
|----------|---------|------|
| 后端公共基类必须落地 | `common` 基座完整，绝大多数业务模型/视图沿用公共基座；`Organization` 属于循环依赖例外 | 基本达标 |
| 统一动态对象路由 | `/api/system/objects/{code}/` 已完整落地；但 `config/urls.py` 仍保留多个业务模块独立域路由 | 部分收敛 |
| 前端必须具备列表/表单/详情三基座 | `BaseListPage`、`BaseDetailPage` 已存在；`BaseFormPage` 缺位 | 未完全达标 |
| 动态工作区应成为业务主入口 | 资产、耗材、部分生命周期对象已切到 `/objects/:code`；财务、保险、租赁仍保留专页模式 | 部分达标 |
| 外部集成必须异步、可审计、幂等 | 财务推送任务、日志、重试、告警已具备；真实 ERP 适配仍存在模拟分支 | 部分达标 |
| 报告必须集中到 `docs/reports/` | 根目录仍有多份总结/修复报告 | 未达标 |

## 三、规范遵循验证

| 规范项 | 状态 | 说明 |
|------|------|------|
| 多组织隔离 | ✅ | `BaseModel` + `TenantManager` + 请求组织解析已成体系 |
| 统一响应格式 | ✅ | `BaseResponse` 已存在，主要业务接口基本保持 `success/data/error` 结构 |
| 元数据驱动能力 | ✅ | `BusinessObject`、`FieldDefinition`、`PageLayout`、runtime/layout/object router 已成主干 |
| 公共表单基座 | ⚠️ | 动态表单可用，但文档要求的 `BaseFormPage` 未真正落地 |
| 模块收敛度 | ⚠️ | 动态工作区与专属页面并存，形成“混合架构” |
| 报告治理 | ❌ | 根目录存在 `BULK_QR_FIX_SUMMARY.md` 等 7 份以上游离报告 |
| 环境可验证性 | ❌ | 当前工作区缺少后端/前端依赖，无法直接完成构建级验证 |

## 四、核心判断

### 4.1 项目当前所处阶段

GZEAMS 已经不是“从 0 到 1”的原型期，而是“平台能力已成型、需要架构收敛和业务闭环”的阶段。

### 4.2 当前最主要的风险

当前最大风险不是“功能没有”，而是“同一类能力用两套方式维护”：

1. 动态对象工作区已成熟，但仍有一批专页继续独立演进。
2. 文档规定存在 `BaseFormPage`，代码里却没有同名基座组件。
3. 历史 PRD / 报告对现状判断偏旧，容易继续推动错误优先级。

### 4.3 推荐的下一阶段方向

优先启动“业务工作区收敛 Phase 1”，先补齐平台一致性，再继续扩新模块。

推荐原因：

1. 与项目“元数据驱动低代码 + 统一对象路由”的核心定位一致。
2. 能同时消化前端基座缺口、专页重复开发和动态运行时契约分裂问题。
3. 以财务模块作为试点最合适，现有异步推送、日志、详情行为已具备迁移条件。

## 五、优先级建议

| 优先级 | 建议项 | 原因 |
|------|------|------|
| P0 | 业务工作区收敛 Phase 1 | 先统一工作区、表单基座、专页扩展机制，再扩业务域 |
| P1 | 资产项目管理（Phase 7.2） | 业务价值高，且依赖的资产/组织/工作流基础已具备 |
| P2 | 资产标签系统（Phase 7.3） | 能直接增强筛选、统计、后续智能搜索效果 |
| P3 | 智能搜索增强（Phase 7.4） | 当前已有全局搜索雏形，待标签和工作区统一后再深化更稳妥 |
| P3 | 文档与报告治理 | 根目录报告归档、README 索引更新、建立验证基线 |

## 六、关键证据文件清单

| 文件 | 行数 | 观察点 |
|------|------|------|
| `backend/apps/common/models.py` | 136 | 多组织 + 软删除 + 审计基座 |
| `backend/apps/common/serializers/base.py` | 156 | 公共字段与引用归一化 |
| `backend/apps/common/viewsets/base.py` | 497 | 组织隔离、软删除、批量操作 |
| `backend/apps/system/urls.py` | 145 | 动态对象统一入口定义 |
| `backend/config/urls.py` | 78 | 仍保留多个业务域独立路由 |
| `backend/apps/system/viewsets/object_router.py` | 3,173 | 动态对象运行时核心 |
| `frontend/src/api/dynamic.ts` | 807 | 前端统一对象 API 客户端 |
| `frontend/src/views/dynamic/DynamicListPage.vue` | 500 | 动态对象列表工作区 |
| `frontend/src/views/dynamic/workspace/useDynamicFormController.ts` | 201 | 动态表单数据/提交流程 |
| `frontend/src/views/dynamic/workspace/useDynamicDetailController.ts` | 143 | 动态详情与关系导航 |
| `frontend/src/router/index.ts` | 627 | `/objects/:code` 与 legacy alias 并存 |
| `frontend/src/components/common/BaseDetailPage.vue` | 781 | 详情基座已存在 |
| `backend/apps/organizations/models.py` | 676 | 组织模型为 BaseModel 例外 |
| `backend/apps/organizations/viewsets/organization.py` | 652 | 组织管理仍走专属 ViewSet |
| `backend/apps/finance/tasks.py` | 404 | 财务推送异步化、日志、重试 |
| `frontend/src/views/finance/VoucherList.vue` | 459 | 财务仍为专页模式 |
| `frontend/src/views/finance/VoucherDetail.vue` | 414 | 财务详情行为可迁移到统一工作区 |

## 七、后续建议

1. 立即按推荐优先级启动“业务工作区收敛 Phase 1”PRD 评审与任务拆分。
2. 在进入新功能开发前，先补齐 `BaseFormPage` 与统一工作区扩展机制。
3. 将根目录游离报告逐步迁移到 `docs/reports/`，避免后续分析继续被旧文档干扰。
