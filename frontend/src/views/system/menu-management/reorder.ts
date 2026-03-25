import type { MenuManagementItem } from '@/api/system'
import { getItemIdentity, normalizeOrder, type EditableCategory } from './shared'

export const reorderByPageMove = <T>(
  collection: T[],
  visibleItems: T[],
  oldIndex: number,
  newIndex: number,
  identity: (item: T) => string,
) => {
  if (oldIndex === newIndex) return collection
  const movedVisible = visibleItems[oldIndex]
  const targetVisible = visibleItems[newIndex]
  if (!movedVisible || !targetVisible) return collection

  const next = [...collection]
  const movedCollectionIndex = next.findIndex((item) => identity(item) === identity(movedVisible))
  if (movedCollectionIndex < 0) return collection

  const [movedItem] = next.splice(movedCollectionIndex, 1)
  const targetCollectionIndex = next.findIndex((item) => identity(item) === identity(targetVisible))
  if (targetCollectionIndex < 0) {
    next.push(movedItem)
    return next
  }

  const insertIndex = oldIndex < newIndex ? targetCollectionIndex + 1 : targetCollectionIndex
  next.splice(insertIndex, 0, movedItem)
  return next
}

export const moveCategoryList = (orderedCategories: EditableCategory[], originalCode: string, offset: -1 | 1) => {
  const current = [...orderedCategories]
  const index = current.findIndex((item) => item.originalCode === originalCode)
  const targetIndex = index + offset
  if (index < 0 || targetIndex < 0 || targetIndex >= current.length) return orderedCategories
  ;[current[index], current[targetIndex]] = [current[targetIndex], current[index]]
  normalizeOrder(current)
  return current
}

export const syncItemCollections = (
  sourceItems: MenuManagementItem[],
  updates: Map<string, { groupCode: string; order: number }>,
) => sourceItems.map((item) => {
  const update = updates.get(getItemIdentity(item))
  return update ? { ...item, ...update } : item
})

export const applyGroupOrder = (
  category: Pick<EditableCategory, 'code'>,
  groupItems: MenuManagementItem[],
  updates: Map<string, { groupCode: string; order: number }>,
) => {
  groupItems.forEach((item, index) => {
    updates.set(getItemIdentity(item), {
      groupCode: category.code.trim(),
      order: (index + 1) * 10,
    })
  })
}

export const buildGroupCodeMap = (categories: EditableCategory[]) => {
  const codeMap = new Map<string, string>()
  for (const category of categories) {
    codeMap.set(category.originalCode, category.code.trim())
  }
  return codeMap
}

export { normalizeOrder }
