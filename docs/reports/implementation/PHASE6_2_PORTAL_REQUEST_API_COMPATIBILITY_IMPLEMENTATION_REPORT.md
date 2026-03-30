# Phase 6.2 Portal Request API Compatibility Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-28 |
| 涉及阶段 | Phase 6.2 |
| 作者/Agent | Codex |

## 一、实施概述
- 本轮先分析了 [frontend_v2.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/plans/phase5_1_m18_adapter/frontend_v2.md) 与 [frontend_v2.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/plans/phase5_3_depreciation/frontend_v2.md)，再对照现有实现确认优先级。
- 结论是 `Phase 5.1 M18` 仍受后端专用适配器缺失限制，`Phase 5.3` 前端契约测试已基本成立，而 `Phase 6` 门户申请类型与资产操作 API 存在真实运行时错位，因此优先实施门户/资产操作兼容性修复。
- 本次实施补齐了 `transfer / loan / return` 的后端兼容动作，修正了门户申请状态模型与国际化状态集，并修复了退库前端 API 的动态对象解析方式。

### 文件清单
- [operation_service.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/services/operation_service.py)
- [operation.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/viewsets/operation.py)
- [test_api_compat.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/tests/test_api_compat.py)
- [assets.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/api/assets.ts)
- [return.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/api/assets/return.ts)
- [UserPortal.vue](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/UserPortal.vue)
- [portalRequestModel.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/portalRequestModel.ts)
- [portalRequestModel.test.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/portalRequestModel.test.ts)
- [portal.json](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/locales/en-US/portal.json)
- [portal.json](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/locales/zh-CN/portal.json)

### 代码行数统计
- 触达文件总行数：3752
- 已跟踪文件差异统计：417 行新增，54 行删除
- 新增文件：1 个后端兼容测试文件

## 二、与 PRD 对应关系
| PRD / 任务要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 检查 `phase5_1_m18_adapter` 与 `phase5_3_depreciation` 文档并确认缺口 | 已完成 | [PHASE6_2_PORTAL_REQUEST_API_COMPATIBILITY_IMPLEMENTATION_REPORT.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/implementation/PHASE6_2_PORTAL_REQUEST_API_COMPATIBILITY_IMPLEMENTATION_REPORT.md) |
| 验证门户 `pickup / transfer / loan / return` 与后端接口一致性 | 已完成 | [portalRequestModel.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/portalRequestModel.ts), [operation.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/viewsets/operation.py) |
| 实现优先级最高的缺失功能 | 已完成 | [operation_service.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/services/operation_service.py), [UserPortal.vue](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/UserPortal.vue) |
| 中英文国际化补齐 | 已完成 | [portal.json](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/locales/en-US/portal.json), [portal.json](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/locales/zh-CN/portal.json) |
| 增加验证覆盖 | 已完成 | [portalRequestModel.test.ts](/Users/abner/My_Project/HOOK_GZEAMS/frontend/src/views/portal/portalRequestModel.test.ts), [test_api_compat.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/tests/test_api_compat.py) |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| 代码注释使用英文 | 符合 | 本次新增 docstring 与注释均为英文 |
| 后端组件遵循既有基类体系 | 符合 | 未新增绕过基类的新模型 / ViewSet / Service，兼容动作建立在既有 `BaseModelViewSetWithBatch` 与 `BaseCRUDService` 之上 |
| 前端使用 TypeScript 与 Element Plus | 符合 | 门户状态模型与页面状态筛选保持 TypeScript 类型，页面仍基于 Element Plus 组件 |
| 字段与参数命名保持 camelCase 兼容 | 符合 | 前端请求继续支持 camelCase，后端兼容动作同时接受现有字段命名 |
| 国际化双语一致性 | 符合 | `npm run i18n:parity -- --changed` 通过，`portal.json` 无缺失项 |

## 四、创建文件清单
- [test_api_compat.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/assets/tests/test_api_compat.py)

## 五、验证结果
- 前端单测通过：`npm test -- --run src/__tests__/unit/api/business-contract-adapters.spec.ts src/views/portal/portalRequestModel.test.ts`
- i18n 校验通过：`npm run i18n:parity -- --changed`
- Python 语法编译通过：`PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile backend/apps/assets/services/operation_service.py backend/apps/assets/viewsets/operation.py backend/apps/assets/tests/test_api_compat.py`
- 未完成的验证：`python3 backend/manage.py test backend.apps.assets.tests.test_api_compat --settings=config.settings.test`
  原因：当前环境未安装 Django 依赖，无法执行后端运行时测试

## 六、后续建议
- 下一优先级建议回到 `Phase 5.1 M18`，但前提是先补齐真实的 `M18Adapter` 与适配器注册链路，否则前端专项同步功能只能停留在通用任务触发层。
- `Phase 5.3` 可继续补一轮真实数据验证，重点核对折旧页面与后端报表汇总字段在联调环境中的最终表现。
- 资产操作前端列表页仍存在历史状态文案差异，建议后续统一收敛到一套状态字典映射，避免门户页与业务列表页各自维护。
