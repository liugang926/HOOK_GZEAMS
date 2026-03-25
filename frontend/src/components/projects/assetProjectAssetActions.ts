type ProjectRecord = Record<string, unknown> | null | undefined
type ProjectAssetRecord = Record<string, unknown>

const readString = (value: unknown) => {
  if (value && typeof value === 'object') {
    const candidate = value as Record<string, unknown>
    for (const key of ['id', 'value', 'code', 'name', 'title']) {
      const nested = String(candidate[key] || '').trim()
      if (nested) return nested
    }
  }
  return String(value || '').trim()
}

const readRecordValue = (record: ProjectRecord, keys: string[]) => {
  if (!record || typeof record !== 'object') return ''
  for (const key of keys) {
    const value = readString((record as Record<string, unknown>)[key])
    if (value) return value
  }
  return ''
}

const buildProjectLabel = (projectRecord: ProjectRecord) => {
  const projectCode = readRecordValue(projectRecord, ['projectCode', 'project_code', 'code'])
  const projectName = readRecordValue(projectRecord, ['projectName', 'project_name', 'name', 'title'])
  if (projectCode && projectName) return `${projectCode} ${projectName}`
  return projectCode || projectName || ''
}

const buildAssetLabel = (row: ProjectAssetRecord) => {
  const assetCode = readRecordValue(row, ['assetCode', 'asset_code'])
  const assetName = readRecordValue(row, ['assetName', 'asset_name'])
  if (assetCode && assetName) return `${assetCode} ${assetName}`
  return assetCode || assetName || ''
}

const toDateString = (value: Date) => value.toISOString().slice(0, 10)

export const buildAssetProjectDetailPath = (projectId: string) => {
  const normalizedProjectId = readString(projectId)
  return `/objects/AssetProject/${encodeURIComponent(normalizedProjectId)}`
}

export const buildAssetProjectReturnCreateRoute = ({
  projectId,
  projectRecord,
  row,
  date = new Date(),
}: {
  projectId: string
  projectRecord?: ProjectRecord
  row: ProjectAssetRecord
  date?: Date
}) => {
  const assetId = readRecordValue(row, ['asset', 'assetId', 'asset_id'])
  const projectAllocationId = readRecordValue(row, ['id', 'projectAllocationId', 'project_allocation_id'])
  const projectLabel = buildProjectLabel(projectRecord)
  const assetLabel = buildAssetLabel(row)
  const returnReason = projectLabel
    ? `Project asset recycle: ${projectLabel}`
    : 'Project asset recycle'
  const remarkParts = [
    projectLabel ? `Source project: ${projectLabel}` : '',
    assetLabel ? `Asset: ${assetLabel}` : '',
  ].filter(Boolean)

  return {
    path: '/objects/AssetReturn/create',
    query: {
      prefill: JSON.stringify({
        return_date: toDateString(date),
        return_reason: returnReason,
        items: assetId
          ? [
            {
              asset_id: assetId,
              project_allocation_id: projectAllocationId,
              asset_status: 'idle',
              remark: remarkParts.join(' | '),
            },
          ]
          : [],
      }),
      returnTo: buildAssetProjectDetailPath(projectId),
    },
  }
}

export const formatTransferProjectOptionLabel = (row: ProjectRecord) => {
  const projectCode = readRecordValue(row, ['projectCode', 'project_code'])
  const projectName = readRecordValue(row, ['projectName', 'project_name', 'name'])
  if (projectCode && projectName) return `${projectCode} - ${projectName}`
  return projectCode || projectName || ''
}
