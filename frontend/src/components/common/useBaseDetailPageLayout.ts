import { computed } from 'vue'

interface DetailFieldLike {
  prop: string
  label: string
  hidden?: boolean
  span?: number
  minHeight?: number
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas?: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

interface DetailTabLike {
  fields: DetailFieldLike[]
}

interface DetailSectionLike {
  name: string
  type?: string
  position?: 'main' | 'sidebar'
  fields: DetailFieldLike[]
  tabs?: DetailTabLike[]
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
