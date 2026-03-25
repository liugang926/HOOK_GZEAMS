import type { Ref } from 'vue'
import type {
  DesignerAnyRecord,
  DesignerFieldDefinition,
  LayoutConfig
} from '@/components/designer/designerTypes'
import type { ReverseRelationField } from '@/components/common/BaseDetailPage.vue'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

export type AnyRecord = DesignerAnyRecord
export type ApiDataEnvelope<T> = { data?: T }

export interface DesignerPersistenceHistory {
  clear: () => void
  push: (snapshot: Record<string, unknown>, description: string) => void
}

export interface UseDesignerPersistenceOptions {
  props: {
    layoutId?: string
    mode?: string
    objectCode?: string
    layoutName?: string
    businessObjectId?: string
    layoutConfig?: LayoutConfig
  }
  availableFields: Ref<DesignerFieldDefinition[]>
  aggregateDetailRegions: Ref<RuntimeAggregateDetailRegion[]>
  previewReverseRelations: Ref<ReverseRelationField[]>
  layoutConfig: Ref<LayoutConfig>
  layoutMode: Ref<'Detail' | 'Compact'>
  previewMode: Ref<'current' | 'active'>
  currentLayoutSnapshot: Ref<LayoutConfig | null>
  previewLoading: Ref<boolean>
  isDefault: Ref<boolean>
  isPublished: Ref<boolean>
  layoutVersion: Ref<string>
  sharedEditLayoutId: Ref<string>
  sampleData: Ref<Record<string, unknown>>
  saving: Ref<boolean>
  publishing: Ref<boolean>
  selectedId: Ref<string>
  history: DesignerPersistenceHistory
  normalizeAvailableFields: (fields: AnyRecord[]) => DesignerFieldDefinition[]
  mapPreviewReverseRelations: (fields: AnyRecord[]) => ReverseRelationField[]
  buildLayoutConfigWithPlacementSnapshot: (rawConfig: LayoutConfig) => LayoutConfig
  previewObjectName: Ref<string>
  unwrapData: <T>(raw: T | ApiDataEnvelope<T>) => T
  readErrorMessage: (error: unknown) => string | null
  emitSave: (data: Record<string, unknown>) => void
  emitPublished: (data: LayoutConfig | Record<string, unknown>) => void
}
