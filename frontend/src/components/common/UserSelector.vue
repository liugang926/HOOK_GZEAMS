<template>
  <el-select
    v-model="selectedUsers"
    multiple
    filterable
    remote
    :remote-method="searchUsers"
    placeholder="搜索用户"
    style="width: 100%"
    :loading="loading"
  >
    <el-option
      v-for="user in options"
      :key="user.id"
      :label="user.real_name || user.username"
      :value="user.id"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getUsers } from '@/api/system'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  multiple: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const loading = ref(false)
const options = ref<any[]>([])

const selectedUsers = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const searchUsers = async (query: string) => {
  if (query) {
    loading.value = true
    try {
        // Assume API supports 'search' param
        const res = await getUsers({ search: query })
        options.value = res.results || res.items || []
    } catch (e) {
        console.error(e)
    } finally {
        loading.value = false
    }
  } else {
    options.value = []
  }
}

// Initial load if needed, or rely on search
</script>
