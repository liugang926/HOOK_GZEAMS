# GZEAMS Object History Convergence Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-25 |
| 涉及阶段 | Object Layering & History Convergence |
| 作者/Agent | Codex |
| 对应 PRD | `docs/prd/prd-object-layering-history-convergence-2026-03-25.md` |

## 一、实施概述

### 任务清单
1. 收敛 `AssetStatusLog` 与 `ConfigurationChange` 的对象协议，归类为 `log` 审计对象。
2. 为对象路由新增统一 `history` 聚合接口，合并 Activity Log、Asset Status Log、Configuration Change。
3. 调整详情页历史数据来源，默认改走对象级 `history` 接口。
4. 调整详情页 `Related` 过滤规则，排除 `log/history` 关系。
5. 调整前端菜单 fallback 规则，排除 `log` 对象与 `allowStandaloneRoute=false` 对象。
6. 补充后端与前端定向测试，验证对象协议、关系元数据、历史聚合与菜单兜底行为。

### 完成情况
- 已完成对象协议收敛：`AssetStatusLog`、`ConfigurationChange` 默认隐藏菜单，禁止顶层导航，禁止独立业务路由。
- 已完成后端统一历史接口：`GET /api/system/objects/{code}/{id}/history/`。
- 已完成详情页去重：`ChangeHistory` 统一聚合，`Related` 不再显示审计型变更关系。
- 已完成菜单兜底收敛：即使菜单 API fallback 到 BusinessObject 也不会重新暴露审计对象。
- 已完成定向测试验证。

### 文件统计
- 影响文件数：17
- 影响文件总行数：5209

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 审计对象从业务导航中收敛为 `log` 类型 | 已完成 | `backend/apps/system/object_catalog.py` |
| 现存元数据与关系定义需通过迁移持久化收敛 | 已完成 | `backend/apps/system/migrations/0051_object_history_convergence.py` |
| 详情页历史改为统一聚合接口 | 已完成 | `backend/apps/system/services/object_history_aggregation_service.py` |
| 对象路由暴露统一历史入口 | 已完成 | `backend/apps/system/viewsets/object_router_relation_actions.py`、`backend/apps/system/urls.py` |
| `Related` 标签页只保留业务关系，不再混入历史关系 | 已完成 | `frontend/src/components/common/useBaseDetailPageRelations.ts` |
| 前端菜单 fallback 不应重新暴露审计对象 | 已完成 | `frontend/src/router/menuRegistry.ts` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|--------|------|------|
| Dynamic Object Routing | ✅ | 新接口通过 `/api/system/objects/{code}/{id}/history/` 挂载，无新增独立业务 URL 配置 |
| Unified API Response | ✅ | 历史接口通过 `BaseResponse.paginated()` 返回统一分页格式 |
| Metadata-Driven Object Protocol | ✅ | 审计对象协议字段通过 hardcoded catalog + 数据迁移双层收敛 |
| Frontend Consistency | ✅ | 详情页历史与 Related 分工明确，菜单 fallback 与后端对象协议一致 |
| English Comments Only | ✅ | 本次新增代码未引入中文注释 |

## 四、创建文件清单
- `backend/apps/system/services/object_history_aggregation_service.py`
- `backend/apps/system/migrations/0051_object_history_convergence.py`
- `backend/apps/system/tests/test_object_router_history.py`
- `docs/reports/summaries/GZEAMS_OBJECT_HISTORY_CONVERGENCE_REPORT.md`

## 五、变更文件清单
- `backend/apps/system/object_catalog.py`
- `backend/apps/system/menu_config.py`
- `backend/apps/system/viewsets/object_router_relation_actions.py`
- `backend/apps/system/urls.py`
- `backend/apps/system/tests/test_master_detail_protocol.py`
- `backend/apps/system/tests/test_menu_config_sync.py`
- `backend/apps/system/tests/test_object_router_relations.py`
- `frontend/src/composables/useActivityTimeline.ts`
- `frontend/src/components/common/useBaseDetailPageRelations.ts`
- `frontend/src/router/menuRegistry.ts`
- `frontend/src/components/common/__tests__/useBaseDetailPageRelations.spec.ts`
- `frontend/src/router/menuRegistry.test.ts`
- `frontend/src/__tests__/unit/components/common/ActivityTimeline.spec.ts`
- `docs/prd/prd-object-layering-history-convergence-2026-03-25.md`

## 六、验证结果
- 后端：`docker compose exec -T backend pytest apps/system/tests/test_master_detail_protocol.py apps/system/tests/test_menu_config_sync.py apps/system/tests/test_object_router_relations.py apps/system/tests/test_object_router_history.py -q`
  - 结果：25 passed in 48.82s
- 前端：`cd frontend && npm test -- --run src/components/common/__tests__/useBaseDetailPageRelations.spec.ts src/router/menuRegistry.test.ts src/__tests__/unit/components/common/ActivityTimeline.spec.ts`
  - 结果：13 passed in 668ms

## 七、后续建议
- 执行 `docker compose exec backend python manage.py migrate`，将 `0051_object_history_convergence` 应用到目标环境。
- 在测试/预发环境复跑 `sync_schemas` 与菜单校验，确认历史关系不再出现在 `Related`。
- 后续如果要彻底收口后台入口，可继续评估旧静态列表页是否转为管理员专用入口或并入统一审计中心。
