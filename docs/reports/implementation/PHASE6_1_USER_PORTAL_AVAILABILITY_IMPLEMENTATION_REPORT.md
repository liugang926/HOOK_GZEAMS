# Phase 6.1 User Portal Availability Implementation Report

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-28 |
| 涉及阶段 | Phase 6.1 |
| 作者/Agent | Codex |

## 一、实施概述
- 本次实施聚焦用户门户可用性修复，优先解决门户菜单不可见和待办详情跳转错误两个阻塞项。
- 后端在 `STATIC_MENU_ITEMS` 中补充 `UserPortal` 静态菜单项，确保 `/api/system/menu/` 同步时能注册 `/portal` 导航入口。
- 前端将门户待办详情跳转从旧任务页修正为审批详情页 `/workflow/approvals/:taskId`，与现有 `ApprovalDetail` 路由保持一致。
- 现状复核结果显示 `frontend/src/locales/zh-CN/portal.json`、`frontend/src/locales/en-US/portal.json` 以及两端 `index.ts` 导入已存在，本阶段未重复创建。

文件清单与当前文件行数统计：

| 文件 | 作用 | 当前行数 |
|------|------|---------|
| `backend/apps/system/menu_config.py` | 注册 `UserPortal` 静态菜单项 | 1610 |
| `backend/apps/system/tests/test_menu_config_sync.py` | 新增门户菜单同步回归用例 | 170 |
| `frontend/src/views/portal/portalTaskModel.ts` | 修正门户待办详情路径 | 24 |
| `frontend/src/views/portal/portalTaskModel.test.ts` | 更新门户待办路径断言 | 26 |

验证结果：
- `npx vitest run src/views/portal/portalTaskModel.test.ts`：通过
- `PYTHONPYCACHEPREFIX=/tmp/pycache python3 -m py_compile backend/apps/system/menu_config.py backend/apps/system/tests/test_menu_config_sync.py`：通过
- 后端 `pytest` 运行：当前本机无 `pytest`，Docker API 亦被沙箱限制，未完成运行级验证

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 用户门户需要可从系统菜单进入 | 已完成 | `backend/apps/system/menu_config.py` |
| 门户待办需跳转到正确审批详情页 | 已完成 | `frontend/src/views/portal/portalTaskModel.ts` |
| 门户国际化需具备中英文资源并接入入口 | 已确认已存在 | `frontend/src/locales/zh-CN/portal.json` |
| 门户国际化需具备中英文资源并接入入口 | 已确认已存在 | `frontend/src/locales/en-US/portal.json` |
| 门户国际化需在 locale 聚合入口注册 | 已确认已存在 | `frontend/src/locales/zh-CN/index.ts` |
| 门户国际化需在 locale 聚合入口注册 | 已确认已存在 | `frontend/src/locales/en-US/index.ts` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|--------|------|------|
| 统一菜单注册 | 符合 | 使用 `apps.system.menu_config.STATIC_MENU_ITEMS`，未新增独立菜单机制 |
| 前端路由一致性 | 符合 | 使用既有 `ApprovalDetail` 路由协议 `/workflow/approvals/:taskId` |
| 国际化接入 | 符合 | 复核确认 `portal` locale 已接入，无重复定义 |
| 英文注释规范 | 符合 | 本次代码改动未新增非英文注释 |
| 最小化变更原则 | 符合 | 仅调整菜单注册、路径 helper 与对应测试 |

## 四、创建文件清单
- `docs/reports/implementation/PHASE6_1_USER_PORTAL_AVAILABILITY_IMPLEMENTATION_REPORT.md`

变更文件清单：
- `backend/apps/system/menu_config.py`
- `backend/apps/system/tests/test_menu_config_sync.py`
- `frontend/src/views/portal/portalTaskModel.ts`
- `frontend/src/views/portal/portalTaskModel.test.ts`

## 五、后续建议
- 继续执行 Phase 6 第二阶段，核对门户申请类型与后端对象/动作接口的一致性，重点验证 `transfer` 流程。
- 在具备 Docker 或 Python 测试依赖的环境中补跑 `backend/apps/system/tests/test_menu_config_sync.py`。
- 通过 `/api/system/menu/` 或 `/api/system/menu/flat` 做一次接口级冒烟，确认 `UserPortal` 已出现在 `workflow` 分组中。
