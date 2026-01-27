<template>
  <div class="workflow-edit">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? '编辑工作流' : '创建工作流'"
        @back="$router.back()"
      />
    </div>
    
    <div class="form-container">
      <el-form
        inline
        :model="form"
      >
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="业务对象">
          <el-select v-model="form.business_object">
            <el-option
              label="资产领用"
              value="asset_pickup"
            />
            <el-option
              label="资产调拨"
              value="asset_transfer"
            />
            <el-option
              label="资产退库"
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
import WorkflowDesigner from '@/components/workflow/WorkflowDesigner.vue'
import { createWorkflow, updateWorkflow, getWorkflow } from '@/api/workflows'

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
        ElMessage.warning('请填写名称和编码')
        return
    }
    form.graph_data = graphData
    
    try {
        if (isEdit.value) {
            await updateWorkflow(Number(route.params.id), form)
            ElMessage.success('更新成功')
        } else {
            await createWorkflow(form)
            ElMessage.success('创建成功')
            router.back()
        }
    } catch (e: any) {
        ElMessage.error(e.message || '保存失败')
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
