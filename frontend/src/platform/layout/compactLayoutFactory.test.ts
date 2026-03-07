import { describe, expect, it } from 'vitest'
import { deriveCompactLayout, isCompactLayout } from './compactLayoutFactory'

function makeField(code: string, required = false) {
    return { fieldCode: code, label: code, span: 12, required }
}

describe('deriveCompactLayout', () => {
    it('flattens tabs into a single section', () => {
        const detailConfig = {
            sections: [
                {
                    id: 'tab1',
                    type: 'tab',
                    tabs: [
                        { id: 't1', title: 'Tab A', fields: [makeField('a'), makeField('b')] },
                        { id: 't2', title: 'Tab B', fields: [makeField('c')] },
                    ],
                },
            ],
        }

        const compact = deriveCompactLayout(detailConfig)
        expect(compact.layoutType).toBe('Compact')
        expect(compact.sections).toHaveLength(1)

        const fields = compact.sections[0].fields
        expect(fields.map((f: any) => f.fieldCode)).toEqual(['a', 'b', 'c'])
    })

    it('flattens collapse items into a single section', () => {
        const detailConfig = {
            sections: [
                {
                    id: 'collapse1',
                    type: 'collapse',
                    items: [
                        { id: 'c1', title: 'Panel', fields: [makeField('x'), makeField('y')] },
                    ],
                },
            ],
        }

        const compact = deriveCompactLayout(detailConfig)
        expect(compact.sections[0].fields).toHaveLength(2)
    })

    it('prioritizes required fields', () => {
        const detailConfig = {
            sections: [
                {
                    id: 's1',
                    type: 'section',
                    fields: [
                        makeField('optional1'),
                        makeField('required1', true),
                        makeField('optional2'),
                        makeField('required2', true),
                    ],
                },
            ],
        }

        const meta = [
            { code: 'required1', isRequired: true },
            { code: 'required2', isRequired: true },
        ]

        const compact = deriveCompactLayout(detailConfig, meta, { maxFields: 3 })
        const codes = compact.sections[0].fields.map((f: any) => f.fieldCode)
        // Required fields come first
        expect(codes[0]).toBe('required1')
        expect(codes[1]).toBe('required2')
        expect(codes).toHaveLength(3)
    })

    it('limits the number of fields', () => {
        const detailConfig = {
            sections: [
                {
                    id: 's1',
                    type: 'section',
                    fields: Array.from({ length: 20 }, (_, i) => makeField(`f${i}`)),
                },
            ],
        }

        const compact = deriveCompactLayout(detailConfig, [], { maxFields: 5 })
        expect(compact.sections[0].fields).toHaveLength(5)
    })

    it('excludes sidebar sections', () => {
        const detailConfig = {
            sections: [
                {
                    id: 'main',
                    type: 'section',
                    position: 'main',
                    fields: [makeField('a')],
                },
                {
                    id: 'side',
                    type: 'section',
                    position: 'sidebar',
                    fields: [makeField('b')],
                },
            ],
        }

        const compact = deriveCompactLayout(detailConfig)
        const codes = compact.sections[0].fields.map((f: any) => f.fieldCode)
        expect(codes).toContain('a')
        expect(codes).not.toContain('b')
    })

    it('deduplicates fields by code', () => {
        const detailConfig = {
            sections: [
                { id: 's1', type: 'section', fields: [makeField('a')] },
                { id: 's2', type: 'section', fields: [makeField('a'), makeField('b')] },
            ],
        }

        const compact = deriveCompactLayout(detailConfig)
        const codes = compact.sections[0].fields.map((f: any) => f.fieldCode)
        expect(codes).toEqual(['a', 'b'])
    })
})

describe('isCompactLayout', () => {
    it('returns true for Compact layout type', () => {
        expect(isCompactLayout({ layoutType: 'Compact' })).toBe(true)
    })

    it('returns false for Detail or missing', () => {
        expect(isCompactLayout({ layoutType: 'Detail' })).toBe(false)
        expect(isCompactLayout(null)).toBe(false)
        expect(isCompactLayout(undefined)).toBe(false)
        expect(isCompactLayout({})).toBe(false)
    })
})
