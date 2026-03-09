import { computed } from 'vue'

interface DetailSectionLike {
  name: string
  position?: 'main' | 'sidebar'
}

interface UseBaseDetailPageLayoutOptions {
  sections: () => DetailSectionLike[]
}

export function useBaseDetailPageLayout(options: UseBaseDetailPageLayoutOptions) {
  const mainSections = computed(() => {
    return options.sections().filter((section) => section.position !== 'sidebar')
  })

  const sidebarSections = computed(() => {
    return options.sections().filter((section) => section.position === 'sidebar')
  })

  return {
    mainSections,
    sidebarSections
  }
}
