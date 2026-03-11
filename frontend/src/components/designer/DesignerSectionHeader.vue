<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  sectionId: string
  title: string
  selected?: boolean
  interactive?: boolean
  selectSection: (sectionId: string) => void
}>(), {
  selected: false,
  interactive: true
})

const emit = defineEmits<{
  titleUpdate: [sectionId: string, title: string]
}>()

const editingTitle = ref(false)
const titleDraft = ref(props.title)
const titleInputRef = ref<HTMLInputElement | null>(null)
let cancelPending = false

watch(
  () => props.title,
  (value) => {
    if (!editingTitle.value) {
      titleDraft.value = value
    }
  }
)

const startEditing = async () => {
  if (!props.interactive) return
  props.selectSection(props.sectionId)
  editingTitle.value = true
  titleDraft.value = props.title
  await nextTick()
  titleInputRef.value?.focus()
  titleInputRef.value?.select()
}

const finishEditing = () => {
  if (!editingTitle.value) return
  editingTitle.value = false
  const nextTitle = titleDraft.value.trim()
  if (nextTitle && nextTitle !== props.title) {
    emit('titleUpdate', props.sectionId, nextTitle)
  } else {
    titleDraft.value = props.title
  }
}

const cancelEditing = () => {
  cancelPending = true
  editingTitle.value = false
  titleDraft.value = props.title
}

const handleBlur = () => {
  if (cancelPending) {
    cancelPending = false
    return
  }
  finishEditing()
}
</script>

<template>
  <div
    class="designer-section-header"
    :class="{ 'is-selected': selected, 'is-editing': editingTitle }"
    @click.stop="selectSection(sectionId)"
  >
    <input
      v-if="editingTitle"
      ref="titleInputRef"
      v-model="titleDraft"
      class="designer-section-title-input"
      data-testid="designer-section-title-input"
      type="text"
      @click.stop
      @blur="handleBlur"
      @keydown.enter.prevent="finishEditing"
      @keydown.esc.prevent="cancelEditing"
    />
    <span
      v-else
      class="designer-section-title-text"
      data-testid="designer-section-title"
      @dblclick.stop="startEditing"
    >
      {{ title }}
    </span>
  </div>
</template>

<style scoped lang="scss">
.designer-section-header {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: 100%;
  border-radius: 6px;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
}

.designer-section-header.is-selected {
  background: rgba(64, 158, 255, 0.08);
}

.designer-section-title-text {
  display: inline-block;
  min-width: 0;
  max-width: 100%;
  padding: 2px 6px;
  border-radius: 6px;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
  cursor: text;
}

.designer-section-title-text:hover {
  background: rgba(64, 158, 255, 0.08);
}

.designer-section-title-input {
  width: min(320px, 100%);
  min-width: 160px;
  padding: 4px 8px;
  font: inherit;
  font-weight: 600;
  color: inherit;
  background: #ffffff;
  border: 1px solid var(--el-color-primary, #409eff);
  border-radius: 6px;
  outline: none;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
}
</style>
