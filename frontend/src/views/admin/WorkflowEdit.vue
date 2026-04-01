<template>
  <div class="workflow-edit">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? $t('system.workflow.editTitle') : $t('system.workflow.createTitle')"
        @back="$router.back()"
      />
    </div>

    <div class="form-container">
      <el-form inline :model="form">
        <el-form-item :label="$t('system.workflow.form.name')">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('system.workflow.form.code')">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item :label="$t('system.workflow.form.businessObject')">
          <el-select
            v-model="form.business_object"
            :loading="loadingObjects"
            filterable
            style="min-width: 220px"
          >
            <el-option
              v-for="obj in businessObjects"
              :key="obj.code"
              :label="obj.name"
              :value="obj.code"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- Designer takes remaining height -->
    <div class="designer-container">
      <WorkflowDesigner
        v-model="form.graph_data"
        :business-object="form.business_object"
        @save="handleSave"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, computed, defineAsyncComponent, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createWorkflow, updateWorkflow, getWorkflow } from '@/api/workflows'
import request from '@/utils/request'

const WorkflowDesigner = defineAsyncComponent(
  () => import('@/components/workflow/WorkflowDesigner.vue'),
)

interface BusinessObjectItem {
  code: string
  name: string
}

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  code: '',
  business_object: '',
  graph_data: { nodes: [], edges: [] },
})

// Dynamically fetched business objects
const businessObjects = ref<BusinessObjectItem[]>([])
const loadingObjects = ref(false)

const loadBusinessObjects = async () => {
  loadingObjects.value = true
  try {
    const response = await request.get<{ results?: BusinessObjectItem[]; count?: number } | BusinessObjectItem[]>(
      '/system/business-objects/?page_size=200',
    )
    const items: BusinessObjectItem[] = Array.isArray(response)
      ? response
      : ((response as any).results ?? [])
    businessObjects.value = items.map((item: any) => ({
      code: item.code ?? item.object_code ?? '',
      name: item.name ?? item.object_name ?? item.code ?? '',
    }))
  } catch {
    // Non-fatal: designer still works, just the dropdown will be empty
    businessObjects.value = []
  } finally {
    loadingObjects.value = false
  }
}

onMounted(async () => {
  await loadBusinessObjects()

  if (isEdit.value) {
    try {
      const data = await getWorkflow(Number(route.params.id))
      Object.assign(form, data)
    } catch (e) {
      console.error('Failed to load workflow:', e)
    }
  }
})

const handleSave = async (graphData: any) => {
  if (!form.name || !form.code) {
    ElMessage.warning(t('system.workflow.messages.required'))
    return
  }
  form.graph_data = graphData

  try {
    if (isEdit.value) {
      await updateWorkflow(Number(route.params.id), form)
      ElMessage.success(t('system.workflow.messages.updateSuccess'))
    } else {
      await createWorkflow(form)
      ElMessage.success(t('system.workflow.messages.createSuccess'))
      router.back()
    }
  } catch (e: any) {
    ElMessage.error(e.message || t('system.workflow.messages.saveFailed'))
  }
}
</script>

<style scoped>
.workflow-edit {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.page-header {
  padding: 10px 20px;
  border-bottom: 1px solid #eee;
}

.form-container {
  padding: 10px 20px;
}

.designer-container {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>
