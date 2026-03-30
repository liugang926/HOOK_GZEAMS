import { ref, type ComputedRef } from 'vue'
import type { Router } from 'vue-router'

import { assetApi } from '@/api/assets'
import type { PortalAssetRecord } from '@/types/portal'

import { getPortalAssetDetailPath } from './portalAssetModel'

type UserIdRef = ComputedRef<string | number | undefined>

export const usePortalAssets = (
  userId: UserIdRef,
  router: Router,
) => {
  const loadingAssets = ref(false)
  const myAssets = ref<PortalAssetRecord[]>([])
  const assetSearch = ref('')
  const assetStatusFilter = ref('')
  const assetPage = ref(1)
  const assetPageSize = ref(15)
  const assetTotal = ref(0)
  const myAssetCount = ref(0)

  const loadMyAssets = async () => {
    loadingAssets.value = true
    try {
      const response: any = await assetApi.list({
        page: assetPage.value,
        page_size: assetPageSize.value,
        search: assetSearch.value || undefined,
        status: assetStatusFilter.value || undefined,
        responsible_user_id: userId.value,
      })
      myAssets.value = response?.results ?? response?.items ?? []
      assetTotal.value = response?.count ?? response?.total ?? 0
    } finally {
      loadingAssets.value = false
    }
  }

  const refreshMyAssetCount = async () => {
    const response: any = await assetApi.list({
      page: 1,
      page_size: 1,
      responsible_user_id: userId.value,
    })
    myAssetCount.value = response?.count ?? response?.total ?? 0
  }

  const goToAsset = (row: PortalAssetRecord) => router.push(getPortalAssetDetailPath(row.id))

  return {
    assetPage,
    assetPageSize,
    assetSearch,
    assetStatusFilter,
    assetTotal,
    goToAsset,
    loadingAssets,
    loadMyAssets,
    myAssetCount,
    myAssets,
    refreshMyAssetCount,
  }
}
