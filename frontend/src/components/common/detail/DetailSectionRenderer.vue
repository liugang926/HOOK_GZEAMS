<template>
  <div :class="rootClasses">
    <div
      v-if="section.title"
      class="section-header"
      :data-testid="sectionHeaderTestId || undefined"
      @click="emit('section-click', section)"
    >
      <div class="section-title">
        <el-icon
          v-if="section.icon"
          class="section-icon"
        >
          <component :is="section.icon" />
        </el-icon>
        <span>{{ displayTitle }}</span>
      </div>
      <el-icon
        v-if="section.collapsible"
        :class="['collapse-icon', { 'is-collapsed': collapsed }]"
      >
        <ArrowDown />
      </el-icon>
    </div>

    <div
      v-show="!collapsed"
      class="section-content"
    >
      <ErrorBoundary>
        <template #fallback="{ error, reset }">
          <el-alert
            :title="errorTitle"
            type="warning"
            show-icon
            :closable="false"
          >
            <template #default>
              <div class="error-description">
                {{ error || $t('common.messages.operationFailed') }}
              </div>
              <div class="error-actions">
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="reset"
                >
                  {{ $t('system.fieldDefinition.actions.retry') }}
                </el-button>
              </div>
            </template>
          </el-alert>
        </template>

        <slot
          v-if="hasSectionSlot"
          name="section"
          :data="data"
          :section="section"
        />

        <template v-else>
          <template v-if="section.type === 'tab' && section.tabs && section.tabs.length > 0">
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
                  class="detail-canvas-grid"
                  :style="getSectionCanvasStyle(section)"
                >
                  <div
                    v-for="field in tab.fields.filter(f => !f.hidden)"
                    :key="field.prop"
                    class="field-col"
                    :style="getFieldColStyle(field, section)"
                  >
                    <div
                      v-if="field.type === 'slot'"
                      class="field-item"
                      :style="getFieldItemStyle(field)"
                      v-bind="getFieldPlacementAttrs(field)"
                    >
                      <slot
                        :name="`field-${field.prop}`"
                        :field="field"
                        :data="data"
                        :value="resolveFieldValue(field)"
                      />
                    </div>

                    <div
                      v-else
                      :class="['field-item', { 'field-image': field.type === 'image' }]"
                      :style="getFieldItemStyle(field)"
                      v-bind="getFieldPlacementAttrs(field)"
                    >
                      <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                      <div :class="['field-value', field.valueClass]">
                        <slot
                          name="field-content"
                          :field="field"
                          :data="data"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </template>

          <template v-else>
            <div
              :class="['detail-canvas-grid', { 'sidebar-canvas-grid': sidebar }]"
              :style="getSectionCanvasStyle(section)"
            >
              <div
                v-for="field in section.fields.filter(f => !f.hidden)"
                :key="field.prop"
                :class="['field-col', { 'sidebar-field-col': sidebar }]"
                :style="getFieldColStyle(field, section)"
              >
                <div
                  v-if="field.type === 'slot'"
                  :class="['field-item', { 'sidebar-field-item': sidebar }]"
                  :style="getFieldItemStyle(field)"
                  v-bind="getFieldPlacementAttrs(field)"
                >
                  <slot
                    :name="`field-${field.prop}`"
                    :field="field"
                    :data="data"
                    :value="resolveFieldValue(field)"
                  />
                </div>

                <div
                  v-else
                  :class="[
                    'field-item',
                    { 'field-image': field.type === 'image', 'sidebar-field-item': sidebar }
                  ]"
                  :style="getFieldItemStyle(field)"
                  v-bind="getFieldPlacementAttrs(field)"
                >
                  <span :class="['field-label', field.labelClass]">{{ field.label }}</span>
                  <div :class="['field-value', field.valueClass]">
                    <slot
                      name="field-content"
                      :field="field"
                      :data="data"
                    />
                  </div>
                </div>
              </div>
            </div>
          </template>
        </template>
      </ErrorBoundary>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import ErrorBoundary from '../ErrorBoundary.vue'
import type { DetailField, DetailSection } from '../BaseDetailPage.vue'
import { useDetailGridPlacement } from '@/composables/useDetailGridPlacement'
import { resolveTranslatableText } from '@/utils/localeText'

type AnyRecord = Record<string, unknown>

const props = withDefaults(defineProps<{
  section: DetailSection
  data: AnyRecord
  fieldSpan?: number
  collapsed?: boolean
  activeTabId?: string
  displayTitle?: string
  errorTitle?: string
  sectionHeaderTestId?: string
  sidebar?: boolean
  hasSectionSlot?: boolean
  getFieldValue?: (field: DetailField) => unknown
}>(), {
  fieldSpan: 12,
  collapsed: false,
  activeTabId: '',
  displayTitle: '',
  errorTitle: '',
  sectionHeaderTestId: '',
  sidebar: false,
  hasSectionSlot: false,
  getFieldValue: undefined
})

const emit = defineEmits<{
  (e: 'section-click', section: DetailSection): void
  (e: 'tab-change', tabId: string, sectionName: string): void
}>()

const { locale } = useI18n()

const { getSectionCanvasStyle, getFieldColStyle, getFieldItemStyle, getFieldPlacementAttrs } = useDetailGridPlacement({
  fieldSpan: computed(() => props.fieldSpan)
})

const rootClasses = computed(() => [
  'detail-section',
  {
    'is-collapsed': props.collapsed,
    'sidebar-section-block': props.sidebar
  }
])

const getDisplayText = (value: any): string => {
  if (typeof value === 'string') return value
  return resolveTranslatableText(value, locale.value as 'zh-CN' | 'en-US')
}

const displayTitle = computed(() => props.displayTitle || getDisplayText(props.section.title) || '')
const errorTitle = computed(() => props.errorTitle || displayTitle.value)

const activeTabModel = computed({
  get: () => props.activeTabId || props.section.tabs?.[0]?.id || '',
  set: (value: string) => emit('tab-change', value, props.section.name)
})

const resolveFieldValue = (field: DetailField) => {
  return props.getFieldValue ? props.getFieldValue(field) : undefined
}
</script>

