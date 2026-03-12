<script setup lang="ts">
/**
 * InlineLineItemTabs - Renders L1 (line item) relations inline in the Details tab.
 *
 * Fetches related records via dynamicApi.getRelated() and displays them
 * in a read-only table with count badge and empty state.
 */
import { computed, onMounted, ref, watch } from 'vue'
import { dynamicApi } from '@/api/dynamic'
import RelatedObjectTable from './RelatedObjectTable.vue'
import ContextDrawer from './ContextDrawer.vue'
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
const editDrawerVisible = ref(false)
const relationTableVersions = ref<Record<string, number>>({})

const draftStatuses = new Set(['draft'])
const isDraftEditable = computed(() => {
  const rawStatus = String(props.data?.status || '').trim().toLowerCase()
  return !!props.parentId && draftStatuses.has(rawStatus)
})

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

const bumpRelationTable = (relationCode?: string) => {
  if (relationCode) {
    relationTableVersions.value = {
      ...relationTableVersions.value,
      [relationCode]: (relationTableVersions.value[relationCode] || 0) + 1
    }
    return
  }

  const nextVersions: Record<string, number> = { ...relationTableVersions.value }
  for (const relation of props.lineItemRelations) {
    nextVersions[relation.code] = (nextVersions[relation.code] || 0) + 1
  }
  relationTableVersions.value = nextVersions
}

const onRecordClick = (relationCode: string, record: any, targetObjectCode?: string) => {
  emit('recordClick', relationCode, record, targetObjectCode)
}

const onRecordEdit = (relationCode: string, record: any, targetObjectCode?: string) => {
  emit('recordEdit', relationCode, record, targetObjectCode)
}

const onRefresh = (relationCode: string) => {
  fetchRelationCounts()
  bumpRelationTable(relationCode)
  emit('refresh', relationCode)
}

const openEditDrawer = () => {
  if (!isDraftEditable.value) return
  editDrawerVisible.value = true
}

const handleDrawerSuccess = () => {
  editDrawerVisible.value = false
  fetchRelationCounts()
  bumpRelationTable()
  for (const relation of props.lineItemRelations) {
    emit('refresh', relation.code)
  }
}
</script>

<template>
  <div
    v-if="lineItemRelations.length > 0"
    class="inline-line-item-tabs"
  >
    <div
      v-if="isDraftEditable"
      class="line-item-actions"
    >
      <div class="line-item-actions__copy">
        <span class="line-item-actions__title">Line Items</span>
        <span class="line-item-actions__hint">Edit draft line items without leaving this page.</span>
      </div>
      <el-button
        type="primary"
        @click="openEditDrawer"
      >
        Edit Line Items
      </el-button>
    </div>

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
          :key="`${relation.code}-${relationTableVersions[relation.code] || 0}`"
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

    <ContextDrawer
      v-model="editDrawerVisible"
      :object-code="parentObjectCode"
      :record-id="parentId"
      title-override="Edit Line Items"
      @success="handleDrawerSuccess"
    />
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.inline-line-item-tabs {
  margin-top: 16px;

  .line-item-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
    padding: 14px 16px;
    border-radius: 12px;
    border: 1px solid rgba(37, 99, 235, 0.12);
    background: linear-gradient(135deg, rgba(239, 246, 255, 0.92), rgba(248, 250, 252, 0.98));
  }

  .line-item-actions__copy {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .line-item-actions__title {
    font-size: 13px;
    font-weight: 700;
    color: $text-main;
  }

  .line-item-actions__hint {
    font-size: 12px;
    color: $text-secondary;
  }

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
