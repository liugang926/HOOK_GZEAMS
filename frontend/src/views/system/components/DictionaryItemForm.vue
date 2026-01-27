<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? '编辑字典项' : '添加字典项'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item
        label="字典项编码"
        prop="code"
      >
        <el-input
          v-model="formData.code"
          placeholder="请输入字典项编码（英文）"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item
        label="显示名称"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          placeholder="请输入显示名称（中文）"
        />
      </el-form-item>

      <el-form-item
        label="英文名称"
        prop="name_en"
      >
        <el-input
          v-model="formData.name_en"
          placeholder="请输入英文名称"
        />
      </el-form-item>

      <el-form-item
        label="排序号"
        prop="sort_order"
      >
        <el-input-number
          v-model="formData.sort_order"
          :min="0"
          :max="9999"
        />
      </el-form-item>

      <el-form-item
        label="显示颜色"
        prop="color"
      >
        <div class="color-picker-wrapper">
          <el-color-picker
            v-model="formData.color"
            show-alpha
          />
          <el-input
            v-model="formData.color"
            placeholder="请输入颜色值（如：#409EFF）"
            style="width: 200px; margin-left: 10px"
          />
        </div>
      </el-form-item>

      <el-form-item
        label="图标"
        prop="icon"
      >
        <el-select
          v-model="formData.icon"
          placeholder="选择图标"
          filterable
          clearable
        >
          <el-option
            v-for="icon in commonIcons"
            :key="icon.value"
            :label="icon.label"
            :value="icon.value"
          >
            <div class="icon-option">
              <el-icon><component :is="icon.value" /></el-icon>
              <span>{{ icon.label }}</span>
            </div>
          </el-option>
        </el-select>
      </el-form-item>

      <el-form-item
        label="设为默认"
        prop="is_default"
      >
        <el-switch v-model="formData.is_default" />
        <div class="form-tip">
          默认选项将自动选中
        </div>
      </el-form-item>

      <el-form-item
        label="启用状态"
        prop="is_active"
      >
        <el-switch
          v-model="formData.is_active"
          active-text="启用"
          inactive-text="禁用"
        />
      </el-form-item>

      <el-form-item
        label="描述"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="请输入描述"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        取消
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? '保存' : '添加' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  Check,
  Close,
  Delete,
  Edit,
  Search,
  Star,
  Plus,
  Minus,
  Warning,
  InfoFilled,
  SuccessFilled,
  CircleCheck,
  CircleClose,
  CirclePlus,
  Remove,
  Refresh,
  Download,
  Upload,
  Folder,
  Document,
  Files,
  Link,
  User,
  Setting,
  Bell,
  ChatDotRound,
  Message,
  Phone,
  Location,
  Calendar,
  Clock,
  Timer,
  Histogram,
  Grid,
  List,
  Sort,
  Filter,
  Share,
  StarFilled,
  Thumb,
  CaretRight,
  CaretDown,
  CaretLeft,
  CaretUp,
  ArrowRight,
  ArrowDown,
  ArrowLeft,
  ArrowUp
} from '@element-plus/icons-vue'
import type { DictionaryItem } from '@/api/system'
import { dictionaryItemApi } from '@/api/system'

interface Props {
  visible: boolean
  dictionaryTypeCode: string
  data?: DictionaryItem | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  code: '',
  name: '',
  name_en: '',
  color: '',
  icon: '',
  sort_order: 0,
  is_default: false,
  is_active: true,
  description: ''
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入字典项编码', trigger: 'blur' },
    { pattern: /^[A-Za-z_][A-Za-z0-9_]*$/, message: '编码只能包含字母、数字和下划线，且必须以字母或下划线开头', trigger: 'blur' }
  ],
  name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }]
}

const commonIcons = [
  { value: 'Check', label: 'Check (勾选)' },
  { value: 'Close', label: 'Close (关闭)' },
  { value: 'Delete', label: 'Delete (删除)' },
  { value: 'Edit', label: 'Edit (编辑)' },
  { value: 'Search', label: 'Search (搜索)' },
  { value: 'Star', label: 'Star (星标)' },
  { value: 'Plus', label: 'Plus (加号)' },
  { value: 'Minus', label: 'Minus (减号)' },
  { value: 'Warning', label: 'Warning (警告)' },
  { value: 'InfoFilled', label: 'InfoFilled (信息)' },
  { value: 'SuccessFilled', label: 'SuccessFilled (成功)' },
  { value: 'CircleCheck', label: 'CircleCheck (圆勾)' },
  { value: 'CircleClose', label: 'CircleClose (圆叉)' },
  { value: 'CirclePlus', label: 'CirclePlus (圆加)' },
  { value: 'Remove', label: 'Remove (移除)' },
  { value: 'Refresh', label: 'Refresh (刷新)' },
  { value: 'Download', label: 'Download (下载)' },
  { value: 'Upload', label: 'Upload (上传)' },
  { value: 'Folder', label: 'Folder (文件夹)' },
  { value: 'Document', label: 'Document (文档)' },
  { value: 'Files', label: 'Files (文件)' },
  { value: 'Link', label: 'Link (链接)' },
  { value: 'User', label: 'User (用户)' },
  { value: 'Setting', label: 'Setting (设置)' },
  { value: 'Bell', label: 'Bell (铃铛)' },
  { value: 'ChatDotRound', label: 'ChatDotRound (聊天)' },
  { value: 'Message', label: 'Message (消息)' },
  { value: 'Phone', label: 'Phone (电话)' },
  { value: 'Location', label: 'Location (位置)' },
  { value: 'Calendar', label: 'Calendar (日历)' },
  { value: 'Clock', label: 'Clock (时钟)' },
  { value: 'Timer', label: 'Timer (计时器)' },
  { value: 'StarFilled', label: 'StarFilled (实心星)' },
  { value: 'Thumb', label: 'Thumb (点赞)' }
]

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      code: props.data.code || '',
      name: props.data.name || '',
      name_en: props.data.name_en || '',
      color: props.data.color || '',
      icon: props.data.icon || '',
      sort_order: props.data.sort_order || 0,
      is_default: props.data.is_default || false,
      is_active: props.data.is_active ?? true,
      description: props.data.description || ''
    })
  } else if (val) {
    resetForm()
  }
})

const resetForm = () => {
  formData.value = {
    code: '',
    name: '',
    name_en: '',
    color: '',
    icon: '',
    sort_order: 0,
    is_default: false,
    is_active: true,
    description: ''
  }
  formRef.value?.clearValidate()
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await dictionaryItemApi.update(props.data!.id, formData.value)
      } else {
        await dictionaryItemApi.create({
          ...formData.value,
          dictionary_type: props.dictionaryTypeCode
        })
      }
      ElMessage.success(isEdit.value ? '更新成功' : '添加成功')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('操作失败')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.color-picker-wrapper {
  display: flex;
  align-items: center;
}

.icon-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
