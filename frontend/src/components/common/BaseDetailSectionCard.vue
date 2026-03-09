<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import ErrorBoundary from './ErrorBoundary.vue'
import FieldDisplay from './FieldDisplay.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

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
  collapsible?: boolean
  position?: 'main' | 'sidebar'
  fields: DetailFieldLike[]
  tabs?: DetailTabLike[]
}

interface Props {
  section: DetailSectionLike
  data: Record<string, any>
  editMode: boolean
  activeTabs: Record<string, string>
  sectionHeaderTestId?: string
  sidebar?: boolean
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
}

const props = withDefaults(defineProps<Props>(), {
  sectionHeaderTestId: '',
  sidebar: false
})

const { t } = useI18n()

const activeTabModel = computed({
  get: () => props.activeTabs[props.section.name],
  set: (value: string) => {
    props.activeTabs[props.section.name] = value
  }
})

const visibleSectionFields = computed(() => {
  return (props.section.fields || []).filter((field) => !field.hidden)
})

const sectionClass = computed(() => [
  'detail-section',
  {
    'is-collapsed': props.isSectionCollapsed(props.section),
    'sidebar-section-block': props.sidebar
  }
])

const canvasClass = computed(() => [
  'detail-canvas-grid',
  {
    'sidebar-canvas-grid': props.sidebar
  }
])

const fieldColClass = computed(() => [
  'field-col',
  {
    'sidebar-field-col': props.sidebar
  }
])

const fieldItemBaseClass = (field: DetailFieldLike) => [
  'field-item',
  {
    'sidebar-field-item': props.sidebar,
    'field-image': field.type === 'image'
  }
]
</script>

<template>
  <div :class="sectionClass">
    <div
      v-if="section.title"
      class="section-header"
      :data-testid="sectionHeaderTestId || undefined"
      @click="handleSectionHeaderClick(section)"
    >
      <div class="section-title">
        <el-icon
          v-if="section.icon"
          class="section-icon"
        >
          <component :is="section.icon" />
        </el-icon>
        <span>{{ getSectionDisplayTitle(section) }}</span>
      </div>
      <el-icon
        v-if="section.collapsible"
        :class="['collapse-icon', { 'is-collapsed': isSectionCollapsed(section) }]"
      >
        <ArrowDown />
      </el-icon>
    </div>

    <div
      v-show="!isSectionCollapsed(section)"
      class="section-content"
    >
      <ErrorBoundary>
        <template #fallback="{ error, reset }">
          <el-alert
            :title="getSectionErrorTitle(section)"
            type="warning"
            show-icon
            :closable="false"
          >
            <template #default>
              <div class="error-description">
                {{ error || t('common.messages.operationFailed') }}
              </div>
              <div class="error-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="reset"
                >
                  {{ t('system.fieldDefinition.actions.retry') }}
                </el-button>
              </div>
            </template>
          </el-alert>
        </template>

        <slot
          v-if="$slots[`section-${section.name}`]"
          :name="`section-${section.name}`"
          :data="data"
          :section="section"
        />

        <template v-else-if="!sidebar && section.type === 'tab' && section.tabs && section.tabs.length > 0">
          <el-tabs
            v-model="activeTabModel"
            type="card"
            class="detail-section-tabs"
          >
            <el-tab-pane
              v-for="tab in section.tabs"
              :key="tab.id"
              :label="getDisplayText(tab.title)"
              :name="tab.id"
            >
              <div
                :class="canvasClass"
                :style="getSectionCanvasStyle(section)"
              >
                <div
                  v-for="field in tab.fields.filter((item) => !item.hidden)"
                  :key="field.prop"
                  :class="fieldColClass"
                  :style="getFieldColStyle(field, section)"
                >
                  <div
                    v-if="field.type === 'slot'"
                    :class="fieldItemBaseClass(field)"
                    :style="getFieldItemStyle(field)"
                    v-bind="getFieldPlacementAttrs(field)"
                  >
                    <slot
                      :name="`field-${field.prop}`"
                      :field="field"
                      :data="data"
                      :value="getFieldValue(field)"
                    />
                  </div>

                  <div
                    v-else
                    :class="fieldItemBaseClass(field)"
                    :style="getFieldItemStyle(field)"
                    v-bind="getFieldPlacementAttrs(field)"
                  >
                    <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                    <div :class="['field-value', field.valueClass]">
                      <template v-if="editMode">
                        <el-form-item
                          :prop="field.prop"
                          style="margin-bottom: 0px"
                        >
                          <FieldRenderer
                            :field="toInlineEditRuntimeField(field)"
                            :model-value="getEditFieldValue(field)"
                            :disabled="field.readonly === true"
                            @update:model-value="updateFormData(field.prop, $event)"
                          />
                        </el-form-item>
                      </template>
                      <template v-else-if="field.type === 'related_object'">
                        <FieldRenderer
                          :field="toInlineEditRuntimeField(field)"
                          :model-value="getEditFieldValue(field)"
                          :disabled="true"
                        />
                      </template>
                      <template v-else>
                        <FieldDisplay
                          :field="field"
                          :value="getFieldValue(field)"
                        />
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>

        <template v-else>
          <div
            :class="canvasClass"
            :style="getSectionCanvasStyle(section)"
          >
            <div
              v-for="field in visibleSectionFields"
              :key="field.prop"
              :class="fieldColClass"
              :style="getFieldColStyle(field, section)"
            >
              <div
                v-if="field.type === 'slot'"
                :class="fieldItemBaseClass(field)"
                :style="getFieldItemStyle(field)"
                v-bind="getFieldPlacementAttrs(field)"
              >
                <slot
                  :name="`field-${field.prop}`"
                  :field="field"
                  :data="data"
                  :value="getFieldValue(field)"
                />
              </div>

              <div
                v-else
                :class="fieldItemBaseClass(field)"
                :style="getFieldItemStyle(field)"
                v-bind="getFieldPlacementAttrs(field)"
              >
                <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                <div :class="['field-value', field.valueClass]">
                  <template v-if="editMode">
                    <el-form-item
                      :prop="field.prop"
                      style="margin-bottom: 0px"
                    >
                      <FieldRenderer
                        :field="toInlineEditRuntimeField(field)"
                        :model-value="getEditFieldValue(field)"
                        :disabled="field.readonly === true"
                        @update:model-value="updateFormData(field.prop, $event)"
                      />
                    </el-form-item>
                  </template>
                  <template v-else-if="field.type === 'related_object'">
                    <FieldRenderer
                      :field="toInlineEditRuntimeField(field)"
                      :model-value="getEditFieldValue(field)"
                      :disabled="true"
                    />
                  </template>
                  <template v-else>
                    <FieldDisplay
                      :field="field"
                      :value="getFieldValue(field)"
                    />
                  </template>
                </div>
              </div>
            </div>
          </div>
        </template>
      </ErrorBoundary>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.detail-section {
  background-color: $bg-card;
  border-radius: $radius-large;
  box-shadow: $shadow-sm;
  overflow: hidden;
  border: 1px solid $border-light;

  &.is-collapsed {
    .section-content {
      display: none;
    }

    .collapse-icon {
      transform: rotate(-90deg);
    }
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px $spacing-lg;
    background-color: #f8fafc;
    border-bottom: 1px solid $border-light;
    border-left: 3px solid $primary-color;
    cursor: default;
    transition: background-color 0.15s;

    &:hover {
      background-color: #f1f5f9;
    }

    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      color: $text-main;

      .section-icon {
        font-size: 16px;
        color: $primary-color;
      }
    }

    .collapse-icon {
      transition: transform 0.3s;
      color: $text-secondary;
    }
  }

  .section-content {
    padding: 20px;

    .detail-canvas-grid {
      display: grid;
      grid-template-columns: repeat(var(--detail-section-columns, 2), minmax(0, 1fr));
      gap: 16px 24px;
      align-items: start;
      grid-auto-flow: row dense;
    }

    .detail-canvas-grid.sidebar-canvas-grid {
      grid-template-columns: repeat(1, minmax(0, 1fr));
      gap: 12px 0;
    }

    .field-col {
      min-width: 0;
    }

    .field-item {
      display: grid;
      grid-template-columns: var(--detail-label-width) minmax(0, 1fr);
      column-gap: var(--detail-field-gap);
      align-items: flex-start;

      &.field-image {
        display: flex;
        flex-direction: column;
        align-items: flex-start;

        .detail-image {
          width: 120px;
          height: 120px;
          border-radius: 4px;
          overflow: hidden;

          .image-error {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            background-color: #f5f7fa;
            color: #c0c4cc;
            font-size: 32px;
          }
        }
      }

      .field-label {
        display: block;
        font-size: 13px;
        color: $text-secondary;
        line-height: 22px;
        font-weight: 500;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
      }

      .field-value {
        min-width: 0;
        font-size: 14px;
        color: $text-main;
        line-height: 22px;
        overflow-wrap: anywhere;
        word-break: break-word;
      }
    }

    .sidebar-field-col {
      min-width: 0;
    }

    .sidebar-field-item {
      display: flex;
      flex-direction: column;
      align-items: flex-start;

      .field-label {
        margin-bottom: 4px;
        color: $text-secondary;
        font-size: 13px;
        font-weight: 500;
        white-space: normal;
        overflow-wrap: anywhere;
        word-break: break-word;
      }

      .field-value {
        width: 100%;
        font-size: 14px;
        color: $text-main;
        overflow-wrap: anywhere;
        word-break: break-word;
      }
    }
  }
}

@media (max-width: 768px) {
  .detail-section {
    .section-content {
      padding: 12px;

      .detail-canvas-grid {
        grid-template-columns: 1fr !important;
        gap: 12px;
      }

      .field-item {
        grid-template-columns: 1fr;
        row-gap: 4px;

        .field-label {
          margin-bottom: 0;
        }
      }
    }
  }
}
</style>
