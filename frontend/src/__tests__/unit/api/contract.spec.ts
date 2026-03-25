import { describe, expect, it } from 'vitest'
import {
  normalizeQueryParams,
  toActionResult,
  toCamelDeep,
  toData,
  toPaginated,
} from '@/api/contract'

describe('api contract helpers', () => {
  it('normalizeQueryParams should convert camelCase to snake_case', () => {
    const normalized = normalizeQueryParams({
      page: 1,
      pageSize: 20,
      voucherNo: 'VCH-001',
      status: '',
      healthStatus: 'healthy',
    })

    expect(normalized).toEqual({
      page: 1,
      page_size: 20,
      voucher_no: 'VCH-001',
      health_status: 'healthy',
    })
  })

  it('normalizeQueryParams should respect aliases and preserve keys', () => {
    const normalized = normalizeQueryParams(
      {
        page: 2,
        pageSize: 50,
        currentOrgId: 'org-1',
      },
      {
        aliases: { currentOrgId: 'organization_id' },
        preserveKeys: ['page'],
      }
    )

    expect(normalized).toEqual({
      page: 2,
      page_size: 50,
      organization_id: 'org-1',
    })
  })

  it('toData should unwrap API envelope', () => {
    const data = toData<{ id: string }>({
      success: true,
      data: { id: '123' },
    })

    expect(data).toEqual({ id: '123' })
  })

  it('toActionResult should normalize envelope', () => {
    const result = toActionResult({
      success: true,
      message: 'ok',
      data: { id: 'x1' },
    })

    expect(result.success).toBe(true)
    expect(result.message).toBe('ok')
    expect(result.data).toEqual({ id: 'x1' })
  })

  it('toPaginated should normalize envelope and list payloads', () => {
    const pageA = toPaginated<{ id: number }>({
      success: true,
      data: {
        count: 2,
        next: null,
        previous: null,
        results: [{ id: 1 }, { id: 2 }],
      },
    })

    const pageB = toPaginated<{ id: number }>([{ id: 10 }])

    expect(pageA.count).toBe(2)
    expect(pageA.results).toHaveLength(2)
    expect(pageB.count).toBe(1)
    expect(pageB.results[0].id).toBe(10)
  })

  it('toCamelDeep should convert nested keys to camelCase', () => {
    const result = toCamelDeep({
      system_type: 'm18',
      connection_config: {
        api_url: 'http://example.com',
      },
      enabled_modules: [{ module_name: 'finance' }],
    })

    expect(result).toEqual({
      systemType: 'm18',
      connectionConfig: {
        apiUrl: 'http://example.com',
      },
      enabledModules: [{ moduleName: 'finance' }],
    })
  })
})
