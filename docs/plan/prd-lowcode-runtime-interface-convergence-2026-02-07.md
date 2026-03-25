# PRD: 低代码运行时接口收敛与详情只读一致性（Phase 2）

日期: 2026-02-07

## 1. 背景与问题
当前平台为“元素驱动的低代码平台”，前端运行时渲染依赖后端元数据（字段 + 布局）与对象数据（记录详情）。近期暴露的核心问题：
- 对象详情只读页与编辑页不一致：只读页部分字段为空，但编辑页有值（典型根因是布局字段 code 不规范/被错误保存为 label，导致取值失败）。
- 页面加载存在“404 toast 风暴”：只读/详情页为了展示 reference 字段名称可能触发大量按 id 请求或错误的 endpoint，造成性能与体验问题。
- 接口与模型分散：同一能力存在多条旧接口与新接口并存，容易出现“某页面走旧接口导致 404/500，另一个页面走新接口正常”的不一致。

## 2. 目标（Goals）
- G1: 详情只读页与编辑页渲染一致（WYSIWYG 一致性：字段、值、布局一致）。
- G2: 只读/详情页 reference 解析不再触发请求风暴；优先批量解析并具备缓存。
- G3: 收敛到统一对象路由接口（`/api/system/objects/{code}/...`）并保留必要的兼容 fallback，减少历史路径导致的 404/500。
- G4: 建立可回归的工程化验证（至少覆盖“详情值渲染 + 无 404 + reference 提交为 id”）。

## 3. 非目标（Non-Goals）
- 不在本阶段重构全部业务模块与权限体系。
- 不强行一次性移除所有 legacy endpoint（仅做“先新后旧”的逐步迁移）。
- 不引入新的前端状态管理体系或 UI 框架。

## 4. 关键需求（FR/NFR）
- FR1: 布局字段 code 解析需具备容错：当 layout 中误存 `asset code` 等 label 时，运行时能回退匹配到真实 code（如 `asset_code`）。
- FR2: reference 字段解析支持批量接口：`POST /api/system/objects/{code}/batch-get/`（已在 Phase 1 引入，Phase 2 扩展到 `User` 等账户域对象）。
- FR3: 统一 `User` 的引用解析：尽可能通过 object router 解决，保留 `/api/auth/users` 作为 fallback。
- NFR1: 只读页加载时 404 toast 不应出现（除非用户显式触发非法操作）。
- NFR2: 只读页 reference 解析请求数量应显著降低（批量 + 缓存）。

## 5. API 收敛范围
### 5.1 首选接口（Preferred）
- `GET /api/system/objects/{code}/runtime/?mode=edit|readonly|list|search`
- `GET /api/system/objects/{code}/{id}/`
- `POST /api/system/objects/{code}/batch-get/` body `{ ids: [...] }`
- `GET /api/system/objects/{code}/`（reference 搜索下拉与列表）

### 5.2 兼容 fallback（保留）
- `GET /api/auth/users/`、`GET /api/auth/users/{id}/`（当 object router 未开放 User 或权限不允许时）

## 6. 交付物（Deliverables）
- D1: 运行时布局适配层增强（布局字段 code 解析容错 + 可观测性）。
- D2: 账户域对象（至少 User）接入统一 object router 能力（list/retrieve/batch-get 可用）。
- D3: referenceResolver 对 User 启用 batch-get（优先）并保留 fallback。
- D4: E2E 回归用例持续通过（详情值渲染、无 404、reference 提交为 id）。
- D5: 提供历史布局数据扫描/修复工具（dry-run + apply），把“字段 code 写成 label”的存量数据修回规范。
- D6: runtime DTO 增加 `runtimeVersion`，前端对 runtime 合同进行轻量校验，合同不满足时自动回退 legacy 接口，避免空白页。

## 7. 验收标准（Acceptance）
- A1: `/objects/{code}/{id}` 详情只读页字段值与 `/objects/{code}/{id}/edit` 编辑页一致（至少 Asset 样例字段：`assetCode/assetName/assetCategory` 等）。
- A2: 详情页加载过程中不出现 API 404 响应（Playwright 监听为准）。
- A3: reference 字段提交 payload 为 id（非展开对象），且不出现 `[object Object]` 文本渲染。

## 8. 风险与对策
- 风险：历史布局数据不规范（code 被写成 label）。
  - 对策：adapter 容错 + 后台保存前校验（后续 Phase 3 引入 schema 校验与修复工具）。
- 风险：User/Organization 等对象 viewset serializer 不一致导致 retrieve 500。
  - 对策：补齐 serializer fields；必要时 batch-get 强制使用 list serializer 兜底。

## 9. 下一步（Phase 3 展望）
- 引入“契约测试/Schema 校验”来保证 layoutConfig/fieldDefinition 持久化结构稳定。
- 在 runtime endpoint 返回“reference 最小显示值”（id+name）以进一步减少解析请求。
- 增加“布局保存前后端双重校验”：保存前拒绝不合法 fieldCode；保存后后台定期巡检并提示修复。
