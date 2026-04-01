import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { AggregateDocumentResponse } from '@/types/runtime'
import type {
  ObjectWorkspaceActionLink,
  ObjectWorkspaceChip,
  ObjectWorkspaceStat,
} from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import {
  DETAIL_ACTIVITY_ANCHOR,
  buildTimelineHighlightSourceLocation,
  formatTimelineHighlightContext,
  formatTimelineHighlightSummary,
  formatTimelineHighlightTimestamp,
  resolveLatestTimelineHighlight,
  resolveTimelineHighlightSourceLabel,
  summarizeTimelineHighlightValue,
  type TimelineHighlightSummary,
} from '@/utils/timelineHighlights'

interface Params {
  isZhLocale: ComputedRef<boolean>
  objectCode: Ref<string>
  recordId: Ref<string>
  objectMetadata: Ref<ObjectMetadata | null>
  objectDisplayName: ComputedRef<string>
  loadedRecord: Ref<Record<string, unknown> | null>
  documentPayload: Ref<AggregateDocumentResponse | null>
  hasActivitySection: ComputedRef<boolean>
}

export const useDynamicDetailWorkspace = ({
  isZhLocale,
  objectCode,
  recordId,
  objectMetadata,
  objectDisplayName,
  loadedRecord,
  documentPayload,
  hasActivitySection,
}: Params) => {
  const moduleLabel = computed(() => {
    return String(objectMetadata.value?.module || '').trim() || objectCode.value
  })
  const isAssetProject = computed(() => objectCode.value === 'AssetProject')
  const getRecordValue = (key: string) => {
    if (!loadedRecord.value || typeof loadedRecord.value !== 'object') return undefined
    return loadedRecord.value[key]
  }
  const normalizeStatValue = (value: unknown, fallback: string | number): string | number => {
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && value.trim()) return value.trim()
    return fallback
  }
  const resolveNestedRecordValue = (
    record: Record<string, unknown> | null | undefined,
    path: string[],
  ): unknown => {
    let current: unknown = record
    for (const segment of path) {
      if (!current || typeof current !== 'object') return undefined
      current = (current as Record<string, unknown>)[segment]
    }
    return current
  }
  const resolveCancelReason = () => {
    const record = loadedRecord.value
    if (!record || typeof record !== 'object') return ''
    const candidatePaths = [
      ['customFields', 'cancelReason'],
      ['custom_fields', 'cancel_reason'],
      ['closureSummary', 'metrics', 'cancelReason'],
      ['closure_summary', 'metrics', 'cancel_reason'],
    ]
    for (const path of candidatePaths) {
      const value = resolveNestedRecordValue(record, path)
      if (typeof value === 'string' && value.trim()) {
        return value.trim()
      }
    }
    return ''
  }
  const resolveNestedLabel = (value: unknown, keys: string[], fallback = '--') => {
    if (!value || typeof value !== 'object') return fallback
    const candidate = value as Record<string, unknown>
    for (const key of keys) {
      const nestedValue = candidate[key]
      if (typeof nestedValue === 'string' && nestedValue.trim()) {
        return nestedValue.trim()
      }
    }
    return fallback
  }

  const detailModeLabel = computed(() => {
    if (isAssetProject.value) {
      return isZhLocale.value ? '项目工作区' : 'Project workspace'
    }
    return isZhLocale.value ? '对象详情' : 'Detail view'
  })

  const summaryLabel = computed(() => {
    if (isAssetProject.value) {
      return isZhLocale.value ? '项目摘要' : 'Project summary'
    }
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

  const statusLabel = computed(() => {
    return isZhLocale.value ? '当前状态' : 'Status'
  })
  const cancelReasonLabel = computed(() => {
    return isZhLocale.value ? '取消原因' : 'Cancel reason'
  })
  const latestSignalLabel = computed(() => {
    return isZhLocale.value ? '最近原因信号' : 'Latest signal'
  })
  const latestSignalSourceLabel = computed(() => {
    return isZhLocale.value ? '来源对象' : 'Source object'
  })
  const latestSignalTimeLabel = computed(() => {
    return isZhLocale.value ? '发生时间' : 'Signal time'
  })
  const openSourceActionLabel = computed(() => {
    return isZhLocale.value ? '查看来源' : 'Open source'
  })
  const openActivityActionLabel = computed(() => {
    return isZhLocale.value ? '跳转活动区' : 'Jump to activity'
  })
  const displayLocale = computed(() => (isZhLocale.value ? 'zh-CN' : 'en-US'))

  const heroStatusValue = computed(() => {
    const status = loadedRecord.value?.status
    if (status !== undefined && status !== null && String(status).trim()) return String(status)
    return isZhLocale.value ? '已加载' : 'Loaded'
  })
  const isCancelled = computed(() => heroStatusValue.value.trim().toLowerCase() === 'cancelled')
  const cancelReason = computed(() => resolveCancelReason())
  const cancelReasonTooltip = computed(() => {
    if (!isCancelled.value || !cancelReason.value) return ''
    return `${cancelReasonLabel.value}: ${cancelReason.value}`
  })
  const fallbackSignals = computed<TimelineHighlightSummary[]>(() => {
    const record = loadedRecord.value
    if (!record || typeof record !== 'object') return []
    const customFields = (
      (record.custom_fields as Record<string, unknown> | undefined) ||
      (record.customFields as Record<string, unknown> | undefined) ||
      {}
    )
    const directRecord = record as Record<string, unknown>
    const candidates = [
      {
        code: 'reject_reason',
        label: isZhLocale.value ? '驳回原因' : 'Rejection reason',
        value: directRecord.reject_reason ?? customFields.reject_reason,
      },
      {
        code: 'approval_comment',
        label: isZhLocale.value ? '审批备注' : 'Approval comment',
        value: directRecord.approval_comment ?? customFields.approval_comment,
      },
      {
        code: 'inspection_result',
        label: isZhLocale.value ? '验收结果' : 'Inspection result',
        value: directRecord.inspection_result,
      },
      {
        code: 'verification_result',
        label: isZhLocale.value ? '维修验收结果' : 'Verification result',
        value: directRecord.verification_result,
      },
      {
        code: 'return_comment',
        label: isZhLocale.value ? '归还备注' : 'Return comment',
        value: directRecord.return_comment,
      },
    ]

    return candidates
      .map((candidate) => ({
        code: candidate.code,
        label: candidate.label,
        value: typeof candidate.value === 'string' ? candidate.value.trim() : '',
        createdAt: String(
          directRecord.updated_at ||
          directRecord.updatedAt ||
          directRecord.created_at ||
          directRecord.createdAt ||
          '',
        ).trim() || null,
        source: objectCode.value,
        sourceLabel: objectDisplayName.value,
        objectCode: objectCode.value,
        objectId: String(directRecord.id || recordId.value || '').trim() || undefined,
      }))
      .filter((candidate) => candidate.value)
  })
  const latestReasonHighlight = computed<TimelineHighlightSummary | null>(() => {
    const timelineEntries = Array.isArray(documentPayload.value?.timeline) && (documentPayload.value?.timeline || []).length > 0
      ? documentPayload.value?.timeline || []
      : (Array.isArray(documentPayload.value?.workflow?.timeline) ? documentPayload.value?.workflow?.timeline || [] : [])
    return resolveLatestTimelineHighlight(timelineEntries) || fallbackSignals.value[0] || null
  })
  const latestSignalSummary = computed(() => {
    return formatTimelineHighlightSummary(latestReasonHighlight.value)
  })
  const latestSignalSourceValue = computed(() => {
    return resolveTimelineHighlightSourceLabel(latestReasonHighlight.value)
  })
  const latestSignalTimeValue = computed(() => {
    return formatTimelineHighlightTimestamp(
      latestReasonHighlight.value?.createdAt,
      displayLocale.value,
    )
  })
  const latestSignalMeta = computed(() => {
    return formatTimelineHighlightContext(latestReasonHighlight.value, displayLocale.value)
  })
  const latestSignalActions = computed<ObjectWorkspaceActionLink[]>(() => {
    if (!latestReasonHighlight.value) return []
    const actions: ObjectWorkspaceActionLink[] = []
    const sourceLocation = buildTimelineHighlightSourceLocation({
      highlight: latestReasonHighlight.value,
      currentObjectCode: objectCode.value,
      currentRecordId: recordId.value,
    })

    if (sourceLocation) {
      actions.push({
        label: openSourceActionLabel.value,
        to: sourceLocation,
      })
    }

    if (hasActivitySection.value) {
      actions.push({
        label: openActivityActionLabel.value,
        to: { hash: DETAIL_ACTIVITY_ANCHOR },
      })
    }

    return actions
  })
  const latestSignalTooltip = computed(() => {
    return [latestSignalSummary.value, latestSignalMeta.value].filter(Boolean).join(' · ')
  })
  const latestSignalValue = computed(() => {
    if (!latestReasonHighlight.value) return ''
    return summarizeTimelineHighlightValue(latestReasonHighlight.value.value, 36)
  })

  const detailPanelTitle = computed(() => {
    if (isAssetProject.value) {
      return isZhLocale.value ? '项目指挥面板' : 'Project command panel'
    }
    return isZhLocale.value ? '记录详情' : 'Record details'
  })

  const detailPanelDescription = computed(() => {
    if (isAssetProject.value) {
      return isZhLocale.value
        ? '这里聚合项目主数据、预算执行与项目资产/成员面板，适合连续处理项目协同任务。'
        : 'This workspace brings together the core project record, budget execution, and the related asset/member panels for faster project coordination.'
    }
    return isZhLocale.value
      ? '在这里查看字段详情、关联记录和业务状态。需要调整内容时，可直接使用详情页中的编辑能力。'
      : 'Review fields, related records, and business status here. Use the built-in detail actions whenever updates are needed.'
  })

  const heroTitle = computed(() => {
    const candidates = [
      loadedRecord.value?.projectName,
      loadedRecord.value?.project_name,
      loadedRecord.value?.name,
      loadedRecord.value?.title,
      loadedRecord.value?.projectCode,
      loadedRecord.value?.project_code,
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
    if (isAssetProject.value) {
      return isZhLocale.value
        ? `${objectDisplayName.value} 详情已升级为统一项目工作区，可继续处理项目资产、项目成员与预算执行上下文。`
        : `This ${objectDisplayName.value} detail view now acts as the unified project workspace for handling project assets, members, and budget context.`
    }
    if (isZhLocale.value) {
      return `${objectDisplayName.value} 的详情页已按当前对象布局生成，可用于查看审计信息、关联对象和状态流转。`
    }
    return `This ${objectDisplayName.value} detail page is generated from the current object layout for reviewing audit info, related records, and status changes.`
  })

  const tipsLabel = computed(() => {
    if (isAssetProject.value) {
      return isZhLocale.value ? '项目提示' : 'Project tips'
    }
    return isZhLocale.value ? '查看提示' : 'Review tips'
  })

  const tips = computed<string[]>(() => [
    ...(isAssetProject.value
      ? [
        isZhLocale.value
          ? '如果项目资产或成员面板为空，先检查对应对象是否已按当前项目过滤创建记录。'
          : 'If the project asset or member panels are empty, verify that the related records were created against the current project context.',
        isZhLocale.value
          ? '修改预算、项目经理或时间计划后，可以使用“刷新汇总”动作重新同步项目概览指标。'
          : 'After changing budget, owner, or schedule details, use the refresh action to resync the project summary metrics.',
      ]
      : []),
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

  const processSummaryStats = computed<ObjectWorkspaceStat[]>(() => ([
    ...(isAssetProject.value
      ? [
        {
          label: isZhLocale.value ? '在用资产' : 'Active assets',
          value: normalizeStatValue(
            getRecordValue('activeAssets') ?? getRecordValue('active_assets'),
            0,
          ),
        },
        {
          label: isZhLocale.value ? '成员数' : 'Members',
          value: normalizeStatValue(
            getRecordValue('memberCount') ?? getRecordValue('member_count'),
            0,
          ),
        },
        {
          label: statusLabel.value,
          value: heroStatusValue.value,
          tooltip: cancelReasonTooltip.value || undefined,
        },
      ]
      : [
        {
          label: statusLabel.value,
          value: heroStatusValue.value,
          tooltip: cancelReasonTooltip.value || undefined,
        },
      ]),
  ]))
  const detailHeroStats = computed<ObjectWorkspaceStat[]>(() => [])

  const latestSignalInfoRows = computed<ObjectWorkspaceInfoRow[]>(() => {
    if (!latestReasonHighlight.value) return []

    const rows: ObjectWorkspaceInfoRow[] = [
      {
        label: latestSignalLabel.value,
        value: latestSignalSummary.value || latestSignalValue.value,
        tooltip: latestSignalTooltip.value || undefined,
        meta: latestSignalMeta.value || undefined,
        actions: latestSignalActions.value,
      },
    ]

    if (latestSignalSourceValue.value) {
      rows.push({
        label: latestSignalSourceLabel.value,
        value: latestSignalSourceValue.value,
        actions: latestSignalActions.value.filter((action) => action.label === openSourceActionLabel.value),
      })
    }

    if (latestSignalTimeValue.value) {
      rows.push({
        label: latestSignalTimeLabel.value,
        value: latestSignalTimeValue.value,
        actions: latestSignalActions.value.filter((action) => action.label === openActivityActionLabel.value),
      })
    }

    return rows
  })
  const closureRows = computed<ObjectWorkspaceInfoRow[]>(() => {
    if (!latestReasonHighlight.value) return []
    return [
      {
        label: latestSignalLabel.value,
        value: latestSignalSummary.value || latestSignalValue.value,
        tooltip: latestSignalTooltip.value || undefined,
        meta: latestSignalMeta.value || undefined,
        actions: latestSignalActions.value,
      },
    ]
  })

  const infoRows = computed<ObjectWorkspaceInfoRow[]>(() => ([
    ...(isAssetProject.value
      ? [
        {
          label: isZhLocale.value ? '项目编码' : 'Project code',
          value: normalizeStatValue(
            getRecordValue('projectCode') ?? getRecordValue('project_code'),
            '--',
          ),
        },
        {
          label: isZhLocale.value ? '项目经理' : 'Project manager',
          value: resolveNestedLabel(
            getRecordValue('projectManagerDetail'),
            ['fullName', 'full_name', 'name', 'username'],
          ),
        },
        {
          label: isZhLocale.value ? '所属部门' : 'Department',
          value: resolveNestedLabel(
            getRecordValue('departmentDetail'),
            ['name', 'departmentName'],
          ),
        },
      ]
      : [
        { label: objectCodeLabel.value, value: objectCode.value },
        { label: recordIdLabel.value, value: recordId.value || '--' },
        { label: moduleNameLabel.value, value: moduleLabel.value },
        ...latestSignalInfoRows.value,
        ...(isCancelled.value && cancelReason.value
          ? [{ label: cancelReasonLabel.value, value: cancelReason.value }]
          : []),
      ]),
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
    detailHeroStats,
    processSummaryStats,
    infoRows,
    closureRows,
    tips,
  }
}
