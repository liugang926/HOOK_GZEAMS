import type { Router } from 'vue-router'

const normalizePathPart = (value: unknown) => String(value || '').trim()

export const resolveDynamicListRowId = (row: any) => {
  return normalizePathPart(row?.id || row?._id)
}

export const buildDynamicListObjectPath = (objectCode: string) => {
  const normalizedObjectCode = normalizePathPart(objectCode)
  if (!normalizedObjectCode) return ''
  return `/objects/${encodeURIComponent(normalizedObjectCode)}`
}

export const buildDynamicListCreatePath = (objectCode: string) => {
  const listPath = buildDynamicListObjectPath(objectCode)
  if (!listPath) return ''
  return `${listPath}/create`
}

export const buildDynamicListDetailPath = ({
  objectCode,
  row,
}: {
  objectCode: string
  row: any
}) => {
  const listPath = buildDynamicListObjectPath(objectCode)
  const recordId = resolveDynamicListRowId(row)
  if (!listPath || !recordId) return ''
  return `${listPath}/${encodeURIComponent(recordId)}`
}

export const buildDynamicListEditPath = ({
  objectCode,
  row,
}: {
  objectCode: string
  row: any
}) => {
  const detailPath = buildDynamicListDetailPath({ objectCode, row })
  if (!detailPath) return ''
  return `${detailPath}/edit`
}

export const buildDynamicListLayoutSettingsRoute = ({
  objectCode,
  objectName,
}: {
  objectCode: string
  objectName: string
}) => ({
  path: '/system/page-layouts',
  query: {
    objectCode,
    objectName,
  },
})

const pushIfPresent = (router: Router, pathOrRoute: string | Record<string, any>) => {
  if (!pathOrRoute || (typeof pathOrRoute === 'string' && !pathOrRoute.trim())) {
    return
  }
  router.push(pathOrRoute as any)
}

export const pushDynamicListView = ({
  router,
  objectCode,
  row,
}: {
  router: Router
  objectCode: string
  row: any
}) => {
  pushIfPresent(router, buildDynamicListDetailPath({ objectCode, row }))
}

export const pushDynamicListCreate = ({
  router,
  objectCode,
}: {
  router: Router
  objectCode: string
}) => {
  pushIfPresent(router, buildDynamicListCreatePath(objectCode))
}

export const pushDynamicListEdit = ({
  router,
  objectCode,
  row,
}: {
  router: Router
  objectCode: string
  row: any
}) => {
  pushIfPresent(router, buildDynamicListEditPath({ objectCode, row }))
}

export const pushDynamicListLayoutSettings = ({
  router,
  objectCode,
  objectName,
}: {
  router: Router
  objectCode: string
  objectName: string
}) => {
  pushIfPresent(router, buildDynamicListLayoutSettingsRoute({ objectCode, objectName }))
}
