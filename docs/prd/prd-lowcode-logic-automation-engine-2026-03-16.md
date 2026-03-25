# PRD: 低代码逻辑自动化与数据安全引擎 (Architecture Evolution - Next Phase)

> **版本**: v2.0 (Revised)
> **日期**: 2026-03-16
> **作者**: System Architect
> **状态**: 待评审
> **前置依赖**: 主从聚合架构 (Master-Detail)、生命周期闭环体系

---

## 1. 背景与目标

### 1.1 背景（为什么做？）

在过去的高频迭代中，NEWSEAMS 平台已经完成了**元数据基建**的三个核心跃迁：

1. **模型元数据化**：BusinessObject + FieldDefinition，支撑了动态表单与列表。
2. **布局元数据化**：WysiwygLayoutDesigner + PageLayout，实现了双态布局与可视化设计。
3. **关系与流程元数据化**：Master-Detail 协议打通了主从表内聚展示，Lifecycle Orchestrator 打通了跨对象协同流转。

### 1.2 现状盘点（我们已经有什么？）

> **重要：** 以下资产已存在于代码库中，本 PRD 的核心策略是 **"整合 → 贯通 → 增强"**，而非重新研发。

#### 已有后端资产

| 资产 | 位置 | 能力 | 缺口 |
|------|------|------|------|
| **BusinessRule 模型** | `apps/system/models.py` L2446 | rule_code/condition(JSON Logic)/action/trigger_events/priority/error_message，含 `RuleExecution` 审计表 | 未与 `DynamicDataService` CRUD 流程集成 |
| **RuleEngine 服务** | `apps/system/services/rule_engine.py` | JSON Logic 求值、validation/visibility/computed/linkage 四类规则、执行日志记录 | 仅通过独立 API 调用，未嵌入数据保存管线 |
| **BusinessRule API** | `apps/system/viewsets/business_rule.py` | CRUD + `evaluate/{code}/` + `validate/{code}/` + `visibility/{code}/`，含 `RuleExecutionViewSet` | 已完整 |
| **Formula 计算** | `DynamicDataService._calculate_formulas()` | 基于 `simpleeval` 的字段间公式 `{field1} + {field2}` | 无 Rollup 汇总、无依赖拓扑排序 |
| **DataPermission** | `apps/permissions/models/data_permission.py` | 6 种 scope（all/self/self_dept/self_and_sub/specified/custom）+ `apply_to_queryset()` | 未自动注入 `DynamicDataService.query()` |
| **PermissionInheritance** | `apps/permissions/models/permission_inheritance.py` | 角色间权限继承（full/partial/exclude） + 递归查询父/子角色 | 未与 DataPermission 联动 |
| **inherit_permissions 标记** | `BusinessObject.inherit_permissions` | Master-Detail 权限继承声明 | 从未在查询层实现穿透 |

#### 已有前端资产

| 资产 | 位置 | 能力 | 缺口 |
|------|------|------|------|
| **RuleDesigner.vue** | `components/designer/RuleDesigner.vue` | 规则表单（含 ConditionBuilder + ActionConfigurator）、测试对话框 | 已完整可用 |
| **BusinessRuleList.vue** | `views/system/BusinessRuleList.vue` | 规则列表管理页 | 已完整可用 |
| **businessRules.ts API** | `api/businessRules.ts` | evaluateRules/validateOnly/getVisibility 等完整 API Client | **未在 DynamicForm 保存流程中调用** |

### 1.3 目标定位

对标 Salesforce，补齐元数据驱动的最后两块拼图：**声明式业务逻辑引擎的贯通** 和 **企业级数据共享引擎的贯通**。

核心策略为 **"三步走"**：
1. **贯通**：将已有的 RuleEngine/DataPermission 嵌入 DynamicDataService 的 CRUD 管线
2. **增强**：在已有基础上扩展 Rollup Summary 和表达式函数库
3. **治理**：统一表达式引擎，消除 simpleeval 与 JSON Logic 双轨并行

### 1.4 技术栈确认

| 组件 | 技术 |
|------|------|
| 数据库 | PostgreSQL（支持 JSONB、行级锁、窗口函数） |
| 缓存 | Redis（django-redis） |
| 异步队列 | Celery + Redis Broker |
| 表达式引擎 | JSON Logic（统一前后端），simpleeval（仅保留用于 Formula 计算的向后兼容） |

---

## 2. 演进赛道蓝图 (Strategic Tracks)

### 2.1 Track A: 校验规则引擎贯通 (Validation Rule Integration)

**现状**: `RuleEngine` + `BusinessRule` + `BusinessRuleViewSet` 已完整实现，但仅作为独立 API 存在；`DynamicDataService.create()/update()` 的保存流程**从未调用** `RuleEngine.validate_record()`。前端 `DynamicForm` 提交时也未调用 `validateOnly()` API。

**目标**: 将校验规则嵌入数据保存的生命周期 —— **前端提交前拦截 + 后端保存前兜底**。

**具体改动**：

1. **后端：DynamicDataService 集成 RuleEngine**
   - 在 `create()` 和 `update()` 方法内、数据入库前，调用 `RuleEngine(self.bo_code).validate_record(data, event)`
   - 校验不通过时抛出 `ValidationError`，返回 HTTP 400
   - 同时在保存后触发 computed 规则刷新相关衍生字段

2. **前端：DynamicForm 集成规则前置校验**
   - 在表单 `handleSubmit` 中，于原生 Element-Plus 校验通过后，调用 `validateOnly(objectCode, { record, event })` API
   - 将返回的 `errors` 映射到对应字段显示
   - 同时集成 `getVisibility()` 实现条件性字段显隐

3. **统一表达式引擎（建议改进）**
   - 当前存在两套引擎：`RuleEngine` 用 JSON Logic，`_calculate_formulas()` 用 simpleeval
   - **建议**：保留 JSON Logic 作为规则条件引擎（前后端同构），保留 simpleeval 仅用于 Formula 字段的数学计算
   - 明确边界：条件判断 → JSON Logic，数值计算 → simpleeval，不混用

### 2.2 Track B: Rollup Summary 与 Formula 增强 (Rollup & Formula Fields)

**现状**: `FieldDefinition` 已有 `formula` 字段类型和 `_calculate_formulas()` 实现；`ObjectRelationDefinition` 已有 `relation_type='master_detail'` 和 `detail_summary_rules` JSON 字段。但**无 Rollup Summary 字段类型**。

**目标**:
- **Rollup Summary**: 仅在 `master_detail` 关系中生效。支持 COUNT / SUM / MIN / MAX，子表 CUD 时自动刷新父表。
- **Formula 增强**: 支持依赖拓扑排序，确保 Formula A 依赖 Formula B 时计算顺序正确。

**具体改动**：

1. **元数据扩展**
   - 在 `FieldDefinition.FIELD_TYPE_CHOICES` 新增 `('rollup_summary', 'Rollup Summary')`
   - 新增配置字段（可复用已有 `validation_rules` JSON 字段或新增专属 JSON 字段）：
     - `rollup_target_object`: 汇总的明细对象 code
     - `rollup_type`: COUNT / SUM / MIN / MAX
     - `rollup_field`: 被汇总的明细字段 code（SUM/MIN/MAX 时必填）
     - `rollup_filter`: 包含筛选条件（仅汇总满足条件的记录）

2. **运行时触发**
   - 利用 Django `post_save` / `post_delete` Signal 拦截子对象变更
   - 通过 Celery 异步任务执行父表字段刷新（`SELECT ... FOR UPDATE` 行锁防并发）
   - 增加 `rollup_last_calculated_at` 时间戳 + 定时校准任务兜底

3. **Formula 依赖排序**
   - 在 `_calculate_formulas()` 中构建字段依赖 DAG，按拓扑序计算
   - 检测循环依赖并报错

### 2.3 Track C: 数据权限贯通 (Data Permission Integration)

**现状**: `DataPermission` 模型已实现 6 种 scope，含 `apply_to_queryset()` 方法。`PermissionInheritance` 已实现角色间权限继承。`BusinessObject` 已有 `inherit_permissions` 声明字段。但这些组件**各自独立，未自动注入查询管线**。

**目标**: 将分散的权限组件拧成一条自动化管线 —— 任何数据查询自动经过权限过滤。

**具体改动**：

1. **DynamicDataService.query() 自动注入权限过滤**
   - 在 `query()` 方法中，根据当前用户查找其 `DataPermission` 记录
   - 调用 `DataPermission.apply_to_queryset()` 自动过滤结果集
   - Superuser 跳过过滤

2. **Master-Detail 权限穿透**
   - 当 `BusinessObject.inherit_permissions=True` 时，子表查询自动继承父表的可见性判定
   - 实现：子表查询先解析对应的 `ObjectRelationDefinition`，找到父对象，应用父对象的 DataPermission 过滤

3. **Hardcoded Model ViewSet 统一拦截**
   - 创建 `DataPermissionMixin`，注入到所有 Hardcoded 对象的 ViewSet 基类
   - 自动在 `get_queryset()` 中应用权限过滤

4. **基于条件的共享规则（Criteria-Based Sharing）**
   - 扩展 `DataPermission` 新增 scope_type: `criteria`
   - `scope_value` 存储 JSON Logic 条件表达式（复用 RuleEngine 求值能力）
   - 示例：`{"==": [{"var": "category"}, "server"]}` → 仅 IT 部门可见 Server 类资产

---

## 3. 功能点详述 (Function Points)

### 3.1 FP-1: DynamicDataService ← RuleEngine 管线集成

- **改动文件**: `apps/system/services/dynamic_data_service.py`
- **改动内容**:
  - `create()` 方法：在 `_calculate_formulas()` 之后、`DynamicData.objects.create()` 之前，插入 `RuleEngine.validate_record(data, 'create')`
  - `update()` 方法：同上，event 为 `'update'`
  - 校验失败时抛出 `rest_framework.exceptions.ValidationError`
  - 保存成功后，触发 computed 规则反写

### 3.2 FP-2: 前端 DynamicForm 规则前置校验

- **改动文件**: DynamicForm 相关 composable / 组件
- **改动内容**:
  - 表单挂载时调用 `getRulesByObject(objectCode)` 获取 visibility 规则，动态显隐字段
  - 表单提交前调用 `validateOnly(objectCode, { record, event })` API
  - 返回的 errors 通过 `field` 字段定位到表单项，显示 `error_message`
  - 字段值变更时调用 `getVisibility()` 实时刷新显隐状态

### 3.3 FP-3: Rollup Summary Field

- **新增字段类型**: `rollup_summary` 在 `FieldDefinition`
- **配置项**（存储在 FieldDefinition 新增的 JSON 配置字段中）:
  - `rollupTargetObject`: 汇总的目标明细对象
  - `rollupType`: COUNT / SUM / MIN / MAX
  - `rollupField`: 被汇总字段 code（SUM/MIN/MAX 必填）
  - `rollupFilter`: 筛选条件（JSON Logic 格式）
- **运行时**: Django Signal + Celery Task + PostgreSQL `SELECT FOR UPDATE` 行锁

### 3.4 FP-4: DataPermission 自动注入

- **改动文件**: `apps/system/services/dynamic_data_service.py`、各 Hardcoded ViewSet
- **新增**: `DataPermissionMixin` 通用权限过滤 Mixin
- **改动内容**: `query()` 方法自动获取当前用户的 DataPermission 并 `apply_to_queryset()`

### 3.5 FP-5: Master-Detail 权限穿透

- **改动文件**: `DynamicDataService.query()`、`DataPermissionMixin`
- **改动内容**: 当 `BusinessObject.inherit_permissions=True`，自动向上追溯父对象权限，子表记录仅返回有权父记录下的明细

---

## 4. 验收标准体系 (Acceptance Criteria)

### 4.1 Track A: 校验规则贯通

| AC 编号 | 验收点 | 验证手段 |
|---------|--------|----------|
| AC-A.1 | 通过已有 RuleDesigner UI 为 `AssetPickup` 添加一条 validation 规则：当 `status=='Draft' && ISNULL(reason)` 时报错 | 前端 RuleDesigner 操作 |
| AC-A.2 | 前端 DynamicForm 提交时，自动调用 `validateOnly` API 前置拦截并显示错误信息 | 浏览器手动触发验证 |
| AC-A.3 | 绕过前端直接调用 `POST /api/dynamic-data/{code}/` 保存，后端 DynamicDataService 内部二次校验返回 400 | Pytest / cURL |
| AC-A.4 | 通过 RuleDesigner 修改规则条件后，下一次保存立即生效（无需重启） | API 验证 |
| AC-A.5 | `RuleExecution` 表正确记录每次校验的 input/condition_result/execution_time | 数据库查询验证 |

### 4.2 Track B: Rollup 计算

| AC 编号 | 验收点 | 验证手段 |
|---------|--------|----------|
| AC-B.1 | 为 `AssetPickup` 添加一个 `rollup_summary` 字段 `total_items_count`，配置为 `PickupItem` 的 COUNT | 元数据配置 |
| AC-B.2 | 新建领用单添加 3 行明细，保存后主单 `total_items_count` 显示 3 | 前端详情页验证 |
| AC-B.3 | 编辑领用单删除 1 行明细，保存后汇总字段自动刷新为 2 | 前端 / API 验证 |
| AC-B.4 | 并发场景：对同一主单并行 50 次子表操作，最终 Count 正确无死锁 | Pytest 并发测试（PostgreSQL `SELECT FOR UPDATE`） |
| AC-B.5 | Formula 字段 A 依赖 Formula 字段 B，B 先于 A 计算，结果正确 | Pytest 单元测试 |

### 4.3 Track C: 数据权限贯通

| AC 编号 | 验收点 | 验证手段 |
|---------|--------|----------|
| AC-C.1 | 为某用户设置 `DataPermission` scope_type='self_dept'，调用列表 API 只返回本部门数据 | Pytest / API |
| AC-C.2 | 设置 criteria-based sharing：分类为 Server 的资产仅 IT 部门可见，HR 账号查不到 Server 资产 | UI 列表 + API |
| AC-C.3 | Master-Detail 权限穿透：用户无权查看某 `AssetPickup`，API 查询其 `PickupItem` 也被拦截 | Pytest |
| AC-C.4 | `DataPermissionMixin` 同时作用于 Hardcoded ViewSet 和 Dynamic 数据查询 | Pytest |

---

## 5. 现有代码改进建议（项目未投产，可直接修正）

以下是分析过程中发现的现存问题，建议在实施本 PRD 前或同步修正：

### 5.1 DynamicDataService 缺少 Request Context

当前 `DynamicDataService` 没有接收 `request` 或 `user` 参数，导致无法获取当前用户信息用于权限过滤。

**建议**: 重构构造函数，增加 `user` 参数：
```python
def __init__(self, business_object_code: str, user=None):
    self.user = user
```

调用方（ViewSet）在初始化时传入 `request.user`。

### 5.2 开发环境数据库统一

`development.py` 中无 `DATABASE_URL` 时回退到 SQLite。由于本 PRD 依赖 PostgreSQL 特性（JSONB 聚合、`SELECT FOR UPDATE`），建议：

**建议**: 删除 SQLite fallback，统一使用 Docker Compose 提供的 PostgreSQL（即使本地开发也用 Docker PG）。

### 5.3 表达式引擎双轨清理

当前 `simpleeval` 在 3 处被使用（`dynamic_data_service.py`、`rule_engine.py`、`dynamic_field.py`），`json-logic` 在 `rule_engine.py` 使用。

**建议**: 明确边界文档化 —— 条件判断统一 JSON Logic，数值计算统一 simpleeval，禁止混用。长期可考虑将 Formula 计算也迁移到 JSON Logic 的 `{"+": [...]}` 运算符。

### 5.4 RuleEngine 缓存策略

当前 `RuleEngine._rules_cache` 为实例级缓存，每次构造新实例都会重新查库。

**建议**: 利用已有 Redis 缓存，将活跃规则按 `bo_code` 缓存到 Redis，设置 TTL + 规则变更时主动失效。

---

## 6. 实施路线图 (Roadmap)

### Sprint 5: 规则引擎贯通（2 周）

**目标**: 让已有的 RuleEngine/BusinessRule 真正"活"起来。

| 任务 | 预估 | 说明 |
|------|------|------|
| DynamicDataService 重构（增加 user 参数） | 1d | FP-1 前置 |
| DynamicDataService.create/update 集成 RuleEngine 校验 | 2d | FP-1 核心 |
| 前端 DynamicForm 集成 validateOnly + visibility | 3d | FP-2 |
| RuleEngine Redis 缓存 + 规则变更失效 | 1d | 性能优化 |
| 单元测试 + E2E 测试 | 2d | AC-A.1 ~ AC-A.5 |

### Sprint 6: Rollup Summary + Formula 增强（2 周）

**目标**: 主从表自动汇总，Formula 依赖排序。

| 任务 | 预估 | 说明 |
|------|------|------|
| FieldDefinition 新增 rollup_summary 类型 + 配置字段 | 1d | FP-3 元数据 |
| Django Signal 拦截子对象 CUD | 2d | FP-3 触发器 |
| Celery Task + PostgreSQL FOR UPDATE 行锁刷新 | 2d | FP-3 运行时 |
| 前端 Rollup 字段只读渲染 | 1d | 前端展示 |
| Formula 依赖拓扑排序 | 1d | FP-3 增强 |
| 并发测试 + 定时校准任务 | 2d | AC-B.1 ~ AC-B.5 |

### Sprint 7: 数据权限贯通（2 周）

**目标**: DataPermission 自动注入，Master-Detail 穿透。

| 任务 | 预估 | 说明 |
|------|------|------|
| DataPermissionMixin 创建 | 1d | FP-4 基础 |
| DynamicDataService.query() 自动注入权限 | 2d | FP-4 核心 |
| Hardcoded ViewSet 批量集成 Mixin | 1d | FP-4 扩展 |
| Master-Detail 权限穿透实现 | 2d | FP-5 |
| Criteria-Based Sharing（DataPermission scope 扩展） | 2d | 增强 |
| 权限测试 + 安全审计 | 2d | AC-C.1 ~ AC-C.4 |

---

## 7. 风险与约束

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| RuleEngine 集成导致保存延迟 | 性能 | Redis 缓存规则 + 异步执行非阻塞规则 |
| Rollup 并发死锁 | 数据一致性 | PostgreSQL `SELECT FOR UPDATE SKIP LOCKED` + 重试机制 |
| 权限过滤遗漏查询出口 | 安全 | 统一 Mixin + 集成测试覆盖所有 ViewSet |
| Formula 循环依赖 | 运行时错误 | 保存时 DAG 检测，发现环即拒绝 |
