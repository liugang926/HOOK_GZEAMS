# PHASE7_2_21_DEMO_DATA_TOP_UP_SMOKE_TEST_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-22 |
| 涉及阶段 | Phase 7.2.21 |
| 作者/Agent | Codex |

## 一、实施概述
- 在 [test_create_demo_data_command.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/tests/test_create_demo_data_command.py) 增加 `create_demo_data` 的 top-up 复跑 smoke test，覆盖 `--skip-existing --top-up-existing` 的真实命令入口行为。
- 测试以新组织上的 `count=1` 首跑为起点，再执行一次 top-up 复跑，验证命令只修复启用了 top-up 的对象，而不会误补不走 top-up 的对象。
- Docker 容器内定向回归已通过，命令入口现在同时具备“首跑 smoke”与“复跑补量 smoke”双重验证。

文件清单与行数统计：
- [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) - 2,519 行
- [test_create_demo_data_command.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/tests/test_create_demo_data_command.py) - 222 行
- [README.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/README.md) - 220 行

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 演示数据命令需要支持首跑后复跑补量验证 | 已完成 | `test_create_demo_data_command.py` 中 top-up smoke test |
| top-up 模式只能补齐启用补量的对象，不能误改普通对象数量 | 已完成 | `test_create_demo_data_command.py` 中 `InventoryScan / Asset / PurchaseRequest` 断言 |
| 复跑命令入口应可在 Docker 测试环境稳定执行 | 已完成 | 容器内 `pytest` 定向验证 |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| English comments only | ✅ | 本轮未新增非英文代码注释 |
| 命令入口自动化验证 | ✅ | 已覆盖首次 seed 与 top-up 复跑 |
| Docker 运行态验证 | ✅ | `8 passed` 定向回归已通过 |
| 报告索引更新 | ✅ | 已更新 `docs/reports/README.md` |

## 四、创建文件清单
- 新建 [PHASE7_2_21_DEMO_DATA_TOP_UP_SMOKE_TEST_IMPLEMENTATION_REPORT.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/implementation/PHASE7_2_21_DEMO_DATA_TOP_UP_SMOKE_TEST_IMPLEMENTATION_REPORT.md)

## 五、验证结果
- `python3 -m py_compile backend/apps/common/tests/test_create_demo_data_command.py backend/apps/common/management/commands/create_demo_data.py`：通过
- `docker compose exec -T backend python manage.py check`：通过，保留 3 个既有 warning
- `docker compose exec -T backend pytest apps/common/tests/test_create_demo_data_command.py -q`：通过
- 测试结果：`8 passed in 47.28s`
- top-up smoke test 关键断言：
  - 首跑后 `InventoryScan=1`
  - top-up 复跑后 `InventoryScan=20`
  - `Asset=1` 在复跑后保持不变
  - `PurchaseRequest=1` 在复跑后保持不变
  - 复跑输出包含 `Topped up inventory scans by`

## 六、后续建议
- 下一步可以把这组 smoke test 再扩一条 `--skip-existing` 非 top-up 复跑断言，验证“仅复用，不补量”的第三条命令入口路径。
- 如果后续继续扩 demo data 对象，优先为 top-up 行为补入口 smoke test，再增加对象级断言。
