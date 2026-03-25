/**
 * useImportProcessor — Handles the full import pipeline for dynamic objects.
 *
 * Features:
 *   1. Reference field resolution: "财务部" → department_id
 *   2. Dictionary reverse mapping: "启用" → "active"
 *   3. Import strategies: Create Only / Upsert / Skip Duplicates
 *   4. Progress tracking
 *
 * Usage:
 *   const { processImport, importing, progress } = useImportProcessor({
 *     objectCode: () => objectCode.value,
 *     fields: orderedVisibleFieldsSource
 *   })
 */

import { ref, computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createObjectClient } from '@/api/dynamic'
import { filterSystemFields } from '@/utils/transform'
import { normalizeFieldType, resolveFieldType } from '@/utils/fieldType'
import {
  isReferenceLikeFieldType,
  resolveReferenceObjectCode,
} from '@/platform/reference/referenceFieldMeta'

// ── Types ──────────────────────────────────────────────────────────────────────

export type ImportStrategy = 'create' | 'upsert' | 'skip_duplicates'

export interface ImportProcessorOptions {
  objectCode: () => string
  fields: Ref<any[]>
}

export interface ImportProgress {
  total: number
  current: number
  created: number
  updated: number
  skipped: number
  failed: number
  errors: Array<{ row: number; message: string }>
}

interface FieldMeta {
  code: string
  fieldType: string
  referenceObjectCode: string
  options: Map<string, any> | null // label → value reverse map
}

// ── Helpers ────────────────────────────────────────────────────────────────────

/** Build a reverse lookup map: option.label → option.value */
function buildReverseLabelMap(field: any): Map<string, any> | null {
  const options = field?.options || field?.choices || []
  if (!options.length) return null
  const map = new Map<string, any>()
  for (const opt of options) {
    if (opt.label && opt.value !== undefined) {
      map.set(String(opt.label).trim(), opt.value)
      // Also map lowercase for fuzzy matching
      map.set(String(opt.label).trim().toLowerCase(), opt.value)
    }
  }
  return map.size > 0 ? map : null
}

/** Try to resolve a reference display name to its ID */
async function resolveReferenceId(
  objectCode: string,
  displayValue: string,
  cache: Map<string, string | null>
): Promise<string | null> {
  if (!objectCode || !displayValue) return null

  const cacheKey = `${objectCode}::${displayValue}`
  if (cache.has(cacheKey)) return cache.get(cacheKey) || null

  try {
    const client = createObjectClient(objectCode)
    const response = await client.list({ search: displayValue, page_size: 5 })
    const results = (response as any)?.data?.results ?? (response as any)?.results ?? []

    // Find exact match by common display fields
    const exactMatch = results.find((r: any) =>
      [r.name, r.label, r.title, r.display_name, r.code, r.username, r.full_name]
        .filter(Boolean)
        .some((v: string) => String(v).trim().toLowerCase() === displayValue.toLowerCase())
    )

    const id = exactMatch?.id ?? results[0]?.id ?? null
    cache.set(cacheKey, id ? String(id) : null)
    return id ? String(id) : null
  } catch {
    cache.set(cacheKey, null)
    return null
  }
}

// ── Composable ─────────────────────────────────────────────────────────────────

export function useImportProcessor(options: ImportProcessorOptions) {
  const { t } = useI18n()

  const importing = ref(false)
  const progress = ref<ImportProgress>({
    total: 0, current: 0, created: 0, updated: 0, skipped: 0, failed: 0, errors: []
  })

  /** Extract field metadata for import processing */
  const fieldMetas = computed<FieldMeta[]>(() => {
    return filterSystemFields(options.fields.value || []).map((f: any) => {
      const code = String(f?.code || f?.fieldCode || f?.field_code || '').trim()
      const fieldType = normalizeFieldType(resolveFieldType(f))
      const refCode = resolveReferenceObjectCode(f)
      return {
        code,
        fieldType,
        referenceObjectCode: refCode,
        options: buildReverseLabelMap(f)
      }
    }).filter(m => m.code)
  })

  /** Get reference-like fields that need name→ID resolution */
  const referenceFields = computed(() =>
    fieldMetas.value.filter(f =>
      isReferenceLikeFieldType(f.fieldType) || !!f.referenceObjectCode
    )
  )

  /** Get select/dictionary fields that need label→code conversion */
  const selectFields = computed(() =>
    fieldMetas.value.filter(f =>
      ['select', 'dictionary', 'tag', 'radio', 'multi_select'].includes(f.fieldType) &&
      f.options != null
    )
  )

  /**
   * Transform a single import row:
   * - Resolve reference display names → IDs
   * - Reverse-map select labels → codes
   */
  async function transformRow(
    row: Record<string, any>,
    refCache: Map<string, string | null>
  ): Promise<Record<string, any>> {
    const transformed = { ...row }

    // Resolve reference fields (name → ID)
    for (const field of referenceFields.value) {
      const rawValue = transformed[field.code]
      if (!rawValue || typeof rawValue !== 'string') continue

      // Skip if already looks like a UUID or numeric ID
      const trimmed = rawValue.trim()
      if (/^[0-9a-f]{8}-/.test(trimmed) || /^\d+$/.test(trimmed)) continue

      const resolvedId = await resolveReferenceId(
        field.referenceObjectCode,
        trimmed,
        refCache
      )
      if (resolvedId) {
        transformed[field.code] = resolvedId
      }
      // If not resolved, leave original value (backend will validate)
    }

    // Reverse-map select/dictionary labels → codes
    for (const field of selectFields.value) {
      const rawValue = transformed[field.code]
      if (rawValue === undefined || rawValue === null || rawValue === '') continue
      if (!field.options) continue

      const trimmed = String(rawValue).trim()
      const resolved = field.options.get(trimmed) ?? field.options.get(trimmed.toLowerCase())
      if (resolved !== undefined) {
        transformed[field.code] = resolved
      }
    }

    return transformed
  }

  /**
   * Find existing record for upsert by match field
   */
  async function findExistingRecord(
    apiClient: ReturnType<typeof createObjectClient>,
    row: Record<string, any>,
    matchField: string
  ): Promise<string | null> {
    const matchValue = row[matchField]
    if (!matchValue) return null

    try {
      const response = await apiClient.list({
        [matchField]: matchValue,
        page_size: 1
      })
      const results = (response as any)?.data?.results ?? (response as any)?.results ?? []
      return results[0]?.id ?? null
    } catch {
      return null
    }
  }

  /**
   * Process the full import pipeline
   */
  async function processImport(
    data: Record<string, any>[],
    strategy: ImportStrategy = 'create',
    matchField?: string
  ): Promise<ImportProgress> {
    const code = options.objectCode()
    if (!code) throw new Error('Object code is required')

    importing.value = true
    const refCache = new Map<string, string | null>()
    const apiClient = createObjectClient(code)

    progress.value = {
      total: data.length,
      current: 0,
      created: 0,
      updated: 0,
      skipped: 0,
      failed: 0,
      errors: []
    }

    try {
      for (let i = 0; i < data.length; i++) {
        progress.value.current = i + 1

        try {
          // Transform: resolve references + select labels
          const transformed = await transformRow(data[i], refCache)

          if (strategy === 'create') {
            await apiClient.create(transformed)
            progress.value.created++
          } else if (strategy === 'upsert' && matchField) {
            const existingId = await findExistingRecord(apiClient, transformed, matchField)
            if (existingId) {
              await apiClient.partialUpdate(existingId, transformed)
              progress.value.updated++
            } else {
              await apiClient.create(transformed)
              progress.value.created++
            }
          } else if (strategy === 'skip_duplicates' && matchField) {
            const existingId = await findExistingRecord(apiClient, transformed, matchField)
            if (existingId) {
              progress.value.skipped++
            } else {
              await apiClient.create(transformed)
              progress.value.created++
            }
          } else {
            // Fallback to create
            await apiClient.create(transformed)
            progress.value.created++
          }
        } catch (e: any) {
          progress.value.failed++
          progress.value.errors.push({
            row: i + 1,
            message: e?.response?.data?.message || e?.message || t('common.messages.operationFailed')
          })
        }
      }
    } finally {
      importing.value = false
    }

    return progress.value
  }

  return {
    importing,
    progress,
    processImport,
    referenceFields,
    selectFields,
    fieldMetas
  }
}
