# Vue3 元数据渲染引擎重构 PRD

## 1. 文档信息
- 文档版本: `v1.0`
- 日期: `2026-02-26`
- 负责人: `Frontend Platform / Low-Code Engine`
- 适用范围: `GZEAMS Vue3 前端 + System Metadata 后端契约`

## 2. 背景与问题
- 当前布局设计器、详情页、编辑页存在“同对象不同渲染结果”的一致性问题。
- 历史存在 `form/detail/search/list` 多模型并行，导致配置分裂、维护复杂、回归成本高。
- 字段属性 schema、分区属性 schema 分散在多个模块，演进时容易遗漏。
- 低代码目标要求 `25` 种字段类型统一接入，但当前字段类型映射与属性配置仍有重复定义。

## 3. 产品目标
- 统一页面布局模型: 编辑页与详情页共享同一布局配置（单一模型）。
- 统一渲染契约: 设计器预览与运行时渲染使用同一套字段/布局 contract。
- 统一字段扩展机制: 新字段类型接入不超过 1 天，且无跨模块重复改动。
- 建立可回归体系: 核心路径具备稳定自动化测试（单测 + E2E smoke）。

## 4. 非目标
- 不在本阶段重写所有业务页面 UI。
- 不在本阶段替换后端业务模型（Django app 领域模型保持现状）。
- 不在本阶段引入新的可视化规则引擎（仅做契约和渲染一致性）。

## 5. 核心用户与场景
- 系统管理员: 配置对象字段与页面布局。
- 业务管理员: 在布局设计器调整字段顺序、显示、只读、分区结构。
- 业务用户: 在列表/详情/编辑页看到与设计器一致的页面表现。

## 6. 功能需求

### FR-1 单一布局模型
- `edit/readonly/detail/search` 统一映射到共享 `form` 布局模型。
- 详情页与编辑页复用同一结构，仅通过模式控制字段交互能力（readonly/disabled）。
- 列表页改为字段驱动（`show_in_list + sort_order`）+ 用户列偏好，不再依赖独立 `list` 布局记录。

### FR-2 字段属性与分区属性契约统一
- 建立统一 schema 源，供设计器属性面板、渲染器、校验器共用。
- 保留兼容导出层，避免一次性改动导致页面中断。
- 约束字段属性 key、类型与默认值，消除同义字段差异。

### FR-3 WYSIWYG 设计器一致性
- 设计器画布、预览模式、运行时页面必须可复用同一布局配置结构。
- 支持 `section/tab/collapse` 三类容器编辑与保存。
- 支持发布、回滚、草稿管理，且行为在单一布局模型下可用。

### FR-4 25 字段类型统一接入
- 字段组件通过统一 registry 注册，支持别名归一（如 `richtext -> rich_text`）。
- 字段类型能力矩阵（编辑、详情、列表）在 contract 层声明。
- 新字段类型接入包含: 组件、schema、适配器、测试模板。

### FR-5 运行时稳态能力
- 元数据接口异常时（如 `metadata 500`）可回退到 runtime/default contract 渲染，不出现空白页。
- 动态页面必须具备加载、空态、异常态的稳定表现。

## 7. 技术方案（目标架构）
- `Contract Layer`: `types/runtime.ts + platform/layout/*`（唯一数据契约入口）。
- `Adapter Layer`: `adapters/*` 负责历史字段/布局格式归一化。
- `Designer Layer`: `components/designer/*` 仅消费 contract，不自行定义私有 schema。
- `Runtime Layer`: `views/dynamic/* + components/engine/*` 使用同一 contract 渲染。
- `API Layer`: `api/dynamic.ts + api/system/*` 保证返回结构可归一。

## 8. 数据与接口要求
- 后端 layout 输出统一为 `layout_type=form`（单一模型），历史类型仅兼容读取。
- runtime 返回字段:
  - `fields.editableFields`
  - `fields.reverseRelations`
  - `layout.layoutConfig`
- 布局配置必须包含稳定标识（`section.id`, `field.id/fieldCode`）。

## 9. 迁移策略
- 阶段化迁移，不做大爆炸重构。
- 旧 `list` 布局记录归档，runtime 不再使用。
- 保留旧前端调用入口（composable re-export），内部切换到新 contract 源。
- 对关键对象（Asset/Department/Supplier/Finance Voucher）做优先回归。

## 10. 测试与质量门禁
- 单测:
  - schema contract（字段/分区属性）
  - layout normalize / runtime resolver
  - field registry 类型归一
- 集成/E2E:
  - 设计器保存 -> 详情页渲染
  - 发布/回滚
  - metadata 500 fallback
- CI 门禁:
  - 必过 `vitest + e2e smoke`
  - 禁止新增 breaking contract（通过 contract snapshot 检查）

## 11. 里程碑计划
- M1（已完成）: 单一布局模型主干打通（edit/detail 共用、list 字段驱动）。
- M2（进行中）: 属性 schema 契约统一到 `platform/layout`，并完成兼容导出。
- M3: 25 字段类型 capability matrix + registry 标准化。
- M4: 设计器与运行时 contract 快照化测试，纳入 CI 强校验。
- M5: 历史兼容层清理（仅保留必要 adapter）。

## 12. 验收标准（DoD）
- 同一对象在设计器预览、详情页、编辑页字段顺序与可见性一致。
- 列表页列显示仅由字段定义与用户偏好控制，不依赖 list layout。
- 关键回归用例（布局保存/发布/回滚、metadata fallback）全部通过。
- 新增字段类型按标准模板接入，且不需要修改 3 处以上核心模块。

## 13. 风险与缓解
- 风险: 历史布局数据质量不一致（缺失 id、旧 key 命名）。
  - 缓解: 后端/前端双重 normalize + 修复脚本 + 回归用例。
- 风险: 业务模块仍有直连旧接口。
  - 缓解: 增加兼容层与调用扫描清单，逐模块迁移。
- 风险: 设计器交互复杂导致回归成本高。
  - 缓解: 保留 smoke 主链路并扩充关键行为断言（保存/回滚/跨容器编辑）。

