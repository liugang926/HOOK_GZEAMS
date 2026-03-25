type TranslateFn = (key: string) => string
type TranslateExistsFn = (key: string) => boolean

const OBJECT_CODE_ROUTE_KEY_MAP: Record<string, string> = {
  Asset: 'assetList',
  AssetCategory: 'assetCategory',
  Location: 'location',
  Supplier: 'supplier',
  AssetStatusLog: 'assetStatusLog',
  AssetPickup: 'assetPickup',
  AssetTransfer: 'assetTransfer',
  AssetReturn: 'assetReturn',
  AssetLoan: 'assetLoan',
  Consumable: 'consumable',
  ConsumableCategory: 'consumableCategory',
  ConsumableStock: 'consumableStock',
  ConsumablePurchase: 'consumablePurchase',
  ConsumableIssue: 'consumableIssue',
  PurchaseRequest: 'purchaseRequest',
  AssetReceipt: 'assetReceipt',
  Maintenance: 'maintenance',
  MaintenanceTask: 'maintenanceTask',
  MaintenancePlan: 'maintenancePlan',
  DisposalRequest: 'disposalRequest',
  InventoryTask: 'inventoryTask',
  InventorySnapshot: 'inventorySnapshot',
  InventoryItem: 'inventoryItem',
  Organization: 'organization',
  Department: 'department',
  User: 'users',
  WorkflowDefinition: 'workflowDefinitions',
  WorkflowInstance: 'workflowInstances',
  FinanceVoucher: 'financeVoucher',
  VoucherTemplate: 'voucherTemplate',
  DepreciationConfig: 'depreciationConfig',
  DepreciationRecord: 'depreciationRecord',
  DepreciationRun: 'depreciationRun',
  ITAsset: 'itAsset',
  ITMaintenanceRecord: 'itMaintenanceRecord',
  ConfigurationChange: 'configurationChange',
  ITSoftware: 'itSoftware',
  ITSoftwareLicense: 'itSoftwareLicense',
  ITLicenseAllocation: 'itLicenseAllocation',
  Software: 'software',
  SoftwareLicense: 'softwareLicense',
  LicenseAllocation: 'licenseAllocation',
  LeasingContract: 'leasingContract',
  LeaseItem: 'leaseItem',
  LeaseExtension: 'leaseExtension',
  LeaseReturn: 'leaseReturn',
  RentPayment: 'rentPayment',
  InsuranceCompany: 'insuranceCompany',
  InsurancePolicy: 'insurancePolicy',
  InsuredAsset: 'insuredAsset',
  PremiumPayment: 'premiumPayment',
  ClaimRecord: 'claimRecord',
  PolicyRenewal: 'policyRenewal',
  AssetProject: 'assetProject',
  ProjectAsset: 'projectAsset',
  ProjectMember: 'projectMember'
}

const getRouteLabelKey = (objectCode: string): string => {
  const code = String(objectCode || '').trim()
  if (!code) return ''
  const mapped = OBJECT_CODE_ROUTE_KEY_MAP[code] || code
  return `menu.routes.${mapped}`
}

export const translateObjectCodeLabel = (
  objectCode: string,
  t: TranslateFn,
  te: TranslateExistsFn
): string | null => {
  const labelKey = getRouteLabelKey(objectCode)
  if (labelKey && te(labelKey)) return t(labelKey)

  const rawCodeKey = `menu.routes.${String(objectCode || '').trim()}`
  if (rawCodeKey && te(rawCodeKey)) return t(rawCodeKey)

  return null
}

export const resolveObjectDisplayName = (
  objectCode: string,
  fallbackName: string,
  t: TranslateFn,
  te: TranslateExistsFn
): string => {
  const translated = translateObjectCodeLabel(objectCode, t, te)
  if (translated) return translated

  const fallback = String(fallbackName || '').trim()
  if (fallback) return fallback

  return String(objectCode || '').trim()
}
