# PHASE7_2_20_DEMO_DATA_SMOKE_TEST_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-21 |
| 涉及阶段 | Phase 7.2.20 |
| 作者/Agent | Codex |

## 一、实施概述
- 在 [test_create_demo_data_command.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/tests/test_create_demo_data_command.py) 新增 `call_command("create_demo_data")` 的 smoke test，用小样本组织直接验证命令入口可运行成功。
- 根据 smoke test 暴露的真实边界问题，修复了 [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) 两处 small-count 缺陷：
  - `AssetReturn` 明细生成在资产池耗尽时不再插入 `asset=None` 的 `ReturnItem`
  - `InventorySnapshot` 在资产数量少于 10 时改为自适应随机范围，不再触发 `randrange()` 空区间错误
- 定向 Docker 回归现已全绿，命令入口 smoke test 可稳定覆盖这些边界。

文件清单与行数统计：
- [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) - 2,519 行
- [test_create_demo_data_command.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/tests/test_create_demo_data_command.py) - 176 行
- [README.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/README.md) - 216 行

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 演示数据命令需要支持开发/测试环境的快速 smoke 验证 | 已完成 | `test_create_demo_data_command.py` 中 smoke test |
| 小样本 seed 不应因边界资产数量导致命令失败 | 已完成 | `create_demo_data.py` 中 `_create_asset_returns()`、`_create_inventory_snapshots()` |
| 回归测试需要覆盖真实命令入口而不只验证 helper | 已完成 | `call_command("create_demo_data")` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| English comments only | ✅ | 本轮未新增非英文代码注释 |
| 管理命令单入口 | ✅ | 继续通过 `python manage.py create_demo_data` 暴露能力 |
| Docker 运行态验证 | ✅ | 定向 `pytest` 已在容器内通过 |
| 报告索引更新 | ✅ | 已更新 `docs/reports/README.md` |

## 四、创建文件清单
- 新建 [PHASE7_2_20_DEMO_DATA_SMOKE_TEST_IMPLEMENTATION_REPORT.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/implementation/PHASE7_2_20_DEMO_DATA_SMOKE_TEST_IMPLEMENTATION_REPORT.md)

## 五、验证结果
- `python3 -m py_compile backend/apps/common/management/commands/create_demo_data.py backend/apps/common/tests/test_create_demo_data_command.py`：通过
- `docker compose exec -T backend pytest apps/common/tests/test_create_demo_data_command.py -q`：通过
- 测试结果：`7 passed in 46.19s`
- smoke test 关键断言：
  - 新组织上命令执行成功并输出 `Demo data creation completed!`
  - `Supplier=10`
  - `Asset=1`
  - `AssetProject=20`
  - `FinanceVoucher=20`
  - `PurchaseRequest=1`
  - `AssetReturn=20`
  - `InventoryTask=20`

## 六、后续建议
- 下一步可增加 `--skip-existing --top-up-existing` 的命令入口 smoke test，补齐“首次 seed + 复跑补量”双入口回归。
- 如果后续还要扩更多小样本开发场景，建议把 `count=1` 明确纳入 demo data 的兼容基线。
