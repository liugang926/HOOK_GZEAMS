import { defineComponent, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { useRelationGroupExpansion, type RelationGroupExpansionItem } from '@/composables/useRelationGroupExpansion'

const makeKey = (objectCode: string, scopeId: string) => `${objectCode}:${scopeId}`

const createMemoryPreferenceStore = () => {
  const map = new Map<string, string[]>()
  return {
    load: (objectCode: string, recordId: string): string[] | null => {
      const value = map.get(makeKey(objectCode, recordId))
      return value ? [...value] : null
    },
    save: (objectCode: string, recordId: string, expandedGroups: string[]) => {
      map.set(makeKey(objectCode, recordId), [...expandedGroups])
    },
    get: (objectCode: string, recordId: string): string[] | null => {
      const value = map.get(makeKey(objectCode, recordId))
      return value ? [...value] : null
    },
    set: (objectCode: string, recordId: string, expandedGroups: string[]) => {
      map.set(makeKey(objectCode, recordId), [...expandedGroups])
    }
  }
}

const defaultGroups = (): RelationGroupExpansionItem[] => ([
  { key: 'workflow', defaultExpanded: true },
  { key: 'finance', defaultExpanded: false }
])

describe('useRelationGroupExpansion', () => {
  it('hydrates from preference when scope exists and falls back to defaults otherwise', async () => {
    const store = createMemoryPreferenceStore()
    store.set('Organization', 'org-2', ['finance'])

    const Host = defineComponent({
      setup() {
        const objectCode = ref('Organization')
        const recordId = ref('org-1')
        const groups = ref<RelationGroupExpansionItem[]>(defaultGroups())
        const state = useRelationGroupExpansion({
          groups: () => groups.value,
          objectCode: () => objectCode.value,
          scopeId: () => recordId.value,
          loadPreference: store.load,
          savePreference: store.save
        })
        return { objectCode, recordId, groups, ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['workflow'])

    ;(wrapper.vm as any).recordId = 'org-2'
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['finance'])

    wrapper.unmount()
  })

  it('persists expanded groups after toggle for scoped records', async () => {
    const store = createMemoryPreferenceStore()

    const Host = defineComponent({
      setup() {
        const objectCode = ref('Organization')
        const recordId = ref('org-3')
        const groups = ref<RelationGroupExpansionItem[]>(defaultGroups())
        const state = useRelationGroupExpansion({
          groups: () => groups.value,
          objectCode: () => objectCode.value,
          scopeId: () => recordId.value,
          loadPreference: store.load,
          savePreference: store.save
        })
        return { objectCode, recordId, groups, ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)
    await nextTick()

    ;(wrapper.vm as any).toggle('finance')
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['workflow', 'finance'])
    expect(store.get('Organization', 'org-3')).toEqual(['workflow', 'finance'])

    ;(wrapper.vm as any).toggle('workflow')
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['finance'])
    expect(store.get('Organization', 'org-3')).toEqual(['finance'])

    wrapper.unmount()
  })

  it('does not persist when scope is incomplete and filters invalid groups', async () => {
    const store = createMemoryPreferenceStore()

    const Host = defineComponent({
      setup() {
        const objectCode = ref('Organization')
        const recordId = ref('')
        const groups = ref<RelationGroupExpansionItem[]>(defaultGroups())
        const state = useRelationGroupExpansion({
          groups: () => groups.value,
          objectCode: () => objectCode.value,
          scopeId: () => recordId.value,
          loadPreference: store.load,
          savePreference: store.save
        })
        return { objectCode, recordId, groups, ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)
    await nextTick()

    ;(wrapper.vm as any).toggle('finance')
    await nextTick()
    expect(store.get('Organization', '')).toBeNull()

    ;(wrapper.vm as any).recordId = 'org-4'
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['workflow'])

    ;(wrapper.vm as any).groups = [{ key: 'workflow', defaultExpanded: true }]
    await nextTick()
    expect((wrapper.vm as any).activeGroups).toEqual(['workflow'])
    expect(store.get('Organization', 'org-4')).toEqual(['workflow'])

    wrapper.unmount()
  })
})
