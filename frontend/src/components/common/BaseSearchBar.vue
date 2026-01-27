<template>
  <div class="base-search-bar">
    <el-form
      :model="formData"
      inline
      @submit.prevent="handleSearch"
    >
      <!-- Search input -->
      <el-form-item
        v-if="showSearch"
        label="Search"
      >
        <el-input
          v-model="formData.search"
          :placeholder="searchPlaceholder"
          clearable
          @clear="handleClear"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </el-form-item>

      <!-- Dynamic filter fields -->
      <template
        v-for="field in filterFields"
        :key="field.key"
      >
        <el-form-item :label="field.label">
          <!-- Select filter -->
          <el-select
            v-if="field.type === 'select'"
            v-model="formData[field.key]"
            :placeholder="field.placeholder || `Select ${field.label}`"
            clearable
            filterable
            style="width: 180px"
          >
            <el-option
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>

          <!-- Date range filter -->
          <el-date-picker
            v-else-if="field.type === 'dateRange'"
            v-model="formData[field.key]"
            type="daterange"
            :placeholder="field.placeholder || 'Select date range'"
            range-separator="-"
            start-placeholder="Start date"
            end-placeholder="End date"
            value-format="YYYY-MM-DD"
            style="width: 240px"
            clearable
          />

          <!-- Date filter -->
          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formData[field.key]"
            type="date"
            :placeholder="field.placeholder || 'Select date'"
            value-format="YYYY-MM-DD"
            style="width: 180px"
            clearable
          />

          <!-- Number range filter -->
          <div
            v-else-if="field.type === 'numberRange'"
            class="number-range"
          >
            <el-input-number
              v-model="formData[field.key + '_min']"
              :placeholder="field.minPlaceholder || 'Min'"
              :controls="false"
              style="width: 100px"
            />
            <span class="range-separator">-</span>
            <el-input-number
              v-model="formData[field.key + '_max']"
              :placeholder="field.maxPlaceholder || 'Max'"
              :controls="false"
              style="width: 100px"
            />
          </div>

          <!-- Boolean filter -->
          <el-switch
            v-else-if="field.type === 'boolean'"
            v-model="formData[field.key]"
            :active-text="field.activeText || 'Yes'"
            :inactive-text="field.inactiveText || 'No'"
          />

          <!-- Text input filter (default) -->
          <el-input
            v-else
            v-model="formData[field.key]"
            :placeholder="field.placeholder || `Enter ${field.label}`"
            clearable
            style="width: 180px"
          />
        </el-form-item>
      </template>

      <!-- Actions -->
      <el-form-item>
        <el-button
          type="primary"
          :icon="Search"
          @click="handleSearch"
        >
          Search
        </el-button>
        <el-button
          :icon="RefreshLeft"
          @click="handleReset"
        >
          Reset
        </el-button>
        <el-button
          v-if="showAdvanced"
          text
          @click="toggleAdvanced"
        >
          {{ advancedVisible ? 'Collapse' : 'Advanced' }}
          <el-icon>
            <ArrowDown v-if="!advancedVisible" />
            <ArrowUp v-else />
          </el-icon>
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Advanced filters panel -->
    <el-collapse-transition>
      <div
        v-if="advancedVisible && advancedFields.length > 0"
        class="advanced-filters"
      >
        <el-divider />
        <el-form
          :model="formData"
          inline
        >
          <el-form-item
            v-for="field in advancedFields"
            :key="field.key"
            :label="field.label"
          >
            <!-- Same field types as above -->
            <el-select
              v-if="field.type === 'select'"
              v-model="formData[field.key]"
              :placeholder="field.placeholder || `Select ${field.label}`"
              clearable
              filterable
              style="width: 180px"
            >
              <el-option
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>

            <el-date-picker
              v-else-if="field.type === 'dateRange'"
              v-model="formData[field.key]"
              type="daterange"
              :placeholder="field.placeholder || 'Select date range'"
              value-format="YYYY-MM-DD"
              style="width: 240px"
              clearable
            />

            <el-input
              v-else
              v-model="formData[field.key]"
              :placeholder="field.placeholder || `Enter ${field.label}`"
              clearable
              style="width: 180px"
            />
          </el-form-item>
        </el-form>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { Search, RefreshLeft, ArrowDown, ArrowUp } from '@element-plus/icons-vue'

/**
 * Filter field types
 */
export type FilterFieldType =
  | 'text'
  | 'select'
  | 'date'
  | 'dateRange'
  | 'numberRange'
  | 'boolean'

export interface FilterField {
  key: string
  label: string
  type?: FilterFieldType
  placeholder?: string
  minPlaceholder?: string
  maxPlaceholder?: string
  activeText?: string
  inactiveText?: string
  options?: Array<{ label: string; value: any }>
  defaultValue?: any
  advanced?: boolean
}

export interface FilterFormData {
  search?: string
  [key: string]: any
}

interface Props {
  showSearch?: boolean
  searchPlaceholder?: string
  filterFields?: FilterField[]
  showAdvanced?: boolean
  initialFilters?: FilterFormData
}

interface Emits {
  (e: 'search', filters: FilterFormData): void
  (e: 'reset'): void
  (e: 'change', filters: FilterFormData): void
}

const props = withDefaults(defineProps<Props>(), {
  showSearch: true,
  searchPlaceholder: 'Search...',
  filterFields: () => [],
  showAdvanced: false,
  initialFilters: () => ({})
})

const emit = defineEmits<Emits>()

// Form data state
const formData = reactive<FilterFormData>({ ...props.initialFilters })

// Advanced panel visibility
const advancedVisible = ref(false)

// Split fields into basic and advanced
const basicFields = computed(() => props.filterFields.filter(f => !f.advanced))
const advancedFields = computed(() => props.filterFields.filter(f => f.advanced))

// Initialize default values
const initializeDefaults = () => {
  props.filterFields.forEach(field => {
    if (field.defaultValue !== undefined && formData[field.key] === undefined) {
      formData[field.key] = field.defaultValue
    }
  })
}

// Toggle advanced panel
const toggleAdvanced = () => {
  advancedVisible.value = !advancedVisible.value
}

// Handle search
const handleSearch = () => {
  emit('search', { ...formData })
}

// Handle reset
const handleReset = () => {
  Object.keys(formData).forEach(key => {
    if (key === 'search') {
      formData[key] = ''
    } else {
      delete formData[key]
    }
  })
  initializeDefaults()
  emit('reset')
}

// Handle clear
const handleClear = () => {
  formData.search = ''
  emit('change', { ...formData })
}

// Watch for form data changes
watch(
  () => formData,
  (newData) => {
    emit('change', { ...newData })
  },
  { deep: true }
)

// Initialize defaults on mount
initializeDefaults()
</script>

<script lang="ts">
import { computed } from 'vue'
export default {
  computed
}
</script>

<style scoped>
.base-search-bar {
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 4px;
  margin-bottom: 16px;
}

.number-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-separator {
  color: var(--el-text-color-placeholder);
}

.advanced-filters {
  padding-top: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 12px;
}

:deep(.el-form-item:last-child) {
  margin-bottom: 0;
}
</style>
