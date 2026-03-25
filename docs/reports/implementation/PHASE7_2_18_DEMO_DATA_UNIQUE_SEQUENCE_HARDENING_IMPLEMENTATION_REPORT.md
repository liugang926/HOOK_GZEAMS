# PHASE7_2_18_DEMO_DATA_UNIQUE_SEQUENCE_HARDENING_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-21 |
| 涉及阶段 | Phase 7.2.18 |
| 作者/Agent | Codex |

## 一、实施概述
- 在 [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) 加固了前缀序列生成逻辑，修复 mixed-width suffix 场景下的最大号段判断错误，避免新组织首次 seed 命中历史 demo 编码冲突。
- 将供应商、易耗品分类、易耗品、采购申请等仍依赖固定编码或易冲突前缀的对象切换到 organization-aware 或 numeric max-sequence 生成策略。
- 在 Docker 开发环境完成了 fresh-org 首次 seed 和 `--skip-existing --top-up-existing` 复跑验证，确认日志中无 `RuntimeWarning: DateTimeField`、`IntegrityError`、`UniqueViolation`。

文件清单与行数统计：
- [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) - 2,510 行
- [DEMO_DATA_COMMAND_QUICK_START.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/quickstart/DEMO_DATA_COMMAND_QUICK_START.md) - 461 行
- [README.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/README.md) - 214 行

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 演示数据应支持跨对象关联关系闭环，并可在开发环境稳定重复执行 | 已完成 | `create_demo_data.py` 中 `_next_prefixed_sequence()` 与各 `_create_*` seed 方法 |
| 单据与主数据编码应避免跨组织冲突，不能因历史 demo 数据导致首跑失败 | 已完成 | `create_demo_data.py` 中 suppliers / consumables / purchase requests / finance voucher related helpers |
| 快速入门文档应反映首跑与复跑策略 | 已完成 | `DEMO_DATA_COMMAND_QUICK_START.md` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| English comments only | ✅ | 本轮未新增非英文代码注释 |
| 单命令统一入口 | ✅ | 继续通过 `python manage.py create_demo_data` 暴露能力 |
| Docker 运行态验证 | ✅ | 已在容器内完成 fresh-org 首跑与 top-up 复跑 |
| 报告索引更新 | ✅ | 已更新 `docs/reports/README.md` |

## 四、创建文件清单
- 新建 [PHASE7_2_18_DEMO_DATA_UNIQUE_SEQUENCE_HARDENING_IMPLEMENTATION_REPORT.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/implementation/PHASE7_2_18_DEMO_DATA_UNIQUE_SEQUENCE_HARDENING_IMPLEMENTATION_REPORT.md)

## 五、验证结果
- `python3 -m py_compile backend/apps/common/management/commands/create_demo_data.py`：通过
- `docker compose exec -T backend python manage.py create_demo_data --organization f3f909a6-e50f-425a-a85a-f6d8ef0db4c7 --count 20`：通过
- `docker compose exec -T backend python manage.py create_demo_data --organization f3f909a6-e50f-425a-a85a-f6d8ef0db4c7 --count 20 --skip-existing --top-up-existing`：通过
- 关键 fresh-org 首跑结果：
  - `asset_projects=20`
  - `project_members=59`
  - `finance_vouchers=20`
  - `consumables=20`
  - `purchase_requests=20`
  - `inventory_tasks=20`
  - `total records created=886`
- 日志检查：
  - `/tmp/create_demo_data_seedwarn0321d.log` 未命中 `RuntimeWarning: DateTimeField|IntegrityError|UniqueViolation`
  - `/tmp/create_demo_data_seedwarn0321d_topup.log` 未命中 `RuntimeWarning: DateTimeField|IntegrityError|UniqueViolation`
- 复跑结果：
  - 所有关键对象均输出 `Using existing ...`
  - 未发生重复插入或补量漂移

## 六、后续建议
- 为 `create_demo_data` 增加自动化回归测试，覆盖 fresh-org 首跑、legacy mixed-width code、以及 `--skip-existing --top-up-existing` 三类场景。
- 继续清理 Django system check 的现存 warning，例如 `/app/static` 缺失和 `Comment` 模型 `db_comment` 提示。
