import { describe, expect, it } from 'vitest'
import { normalizeBusinessObjects, normalizeMenuGroups } from '../menu'

// =============================================================================
// normalizeBusinessObjects
// =============================================================================
describe('normalizeBusinessObjects', () => {
    it('extracts objects from results array', () => {
        const result = normalizeBusinessObjects({
            results: [
                { code: 'Asset', name: 'Asset', id: '1' },
                { code: 'Location', name: 'Location', id: '2' },
            ],
        })
        expect(result).toHaveLength(2)
        expect(result[0].code).toBe('Asset')
        expect(result[1].code).toBe('Location')
    })

    it('extracts objects from hardcoded and custom arrays', () => {
        const result = normalizeBusinessObjects({
            hardcoded: [{ code: 'Asset', name: 'Asset' }],
            custom: [{ code: 'MyObj', name: 'My Object' }],
        })
        expect(result).toHaveLength(2)
        expect(result.map((o) => o.code)).toEqual(['Asset', 'MyObj'])
    })

    it('deduplicates by code', () => {
        const result = normalizeBusinessObjects({
            results: [
                { code: 'Asset', name: 'Asset-1' },
                { code: 'Asset', name: 'Asset-2' },
            ],
        })
        expect(result).toHaveLength(1)
        expect(result[0].name).toBe('Asset-1')
    })

    it('skips entries with empty code', () => {
        const result = normalizeBusinessObjects({
            results: [
                { code: '', name: 'Empty' },
                { code: 'Valid', name: 'Valid' },
            ],
        })
        expect(result).toHaveLength(1)
        expect(result[0].code).toBe('Valid')
    })

    it('normalizes camelCase / snake_case field variants', () => {
        const result = normalizeBusinessObjects({
            results: [
                {
                    code: 'A',
                    name_en: 'English Name',
                    is_hardcoded: true,
                    menu_category: 'core',
                    is_menu_hidden: true,
                },
            ],
        })
        expect(result[0].nameEn).toBe('English Name')
        expect(result[0].isHardcoded).toBe(true)
        expect(result[0].menuCategory).toBe('core')
        expect(result[0].isMenuHidden).toBe(true)
    })

    it('returns empty array for null/undefined input', () => {
        expect(normalizeBusinessObjects({})).toEqual([])
        expect(normalizeBusinessObjects({ results: null } as any)).toEqual([])
    })
})

// =============================================================================
// normalizeMenuGroups
// =============================================================================
describe('normalizeMenuGroups', () => {
    it('normalizes groups with items', () => {
        const result = normalizeMenuGroups({
            groups: [
                {
                    code: 'core',
                    name: 'Core',
                    icon: 'Folder',
                    order: 1,
                    translationKey: 'menu.categories.core',
                    items: [
                        { code: 'Asset', name: 'Asset', url: '/objects/Asset', icon: 'Document', order: 1 },
                    ],
                },
            ],
        })
        expect(result).toHaveLength(1)
        expect(result[0].code).toBe('core')
        expect(result[0].items).toHaveLength(1)
        expect(result[0].items[0].code).toBe('Asset')
        expect(result[0].items[0].url).toBe('/objects/Asset')
    })

    it('filters out empty groups', () => {
        const result = normalizeMenuGroups({
            groups: [
                { code: 'empty', name: 'Empty', items: [] },
                { code: 'filled', name: 'Filled', items: [{ code: 'X', url: '/x' }] },
            ],
        })
        expect(result).toHaveLength(1)
        expect(result[0].code).toBe('filled')
    })

    it('assigns default values for missing fields', () => {
        const result = normalizeMenuGroups({
            groups: [
                {
                    items: [{ code: 'Obj' }],
                },
            ],
        })
        expect(result).toHaveLength(1)
        expect(result[0].icon).toBe('Menu')
        expect(result[0].items[0].url).toBe('')
    })

    it('returns empty array when groups is not present', () => {
        expect(normalizeMenuGroups({})).toEqual([])
        expect(normalizeMenuGroups({ groups: null } as any)).toEqual([])
    })
})
