# SPRINT2_CODE_COMPLIANCE_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-24 |
| 涉及阶段 | Sprint 2 |
| 作者/Agent | Codex |

## 一、实施概述
- 审查范围：7 个 Sprint 2 文件，覆盖后端服务、前端样式与组件、E2E 测试。
- 代码总量：2,887 行。
- 总体质量评分：4/10。
- 结论：实现思路清晰，但当前版本存在多处接口契约漂移、未接线实现、类型系统失配和测试有效性不足的问题，尚未达到可稳定交付状态。

### 审查文件清单
| 文件 | 行数 | 结论 |
|------|------|------|
| `backend/apps/workflows/services/notification_service.py` | 390 | 运行时契约错误较多，且未完成接线 |
| `backend/apps/common/services/redis_service.py` | 403 | 缓存策略有组织隔离和失效一致性风险 |
| `backend/apps/workflows/services/sla_service.py` | 407 | 核心状态判断与模型字段引用错误 |
| `frontend/src/styles/workflow.scss` | 605 | 样式量大，但集成度低且与现有组件样式重复 |
| `frontend/src/composables/useWorkflowDesigner.ts` | 371 | TypeScript 编译失败，当前不可用 |
| `frontend/src/components/workflow/PermissionBadge.vue` | 207 | 组件 API 未落地，且存在编译错误 |
| `backend/apps/workflows/tests/test_e2e_complete_workflow.py` | 504 | 覆盖面看似完整，但多处断言和路径不具备真实验证价值 |

### 验证记录
- `python3 -m py_compile ...`：通过，仅验证 Python 语法，不覆盖 Django 运行时行为。
- `python3 -m pytest backend/apps/workflows/tests/test_e2e_complete_workflow.py -q`：无法执行，当前环境缺少 `pytest` 模块。
- `cd frontend && npx vue-tsc --noEmit --pretty false`：失败，目标文件包含真实 TypeScript 错误。
- `cd frontend && npx eslint src/composables/useWorkflowDesigner.ts src/components/workflow/PermissionBadge.vue`：通过，但仅给出 warning，未捕获关键运行时/契约问题。

## 二、与 PRD 对应关系
| PRD / 工程要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 工作流通知应可按事件触发并输出有效通知 | 不符合 | `backend/apps/workflows/services/notification_service.py` |
| 工作流 SLA 监控应能正确统计超时、瓶颈、合规率 | 不符合 | `backend/apps/workflows/services/sla_service.py` |
| 前端工作流设计器应提供可编译、可调用的权限配置能力 | 不符合 | `frontend/src/composables/useWorkflowDesigner.ts` |
| 权限徽标组件应支持可复用 UI API，并遵守 i18n 规范 | 部分符合 | `frontend/src/components/workflow/PermissionBadge.vue` |
| 工作流样式应与现有页面实际集成，避免重复定义 | 部分符合 | `frontend/src/styles/workflow.scss` |
| E2E 测试应真实覆盖主流程、异常流和接口回归 | 部分符合 | `backend/apps/workflows/tests/test_e2e_complete_workflow.py` |
| 多组织隔离与统一行为模式不得被缓存/统计逻辑破坏 | 不符合 | `backend/apps/common/services/redis_service.py`, `backend/apps/workflows/services/sla_service.py` |

## 三、关键问题

### Critical
1. `frontend/src/composables/useWorkflowDesigner.ts` 当前无法通过 TypeScript 编译，且与现有 API/Store/Composable 契约不一致。
   - 直接引用未导入的 `metadataApi` 和 `formPermissionsApi`。
   - 以错误方式调用 `useFieldPermissions()`，该 composable 需要 `Ref<NodeFormPermissions>` 参数。
   - 访问不存在的 `workflowStore.currentWorkflow`。
   - 将 `FieldPermissionLevel` 声明成接口映射，而不是联合类型，导致后续 switch 和赋值全部失真。
   - 这意味着该 composable 即使被引入，也会在构建阶段或运行时失败。

2. `backend/apps/workflows/services/notification_service.py` 和 `backend/apps/workflows/services/sla_service.py` 以错误的模型字段和状态枚举为基础实现，核心逻辑不可正确执行。
   - 两个服务均大量使用不存在的 `task.workflow_instance`、`workflow_instance.workflow_definition`。
   - `notification_service.py` 读取不存在的 `task.comment`，并按不存在的 `status='completed'` 过滤任务。
   - `sla_service.py` 同样按不存在的 `status='completed'` 聚合任务，且将已完成任务状态误判逻辑建立在 `completed` 上，而真实模型完成态为 `approved/rejected/returned`。
   - 这不是边角 bug，而是主路径契约错误。

3. `backend/apps/common/services/redis_service.py` 的缓存键和失效逻辑不满足多组织安全边界。
   - 工作流统计缓存键仅使用 `stats_type`，未带 `organization_id`，若未来启用缓存，极易发生跨组织统计串读。
   - `delete_pattern()` 使用 Redis `KEYS`，对生产 Redis 是阻塞式全量扫描。
   - Django cache fallback 不支持 pattern delete，但服务仍继续返回“已失效”语义，存在陈旧缓存风险。

### High
1. `backend/apps/workflows/tests/test_e2e_complete_workflow.py` 中多项测试并未真正验证业务行为。
   - “取消/撤回”测试直接改 `status` 并 `save()`，绕过引擎、信号和业务同步逻辑。
   - “错误恢复”测试对错误用户审批没有断言，注释还明确写了“可能成功”。
   - “by-business endpoint” 测试发起请求但刻意不校验响应。
   - 文件尾部还有 3 个 `pass` 占位测试。

2. `frontend/src/components/workflow/PermissionBadge.vue` 存在真实编译错误和未兑现 API。
   - `@element-plus/icons-vue` 中不存在 `Question` 导出，`vue-tsc` 已报错。
   - `size`、`showTooltip` props 已声明，但模板未真正使用。
   - 文案为硬编码英文，未遵循前端 i18n 规范。

3. Sprint 2 工作流增强代码整体接线不足。
   - `frontend/src/composables/useWorkflowDesigner.ts` 无任何调用点。
   - `frontend/src/components/workflow/PermissionBadge.vue` 无任何调用点。
   - `backend/apps/workflows/services/notification_service.py`、`backend/apps/common/services/redis_service.py` 未接入 `apps.workflows.apps.WorkflowsConfig.ready()` 的信号链路。
   - `notification_service.py` 引用的 `workflows/notifications/*.html` 模板在仓库中不存在。

## 四、文件级审查结论

### 1. `backend/apps/workflows/services/notification_service.py`
**Code organization and structure**
- 结构上分层清楚，事件类型配置集中在 `NOTIFICATION_TYPES`，接口可读性尚可。
- 但实现建立在错误模型字段之上，导致组织良好的外观掩盖了不可执行的内部契约。

**Error handling**
- `send_notification()`、`_send_email()` 均采用“记录日志并吞掉异常”的策略。
- 这适合非阻塞通知，但当前没有 error code、重试、降级记录或任务队列接入，排障信号太弱。

**Performance**
- 邮件发送同步执行，不符合项目“Async First Principle”。
- 大量通知场景下会阻塞业务事务或请求线程。

**Security**
- `_get_approval_link()` 直接拼接前端链接，没有签名/一次性 token/权限边界。
- 如链接被转发，仍完全依赖后端页面二次鉴权。

**Documentation quality**
- docstring 质量总体可以，但文档描述“supports multiple channels”明显超前于实际实现；push/in-app 仍是占位实现。

### 2. `backend/apps/common/services/redis_service.py`
**Code organization and structure**
- API 包装完整，key 生成与失效方法拆分合理。
- 但类名叫 `RedisService`，实际又承担 Django cache fallback 和业务语义失效，职责边界偏宽。

**Error handling**
- 失败时统一吞异常并返回布尔值，调用方难以区分“缓存未命中”和“缓存层故障”。

**Performance**
- `delete_pattern()` 使用 `keys(pattern)`，在 key 数量大时会阻塞 Redis。
- 工作流统计与用户任务缓存都没有批量或版本化失效策略，后续增长后会放大问题。

**Security**
- `workflow:stats:{type}` 未加入组织维度，违反多组织隔离预期。
- 若后台任务中线程上下文未注入组织，相关调用极易跨租户复用缓存。

**Best practice adherence**
- `on_task_assigned()` / `on_task_completed()` 使用不存在的 `task.assigned_to`，说明实现未与模型同步。

### 3. `backend/apps/workflows/services/sla_service.py`
**Code organization and structure**
- 服务目标明确，方法划分也合理。
- 但多个核心方法在状态枚举、模型路径、组织过滤假设上与当前模型脱节。

**Error handling**
- `_get_sla_hours_for_node()` 捕获所有异常后回退默认 SLA，会隐藏真实配置错误。

**Performance**
- `get_bottleneck_report()` 逐条遍历任务并逐节点再次查询 `WorkflowDefinition`，存在 N+1 风险。
- `get_sla_compliance_summary()` 全量 Python 循环统计，不适合作为高频仪表板查询。

**Security**
- 可选 `organization_id` 过滤不足以保证隔离；在没有线程上下文的后台任务中，`TenantManager` 会返回所有组织数据。

**Documentation quality**
- 文档说明清晰，但与真实状态机不一致，容易误导后续维护者继续沿用错误状态值。

### 4. `frontend/src/styles/workflow.scss`
**Code organization and structure**
- 样式拆成色板、mixins、组件区块，形式上清楚。
- 但该文件没有在 `frontend/src` 中被引用，且大量类名与 `ApprovalPanel.vue` 自带 scoped 样式重复，实际集成价值偏低。

**Performance**
- 全局 class 和重复样式并存，会增加后续维护与调试成本。

**Best practice adherence**
- 使用 Sass 变量而不是统一 design token / CSS variable，跨主题扩展性一般。
- 样式文件体量较大，但没有明确的消费入口，属于“实现了视觉层代码，但没有交付到页面”。

**Documentation quality**
- 注释清晰，命名一致，这是该文件的优点。

### 5. `frontend/src/composables/useWorkflowDesigner.ts`
**Code organization and structure**
- 想把权限读取、导入导出、节点状态和摘要汇总收敛到一个 composable，这个方向正确。
- 但当前文件同时存在契约错误、类型错误、未使用代码、错误缓存基线设计，实际不可用。

**Type safety**
- 当前是本次审查中最差的 TypeScript 文件。
- `selectedNode`、`getBusinessFieldValue()`、`FieldDefinition.defaultValue`、`validation` 等大量 `any`。
- `FieldPermissionLevel` 类型定义错误，直接破坏整个文件类型系统。

**Error handling**
- 全部通过 `console.error` 处理，未复用全局错误提示机制，违反前端统一交互标准。

**Performance**
- `setSelectedNode()` 每次选择审批节点都重新 `loadPermissions()`，没有去抖也没有“已加载即跳过”策略。
- `hasUnsavedChanges` 用对象引用比较嵌套权限对象，结果既不可靠，也会在后续修改中产生误报。

**Documentation quality**
- 注释数量足够，但内容和实际实现不一致，属于“文档覆盖了错误代码”。

### 6. `frontend/src/components/workflow/PermissionBadge.vue`
**Code organization and structure**
- 单文件组件结构小，容易阅读。
- 但模板、props、computed 之间没有闭环：`sizeClasses`、`showTooltip`、`color` 都未真正落地。

**Type safety**
- `vue-tsc` 已确认图标导入错误。

**Security / accessibility**
- 看起来可交互的 badge 使用 `cursor: pointer` 和 `focus-visible`，但根元素不可聚焦，键盘可访问性不足。

**Documentation quality**
- 英文注释清楚，但 tooltip 文案没有 i18n，和项目标准冲突。

### 7. `backend/apps/workflows/tests/test_e2e_complete_workflow.py`
**Code organization and structure**
- 文件按场景拆 test，阅读顺序合理。
- 但导入过多无用依赖，且后半段开始退化成“示意测试”而非可靠自动化用例。

**Error handling**
- 多个测试在失败路径上没有断言具体错误内容，无法为回归提供稳定诊断。

**Performance**
- 主要是测试代码，性能不是核心问题。

**Security**
- 未认证 API 调用、未设置组织上下文，无法验证权限和数据隔离要求。

**Documentation quality**
- 测试注释有助于理解意图，这是优点。
- 但注释中多次出现“if available”“implementation dependent”等措辞，说明测试目标未固化。

## 五、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| 英文代码注释 | 符合 | 目标文件中的代码注释基本为英文 |
| 前端 i18n 使用 | 不符合 | `PermissionBadge.vue` tooltip 使用硬编码英文 |
| Async First 原则 | 不符合 | `notification_service.py` 同步发送邮件 |
| 多组织隔离 | 不符合 | `redis_service.py` 缓存键无组织维度；`sla_service.py` 依赖可缺失的线程上下文 |
| 类型安全 | 不符合 | `useWorkflowDesigner.ts` 编译失败，存在错误类型声明 |
| 可执行测试 | 部分符合 | Python 语法可编译，但 pytest 环境缺失，且测试本身存在弱断言和占位用例 |
| 文档与实现一致性 | 不符合 | 多处 docstring/注释描述的行为与实际契约不一致 |

## 六、改进建议
1. 先修复模型契约漂移，再考虑功能完善。
   - 将 `workflow_instance` 统一替换为 `instance`，`workflow_definition` 统一替换为 `definition`，`assigned_to` 统一替换为 `assignee`。
   - 将任务完成态统一改为 `approved/rejected/returned`，不要再引入不存在的 `completed`。

2. 让前端设计器代码先达到“可编译、可引用、可落地”。
   - 正确导入现有 API：系统字段定义应使用 `@/api/system`，工作流表单权限应基于真实 `/workflows/definitions/{id}/form-permissions/` 客户端封装。
   - 复用已有 `NodeFormPermissions` / `FieldPermissionLevel` 类型，不要在文件末尾重新定义一套不兼容类型。
   - 删除无调用点的死代码，或者尽快接入真实页面。

3. 把通知和缓存增强接入实际运行链路。
   - 在工作流 app 的 signal 处理链中接入通知和缓存失效。
   - 通知发送、超时提醒、统计重算应转为 Celery 异步任务。
   - 为统计缓存加入组织维度和版本化失效策略。

4. 让测试变成真正的质量门，而不是示意脚本。
   - 禁止通过直接改 `status` 伪造取消场景。
   - 所有失败场景都要断言 `success`、错误消息和副作用。
   - 删除 `pass` 占位测试，或者标记 `skip` 并写清阻塞条件。

5. 收敛重复 UI 资产。
   - 如果 `workflow.scss` 是全局设计稿，请在真实入口导入并删掉 `ApprovalPanel.vue` 重复样式。
   - 如果最终以组件内 scoped 样式为准，应删除未集成的全局样式和未使用组件。

## 七、已遵循的最佳实践
- 目标后端服务和前端文件大多有清晰的 docstring / 注释，意图表达比平均水平好。
- `notification_service.py`、`redis_service.py`、`sla_service.py` 都采用了服务对象封装，避免把流程逻辑散落到视图层。
- `workflow.scss` 使用变量和 mixin 抽象重复样式，说明作者具备样式复用意识。
- `test_e2e_complete_workflow.py` 使用真实流程图数据搭建场景，至少在测试意图上覆盖了主路径、条件分支和异常路径。

## 八、后续建议
- 建议以“先修契约、再接线、最后补测试”的顺序处理，而不是先做 UI polish。
- 优先级建议：
  1. 修复 `useWorkflowDesigner.ts` 和 `PermissionBadge.vue` 编译错误。
  2. 修复 `notification_service.py`、`sla_service.py`、`redis_service.py` 的模型字段/状态常量问题。
  3. 将通知与缓存服务接入信号或 Celery。
  4. 重写 `test_e2e_complete_workflow.py` 中的伪 E2E 场景。
