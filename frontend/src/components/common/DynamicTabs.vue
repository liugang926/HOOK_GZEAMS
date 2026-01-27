<template>
  <el-tabs
    v-model="activeTab"
    type="card"
    closable
    @tab-remove="removeTab"
  >
    <el-tab-pane
      v-for="item in tabs"
      :key="item.name"
      :label="item.title"
      :name="item.name"
    >
      <component
        :is="item.component"
        v-bind="item.props"
      />
    </el-tab-pane>
  </el-tabs>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  modelValue: string
  tabs: any[]
}>()

const emit = defineEmits(['update:modelValue', 'remove'])

const activeTab = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const removeTab = (targetName: string) => {
  emit('remove', targetName)
}
</script>
