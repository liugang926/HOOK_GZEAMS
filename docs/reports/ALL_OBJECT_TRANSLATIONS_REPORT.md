# All Object Translations Completion Report

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Created Date | 2026-02-28 |
| Module | Backend Translation Initialization |

## Summary

Created a comprehensive management command `init_all_translations.py` to initialize translations for all business objects, dictionary types, and dictionary items in the system.

## File Created

**`backend/apps/system/management/commands/init_all_translations.py`**

This command initializes:
1. Static translations (buttons, status, labels)
2. BusinessObject name translations
3. DictionaryType name translations
4. DictionaryItem name translations

## Translation Coverage

### 1. Static Translations (43 keys)

**Buttons (21 keys)**
- button.save, button.cancel, button.confirm, button.add, button.edit
- button.delete, button.export, button.import, button.search, button.reset
- button.submit, button.approve, button.reject, button.back, button.close
- button.refresh, button.download, button.upload, button.print, button.view
- button.create, button.update

**Status (16 keys)**
- status.active, status.inactive, status.enabled, status.disabled
- status.idle, status.in_use, status.maintenance, status.pending
- status.approved, status.rejected, status.draft, status.completed
- status.cancelled, status.in_progress, status.locked, status.archived

**Labels (22 keys)**
- label.yes, label.no, label.all, label.name, label.code
- label.description, label.remark, label.notes, label.created_at, label.updated_at
- label.created_by, label.updated_by, label.actions, label.status, label.type
- label.category, label.quantity, label.amount, label.price, label.date
- label.time, label.user, label.department, label.location, label.address
- label.phone, label.email, label.attachment, label.image, label.file

### 2. BusinessObject Translations (37 objects)

| Code | zh-CN | en-US |
|------|-------|-------|
| Asset | 固定资产 | Fixed Asset |
| AssetCategory | 资产分类 | Asset Category |
| Location | 存放位置 | Storage Location |
| Supplier | 供应商 | Supplier |
| AssetPickup | 资产领用 | Asset Pickup |
| AssetTransfer | 资产调拨 | Asset Transfer |
| AssetReturn | 资产退库 | Asset Return |
| AssetLoan | 资产借用 | Asset Loan |
| Consumable | 耗材 | Consumable |
| ConsumableCategory | 耗材分类 | Consumable Category |
| ConsumableStock | 耗材库存 | Consumable Stock |
| ConsumablePurchase | 耗材采购 | Consumable Purchase |
| ConsumableIssue | 耗材领用 | Consumable Issue |
| PurchaseRequest | 采购申请 | Purchase Request |
| InventoryTask | 盘点任务 | Inventory Task |
| InventorySnapshot | 资产快照 | Asset Snapshot |
| InventoryItem | 盘点明细 | Inventory Item |
| Maintenance | 维修记录 | Maintenance Record |
| MaintenanceTask | 维修任务 | Maintenance Task |
| DisposalRequest | 报废申请 | Disposal Request |
| Voucher | 财务凭证 | Finance Voucher |
| VoucherTemplate | 凭证模板 | Voucher Template |
| DepreciationConfig | 折旧配置 | Depreciation Config |
| DepreciationRecord | 折旧记录 | Depreciation Record |
| ITAsset | IT资产 | IT Asset |
| ITMaintenanceRecord | IT维护记录 | IT Maintenance Record |
| ConfigurationChange | 配置变更 | Configuration Change |
| Software | 软件目录 | Software Catalog |
| SoftwareLicense | 软件许可 | Software License |
| LicenseAllocation | 许可证分配 | License Allocation |
| LeasingContract | 租赁合同 | Leasing Contract |
| LeaseItem | 租赁明细 | Lease Item |
| LeaseExtension | 租赁展期 | Lease Extension |
| LeaseReturn | 租赁归还 | Lease Return |
| RentPayment | 租金支付 | Rent Payment |
| InsuranceCompany | 保险公司 | Insurance Company |
| InsurancePolicy | 保险保单 | Insurance Policy |
| InsuredAsset | 参保资产 | Insured Asset |
| PremiumPayment | 保费支付 | Premium Payment |
| ClaimRecord | 理赔记录 | Claim Record |
| PolicyRenewal | 保单续保 | Policy Renewal |
| WorkflowDefinition | 工作流定义 | Workflow Definition |
| WorkflowInstance | 工作流实例 | Workflow Instance |
| WorkflowTask | 工作流任务 | Workflow Task |

### 3. DictionaryType Translations (31 types)

| Code | zh-CN | en-US |
|------|-------|-------|
| ASSET_STATUS | 资产状态 | Asset Status |
| ASSET_TYPE | 资产类型 | Asset Type |
| ASSET_CATEGORY | 资产分类 | Asset Category |
| UNIT | 计量单位 | Unit |
| ASSET_BRAND | 资产品牌 | Asset Brand |
| DEPRECIATION_METHOD | 折旧方法 | Depreciation Method |
| INVENTORY_DISCREPANCY_TYPE | 盘点差异类型 | Inventory Discrepancy Type |
| INVENTORY_STATUS | 盘点状态 | Inventory Status |
| INVENTORY_TYPE | 盘点类型 | Inventory Type |
| MAINTENANCE_TYPE | 维护类型 | Maintenance Type |
| MAINTENANCE_STATUS | 维护状态 | Maintenance Status |
| CONSUMABLE_TYPE | 耗材类型 | Consumable Type |
| CONSUMIBLE_CATEGORY | 耗材分类 | Consumable Category |
| VOUCHER_STATUS | 凭证状态 | Voucher Status |
| VOUCHER_TYPE | 凭证类型 | Voucher Type |
| SOFTWARE_TYPE | 软件类型 | Software Type |
| LICENSE_TYPE | 许可类型 | License Type |
| LICENSE_STATUS | 许可状态 | License Status |
| ALLOCATION_STATUS | 分配状态 | Allocation Status |
| LEASE_STATUS | 租赁状态 | Lease Status |
| INSURANCE_TYPE | 保险类型 | Insurance Type |
| CLAIM_STATUS | 理赔状态 | Claim Status |
| WORKFLOW_STATUS | 流程状态 | Workflow Status |
| TASK_STATUS | 任务状态 | Task Status |
| APPROVAL_RESULT | 审批结果 | Approval Result |
| PAYMENT_STATUS | 支付状态 | Payment Status |
| CONTRACT_STATUS | 合同状态 | Contract Status |
| POLICY_STATUS | 保单状态 | Policy Status |
| OS_TYPE | 操作系统 | OS Type |
| ASSET_SOURCE | 资产来源 | Asset Source |
| USAGE_STATUS | 使用状态 | Usage Status |

### 4. DictionaryItem Translations

#### Asset Status (13 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| IDLE | 空闲 | Idle |
| IN_USE | 使用中 | In Use |
| MAINTENANCE | 维护中 | Maintenance |
| REPAIR | 维修中 | Under Repair |
| SCRAPPED | 已报废 | Scrapped |
| LOST | 已丢失 | Lost |
| RETIRE | 已退役 | Retired |
| BORROWED | 借用中 | Borrowed |
| PICKUP_PENDING | 待领用 | Pickup Pending |
| TRANSFER_PENDING | 待调拨 | Transfer Pending |
| RETURN_PENDING | 待退库 | Return Pending |
| ON_LOAN | 借出 | On Loan |
| DISPOSAL | 报废 | Disposal |

#### Inventory Status (4 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| PENDING | 待开始 | Pending |
| IN_PROGRESS | 进行中 | In Progress |
| COMPLETED | 已完成 | Completed |
| CANCELLED | 已取消 | Cancelled |

#### Inventory Type (5 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| FULL | 全盘 | Full Inventory |
| RANDOM | 抽盘 | Random |
| DYNAMIC | 动盘 | Dynamic |
| PARTIAL | 部分盘点 | Partial |
| DEPARTMENT | 部门盘点 | Department |

#### Maintenance Type (7 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| PREVENTIVE | 预防性维护 | Preventive |
| CORRECTIVE | 纠正性维护 | Corrective |
| UPGRADE | 升级 | Upgrade |
| REPLACEMENT | 更换 | Replacement |
| INSPECTION | 巡检 | Inspection |
| CLEANING | 清洁 | Cleaning |
| OTHER | 其他 | Other |

#### Workflow Status (4 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| DRAFT | 草稿 | Draft |
| ACTIVE | 生效中 | Active |
| INACTIVE | 已停用 | Inactive |
| ARCHIVED | 已归档 | Archived |

#### Task Status (5 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| PENDING | 待处理 | Pending |
| IN_PROGRESS | 处理中 | In Progress |
| COMPLETED | 已完成 | Completed |
| CANCELLED | 已取消 | Cancelled |
| RETURNED | 已退回 | Returned |

#### Approval Result (4 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| APPROVED | 同意 | Approved |
| REJECTED | 拒绝 | Rejected |
| RETURNED | 退回 | Returned |
| CANCELLED | 撤销 | Cancelled |

#### Voucher Status (5 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| DRAFT | 草稿 | Draft |
| PENDING | 待审批 | Pending |
| APPROVED | 已审批 | Approved |
| POSTED | 已入账 | Posted |
| REJECTED | 已驳回 | Rejected |

#### Software Type (7 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| OS | 操作系统 | Operating System |
| OFFICE | 办公软件 | Office Software |
| PROFESSIONAL | 专业软件 | Professional |
| DEVELOPMENT | 开发工具 | Development Tool |
| SECURITY | 安全软件 | Security Software |
| DATABASE | 数据库 | Database |
| OTHER | 其他 | Other |

#### License Status (4 items)
| Code | zh-CN | en-US |
|------|-------|-------|
| ACTIVE | 生效中 | Active |
| EXPIRED | 已过期 | Expired |
| SUSPENDED | 暂停 | Suspended |
| REVOKED | 撤销 | Revoked |

## Docker Command to Run

```bash
# Initialize all translations
docker-compose exec backend python manage.py init_all_translations
```

## Features

1. **Idempotent**: Can be run multiple times without creating duplicates
2. **Smart Skip**: Skips translations that already exist
3. **Batch Create**: Uses bulk_create for efficient database operations
4. **Graceful Handling**: Handles missing objects gracefully with warnings
5. **Comprehensive Coverage**: Covers all major business objects and dictionaries

## Translation Storage

Translations are stored in the `Translation` model with the following structure:
- **Static translations**: namespace='button', key='save', language_code='en-US', text='Save'
- **Object translations**: content_type=BusinessObject, object_id=uuid, field_name='name', language_code='en-US', text='Fixed Asset'

## Notes

- All translations are marked as `is_system=True` to prevent accidental deletion
- The command uses GenericForeignKey to support translations for any model
- Existing `name_en` fields on models are preserved for backward compatibility
