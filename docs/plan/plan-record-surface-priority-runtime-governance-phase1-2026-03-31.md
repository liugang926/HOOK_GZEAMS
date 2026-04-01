# 开发计划：记录页 Surface Priority 运行时治理

## 文档信息
| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-03-31 |
| 涉及阶段 | Phase 7.2.50 |
| 作者/Agent | Codex |

## 一、目标
- 给 workbench item 补齐 `surfacePriority` 协议
- 让默认记录页只保留 `primary / context` 信息层
- 让 workspace 模式承担 `related / admin` 类型信息
- 控制影响范围，仅对已治理对象启用 page mode 切换

## 二、范围

### 2.1 本阶段实施
1. 扩展 runtime 类型和 contract
2. 扩展 `useObjectWorkbench` 的 surface priority 过滤
3. 改造 `DynamicDetailPage` 的记录页 / 工作台可见面逻辑
4. 给资产与生命周期对象的 workbench 配置批量补 `surface_priority`
5. 增加前后端定向测试
6. 归档 PRD、计划、实施报告

### 2.2 本阶段不实施
1. 不改列表页
2. 不新增后台配置 UI
3. 不扩展 aggregate document summary schema
4. 不改 workflow audit / timeline 结构

## 三、任务拆分

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 设计 surface priority 协议 | PRD、类型定义 |
| 2 | workbench composable 过滤收敛 | `useObjectWorkbench.ts` |
| 3 | 详情页 page mode 可见面收敛 | `DynamicDetailPage.vue` |
| 4 | 后端 menu workbench 元数据装饰 | `menu_config.py` |
| 5 | runtime contract / router 测试补齐 | 前后端测试 |
| 6 | 文档归档 | report + README |

## 四、实施顺序
1. 先定义协议和 contract 校验
2. 再改 composable 过滤规则
3. 再改 detail shell 的 page mode 判定
4. 最后回填 menu metadata 和回归测试

## 五、风险与控制

| 风险 | 影响 | 控制措施 |
|------|------|---------|
| 未治理对象被误过滤 | 详情页信息缺失 | 对未标注 `surfacePriority` 的对象保持兼容，不做强制过滤 |
| page mode 开关扩散过广 | 用户认知混乱 | 仅当对象存在 workspace-only surface 时显示切换 |
| 推荐动作被下沉后用户找不到入口 | 流转效率下降 | 保留 action bar，不用推荐动作卡承担唯一入口 |
| 本地后端测试环境不完整 | 无法完整跑 pytest | 使用 `py_compile` + 前端定向测试，并明确记录 `pytest` 缺失 |

## 六、阶段交付物
- PRD：`docs/prd/prd-record-surface-priority-runtime-governance-2026-03-31.md`
- 开发计划：`docs/plan/plan-record-surface-priority-runtime-governance-phase1-2026-03-31.md`
- 代码交付：surface priority 协议与详情页减载逻辑
- 验证交付：Vitest、py_compile、筛选式 typecheck
- 报告交付：Phase 7.2.50 实施报告

## 七、后续阶段建议
### Phase 7.2.51
- 将 `ClosedLoopNavigationCard`、`Process Summary`、`Hero stats` 接入同一 surface schema

### Phase 7.2.52
- 在后台元数据管理界面暴露 surface priority 配置，减少 `menu_config.py` 手工维护
