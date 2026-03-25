import type { TableColumn } from '@/types/common'

export const reorderBaseListColumnsAfterDrag = ({
  activeColumns,
  visibleColumns,
  oldIndex,
  newIndex,
  selectable,
  showIndex,
}: {
  activeColumns: TableColumn[]
  visibleColumns: TableColumn[]
  oldIndex: number
  newIndex: number
  selectable: boolean
  showIndex: boolean
}) => {
  let offset = 0
  if (selectable) offset++
  if (showIndex) offset++

  const visibleOldIndex = oldIndex - offset
  const visibleNewIndex = newIndex - offset

  if (visibleOldIndex < 0 || visibleNewIndex < 0) return null
  if (visibleOldIndex >= visibleColumns.length || visibleNewIndex >= visibleColumns.length) return null

  const reorderedVisibleColumns = [...visibleColumns]
  const movedColumn = reorderedVisibleColumns.splice(visibleOldIndex, 1)[0]
  reorderedVisibleColumns.splice(visibleNewIndex, 0, movedColumn)

  const hiddenColumns = activeColumns.filter((column) => column.visible === false)
  return [...reorderedVisibleColumns, ...hiddenColumns]
}

export const applyBaseListColumnWidth = (
  columns: TableColumn[],
  prop: string,
  width: number,
) => {
  const targetIndex = columns.findIndex((column) => column.prop === prop)
  if (targetIndex === -1) return columns

  return columns.map((column, index) => {
    if (index !== targetIndex) return column
    return {
      ...column,
      width,
    }
  })
}
