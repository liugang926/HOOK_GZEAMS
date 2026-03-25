<template>
  <aside class="detail-panel detail-panel--aside">
    <ObjectWorkspaceInfoCard
      variant="detail"
      :eyebrow="summaryLabel"
      :title="objectDisplayName"
      :rows="infoRows"
    />

    <ObjectWorkspaceInfoCard
      variant="detail"
      :eyebrow="tipsLabel"
      :tips="tips"
      soft
    />
  </aside>
</template>

<script setup lang="ts">
import ObjectWorkspaceInfoCard from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'

interface Props {
  summaryLabel: string
  tipsLabel: string
  objectDisplayName: string
  infoRows: ObjectWorkspaceInfoRow[]
  tips: string[]
}

defineProps<Props>()
</script>
