<template>
  <div class="section-block">
    <div
      class="section-header"
      @click="toggle"
    >
      <div class="title">
        <el-icon :class="{ 'is-collapsed': isCollapsed }">
          <ArrowDown />
        </el-icon>
        <span class="text">{{ title }}</span>
      </div>
      <div class="actions">
        <slot name="actions" />
      </div>
    </div>
    <el-collapse-transition>
      <div
        v-show="!isCollapsed"
        class="section-body"
      >
        <slot />
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps<{
  title: string
  collapsed?: boolean
}>()

const isCollapsed = ref(props.collapsed || false)

const toggle = () => {
  isCollapsed.value = !isCollapsed.value
}
</script>

<style scoped>
.section-block {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}
.section-header {
  padding: 10px 15px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.title {
  display: flex;
  align-items: center;
  font-weight: bold;
}
.text {
  margin-left: 5px;
}
.is-collapsed {
  transform: rotate(-90deg);
}
.section-body {
  padding: 15px;
}
</style>
