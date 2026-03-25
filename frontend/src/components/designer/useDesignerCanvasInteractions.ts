import type { ComputedRef, Ref } from 'vue'
import type {
  ContainerMeta,
  DesignerFieldDefinition,
  DesignerDetailRegionOption,
  DesignerSectionTemplateOption,
  SectionTemplateType,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'
import { useDesignerDragInteractions } from '@/components/designer/useDesignerDragInteractions'
import { useDesignerResizeInteractions } from '@/components/designer/useDesignerResizeInteractions'

interface UseDesignerCanvasInteractionsOptions {
  layoutConfig: Ref<LayoutConfig>
  renderMode: Ref<'design' | 'preview'>
  isDesignMode: ComputedRef<boolean>
  selectedId: Ref<string>
  fieldProps: Ref<Partial<LayoutField>>
  draggedField: Ref<DesignerFieldDefinition | null>
  draggedDetailRegion: Ref<DesignerDetailRegionOption | null>
  draggedSectionId: Ref<string | null>
  isDragOverCanvas: Ref<boolean>
  dragOverSection: Ref<string | null>
  canvasAreaElement: ComputedRef<HTMLElement | null>
  canvasContentElement: ComputedRef<HTMLElement | null>
  canAddField: (field: DesignerFieldDefinition) => boolean
  notifyUnsupportedField: (field: DesignerFieldDefinition) => void
  handleFieldClick: (field: DesignerFieldDefinition) => void
  addSectionTemplate: (
    template?: SectionTemplateType | DesignerSectionTemplateOption,
    options?: { insertIndex?: number | null }
  ) => void
  addDetailRegion: (
    detailRegion?: string | DesignerDetailRegionOption,
    options?: { insertIndex?: number | null }
  ) => void
  moveSectionToIndex: (sectionId: string, options?: { insertIndex?: number | null }) => void
  addFieldToContainer: (field: DesignerFieldDefinition, meta: ContainerMeta) => void
  commitLayoutChange: (newConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
  findSectionByFieldId: (config: LayoutConfig, fieldId: string) => LayoutSection | null
  findLayoutFieldById: (config: LayoutConfig, fieldId: string) => LayoutField | null
  getColumns: (section: Partial<LayoutSection> | null | undefined) => number
  resolveLayoutFieldMinHeight: (field: LayoutField | null | undefined) => number | undefined
  clampFieldMinHeight: (value: number) => number
  setLayoutFieldMinHeight: (field: LayoutField, value: unknown) => void
  selectField: (field: LayoutField, section: LayoutSection) => void
}

export function useDesignerCanvasInteractions(options: UseDesignerCanvasInteractionsOptions) {
  const resizeInteractions = useDesignerResizeInteractions({
    layoutConfig: options.layoutConfig,
    isDesignMode: options.isDesignMode,
    selectedId: options.selectedId,
    fieldProps: options.fieldProps,
    canvasAreaElement: options.canvasAreaElement,
    canvasContentElement: options.canvasContentElement,
    findSectionByFieldId: options.findSectionByFieldId,
    findLayoutFieldById: options.findLayoutFieldById,
    getColumns: options.getColumns,
    resolveLayoutFieldMinHeight: options.resolveLayoutFieldMinHeight,
    clampFieldMinHeight: options.clampFieldMinHeight,
    setLayoutFieldMinHeight: options.setLayoutFieldMinHeight,
    selectField: options.selectField,
    commitLayoutChange: options.commitLayoutChange
  })

  const dragInteractions = useDesignerDragInteractions({
    layoutConfig: options.layoutConfig,
    renderMode: options.renderMode,
    draggedField: options.draggedField,
    draggedDetailRegion: options.draggedDetailRegion,
    draggedSectionId: options.draggedSectionId,
    isDragOverCanvas: options.isDragOverCanvas,
    dragOverSection: options.dragOverSection,
    canvasContentElement: options.canvasContentElement,
    canAddField: options.canAddField,
    notifyUnsupportedField: options.notifyUnsupportedField,
    handleFieldClick: options.handleFieldClick,
    addSectionTemplate: options.addSectionTemplate,
    addDetailRegion: options.addDetailRegion,
    moveSectionToIndex: options.moveSectionToIndex,
    addFieldToContainer: options.addFieldToContainer,
    commitLayoutChange: options.commitLayoutChange
  })

  return {
    ...resizeInteractions,
    ...dragInteractions
  }
}
