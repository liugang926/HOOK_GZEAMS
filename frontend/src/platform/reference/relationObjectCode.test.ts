import { describe, expect, it } from 'vitest'
import {
  deriveObjectCodeFromRelationCode,
  extractObjectCodeFromModelPath,
  resolveRelationTargetObjectCode
} from './relationObjectCode'

describe('relationObjectCode', () => {
  it('derives object code from snake relation code', () => {
    expect(deriveObjectCodeFromRelationCode('maintenance_records')).toBe('Maintenance')
    expect(deriveObjectCodeFromRelationCode('asset_loan_record')).toBe('AssetLoan')
    expect(deriveObjectCodeFromRelationCode('pickup_orders')).toBe('Pickup')
  })

  it('derives object code from camel relation code', () => {
    expect(deriveObjectCodeFromRelationCode('maintenanceRecords')).toBe('Maintenance')
    expect(deriveObjectCodeFromRelationCode('AssetLoanItems')).toBe('AssetLoan')
    expect(deriveObjectCodeFromRelationCode('TransferOrders')).toBe('Transfer')
  })

  it('extracts object code from model path', () => {
    expect(extractObjectCodeFromModelPath('apps.lifecycle.models.Maintenance')).toBe('Maintenance')
  })

  it('prefers explicit target and then model path', () => {
    expect(resolveRelationTargetObjectCode({
      explicitTarget: 'AssetLoan',
      reverseRelationModel: 'apps.lifecycle.models.Maintenance',
      relationCode: 'maintenance_records'
    })).toBe('AssetLoan')

    expect(resolveRelationTargetObjectCode({
      reverseRelationModel: 'apps.lifecycle.models.Maintenance',
      relationCode: 'loan_records'
    })).toBe('Maintenance')
  })
})
