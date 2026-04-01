# 开发计划：Process Summary Surface 收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.51 |
| 作者/Agent | Codex |

## 一、目标
- 将默认记录页中的流程摘要能力并到单一 `Process Summary` surface
- 让 hero 回到轻量记录头部，而不是继续堆流程 stats
- 消除 `closure summary` 与 `closed-loop navigation` 的并列展示
- 保持 detail navigation、activity hash 和 runtime page mode 兼容

## 二、范围

### 2.1 本阶段实施
1. 新增 `ProcessSummaryPanel` 组件
2. 拆分 detail workspace 的 `heroStats / processSummaryStats`
3. 改造 `DynamicDetailPage`，用统一 process summary surface 替换旧布局
4. 补齐中英文文案
5. 增加组件、workspace、详情页定向测试
6. 归档 PRD、计划和实施报告

### 2.2 本阶段不实施
1. 不改 aggregate document workbench
2. 不调整对象动作或权限协议
3. 不新增后端接口或数据库 schema
4. 不在后台元数据管理界面暴露新的 surface 配置

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 设计统一 process summary surface | PRD |
| 2 | 新增组件并定义输入协议 | `ProcessSummaryPanel.vue` |
| 3 | 收敛 detail workspace 视图模型 | `useDynamicDetailWorkspace.ts` |
| 4 | 改造详情页布局 | `DynamicDetailPage.vue` |
| 5 | 补齐测试与 locale | Vitest + locale keys |
| 6 | 文档归档 | report + README |

## 四、实施顺序
1. 先补统一组件
2. 再拆 workspace view model 的 stats 来源
3. 再替换 detail page 中旧 surface
4. 最后补测试、文案与报告

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| 记录页顶部信息过少 | 用户误判页面缺信息 | 保留 header 主字段与状态，流程摘要下沉到紧随其后的 process surface |
| 导航按钮事件回归 | 无法跳转关联对象 | 复用 detail navigation 既有 `select` 事件链路并补测试 |
| 旧对象空 surface 占位 | 记录页出现空卡片 | `ProcessSummaryPanel` 无内容时完全隐藏 |
| 全量 typecheck 存量错误干扰 | 无法判断本轮质量 | 使用筛选式 `typecheck` 检查本轮触达文件 |

## 六、阶段交付物
- PRD：`docs/prd/prd-process-summary-surface-convergence-2026-03-31.md`
- 开发计划：`docs/plan/plan-process-summary-surface-convergence-phase1-2026-03-31.md`
- 代码交付：统一 `Process Summary` surface 与 detail hero 减载
- 验证交付：Vitest、locale JSON 校验、筛选式 typecheck
- 报告交付：Phase 7.2.51 实施报告

## 七、后续阶段建议
### Phase 7.2.52
- 将 aggregate document 的 signal / stage / workflow summary 继续收敛到同一 `Process Summary` 协议

### Phase 7.2.53
- 把 `Process Summary` 的 surface schema 暴露到 runtime metadata，降低 `DynamicDetailPage` 中的特例逻辑
