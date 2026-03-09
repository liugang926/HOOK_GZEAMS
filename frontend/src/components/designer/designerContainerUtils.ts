import type {
  ContainerMeta,
  LayoutConfig,
  LayoutField
} from '@/components/designer/designerTypes'

export function parseDesignerContainerMeta(el: HTMLElement | null): ContainerMeta | null {
  if (!el) return null
  const kind = el.dataset.containerKind as ContainerMeta['kind'] | undefined
  const sectionId = el.dataset.sectionId || ''

  if (!kind || !sectionId) return null
  if (kind === 'tab') {
    const tabId = el.dataset.tabId || ''
    if (!tabId) return null
    return { kind, sectionId, tabId }
  }
  if (kind === 'collapse') {
    const collapseId = el.dataset.collapseId || ''
    if (!collapseId) return null
    return { kind, sectionId, collapseId }
  }
  return { kind: 'section', sectionId }
}

export function getDesignerFieldArrayRef(
  config: LayoutConfig,
  meta: ContainerMeta
): LayoutField[] | null {
  const section = (config.sections || []).find((item) => item.id === meta.sectionId)
  if (!section) return null

  if (meta.kind === 'section') {
    section.fields = section.fields || []
    return section.fields
  }

  if (meta.kind === 'tab') {
    section.tabs = section.tabs || []
    const tab = (section.tabs || []).find((item) => item.id === meta.tabId)
    if (!tab) return null
    tab.fields = tab.fields || []
    return tab.fields
  }

  section.items = section.items || []
  const collapseItem = (section.items || []).find((item) => item.id === meta.collapseId)
  if (!collapseItem) return null
  collapseItem.fields = collapseItem.fields || []
  return collapseItem.fields
}
