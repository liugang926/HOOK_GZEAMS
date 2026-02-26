<template>
  <div class="location-form">
    <div class="page-header">
      <el-page-header
        :title="isEdit ? t('assets.location.edit') : t('assets.location.create')"
        @back="goBack"
      />
      <div class="header-actions">
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ t('common.actions.save') }}
        </el-button>
      </div>
    </div>

    <el-card
      shadow="never"
      class="mt-4"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="t('assets.location.code')"
              prop="code"
            >
              <el-input
                v-model="form.code"
                :placeholder="t('assets.location.enterCode')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('assets.location.name')"
              prop="name"
            >
              <el-input
                v-model="form.name"
                :placeholder="t('assets.location.enterName')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item
              :label="t('assets.location.parent')"
              prop="parentId"
            >
              <el-tree-select
                v-model="form.parentId"
                :data="locationTree"
                :props="{ label: 'name', value: 'id' }"
                clearable
                check-strictly
                :placeholder="t('assets.location.selectParent')"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item
              :label="t('common.labels.status')"
              prop="isActive"
            >
              <el-switch
                v-model="form.isActive"
                :active-text="t('common.status.enabled')"
                :inactive-text="t('common.status.inactive')"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item
          :label="t('assets.location.sort')"
          prop="sortOrder"
        >
          <el-input-number
            v-model="form.sortOrder"
            :min="0"
            :max="9999"
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item
          :label="t('common.labels.description')"
          prop="description"
        >
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            :placeholder="t('common.placeholders.input', { field: t('assets.location.description') })"
          />
        </el-form-item>
        <el-form-item
          :label="t('common.labels.remark')"
          prop="remark"
        >
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="2"
            :placeholder="t('common.placeholders.input', { field: t('common.labels.remark') })"
          />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { createLocation, updateLocation, getLocationDetail, getLocationTree } from '@/api/assets/locations'

const { t } = useI18n()

const route = useRoute()
const router = useRouter()

const formRef = ref()
const submitting = ref(false)
const locationTree = ref([])

const form = reactive({
    id: null,
    code: '',
    name: '',
    parentId: null,
    description: '',
    remark: '',
    isActive: true,
    sortOrder: 0
})

const rules = {
    code: [{ required: true, message: t('assets.location.enterCode'), trigger: 'blur' }],
    name: [{ required: true, message: t('assets.location.enterName'), trigger: 'blur' }]
}

const isEdit = computed(() => !!route.params.id)

const fetchLocationTree = async () => {
    try {
        const res = await getLocationTree()
        locationTree.value = res || []
    } catch (e) {
        console.error(e)
    }
}

const handleSubmit = async () => {
    try {
        await formRef.value.validate()
        submitting.value = true

        const payload: any = {
            code: form.code,
            name: form.name,
            description: form.description,
            remark: form.remark,
            is_active: form.isActive,
            sort_order: form.sortOrder
        }

        if (form.parentId) {
            payload.parent_id = form.parentId
        }

        if (isEdit.value) {
            await updateLocation(String(route.params.id), payload)
            ElMessage.success(t('common.messages.updateSuccess'))
        } else {
            await createLocation(payload)
            ElMessage.success(t('common.messages.saveSuccess'))
        }
        goBack()
    } catch (e: any) {
        if (e !== false) {
            console.error(e)
            ElMessage.error(e.response?.data?.message || e.message || t('common.messages.operationFailed'))
        }
    } finally {
        submitting.value = false
    }
}

const goBack = () => {
    router.back()
}

onMounted(async () => {
    await fetchLocationTree()

    // Set parent from query param if creating new
    if (!isEdit.value && route.query.parent) {
        form.parentId = route.query.parent as string
    }

    if (isEdit.value) {
        try {
            const data = await getLocationDetail(String(route.params.id))
            form.id = data.id
            form.code = data.code
            form.name = data.name
            form.parentId = data.parent?.id
            form.description = data.description
            form.remark = data.remark
            form.isActive = data.is_active
            form.sortOrder = data.sort_order || 0
        } catch (e) {
            console.error(e)
            ElMessage.error(t('common.messages.loadFailed'))
            goBack()
        }
    }
})
</script>

<style scoped>
.location-form {
    padding: 20px;
}
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.mt-4 {
    margin-top: 20px;
}
</style>
