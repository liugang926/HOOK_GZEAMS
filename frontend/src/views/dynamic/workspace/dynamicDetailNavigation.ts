import type { Router } from 'vue-router'
import { deriveObjectCodeFromRelationCode } from '@/platform/reference/relationObjectCode'

const normalizePathPart = (value: unknown) => String(value || '').trim()

export const resolveDynamicDetailRelationObjectCode = (
  relationCode: string,
  targetObjectCode?: string,
) => {
  const explicitTarget = normalizePathPart(targetObjectCode)
  if (explicitTarget) return explicitTarget
  return deriveObjectCodeFromRelationCode(relationCode)
}

export const buildDynamicObjectListPath = (objectCode: string) => {
  const normalizedObjectCode = normalizePathPart(objectCode)
  if (!normalizedObjectCode) return ''
  return `/objects/${encodeURIComponent(normalizedObjectCode)}`
}

export const buildDynamicObjectDetailPath = (objectCode: string, recordId: unknown) => {
  const normalizedObjectCode = normalizePathPart(objectCode)
  const normalizedRecordId = normalizePathPart(recordId)
  if (!normalizedObjectCode || !normalizedRecordId) return ''
  return `${buildDynamicObjectListPath(normalizedObjectCode)}/${encodeURIComponent(normalizedRecordId)}`
}

export const buildDynamicObjectEditPath = (objectCode: string, recordId: unknown) => {
  const detailPath = buildDynamicObjectDetailPath(objectCode, recordId)
  if (!detailPath) return ''
  return `${detailPath}/edit`
}

export const pushDynamicObjectDetail = ({
  router,
  relationCode,
  record,
  targetObjectCode,
}: {
  router: Router
  relationCode: string
  record: any
  targetObjectCode?: string
}) => {
  const relatedCode = resolveDynamicDetailRelationObjectCode(relationCode, targetObjectCode)
  const path = buildDynamicObjectDetailPath(relatedCode, record?.id)
  if (!path) return
  router.push(path)
}

export const pushDynamicObjectEdit = ({
  router,
  relationCode,
  record,
  targetObjectCode,
}: {
  router: Router
  relationCode: string
  record: any
  targetObjectCode?: string
}) => {
  const relatedCode = resolveDynamicDetailRelationObjectCode(relationCode, targetObjectCode)
  const path = buildDynamicObjectEditPath(relatedCode, record?.id)
  if (!path) return
  router.push(path)
}
