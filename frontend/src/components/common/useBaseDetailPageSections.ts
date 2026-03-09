import { computed, ref, watch, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { resolveTranslatableText } from '@/utils/localeText'

interface DetailTabLike {
  id: string
  title: any
  fields: unknown[]
}

interface DetailSectionLike {
  name: string
  title: any
  type?: string
  collapsible?: boolean
  collapsed?: boolean
  fields: unknown[]
  tabs?: DetailTabLike[]
}

interface UseBaseDetailPageSectionsOptions {
  sections: Ref<DetailSectionLike[]>
  emitSectionClick: (sectionName: string) => void
}

export function useBaseDetailPageSections(options: UseBaseDetailPageSectionsOptions) {
  const { t, locale } = useI18n()
  const collapsedSections = ref<Set<string>>(new Set())
  const activeTabs = ref<Record<string, string>>({})
  const activeMainTab = ref<string>('details')

  const getSectionDisplayTitle = (section: DetailSectionLike): string => {
    const baseTitle = resolveTranslatableText(section.title, locale.value as 'zh-CN' | 'en-US') || ''
    if (section.type !== 'tab' || !Array.isArray(section.tabs) || section.tabs.length === 0) {
      return baseTitle
    }

    const activeId = activeTabs.value[section.name] || section.tabs[0]?.id
    const activeTab = section.tabs.find((tab) => tab.id === activeId) || section.tabs[0]
    const tabTitle = resolveTranslatableText(activeTab?.title, locale.value as 'zh-CN' | 'en-US') || ''

    if (!baseTitle) return tabTitle
    if (!tabTitle) return baseTitle
    if (baseTitle === tabTitle) return baseTitle
    return `${baseTitle} / ${tabTitle}`
  }

  const getSectionErrorTitle = (section: DetailSectionLike): string => {
    const sectionTitle = getSectionDisplayTitle(section)
    if (!sectionTitle) return t('common.messages.loadFailed')
    return `${sectionTitle} - ${t('common.messages.loadFailed')}`
  }

  const toggleSection = (sectionName: string) => {
    if (collapsedSections.value.has(sectionName)) {
      collapsedSections.value.delete(sectionName)
    } else {
      collapsedSections.value.add(sectionName)
    }
  }

  const handleSectionHeaderClick = (section: DetailSectionLike) => {
    options.emitSectionClick(section.name)
    if (section.collapsible) {
      toggleSection(section.name)
    }
  }

  const isSectionCollapsed = (section: DetailSectionLike) => {
    return Boolean(section.collapsed || collapsedSections.value.has(section.name))
  }

  watch(
    options.sections,
    (sections) => {
      const nextTabs = { ...activeTabs.value }
      let changed = false

      for (const section of sections || []) {
        if (section.type !== 'tab' || !Array.isArray(section.tabs) || section.tabs.length === 0) continue
        const current = nextTabs[section.name]
        const exists = section.tabs.some((tab) => tab.id === current)
        if (!exists) {
          nextTabs[section.name] = section.tabs[0].id
          changed = true
        }
      }

      if (changed) activeTabs.value = nextTabs
    },
    { immediate: true }
  )

  return {
    activeTabs,
    activeMainTab,
    getSectionDisplayTitle,
    getSectionErrorTitle,
    toggleSection,
    handleSectionHeaderClick,
    isSectionCollapsed
  }
}
