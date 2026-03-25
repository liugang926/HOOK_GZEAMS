# PHASE7_2_17_DEMO_DATA_DATETIME_WARNING_FIX_IMPLEMENTATION_REPORT

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-03-21 |
| 涉及阶段 | Phase 7.2.17 |
| 作者/Agent | Codex |

## 一、实施概述
- 在 [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py) 新增统一的 timezone-aware datetime helper，用于将基于 `date` 的业务时间种子转换为带时区的 `datetime`。
- 将易耗品采购/领用、采购申请、资产验收、处置、领用、转移、借用、盘点任务等 demo data 中原先直接写入 `DateTimeField` 的 `date + timedelta(...)` 赋值全部切换到统一 helper。
- 更新 [DEMO_DATA_COMMAND_QUICK_START.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/quickstart/DEMO_DATA_COMMAND_QUICK_START.md)，补充该命令已按时区感知方式生成流程时间字段。

文件清单：
- [create_demo_data.py](/Users/abner/My_Project/HOOK_GZEAMS/backend/apps/common/management/commands/create_demo_data.py)
- [DEMO_DATA_COMMAND_QUICK_START.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/quickstart/DEMO_DATA_COMMAND_QUICK_START.md)

## 二、与 PRD 对应关系
| PRD 要求 | 实现状态 | 代码位置 |
|----------|---------|---------|
| 开发演示数据需要可稳定执行，不应因时区写入告警污染验证输出 | 已完成 | `create_demo_data.py` 中 `_seed_datetime()` |
| 单据对象与流程对象的时间字段应保持一致的生成规范 | 已完成 | `create_demo_data.py` 中 consumables / lifecycle / assets / inventory 相关 seed 方法 |
| 快速入门文档需反映命令当前行为 | 已完成 | `DEMO_DATA_COMMAND_QUICK_START.md` |

## 三、规范遵循验证
| 规范项 | 状态 | 说明 |
|------|------|------|
| English comments only | ✅ | 本轮未新增非英文代码注释 |
| 管理命令单入口 | ✅ | 继续沿用 `python manage.py create_demo_data` |
| 统一时间生成规则 | ✅ | 新增 `_seed_datetime()` 并统一复用 |
| 运行态验证 | ✅ | 已在 2026-03-21 同日 Docker 环境补跑新组织首次 seed，详见 `PHASE7_2_18` |

## 四、创建文件清单
- 新建 [PHASE7_2_17_DEMO_DATA_DATETIME_WARNING_FIX_IMPLEMENTATION_REPORT.md](/Users/abner/My_Project/HOOK_GZEAMS/docs/reports/implementation/PHASE7_2_17_DEMO_DATA_DATETIME_WARNING_FIX_IMPLEMENTATION_REPORT.md)

## 五、验证结果
- `python3 -m py_compile backend/apps/common/management/commands/create_demo_data.py`：通过
- `docker compose exec -T backend python manage.py create_demo_data --organization f3f909a6-e50f-425a-a85a-f6d8ef0db4c7 --count 20`：通过
- 新组织首次 seed 日志未命中 `RuntimeWarning: DateTimeField`
- 静态审查确认以下历史 warning 来源已切换到 timezone-aware helper：
  - `ConsumablePurchase.approved_at / received_at`
  - `ConsumableIssue.approved_at / issued_at`
  - `PurchaseRequest.approved_at`
  - `AssetReceipt.passed_at`
  - `DisposalItem.appraised_at / executed_at`
  - `AssetPickup.approved_at / completed_at`
  - `AssetTransfer.from_approved_at / to_approved_at / completed_at`
  - `AssetLoan.approved_at / lent_at / returned_at`
  - `InventoryTask.started_at / completed_at`

## 六、后续建议
- 为 `_seed_datetime()` 和 `_next_prefixed_sequence()` 增加独立单元测试，避免后续 seed 逻辑回退。
- 继续处理命令中剩余的统计一致性问题，例如 `InventorySnapshot` 数量天然高于主表数量时的输出解释。
