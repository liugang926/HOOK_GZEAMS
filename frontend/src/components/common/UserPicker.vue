<!--
  UserPicker Component

  A user selection component with:
  - Searchable user dropdown
  - Department filtering
  - Multiple selection support
  - User avatar display
  - Lazy loading for large user lists

  Usage:
  <UserPicker
    v-model="selectedUser"
    :multiple="false"
    :filter-dept="true"
    placeholder="请选择用户"
    @change="handleUserChange"
  />
-->

<script setup lang="ts">
/**
 * UserPicker Component
 *
 * A specialized picker component for selecting users from the organization.
 * Supports search, department filtering, and multiple selection.
 */

import { ref, computed, watch } from 'vue'
import { userApi } from '@/api/users'
import { deptApi } from '@/api/organizations'
import type { User } from '@/types/common'

// ============================================================================
// Types
// ============================================================================

interface UserOption extends User {
  /** Display label */
  label?: string
  /** Value for selection */
  value?: string
}

interface Props {
  /** Selected user(s) */
  modelValue?: string | string[] | User | User[]
  /** Multiple selection */
  multiple?: boolean
  /** Disabled state */
  disabled?: boolean
  /** Clearable */
  clearable?: boolean
  /** Placeholder text */
  placeholder?: string
  /** Filter by department */
  filterDept?: boolean
  /** Show department info */
  showDept?: boolean
  /** Show avatar */
  showAvatar?: boolean
  /** Maximum selections (for multiple) */
  maxSelections?: number
  /** Collapse tags for multiple selection */
  collapseTags?: boolean
  /** Remote search (search API) */
  remote?: boolean
  /** Debounce delay for remote search (ms) */
  debounce?: number
  /** Size */
  size?: 'large' | 'default' | 'small'
}

interface Emits {
  (e: 'update:modelValue', value: string | string[] | User | User[] | undefined): void
  (e: 'change', value: any): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  multiple: false,
  disabled: false,
  clearable: true,
  placeholder: '请选择用户',
  filterDept: false,
  showDept: true,
  showAvatar: false,
  remote: true,
  debounce: 300,
  size: 'default'
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const loading = ref(false)
const users = ref<UserOption[]>([])
const departments = ref<Array<{ id: string; name: string }>>([])
const selectedDept = ref<string>()
const searchKeyword = ref('')

// ============================================================================
// Computed
// ============================================================================

/** Current value as array */
const valueArray = computed(() => {
  if (!props.modelValue) return []
  if (Array.isArray(props.modelValue)) {
    return props.modelValue
  }
  return [props.modelValue]
})

/** Display label for user */
const getUserLabel = (user: UserOption): string => {
  const name = `${user.firstName || ''} ${user.lastName || ''}`.trim()
  const username = user.username || ''

  if (name && props.showDept && user.departmentName) {
    return `${name} (${user.departmentName})`
  } else if (name) {
    return `${name} (@${username})`
  }
  return username
}

/** Options for select dropdown */
const selectOptions = computed(() => {
  return users.value.map(user => ({
    label: getUserLabel(user),
    value: user.id,
    ...user
  }))
})

/** Can select more */
const canSelectMore = computed(() => {
  if (!props.multiple || !props.maxSelections) return true
  return valueArray.value.length < props.maxSelections
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Load users
 */
const loadUsers = async (keyword?: string) => {
  if (!canSelectMore.value && !keyword) return

  loading.value = true
  try {
    const params: any = {
      pageSize: 50,
      isActive: true
    }

    if (keyword) {
      params.search = keyword
    }

    if (selectedDept.value) {
      params.departmentId = selectedDept.value
    }

    const response = await userApi.list(params)
    users.value = response.results || []
  } catch (error) {
    users.value = []
  } finally {
    loading.value = false
  }
}

/**
 * Load departments for filter
 */
const loadDepartments = async () => {
  if (!props.filterDept) return

  try {
    const depts = await deptApi.list()
    departments.value = depts.map((d: any) => ({
      id: d.id,
      name: d.name
    }))
  } catch (error) {
    departments.value = []
  }
}

/**
 * Handle remote search
 */
let searchTimer: ReturnType<typeof setTimeout> | null = null
const handleSearch = (keyword: string) => {
  if (!props.remote) return

  if (searchTimer) {
    clearTimeout(searchTimer)
  }

  searchTimer = setTimeout(() => {
    searchKeyword.value = keyword
    loadUsers(keyword)
  }, props.debounce)
}

/**
 * Handle department change
 */
const handleDeptChange = () => {
  loadUsers()
}

/**
 * Handle value change
 */
const handleChange = (value: string | string[]) => {
  emit('update:modelValue', value)
  emit('change', value)
}

/**
 * Handle visible change (dropdown open/close)
 */
const handleVisibleChange = (visible: boolean) => {
  if (visible && users.value.length === 0) {
    loadUsers()
  }
}

/**
 * Get user by ID
 */
const getUserById = (id: string) => {
  return users.value.find(u => u.id === id)
}

/**
 * Get selected user objects
 */
const getSelectedUsers = (): User[] => {
  return valueArray.value
    .map(id => getUserById(id as string))
    .filter(u => u) as User[]
}

// ============================================================================
// Watch
// ============================================================================

// Load departments when component mounts
watch(() => props.filterDept, (enabled) => {
  if (enabled) {
    loadDepartments()
  }
}, { immediate: true })

// Reload users when department filter changes
watch(selectedDept, handleDeptChange)

// ============================================================================
// Lifecycle
// ============================================================================

// Initial load if not remote
if (!props.remote) {
  loadUsers()
}

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  loadUsers,
  loadDepartments,
  getSelectedUsers
})
</script>

<template>
  <div class="user-picker">
    <div v-if="filterDept" class="dept-filter">
      <el-select
        v-model="selectedDept"
        placeholder="按部门筛选"
        clearable
        :size="size"
        @change="handleDeptChange"
      >
        <el-option
          v-for="dept in departments"
          :key="dept.id"
          :label="dept.name"
          :value="dept.id"
        />
      </el-select>
    </div>

    <el-select
      :model-value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :clearable="clearable"
      :filterable="true"
      :remote="remote"
      :remote-method="handleSearch"
      :loading="loading"
      :multiple="multiple"
      :collapse-tags="collapseTags"
      :collapse-tags-tooltip="collapseTags"
      :size="size"
      :no-match-text="searchKeyword ? '未找到匹配的用户' : '请输入关键字搜索'"
      @update:model-value="handleChange"
      @visible-change="handleVisibleChange"
    >
      <el-option
        v-for="option in selectOptions"
        :key="option.value"
        :label="option.label"
        :value="option.value"
        :disabled="!canSelectMore && !valueArray.includes(option.value)"
      >
        <div class="user-option">
          <!-- Avatar -->
          <el-avatar
            v-if="showAvatar"
            :src="option.avatar"
            :size="32"
            class="user-avatar"
          >
            {{ (option.firstName || 'U')[0] }}
          </el-avatar>

          <!-- User info -->
          <div class="user-info">
            <div class="user-name">
              {{ option.firstName }} {{ option.lastName }}
              <span v-if="option.username" class="user-username">@{{ option.username }}</span>
            </div>
            <div v-if="showDept && option.departmentName" class="user-dept">
              {{ option.departmentName }}
            </div>
          </div>

          <!-- Status indicator -->
          <el-tag v-if="!option.isActive" type="info" size="small">停用</el-tag>
        </div>
      </el-option>
    </el-select>
  </div>
</template>

<style scoped lang="scss">
.user-picker {
  .dept-filter {
    margin-bottom: 8px;

    .el-select {
      width: 100%;
    }
  }

  .el-select {
    width: 100%;
  }

  .user-option {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;

    .user-avatar {
      flex-shrink: 0;
    }

    .user-info {
      flex: 1;
      min-width: 0;

      .user-name {
        font-size: 14px;
        color: #303133;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;

        .user-username {
          margin-left: 4px;
          font-size: 12px;
          color: #909399;
        }
      }

      .user-dept {
        font-size: 12px;
        color: #909399;
        margin-top: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
    }
  }
}
</style>
