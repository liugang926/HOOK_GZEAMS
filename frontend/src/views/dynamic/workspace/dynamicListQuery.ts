export const buildDynamicListRequestParams = ({
  params,
  routeFilters,
  unifiedSearchFieldOptions,
}: {
  params?: Record<string, any>
  routeFilters?: Record<string, any>
  unifiedSearchFieldOptions: Array<{ label?: string; value: string }>
}) => {
  const nextParams = { ...(routeFilters || {}), ...(params || {}) }
  const keyword = String(nextParams.__unifiedKeyword || '').trim()
  const selectedField = String(nextParams.__unifiedField || '__all').trim()
  const visibleFieldCodeSet = new Set(
    (Array.isArray(nextParams.__visibleFieldCodes) ? nextParams.__visibleFieldCodes : [])
      .map((item: any) => String(item || '').trim())
      .filter(Boolean),
  )
  const constrainedFieldCodes = unifiedSearchFieldOptions
    .map((item) => String(item?.value || '').trim())
    .filter((value) => !visibleFieldCodeSet.size || visibleFieldCodeSet.has(value))

  delete nextParams.__unifiedKeyword
  delete nextParams.__unifiedField
  delete nextParams.__unifiedSearch
  delete nextParams.__visibleFieldCodes
  delete nextParams.searchFields
  delete nextParams.search_fields

  if (keyword) {
    if (selectedField && selectedField !== '__all') {
      nextParams[selectedField] = keyword
    } else if (constrainedFieldCodes.length) {
      nextParams.search = keyword
      nextParams.searchFields = constrainedFieldCodes.join(',')
    } else {
      nextParams.search = keyword
    }
  }

  return nextParams
}
