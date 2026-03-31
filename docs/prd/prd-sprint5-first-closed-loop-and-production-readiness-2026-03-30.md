# GZEAMS Sprint 5 PRD — InventoryTask 闭环工作台试点

## 文档信息

| 字段 | 说明 |
|------|------|
| 功能名称 | InventoryTask 闭环工作台试点 |
| 功能代码 | `sprint5_inventory_task_workbench_pilot` |
| 文档版本 | 2.0.0 |
| 创建日期 | 2026-03-30 |
| 更新日期 | 2026-03-31 |
| 维护人 | Codex |
| 审核状态 | 待审核 |
| 关联文档 | `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md` / `docs/plans/common_base_features/99_reference/prd_writing_guide.md` |

---

## 1. 功能概述与业务场景

### 1.1 背景

截至 2026-03-31，Sprint 5 原始草稿中列出的若干“待实施项”已经在仓库中落地，包括：

| 项 | 当前基线 |
|----|---------|
| `AssetPickup` 工作流集成 | 已继承 `WorkflowStatusMixin` |
| 开发 Docker 启动方式 | 已使用 Gunicorn |
| DRF 限流 | `REST_FRAMEWORK` 已配置 throttle |
| Dashboard 聚合接口 | `/api/dashboard/summary/` 已存在 |
| Dashboard 页面 | 已完成增强版页面，不再是最小占位页 |

因此 Sprint 5 不应继续围绕上述已完成项重复立项，而应回到当前路线图定义的核心目标：将已有业务对象升级为“工作台 + 队列 + 动作 + 结案”的闭环经营界面。

### 1.2 当前问题

`InventoryTask` 已具备以下闭环基础：

| 能力 | 当前状态 |
|------|---------|
| 统一动态对象详情页 | 已可显示 runtime workbench 区域 |
| workbench summary / queue / exception / closure | 已在 `menu_config` 中配置 |
| 差异汇总 | `difference_summary` 已进入任务详情序列化 |
| 执行人进度数据 | `/api/inventory/tasks/{id}/executors/progress/` 已提供 |
| 对象级 SLA 接口 | `/api/system/objects/{code}/{id}/sla/` 已提供 |

但当前仍存在两个关键缺口：

1. `InventoryTask` 详情页虽有 summary / queue / closure，但缺少执行层面板，无法直接查看各执行人的负载与扫描进度。
2. `InventoryTask` 的 workbench 尚未配置 `sla_indicators`，对象已具备 SLA API 能力，但详情页无法直接展示 workflow SLA 状态。

### 1.3 本期目标

本 Sprint 以 `InventoryTask` 为试点，完成第一批真正对齐路线图的闭环工作台增强：

1. 在统一动态详情页中，为 `InventoryTask` 增加执行人进度面板。
2. 将对象级 workflow SLA 正式接入 `InventoryTask` workbench。
3. 将 Sprint 5 文档基线修正到当前真实代码状态，避免重复开发已完成内容。

### 1.4 范围内

1. 修订 Sprint 5 PRD 和实施计划。
2. 调整 `InventoryTask` 的 workbench runtime 配置。
3. 新增 `InventoryTask` 执行人进度面板组件。
4. 为 `InventoryTask` 配置 SLA 指示器。
5. 补充前后端回归测试。

### 1.5 不在本期范围

1. 不新增独立的 InventoryTask 专属静态详情页。
2. 不重做 `AssignmentPanel.vue` 的完整分配能力整合。
3. 不在本期引入新的 `InventoryTask` workflow 模型字段。
4. 不处理全部前端 TypeScript 遗留问题；该项单独跟踪。

### 1.6 非目标

1. 不重构动态对象路由架构。
2. 不新增散落的专用后端 URL 配置。
3. 不把 Dashboard 继续作为 Sprint 5 主目标。

---

## 2. 用户角色与权限

| 用户角色 | 使用场景 | 核心需求 |
|---------|---------|----------|
| 盘点管理员 | 查看任务总体推进、差异积压和结案阻塞 | 能在任务详情中直接掌握执行态势 |
| 盘点执行人 | 查看自己是否在执行队列中、当前完成进度 | 能确认执行责任和推进状态 |
| 审批人/主管 | 关注任务是否进入 workflow，是否接近 SLA | 能快速识别超时风险 |
| 系统管理员 | 维护对象 runtime/workbench 配置 | 能通过统一配置扩展工作台 |

### 2.1 权限矩阵

| 功能 | 盘点管理员 | 执行人 | 审批人/主管 | 系统管理员 |
|------|-----------|--------|-------------|-----------|
| 查看任务执行人进度面板 | ✅ | ✅ | ✅ | ✅ |
| 查看 SLA 状态 | ✅ | 视授权 | ✅ | ✅ |
| 使用任务级动作（开始/完成/刷新统计） | ✅ | 视授权 | ❌ | ✅ |
| 配置 workbench runtime | ❌ | ❌ | ❌ | ✅ |

---

## 3. 公共模型引用声明

### 3.1 后端公共模型引用

| 组件类型 | 基类/能力 | 引用路径 | 自动获得功能 |
|---------|-----------|---------|-------------|
| Model | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化 |
| ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 统一 CRUD 方法 |
| Dynamic Object Router | `ObjectRouterViewSet` | `apps.system.viewsets.object_router.ObjectRouterViewSet` | runtime、SLA、统一对象动作 |

### 3.2 前端公共组件引用

| 组件类型 | 组件 | 路径 | 说明 |
|---------|------|------|------|
| 统一详情页 | `DynamicDetailPage` | `frontend/src/views/dynamic/DynamicDetailPage.vue` | 承载 workbench 扩展区 |
| 工作台面板宿主 | `ObjectWorkbenchPanelHost` | `frontend/src/components/common/ObjectWorkbenchPanelHost.vue` | 渲染 detail panels |
| SLA 面板 | `SlaIndicatorBar` | `frontend/src/components/common/SlaIndicatorBar.vue` | 渲染对象 SLA |
| 结案面板 | `ClosureStatusPanel` | `frontend/src/components/common/ClosureStatusPanel.vue` | 渲染闭环状态 |
| 新增面板 | `InventoryTaskExecutorProgressPanel` | `frontend/src/components/inventory/InventoryTaskExecutorProgressPanel.vue` | 展示执行人进度 |

---

## 4. 数据模型设计

### 4.1 设计原则

1. 不新增 `InventoryTask` 表字段。
2. 继续复用已有 `difference_summary`、`executors`、`executor progress` 和对象级 SLA 数据。
3. 闭环能力优先通过 runtime workbench 配置补齐，不创建额外业务对象。

### 4.2 Workbench Runtime 增量

本期对 `InventoryTask` workbench 补充以下配置：

| 配置项 | 类型 | 说明 |
|------|------|------|
| `workbench.detail_panels` | array | 新增执行人进度面板定义 |
| `workbench.sla_indicators` | array | 新增 workflow SLA 指示器定义 |

### 4.3 详情页数据来源

| 数据块 | 来源 | 说明 |
|------|------|------|
| Summary Cards | `InventoryTaskDetailSerializer` | 直接读取任务详情字段与 `difference_summary` |
| Queue / Exception | runtime config + 任务详情 | 仅使用现有字段映射 |
| Closure | `difference_summary` | 显示当前闭环阶段、阻塞项、完成度 |
| SLA | `/api/system/objects/InventoryTask/{id}/sla/` | 复用对象级 workflow SLA 能力 |
| 执行人面板 | `/api/inventory/tasks/{id}/executors/` + `/executors/progress/` | 聚合执行人、扫描量、异常量、完成度 |

---

## 5. API 接口设计

### 5.1 统一原则

1. 不新增独立业务对象 URL 配置。
2. `InventoryTask` 仍以动态对象详情作为主入口。
3. 工作台面板仅消费已有接口。

### 5.2 本期使用的接口

| 方法 | 端点 | 用途 |
|------|------|------|
| GET | `/api/system/objects/InventoryTask/{id}/` | 加载任务详情与 `difference_summary` |
| GET | `/api/system/objects/InventoryTask/runtime/` | 加载 workbench runtime 配置 |
| GET | `/api/system/objects/InventoryTask/{id}/sla/` | 获取对象级 workflow SLA 摘要 |
| GET | `/api/inventory/tasks/{id}/executors/` | 获取任务执行人列表 |
| GET | `/api/inventory/tasks/{id}/executors/progress/` | 获取执行人进度 |

### 5.3 本期不新增接口

| 能力 | 说明 |
|------|------|
| `InventoryTask` 专属 `workbench/summary/` | 暂不新增，现阶段由详情字段直出即可支撑 |
| `closure/` 独立端点 | 暂不新增，继续复用 `difference_summary` |
| 分配编辑专属 panel API | 暂不新增，继续复用现有 executors 端点 |

### 5.4 错误码

沿用平台统一错误码：

| 错误码 | HTTP 状态 | 说明 |
|--------|-----------|------|
| `VALIDATION_ERROR` | 400 | 参数不合法 |
| `NOT_FOUND` | 404 | 任务或资源不存在 |
| `PERMISSION_DENIED` | 403 | 无查看或执行权限 |
| `SERVER_ERROR` | 500 | 后端聚合数据失败 |

---

## 6. 前端组件设计

### 6.1 统一详情页增强方式

`InventoryTask` 不新建专属页面，继续使用 `DynamicDetailPage` 的 workbench 扩展区：

| 区块 | 组件 | 数据来源 |
|------|------|---------|
| Summary | `WorkbenchSummaryCards` | 任务详情字段 |
| Queue / Exception | `WorkbenchQueuePanel` | runtime + 任务详情字段 |
| Closure | `ClosureStatusPanel` | `difference_summary` |
| SLA | `SlaIndicatorBar` | runtime + object SLA API |
| 执行人进度 | `InventoryTaskExecutorProgressPanel` | executors + executor progress API |

### 6.2 新增执行人进度面板

| 项 | 说明 |
|----|------|
| 面板类型 | `detail_panel` |
| 组件编码 | `inventory-task-executor-progress` |
| 展示内容 | 执行人数、累计扫描、累计异常、每位执行人的进度卡片 |
| 交互 | 支持局部刷新，不跳出当前详情页 |
| 空态 | 无执行人时显示统一空态 |
| 异常态 | 使用内联告警，避免详情页自动弹全局错误消息 |

### 6.3 SLA 指示器

| 项 | 说明 |
|----|------|
| 数据来源 | `objectSla` |
| 展示内容 | SLA 状态、截止时间、当前责任人 |
| 可见条件 | `InventoryTask` 进入流程后自动显示；无实例时不显示 |

---

## 7. 测试用例

### 7.1 后端测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-B1 | `InventoryTask` menu config 含执行人面板配置 | `detail_panels` 返回新增组件编码 |
| TC-B2 | `InventoryTask` menu config 含 SLA indicator 配置 | `sla_indicators` 非空且字段正确 |
| TC-B3 | 对象 runtime 输出 workbench 时包含上述配置 | 动态 runtime 可消费 |

### 7.2 前端测试

| 编号 | 测试点 | 预期 |
|------|--------|------|
| TC-F1 | `ObjectWorkbenchPanelHost` 能渲染 `inventory-task-executor-progress` | detail panel 正常挂载 |
| TC-F2 | 执行人进度面板能合并 executors 与 progress 数据 | 卡片显示人数、扫描数和异常数 |
| TC-F3 | 面板刷新时重新请求数据 | `panelRefreshVersion` 变更后重新加载 |
| TC-F4 | 无 workflow 实例时 SLA 指示器不报错 | 页面正常渲染 |

### 7.3 集成验证

| 编号 | 场景 | 预期 |
|------|------|------|
| TC-I1 | 打开 `InventoryTask` 详情页 | summary / queue / closure / panel 正常展示 |
| TC-I2 | 已存在 workflow instance 的任务详情页 | SLA 状态正常显示 |
| TC-I3 | 已分配执行人的任务详情页 | 执行人进度卡片正常显示 |

---

## 8. 验收标准

| 编号 | 验收项 | 标准 |
|------|--------|------|
| AC-1 | Sprint 5 文档与当前仓库状态一致 | 不再把已完成项重复列为待实施 |
| AC-2 | `InventoryTask` 详情页出现执行人进度面板 | 至少能显示空态、加载态、正常态 |
| AC-3 | `InventoryTask` workbench 已接入对象级 SLA | 有实例时显示 SLA 状态与责任人 |
| AC-4 | 前后端测试通过 | 目标测试集零失败 |

---

## 9. 后续建议

1. 下一阶段可继续为 `InventoryTask` 增加独立的 closure detail panel，而非仅依赖 `difference_summary`。
2. 若业务确认盘点任务需要正式审批流，可再评估 `InventoryTask` 与 workflow 的业务绑定策略。
3. `InventoryFollowUp` 可作为下一批 workbench 纵向深化对象，补齐提醒、催办和结案联动。
