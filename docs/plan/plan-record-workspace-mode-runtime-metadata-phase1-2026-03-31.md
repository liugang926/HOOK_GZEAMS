# 开发计划：记录页 / 工作台模式运行时元数据收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.49 |
| 作者/Agent | Codex |

## 一、目标
- 将记录页 / 工作台模式默认规则沉淀到 runtime metadata。
- 将详情页和聚合单据页的默认 surface 规则改为可配置而非组件硬编码。
- 让聚合单据对象默认回到轻量记录页，工作台只在需要时展开。

## 二、范围

### 2.1 本阶段实施
1. 扩展 `RuntimeWorkbench` 类型与 runtime contract
2. 扩展 runtime resolver 和后端 runtime payload
3. 为核心资产生命周期对象补齐 `default_page_mode` 与默认 surface metadata
4. 改造 `DynamicDetailPage` 支持 `record / workspace` 切换
5. 改造 `DocumentWorkbench` 读取 metadata 控制默认 surface
6. 补齐 locale 与前后端定向测试
7. 归档 PRD、计划、实施报告

### 2.2 本阶段不实施
1. 不引入 `surfacePriority`
2. 不重构列表页摘要列
3. 不调整动作协议或闭环数据结构
4. 不新增数据库字段

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | runtime 元数据协议设计 | PRD、类型定义 |
| 2 | 前端 contract / resolver 收敛 | `runtimeContract.ts`、`runtimeLayoutResolver.ts` |
| 3 | 后端 runtime payload 扩展 | `object_router_runtime_actions.py` |
| 4 | 资产生命周期对象 menu metadata 补齐 | `menu_config.py` |
| 5 | 详情页模式切换改造 | `DynamicDetailPage.vue` |
| 6 | 聚合单据默认 surface 改造 | `DocumentWorkbench.vue`、`DynamicFormPage.vue` |
| 7 | 定向回归与文档归档 | 测试、README、实施报告 |

## 四、实施顺序
1. 先定义 runtime 协议和校验规则，防止 metadata 失控。
2. 再改后端 runtime payload 和菜单配置，保证前端有稳定输入。
3. 再改 `DynamicDetailPage` 与 `DocumentWorkbench` 的默认模式行为。
4. 最后补 locale、回归测试与归档文档。

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| runtime metadata 值不合法 | 页面渲染异常 | contract 增加枚举校验并提供 resolver 兜底 |
| 聚合对象默认模式切换影响既有跳转 | 用户进入错误页面 | 保留 `page_mode` query 覆盖与 hash 行为 |
| 只读/编辑模式默认 surface 被 metadata 误覆盖 | 表单首屏体验退化 | 仅在 metadata 显式存在时覆盖旧规则 |
| 仓库存量 typecheck 问题 | 无法用全量类型检查单独验收 | 记录存量问题，重点验证本轮触达文件不新增命中 |

## 六、阶段交付物
- PRD：`docs/prd/prd-record-workspace-mode-runtime-metadata-2026-03-31.md`
- 开发计划：`docs/plan/plan-record-workspace-mode-runtime-metadata-phase1-2026-03-31.md`
- 代码交付：runtime metadata、详情页模式切换、聚合单据默认 surface
- 验证交付：Vitest 定向回归、后端语法校验、locale JSON 校验
- 报告交付：Phase 7.2.49 实施报告

## 七、后续阶段建议
### Phase 7.2.50
- 将 `surfacePriority` 继续元数据化，驱动记录页摘要、related、activity 的统一排序

### Phase 7.2.51
- 将列表页摘要列、hero stats 和 workbench summary 合并到统一 surface schema
