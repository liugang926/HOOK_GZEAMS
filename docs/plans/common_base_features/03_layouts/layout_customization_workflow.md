# 布局自定义工作流规范 (Layout Customization Workflow)

## 1. 工作流程概述

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

**注意**: 布局工作流相关模型（LayoutWorkflowConfig、LayoutWorkflowInstance 等）继承 BaseModel，用于管理 PageLayout 的草稿、审批和发布流程。

### 1.1 功能目标
布局自定义工作流定义了管理员从**创建草稿到发布生产**的完整布局生命周期管理流程，旨在实现：
- 布局草稿的可视化编辑与自动保存
- 布局发布的审批与版本控制
- 布局变更的全面追溯与回滚
- 布局权限的细粒度控制
- 跨组织的布局共享与导入导出

### 1.2 工作流生命周期

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       布局生命周期状态机                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   [草稿 Draft] ──────→ [待审批 Pending] ──────→ [已发布 Published]      │
│        │                     │                      │                   │
│        │ 编辑                │ 审批通过              │ 用户使用           │
│        │ 保存                │ 发布                  │                   │
│        ↓                     ↓                      ↓                   │
│   [草稿 Draft]         [已拒绝 Rejected]      [已归档 Archived]        │
│        │                     │                      │                   │
│        │ 继续编辑            │ 修改后重新提交        │ 重新激活           │
│        └─────────────────────┴──────────────────────┘                   │
│                              │                                          │
│                              ↓                                          │
│                         [已删除 Deleted]                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 参与角色与权限

| 角色 | 职责 | 权限 |
|------|------|------|
| **系统管理员** | 完全控制布局生命周期 | `view_layout`, `edit_layout`, `publish_layout`, `delete_layout`, `approve_layout` |
| **布局管理员** | 创建和编辑布局、提交发布 | `view_layout`, `edit_layout`, `publish_layout` |
| **审批人员** | 审批布局发布申请 | `view_layout`, `approve_layout` |
| **普通用户** | 查看已发布的布局 | `view_layout` |

### 1.4 工作流配置模型

```python
# apps/system/models.py
from django.db import models
from apps.common.models import BaseModel

class LayoutWorkflowConfig(BaseModel):
    """布局工作流配置"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='layout_workflow_configs',
        verbose_name='组织'
    )

    # 是否启用审批流程
    enable_approval = models.BooleanField(
        default=False,
        verbose_name='启用审批流程'
    )

    # 审批人员（多对多）
    approvers = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='pending_layout_approvals',
        verbose_name='审批人员'
    )

    # 自动发布规则
    auto_publish_roles = models.JSONField(
        default=list,
        verbose_name='自动发布角色',
        help_text='拥有这些角色的用户发布布局时无需审批'
    )

    # 版本号生成规则
    version_strategy = models.CharField(
        max_length=20,
        choices=[
            ('major_minor', '主版本.次版本 (如 1.0)'),
            ('semantic', '语义化版本 (如 1.0.0)'),
            ('timestamp', '时间戳版本 (如 202401151030)'),
        ],
        default='semantic',
        verbose_name='版本号策略'
    )

    # 最大草稿保存天数
    draft_retention_days = models.IntegerField(
        default=30,
        verbose_name='草稿保留天数'
    )

    # 是否启用自动保存
    enable_auto_save = models.BooleanField(
        default=True,
        verbose_name='启用自动保存'
    )

    # 自动保存间隔（秒）
    auto_save_interval = models.IntegerField(
        default=120,
        verbose_name='自动保存间隔（秒）'
    )

    class Meta:
        db_table = 'system_layout_workflow_config'
        verbose_name = '布局工作流配置'
        verbose_name_plural = '布局工作流配置'
        unique_together = [['organization']]

    def __str__(self):
        return f"{self.organization.name} - 布局工作流配置"
```

---

## 2. 布局草稿管理

### 2.1 草稿创建

#### 2.1.1 创建新布局草稿

**API 调用**:
```http
POST /api/system/page-layouts/
Content-Type: application/json

{
  "business_object": "Asset",
  "layout_type": "form",
  "layout_name": "资产表单布局",
  "description": "资产新增/编辑表单布局",
  "status": "draft",
  "config": {
    "sections": []
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "草稿创建成功",
  "data": {
    "id": "layout-uuid-v4",
    "business_object": "Asset",
    "layout_type": "form",
    "layout_name": "资产表单布局",
    "status": "draft",
    "version": "1.0.0-draft",
    "created_at": "2024-01-15T10:00:00Z",
    "created_by": {
      "id": "user-uuid",
      "username": "admin",
      "full_name": "系统管理员"
    }
  }
}
```

#### 2.1.2 复制现有布局为草稿

**API 调用**:
```http
POST /api/system/page-layouts/{id}/clone/
Content-Type: application/json

{
  "layout_name": "资产表单布局（副本）",
  "status": "draft"
}
```

**后端实现**:
```python
# apps/system/viewsets.py
@action(detail=True, methods=['post'])
def clone(self, request, pk=None):
    """克隆布局为新草稿"""
    original_layout = self.get_object()

    # 创建新草稿
    new_layout = PageLayout.objects.create(
        business_object=original_layout.business_object,
        layout_type=original_layout.layout_type,
        layout_name=request.data.get('layout_name', f"{original_layout.layout_name}（副本）"),
        description=request.data.get('description', original_layout.description),
        config=original_layout.config,
        status='draft',
        version='1.0.0-draft',
        organization=request.user.organization,
        created_by=request.user
    )

    serializer = self.get_serializer(new_layout)
    return Response(BaseResponse.success(
        message='布局克隆成功',
        data=serializer.data
    ))
```

### 2.2 草稿编辑

#### 2.2.1 自动保存机制

**前端实现** (Vue 3 Composition API):
```javascript
// composables/useAutoSave.js
import { ref, watch, onUnmounted } from 'vue'
import { debounce } from 'lodash-es'
import { ElMessage } from 'element-plus'

export function useAutoSave(layoutId, layoutConfig, autoSaveEnabled = true) {
  const isSaving = ref(false)
  const lastSavedAt = ref(null)
  const saveError = ref(null)
  let autoSaveTimer = null

  // 防抖保存函数
  const debouncedSave = debounce(async () => {
    if (!autoSaveEnabled.value || !layoutId.value) {
      return
    }

    isSaving.value = true
    saveError.value = null

    try {
      await api.system.pageLayouts.saveDraft(layoutId.value, {
        config: layoutConfig.value
      })

      lastSavedAt.value = new Date()
      ElMessage.success({
        message: '自动保存成功',
        duration: 2000,
        showClose: false
      })
    } catch (error) {
      saveError.value = error
      console.error('自动保存失败:', error)
    } finally {
      isSaving.value = false
    }
  }, 2000) // 2秒防抖延迟

  // 监听布局配置变化
  watch(
    layoutConfig,
    () => {
      debouncedSave()
    },
    { deep: true }
  )

  // 清理定时器
  onUnmounted(() => {
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer)
    }
    debouncedSave.cancel()
  })

  return {
    isSaving,
    lastSavedAt,
    saveError
  }
}
```

**在 LayoutDesigner 中使用**:
```vue
<script setup>
import { useAutoSave } from './composables/useAutoSave'

const layoutId = ref('layout-uuid')
const layoutConfig = ref({ sections: [] })

// 启用自动保存
const { isSaving, lastSavedAt, saveError } = useAutoSave(layoutId, layoutConfig)
</script>

<template>
  <div class="auto-save-indicator">
    <el-icon v-if="isSaving" class="is-loading"><Loading /></el-icon>
    <span v-if="lastSavedAt">
      上次保存: {{ formatTime(lastSavedAt) }}
    </span>
    <el-alert
      v-if="saveError"
      type="error"
      :closable="false"
      show-icon
    >
      自动保存失败，请手动保存
    </el-alert>
  </div>
</template>
```

#### 2.2.2 手动保存草稿

**前端实现**:
```javascript
const handleSaveDraft = async () => {
  try {
    // 验证配置
    const validation = validateLayoutSchema(layoutConfig.value)
    if (!validation.valid) {
      ElMessage.error(`布局配置无效: ${validation.errors.join(', ')}`)
      return
    }

    // 保存草稿
    await api.system.pageLayouts.saveDraft(layoutId.value, {
      config: layoutConfig.value,
      comment: saveComment.value
    })

    ElMessage.success('草稿保存成功')
    hasChanges.value = false
  } catch (error) {
    ElMessage.error('保存失败')
    console.error(error)
  }
}
```

### 2.3 草稿预览

#### 2.3.1 实时预览

**预览组件实现**:
```vue
<!-- components/LayoutPreview.vue -->
<template>
  <div class="layout-preview" :class="`preview-${responsiveMode}`">
    <!-- 设备切换 -->
    <div class="preview-toolbar">
      <el-radio-group v-model="responsiveMode" size="small">
        <el-radio-button label="desktop">
          <el-icon><Monitor /></el-icon>
          桌面端
        </el-radio-button>
        <el-radio-button label="tablet">
          <el-icon><Iphone /></el-icon>
          平板
        </el-radio-button>
        <el-radio-button label="mobile">
          <el-icon><Cellphone /></el-icon>
          移动端
        </el-radio-button>
      </el-radio-group>

      <el-switch
        v-model="showMockData"
        active-text="模拟数据"
        inactive-text="空数据"
      />
    </div>

    <!-- 布局渲染 -->
    <div class="preview-canvas">
      <DynamicForm
        v-if="layoutType === 'form'"
        :config="config"
        :business-object="businessObject"
        :preview-mode="true"
        :mock-data="showMockData ? mockFormData : {}"
      />

      <DynamicList
        v-else-if="layoutType === 'list'"
        :config="config"
        :business-object="businessObject"
        :preview-mode="true"
        :mock-data="showMockData ? mockListData : []"
      />

      <DynamicDetail
        v-else-if="layoutType === 'detail'"
        :config="config"
        :business-object="businessObject"
        :preview-mode="true"
        :mock-data="showMockData ? mockDetailData : {}"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import DynamicForm from '@/components/engine/DynamicForm.vue'
import DynamicList from '@/components/engine/DynamicList.vue'
import DynamicDetail from '@/components/engine/DynamicDetail.vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  businessObject: {
    type: String,
    required: true
  },
  layoutType: {
    type: String,
    required: true
  }
})

const responsiveMode = ref('desktop')
const showMockData = ref(true)

// 模拟数据
const mockFormData = ref({
  asset_code: 'ASSET2024001',
  asset_name: ' MacBook Pro 16英寸',
  category: '电子设备',
  status: '在用',
  purchase_date: '2024-01-10',
  original_value: 18999.00
})

const mockListData = ref([
  { id: 1, asset_code: 'ASSET2024001', asset_name: 'MacBook Pro', status: '在用' },
  { id: 2, asset_code: 'ASSET2024002', asset_name: 'iPhone 15', status: '在用' },
  { id: 3, asset_code: 'ASSET2024003', asset_name: 'iPad Pro', status: '闲置' }
])

const mockDetailData = ref({
  asset_code: 'ASSET2024001',
  asset_name: 'MacBook Pro 16英寸',
  specification: 'M3 Max / 64GB / 1TB',
  serial_number: 'C02XXXXXXXX',
  custodian: '张三',
  department: '技术部'
})
</script>

<style scoped lang="scss">
.layout-preview {
  min-height: 600px;
  background-color: #f5f7fa;
  padding: 24px;

  &.preview-desktop {
    max-width: 100%;
  }

  &.preview-tablet {
    max-width: 768px;
    margin: 0 auto;
    border: 1px solid #dcdfe6;
  }

  &.preview-mobile {
    max-width: 375px;
    margin: 0 auto;
    border: 1px solid #dcdfe6;
  }

  .preview-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px;
    background-color: #fff;
    border-radius: 4px;
  }

  .preview-canvas {
    background-color: #fff;
    border-radius: 4px;
    padding: 24px;
    min-height: 400px;
  }
}
</style>
```

### 2.4 草稿删除

#### 2.4.1 软删除草稿

**API 调用**:
```http
DELETE /api/system/page-layouts/{id}/
```

**后端实现**:
```python
def perform_destroy(self, instance):
    """软删除草稿"""
    if instance.status == 'published':
        raise PermissionDenied("已发布的布局不能直接删除，请先归档")

    # 调用 BaseModel 的软删除方法
    instance.soft_delete(self.request.user)
```

#### 2.4.2 批量删除草稿

**API 调用**:
```http
POST /api/system/page-layouts/batch-delete/
Content-Type: application/json

{
  "ids": ["uuid1", "uuid2", "uuid3"]
}
```

**响应**:
```json
{
  "success": true,
  "message": "批量删除完成",
  "summary": {
    "total": 3,
    "succeeded": 3,
    "failed": 0
  },
  "results": [
    {"id": "uuid1", "success": true},
    {"id": "uuid2", "success": true},
    {"id": "uuid3", "success": true}
  ]
}
```

---

## 3. 布局发布流程

### 3.1 发布前验证

#### 3.1.1 配置完整性验证

**验证器实现**:
```python
# apps/system/validators.py
from rest_framework.exceptions import ValidationError

def validate_layout_for_publish(config):
    """发布前验证布局配置"""

    errors = []

    # 1. 基础结构验证
    if not isinstance(config, dict):
        raise ValidationError("配置必须是 JSON 对象")

    if 'sections' not in config:
        errors.append("缺少 sections 字段")
    elif not config['sections'] or len(config['sections']) == 0:
        errors.append("布局至少需要一个区块")

    # 2. 字段引用验证
    from .models import FieldDefinition

    def validate_fields_in_sections(sections):
        for section in sections:
            if section.get('type') == 'section' and 'fields' in section:
                for field in section['fields']:
                    field_code = field.get('field_code')
                    if not FieldDefinition.objects.filter(code=field_code).exists():
                        errors.append(f"字段 {field_code} 不存在")

            elif section.get('type') == 'tab' and 'tabs' in section:
                for tab in section['tabs']:
                    if 'fields' in tab:
                        for field in tab['fields']:
                            field_code = field.get('field_code')
                            if not FieldDefinition.objects.filter(code=field_code).exists():
                                errors.append(f"字段 {field_code} 不存在")

    validate_fields_in_sections(config.get('sections', []))

    # 3. 布局逻辑验证
    def validate_section_logic(section):
        # 检查区块列数
        if section.get('type') == 'section':
            columns = section.get('columns', 1)
            if columns not in [1, 2, 3, 4]:
                errors.append(f"区块 {section.get('title')} 的列数必须是 1-4")

            # 检查字段列宽
            if 'fields' in section:
                total_span = sum(f.get('span', 12) for f in section['fields'])
                if total_span > 24:
                    errors.append(f"区块 {section.get('title')} 的字段总列宽超过 24")

    for section in config.get('sections', []):
        validate_section_logic(section)

    # 4. 必填字段验证
    required_fields = ['asset_code', 'asset_name']  # 根据业务对象定义
    field_codes_in_layout = set()

    def collect_field_codes(sections):
        for section in sections:
            if 'fields' in section:
                for field in section['fields']:
                    field_codes_in_layout.add(field.get('field_code'))
            if 'tabs' in section:
                for tab in section['tabs']:
                    if 'fields' in tab:
                        for field in tab['fields']:
                            field_codes_in_layout.add(field.get('field_code'))

    collect_field_codes(config.get('sections', []))

    missing_fields = set(required_fields) - field_codes_in_layout
    if missing_fields:
        errors.append(f"布局缺少必填字段: {', '.join(missing_fields)}")

    if errors:
        raise ValidationError({
            'code': 'LAYOUT_VALIDATION_ERROR',
            'message': '布局配置验证失败',
            'details': errors
        })

    return True
```

#### 3.1.2 前端实时验证

**前端验证 Hook**:
```javascript
// composables/useLayoutValidation.js
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export function useLayoutValidation(config) {
  const errors = ref([])
  const warnings = ref([])
  const isValid = computed(() => errors.value.length === 0)

  const validate = () => {
    errors.value = []
    warnings.value = []

    // 1. 基础验证
    if (!config.value.sections || config.value.sections.length === 0) {
      errors.value.push('布局至少需要一个区块')
      return { valid: false, errors: errors.value, warnings: warnings.value }
    }

    // 2. 区块验证
    config.value.sections.forEach((section, sIndex) => {
      if (!section.id) {
        errors.value.push(`区块 #${sIndex + 1} 缺少 ID`)
      }

      if (!section.type) {
        errors.value.push(`区块 ${section.id || '#' + (sIndex + 1)} 缺少类型`)
      }

      // 字段验证
      if (section.fields && section.fields.length > 0) {
        section.fields.forEach((field, fIndex) => {
          if (!field.field_code) {
            errors.value.push(`区块 ${section.title} 的字段 #${fIndex + 1} 缺少 field_code`)
          }

          if (!field.label) {
            warnings.value.push(`区块 ${section.title} 的字段 ${field.field_code} 缺少标签`)
          }

          if (field.span && (field.span < 1 || field.span > 24)) {
            errors.value.push(`字段 ${field.field_code} 的列宽必须在 1-24 之间`)
          }
        })

        // 列宽总和验证
        const totalSpan = section.fields.reduce((sum, field) => sum + (field.span || 12), 0)
        if (totalSpan > 24) {
          errors.value.push(`区块 ${section.title} 的字段总列宽 (${totalSpan}) 超过 24`)
        }
      }

      // 标签页验证
      if (section.type === 'tab' && section.tabs) {
        section.tabs.forEach((tab, tIndex) => {
          if (!tab.title) {
            errors.value.push(`标签页 #${tIndex + 1} 缺少标题`)
          }

          if (!tab.id) {
            warnings.value.push(`标签页 ${tab.title} 缺少 ID`)
          }
        })
      }
    })

    return {
      valid: errors.value.length === 0,
      errors: errors.value,
      warnings: warnings.value
    }
  }

  const validateBeforePublish = () => {
    const result = validate()

    if (!result.valid) {
      ElMessage.error({
        message: '布局验证失败，无法发布',
        description: result.errors.join('\n'),
        duration: 5000
      })
    } else if (result.warnings.length > 0) {
      ElMessage.warning({
        message: '布局存在警告',
        description: result.warnings.join('\n'),
        duration: 5000
      })
    }

    return result.valid
  }

  return {
    errors,
    warnings,
    isValid,
    validate,
    validateBeforePublish
  }
}
```

### 3.2 版本号生成规则

#### 3.2.1 语义化版本生成

**版本号生成器**:
```python
# apps/system/utils/version_generator.py
from datetime import datetime
from django.utils import timezone

class LayoutVersionGenerator:
    """布局版本号生成器"""

    def __init__(self, strategy='semantic'):
        self.strategy = strategy

    def generate_version(self, current_layout, new_config, old_config=None):
        """根据策略生成新版本号"""

        if self.strategy == 'semantic':
            return self._generate_semantic_version(current_layout, new_config, old_config)
        elif self.strategy == 'major_minor':
            return self._generate_major_minor_version(current_layout, new_config, old_config)
        elif self.strategy == 'timestamp':
            return self._generate_timestamp_version()
        else:
            return self._generate_semantic_version(current_layout, new_config, old_config)

    def _generate_semantic_version(self, current_layout, new_config, old_config):
        """语义化版本: 主版本.次版本.修订版 (如 1.0.0)"""
        current_version = current_layout.version or '0.0.0'

        # 移除 -draft 等后缀
        base_version = current_version.split('-')[0]
        major, minor, patch = map(int, base_version.split('.'))

        # 判断变更级别
        change_level = self._detect_change_level(new_config, old_config)

        if change_level == 'major':
            # 主版本: 布局结构重大变更
            return f"{major + 1}.0.0"
        elif change_level == 'minor':
            # 次版本: 新增字段或区块
            return f"{major}.{minor + 1}.0"
        else:
            # 修订版: 字段属性调整
            return f"{major}.{minor}.{patch + 1}"

    def _generate_major_minor_version(self, current_layout, new_config, old_config):
        """主次版本: 主版本.次版本 (如 1.0)"""
        current_version = current_layout.version or '0.0'
        base_version = current_version.split('-')[0]
        major, minor = map(int, base_version.split('.'))

        change_level = self._detect_change_level(new_config, old_config)

        if change_level in ['major', 'minor']:
            return f"{major + 1}.0"
        else:
            return f"{major}.{minor + 1}"

    def _generate_timestamp_version(self):
        """时间戳版本: YYYYMMDDHHMM (如 202401151030)"""
        return timezone.now().strftime('%Y%m%d%H%M')

    def _detect_change_level(self, new_config, old_config):
        """检测变更级别"""

        if not old_config:
            return 'major'

        old_sections = old_config.get('sections', [])
        new_sections = new_config.get('sections', [])

        # 检查区块数量变化
        if len(new_sections) != len(old_sections):
            return 'major'

        # 检查区块结构变化
        old_section_types = {s.get('type') for s in old_sections}
        new_section_types = {s.get('type') for s in new_sections}

        if old_section_types != new_section_types:
            return 'major'

        # 检查字段数量变化
        def count_fields(sections):
            count = 0
            for section in sections:
                if 'fields' in section:
                    count += len(section['fields'])
                if 'tabs' in section:
                    for tab in section['tabs']:
                        if 'fields' in tab:
                            count += len(tab['fields'])
            return count

        old_field_count = count_fields(old_sections)
        new_field_count = count_fields(new_sections)

        if new_field_count > old_field_count:
            return 'minor'
        elif new_field_count < old_field_count:
            return 'major'
        else:
            return 'patch'
```

**在 ViewSet 中使用**:
```python
@action(detail=True, methods=['post'])
def publish(self, request, pk=None):
    """发布布局"""
    layout = self.get_object()

    # 验证配置
    try:
        validate_layout_for_publish(request.data.get('config', layout.config))
    except ValidationError as e:
        return Response(BaseResponse.error(
            message='布局配置验证失败',
            details=e.detail
        ), status=status.HTTP_400_BAD_REQUEST)

    # 生成版本号
    from .utils.version_generator import LayoutVersionGenerator

    workflow_config = LayoutWorkflowConfig.objects.get(
        organization=request.user.organization
    )

    version_generator = LayoutVersionGenerator(
        strategy=workflow_config.version_strategy
    )

    old_config = layout.config if layout.status == 'published' else None
    new_version = version_generator.generate_version(
        layout,
        request.data.get('config', layout.config),
        old_config
    )

    # 更新布局
    layout.config = request.data.get('config', layout.config)
    layout.version = new_version
    layout.status = 'pending' if workflow_config.enable_approval else 'published'
    layout.parent_version = layout.version if layout.status == 'published' else None
    layout.published_at = timezone.now()
    layout.published_by = request.user
    layout.save()

    # 记录发布历史
    LayoutHistory.objects.create(
        layout=layout,
        version=new_version,
        config_snapshot=layout.config,
        published_by=request.user,
        action='publish'
    )

    serializer = self.get_serializer(layout)
    return Response(BaseResponse.success(
        message='布局提交发布成功' if layout.status == 'pending' else '布局发布成功',
        data=serializer.data
    ))
```

### 3.3 发布审批（可选）

#### 3.3.1 审批流程模型

```python
# apps/system/models.py
class LayoutApproval(BaseModel):
    """布局发布审批"""

    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]

    layout = models.ForeignKey(
        PageLayout,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='布局'
    )

    # 申请人
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='layout_applications',
        verbose_name='申请人'
    )

    # 审批人
    approver = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='layout_approvals_processed',
        verbose_name='审批人'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='审批状态'
    )

    # 申请说明
    comment = models.TextField(
        blank=True,
        verbose_name='申请说明'
    )

    # 审批意见
    approval_comment = models.TextField(
        blank=True,
        verbose_name='审批意见'
    )

    # 审批时间
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='审批时间'
    )

    class Meta:
        db_table = 'system_layout_approval'
        verbose_name = '布局审批'
        verbose_name_plural = '布局审批'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.layout.layout_name} - {self.get_status_display()}"

    def approve(self, approver, comment=''):
        """通过审批"""
        from django.utils import timezone

        self.status = 'approved'
        self.approver = approver
        self.approval_comment = comment
        self.approved_at = timezone.now()
        self.save()

        # 发布布局
        self.layout.status = 'published'
        self.layout.save()

        # 发送通知
        from .notifications import send_layout_publish_notification
        send_layout_publish_notification(self.layout, self.applicant)

    def reject(self, approver, comment):
        """拒绝审批"""
        from django.utils import timezone

        self.status = 'rejected'
        self.approver = approver
        self.approval_comment = comment
        self.approved_at = timezone.now()
        self.save()

        # 布局状态回退为草稿
        self.layout.status = 'draft'
        self.layout.save()

        # 发送通知
        from .notifications import send_layout_rejection_notification
        send_layout_rejection_notification(self.layout, self.applicant, comment)
```

#### 3.3.2 审批 ViewSet

```python
# apps/system/viewsets.py
class LayoutApprovalViewSet(BaseModelViewSet):
    """布局审批视图集"""

    queryset = LayoutApproval.objects.all()
    serializer_class = LayoutApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """获取待审批列表"""
        queryset = super().get_queryset()

        # 仅显示本组织的审批
        queryset = queryset.filter(layout__organization=self.request.user.organization)

        # 过滤状态
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # 审批人只能看到待自己审批的记录
        if not self.request.user.is_admin:
            queryset = queryset.filter(
                approvers__in=[self.request.user]
            )

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """通过审批"""
        approval = self.get_object()

        if approval.status != 'pending':
            return Response(BaseResponse.error(
                message=f'该审批申请已被{approval.get_status_display()}'
            ), status=status.HTTP_400_BAD_REQUEST)

        # 执行审批
        approval.approve(request.user, request.data.get('comment', ''))

        serializer = self.get_serializer(approval)
        return Response(BaseResponse.success(
            message='审批通过',
            data=serializer.data
        ))

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """拒绝审批"""
        approval = self.get_object()

        if approval.status != 'pending':
            return Response(BaseResponse.error(
                message=f'该审批申请已被{approval.get_status_display()}'
            ), status=status.HTTP_400_BAD_REQUEST)

        comment = request.data.get('comment', '')
        if not comment:
            return Response(BaseResponse.error(
                message='请填写拒绝原因'
            ), status=status.HTTP_400_BAD_REQUEST)

        # 执行拒绝
        approval.reject(request.user, comment)

        serializer = self.get_serializer(approval)
        return Response(BaseResponse.success(
            message='已拒绝审批申请',
            data=serializer.data
        ))

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消审批申请"""
        approval = self.get_object()

        if approval.status != 'pending':
            return Response(BaseResponse.error(
                message='只能取消待审批的申请'
            ), status=status.HTTP_400_BAD_REQUEST)

        if approval.applicant != request.user:
            return Response(BaseResponse.error(
                message='只能取消自己的申请'
            ), status=status.HTTP_403_FORBIDDEN)

        approval.status = 'cancelled'
        approval.save()

        # 布局状态回退为草稿
        approval.layout.status = 'draft'
        approval.layout.save()

        serializer = self.get_serializer(approval)
        return Response(BaseResponse.success(
            message='已取消审批申请',
            data=serializer.data
        ))
```

### 3.4 发布操作

#### 3.4.1 前端发布对话框

```vue
<!-- components/PublishDialog.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="发布布局"
    width="600px"
    :close-on-click-modal="false"
    @before-close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="120px"
    >
      <!-- 布局信息 -->
      <el-form-item label="布局名称">
        <el-tag>{{ layout?.layout_name }}</el-tag>
      </el-form-item>

      <el-form-item label="布局类型">
        <el-tag type="info">{{ layout?.layout_type_display }}</el-tag>
      </el-form-item>

      <el-form-item label="当前版本">
        <el-tag type="warning">{{ layout?.version }}</el-tag>
      </el-form-item>

      <!-- 新版本号 -->
      <el-form-item label="新版本号" prop="version">
        <el-input
          v-model="formData.version"
          placeholder="自动生成或手动输入"
          :readonly="autoVersion"
        >
          <template #prepend>
            <el-checkbox v-model="autoVersion">自动</el-checkbox>
          </template>
        </el-input>
        <div class="form-tip">
          系统将根据变更内容自动生成版本号，也可手动指定
        </div>
      </el-form-item>

      <!-- 变更说明 -->
      <el-form-item label="变更说明" prop="comment">
        <el-input
          v-model="formData.comment"
          type="textarea"
          :rows="4"
          placeholder="请描述本次布局变更的内容和原因"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 审批选项 -->
      <el-form-item v-if="enableApproval" label="提交审批">
        <el-switch
          v-model="formData.requireApproval"
          active-text="是"
          inactive-text="否"
        />
        <div class="form-tip">
          启用后，布局需要审批人员批准后才能发布到生产环境
        </div>
      </el-form-item>

      <!-- 验证警告 -->
      <el-alert
        v-if="validationWarnings.length > 0"
        type="warning"
        :closable="false"
        show-icon
        title="布局验证警告"
      >
        <ul>
          <li v-for="(warning, index) in validationWarnings" :key="index">
            {{ warning }}
          </li>
        </ul>
      </el-alert>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="publishing"
          @click="handlePublish"
        >
          {{ formData.requireApproval ? '提交审批' : '确认发布' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  layout: {
    type: Object,
    default: null
  },
  validationWarnings: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const publishing = ref(false)
const autoVersion = ref(true)
const enableApproval = ref(false)

const formData = ref({
  version: '',
  comment: '',
  requireApproval: false
})

const formRules = {
  comment: [
    { required: true, message: '请填写变更说明', trigger: 'blur' }
  ]
}

// 监听布局变化，生成版本号
watch(
  () => props.layout,
  (newLayout) => {
    if (newLayout && autoVersion.value) {
      // 调用 API 生成版本号
      generateVersion()
    }

    // 检查是否启用审批
    if (newLayout) {
      checkApprovalEnabled()
    }
  },
  { immediate: true }
)

const generateVersion = async () => {
  try {
    const response = await api.system.pageLayouts.generateVersion(props.layout.id)
    formData.value.version = response.data.version
  } catch (error) {
    console.error('生成版本号失败:', error)
  }
}

const checkApprovalEnabled = async () => {
  try {
    const response = await api.system.pageLayouts.checkApprovalRequired(props.layout.id)
    enableApproval.value = response.data.enabled
    formData.value.requireApproval = response.data.enabled
  } catch (error) {
    console.error('检查审批配置失败:', error)
  }
}

const handlePublish = async () => {
  try {
    await formRef.value.validate()

    publishing.value = true

    await api.system.pageLayouts.publish(props.layout.id, {
      version: formData.value.version,
      comment: formData.value.comment,
      require_approval: formData.value.requireApproval
    })

    ElMessage.success(
      formData.value.requireApproval ? '提交审批成功' : '布局发布成功'
    )

    emit('confirm')
    visible.value = false
  } catch (error) {
    if (error.response?.status === 400) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('发布失败，请稍后重试')
    }
  } finally {
    publishing.value = false
  }
}

const handleClose = () => {
  formRef.value?.resetFields()
  visible.value = false
}
</script>

<style scoped lang="scss">
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
```

### 3.5 发布回滚

#### 3.5.1 版本回滚 API

**API 调用**:
```http
POST /api/system/page-layouts/{id}/rollback/
Content-Type: application/json

{
  "version": "1.0.0",
  "comment": "回滚到稳定版本"
}
```

**后端实现**:
```python
@action(detail=True, methods=['post'])
def rollback(self, request, pk=None):
    """回滚到指定版本"""
    layout = self.get_object()
    target_version = request.data.get('version')

    if not target_version:
        return Response(BaseResponse.error(
            message='请指定要回滚的版本号'
        ), status=status.HTTP_400_BAD_REQUEST)

    # 查找历史版本
    try:
        history = LayoutHistory.objects.get(
            layout=layout,
            version=target_version,
            action='publish'
        )
    except LayoutHistory.DoesNotExist:
        return Response(BaseResponse.error(
            message=f'版本 {target_version} 不存在'
        ), status=status.HTTP_404_NOT_FOUND)

    # 备份当前版本
    current_version = layout.version
    current_config = layout.config

    # 执行回滚
    layout.config = history.config_snapshot
    layout.parent_version = current_version
    layout.version = f"{target_version}-rollback-{int(timezone.now().timestamp())}"
    layout.status = 'published'
    layout.save()

    # 记录回滚操作
    LayoutHistory.objects.create(
        layout=layout,
        version=layout.version,
        config_snapshot=current_config,
        published_by=request.user,
        action='rollback',
        comment=request.data.get('comment', f'回滚到版本 {target_version}')
    )

    serializer = self.get_serializer(layout)
    return Response(BaseResponse.success(
        message=f'已回滚到版本 {target_version}',
        data=serializer.data
    ))
```

---

## 4. 布局版本管理

### 4.1 版本历史查看

#### 4.1.1 版本历史列表

**API 调用**:
```http
GET /api/system/page-layouts/{id}/versions/
```

**响应**:
```json
{
  "success": true,
  "data": {
    "count": 10,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "history-uuid",
        "version": "1.2.0",
        "action": "publish",
        "action_display": "发布",
        "config_snapshot": { /* 完整配置快照 */ },
        "published_by": {
          "id": "user-uuid",
          "username": "admin",
          "full_name": "系统管理员"
        },
        "created_at": "2024-01-15T10:30:00Z",
        "comment": "优化字段分组和排列"
      }
    ]
  }
}
```

#### 4.1.2 前端版本历史组件

```vue
<!-- components/LayoutVersionHistory.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="版本历史"
    width="900px"
  >
    <!-- 时间线展示 -->
    <el-timeline>
      <el-timeline-item
        v-for="history in versions"
        :key="history.id"
        :timestamp="formatTime(history.created_at)"
        placement="top"
        :type="getTimelineType(history.action)"
        :icon="getTimelineIcon(history.action)"
      >
        <el-card>
          <div class="version-header">
            <el-tag :type="getVersionTagType(history.action)">
              {{ history.version }}
            </el-tag>
            <el-tag type="info">{{ history.action_display }}</el-tag>
          </div>

          <div class="version-info">
            <div class="info-item">
              <el-icon><User /></el-icon>
              <span>{{ history.published_by?.full_name || history.published_by?.username }}</span>
            </div>

            <div v-if="history.comment" class="info-item">
              <el-icon><Document /></el-icon>
              <span>{{ history.comment }}</span>
            </div>
          </div>

          <div class="version-actions">
            <el-button
              size="small"
              @click="handleViewConfig(history)"
            >
              查看配置
            </el-button>

            <el-button
              v-if="history.action === 'publish'"
              size="small"
              type="warning"
              @click="handleRollback(history)"
            >
              回滚到此版本
            </el-button>

            <el-button
              size="small"
              @click="handleCompare(history)"
            >
              对比
            </el-button>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>

    <!-- 配置查看对话框 -->
    <el-dialog
      v-model="configVisible"
      title="配置详情"
      width="700px"
      append-to-body
    >
      <pre class="config-json">{{ formatJSON(selectedHistory?.config_snapshot) }}</pre>
    </el-dialog>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  layoutId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'rollback'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const versions = ref([])
const configVisible = ref(false)
const selectedHistory = ref(null)

const loadVersions = async () => {
  try {
    const response = await api.system.pageLayouts.listVersions(props.layoutId)
    versions.value = response.data.results
  } catch (error) {
    ElMessage.error('加载版本历史失败')
  }
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

const getTimelineType = (action) => {
  const types = {
    'publish': 'success',
    'update': 'primary',
    'rollback': 'warning'
  }
  return types[action] || 'info'
}

const getTimelineIcon = (action) => {
  const icons = {
    'publish': 'CircleCheck',
    'update': 'Edit',
    'rollback': 'RefreshLeft'
  }
  return icons[action] || 'Document'
}

const getVersionTagType = (action) => {
  const types = {
    'publish': 'success',
    'update': 'primary',
    'rollback': 'warning'
  }
  return types[action] || 'info'
}

const handleViewConfig = (history) => {
  selectedHistory.value = history
  configVisible.value = true
}

const formatJSON = (obj) => {
  return JSON.stringify(obj, null, 2)
}

const handleRollback = async (history) => {
  try {
    await ElMessageBox.confirm(
      `确定要回滚到版本 ${history.version} 吗？当前版本将被备份。`,
      '回滚确认',
      {
        confirmButtonText: '确定回滚',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.system.pageLayouts.rollback(props.layoutId, {
      version: history.version
    })

    ElMessage.success(`已回滚到版本 ${history.version}`)
    emit('rollback', history)
    visible.value = false
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('回滚失败')
    }
  }
}

const handleCompare = (history) => {
  // 打开版本对比对话框
  emit('compare', history)
}

// 监听对话框打开
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      loadVersions()
    }
  }
)
</script>

<style scoped lang="scss">
.version-header {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.version-info {
  margin: 12px 0;

  .info-item {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 8px;
    font-size: 14px;
    color: #606266;
  }
}

.version-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.config-json {
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  max-height: 500px;
  overflow-y: auto;
}
</style>
```

### 4.2 版本对比

#### 4.2.1 版本对比组件

```vue
<!-- components/LayoutVersionCompare.vue -->
<template>
  <el-dialog
    v-model="visible"
    title="版本对比"
    width="1200px"
  >
    <div class="compare-header">
      <div class="version-selector">
        <span>对比版本:</span>
        <el-select
          v-model="compareVersion"
          placeholder="选择版本"
          @change="loadCompareVersion"
        >
          <el-option
            v-for="version in availableVersions"
            :key="version.id"
            :label="`${version.version} (${formatTime(version.created_at)})`"
            :value="version.version"
          />
        </el-select>
      </div>
    </div>

    <div class="compare-content">
      <div class="compare-panel">
        <div class="panel-header">
          <h4>当前版本 ({{ currentVersion }})</h4>
        </div>
        <div class="panel-body">
          <vue-json-compare
            :old-data="compareConfig"
            :new-data="currentConfig"
            :no-change="(a, b) => JSON.stringify(a) === JSON.stringify(b)"
          />
        </div>
      </div>
    </div>

    <div class="compare-legend">
      <div class="legend-item">
        <span class="legend-color added"></span>
        <span>新增</span>
      </div>
      <div class="legend-item">
        <span class="legend-color modified"></span>
        <span>修改</span>
      </div>
      <div class="legend-item">
        <span class="legend-color deleted"></span>
        <span>删除</span>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '@/api'
import VueJsonCompare from 'vue-json-compare'
import 'vue-json-compare/lib/vue-json-compare.css'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  layoutId: {
    type: String,
    required: true
  },
  currentConfig: {
    type: Object,
    required: true
  },
  currentVersion: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const availableVersions = ref([])
const compareVersion = ref('')
const compareConfig = ref(null)

const loadVersions = async () => {
  try {
    const response = await api.system.pageLayouts.listVersions(props.layoutId)
    availableVersions.value = response.data.results.filter(
      v => v.version !== props.currentVersion && v.action === 'publish'
    )

    if (availableVersions.value.length > 0) {
      compareVersion.value = availableVersions.value[0].version
      loadCompareVersion()
    }
  } catch (error) {
    console.error('加载版本列表失败:', error)
  }
}

const loadCompareVersion = async () => {
  const history = availableVersions.value.find(
    v => v.version === compareVersion.value
  )

  if (history) {
    compareConfig.value = history.config_snapshot
  }
}

const formatTime = (time) => {
  return new Date(time).toLocaleDateString('zh-CN')
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      loadVersions()
    }
  }
)
</script>

<style scoped lang="scss">
.compare-header {
  margin-bottom: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;

  .version-selector {
    display: flex;
    align-items: center;
    gap: 12px;

    span {
      font-weight: 500;
    }
  }
}

.compare-content {
  .compare-panel {
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    overflow: hidden;

    .panel-header {
      padding: 12px 16px;
      background-color: #f5f7fa;
      border-bottom: 1px solid #dcdfe6;

      h4 {
        margin: 0;
        font-size: 14px;
        font-weight: 500;
      }
    }

    .panel-body {
      padding: 16px;
      max-height: 600px;
      overflow-y: auto;
    }
  }
}

.compare-legend {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;

    .legend-color {
      width: 16px;
      height: 16px;
      border-radius: 2px;

      &.added {
        background-color: #67c23a;
      }

      &.modified {
        background-color: #e6a23c;
      }

      &.deleted {
        background-color: #f56c6c;
      }
    }
  }
}

// JSON Compare 样式覆盖
:deep(.json-compare) {
  .added {
    background-color: rgba(103, 194, 58, 0.2);
  }

  .modified {
    background-color: rgba(230, 162, 60, 0.2);
  }

  .deleted {
    background-color: rgba(245, 108, 108, 0.2);
    text-decoration: line-through;
  }
}
</style>
```

### 4.3 版本分支（未来规划）

#### 4.3.1 分支创建策略

```
                    [main]
                       │
        ┌──────────────┼──────────────┐
        │              │              │
    v1.0.0          v1.1.0          v1.2.0
        │              │              │
        │         ┌────┴────┐         │
        │         │         │         │
    feature-a  feature-b  feature-c
        │         │         │         │
        └─────────┴─────────┴─────────┘
                    │
                 merge
```

**分支模型扩展**:
```python
class LayoutBranch(BaseModel):
    """布局版本分支"""

    BRANCH_TYPE_CHOICES = [
        ('feature', '功能分支'),
        ('hotfix', '热修复分支'),
        ('experiment', '实验分支'),
    ]

    layout = models.ForeignKey(
        PageLayout,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name='布局'
    )

    branch_name = models.CharField(
        max_length=100,
        verbose_name='分支名称'
    )

    branch_type = models.CharField(
        max_length=20,
        choices=BRANCH_TYPE_CHOICES,
        default='feature',
        verbose_name='分支类型'
    )

    base_version = models.CharField(
        max_length=20,
        verbose_name='基础版本'
    )

    config = models.JSONField(
        verbose_name='分支配置'
    )

    is_merged = models.BooleanField(
        default=False,
        verbose_name='是否已合并'
    )

    class Meta:
        db_table = 'system_layout_branch'
        verbose_name = '布局分支'
        verbose_name_plural = '布局分支'
        ordering = ['-created_at']
```

---

## 5. 布局权限控制

### 5.1 权限模型设计

#### 5.1.1 布局权限定义

```python
# apps/system/permissions.py
from rest_framework import permissions

class LayoutPermission(permissions.BasePermission):
    """布局权限控制"""

    # 权限映射
    PERMISSION_MAP = {
        'list': 'view_layout',
        'retrieve': 'view_layout',
        'create': 'edit_layout',
        'update': 'edit_layout',
        'partial_update': 'edit_layout',
        'destroy': 'delete_layout',
        'save_draft': 'edit_layout',
        'publish': 'publish_layout',
        'set_default': 'publish_layout',
        'rollback': 'delete_layout',
        'versions': 'view_layout',
    }

    def has_permission(self, request, view):
        """基础权限检查"""
        if not request.user or not request.user.is_authenticated:
            return False

        # 系统管理员拥有所有权限
        if request.user.is_admin:
            return True

        # 获取所需权限
        required_permission = self.PERMISSION_MAP.get(view.action)
        if not required_permission:
            return False

        # 检查用户权限
        return self._check_permission(request.user, required_permission)

    def has_object_permission(self, request, view, obj):
        """对象级权限检查"""
        # 系统管理员拥有所有权限
        if request.user.is_admin:
            return True

        # 只能操作本组织的布局
        if obj.organization_id != request.user.organization_id:
            return False

        # 获取所需权限
        required_permission = self.PERMISSION_MAP.get(view.action)
        if not required_permission:
            return True

        # 检查用户权限
        return self._check_permission(request.user, required_permission)

    def _check_permission(self, user, permission_code):
        """检查用户是否拥有指定权限"""
        # 从用户角色权限中查找
        from accounts.models import Permission

        return Permission.objects.filter(
            code=permission_code,
            organization=user.organization,
            roles__users=user
        ).exists()
```

#### 5.1.2 权限初始化数据

```python
# apps/system/data/permissions.py

LAYOUT_PERMISSIONS = [
    {
        'code': 'view_layout',
        'name': '查看布局',
        'description': '查看页面布局配置和版本历史',
        'module': 'system',
        'category': 'layout'
    },
    {
        'code': 'edit_layout',
        'name': '编辑布局',
        'description': '创建、编辑页面布局草稿',
        'module': 'system',
        'category': 'layout'
    },
    {
        'code': 'publish_layout',
        'name': '发布布局',
        'description': '发布页面布局到生产环境',
        'module': 'system',
        'category': 'layout'
    },
    {
        'code': 'approve_layout',
        'name': '审批布局',
        'description': '审批布局发布申请',
        'module': 'system',
        'category': 'layout'
    },
    {
        'code': 'delete_layout',
        'name': '删除布局',
        'description': '删除页面布局和版本历史',
        'module': 'system',
        'category': 'layout'
    },
    {
        'code': 'manage_layout',
        'name': '管理布局',
        'description': '完全控制布局生命周期（设置默认、导入导出）',
        'module': 'system',
        'category': 'layout'
    }
]

# 默认角色权限映射
DEFAULT_ROLE_PERMISSIONS = {
    '系统管理员': [
        'view_layout', 'edit_layout', 'publish_layout',
        'approve_layout', 'delete_layout', 'manage_layout'
    ],
    '布局管理员': [
        'view_layout', 'edit_layout', 'publish_layout'
    ],
    '审批人员': [
        'view_layout', 'approve_layout'
    ],
    '普通用户': [
        'view_layout'
    ]
}
```

### 5.2 权限检查中间件

#### 5.2.1 前端权限指令

```javascript
// directives/permission.js
import { useUserStore } from '@/stores/user'

export default {
  mounted(el, binding) {
    const { value } = binding
    const userStore = useUserStore()
    const permissions = userStore.permissions || []

    if (value && value instanceof Array && value.length > 0) {
      const hasPermission = permissions.some(permission => {
        return value.includes(permission)
      })

      if (!hasPermission) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      throw new Error('需要指定权限！如 v-permission="[\'edit_layout\']"')
    }
  }
}

// main.js 注册
import permission from '@/directives/permission'
app.directive('permission', permission)
```

**使用示例**:
```vue
<template>
  <el-button
    v-permission="['edit_layout']"
    @click="handleEdit"
  >
    编辑布局
  </el-button>

  <el-button
    v-permission="['publish_layout']"
    type="primary"
    @click="handlePublish"
  >
    发布
  </el-button>
</template>
```

#### 5.2.2 前端权限 Hook

```javascript
// hooks/usePermission.js
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

export function usePermission() {
  const userStore = useUserStore()

  const permissions = computed(() => userStore.permissions || [])

  const hasPermission = (permissionCodes) => {
    if (!permissionCodes || permissionCodes.length === 0) {
      return true
    }

    return permissionCodes.some(code => permissions.value.includes(code))
  }

  const hasAllPermissions = (permissionCodes) => {
    if (!permissionCodes || permissionCodes.length === 0) {
      return true
    }

    return permissionCodes.every(code => permissions.value.includes(code))
  }

  const hasAnyPermission = (permissionCodes) => {
    return hasPermission(permissionCodes)
  }

  return {
    permissions,
    hasPermission,
    hasAllPermissions,
    hasAnyPermission
  }
}
```

**使用示例**:
```vue
<script setup>
import { usePermission } from '@/hooks/usePermission'

const { hasPermission } = usePermission()

const canEdit = computed(() => hasPermission(['edit_layout']))
const canPublish = computed(() => hasPermission(['publish_layout']))
</script>

<template>
  <div>
    <el-button v-if="canEdit" @click="handleEdit">编辑</el-button>
    <el-button v-if="canPublish" type="primary" @click="handlePublish">
      发布
    </el-button>
  </div>
</template>
```

---

## 6. 布局变更通知

### 6.1 通知模型

```python
# apps/system/models.py
class LayoutNotification(BaseModel):
    """布局变更通知"""

 NOTIFICATION_TYPE_CHOICES = [
        ('publish', '布局发布'),
        ('update', '布局更新'),
        ('rollback', '版本回滚'),
        ('approval_pending', '待审批'),
        ('approval_approved', '审批通过'),
        ('approval_rejected', '审批拒绝'),
    ]

    layout = models.ForeignKey(
        PageLayout,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='布局'
    )

    # 通知类型
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='通知类型'
    )

    # 接收人
    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='layout_notifications',
        verbose_name='接收人'
    )

    # 是否已读
    is_read = models.BooleanField(
        default=False,
        verbose_name='是否已读'
    )

    # 通知内容
    title = models.CharField(
        max_length=200,
        verbose_name='通知标题'
    )

    message = models.TextField(
        verbose_name='通知内容'
    )

    # 相关数据（JSONB）
    extra_data = models.JSONField(
        default=dict,
        verbose_name='额外数据'
    )

    class Meta:
        db_table = 'system_layout_notification'
        verbose_name = '布局通知'
        verbose_name_plural = '布局通知'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"
```

### 6.2 通知发送服务

```python
# apps/system/services/notification_service.py
from django.utils import timezone
from .models import LayoutNotification, PageLayout

class LayoutNotificationService:
    """布局通知服务"""

    @staticmethod
    def send_publish_notification(layout, recipients):
        """发送布局发布通知"""
        notifications = []

        for recipient in recipients:
            notification = LayoutNotification.objects.create(
                layout=layout,
                notification_type='publish',
                recipient=recipient,
                title=f'布局 {layout.layout_name} 已发布',
                message=f'布局 "{layout.layout_name}" 已发布到生产环境，版本: {layout.version}',
                extra_data={
                    'layout_id': str(layout.id),
                    'layout_name': layout.layout_name,
                    'version': layout.version,
                    'layout_type': layout.layout_type,
                    'published_by': {
                        'id': str(layout.published_by.id),
                        'username': layout.published_by.username
                    } if layout.published_by else None
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def send_approval_notification(layout_approval):
        """发送审批通知"""
        # 通知审批人员
        workflow_config = LayoutWorkflowConfig.objects.get(
            organization=layout_approval.layout.organization
        )

        notifications = []

        for approver in workflow_config.approvers.all():
            notification = LayoutNotification.objects.create(
                layout=layout_approval.layout,
                notification_type='approval_pending',
                recipient=approver,
                title=f'布局发布申请待审批',
                message=f'{layout_approval.applicant.get_full_name()} 提交了布局 "{layout_approval.layout.layout_name}" 的发布申请，请及时审批。',
                extra_data={
                    'approval_id': str(layout_approval.id),
                    'layout_id': str(layout_approval.layout.id),
                    'applicant': {
                        'id': str(layout_approval.applicant.id),
                        'name': layout_approval.applicant.get_full_name()
                    },
                    'comment': layout_approval.comment
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def send_approval_result_notification(layout_approval, approved):
        """发送审批结果通知"""
        notification_type = 'approval_approved' if approved else 'approval_rejected'
        title = '布局发布申请已通过' if approved else '布局发布申请已拒绝'
        message = f'您提交的布局 "{layout_approval.layout.layout_name}" 发布申请已被{layout_approval.approver.get_full_name()}{"通过" if approved else "拒绝"}。'

        if not approved and layout_approval.approval_comment:
            message += f'\n拒绝原因: {layout_approval.approval_comment}'

        notification = LayoutNotification.objects.create(
            layout=layout_approval.layout,
            notification_type=notification_type,
            recipient=layout_approval.applicant,
            title=title,
            message=message,
            extra_data={
                'approval_id': str(layout_approval.id),
                'layout_id': str(layout_approval.layout.id),
                'approver': {
                    'id': str(layout_approval.approver.id),
                    'name': layout_approval.approver.get_full_name()
                },
                'comment': layout_approval.approval_comment
            }
        )

        return notification

    @staticmethod
    def send_rollback_notification(layout, target_version, operator):
        """发送版本回滚通知"""
        # 通知所有有权限查看布局的用户
        from apps.accounts.models import User
        from apps.accounts.models import Permission

        view_permission = Permission.objects.get(code='view_layout')
        recipients = User.objects.filter(
            organization=layout.organization,
            roles__permissions=view_permission,
            is_active=True
        ).distinct()

        notifications = []

        for recipient in recipients:
            notification = LayoutNotification.objects.create(
                layout=layout,
                notification_type='rollback',
                recipient=recipient,
                title=f'布局已回滚到版本 {target_version}',
                message=f'布局 "{layout.layout_name}" 已被 {operator.get_full_name()} 回滚到版本 {target_version}',
                extra_data={
                    'layout_id': str(layout.id),
                    'layout_name': layout.layout_name,
                    'target_version': target_version,
                    'operator': {
                        'id': str(operator.id),
                        'name': operator.get_full_name()
                    }
                }
            )
            notifications.append(notification)

        return notifications

    @staticmethod
    def mark_as_read(notification_id, user):
        """标记通知为已读"""
        try:
            notification = LayoutNotification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.is_read = True
            notification.save(update_fields=['is_read'])
            return True
        except LayoutNotification.DoesNotExist:
            return False

    @staticmethod
    def mark_all_as_read(user):
        """标记所有通知为已读"""
        LayoutNotification.objects.filter(
            recipient=user,
            is_read=False
        ).update(is_read=True)
```

### 6.3 前端通知组件

```vue
<!-- components/LayoutNotificationCenter.vue -->
<template>
  <div class="notification-center">
    <!-- 通知铃铛 -->
    <el-badge
      :value="unreadCount"
      :hidden="unreadCount === 0"
      class="notification-badge"
    >
      <el-button
        :icon="Bell"
        circle
        @click="handleClick"
      />
    </el-badge>

    <!-- 通知面板 -->
    <el-popover
      v-model:visible="visible"
      placement="bottom-end"
      :width="400"
      trigger="click"
    >
      <template #reference>
        <div></div>
      </template>

      <div class="notification-panel">
        <div class="panel-header">
          <h4>通知中心</h4>
          <el-button
            link
            size="small"
            @click="handleMarkAllRead"
          >
            全部已读
          </el-button>
        </div>

        <el-scrollbar max-height="400px">
          <div v-if="notifications.length === 0" class="empty-state">
            <el-empty description="暂无通知" :image-size="60" />
          </div>

          <div v-else class="notification-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="{ 'is-unread': !notification.is_read }"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon">
                <el-icon
                  :color="getNotificationColor(notification.notification_type)"
                >
                  <component :is="getNotificationIcon(notification.notification_type)" />
                </el-icon>
              </div>

              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-time">
                  {{ formatTime(notification.created_at) }}
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>

        <div class="panel-footer">
          <el-button
            link
            size="small"
            @click="handleViewAll"
          >
            查看全部通知
          </el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bell, CircleCheck, CircleClose, RefreshLeft, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const visible = ref(false)
const notifications = ref([])

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

const loadNotifications = async () => {
  try {
    const response = await api.system.layoutNotifications.list({
      is_read: false,
      page_size: 10
    })
    notifications.value = response.data.results
  } catch (error) {
    console.error('加载通知失败:', error)
  }
}

const getNotificationIcon = (type) => {
  const icons = {
    'publish': CircleCheck,
    'update': InfoFilled,
    'rollback': RefreshLeft,
    'approval_pending': InfoFilled,
    'approval_approved': CircleCheck,
    'approval_rejected': CircleClose
  }
  return icons[type] || InfoFilled
}

const getNotificationColor = (type) => {
  const colors = {
    'publish': '#67c23a',
    'update': '#409eff',
    'rollback': '#e6a23c',
    'approval_pending': '#409eff',
    'approval_approved': '#67c23a',
    'approval_rejected': '#f56c6c'
  }
  return colors[type] || '#909399'
}

const formatTime = (time) => {
  const now = new Date()
  const notificationTime = new Date(time)
  const diff = now - notificationTime

  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return notificationTime.toLocaleDateString('zh-CN')
  }
}

const handleNotificationClick = async (notification) => {
  // 标记为已读
  if (!notification.is_read) {
    await api.system.layoutNotifications.markAsRead(notification.id)
    notification.is_read = true
  }

  // 跳转到相关页面
  if (notification.extra_data?.layout_id) {
    // 跳转到布局详情页
    window.location.href = `/system/layouts/${notification.extra_data.layout_id}`
  }

  visible.value = false
}

const handleMarkAllRead = async () => {
  try {
    await api.system.layoutNotifications.markAllAsRead()
    notifications.value.forEach(n => n.is_read = true)
    ElMessage.success('已全部标记为已读')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleViewAll = () => {
  // 跳转到通知列表页
  window.location.href = '/system/notifications'
}

const handleClick = () => {
  visible.value = !visible.value
  if (visible.value) {
    loadNotifications()
  }
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped lang="scss">
.notification-center {
  .notification-badge {
    margin-right: 16px;
  }
}

.notification-panel {
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid #ebeef5;

    h4 {
      margin: 0;
      font-size: 14px;
      font-weight: 500;
    }
  }

  .empty-state {
    padding: 40px 20px;
    text-align: center;
  }

  .notification-list {
    .notification-item {
      display: flex;
      gap: 12px;
      padding: 12px 16px;
      cursor: pointer;
      transition: background-color 0.2s;

      &:hover {
        background-color: #f5f7fa;
      }

      &.is-unread {
        background-color: #ecf5ff;

        &::before {
          content: '';
          position: absolute;
          left: 8px;
          top: 50%;
          transform: translateY(-50%);
          width: 6px;
          height: 6px;
          background-color: #409eff;
          border-radius: 50%;
        }
      }

      .notification-icon {
        flex-shrink: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .notification-content {
        flex: 1;
        min-width: 0;

        .notification-title {
          font-size: 14px;
          font-weight: 500;
          color: #303133;
          margin-bottom: 4px;
        }

        .notification-message {
          font-size: 12px;
          color: #606266;
          line-height: 1.5;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
        }

        .notification-time {
          font-size: 12px;
          color: #909399;
        }
      }
    }
  }

  .panel-footer {
    padding: 12px 16px;
    border-top: 1px solid #ebeef5;
    text-align: center;
  }
}
</style>
```

---

## 7. 布局导入导出

### 7.1 布局导出

#### 7.1.1 导出 API

**API 调用**:
```http
GET /api/system/page-layouts/{id}/export/
```

**响应**:
```json
{
  "success": true,
  "data": {
    "layout_name": "资产表单布局",
    "exported_at": "2024-01-15T10:30:00Z",
    "version": "1.2.0",
    "config": { /* 完整布局配置 */ },
    "metadata": {
      "business_object": "Asset",
      "layout_type": "form",
      "description": "资产新增/编辑表单布局",
      "exported_by": "admin"
    }
  }
}
```

**后端实现**:
```python
@action(detail=True, methods=['get'])
def export(self, request, pk=None):
    """导出布局配置"""
    layout = self.get_object()

    export_data = {
        'layout_name': layout.layout_name,
        'exported_at': timezone.now().isoformat(),
        'version': layout.version,
        'config': layout.config,
        'metadata': {
            'business_object': layout.business_object.code,
            'layout_type': layout.layout_type,
            'description': layout.description,
            'exported_by': request.user.username
        }
    }

    # 生成 JSON 文件
    import json
    from django.http import HttpResponse

    response = HttpResponse(
        json.dumps(export_data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="{layout.layout_name}-{layout.version}.json"'

    return response
```

### 7.2 布局导入

#### 7.2.1 导入验证

**验证器实现**:
```python
# apps/system/validators.py
def validate_import_data(import_data):
    """验证导入数据"""

    errors = []

    # 1. 基础结构验证
    required_fields = ['layout_name', 'config', 'metadata']
    for field in required_fields:
        if field not in import_data:
            errors.append(f"缺少必填字段: {field}")

    if 'metadata' in import_data:
        metadata = import_data['metadata']
        required_metadata = ['business_object', 'layout_type']
        for field in required_metadata:
            if field not in metadata:
                errors.append(f"metadata 缺少必填字段: {field}")

    # 2. 业务对象验证
    if 'metadata' in import_data:
        business_object_code = import_data['metadata'].get('business_object')
        if not BusinessObject.objects.filter(code=business_object_code).exists():
            errors.append(f"业务对象 {business_object_code} 不存在")

    # 3. 布局配置验证
    if 'config' in import_data:
        try:
            validate_layout_config(import_data['config'])
        except ValidationError as e:
            errors.extend(e.detail)

    if errors:
        raise ValidationError({
            'code': 'IMPORT_VALIDATION_ERROR',
            'message': '导入数据验证失败',
            'details': errors
        })

    return True
```

#### 7.2.2 导入 API

**API 调用**:
```http
POST /api/system/page-layouts/import/
Content-Type: application/json

{
  "file": "<base64 encoded JSON file>",
  "layout_name": "资产表单布局（导入）",
  "description": "从模板导入"
}
```

**后端实现**:
```python
@action(detail=False, methods=['post'])
def import_config(self, request):
    """导入布局配置"""
    import base64
    import json

    # 解析文件
    file_data = request.data.get('file')
    if not file_data:
        return Response(BaseResponse.error(
            message='缺少上传文件'
        ), status=status.HTTP_400_BAD_REQUEST)

    try:
        # Base64 解码
        json_data = base64.b64decode(file_data).decode('utf-8')
        import_data = json.loads(json_data)

        # 验证导入数据
        validate_import_data(import_data)

        # 创建新布局
        layout = PageLayout.objects.create(
            business_object=BusinessObject.objects.get(
                code=import_data['metadata']['business_object']
            ),
            layout_type=import_data['metadata']['layout_type'],
            layout_name=request.data.get(
                'layout_name',
                f"{import_data['layout_name']}（导入）"
            ),
            description=request.data.get(
                'description',
                import_data['metadata'].get('description', '')
            ),
            config=import_data['config'],
            status='draft',
            version='1.0.0-draft',
            organization=request.user.organization,
            created_by=request.user
        )

        serializer = self.get_serializer(layout)
        return Response(BaseResponse.success(
            message='布局导入成功',
            data=serializer.data
        ), status=status.HTTP_201_CREATED)

    except json.JSONDecodeError:
        return Response(BaseResponse.error(
            message='文件格式错误'
        ), status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response(BaseResponse.error(
            message='导入数据验证失败',
            details=e.detail
        ), status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(BaseResponse.error(
            message=f'导入失败: {str(e)}'
        ), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 7.3 跨组织布局共享

#### 7.3.1 布局模板库

```python
# apps/system/models.py
class LayoutTemplate(BaseModel):
    """布局模板库（跨组织共享）"""

    TEMPLATE_SCOPE_CHOICES = [
        ('public', '公开'),
        ('private', '私有'),
        ('organization', '组织内'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name='模板名称'
    )

    description = models.TextField(
        blank=True,
        verbose_name='模板描述'
    )

    # 适用业务对象
    business_object = models.ForeignKey(
        'BusinessObject',
        on_delete=models.CASCADE,
        related_name='templates',
        verbose_name='业务对象'
    )

    # 布局类型
    layout_type = models.CharField(
        max_length=20,
        choices=PageLayout.LAYOUT_TYPE_CHOICES,
        verbose_name='布局类型'
    )

    # 布局配置
    config = models.JSONField(
        verbose_name='布局配置'
    )

    # 模板缩略图（base64）
    thumbnail = models.TextField(
        blank=True,
        verbose_name='缩略图'
    )

    # 使用次数
    usage_count = models.IntegerField(
        default=0,
        verbose_name='使用次数'
    )

    # 评分
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0.0,
        verbose_name='评分'
    )

    # 范围
    scope = models.CharField(
        max_length=20,
        choices=TEMPLATE_SCOPE_CHOICES,
        default='public',
        verbose_name='共享范围'
    )

    # 标签
    tags = models.JSONField(
        default=list,
        verbose_name='标签'
    )

    # 发布组织（用于 public 模板）
    publisher_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='published_templates',
        verbose_name='发布组织'
    )

    class Meta:
        db_table = 'system_layout_template'
        verbose_name = '布局模板'
        verbose_name_plural = '布局模板'
        ordering = ['-usage_count', '-rating']

    def __str__(self):
        return self.name
```

#### 7.3.2 从模板创建布局

**API 调用**:
```http
POST /api/system/layout-templates/{id}/apply/
Content-Type: application/json

{
  "layout_name": "资产表单布局（基于模板）"
}
```

**后端实现**:
```python
# apps/system/viewsets.py
class LayoutTemplateViewSet(BaseModelViewSet):
    """布局模板视图集"""

    queryset = LayoutTemplate.objects.all()
    serializer_class = LayoutTemplateSerializer

    def get_queryset(self):
        """获取模板列表"""
        queryset = super().get_queryset()

        # 过滤参数
        business_object = self.request.query_params.get('business_object')
        layout_type = self.request.query_params.get('layout_type')
        scope = self.request.query_params.get('scope', 'public')
        tags = self.request.query_params.getlist('tags')

        if business_object:
            queryset = queryset.filter(business_object__code=business_object)
        if layout_type:
            queryset = queryset.filter(layout_type=layout_type)
        if scope:
            queryset = queryset.filter(scope=scope)
        if tags:
            queryset = queryset.filter(tags__overlap=tags)

        return queryset

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """应用模板创建布局"""
        template = self.get_object()

        # 创建新布局
        layout = PageLayout.objects.create(
            business_object=template.business_object,
            layout_type=template.layout_type,
            layout_name=request.data.get(
                'layout_name',
                f"{template.name}（基于模板）"
            ),
            description=template.description,
            config=template.config,
            status='draft',
            version='1.0.0-draft',
            organization=request.user.organization,
            created_by=request.user
        )

        # 增加使用次数
        template.usage_count += 1
        template.save(update_fields=['usage_count'])

        serializer = PageLayoutSerializer(layout)
        return Response(BaseResponse.success(
            message='模板应用成功',
            data=serializer.data
        ))

    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """评分"""
        template = self.get_object()
        rating = request.data.get('rating')

        if not rating or not (1 <= rating <= 5):
            return Response(BaseResponse.error(
                message='评分必须在 1-5 之间'
            ), status=status.HTTP_400_BAD_REQUEST)

        # 更新评分（简单平均）
        from django.db.models import Avg

        template.rating = (template.usage_count * template.rating + rating) / (template.usage_count + 1)
        template.save(update_fields=['rating'])

        serializer = self.get_serializer(template)
        return Response(BaseResponse.success(
            message='评分成功',
            data=serializer.data
        ))
```

---

## 8. 前端工作流集成

### 8.1 布局管理界面

```vue
<!-- views/system/LayoutManagement.vue -->
<template>
  <div class="layout-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>布局管理</h2>
        <el-breadcrumb separator="/">
          <el-breadcrumb-item>系统管理</el-breadcrumb-item>
          <el-breadcrumb-item>布局管理</el-breadcrumb-item>
        </el-breadcrumb>
      </div>

      <div class="header-right">
        <el-button
          v-permission="['edit_layout']"
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建布局
        </el-button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-form :inline="true" :model="filters">
        <el-form-item label="业务对象">
          <el-select
            v-model="filters.business_object"
            placeholder="选择业务对象"
            clearable
            @change="handleSearch"
          >
            <el-option
              v-for="obj in businessObjects"
              :key="obj.code"
              :label="obj.name"
              :value="obj.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="布局类型">
          <el-select
            v-model="filters.layout_type"
            placeholder="选择布局类型"
            clearable
            @change="handleSearch"
          >
            <el-option label="表单布局" value="form" />
            <el-option label="列表布局" value="list" />
            <el-option label="详情布局" value="detail" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select
            v-model="filters.status"
            placeholder="选择状态"
            clearable
            @change="handleSearch"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :icon="Search" @click="handleSearch">
            搜索
          </el-button>
          <el-button :icon="Refresh" @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 布局列表 -->
    <el-table
      v-loading="loading"
      :data="layouts"
      border
      style="width: 100%"
    >
      <el-table-column prop="layout_name" label="布局名称" min-width="200" />

      <el-table-column prop="business_object_name" label="业务对象" width="150" />

      <el-table-column label="布局类型" width="120">
        <template #default="{ row }">
          <el-tag :type="getLayoutTypeTag(row.layout_type)">
            {{ row.layout_type_display }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusTag(row.status)">
            {{ row.status_display }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column prop="version" label="版本" width="100" />

      <el-table-column prop="modified_at" label="修改时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.modified_at) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            :icon="Edit"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>

          <el-button
            v-if="row.status === 'draft'"
            link
            type="success"
            :icon="Promotion"
            @click="handlePublish(row)"
          >
            发布
          </el-button>

          <el-dropdown @command="(cmd) => handleMoreAction(cmd, row)">
            <el-button link type="primary">
              更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="preview" :icon="View">
                  预览
                </el-dropdown-item>
                <el-dropdown-item command="versions" :icon="Clock">
                  版本历史
                </el-dropdown-item>
                <el-dropdown-item command="clone" :icon="CopyDocument">
                  克隆
                </el-dropdown-item>
                <el-dropdown-item command="export" :icon="Download">
                  导出
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="row.status === 'published'"
                  command="setDefault"
                  :icon="Star"
                >
                  设为默认
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="row.status === 'published'"
                  command="archive"
                  :icon="FolderOpened"
                >
                  归档
                </el-dropdown-item>
                <el-dropdown-item
                  v-if="row.status === 'archived'"
                  command="activate"
                  :icon="RefreshRight"
                >
                  重新激活
                </el-dropdown-item>
                <el-dropdown-item
                  command="delete"
                  :icon="Delete"
                  divided
                >
                  删除
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.pageSize"
      :total="pagination.total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="loadLayouts"
      @current-change="loadLayouts"
    />

    <!-- 发布对话框 -->
    <PublishDialog
      v-model="publishVisible"
      :layout="currentLayout"
      @confirm="handlePublishConfirm"
    />

    <!-- 版本历史对话框 -->
    <LayoutVersionHistory
      v-model="versionHistoryVisible"
      :layout-id="currentLayout?.id"
      @rollback="handleRollback"
    />

    <!-- 版本对比对话框 -->
    <LayoutVersionCompare
      v-model="versionCompareVisible"
      :layout-id="currentLayout?.id"
      :current-config="currentLayout?.config"
      :current-version="currentLayout?.version"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Refresh, Edit, Promotion, View, Clock,
  CopyDocument, Download, Star, FolderOpened, RefreshRight,
  Delete, ArrowDown
} from '@element-plus/icons-vue'
import PublishDialog from '@/components/system/PublishDialog.vue'
import LayoutVersionHistory from '@/components/system/LayoutVersionHistory.vue'
import LayoutVersionCompare from '@/components/system/LayoutVersionCompare.vue'
import { api } from '@/api'
import { usePermission } from '@/hooks/usePermission'

const router = useRouter()
const { hasPermission } = usePermission()

const loading = ref(false)
const layouts = ref([])
const businessObjects = ref([])

const filters = ref({
  business_object: '',
  layout_type: '',
  status: ''
})

const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0
})

const currentLayout = ref(null)
const publishVisible = ref(false)
const versionHistoryVisible = ref(false)
const versionCompareVisible = ref(false)

const loadLayouts = async () => {
  loading.value = true
  try {
    const response = await api.system.pageLayouts.list({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      ...filters.value
    })

    layouts.value = response.data.results
    pagination.value.total = response.data.count
  } catch (error) {
    ElMessage.error('加载布局列表失败')
  } finally {
    loading.value = false
  }
}

const loadBusinessObjects = async () => {
  try {
    const response = await api.system.businessObjects.list({
      page_size: 1000
    })
    businessObjects.value = response.data.results
  } catch (error) {
    console.error('加载业务对象失败:', error)
  }
}

const handleSearch = () => {
  pagination.value.page = 1
  loadLayouts()
}

const handleReset = () => {
  filters.value = {
    business_object: '',
    layout_type: '',
    status: ''
  }
  handleSearch()
}

const handleCreate = () => {
  router.push({
    path: '/system/layouts/create',
    query: {
      object: filters.value.business_object,
      type: filters.value.layout_type
    }
  })
}

const handleEdit = (layout) => {
  router.push(`/system/layouts/${layout.id}/edit`)
}

const handlePublish = (layout) => {
  currentLayout.value = layout
  publishVisible.value = true
}

const handlePublishConfirm = () => {
  ElMessage.success('布局发布成功')
  publishVisible.value = false
  loadLayouts()
}

const handleRollback = () => {
  ElMessage.success('版本回滚成功')
  versionHistoryVisible.value = false
  loadLayouts()
}

const handleMoreAction = async (command, layout) => {
  switch (command) {
    case 'preview':
      router.push(`/system/layouts/${layout.id}/preview`)
      break

    case 'versions':
      currentLayout.value = layout
      versionHistoryVisible.value = true
      break

    case 'clone':
      await handleClone(layout)
      break

    case 'export':
      await handleExport(layout)
      break

    case 'setDefault':
      await handleSetDefault(layout)
      break

    case 'archive':
      await handleArchive(layout)
      break

    case 'activate':
      await handleActivate(layout)
      break

    case 'delete':
      await handleDelete(layout)
      break
  }
}

const handleClone = async (layout) => {
  try {
    await api.system.pageLayouts.clone(layout.id, {
      layout_name: `${layout.layout_name}（副本）`
    })
    ElMessage.success('布局克隆成功')
    loadLayouts()
  } catch (error) {
    ElMessage.error('克隆失败')
  }
}

const handleExport = async (layout) => {
  try {
    const response = await api.system.pageLayouts.export(layout.id)

    // 下载文件
    const blob = new Blob([JSON.stringify(response.data, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${layout.layout_name}-${layout.version}.json`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleSetDefault = async (layout) => {
  try {
    await api.system.pageLayouts.setDefault(layout.id)
    ElMessage.success('已设置为默认布局')
    loadLayouts()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleArchive = async (layout) => {
  try {
    await ElMessageBox.confirm(
      '确定要归档此布局吗？归档后将不再使用。',
      '归档确认',
      { type: 'warning' }
    )

    await api.system.pageLayouts.archive(layout.id)
    ElMessage.success('布局已归档')
    loadLayouts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleActivate = async (layout) => {
  try {
    await api.system.pageLayouts.activate(layout.id)
    ElMessage.success('布局已重新激活')
    loadLayouts()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (layout) => {
  try {
    await ElMessageBox.confirm(
      '确定要删除此布局吗？此操作不可恢复！',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await api.system.pageLayouts.delete(layout.id)
    ElMessage.success('布局已删除')
    loadLayouts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getLayoutTypeTag = (type) => {
  const tags = {
    'form': 'primary',
    'list': 'success',
    'detail': 'warning'
  }
  return tags[type] || 'info'
}

const getStatusTag = (status) => {
  const tags = {
    'draft': 'info',
    'published': 'success',
    'archived': 'warning'
  }
  return tags[status] || 'info'
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(() => {
  loadLayouts()
  loadBusinessObjects()
})
</script>

<style scoped lang="scss">
.layout-management {
  padding: 24px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;

    .header-left {
      h2 {
        margin: 0 0 8px 0;
        font-size: 20px;
        font-weight: 500;
      }
    }
  }

  .filter-bar {
    margin-bottom: 16px;
    padding: 16px;
    background-color: #fff;
    border-radius: 4px;
  }

  .el-pagination {
    margin-top: 16px;
    justify-content: flex-end;
  }
}
</style>
```

### 8.2 布局设计器入口

```vue
<!-- views/system/LayoutDesigner.vue -->
<template>
  <div class="layout-designer-page">
    <!-- 设计器组件 -->
    <LayoutDesigner
      :layout-id="layoutId"
      :business-object="businessObject"
      :layout-type="layoutType"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import LayoutDesigner from '@/components/engine/LayoutDesigner.vue'

const route = useRoute()

const layoutId = computed(() => route.params.id || '')
const businessObject = computed(() => route.query.object || 'Asset')
const layoutType = computed(() => route.query.type || 'form')
</script>
```

### 8.3 路由配置

```javascript
// frontend/src/router/index.js
{
  path: '/system',
  component: Layout,
  meta: { title: '系统管理', requiresAuth: true },
  children: [
    {
      path: 'layouts',
      name: 'LayoutManagement',
      component: () => import('@/views/system/LayoutManagement.vue'),
      meta: {
        title: '布局管理',
        permissions: ['view_layout']
      }
    },
    {
      path: 'layouts/create',
      name: 'LayoutDesignerCreate',
      component: () => import('@/views/system/LayoutDesigner.vue'),
      meta: {
        title: '新建布局',
        permissions: ['edit_layout']
      }
    },
    {
      path: 'layouts/:id/edit',
      name: 'LayoutDesignerEdit',
      component: () => import('@/views/system/LayoutDesigner.vue'),
      meta: {
        title: '编辑布局',
        permissions: ['edit_layout']
      }
    },
    {
      path: 'layouts/:id/preview',
      name: 'LayoutPreview',
      component: () => import('@/views/system/LayoutPreview.vue'),
      meta: {
        title: '布局预览',
        permissions: ['view_layout']
      }
    },
    {
      path: 'notifications',
      name: 'LayoutNotifications',
      component: () => import('@/views/system/LayoutNotifications.vue'),
      meta: {
        title: '通知中心',
        permissions: ['view_layout']
      }
    }
  ]
}
```

---

## 9. 最佳实践与规范

### 9.1 布局版本管理最佳实践

#### 9.1.1 版本号规范

| 场景 | 版本号示例 | 说明 |
|------|-----------|------|
| 初始发布 | `1.0.0` | 首次发布 |
| 新增字段/区块 | `1.1.0`, `1.2.0` | 次版本递增 |
| 字段属性调整 | `1.1.1`, `1.1.2` | 修订版递增 |
| 重大结构调整 | `2.0.0` | 主版本递增 |
| 热修复 | `1.1.1-hotfix` | 带后缀 |
| 回滚 | `1.0.0-rollback-1234567890` | 带时间戳 |

#### 9.1.2 变更说明规范

**好的变更说明**:
```
- 优化资产表单字段分组，将财务信息单独分组
- 新增"折旧信息"标签页，包含折旧方法、残值率等字段
- 调整字段顺序，将必填字段前置
```

**不好的变更说明**:
```
- 更新布局
- 修复问题
```

### 9.2 审批流程配置建议

#### 9.2.1 小型组织（<50人）

```python
workflow_config = {
    'enable_approval': False,  # 不启用审批
    'auto_publish_roles': ['系统管理员', '布局管理员']
}
```

#### 9.2.2 中型组织（50-200人）

```python
workflow_config = {
    'enable_approval': True,
    'approvers': ['IT经理', '业务主管'],
    'auto_publish_roles': ['系统管理员']
}
```

#### 9.2.3 大型组织（>200人）

```python
workflow_config = {
    'enable_approval': True,
    'approvers': ['系统管理员', 'IT总监', '业务部门负责人'],
    'auto_publish_roles': [],  # 所有发布都需要审批
    'require_approval_for_critical_objects': ['Asset', 'ProcurementRequest']
}
```

### 9.3 性能优化建议

#### 9.3.1 草稿自动保存优化

```javascript
// 配置建议
const autoSaveConfig = {
  enabled: true,
  interval: 120,  // 2分钟
  debounceDelay: 2000,  // 2秒防抖
  maxRetries: 3,
  retryDelay: 5000
}
```

#### 9.3.2 版本历史清理策略

```python
# 建议保留策略
VERSION_RETENTION_POLICY = {
    'published': 'all',  # 已发布版本全部保留
    'draft': '30',  # 草稿保留30天
    'archived': '90',  # 归档版本保留90天
    'rollback': '30'  # 回滚版本保留30天
}
```

### 9.4 安全建议

#### 9.4.1 权限最小化原则

- 普通用户：仅查看已发布布局
- 业务管理员：创建和编辑布局草稿
- 系统管理员：完全控制布局生命周期

#### 9.4.2 审批日志记录

```python
# 记录所有审批操作
class ApprovalAuditLog(BaseModel):
    """审批审计日志"""

    approval = models.ForeignKey(
        LayoutApproval,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        verbose_name='审批'
    )

    action = models.CharField(
        max_length=20,
        choices=[
            ('submit', '提交申请'),
            ('approve', '通过'),
            ('reject', '拒绝'),
            ('cancel', '取消'),
        ],
        verbose_name='操作'
    )

    operator = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='操作人'
    )

    ip_address = models.GenericIPAddressField(
        verbose_name='IP地址'
    )

    user_agent = models.TextField(
        verbose_name='用户代理'
    )

    comment = models.TextField(
        blank=True,
        verbose_name='备注'
    )
```

---

## 10. 总结

布局自定义工作流是 GZEAMS 低代码平台的核心能力之一，通过**完整的生命周期管理**和**严格的权限控制**，确保布局变更的安全性、可追溯性和可控性。

**核心优势**：
1. **完整的工作流支持**：草稿 → 审批 → 发布 → 归档，全生命周期管理
2. **细粒度权限控制**：基于角色的权限系统，支持审批流程配置
3. **全面的版本管理**：版本历史、版本对比、版本回滚，支持分支管理
4. **自动化通知机制**：布局变更实时通知，确保相关人员及时获知
5. **跨组织共享**：布局模板库支持跨组织布局共享和复用

**技术亮点**：
- **前端**：Vue 3 Composition API + Pinia + Element Plus
- **后端**：Django REST Framework + PostgreSQL JSONB
- **状态机**：布局状态流转控制
- **版本控制**：语义化版本号生成策略
- **通知系统**：实时通知中心

通过布局自定义工作流，企业可以**安全、高效地管理页面布局变更**，降低操作风险，提升系统稳定性和可维护性。
