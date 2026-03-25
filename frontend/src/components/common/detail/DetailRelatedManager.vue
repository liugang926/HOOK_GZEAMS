<template>
  <div
    v-if="groupedRelations.length > 0"
    class="related-objects-section"
  >
    <div class="related-objects-body">
      <div class="related-groups-collapse">
        <section
          v-for="group in groupedRelations"
          :key="group.key"
          :class="['related-group-item', { 'is-active': isRelationGroupExpanded(group.key) }]"
        >
          <button
            type="button"
            class="related-group-header"
            :aria-expanded="isRelationGroupExpanded(group.key)"
            :aria-controls="`related-group-panel-${group.key}`"
            @click="toggleRelationGroup(group.key)"
          >
            <div class="related-group-title">
              <span class="group-name">{{ group.title }}</span>
              <el-tag
                size="small"
                effect="plain"
                type="info"
                class="group-count"
              >
                {{ group.relations.length }}
              </el-tag>
            </div>
            <el-icon class="related-group-arrow">
              <ArrowDown />
            </el-icon>
          </button>
          <div
            v-show="isRelationGroupExpanded(group.key)"
            :id="`related-group-panel-${group.key}`"
            class="related-group-content"
          >
            <div class="related-objects-list">
              <RelatedObjectTable
                v-for="relation in group.relations"
                :key="relation.code"
                :parent-object-code="parentObjectCode || ''"
                :parent-id="String(parentId)"
                :target-object-code="relation.relatedObjectCode || ''"
                :field="{
                  code: relation.code,
                  label: relation.label,
                  name: relation.label,
                  fieldType: 'reference',
                  relationDisplayMode: relation.displayMode,
                  relationDisplayModeDisplay: relation.displayMode,
                  targetObjectCode: relation.relatedObjectCode,
                  reverseRelationModel: relation.reverseRelationModel,
                  reverseRelationField: relation.reverseRelationField
                } as unknown as FieldDefinition"
                :mode="relation.displayMode"
                :title="relation.title"
                :show-create="relation.showCreate"
                @record-click="(record) => handleRecordClick(relation.code, record, relation.relatedObjectCode)"
                @record-edit="(record) => handleRecordEdit(relation.code, record, relation.relatedObjectCode)"
                @refresh="$emit('related-refresh', relation.code)"
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
  <el-empty
    v-else
    :description="$t('common.messages.noData')"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'
import RelatedObjectTable from '../RelatedObjectTable.vue'
import type { FieldDefinition } from '@/types'
import { useRelationGroupExpansion } from '@/composables/useRelationGroupExpansion'
import type { RelationGroupSection } from '@/platform/reference/relationGrouping'
import type { ReverseRelationField } from '../BaseDetailPage.vue'

type AnyRecord = Record<string, unknown>
type RelatedRelationGroup = RelationGroupSection<ReverseRelationField>

const props = defineProps<{
  groupedRelations: RelatedRelationGroup[]
  parentObjectCode?: string
  parentId: string | number
  relationGroupScopeId?: string
}>()

const emit = defineEmits<{
  (e: 'related-record-click', relationCode: string, record: AnyRecord, targetObjectCode?: string): void
  (e: 'related-record-edit', relationCode: string, record: AnyRecord, targetObjectCode?: string): void
  (e: 'related-refresh', relationCode: string): void
}>()

const relationGroupItems = computed(() => {
  return props.groupedRelations.map((group) => ({
    key: group.key,
    defaultExpanded: group.defaultExpanded
  }))
})

const relationGroupExpansion = useRelationGroupExpansion({
  groups: () => relationGroupItems.value,
  objectCode: () => String(props.parentObjectCode || ''),
  scopeId: () => String(props.relationGroupScopeId || props.parentId || '')
})

const isRelationGroupExpanded = relationGroupExpansion.isExpanded
const toggleRelationGroup = relationGroupExpansion.toggle

const handleRecordClick = (relationCode: string, record: AnyRecord, targetObjectCode?: string) => {
  emit('related-record-click', relationCode, record, targetObjectCode)
}

const handleRecordEdit = (relationCode: string, record: AnyRecord, targetObjectCode?: string) => {
  emit('related-record-edit', relationCode, record, targetObjectCode)
}
</script>

