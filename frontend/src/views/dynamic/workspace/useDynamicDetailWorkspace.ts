import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { ObjectWorkspaceChip, ObjectWorkspaceStat } from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'

interface Params {
  isZhLocale: ComputedRef<boolean>
  objectCode: Ref<string>
  recordId: Ref<string>
  objectMetadata: Ref<ObjectMetadata | null>
  objectDisplayName: ComputedRef<string>
  canEdit: ComputedRef<boolean>
  loadedRecord: Ref<Record<string, any> | null>
}

export const useDynamicDetailWorkspace = ({
  isZhLocale,
  objectCode,
  recordId,
  objectMetadata,
  objectDisplayName,
  canEdit,
  loadedRecord,
}: Params) => {
  const moduleLabel = computed(() => {
    return String(objectMetadata.value?.module || '').trim() || objectCode.value
  })

  const detailModeLabel = computed(() => {
    return isZhLocale.value ? '对象详情' : 'Detail view'
  })

  const summaryLabel = computed(() => {
    return isZhLocale.value ? '对象摘要' : 'Object summary'
  })

  const objectCodeLabel = computed(() => {
    return isZhLocale.value ? '对象编码' : 'Object code'
  })

  const recordIdLabel = computed(() => {
    return isZhLocale.value ? '记录编号' : 'Record ID'
  })

  const moduleNameLabel = computed(() => {
    return isZhLocale.value ? '所属模块' : 'Module'
  })

  const accessLabel = computed(() => {
    return isZhLocale.value ? '当前权限' : 'Access'
  })

  const heroAccessValue = computed(() => {
    if (canEdit.value) return isZhLocale.value ? '可查看与编辑' : 'View and edit'
    return isZhLocale.value ? '只读查看' : 'View only'
  })

  const statusLabel = computed(() => {
    return isZhLocale.value ? '当前状态' : 'Status'
  })

  const heroStatusValue = computed(() => {
    const status = loadedRecord.value?.status
    if (status !== undefined && status !== null && String(status).trim()) return String(status)
    return isZhLocale.value ? '已加载' : 'Loaded'
  })

  const detailPanelTitle = computed(() => {
    return isZhLocale.value ? '记录详情' : 'Record details'
  })

  const detailPanelDescription = computed(() => {
    return isZhLocale.value
      ? '在这里查看字段详情、关联记录和业务状态。需要调整内容时，可直接使用详情页中的编辑能力。'
      : 'Review fields, related records, and business status here. Use the built-in detail actions whenever updates are needed.'
  })

  const heroTitle = computed(() => {
    const candidates = [
      loadedRecord.value?.name,
      loadedRecord.value?.title,
      loadedRecord.value?.code,
      loadedRecord.value?.assetName,
      loadedRecord.value?.asset_name,
      loadedRecord.value?.assetCode,
      loadedRecord.value?.asset_code,
    ]
    const recordTitle = candidates.find((value) => value !== undefined && value !== null && String(value).trim())
    return recordTitle ? String(recordTitle) : objectDisplayName.value
  })

  const heroDescription = computed(() => {
    if (isZhLocale.value) {
      return `${objectDisplayName.value} 的详情页已按当前对象布局生成，可用于查看审计信息、关联对象和状态流转。`
    }
    return `This ${objectDisplayName.value} detail page is generated from the current object layout for reviewing audit info, related records, and status changes.`
  })

  const tipsLabel = computed(() => {
    return isZhLocale.value ? '查看提示' : 'Review tips'
  })

  const tips = computed<string[]>(() => [
    isZhLocale.value
      ? '如果详情页展示内容缺失，优先检查对象布局和字段详情可见性配置。'
      : 'If expected content is missing, verify the object layout and detail visibility settings first.',
    isZhLocale.value
      ? '关联记录支持直接跳转详情或编辑页，适合连续核对上下游业务数据。'
      : 'Related records support direct navigation to detail and edit pages for smoother cross-object review.',
    isZhLocale.value
      ? '生命周期对象会在详情页额外展示流程步骤和扩展业务信息。'
      : 'Lifecycle-enabled objects expose workflow steps and extra business information in this view.',
  ])

  const heroChips = computed<ObjectWorkspaceChip[]>(() => {
    const chips: ObjectWorkspaceChip[] = [
      { label: detailModeLabel.value, kind: 'primary' },
      { label: objectCode.value },
    ]
    if (recordId.value) {
      chips.push({ label: `#${recordId.value}`, kind: 'muted' })
    }
    return chips
  })

  const heroStats = computed<ObjectWorkspaceStat[]>(() => ([
    { label: statusLabel.value, value: heroStatusValue.value },
    { label: objectCodeLabel.value, value: objectCode.value },
    { label: accessLabel.value, value: heroAccessValue.value },
  ]))

  const infoRows = computed<ObjectWorkspaceInfoRow[]>(() => ([
    { label: objectCodeLabel.value, value: objectCode.value },
    { label: recordIdLabel.value, value: recordId.value || '--' },
    { label: moduleNameLabel.value, value: moduleLabel.value },
  ]))

  return {
    moduleLabel,
    detailModeLabel,
    detailPanelTitle,
    detailPanelDescription,
    summaryLabel,
    tipsLabel,
    heroTitle,
    heroDescription,
    heroChips,
    heroStats,
    infoRows,
    tips,
  }
}
