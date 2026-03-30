# 工作流 SLA 业务嵌入实施计划

## 1. 计划信息

- 关联 PRD: `docs/prd/prd-business-closed-loop-optimization-roadmap-2026-03-26.md`
- 对应子能力: `workflow_sla_business_embedding`
- 计划版本: `v1.0`
- 日期: `2026-03-26`
- 实施策略: `先打通对象与 SLA 绑定，再嵌入详情页和工作台，最后形成催办与瓶颈治理闭环`

## 2. 现状判断

当前工作流域已经具备 SLA 能力，但仍以流程中心视角为主，业务对象视角不足。

现状依据:

1. 后端已具备 SLA 判定、超时、升级、瓶颈统计:
   - `backend/apps/workflows/services/sla_service.py`
2. 工作流实例已具备业务对象绑定字段:
   - `backend/apps/workflows/models/workflow_instance.py`
   - 通过 `business_object_code` 与 `business_id` 绑定业务对象
3. 工作流通知已支持超时通知:
   - `backend/apps/workflows/services/notifications.py`
4. 前端当前主要通过审批中心承载:
   - `frontend/src/views/workflow/MyApprovals.vue`
5. 动态详情页尚未原生展示对象级 SLA 摘要:
   - `frontend/src/views/dynamic/DynamicDetailPage.vue`

结论:

1. 技术底座已具备，缺的是“把 workflow SLA 投影到业务对象界面”。
2. 这项能力应作为所有长链路对象的通用增强，而不是某个工作流页面功能。

## 3. 实施原则

1. SLA 数据源以工作流实例和任务为准，业务页面只消费聚合结果。
2. SLA 状态必须进入对象上下文，用户在详情页就能看到是否超时和谁负责。
3. 超时、升级、催办既要出现在审批中心，也要出现在业务工作台。
4. 不为 SLA 新增独立页面壳，优先复用对象工作台、列表和详情页。
5. 管理类分析以统一对象绑定和统一 SLA 状态语义为前提。

## 4. 分阶段执行

## Phase 0: 对象绑定与状态语义冻结

### 目标

冻结 SLA 在对象视角下的标准输出，避免不同对象各自解释。

### 任务

1. 冻结对象级 SLA 返回结构:
   - `status`
   - `dueDate`
   - `remainingHours`
   - `hoursOverdue`
   - `isEscalated`
   - `assignee`
   - `currentNode`
   - `instanceId`
2. 冻结 SLA 状态语义:
   - `within_sla`
   - `approaching_sla`
   - `overdue`
   - `escalated`
   - `completed`
   - `unknown`
3. 冻结业务工作台队列语义:
   - `approaching_sla`
   - `overdue`
   - `escalated`
4. 冻结催办与升级动作的权限边界。

### 验收

1. 业务对象与工作流实例的绑定查找规则明确。
2. SLA 输出结构与状态语义冻结。

建议工期: `1 人天`

---

## Phase 1: 后端对象级 SLA 聚合接口

### 目标

让对象路由可以直接返回对象当前的 SLA 摘要和待处理任务信息。

### 任务

1. 扩展 SLA 服务:
   - `backend/apps/workflows/services/sla_service.py`
   - 增加对象级聚合入口，而不仅是 task/instance 视角
2. 新增对象绑定查询服务:
   - `backend/apps/workflows/services/object_sla_binding_service.py`
   - 基于 `business_object_code` + `business_id` 查找关联实例与活动任务
3. 在对象路由新增:
   - `GET /api/system/objects/{code}/{id}/sla/`
4. 在工作台队列中支持:
   - 即将超时
   - 已超时
   - 已升级
5. 对接通知:
   - 超时催办
   - 升级通知

### 涉及模块

1. `backend/apps/workflows/services/sla_service.py`
2. `backend/apps/workflows/services/notifications.py`
3. `backend/apps/system/viewsets/object_router.py`
4. `backend/apps/system/services/`
   - 如需新增 SLA 聚合适配服务

### 交付物

1. 对象级 SLA 接口
2. 对象级 SLA 绑定服务
3. 超时/升级状态统一输出

### 验收

1. 任一挂接工作流的对象都能查询到当前 SLA 状态。
2. 没有工作流实例的对象返回稳定空结构，而不是报错。
3. `approaching_sla`、`overdue`、`escalated` 状态可被工作台复用。

建议工期: `2-3 人天`

---

## Phase 2: 催办、升级与对象动作联动

### 目标

把 SLA 从“只读状态”升级为“可运营动作”。

### 任务

1. 补充对象级推荐动作:
   - `remind_assignee`
   - `escalate_task`
   - `reassign_task` 如授权允许
2. 将 SLA 动作并入统一对象动作协议，而不是新建单独按钮系统。
3. 明确操作日志:
   - 谁催办
   - 催办对象
   - 催办时间
   - 是否升级
4. 与通知服务打通:
   - 站内通知
   - 邮件/其他外发通道如已启用

### 交付物

1. SLA 运营动作定义
2. 催办/升级/转办的后端执行入口
3. 动作执行日志与通知联动

### 验收

1. 对象详情页可以发起催办或升级动作。
2. 动作执行后能在通知和日志中看到结果。

建议工期: `2 人天`

---

## Phase 3: 前端详情页与工作台嵌入

### 目标

让用户在业务对象界面直接看到 SLA 风险，而不必先进入工作流中心。

### 任务

1. 新增公共组件:
   - `frontend/src/components/common/SlaIndicatorBar.vue`
   - `frontend/src/components/common/SlaStatusCard.vue`
2. 在动态详情页接入:
   - `frontend/src/views/dynamic/DynamicDetailPage.vue`
3. 在工作台摘要卡与队列面板接入:
   - 即将超时数
   - 已超时数
   - 已升级数
4. 在列表页或 workspace hero 增加状态徽标入口。
5. 保证 i18n 与空态文案齐全。

### 交付物

1. SLA 指示条
2. SLA 状态卡
3. 动态详情页嵌入
4. 工作台风险队列接入

### 验收

1. 详情页能直接看到 SLA 状态、责任人、剩余时间。
2. 工作台可按即将超时、已超时、已升级快速进入队列。

建议工期: `3-4 人天`

---

## Phase 4: 管理分析与瓶颈输出

### 目标

把现有瓶颈统计从工作流后台能力升级为经营视角分析。

### 任务

1. 基于现有 `get_bottleneck_report()` 输出对象维度分析。
2. 在工作台摘要或后续驾驶舱中输出:
   - 平均闭环时长
   - 超时率
   - 节点瓶颈排行
   - 责任人堆积排行
3. 明确对象维度埋点与统计窗口。

### 交付物

1. 对象维度瓶颈报表接口
2. SLA 管理分析数据结构

### 验收

1. 管理端可识别高风险对象域和高风险节点。
2. SLA 风险不再只停留在审批列表页面。

建议工期: `2-3 人天`

## 5. 代码级任务清单

### 后端

1. `backend/apps/workflows/services/sla_service.py`
2. `backend/apps/workflows/services/notifications.py`
3. `backend/apps/workflows/models/workflow_instance.py`
   - 如需补索引或辅助字段
4. `backend/apps/system/viewsets/object_router.py`
5. `backend/apps/system/services/`
   - 新增对象级 SLA 聚合与队列服务

### 前端

1. `frontend/src/views/dynamic/DynamicDetailPage.vue`
2. `frontend/src/api/dynamic.ts`
3. `frontend/src/components/common/`
   - 新增 `SlaIndicatorBar.vue`
   - 新增 `SlaStatusCard.vue`
4. `frontend/src/views/workflow/MyApprovals.vue`
   - 与对象工作台语义对齐
5. `frontend/src/composables/`
   - 新增对象级 SLA 查询 composable

## 6. 测试计划

### 6.1 后端

1. 对象无实例时 SLA 接口返回空结构
2. 对象有活动任务时返回正确状态
3. `approaching_sla`、`overdue`、`escalated` 转换正确
4. 催办和升级动作权限与状态校验正确

### 6.2 前端

1. SLA 指示条渲染
2. 超时与升级状态样式映射
3. 动态详情页在有无 SLA 数据下的兼容行为
4. 工作台 SLA 队列筛选与跳转

## 7. 风险控制

| 风险 | 说明 | 控制策略 |
|------|------|---------|
| 业务对象与工作流实例绑定不稳定 | 对象查不到实例或查到多个实例 | 先冻结查找规则，必要时补唯一性与排序规则 |
| SLA 状态定义重复 | 页面层再次自行定义超时逻辑 | 一律通过后端统一输出 |
| 只做显示不做运营动作 | 无法推动闭环处理 | Phase 2 必须补催办与升级动作 |
| 审批中心和业务页面语义不一致 | 用户看到两套状态 | 统一状态字典和前端映射 |

## 8. 完成标准

1. 挂接工作流的业务对象都能在详情页看到 SLA 状态。
2. 工作台可以按 SLA 风险组织待处理队列。
3. 超时、升级、催办进入对象闭环，而不是停留在审批中心。
