# PRD - Layout & Object Runtime i18n Optimization (2026-03-02)
# PRD - 布局与对象运行时国际化优化（2026-03-02）

## 1. 文档信息 / Document Info

| 项目 (CN) | Item (EN) | 内容 / Value |
| --- | --- | --- |
| 文档版本 | Version | v1.1 |
| 日期 | Date | 2026-03-02 |
| 适用范围 | Scope | `frontend` + `backend` + metadata + runtime i18n |
| 系统形态 | Product Type | Metadata-driven fixed-asset low-code platform |
| 关联模块 | Related Modules | `ObjectRouter`, `PageLayout`, `BusinessObject`, `FieldDefinition`, `Language`, `Translation`, user profile locale |

## 2. 功能概述与业务场景 / Business Overview & Scenarios

当前系统已具备动态对象、布局设计器、翻译管理与基础语言切换能力，但仍存在“设计器结果与运行时不一致”“对象元数据翻译无法稳定下发”“用户语言偏好未闭环”等问题。  
The system already supports dynamic objects, layout designer, translation management, and locale switching, but still has gaps in runtime consistency, metadata translation delivery, and user locale persistence.

核心业务场景 / Core Scenarios:
1. 管理员在设计器发布布局后，运行时页面应立即按同一优先级渲染。  
Admin publishes layout in designer and runtime must render with the same priority chain.
2. 用户切换语言后，列表/表单/详情/关系表/子表均应实时显示目标语言。  
After locale switch, list/form/detail/related table/sub-table should update in real time.
3. 对象字段标签、占位符、选项、布局标题、系统提示应统一通过 i18n 机制输出，不允许硬编码文案。  
All object labels/placeholders/options/layout titles/system messages must be served via i18n, with no hard-coded UI strings.

## 3. 用户角色与权限 / User Roles & Permissions

| 角色 (CN) | Role (EN) | 关键权限 / Key Permissions |
| --- | --- | --- |
| 平台管理员 | Platform Admin | 管理语言、词条、对象、布局、发布开关 |
| 配置管理员 | Configuration Admin | 设计/发布布局、配置对象字段与展示规则 |
| 业务操作员 | Business Operator | 使用动态页面处理业务数据、切换个人语言 |
| 审计/只读用户 | Auditor / Readonly User | 只读访问对象页面与审计信息 |

权限矩阵 / Permission Matrix:

| 权限编码 | Description | Admin | Config Admin | Operator | Auditor |
| --- | --- | --- | --- | --- | --- |
| `system.language.view` | 查看语言与词条 / View languages & translations | Y | Y | N | N |
| `system.language.manage` | 维护语言与词条 / Manage translations | Y | N | N | N |
| `layout.design` | 设计布局 / Design layouts | Y | Y | N | N |
| `layout.publish` | 发布布局 / Publish layouts | Y | Y | N | N |
| `object.runtime.view` | 访问运行时 / Access runtime | Y | Y | Y | Y |
| `user.locale.update` | 更新个人语言 / Update profile locale | Y | Y | Y | Y |

## 4. 目标与非目标 / Goals & Non-Goals

### 4.1 目标 / Goals
1. 统一布局链路：设计时与运行时共用同一合并与优先级逻辑。  
Unify layout merge and priority logic between design time and runtime.
2. 标准化字段键：新路径仅允许 `field_code`。  
Standardize field key to `field_code` for all new paths.
3. 对象运行时国际化：字段与布局元数据按请求语言返回。  
Return localized object/layout metadata by request locale.
4. 用户语言闭环：登录加载偏好，切换后可回写偏好。  
Close the loop for profile locale load and persistence.
5. 建立“禁止硬编码语言”治理机制（开发规范 + CI 扫描 + 验收门禁）。  
Enforce no-hardcoded-language policy via standards, CI scan, and release gate.

### 4.2 非目标 / Non-Goals
1. 不替换前端技术栈（Vue3 + Element Plus 保持不变）。  
No frontend framework replacement.
2. 不重构全部业务为专用页面，优先增强通用 low-code runtime。  
No full rewrite into dedicated pages.
3. 不引入新的工作流引擎。  
No new workflow engine in this phase.

## 5. 现状与问题 / Current State & Gaps

1. `ObjectRouter.runtime` 与布局设计器在布局合并路径上仍存在分叉。  
Runtime and designer use inconsistent merge paths.
2. 字段键历史包袱：`fieldCode/prop/code/field_code` 混用。  
Legacy mixed field identifiers increase bug risk.
3. 运行时对象返回未稳定走翻译服务；部分字段仅返回默认语言值。  
Runtime metadata is not consistently translated.
4. `Accept-Language` 解析与后端上下文设置未统一中间件化。  
Locale resolution middleware is incomplete.
5. 用户 `preferred_language` 已有字段但前后端闭环不足。  
`preferred_language` exists but lifecycle is incomplete.
6. 前端仍有硬编码成功/失败提示和按钮文案。  
Hardcoded user-facing strings still exist.

## 6. 需求范围 / Scope

### 6.1 布局 / Layout
1. 统一优先级 `user > role > org > global > default`。  
2. 统一 runtime/designer/detail/form 的布局解析入口。  
3. 在 runtime 返回可观测字段：`layout_source`, `layout_layers`, `layout_id`, `version`, `locale`。

### 6.2 对象运行时 / Object Runtime
1. 新增与改造路径统一为 `field_code`。  
2. `RelatedObjectTable` 改为 metadata 驱动列定义。  
3. `SubTableField` 支持行级规则、批量粘贴/导入、性能保护。

### 6.3 国际化 / i18n
1. 对象名称、字段标签、placeholder、options、布局标题按 locale 返回。  
2. 后端按 `Accept-Language` + 用户偏好 + 系统默认进行解析和回退。  
3. 文案治理：无硬编码语言，统一词条 key 管理与审计。

## 7. 公共模型引用声明 / Public Base Model References (MUST)

### 7.1 后端引用 / Backend References

| 组件类型 | Base Class | 引用路径 | 自动能力 |
| --- | --- | --- | --- |
| Model | `BaseModel` | `apps.common.models.BaseModel` | 组织隔离、软删除、审计字段、`custom_fields` |
| Serializer | `BaseModelSerializer` | `apps.common.serializers.base.BaseModelSerializer` | 公共字段序列化、`custom_fields` 序列化 |
| ViewSet | `BaseModelViewSetWithBatch` | `apps.common.viewsets.base.BaseModelViewSetWithBatch` | 组织过滤、软删除、批量操作 |
| Filter | `BaseModelFilter` | `apps.common.filters.base.BaseModelFilter` | 时间/用户/删除状态过滤 |
| Service | `BaseCRUDService` | `apps.common.services.base_crud.BaseCRUDService` | 标准 CRUD、分页、批量能力 |

### 7.2 前端引用 / Frontend References

| 组件类型 | 组件/Hook | 引用路径 | 说明 |
| --- | --- | --- | --- |
| 列表页 | `BaseListPage` + `useListPage` | `@/components/common/BaseListPage.vue` | 统一列表行为 |
| 表单页 | `BaseFormPage` + `useFormPage` | `@/components/common/BaseFormPage.vue` | 统一表单行为 |
| 详情页 | `BaseDetailPage` | `@/components/common/BaseDetailPage.vue` | 统一详情行为 |
| 动态引擎 | `FieldRenderer` / `DynamicForm` | `@/components/engine/*` | 元数据驱动渲染 |
| 国际化 | `useI18n` | `vue-i18n` | 文案通过 key 渲染，禁止硬编码 |

## 8. 数据模型设计 / Data Model Design

### 8.1 受影响实体 / Affected Models
1. `accounts.User`: 使用并暴露 `preferred_language`。  
2. `system.Translation`: 用于对象/字段/布局翻译读取。  
3. `system.PageLayout`: 增强 runtime 可观测字段映射。  
4. `system.FieldDefinition`: 明确 `field_code` 为主键标识语义。

### 8.2 字段契约 / Field Contract

| 字段 | Type | 约束 / Constraint | 说明 |
| --- | --- | --- | --- |
| `field_code` | string | required, stable | 对外唯一稳定键 / single stable key |
| `label` | string | localized | 运行时本地化后输出 |
| `placeholder` | string | localized | 运行时本地化后输出 |
| `layout_source` | string | enum | `user/role/org/global/default` |
| `locale` | string | IETF tag | 例如 `zh-CN`, `en-US` |

## 9. API 设计 / API Design

### 9.1 动态对象主路由 / Dynamic Object Routing

| 方法 | Endpoint | 说明 |
| --- | --- | --- |
| GET | `/api/objects/{code}/runtime/` | 获取运行时布局与字段（本地化） |
| GET | `/api/objects/{code}/fields/` | 获取字段定义（支持 locale） |
| GET | `/api/objects/{code}/metadata/` | 获取对象元数据（支持 locale） |
| GET | `/api/objects/{code}/` | 列表查询 |
| POST | `/api/objects/{code}/` | 创建记录 |
| GET | `/api/objects/{code}/{id}/` | 详情 |
| PATCH | `/api/objects/{code}/{id}/` | 局部更新 |

### 9.2 用户语言偏好 / User Locale Preference

| 方法 | Endpoint | 说明 |
| --- | --- | --- |
| GET | `/api/system/objects/User/me/` | 返回当前用户信息（含 `preferredLanguage`） |
| PATCH | `/api/system/objects/User/me/profile/` | 更新个人信息（含 `preferredLanguage`） |

### 9.3 返回格式与错误码 / Response Format & Error Codes
统一使用 `success/data/error` 结构；错误码至少覆盖：  
`VALIDATION_ERROR`, `UNAUTHORIZED`, `PERMISSION_DENIED`, `NOT_FOUND`, `CONFLICT`, `SERVER_ERROR`。

### 9.4 国际化响应约束 / i18n Response Rules
1. API 不返回硬编码业务文案，仅返回结构化字段 + 可本地化内容。  
2. 错误提示通过错误码映射前端 i18n key。  
3. 本地化字段无翻译时必须按回退链返回，不得返回空字符串。

## 10. 后端实现设计 / Backend Design

1. 新增或扩展 `LanguageContextMiddleware`：解析 `Accept-Language`，写入翻译上下文，请求结束清理。  
2. 改造 `ObjectRouter.runtime`：统一调用布局合并逻辑，输出 `layout_source/layout_layers/locale`。  
3. 统一翻译读取策略：  
`Translation` -> 多语言字段(`*_en`/`*_zh`) -> 原始值。  
4. 统一字段键规范化输出：新增路径仅输出 `field_code`，旧键通过兼容层过渡并记录 deprecation 日志。

## 11. 前端实现设计 / Frontend Design

1. 新增 `runtimeLayoutResolver`：动态页面统一消费 runtime contract。  
2. 新增 `fieldKeyNormalizer`：组件层内部兼容，组件外暴露统一 `field_code`。  
3. `locale store` 初始化顺序：local cache -> profile locale -> system default。  
4. 切换语言支持两种模式：  
- Local only (仅本机)  
- Sync profile (同步到账号偏好)  
5. 清理 `ModuleWorkbench`、`LanguageList` 等页面硬编码文案，全部改为 i18n key。

## 12. 禁止硬编码语言规范 / No Hardcoded Language Policy

### 12.1 强制规则 / Mandatory Rules
1. 前端用户可见文案必须来自 i18n key，禁止直接写中文/英文业务文案。  
2. 后端不拼接自然语言错误文案到业务返回，统一返回 error code。  
3. 元数据可显示文本（label/placeholder/options）必须经过翻译服务和回退链。  
4. 新增 PR 必须通过 i18n 扫描与审查清单。

### 12.2 CI 扫描策略 / CI Scanning
1. 扫描 `.vue/.ts/.tsx` 中可见硬编码文本（允许名单除外）。  
2. 扫描新增 API 响应中的硬编码 message。  
3. 扫描未使用 i18n key 的 `ElMessage/notification/dialog` 文案。

### 12.3 允许例外 / Allowed Exceptions
1. 开发调试日志（非用户可见）。  
2. 协议常量、标准代码、字段编码。  
3. 第三方库固定输出（需在包装层做翻译映射）。

## 13. 里程碑 / Milestones

| 阶段 | 时间 | 交付 |
| --- | --- | --- |
| M1 | 1-2 周 | 语言上下文中间件、用户偏好 API 闭环、runtime locale 输出 |
| M2 | 2-3 周 | 布局合并统一、`field_code` 标准化、可观测字段输出 |
| M3 | 2-3 周 | 关系表 metadata 化、子表增强、关键页面硬编码清理 |
| M4 | 1-2 周 | i18n 治理、回归测试、性能测试、灰度发布 |

## 14. 验收标准 / Acceptance Criteria

1. 动态页面 i18n 覆盖率 >= 95%。  
2. 设计器预览与 runtime 字段顺序一致率 = 100%。  
3. 新增代码路径 `field_code` 覆盖率 = 100%。  
4. 用户 `preferred_language` 保存后重登生效。  
5. 关系表列配置 100% metadata 驱动，无对象级硬编码模板。  
6. 子表 200 行以内首屏渲染 < 1.5s。  
7. P1 国际化缺陷数 = 0。  
8. CI i18n 扫描通过率 = 100%，不允许“硬编码语言”例外泄漏。

## 15. 指标 / KPI

| 指标 | 目标 |
| --- | --- |
| Runtime i18n coverage | >= 95% |
| Layout consistency defects | -80% |
| Field-key mapping incidents | -70% |
| Fixed-asset task completion time | -20% |
| Profile locale adoption | >= 60% |

## 16. 测试用例 / Test Cases

### 16.1 后端 / Backend
1. `Accept-Language` 解析优先级测试（header > profile > default）。  
2. `ObjectRouter.runtime` 返回本地化字段与 `layout_source/layout_layers/locale`。  
3. 无翻译场景回退链测试（Translation 缺失时不为空）。  
4. `preferred_language` 更新与读取一致性测试。

### 16.2 前端 / Frontend
1. 语言切换后列表/表单/详情即时更新。  
2. `field_code` 映射一致性与旧键兼容告警测试。  
3. `ElMessage`/通知/对话框文案均来自 i18n key。  
4. 关系表与子表在双语下显示正确。

### 16.3 端到端 / E2E
1. `zh-CN` 与 `en-US` 全链路冒烟。  
2. 语言切换 + 布局切换 + 发布后的一致性回归。  
3. 高并发下 runtime 响应 locale 正确性抽样。

## 17. 风险与缓解 / Risks & Mitigations

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 历史布局数据不规范 | runtime 合并失败 | 上线前执行 normalize + 校验脚本 |
| 旧键兼容分支过多 | 新旧混用导致缺陷 | 兼容层限时保留 + 埋点追踪 + 分批下线 |
| 翻译数据不完整 | 页面空白或错语种 | 强制回退链 + 翻译看板 + 批量导入模板 |
| i18n 扫描误报/漏报 | 阻塞或漏检 | 白名单机制 + PR 人工复核 |

## 18. 发布与回滚 / Rollout & Rollback

Feature Flags:
1. `runtime_i18n_enabled`
2. `layout_merge_unified_enabled`
3. `field_code_strict_mode`

灰度顺序 / Rollout Order:
1. 系统管理对象 / system objects
2. 固定资产主对象 / fixed-asset core objects
3. 全对象 / all objects

回滚策略 / Rollback:
1. 可按 flag 粒度回退。  
2. 保留 legacy runtime 路径与旧键只读兼容（限时）。  
3. 回滚期间继续收集埋点，确认风险窗口后再推进。

## 19. 开放问题 / Open Questions

1. 是否需要对 runtime locale 结果引入短期缓存（按 user + object + mode）？  
2. `field_code` 旧键兼容窗口是 2 个迭代还是 3 个迭代？  
3. i18n CI 白名单策略由谁审批、如何审计？
