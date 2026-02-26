<template>
  <el-select
    v-model="selectedUsers"
    :multiple="multiple"
    :disabled="disabled"
    filterable
    remote
    :remote-method="searchUsers"
    :placeholder="$t('common.selectors.searchUser')"
    style="width: 100%"
    :loading="loading"
    value-key="id"
    @visible-change="handleVisibleChange"
  >
    <el-option
      v-for="user in allOptions"
      :key="user.id"
      :label="user.fullName || user.full_name || user.realName || user.real_name || user.username || user.email"
      :value="user.id"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getUsers } from '@/api/system'
import { referenceResolver } from '@/platform/reference/referenceResolver'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: [String, Number, Array],
    default: () => []
  },
  multiple: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const options = ref<any[]>([])
const currentValueUsers = ref<any[]>([])

// Combine search results with current selected users
const allOptions = computed(() => {
  const result = [...options.value]
  // Add current value users if not in options
  if (currentValueUsers.value.length > 0) {
    currentValueUsers.value.forEach(user => {
      if (!result.find(o => o.id === user.id)) {
        result.push(user)
      }
    })
  }
  return result
})

const selectedUsers = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const searchUsers = async (query: string) => {
  loading.value = true
  try {
    const res = await getUsers({ search: query || '' })
    options.value = res.results || res.items || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const handleVisibleChange = (visible: boolean) => {
  if (!visible) return
  if (props.disabled) return
  if (loading.value) return
  if ((options.value || []).length > 0) return
  searchUsers('')
}

// Fetch current selected users by IDs for display
const fetchCurrentUsers = async () => {
  const ids = Array.isArray(props.modelValue)
    ? props.modelValue
    : props.modelValue ? [props.modelValue] : []

  if (ids.length === 0) return

  try {
    // Batch resolve for display — single request instead of N.
    const stringIds = ids.map((id) => String(id))
    const resolved = await referenceResolver.resolveMany('User', stringIds)
    currentValueUsers.value = Object.values(resolved).filter(Boolean)
  } catch (e) {
    console.error('Failed to fetch current users:', e)
  }
}

// Watch for model value changes
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    fetchCurrentUsers()
  }
}, { immediate: true })
</script>
