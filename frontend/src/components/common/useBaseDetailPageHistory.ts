import { computed } from 'vue'

interface HistoryPropsLike {
  data: Record<string, any>
  objectCode?: string
  showActivityHistory: boolean
}

interface UseBaseDetailPageHistoryOptions {
  props: HistoryPropsLike
}

export function useBaseDetailPageHistory(options: UseBaseDetailPageHistoryOptions) {
  const { props } = options

  const activityRecordId = computed(() => {
    const candidate = props.data?.id || props.data?.code || props.data?.dataNo || props.data?.data_no
    if (candidate === undefined || candidate === null) return ''
    return String(candidate).trim()
  })

  const hasActivityHistory = computed(() => {
    return props.showActivityHistory && !!String(props.objectCode || '').trim() && !!activityRecordId.value
  })

  return {
    activityRecordId,
    hasActivityHistory
  }
}
