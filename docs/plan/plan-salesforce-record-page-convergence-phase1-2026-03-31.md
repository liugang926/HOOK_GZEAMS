# 开发计划：Salesforce 风格对象页收敛 Phase 1

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.48 |
| 作者/Agent | Codex |

## 一、目标
- 将默认记录页恢复为“记录优先、流程分层展开”的交互结构。
- 将聚合单据页从纵向堆叠改为多 surface 分层展示。
- 保留闭环、原因信号、动作协议与时间线能力。

## 二、范围

### 2.1 本阶段实施
1. `DocumentWorkbench` 拆分 `Summary / Form / Activity` 三个页签
2. `DynamicDetailPage` 的 detail surface 行为补齐 locale 与回归测试
3. 增加 hash 与 surface tab 的联动
4. 补齐中英文 locale key
5. 补齐 Vitest 回归

### 2.2 本阶段不实施
1. 不增加 metadata 持久化配置项
2. 不改后端 API
3. 不调整 workbench action 协议
4. 不扩展列表摘要列

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 详情页结构审视与收敛策略确认 | PRD、页面壳层方案 |
| 2 | 聚合单据页 surface 拆分 | `DocumentWorkbench.vue` |
| 3 | hash 联动与默认 surface 规则 | 组件脚本逻辑 |
| 4 | 国际化补齐 | `common.json` |
| 5 | 定向回归测试 | 两组 Vitest |
| 6 | 实施归档 | 实施报告、README 索引 |

## 四、实施顺序
1. 先改 `DocumentWorkbench` 结构，防止继续在默认单据页增加一级卡片。
2. 再补 locale，确保新页签不会裸露 key。
3. 再补 `DynamicDetailPage` 的 hash 切换验证，锁定详情页 surface 行为。
4. 最后跑定向测试并生成归档文档。

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| 现有跳转依赖 hash | 活动面不可达 | 增加 hash -> surface 同步逻辑与回归测试 |
| 只读/编辑场景默认页签不同 | 用户首屏认知混乱 | 规定只读默认 `Summary`，编辑默认 `Form` |
| locale key 缺失 | 页面出现原始 key | 补齐中英文 locale 并校验 JSON |
| 仓库存量 typecheck 问题 | 难以用全量类型检查做验收 | 以定向 Vitest + locale 校验为主，并单独记录存量风险 |

## 六、阶段交付物
- PRD：`docs/prd/prd-salesforce-record-page-convergence-2026-03-31.md`
- 开发计划：`docs/plan/plan-salesforce-record-page-convergence-phase1-2026-03-31.md`
- 代码交付：详情页/聚合单据页收敛
- 验证交付：Vitest 定向回归、locale JSON 校验
- 报告交付：Phase 7.2.48 实施报告

## 七、后续阶段建议
### Phase 2
- 将 `surfacePriority/defaultPageMode` 元数据化
- 把列表页摘要列和 detail hero 指标映射到同一配置协议

### Phase 3
- 将 workflow audit、recommended actions、queue panels 再收敛到统一 process summary 协议
