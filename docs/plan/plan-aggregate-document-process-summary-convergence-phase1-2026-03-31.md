# 开发计划：Aggregate Document Process Summary 收敛

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.52 |
| 作者/Agent | Codex |

## 一、目标
- 让 aggregate document 与 dynamic detail 使用同一套 `Process Summary` surface
- 收敛单据页 summary surface 中重复的 signal / stage / navigation 卡片
- 降低单据页 header 与 summary 之间的重复摘要

## 二、范围

### 2.1 本阶段实施
1. 新增 document process summary view model builder
2. 扩展 `useDocumentWorkbenchState`
3. 改造 `DocumentWorkbench` summary surface
4. 补齐 view model 与组件回归测试
5. 归档 PRD、计划、实施报告

### 2.2 本阶段不实施
1. 不调整 aggregate document API
2. 不修改 activity / timeline surface
3. 不改 batch tools 交互
4. 不新增后台 metadata 配置

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 设计 document process summary 协议 | PRD |
| 2 | 新增 process summary stats / rows builder | `documentWorkbenchViewModel.ts` |
| 3 | 扩展 workbench state 装配 | `useDocumentWorkbenchState.ts` |
| 4 | 替换 summary surface 旧卡片 | `DocumentWorkbench.vue` |
| 5 | 增加回归测试 | Vitest |
| 6 | 文档归档 | report + README |

## 四、实施顺序
1. 先补 view model builder
2. 再接入 workbench state
3. 再替换模板层旧卡片
4. 最后补测试与实施报告

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| 单据页流程摘要丢失关键信息 | 用户看不到 latest signal / progress | 将 workflow progress 与 latest signal 一并并入 `Process Summary` |
| summary surface 过度压缩 | 用户难以区分主次信息 | 保留 `Record`、`Workflow`、`Batch Tools` 为次级卡片 |
| 现有单据跳转回归 | 无法访问关联记录 | 继续复用 `navigationSection` 与既有 `handleClosedLoopNavigation` |
| 类型系统因新增 builder 产生回归 | 前端编译不稳定 | 使用筛选式 `typecheck` 检查本轮触达文件 |

## 六、阶段交付物
- PRD：`docs/prd/prd-aggregate-document-process-summary-convergence-2026-03-31.md`
- 开发计划：`docs/plan/plan-aggregate-document-process-summary-convergence-phase1-2026-03-31.md`
- 代码交付：aggregate document `Process Summary` 收敛
- 验证交付：Vitest、筛选式 typecheck
- 报告交付：Phase 7.2.52 实施报告

## 七、后续阶段建议
### Phase 7.2.53
- 将 `Record / Workflow / Batch Tools` 继续按 `surfacePriority` 分类，控制单据页 summary surface 的信息密度

### Phase 7.2.54
- 将 aggregate document 的 `Process Summary` 也元数据化，减少 `DocumentWorkbench` 中硬编码的对象特例
