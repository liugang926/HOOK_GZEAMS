import { ref, watch, type Ref } from 'vue'
import type { DynamicDetailNavigationCounts } from './detailNavigationModel'
import {
  createEmptyDynamicDetailNavigationCounts,
  loadDynamicDetailEnhancementData,
} from './dynamicDetailEnhancementData'

interface Params {
  objectCode: Ref<string>
  recordId: Ref<string>
  loadedRecord: Ref<Record<string, any> | null>
}

export const useDynamicDetailEnhancementData = ({
  objectCode,
  recordId,
  loadedRecord,
}: Params) => {
  const relatedCounts = ref<DynamicDetailNavigationCounts>(createEmptyDynamicDetailNavigationCounts())
  const relatedRecord = ref<Record<string, any> | null>(null)
  let activeLoadToken = 0

  const loadDetailEnhancementData = async () => {
    const token = ++activeLoadToken
    relatedCounts.value = createEmptyDynamicDetailNavigationCounts()
    relatedRecord.value = null

    const result = await loadDynamicDetailEnhancementData({
      objectCode: objectCode.value,
      recordId: recordId.value,
      loadedRecord: loadedRecord.value,
    })

    if (token !== activeLoadToken) {
      return
    }

    relatedCounts.value = result.relatedCounts
    relatedRecord.value = result.relatedRecord
  }

  watch(
    () => [objectCode.value, recordId.value, loadedRecord.value],
    () => {
      loadDetailEnhancementData()
    },
    { immediate: true },
  )

  return {
    relatedCounts,
    relatedRecord,
    loadDetailEnhancementData,
  }
}
