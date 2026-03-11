<script setup lang="ts">
/**
 * InlineLineItemTabs - Renders L1 (line item) relations inline in the Details tab.
 *
 * Fetches related records via dynamicApi.getRelated() and displays them
 * in a read-only table with count badge and empty state.
 */
import { ref, watch, onMounted } from 'vue'
import { dynamicApi } from '@/api/dynamic'
import RelatedObjectTable from './RelatedObjectTable.vue'
import type { FieldDefinition } from '@/types'

interface LineItemRelation {
  code: string
  label: string
  displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  displayTier?: 'L1' | 'L2' | 'L3'
  relatedObjectCode?: string
  reverseRelationField?: string
  title?: string
  showCreate?: boolean
}

interface Props {
  lineItemRelations: LineItemRelation[]
  parentObjectCode: string
  parentId: string
  data: Record<string, any>
  editMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  editMode: false,
})

const emit = defineEmits<{
  recordClick: [relationCode: string, record: any, targetObjectCode?: string]
  recordEdit: [relationCode: string, record: any, targetObjectCode?: string]
  refresh: [relationCode: string]
}>()

const activeLineItemTab = ref('')

// Set first tab as active on mount
onMounted(() => {
  if (props.lineItemRelations.length > 0) {
    activeLineItemTab.value = props.lineItemRelations[0].code
  }
})

watch(
  () => props.lineItemRelations,
  (newRelations) => {
    if (newRelations.length > 0 && !newRelations.find(r => r.code === activeLineItemTab.value)) {
      activeLineItemTab.value = newRelations[0].code
    }
  },
  { immediate: true }
)

// Counts for tab badges
const relationCounts = ref<Record<string, number>>({})

const fetchRelationCounts = async () => {
  if (!props.parentObjectCode || !props.parentId) return
  try {
    const response = await dynamicApi.getRelationCounts(props.parentObjectCode, props.parentId)
    const counts = (response as any)?.data?.counts || (response as any)?.counts || {}
    relationCounts.value = counts
  } catch {
    // Silently ignore — counts are cosmetic
  }
}

onMounted(fetchRelationCounts)
watch(() => props.parentId, fetchRelationCounts)

const getTabLabel = (relation: LineItemRelation) => {
  const count = relationCounts.value[relation.code]
  return count !== undefined ? `${relation.label} (${count})` : relation.label
}

const onRecordClick = (relationCode: string, record: any, targetObjectCode?: string) => {
  emit('recordClick', relationCode, record, targetObjectCode)
}

const onRecordEdit = (relationCode: string, record: any, targetObjectCode?: string) => {
  emit('recordEdit', relationCode, record, targetObjectCode)
}

const onRefresh = (relationCode: string) => {
  fetchRelationCounts()
  emit('refresh', relationCode)
}
</script>

<template>
  <div
    v-if="lineItemRelations.length > 0"
    class="inline-line-item-tabs"
  >
    <el-tabs
      v-model="activeLineItemTab"
      type="border-card"
      class="line-item-tabs"
    >
      <el-tab-pane
        v-for="relation in lineItemRelations"
        :key="relation.code"
        :name="relation.code"
        :label="getTabLabel(relation)"
      >
        <RelatedObjectTable
          :parent-object-code="parentObjectCode"
          :parent-id="parentId"
          :target-object-code="relation.relatedObjectCode || ''"
          :field="{
            code: relation.code,
            label: relation.label,
            name: relation.label,
            fieldType: 'reference',
            relationDisplayMode: relation.displayMode,
            relationDisplayModeDisplay: relation.displayMode,
            targetObjectCode: relation.relatedObjectCode,
            reverseRelationField: relation.reverseRelationField
          } as unknown as FieldDefinition"
          :mode="relation.displayMode"
          :title="relation.title || relation.label"
          :show-create="relation.showCreate && editMode"
          @record-click="(record) => onRecordClick(relation.code, record, relation.relatedObjectCode)"
          @record-edit="(record) => onRecordEdit(relation.code, record, relation.relatedObjectCode)"
          @refresh="onRefresh(relation.code)"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.inline-line-item-tabs {
  margin-top: 16px;

  .line-item-tabs {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
    border: 1px solid rgba(148, 163, 184, 0.16);
    background: #fff;

    :deep(.el-tabs__header) {
      background: rgba(248, 250, 252, 0.9);
      margin-bottom: 0;
      border-bottom: 1px solid rgba(148, 163, 184, 0.12);
    }

    :deep(.el-tabs__item) {
      font-weight: 600;
      font-size: 13px;
      color: $text-secondary;

      &.is-active {
        color: #1d4ed8;
      }
    }

    :deep(.el-tabs__content) {
      padding: 0;
    }
  }
}
</style>
