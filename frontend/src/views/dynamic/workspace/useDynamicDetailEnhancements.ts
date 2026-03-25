import { computed, type Ref } from 'vue'
import {
  buildDynamicDetailNavigationSection,
  buildDynamicDetailTimelineConfig,
} from './detailNavigationModel'
import { useDynamicDetailEnhancementData } from './useDynamicDetailEnhancementData'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  loadedRecord: Ref<Record<string, any> | null>
  t: (key: string, params?: Record<string, unknown>) => string
}

export const useDynamicDetailEnhancements = ({
  objectCode,
  recordId,
  loadedRecord,
  t,
}: Params) => {
  const { relatedCounts, relatedRecord } = useDynamicDetailEnhancementData({
    objectCode,
    recordId,
    loadedRecord,
  })

  const detailNavigationSection = computed(() => {
    return buildDynamicDetailNavigationSection({
      objectCode: objectCode.value,
      recordId: recordId.value,
      record: loadedRecord.value,
      relatedRecord: relatedRecord.value,
      counts: relatedCounts.value,
      t,
    })
  })

  const detailTimelineConfig = computed(() => {
    return buildDynamicDetailTimelineConfig({
      objectCode: objectCode.value,
      recordId: recordId.value,
    })
  })

  return {
    detailNavigationSection,
    detailTimelineConfig,
  }
}
