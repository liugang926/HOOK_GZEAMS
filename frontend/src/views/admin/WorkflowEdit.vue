<template>
  <div class="workflow-edit">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? $t('system.workflow.editTitle') : $t('system.workflow.createTitle')"
        @back="$router.back()"
      />
    </div>
    
    <div class="form-container">
      <el-form
        inline
        :model="form"
      >
        <el-form-item :label="$t('system.workflow.form.name')">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="$t('system.workflow.form.code')">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item :label="$t('system.workflow.form.businessObject')">
          <el-select v-model="form.business_object">
            <el-option
              :label="$t('system.workflow.businessObjects.asset_pickup')"
              value="asset_pickup"
            />
            <el-option
              :label="$t('system.workflow.businessObjects.asset_transfer')"
              value="asset_transfer"
            />
            <el-option
              :label="$t('system.workflow.businessObjects.asset_return')"
              value="asset_return"
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import WorkflowDesigner from '@/components/workflow/WorkflowDesigner.vue'
import { createWorkflow, updateWorkflow, getWorkflow } from '@/api/workflows'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const isEdit = computed(() => !!route.params.id)

const form = reactive({
    id: null,
    name: '',
    code: '',
    business_object: 'asset_pickup',
    graph_data: { nodes: [], edges: [] }
})

onMounted(async () => {
    if (isEdit.value) {
        // Load data
        try {
            const data = await getWorkflow(Number(route.params.id))
            Object.assign(form, data)
        } catch (e) {
            console.error(e)
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
