# 开发计划：Aggregate Document Summary Priority 治理

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.53 |
| 作者/Agent | Codex |

## 一、目标
- 将 aggregate document summary blocks 纳入 runtime priority 协议
- 限制单据 summary 首屏只承载高优先级区块
- 让 `Record / Workflow / Batch Tools` 不再硬编码并列首屏

## 二、范围

### 2.1 本阶段实施
1. 扩展 `RuntimeWorkbench` 与 runtime contract
2. 扩展 runtime resolver 与后端 runtime payload
3. 在 menu config 中为 aggregate documents 增加默认 `document_summary_sections`
4. 改造 `DocumentWorkbench` 首屏 / 折叠区分层
5. 增加前后端定向测试
6. 归档 PRD、计划和实施报告

### 2.2 本阶段不实施
1. 不新增新的 page mode
2. 不调整对象动作协议
3. 不修改 aggregate document 数据返回结构
4. 不开发后台配置 UI

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 设计 document summary priority 协议 | PRD |
| 2 | 扩展 runtime 类型、contract、resolver | frontend runtime files |
| 3 | 扩展后端 workbench payload | `menu_config.py`, `object_router_runtime_actions.py` |
| 4 | 改造 `DocumentWorkbench` 渲染层级 | `DocumentWorkbench.vue` |
| 5 | 补齐回归测试 | Vitest + backend pytest files |
| 6 | 文档归档 | report + README |

## 四、实施顺序
1. 先补 runtime 协议
2. 再补 backend menu/runtime 输出
3. 再改 `DocumentWorkbench` 首屏折叠逻辑
4. 最后补测试与报告

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| 低优先级区块被误隐藏 | 用户误以为能力消失 | 使用折叠区而非直接移除 |
| metadata 只配一部分 section | 显示不完整 | 自动补齐默认 sections |
| runtime payload 新字段破坏旧页面 | 解析失败 | 将字段设计为可选，并补 contract / resolver 回归 |
| 本地后端测试环境不完整 | 无法完整跑 pytest | 使用 `py_compile` 并补齐后端测试文件修改 |

## 六、阶段交付物
- PRD：`docs/prd/prd-aggregate-document-summary-priority-governance-2026-03-31.md`
- 开发计划：`docs/plan/plan-aggregate-document-summary-priority-governance-phase1-2026-03-31.md`
- 代码交付：aggregate document summary priority 协议与 UI 分层
- 验证交付：Vitest、筛选式 typecheck、`py_compile`
- 报告交付：Phase 7.2.53 实施报告

## 七、后续阶段建议
### Phase 7.2.54
- 将 `documentSummarySections` 暴露到后台 metadata 编辑能力，减少 `menu_config.py` 硬编码

### Phase 7.2.55
- 把 aggregate document 的 activity surface 也纳入同类优先级协议，进一步压缩时间线前的噪音区块
