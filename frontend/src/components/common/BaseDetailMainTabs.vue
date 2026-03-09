<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import RelatedObjectTable from './RelatedObjectTable.vue'
import ActivityTimeline from './ActivityTimeline.vue'
import BaseDetailSectionCard from './BaseDetailSectionCard.vue'
import BaseDetailAuditCard from './BaseDetailAuditCard.vue'
import type { FieldDefinition } from '@/types'

interface DetailFieldLike {
  prop: string
  label: string
  hidden?: boolean
  readonly?: boolean
  type?: string
  labelClass?: string
  valueClass?: string
}

interface DetailTabLike {
  id: string
  title: any
  fields: DetailFieldLike[]
}

interface DetailSectionLike {
  name: string
  title: any
  type?: string
  icon?: string
  position?: 'main' | 'sidebar'
  collapsible?: boolean
  fields: DetailFieldLike[]
  tabs?: DetailTabLike[]
}

interface AuditInfoLike {
  createdBy?: string
  createdAt?: string | Date
  updatedBy?: string
  updatedAt?: string | Date
}

interface ReverseRelationLike {
  code: string
  label: string
  displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  relatedObjectCode?: string
  reverseRelationField?: string
  reverseRelationModel?: string
  title?: string
  showCreate?: boolean
}

interface RelationGroupLike {
  key: string
  title: string
  relations: ReverseRelationLike[]
}

interface Props {
  activeMainTab: string
  mainSections: DetailSectionLike[]
  data: Record<string, any>
  editMode: boolean
  activeTabs: Record<string, string>
  sectionHeaderTestId?: string
  hasAuditInfo: boolean
  auditInfo?: AuditInfoLike | null
  objectCode?: string
  activityRecordId?: string
  hasActivityHistory: boolean
  visibleReverseRelations: ReverseRelationLike[]
  groupedReverseRelationSections: RelationGroupLike[]
  disableRelatedObjectFetch: boolean
  getSectionDisplayTitle: (section: DetailSectionLike) => string
  isSectionCollapsed: (section: DetailSectionLike) => boolean
  handleSectionHeaderClick: (section: DetailSectionLike) => void
  getSectionErrorTitle: (section: DetailSectionLike) => string
  getDisplayText: (value: any) => string
  getFieldValue: (field: DetailFieldLike) => any
  getEditFieldValue: (field: DetailFieldLike) => any
  toInlineEditRuntimeField: (field: DetailFieldLike) => Record<string, any>
  getFieldItemStyle: (field: DetailFieldLike) => Record<string, string>
  getSectionCanvasStyle: (section: DetailSectionLike) => Record<string, string>
  getFieldColStyle: (field: DetailFieldLike, section: DetailSectionLike) => Record<string, string>
  getFieldPlacementAttrs: (field: DetailFieldLike) => Record<string, string>
  updateFormData: (prop: string, value: any) => void
  isRelationGroupExpanded: (groupKey: string) => boolean
  toggleRelationGroup: (groupKey: string) => void
  onRelatedRecordClick: (relationCode: string, record: any, targetObjectCode?: string) => void
  onRelatedRecordEdit: (relationCode: string, record: any, targetObjectCode?: string) => void
  onRelatedRefresh: (relationCode: string) => void
}

const props = withDefaults(defineProps<Props>(), {
  sectionHeaderTestId: '',
  auditInfo: null,
  objectCode: '',
  activityRecordId: ''
})

const emit = defineEmits<{
  'update:activeMainTab': [value: string]
}>()

const { t } = useI18n()

const activeMainTabModel = computed({
  get: () => props.activeMainTab,
  set: (value: string) => emit('update:activeMainTab', value)
})
</script>

<template>
  <div class="main-column">
    <el-tabs
      v-model="activeMainTabModel"
      class="record-main-tabs"
    >
      <el-tab-pane
        :label="t('common.labels.details', '详情 (Details)')"
        name="details"
      >
        <div class="detail-sections">
          <el-empty
            v-if="mainSections.length === 0"
            :description="t('common.messages.noData')"
          />

          <template
            v-for="section in mainSections"
            :key="section.name"
          >
            <BaseDetailSectionCard
              :section="section"
              :data="data"
              :edit-mode="editMode"
              :active-tabs="activeTabs"
              :section-header-test-id="sectionHeaderTestId"
              :get-section-display-title="getSectionDisplayTitle"
              :is-section-collapsed="isSectionCollapsed"
              :handle-section-header-click="handleSectionHeaderClick"
              :get-section-error-title="getSectionErrorTitle"
              :get-display-text="getDisplayText"
              :get-field-value="getFieldValue"
              :get-edit-field-value="getEditFieldValue"
              :to-inline-edit-runtime-field="toInlineEditRuntimeField"
              :get-field-item-style="getFieldItemStyle"
              :get-section-canvas-style="getSectionCanvasStyle"
              :get-field-col-style="getFieldColStyle"
              :get-field-placement-attrs="getFieldPlacementAttrs"
              :update-form-data="updateFormData"
            >
              <template
                v-for="(_, slotName) in $slots"
                :key="slotName"
                #[slotName]="slotProps"
              >
                <slot
                  :name="slotName"
                  v-bind="slotProps"
                />
              </template>
            </BaseDetailSectionCard>
          </template>

          <slot
            name="after-sections"
            :data="data"
          />

          <BaseDetailAuditCard
            v-if="hasAuditInfo"
            :audit-info="auditInfo"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane
        :label="t('common.labels.relatedObjects', '相关 (Related)')"
        name="related"
      >
        <div
          v-if="visibleReverseRelations.length > 0"
          class="related-objects-section"
        >
          <div class="related-objects-body">
            <div class="related-groups-collapse">
              <section
                v-for="group in groupedReverseRelationSections"
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
                      :parent-object-code="objectCode || ''"
                      :parent-id="data.id || data.code"
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
                      :disable-data-fetch="disableRelatedObjectFetch"
                      @record-click="(record) => onRelatedRecordClick(relation.code, record, relation.relatedObjectCode)"
                      @record-edit="(record) => onRelatedRecordEdit(relation.code, record, relation.relatedObjectCode)"
                      @refresh="onRelatedRefresh(relation.code)"
                    />
                  </div>
                </div>
              </section>
            </div>
          </div>
        </div>
        <el-empty
          v-else
          :description="t('common.messages.noData')"
        />
      </el-tab-pane>

      <el-tab-pane
        v-if="hasActivityHistory"
        :label="t('common.labels.changeHistory')"
        name="history"
      >
        <div class="record-history-section">
          <ActivityTimeline
            :object-code="objectCode || ''"
            :record-id="activityRecordId"
            size="normal"
          />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.detail-sections {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.record-history-section {
  padding-top: 8px;
}

.related-objects-section {
  margin-top: $spacing-md;
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-sm;
  overflow: hidden;
  border: 1px solid $border-light;

  .related-objects-body {
    .related-groups-collapse {
      border-top: none;
      border-bottom: none;
    }

    .related-group-item {
      border-bottom: 1px solid #eef2f7;

      &:last-child {
        border-bottom: none;
      }
    }

    .related-group-header {
      width: 100%;
      height: 48px;
      padding: 0 16px;
      background: #fbfcff;
      border: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      cursor: pointer;
    }

    .related-group-arrow {
      color: $text-secondary;
      transition: transform 0.2s ease;
    }

    .related-group-item.is-active .related-group-arrow {
      transform: rotate(180deg);
    }

    .related-group-content {
      padding-bottom: 0;
    }

    .related-group-title {
      display: inline-flex;
      align-items: center;
      gap: 8px;

      .group-name {
        font-size: 13px;
        font-weight: 600;
        color: $text-main;
      }
    }

    .related-objects-list {
      display: flex;
      flex-direction: column;
      gap: 0;

      :deep(.related-object-table) {
        border-radius: 0;
        box-shadow: none;

        &:not(:last-child) {
          border-bottom: 1px solid #ebeef5;
        }
      }
    }
  }
}

@media (max-width: 768px) {
  .related-objects-section {
    .related-objects-body {
      :deep(.related-object-table) {
        .table-header {
          flex-direction: column;
          gap: 12px;
          align-items: flex-start;
          padding: 12px 16px;

          .header-actions {
            width: 100%;
            justify-content: flex-start;
          }
        }

        .table-pagination {
          :deep(.el-pagination) {
            flex-wrap: wrap;
            justify-content: center;

            .el-pagination__sizes,
            .el-pagination__jump {
              display: none;
            }
          }
        }
      }
    }
  }
}
</style>
