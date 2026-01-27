/**
 * Software License Management Types
 */

export interface Software {
  id: string
  organization: any
  code: string
  name: string
  version: string
  vendor: string
  softwareType: 'os' | 'office' | 'professional' | 'development' | 'security' | 'database' | 'other'
  licenseType: string
  category?: any
  isActive: boolean
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface SoftwareLicense {
  id: string
  organization: any
  licenseNo: string
  software: string
  softwareName?: string
  softwareVersion?: string
  licenseKey?: string
  totalUnits: number
  usedUnits: number
  availableUnits?: number
  utilizationRate?: number
  purchaseDate: string
  expiryDate?: string
  isExpired?: boolean
  purchasePrice?: number
  annualCost?: number
  status: 'active' | 'expired' | 'suspended' | 'revoked'
  licenseType: string
  agreementNo?: string
  vendor?: any
  notes?: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface LicenseAllocation {
  id: string
  organization: any
  license: string
  softwareName?: string
  licenseNo?: string
  asset: string
  assetName?: string
  assetCode?: string
  allocatedDate: string
  allocatedBy?: string
  allocatedByName?: string
  allocationKey?: string
  deallocatedDate?: string
  deallocatedBy?: string
  deallocatedByName?: string
  isActive: boolean
  notes?: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface ComplianceReport {
  totalLicenses: number
  expiringLicenses: number
  overUtilized: Array<{
    id: string
    licenseNo: string
    software: string
    utilization: number
  }>
}
