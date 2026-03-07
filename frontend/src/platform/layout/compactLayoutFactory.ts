/**
 * Compact Layout Factory
 *
 * Derives a Compact layout from a Detail layout by:
 * 1. Flattening all sections (tabs, collapses) into a single section
 * 2. Prioritizing required fields, then sort_order ascending
 * 3. Limiting to a configurable max number of fields
 * 4. Stripping sidebar sections and related-list placeholders
 */

type AnyRecord = Record<string, any>

interface CompactDeriveOptions {
    /** Maximum fields to include in the compact layout. Default: 10. */
    maxFields?: number
    /** Columns for the compact section. Default: 2. */
    columns?: number
}

/**
 * Extract all field items from a section, including nested tabs/collapses.
 */
function extractFieldsFromSection(section: AnyRecord): AnyRecord[] {
    const fields: AnyRecord[] = []
    const sectionType = String(section?.type || 'section')

    if (sectionType === 'tab' && Array.isArray(section?.tabs)) {
        for (const tab of section.tabs) {
            if (Array.isArray(tab?.fields)) {
                fields.push(...tab.fields)
            }
        }
    } else if (sectionType === 'collapse' && Array.isArray(section?.items)) {
        for (const item of section.items) {
            if (Array.isArray(item?.fields)) {
                fields.push(...item.fields)
            }
        }
    } else if (Array.isArray(section?.fields)) {
        fields.push(...section.fields)
    }

    return fields
}

/**
 * Get the field code from a layout field item (handles multiple naming conventions).
 */
function toFieldCode(field: AnyRecord): string {
    return String(field?.fieldCode || field?.field_code || field?.code || '').trim()
}

/**
 * Sort fields with required ones first, then by their original order.
 * Uses metadata to determine required status if available.
 */
function prioritizeFields(fields: AnyRecord[], metaFields: AnyRecord[]): AnyRecord[] {
    const metaMap = new Map<string, AnyRecord>()
    for (const meta of metaFields) {
        const code = String(meta?.code || meta?.fieldCode || meta?.field_code || '').trim()
        if (code) metaMap.set(code, meta)
    }

    const scored = fields.map((field, index) => {
        const code = toFieldCode(field)
        const meta = metaMap.get(code)
        const isRequired = field?.required === true ||
            meta?.isRequired === true || meta?.is_required === true
        return { field, index, isRequired }
    })

    scored.sort((a, b) => {
        // Required fields first
        if (a.isRequired && !b.isRequired) return -1
        if (!a.isRequired && b.isRequired) return 1
        // Then by original order
        return a.index - b.index
    })

    return scored.map(s => s.field)
}

/**
 * Derive a Compact layout from a Detail layout configuration.
 *
 * @param detailConfig - The full Detail layout config (with sections)
 * @param metaFields  - Field metadata array for determining required status
 * @param options     - Compact derivation options
 * @returns A simplified LayoutConfig suitable for compact/dialog rendering
 */
export function deriveCompactLayout(
    detailConfig: AnyRecord,
    metaFields: AnyRecord[] = [],
    options: CompactDeriveOptions = {}
): AnyRecord {
    const maxFields = options.maxFields ?? 10
    const columns = options.columns ?? 2

    const sections: AnyRecord[] = Array.isArray(detailConfig?.sections)
        ? detailConfig.sections
        : []

    // 1. Collect all fields, excluding sidebar sections
    const allFields: AnyRecord[] = []
    for (const section of sections) {
        const position = String(section?.position || 'main')
        if (position === 'sidebar') continue
        allFields.push(...extractFieldsFromSection(section))
    }

    // 2. Deduplicate by field code
    const seen = new Set<string>()
    const uniqueFields = allFields.filter(field => {
        const code = toFieldCode(field)
        if (!code || seen.has(code)) return false
        seen.add(code)
        return true
    })

    // 3. Prioritize required fields, then limit
    const prioritized = prioritizeFields(uniqueFields, metaFields)
    const limited = prioritized.slice(0, maxFields)

    // 4. Build a single flat section
    return {
        layoutType: 'Compact',
        sections: [
            {
                id: 'compact_main',
                type: 'section',
                title: '',
                columns,
                fields: limited,
            }
        ]
    }
}

/**
 * Check if a layout config is a Compact layout.
 */
export function isCompactLayout(config: AnyRecord | null | undefined): boolean {
    if (!config) return false
    return config.layoutType === 'Compact'
}
