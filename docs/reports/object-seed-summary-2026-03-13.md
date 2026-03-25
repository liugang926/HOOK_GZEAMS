# Object Seed Summary

Date: 2026-03-13

Primary organization used for frontend verification:
- Code: `ORG001`
- Name: `Demo Organization 001`

Seeding script:
- [backend/seed_minimum_demo_data.py](C:/Users/Aberl.liu/Desktop/All%20My%20Project/NEWEAMS/backend/seed_minimum_demo_data.py)

## Result

All 61 hardcoded business objects now have at least 20 records visible inside the primary organization used by the frontend.

## Frontend/API Verification

Authenticated with:
- Username: `admin`
- Organization: `ORG001`

Verified object router list endpoints:
- `GET /api/system/objects/Asset/` -> `count = 20`
- `GET /api/system/objects/Consumable/` -> `count = 20`
- `GET /api/system/objects/InventoryTask/` -> `count = 20`
- `GET /api/system/objects/InsurancePolicy/` -> `count = 20`

Representative first records returned:
- Asset: `ASSET0039`
- Consumable: `CONSUM0001`
- InventoryTask: `INVENT0039`
- InsurancePolicy: `INSURA-20260313-0039`

## Counts

`Primary Org Count` means records visible under `ORG001`.

| Code | Name | Primary Org Count | Total Count |
| --- | --- | ---: | ---: |
| Asset | 资产 | 20 | 39 |
| AssetCategory | 资产分类 | 20 | 39 |
| AssetLoan | 资产借用 | 20 | 39 |
| AssetPickup | 资产领用 | 20 | 39 |
| AssetReceipt | 资产入库 | 20 | 39 |
| AssetReturn | 资产归还 | 20 | 39 |
| AssetStatusLog | 资产状态日志 | 20 | 39 |
| AssetTransfer | 资产调拨 | 20 | 39 |
| ClaimRecord | 理赔记录 | 20 | 39 |
| ConfigurationChange | 配置变更 | 20 | 39 |
| Consumable | 耗材 | 20 | 39 |
| ConsumableCategory | 耗材分类 | 20 | 39 |
| ConsumableIssue | 耗材领用 | 20 | 39 |
| ConsumablePurchase | 耗材采购 | 20 | 39 |
| ConsumableStock | 耗材库存 | 20 | 39 |
| Department | 部门 | 20 | 39 |
| DepreciationConfig | 折旧配置 | 20 | 39 |
| DepreciationRecord | 折旧记录 | 20 | 39 |
| DepreciationRun | 折旧运行 | 20 | 39 |
| DisposalRequest | 报废申请 | 20 | 39 |
| FinanceVoucher | 财务凭证 | 20 | 39 |
| ITAsset | IT资产 | 20 | 39 |
| ITLicenseAllocation | IT许可证分配 | 20 | 39 |
| ITMaintenanceRecord | IT维护记录 | 20 | 39 |
| ITSoftware | IT软件目录 | 20 | 39 |
| ITSoftwareLicense | IT软件许可 | 20 | 39 |
| InsuranceCompany | 保险公司 | 20 | 39 |
| InsurancePolicy | 保险保单 | 20 | 39 |
| InsuredAsset | 投保资产 | 20 | 39 |
| InventoryItem | 盘点明细 | 20 | 39 |
| InventorySnapshot | 资产快照 | 20 | 39 |
| InventoryTask | 盘点任务 | 20 | 39 |
| LeaseExtension | 租赁续租 | 20 | 39 |
| LeaseItem | 租赁明细 | 20 | 39 |
| LeaseReturn | 租赁归还 | 20 | 39 |
| LeasingContract | 租赁合同 | 20 | 39 |
| LicenseAllocation | 许可证分配 | 20 | 39 |
| LoanItem | 鍊熺敤鏄庣粏 | 20 | 39 |
| Location | 位置 | 20 | 39 |
| Maintenance | 维修记录 | 20 | 39 |
| MaintenancePlan | 维修计划 | 20 | 39 |
| MaintenanceTask | 维修任务 | 20 | 39 |
| Organization | 组织 | 20 | 20 |
| PickupItem | 棰嗙敤鏄庣粏 | 20 | 39 |
| PolicyRenewal | 保单续保 | 20 | 39 |
| PremiumPayment | 保费支付 | 20 | 39 |
| PurchaseRequest | 采购申请 | 20 | 39 |
| RentPayment | 租金支付 | 20 | 39 |
| ReturnItem | 褰掕繕鏄庣粏 | 20 | 39 |
| Software | 软件目录 | 20 | 39 |
| SoftwareLicense | 软件许可 | 20 | 39 |
| Supplier | 供应商 | 20 | 39 |
| TransferItem | 璋冩嫧鏄庣粏 | 20 | 39 |
| User | 用户 | 20 | 40 |
| VoucherTemplate | 凭证模板 | 20 | 39 |
| WorkflowApproval | 工作流审批记录 | 20 | 39 |
| WorkflowDefinition | 工作流定义 | 20 | 39 |
| WorkflowInstance | 工作流实例 | 20 | 39 |
| WorkflowOperationLog | 工作流操作日志 | 20 | 39 |
| WorkflowTask | 工作流任务 | 20 | 39 |
| WorkflowTemplate | 工作流模板 | 20 | 39 |

