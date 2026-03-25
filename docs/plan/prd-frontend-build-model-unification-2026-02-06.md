# PRD: 前端构建与公共模型统一

日期: 2026-02-06

## 1. 背景与问题
当前前端在动态表单渲染与布局设计预览之间存在结构差异，导致运行时页面空白或与预览不一致。主要根因：
- 公共模型/字段结构在多处并存，命名不一致（`fieldType/type/field_type`, `code/fieldCode/field`, `columns/column/columnCount`）
- 设计器与运行时未共享统一的“运行时渲染模型”
- 详情接口会返回“展开对象”（如 `assetCategory: {id,name...}`），而表单控件多数期望“ID 值”，导致只读详情/禁用态下出现“字段渲染了但值为空”
- 构建链路缺少一致性约束（Node/包管理器锁定、强制 typecheck/lint/build）
- 缺少渲染错误的结构化降级与可观测性

## 2. 目标
- 运行时页面与设计器预览渲染一致（WYSIWYG）
- 建立唯一的“运行时渲染模型（Runtime）”与“API DTO 模型”映射
- 运行时能同时兼容“ID 值”与“展开对象值”的字段渲染（尤其是 `reference/user/department/location` 等关系字段）
- 明确前端构建流程与质量门槛
- 提升渲染错误可观测性与降级体验

## 3. 非目标
- 不在本阶段重构后端 API 结构
- 不引入新的 UI 组件库
- 不变更业务流程与权限模型

## 4. 需求范围
### 4.1 模型与适配层
- 新增 `Runtime` 模型定义（字段/布局/动作）
- 新增 `layoutAdapter`（API -> Runtime）
- 新增 `fieldAdapter`（API FieldDefinition -> RuntimeField）
- 运行时渲染、设计器预览统一使用 Runtime 模型

### 4.2 渲染一致性
- `DynamicForm` 使用 RuntimeLayoutConfig 渲染
- `WysiwygLayoutDesigner` 画布预览使用同一渲染组件或同一 adapter
- 支持 `section/tab/collapse` 统一渲染

### 4.3 构建与质量门槛
- 固定 Node 版本（`.nvmrc` 或 `.node-version`）
- 固定包管理器版本（`packageManager` 字段）
- CI/本地强制执行：typecheck -> lint -> test -> build

### 4.4 可观测性与降级
- 布局/字段加载失败时输出结构化日志（objectCode、layoutCode、响应结构摘要）
- 渲染为空时展示友好提示与建议

### 4.5 接口收敛（前端侧）
- 统一使用单一 HTTP Client（优先 `src/utils/request.ts`），避免 `fetch`/axios 并存造成的鉴权头、baseURL、错误处理不一致
- 明确“统一响应包裹”契约：仅对 `{ success, data }` 解包；对 `{ success, message, summary, results }` 等非标准结构保持原样
- 关系字段只读展示不依赖“预加载整表 options”，优先按 ID 精确拉取（避免页面加载时大量 404/请求风暴）
- 对历史遗留/后台任务类请求支持 `silent`（不弹 toast），但保留 console 级别可观测性（便于排查）

## 5. 用户故事
- 作为配置管理员，我在布局设计器看到的预览效果，需要与对象详情页一致。
- 作为前端开发者，我希望布局渲染只依赖单一模型，避免手工兼容多结构。
- 作为项目负责人，我希望构建过程可重复并有一致的质量门槛。

## 6. 功能需求（FR）
- FR1: 系统提供统一 Runtime 模型并在运行时与设计器复用
- FR2: 布局解析支持 `sections/tabs/collapse/columns` 多类型结构
- FR3: 运行时渲染不再依赖多字段别名，所有字段在 adapter 中归一化
- FR4: 页面空白时展示清晰的降级提示
- FR5: 关系字段支持 `id | {id,...}` 的值形态，并在只读/禁用态下可显示可读文本（name/label）

## 7. 非功能需求（NFR）
- NFR1: 运行时渲染性能不低于当前版本
- NFR2: 构建流程可重复，依赖版本可追踪
- NFR3: 出错日志可定位到具体对象与布局

## 8. 方案与实现建议
### 8.1 统一模型
- 新增 `src/types/runtime.ts`
- 新增 `src/adapters/layoutAdapter.ts`
- 新增 `src/adapters/fieldAdapter.ts`

### 8.2 运行时渲染
- `DynamicForm` 只接收 RuntimeLayoutConfig + RuntimeField
- 设计器预览改为复用 `DynamicForm` 或同一 adapter

### 8.3 构建链路
- 添加 `.nvmrc` / `.node-version`
- package.json 加入 `packageManager`
- CI 增加 typecheck/lint/test/build 顺序

### 8.4 可观测性
- `useDynamicForm` 输出结构化日志
- 空布局提示组件化

## 9. 里程碑
- M1: Runtime 模型 + Adapter 完成
- M2: 动态表单渲染与设计器预览对齐
- M3: 构建链路完善

## 10. 风险与对策
- 风险：旧页面依赖旧字段结构
  - 对策：adapter 向下兼容，逐步移除旧结构
- 风险：改动影响范围大
  - 对策：分阶段实施，先保证渲染一致性

## 11. 验收标准
- 动态详情页与设计器预览一致
- 页面不再出现“空白”渲染
- 动态详情页只读模式下，关系字段（reference 等）可显示正确值（不再整体为空）
- 详情页加载时不出现“Request failed with status code 404” 类错误弹窗风暴（除非用户显式触发无效操作）
- 构建流程可在干净环境下复现

