# 低代码固定资产平台布局与对象能力优化 PRD（国际化版）

## 1. 文档信息
- 版本：v1.0
- 日期：2026-03-02
- 适用范围：`frontend` + `backend`（低代码运行时、布局设计器、对象元数据、i18n）
- 产品形态：企业级固定资产管理低代码平台（多组织、多对象、元数据驱动）

## 2. 背景与目标
当前系统已具备：
- 元数据驱动对象引擎（`/api/system/objects/{code}`）
- 动态列表/表单/详情页面（`DynamicListPage` / `DynamicForm` / `DynamicDetailPage`）
- 布局设计器（WYSIWYG）
- 语言与翻译管理（`Language` / `Translation` 模型与 API）
- 前端 `vue-i18n` 与 `Accept-Language` 请求头注入

但从“国际化低代码平台”视角，仍存在关键断点：布局优先级链路与运行时未完全统一、对象元数据多语言未直达 runtime、用户语言偏好未形成前后端闭环。

### 2.1 核心目标
1. 布局：统一“设计时-运行时-个性化”链路，保证可预测可回放。
2. 对象：提升固定资产领域对象协同能力（主对象+子对象+反向关系+流程）。
3. 国际化：从“静态文案国际化”升级为“对象与布局数据国际化”。

### 2.2 非目标
1. 本期不替换 UI 框架（仍使用 Vue3 + Element Plus）。
2. 不重构全部业务模块为专属页面，优先增强通用低代码运行时。
3. 不引入新的工作流引擎，仅增强现有流程联动体验。

## 3. 现状评估（前后端联合）

## 3.1 已落地能力（可复用基础）
1. 后端已支持 `BusinessObject/FieldDefinition/PageLayout` 与 runtime 接口。
2. 前端已支持 tab/collapse 布局渲染、反向关系展示、子表字段渲染。
3. 后端已具备 `Language/Translation` 数据模型与批量导入导出能力。
4. 前端已具备通知中心、语言切换、动态对象统一路由。

## 3.2 关键问题（需优化）
1. 布局优先级链路未统一：
`PageLayoutViewSet.get_merged_layout` 支持 user/role/org/global/default 差异合并，但 `ObjectRouter.runtime` 未走同一合并路径，运行时与设计器结果可能不一致。
2. 字段标识仍混用：
前端大量兼容 `fieldCode/field_code/prop/code`，增加维护成本与错配风险。
3. 对象国际化未直达 runtime：
`ObjectRouter` 返回字段 `name/placeholder/options` 时未统一调用对象翻译服务，Translation 能力与对象 runtime 脱节。
4. 语言上下文缺后端中间件闭环：
后端有 i18n service thread-local 机制，但缺统一语言上下文中间件接管 `Accept-Language`。
5. 用户语言偏好未闭环：
`accounts.User` 有 `preferred_language` 字段，但用户 API 与前端 store 未完整打通持久化与回写。
6. 前端仍有硬编码文案：
如 `ModuleWorkbench`、`LanguageList` 成功/失败提示等，存在非 i18n 文案与术语不统一。
7. 反向关系表展示仍偏“写死”：
`RelatedObjectTable` 对多对象列定义依赖硬编码映射，未完全 metadata 化。
8. 子表能力偏基础：
目前可增删行，但缺少行级校验规则、批量编辑、导入、合计栏、性能优化（大行数）。
9. 固定资产业务协同偏“页面可达”，但流程体验不强：
采购、入库、维保、报废、租赁、保险更多是对象 CRUD，缺少跨对象操作向导与场景化工作台。

## 4. 需求范围

## 4.1 布局设计优化（Layout）
1. 统一布局解析入口：
runtime 与设计器、详情页、表单页统一使用同一合并算法与字段规范化。
2. 统一布局优先级：
严格执行 `user > role > org > global > default`。
3. 强化布局类型治理：
在单布局模型下统一 `edit/readonly/search/list` 语义，避免历史 `form/detail/list` 混淆。
4. 布局可观测：
在 runtime 响应中返回 `source`、`layout_id`、`version`、`merged_layers` 供排障。

## 4.2 对象功能优化（Object Runtime）
1. 字段标识标准化：
运行时与持久化只使用 `field_code`（前端内部可保留 dataKey 映射）。
2. 反向关系 metadata 化：
反向关系列表列定义由字段元数据驱动，不再用对象硬编码模板。
3. 子表增强：
支持行级校验、批量新增、复制行、Excel 导入、汇总行、行数性能保护。
4. 场景化操作流：
为固定资产核心链路提供“对象级向导”（采购申请 -> 入库 -> 领用/借用 -> 维保/报废）。

## 4.3 国际化优化（i18n）
1. 运行时对象国际化：
对象名称、字段标签、placeholder、字典值、布局标题按语言实时返回。
2. 语言上下文中间件：
后端统一解析 `Accept-Language`，注入 thread-local/context。
3. 用户偏好闭环：
登录后拉取并应用 `preferred_language`，切换语言后可选回写用户偏好。
4. 文案治理：
清理前端硬编码文案并纳入词条管理与扫描。

## 5. 方案设计（前后端）

## 5.1 后端改造
1. 新增 `LanguageContextMiddleware`（或在现有 middleware 扩展）：
- 解析 `Accept-Language`
- 设置 `TranslationService.set_current_language(...)`
- 请求结束清理上下文

2. 改造 `ObjectRouter.runtime` 与 `fields/metadata`：
- 使用统一布局合并服务（复用 `get_merged_layout` 同源逻辑）
- 输出中增加：
  - `layout_source`（user/role/org/global/default）
  - `layout_layers`（参与合并层）
  - `locale`
- 字段输出支持本地化：
  - `name/label/placeholder/options` 优先翻译值
  - 回退到原始字段值

3. 对象翻译读取策略统一：
- 优先 GenericForeignKey 翻译（`Translation`）
- 次级回退 `*_en` / 多语言字段
- 末级回退原字段

4. 用户语言偏好 API：
- `GET /api/system/objects/User/me/` 返回 `preferredLanguage`
- `PATCH /api/system/objects/User/me/profile/` 支持更新 `preferredLanguage`

5. 字段规范化契约：
- API contract 明确 `field_code` 为唯一稳定键
- 兼容层仅保留过渡期，增加 deprecation 标记与日志

## 5.2 前端改造
1. `runtimeLayoutResolver` 与页面统一入口：
- 所有动态页只消费统一 runtime contract
- 减少页面级 fallback 分歧

2. 字段键治理：
- 新增 `fieldKeyNormalizer`，对外只暴露 `field_code`
- 逐步清理 `prop/code/fieldCode` 兼容分支

3. 语言状态与用户偏好：
- `locale store` 初始化顺序：
  - 本地缓存 -> 用户偏好 -> 默认语言
- 切换语言后支持“仅本机”或“同步账号偏好”

4. i18n 文案清理与校验：
- 建立 CI 扫描（硬编码中文/英文规则）
- 为 `ModuleWorkbench`、`LanguageList`、Designer 提示补齐词条

5. 关系表与子表增强：
- `RelatedObjectTable` 列由 metadata 接口驱动
- `SubTableField` 支持：
  - 行级规则（必填/格式/联动）
  - 批量粘贴/导入
  - 行操作权限控制

## 5.3 数据与接口变更清单
1. 接口新增字段（向后兼容）：
- `runtime`: `layout_source`, `layout_layers`, `locale`
- `fields`: `field_code`（显式）、`label`（本地化后）

2. 账号字段开放：
- `preferred_language` 进入用户详情/更新序列化

3. 兼容策略：
- 保留旧字段读取 2 个迭代周期，埋点统计使用情况后下线。

## 6. 里程碑与排期

### M1（1-2 周）：基础闭环
1. 后端语言上下文中间件 + runtime locale 输出
2. 用户偏好语言 API 打通
3. 前端 locale 初始化链路改造

### M2（2-3 周）：布局与字段规范化
1. runtime 接入统一 diff 合并链路
2. 字段键 `field_code` 标准化改造
3. 布局可观测信息落地（source/layers/version）

### M3（2-3 周）：对象能力增强
1. RelatedObjectTable metadata 化
2. SubTable 高级能力（行级校验+批量导入）
3. 固定资产核心对象向导（采购到入库）

### M4（1-2 周）：治理与验收
1. i18n 文案扫描与清理
2. 回归测试、性能压测、灰度发布

## 7. 验收标准（Acceptance Criteria）
1. 语言切换后，动态对象页（列表/表单/详情）字段标签与字典值实时切换，覆盖率 >= 95%。
2. 同一对象同一模式下，设计器预览与 runtime 渲染字段顺序一致率 100%。
3. `field_code` 在新增代码路径中覆盖率 100%，旧键兼容仅存在于适配层。
4. 用户语言偏好保存后，重新登录自动生效。
5. 反向关系表无硬编码对象列模板，全部由 metadata 驱动。
6. 子表 200 行以内编辑流畅（首屏渲染 < 1.5s，交互无明显卡顿）。
7. 无 P1 级国际化回退缺陷（错语种、空文案、关键按钮未翻译）。

## 8. 指标（KPI）
1. 动态页面国际化覆盖率：>= 95%
2. 布局渲染一致性缺陷数：下降 80%
3. 字段映射类线上问题：下降 70%
4. 固定资产流程任务完成时长：下降 20%
5. 用户语言偏好开启率：>= 60%

## 9. 风险与缓解
1. 历史布局数据不规范导致 runtime 合并异常：
- 缓解：上线前批量执行 layout normalize + 校验脚本。
2. 字段键治理影响旧页面：
- 缓解：保留兼容层、埋点追踪、分批切换。
3. 翻译数据不完整：
- 缓解：缺失回退策略 + 翻译管理看板 + 批量导入模板。
4. 子表增强带来性能压力：
- 缓解：分页/虚拟滚动/延迟校验策略。

## 10. 发布策略
1. Feature Flag 控制：
- `runtime_i18n_enabled`
- `layout_merge_unified_enabled`
- `field_code_strict_mode`
2. 灰度范围：
- 先系统管理对象，再固定资产主对象，再全对象。
3. 回滚策略：
- 保留 legacy runtime 路径与旧字段兼容，支持开关级回退。

