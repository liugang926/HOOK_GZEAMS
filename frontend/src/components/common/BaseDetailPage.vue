<!--
  BaseDetailPage Component

  A reusable detail page component that provides:
  - Section-based data display
  - Audit trail (created/updated info)
  - Edit/Back/Delete actions
  - Slot-based customization
  - Loading and error states
  - System Audit information
-->

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseDetailSectionCard from './BaseDetailSectionCard.vue'
import BaseDetailHeader from './BaseDetailHeader.vue'
import BaseDetailMainTabs from './BaseDetailMainTabs.vue'
import { useBaseDetailPageLayout } from './useBaseDetailPageLayout'
import { useBaseDetailPageHistory } from './useBaseDetailPageHistory'
import { useBaseDetailPageRelations } from './useBaseDetailPageRelations'
import { useBaseDetailPageActions } from './useBaseDetailPageActions'
import { useBaseDetailPageSections } from './useBaseDetailPageSections'
import { useBaseDetailPageFields } from './useBaseDetailPageFields'

export interface DetailField {
  prop: string
  label: string
  editorType?: string
  type?:
    | 'text'
    | 'date'
    | 'datetime'
    | 'time'
    | 'daterange'
    | 'year'
    | 'month'
    | 'number'
    | 'currency'
    | 'percent'
    | 'boolean'
    | 'switch'
    | 'checkbox'
    | 'tag'
    | 'slot'
    | 'link'
    | 'image'
    | 'qr_code'
    | 'barcode'
    | 'color'
    | 'rate'
    | 'file'
    | 'attachment'
    | 'rich_text'
    | 'sub_table'
    | 'json'
    | 'object'
    | string
  options?: { label: string; value: any; color?: string }[]
  dateFormat?: string
  precision?: number
  currency?: string
  tagType?: Record<string, string> | ((value: any, row?: any) => string)
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  span?: number
  minHeight?: number
  href?: string
  hidden?: boolean
  readonly?: boolean
  labelClass?: string
  valueClass?: string
  referenceObject?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  componentProps?: Record<string, any>
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas?: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

export interface DetailTab {
  id: string
  title: any
  fields: DetailField[]
}

export interface DetailSection {
  name: string
  title: any
  type?: string
  position?: 'main' | 'sidebar'
  fields: DetailField[]
  tabs?: DetailTab[]
  icon?: string
  collapsible?: boolean
  collapsed?: boolean
}

export interface AuditInfo {
  createdBy?: string
  createdAt?: string | Date
  updatedBy?: string
  updatedAt?: string | Date
}

export interface ReverseRelationField {
  code: string
  label: string
  displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  relatedObjectCode?: string
  reverseRelationField?: string
  reverseRelationModel?: string
  title?: string
  showCreate?: boolean
  sortOrder?: number
  groupKey?: string
  groupName?: string
  groupOrder?: number
  defaultExpanded?: boolean
}

interface Props {
  title?: string
  sections: DetailSection[]
  data: Record<string, any>
  loading?: boolean
  auditInfo?: AuditInfo | null
  showEdit?: boolean
  showDelete?: boolean
  showBack?: boolean
  editText?: string
  deleteText?: string
  backText?: string
  extraActions?: Array<{
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger' | string
    icon?: string
    action: () => void | Promise<void>
  }>
  deleteConfirmMessage?: string
  fieldSpan?: number
  objectCode?: string
  objectIcon?: string
  objectName?: string
  reverseRelations?: ReverseRelationField[]
  showRelatedObjects?: boolean
  resolveRuntimeRelations?: boolean
  disableRelatedObjectFetch?: boolean
  showActivityHistory?: boolean
  relationGroupScopeId?: string
  editMode?: boolean
  formData?: Record<string, any>
  formRules?: Record<string, any>
  sectionHeaderTestId?: string
}

interface Emits {
  (e: 'edit'): void
  (e: 'delete'): void
  (e: 'back'): void
  (e: 'section-click', sectionName: string): void
  (e: 'related-record-click', relationCode: string, record: any, targetObjectCode?: string): void
  (e: 'related-record-edit', relationCode: string, record: any, targetObjectCode?: string): void
  (e: 'related-refresh', relationCode: string): void
  (e: 'save', data: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'update:formData', data: Record<string, any>): void
}

const props = withDefaults(defineProps<Props>(), {
  auditInfo: null,
  showEdit: true,
  showDelete: true,
  showBack: true,
  editText: undefined,
  deleteText: undefined,
  backText: undefined,
  deleteConfirmMessage: undefined,
  fieldSpan: 12,
  extraActions: () => [],
  reverseRelations: () => [],
  showRelatedObjects: true,
  showActivityHistory: true,
  resolveRuntimeRelations: true,
  disableRelatedObjectFetch: false,
  editMode: false,
  formData: () => ({}),
  formRules: () => ({}),
  sectionHeaderTestId: ''
})

const emit = defineEmits<Emits>()
const formRef = ref<any>(null)
const runtimeRelations = ref<ReverseRelationField[]>([])
const { locale } = useI18n()

const {
  hasAuditInfo,
  availableActions,
  handleBack,
  validateForm,
  updateFormData
} = useBaseDetailPageActions({
  props,
  emit,
  formRef
})

const {
  activeTabs,
  activeMainTab,
  getSectionDisplayTitle,
  getSectionErrorTitle,
  toggleSection,
  handleSectionHeaderClick,
  isSectionCollapsed
} = useBaseDetailPageSections({
  sections: computed(() => props.sections),
  emitSectionClick: (sectionName) => emit('section-click', sectionName)
})

const { mainSections, sidebarSections } = useBaseDetailPageLayout({
  sections: () => props.sections
})

const { activityRecordId, hasActivityHistory } = useBaseDetailPageHistory({
  props
})

const {
  visibleReverseRelations,
  groupedReverseRelationSections,
  isRelationGroupExpanded,
  toggleRelationGroup,
  fetchRuntimeRelations
} = useBaseDetailPageRelations({
  props,
  runtimeRelations
})

const {
  getDisplayText,
  editDrawerProxyFields,
  getFieldValue,
  getEditFieldValue,
  toInlineEditRuntimeField,
  getFieldItemStyle,
  getSectionCanvasStyle,
  getFieldColStyle,
  getFieldPlacementAttrs
} = useBaseDetailPageFields({
  props,
  activeTabs
})

watch(
  () => [props.objectCode, props.showRelatedObjects, props.resolveRuntimeRelations],
  () => {
    fetchRuntimeRelations()
  },
  { immediate: true }
)

watch(
  () => locale.value,
  () => {
    if (!props.showRelatedObjects || !props.resolveRuntimeRelations) return
    fetchRuntimeRelations()
  }
)

defineExpose({
  toggleSection,
  isSectionCollapsed,
  validateForm
})
</script>

<template>
  <div class="base-detail-page">
    <el-skeleton
      v-if="loading"
      animated
      class="detail-content loading-skeleton"
    >
      <template #template>
        <div
          class="page-header record-profile-header"
          style="border-bottom: 1px solid var(--el-border-color-light); padding-bottom: 16px;"
        >
          <div class="header-left">
            <el-skeleton-item
              variant="circle"
              style="width: 48px; height: 48px; margin-right: 16px"
            />
            <div
              class="profile-text"
              style="display: flex; flex-direction: column; justify-content: center;"
            >
              <el-skeleton-item
                variant="text"
                style="width: 80px; margin-bottom: 6px"
              />
              <el-skeleton-item
                variant="h1"
                style="width: 15vw; height: 24px"
              />
            </div>
          </div>
          <div class="header-right">
            <el-skeleton-item
              variant="button"
              style="width: 80px; margin-right: 12px; height: 32px"
            />
            <el-skeleton-item
              variant="button"
              style="width: 80px; height: 32px"
            />
          </div>
        </div>

        <div
          class="detail-layout-container"
          :class="{ 'has-sidebar': sidebarSections.length > 0 }"
        >
          <div class="main-column detail-sections">
            <template v-if="mainSections.length > 0">
              <div
                v-for="section in mainSections"
                :key="section.name"
                class="detail-section-skeleton"
              >
                <div class="section-header">
                  <el-skeleton-item
                    variant="h3"
                    style="width: 120px; height: 20px"
                  />
                </div>
                <div class="section-content">
                  <div
                    class="detail-canvas-grid"
                    :style="getSectionCanvasStyle(section)"
                  >
                    <div
                      v-for="field in (section.type === 'tab' ? (section.tabs?.[0]?.fields || []) : section.fields)"
                      :key="field.prop"
                      class="field-item"
                      :style="getFieldColStyle(field, section)"
                    >
                      <el-skeleton-item
                        variant="text"
                        style="width: 30%; margin-bottom: 8px"
                      />
                      <el-skeleton-item
                        variant="rect"
                        style="width: 80%; height: 20px"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="detail-section-skeleton">
                <div class="section-header">
                  <el-skeleton-item
                    variant="h3"
                    style="width: 120px; height: 20px"
                  />
                </div>
                <div class="section-content">
                  <div
                    class="detail-canvas-grid"
                    style="--detail-section-columns: 2;"
                  >
                    <div
                      v-for="i in 4"
                      :key="i"
                      class="field-item"
                    >
                      <el-skeleton-item
                        variant="text"
                        style="width: 30%; margin-bottom: 8px"
                      />
                      <el-skeleton-item
                        variant="rect"
                        style="width: 80%; height: 20px"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div
            v-if="sidebarSections.length > 0"
            class="sidebar-column"
          >
            <div
              v-for="section in sidebarSections"
              :key="section.name"
              class="detail-section-skeleton sidebar-section-block"
            >
              <div class="section-header">
                <el-skeleton-item
                  variant="h3"
                  style="width: 100px; height: 20px"
                />
              </div>
              <div class="section-content">
                <div class="detail-canvas-grid sidebar-canvas-grid">
                  <div
                    v-for="field in section.fields"
                    :key="field.prop"
                    class="field-item"
                    :style="getFieldColStyle(field, section)"
                  >
                    <el-skeleton-item
                      variant="text"
                      style="width: 40%; margin-bottom: 8px"
                    />
                    <el-skeleton-item
                      variant="rect"
                      style="width: 100%; height: 20px"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </el-skeleton>

    <div
      v-else
      class="detail-content"
    >
      <BaseDetailHeader
        :title="title"
        :object-code="objectCode"
        :object-icon="objectIcon"
        :object-name="objectName"
        :show-back="showBack"
        :back-text="backText"
        :has-audit-info="hasAuditInfo"
        :audit-info="auditInfo"
        :data="data"
        :available-actions="availableActions"
        :on-back="handleBack"
      >
        <template
          v-if="$slots['action-bar']"
          #action-bar="slotProps"
        >
          <slot
            name="action-bar"
            v-bind="slotProps"
          />
        </template>
      </BaseDetailHeader>

      <div
        v-if="editMode"
        class="el-drawer open drawer-compat-proxy"
      >
        <div class="drawer-compat-labels">
          <span
            v-for="field in editDrawerProxyFields"
            :key="`proxy-${field.prop}`"
            class="el-form-item__label"
          >
            {{ field.label }}
          </span>
        </div>
      </div>

      <slot
        name="header-extra"
        :data="data"
      />

      <el-form
        ref="formRef"
        class="dynamic-form"
        :model="formData"
        :rules="formRules"
        @submit.prevent
      >
        <div
          class="detail-layout-container"
          :class="{ 'has-sidebar': sidebarSections.length > 0 }"
        >
          <BaseDetailMainTabs
            :active-main-tab="activeMainTab"
            :main-sections="mainSections"
            :data="data"
            :edit-mode="editMode"
            :active-tabs="activeTabs"
            :section-header-test-id="sectionHeaderTestId"
            :has-audit-info="hasAuditInfo"
            :audit-info="auditInfo"
            :object-code="objectCode"
            :activity-record-id="activityRecordId"
            :has-activity-history="hasActivityHistory"
            :visible-reverse-relations="visibleReverseRelations"
            :grouped-reverse-relation-sections="groupedReverseRelationSections"
            :disable-related-object-fetch="disableRelatedObjectFetch"
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
            :is-relation-group-expanded="isRelationGroupExpanded"
            :toggle-relation-group="toggleRelationGroup"
            :on-related-record-click="(relationCode, record, targetObjectCode) => $emit('related-record-click', relationCode, record, targetObjectCode)"
            :on-related-record-edit="(relationCode, record, targetObjectCode) => $emit('related-record-edit', relationCode, record, targetObjectCode)"
            :on-related-refresh="(relationCode) => $emit('related-refresh', relationCode)"
            @update:active-main-tab="activeMainTab = $event"
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
          </BaseDetailMainTabs>

          <div
            v-if="sidebarSections.length > 0"
            class="sidebar-column"
          >
            <template
              v-for="section in sidebarSections"
              :key="section.name"
            >
              <BaseDetailSectionCard
                :section="section"
                :data="data"
                :edit-mode="editMode"
                :active-tabs="activeTabs"
                :section-header-test-id="sectionHeaderTestId"
                :sidebar="true"
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
          </div>
        </div>
      </el-form>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.base-detail-page {
  padding: $spacing-lg;
  background-color: $bg-body;
  min-height: 100%;
  --detail-label-width: var(--gzeams-detail-label-width, 120px);
  --detail-field-gap: var(--gzeams-detail-field-gap, 16px);
}

.loading-container {
  padding: 40px;
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-md;
}

.detail-content {
  .error-description {
    margin-bottom: 8px;
    word-break: break-word;
  }

  .error-actions {
    margin-top: 8px;
  }

  .drawer-compat-proxy {
    position: absolute !important;
    top: 0;
    left: 0;
    width: 1px !important;
    height: 1px !important;
    overflow: hidden !important;
    pointer-events: none !important;
    opacity: 1 !important;
    box-shadow: none !important;
    background: transparent !important;
  }

  .drawer-compat-labels {
    display: flex;
    flex-direction: column;
  }

  .detail-layout-container {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
    width: 100%;

    &.has-sidebar {
      flex-direction: row;
      align-items: flex-start;

      .main-column {
        flex: 1;
        min-width: 0;
      }

      .sidebar-column {
        width: 320px;
        flex-shrink: 0;
        display: flex;
        flex-direction: column;
        gap: $spacing-md;
      }
    }
  }
}

.detail-section-skeleton {
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-sm;
  overflow: hidden;
  border: 1px solid $border-light;

  .section-header {
    display: flex;
    align-items: center;
    padding: 14px $spacing-lg;
    background-color: #f8fafc;
    border-bottom: 1px solid $border-light;
  }

  .section-content {
    padding: 20px;

    .detail-canvas-grid {
      display: grid;
      grid-template-columns: repeat(var(--detail-section-columns, 2), minmax(0, 1fr));
      gap: 16px 24px;
    }

    .sidebar-canvas-grid {
      grid-template-columns: repeat(1, minmax(0, 1fr));
      gap: 12px 0;
    }
  }
}

@media (max-width: 768px) {
  .base-detail-page {
    padding: 12px;

    .detail-content {
      .detail-layout-container.has-sidebar {
        flex-direction: column;

        .sidebar-column {
          width: 100%;
        }
      }
    }
  }
}
</style>
