# 元数据驱动使用指南

> 本指南整合了 GZEAMS 平台元数据驱动的完整使用方法和最佳实践

---

## 目录

1. [概述](#1-概述)
2. [核心概念](#2-核心概念)
3. [后端使用](#3-后端使用)
4. [前端使用](#4-前端使用)
5. [最佳实践](#5-最佳实践)
6. [常见问题](#6-常见问题)
7. [附录](#7-附录)

---

## 1. 概述

### 1.1 什么是元数据驱动

元数据驱动是一种**通过配置而非编码**来定义业务对象和表单的架构模式。在 GZEAMS 平台中：

| 传统模式 | 元数据驱动模式 |
|---------|--------------|
| 为每个业务对象编写 Model、Serializer、ViewSet | 通过配置 BusinessObject 和 FieldDefinition 自动生成 |
| 字段变更需要修改代码和数据库 | 只需修改配置，无需代码变更 |
| 新增业务对象需要完整的开发流程 | 通过管理界面配置即可创建新对象 |

### 1.2 适用场景

**✅ 适合使用元数据驱动的场景：**

- 动态表单需求（用户自定义表单字段）
- 多租户定制需求（不同组织有不同的字段需求）
- 快速原型开发（快速验证业务逻辑）
- 频繁变更的字段定义（业务规则经常变化）

**❌ 不适合使用元数据驱动的场景：**

- 核心业务实体（Asset、Category 等建议使用传统 Model）
- 复杂业务逻辑（涉及多表关联、复杂计算）
- 高性能要求场景（传统 Model 查询性能更好）

### 1.3 架构组件

```
┌─────────────────────────────────────────────────────────────────┐
│                    GZEAMS 元数据驱动架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    配置层 (Metadata)                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │ │
│  │  │BusinessObject│→│FieldDefinition│→│  PageLayout   │    │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    服务层 (Services)                       │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐    │ │
│  │  │MetadataDrivenService │  │ DynamicFieldProcessor   │    │ │
│  │  └──────────────────┘  └────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    接口层 (API)                            │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐    │ │
│  │  │MetadataDrivenSerializer │  │ MetadataDrivenViewSet │    │ │
│  │  └──────────────────┘  └────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    数据层 (Data)                           │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐    │ │
│  │  │   DynamicData    │  │   custom_fields (JSONB)    │    │ │
│  │  └──────────────────┘  └────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.4 相关文档

| 文档 | 说明 |
|------|------|
| [metadata_driven.md](./metadata_driven.md) | 元数据驱动核心架构 |
| [dynamic_data_service.md](./dynamic_data_service.md) | 动态数据 CRUD 服务 |
| [metadata_validators.md](./metadata_validators.md) | 动态字段验证器 |
| [page_layout_config.md](./page_layout_config.md) | 页面布局配置 |

---

## 2. 核心概念

### 2.1 BusinessObject（业务对象）

业务对象是元数据驱动的核心，代表一个可配置的业务实体。

```python
# 示例：创建一个"采购申请"业务对象
from apps.system.models import BusinessObject

business_object = BusinessObject.objects.create(
    code='ProcurementRequest',
    name='采购申请',
    description='企业采购申请单',
    table_name='procurement_requests',
    enable_workflow=True,      # 启用工作流
    enable_version=True,        # 启用版本控制
    default_ordering='-created_at'
)
```

### 2.2 FieldDefinition（字段定义）

字段定义描述了业务对象包含的字段及其属性。

```python
# 示例：为采购申请添加字段
from apps.system.models import FieldDefinition

# 文本字段
FieldDefinition.objects.create(
    business_object=business_object,
    code='request_no',
    name='申请单号',
    field_type='text',
    is_required=True,
    is_unique=True,
    max_length=50,
    is_searchable=True,
    sortable=True,
    sort_order=1
)

# 选项字段
FieldDefinition.objects.create(
    business_object=business_object,
    code='status',
    name='状态',
    field_type='choice',
    is_required=True,
    default_value='draft',
    options={
        'draft': '草稿',
        'pending': '待审批',
        'approved': '已批准',
        'rejected': '已拒绝'
    },
    sort_order=2
)

# 金额字段
FieldDefinition.objects.create(
    business_object=business_object,
    code='amount',
    name='申请金额',
    field_type='number',
    is_required=True,
    min_value=0,
    max_value=1000000,
    decimal_places=2,
    sort_order=3
)

# 用户选择字段
FieldDefinition.objects.create(
    business_object=business_object,
    code='requester',
    name='申请人',
    field_type='user',
    is_required=True,
    default_value='current',  # 默认为当前用户
    sort_order=4
)

# 公式字段
FieldDefinition.objects.create(
    business_object=business_object,
    code='tax_amount',
    name='税额',
    field_type='formula',
    is_readonly=True,
    formula_expression='amount * 0.13',  # 13% 税率
    decimal_places=2,
    sort_order=5
)
```

### 2.3 支持的字段类型

| 字段类型 | 说明 | 配置属性 | 示例 |
|---------|------|---------|------|
| `text` | 单行文本 | max_length, validation_regex | 产品名称 |
| `textarea` | 多行文本 | max_length, rows | 备注说明 |
| `number` | 数值（小数） | min_value, max_value, decimal_places | 单价、数量 |
| `integer` | 整数 | min_value, max_value | 库存数量 |
| `float` | 浮点数 | min_value, max_value | 重量、长度 |
| `boolean` | 布尔值 | default_value | 是否启用 |
| `date` | 日期 | min_value, max_value | 采购日期 |
| `datetime` | 日期时间 | min_value, max_value | 创建时间 |
| `time` | 时间 | - | 预约时间 |
| `email` | 邮箱 | - | 联系邮箱 |
| `url` | URL地址 | - | 相关链接 |
| `choice` | 单选 | options | 状态、分类 |
| `multi_choice` | 多选 | options | 标签、权限 |
| `file` | 文件上传 | max_size, file_types | 附件 |
| `image` | 图片上传 | max_size, max_dimensions | 产品图片 |
| `reference` | 关联对象 | reference_to | 关联资产 |
| `user` | 用户选择 | default_value='current' | 申请人 |
| `department` | 部门选择 | default_value='current' | 使用部门 |
| `formula` | 公式计算 | formula_expression, decimal_places | 总价、税额 |

---

## 3. 后端使用

### 3.1 创建元数据驱动的 CRUD 服务

```python
# backend/apps/custom_module/services.py

from apps.common.services.metadata_driven import MetadataDrivenService

class ProcurementRequestService(MetadataDrivenService):
    """
    采购申请服务

    继承自 MetadataDrivenService，自动获得完整的 CRUD 能力
    """

    # 指定业务对象编码
    module_name = 'ProcurementRequest'

    def __init__(self):
        super().__init__('ProcurementRequest')

    def get_export_queryset(self, filters):
        """
        获取导出查询集（可选实现）
        """
        return self.query(filters=filters)
```

### 3.2 使用 Service 进行 CRUD 操作

```python
from apps.custom_module.services import ProcurementRequestService

# 创建服务实例
service = ProcurementRequestService()

# 创建数据
request_data = {
    'request_no': 'PR2026001',
    'requester': 'current',  # 自动替换为当前用户
    'amount': 50000.00,
    'status': 'draft'
    # 公式字段 tax_amount 会自动计算
}

new_request = service.create(request_data, user=request.user)
print(f"创建成功，税额: {new_request.custom_fields['tax_amount']}")

# 查询数据
queryset = service.query(
    filters={'status': 'pending'},
    search='PR2026',
    order_by='-created_at'
)

# 分页查询
page_result = service.paginate(
    page=1,
    page_size=20,
    filters={'status': 'pending'}
)

# 更新数据
updated_request = service.update(
    str(new_request.id),
    {'status': 'approved', 'amount': 55000.00},
    user=request.user
)

# 软删除
service.delete(str(new_request.id), user=request.user)

# 批量删除
result = service.batch_delete(
    ids=['id1', 'id2', 'id3'],
    user=request.user
)
```

### 3.3 创建元数据驱动的 ViewSet

```python
# backend/apps/custom_module/viewsets.py

from rest_framework import viewsets
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.serializers.metadata_driven import MetadataDrivenSerializer
from apps.common.filters.metadata_driven import MetadataDrivenFilter

class DynamicDataViewSet(BaseModelViewSet):
    """
    动态数据 ViewSet

    根据业务对象编码动态提供 CRUD 接口
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None
        self.business_object_code = None

    def dispatch(self, request, *args, **kwargs):
        """在请求分发时初始化服务"""
        self.business_object_code = kwargs.get('object_code')
        if self.business_object_code:
            from apps.common.services.metadata_driven import MetadataDrivenService
            self.service = MetadataDrivenService(self.business_object_code)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """获取查询集"""
        if self.service:
            filters = dict(self.request.query_params)
            search = filters.pop('search', None)
            return self.service.query(filters=filters, search=search)
        return DynamicData.objects.none()

    def get_serializer_class(self):
        """动态获取序列化器类"""
        if self.service:
            return MetadataDrivenSerializer.for_business_object(
                self.business_object_code,
                layout_type='list' if self.action == 'list' else 'form'
            )
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """创建数据"""
        if self.service:
            instance = self.service.create(
                serializer.validated_data,
                user=self.request.user
            )
            serializer.instance = instance
        else:
            super().perform_create(serializer)

    def perform_update(self, serializer):
        """更新数据"""
        if self.service:
            instance = self.service.update(
                str(serializer.instance.id),
                serializer.validated_data,
                user=self.request.user
            )
            serializer.instance = instance
        else:
            super().perform_update(serializer)
```

### 3.4 配置 URL 路由

```python
# backend/apps/custom_module/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import DynamicDataViewSet

router = DefaultRouter()
router.register(r'dynamic/(?P<object_code>\w+)', DynamicDataViewSet, basename='dynamic-data')

urlpatterns = [
    path('api/', include(router.urls)),
]
```

### 3.5 API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/dynamic/{object_code}/` | 列表查询 |
| GET | `/api/dynamic/{object_code}/{id}/` | 获取详情 |
| POST | `/api/dynamic/{object_code}/` | 创建数据 |
| PUT | `/api/dynamic/{object_code}/{id}/` | 更新数据 |
| PATCH | `/api/dynamic/{object_code}/{id}/` | 部分更新 |
| DELETE | `/api/dynamic/{object_code}/{id}/` | 软删除 |
| POST | `/api/dynamic/{object_code}/batch-delete/` | 批量删除 |
| GET | `/api/dynamic/{object_code}/metadata/` | 获取元数据 |
| GET | `/api/dynamic/{object_code}/schema/` | 获取数据模式 |

---

## 4. 前端使用

### 4.1 使用元数据驱动的表单组件

```vue
<!-- DynamicForm 示例 -->
<template>
    <MetadataDrivenForm
        :business-object-code="businessObjectCode"
        :layout-type="'form'"
        :data="formData"
        :mode="formMode"
        @submit="handleSubmit"
        @cancel="handleCancel"
    />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MetadataDrivenForm from '@/components/engine/MetadataDrivenForm.vue'
import { metadataApi } from '@/api/metadata'

const route = useRoute()
const businessObjectCode = ref(route.params.object_code || 'ProcurementRequest')
const formMode = ref('create')  // create | edit | view
const formData = ref({})

const handleSubmit = async (data) => {
    // 提交数据
    if (formMode.value === 'create') {
        await metadataApi.createData(businessObjectCode.value, data)
    } else {
        await metadataApi.updateData(businessObjectCode.value, route.params.id, data)
    }
}

onMounted(async () => {
    // 编辑模式加载数据
    if (formMode.value !== 'create') {
        const response = await metadataApi.getData(businessObjectCode.value, route.params.id)
        formData.value = response.data
    }
})
</script>
```

### 4.2 使用元数据驱动的列表组件

```vue
<!-- MetadataDrivenList 示例 -->
<template>
    <MetadataDrivenList
        :business-object-code="businessObjectCode"
        :layout-type="'list'"
        :page-size="20"
        @row-click="handleRowClick"
        @create="handleCreate"
    />
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import MetadataDrivenList from '@/components/engine/MetadataDrivenList.vue'

const router = useRouter()
const businessObjectCode = ref('ProcurementRequest')

const handleRowClick = (row) => {
    router.push(`/${businessObjectCode.value}/${row.id}`)
}

const handleCreate = () => {
    router.push(`/${businessObjectCode.value}/create`)
}
</script>
```

### 4.3 获取和使用元数据

```javascript
// frontend/src/composables/useMetadata.js

import { ref } from 'vue'
import { metadataApi } from '@/api/metadata'

export function useMetadata(objectCode) {
    const businessObject = ref(null)
    const fieldDefinitions = ref([])
    const formLayout = ref(null)
    const listLayout = ref(null)
    const loading = ref(false)

    const loadMetadata = async () => {
        loading.value = true
        try {
            const response = await metadataApi.getMetadata(objectCode)
            businessObject.value = response.data.business_object
            fieldDefinitions.value = response.data.field_definitions
            formLayout.value = response.data.form_layout
            listLayout.value = response.data.list_layout
        } finally {
            loading.value = false
        }
    }

    const getValidationRules = () => {
        // 将字段定义转换为表单验证规则
        const rules = {}
        fieldDefinitions.value.forEach(field => {
            const fieldRules = []

            if (field.is_required) {
                fieldRules.push({
                    required: true,
                    message: `${field.name}不能为空`,
                    trigger: 'blur'
                })
            }

            if (field.max_length) {
                fieldRules.push({
                    max: field.max_length,
                    message: `${field.name}不能超过${field.max_length}个字符`,
                    trigger: 'blur'
                })
            }

            if (field.validation_regex) {
                fieldRules.push({
                    pattern: new RegExp(field.validation_regex),
                    message: `${field.name}格式不正确`,
                    trigger: 'blur'
                })
            }

            if (field.min_value !== undefined || field.max_value !== undefined) {
                fieldRules.push({
                    type: 'number',
                    min: field.min_value,
                    max: field.max_value,
                    message: `${field.name}超出允许范围`,
                    trigger: 'blur'
                })
            }

            rules[field.code] = fieldRules
        })

        return rules
    }

    return {
        businessObject,
        fieldDefinitions,
        formLayout,
        listLayout,
        loading,
        loadMetadata,
        getValidationRules
    }
}
```

### 4.4 API 封装

```javascript
// frontend/src/api/metadata.js

import request from '@/utils/request'

export const metadataApi = {
    /**
     * 获取业务对象元数据
     */
    getMetadata(objectCode) {
        return request({
            url: `/api/dynamic/${objectCode}/metadata/`,
            method: 'get'
        })
    },

    /**
     * 获取数据模式
     */
    getSchema(objectCode) {
        return request({
            url: `/api/dynamic/${objectCode}/schema/`,
            method: 'get'
        })
    },

    /**
     * 创建数据
     */
    createData(objectCode, data) {
        return request({
            url: `/api/dynamic/${objectCode}/`,
            method: 'post',
            data
        })
    },

    /**
     * 更新数据
     */
    updateData(objectCode, id, data) {
        return request({
            url: `/api/dynamic/${objectCode}/${id}/`,
            method: 'put',
            data
        })
    },

    /**
     * 获取数据
     */
    getData(objectCode, id) {
        return request({
            url: `/api/dynamic/${objectCode}/${id}/`,
            method: 'get'
        })
    },

    /**
     * 查询数据
     */
    queryData(objectCode, params) {
        return request({
            url: `/api/dynamic/${objectCode}/`,
            method: 'get',
            params
        })
    },

    /**
     * 删除数据
     */
    deleteData(objectCode, id) {
        return request({
            url: `/api/dynamic/${objectCode}/${id}/`,
            method: 'delete'
        })
    },

    /**
     * 批量删除
     */
    batchDelete(objectCode, ids) {
        return request({
            url: `/api/dynamic/${objectCode}/batch-delete/`,
            method: 'post',
            data: { ids }
        })
    }
}
```

---

## 5. 最佳实践

### 5.1 字段命名规范

| 规则 | 示例 | 说明 |
|------|------|------|
| 使用小写字母和下划线 | `request_no`, `user_name` | 避免使用驼峰命名 |
| 名称要具有描述性 | `purchase_amount` 而非 `amt` | 清晰表达字段含义 |
| 布尔值使用 is 前缀 | `is_active`, `is_approved` | 明确表示布尔属性 |
| 日期使用 _后缀 | `created_at`, `approved_on` | 表示时间/日期 |
| ID使用 _id 后缀 | `department_id`, `user_id` | 表示关联ID |

### 5.2 字段设计建议

1. **合理设置必填字段**：只对核心字段设置必填，过多必填会影响用户体验
2. **提供默认值**：为常用字段设置合理的默认值
3. **使用选项字段**：对于有限选项的字段使用 `choice` 类型，便于统计和过滤
4. **利用公式字段**：使用公式字段自动计算派生数据，减少前端计算
5. **启用搜索和排序**：为常用查询字段启用 `is_searchable` 和 `sortable`

### 5.3 性能优化建议

1. **控制字段数量**：单个业务对象的字段数建议不超过 50 个
2. **合理使用索引**：为常用查询字段和唯一字段创建数据库索引
3. **分页查询**：列表查询始终使用分页，避免一次性加载大量数据
4. **延迟加载**：关联字段的数据采用延迟加载方式

### 5.4 错误处理

```python
# 统一的错误处理
from django.core.exceptions import ValidationError
from apps.common.validators.dynamic_field import FieldValidationError

try:
    instance = service.create(data, user=request.user)
except ValidationError as e:
    # 字段验证错误
    errors = e.message_dict
    return Response({
        'success': False,
        'error': {
            'code': 'VALIDATION_ERROR',
            'message': '数据验证失败',
            'details': errors
        }
    }, status=400)
except ValueError as e:
    # 业务逻辑错误
    return Response({
        'success': False,
        'error': {
            'code': 'BUSINESS_ERROR',
            'message': str(e)
        }
    }, status=400)
except Exception as e:
    # 系统错误
    return Response({
        'success': False,
        'error': {
            'code': 'SERVER_ERROR',
            'message': '系统错误，请稍后重试'
        }
    }, status=500)
```

### 5.5 安全考虑

1. **权限检查**：所有数据操作都应进行权限检查
2. **组织隔离**：确保查询时自动过滤组织数据
3. **输入验证**：严格验证所有用户输入
4. **敏感数据**：敏感字段应设置加密存储

---

## 6. 常见问题

### 6.1 如何在元数据驱动和传统模式之间选择？

**决策树：**

```
是否为核心业务实体（Asset, User, Organization等）？
    ├─ 是 → 使用传统 Model + BaseModelSerializer
    └─ 否 → 是否需要复杂的业务逻辑？
        ├─ 是 → 使用传统 Model
        └─ 否 → 是否需要频繁的字段变更？
            ├─ 是 → 使用元数据驱动
            └─ 否 → 使用传统 Model（性能更好）
```

### 6.2 如何处理跨字段验证？

使用 `DynamicFieldValidator` 的跨字段验证功能：

```python
from apps.common.validators.dynamic_field import DynamicFieldValidator, FieldValidationError

validator = DynamicFieldValidator(field_definitions)

# 添加跨字段验证：结束日期必须晚于开始日期
def validate_date_range(data, instance, action):
    start = data.get('start_date')
    end = data.get('end_date')
    if start and end and start > end:
        raise FieldValidationError(
            'end_date',
            '结束日期必须晚于开始日期',
            'invalid_range'
        )

validator.add_cross_field_validator(validate_date_range)
```

### 6.3 如何实现条件必填？

使用自定义验证器：

```python
# 当类型为"贵重物品"时，保险金额必填
required_validator = DynamicFieldValidator.create_required_field_validator(
    'insurance_amount',
    "data.get('asset_type') == 'valuable'"
)
validator.add_custom_validator('insurance_amount', required_validator)
```

### 6.4 公式字段支持哪些函数？

内置函数列表：

| 函数 | 说明 | 示例 |
|------|------|------|
| `abs(x)` | 绝对值 | `abs(discount)` |
| `round(x, n)` | 四舍五入 | `round(amount, 2)` |
| `min(x, y)` | 最小值 | `min(price1, price2)` |
| `max(x, y)` | 最大值 | `max(quantity, 0)` |
| `sum(arr)` | 求和 | `sum(items)` |
| `len(arr)` | 长度 | `len(tags)` |
| `avg(arr)` | 平均值 | `avg(scores)` |
| `count(arr)` | 非空计数 | `count(values)` |
| `days_between(d1, d2)` | 日期差天数 | `days_between(start_date, end_date)` |
| `years_between(d1, d2)` | 日期差年数 | `years_between(birth_date, TODAY)` |

内置常量：

| 常量 | 说明 |
|------|------|
| `NOW` | 当前日期时间 |
| `TODAY` | 当前日期 |
| `TRUE` | 布尔值 True |
| `FALSE` | 布尔值 False |
| `NULL` | 空值 |

### 6.5 如何优化大量数据的查询性能？

1. **使用传统 Model**：对于大数据量场景，考虑使用传统 Model
2. **添加数据库索引**：为 custom_fields 中的常用查询字段添加 GIN 索引
3. **使用 select_related**：减少关联查询次数
4. **使用 values()**：只查询需要的字段

---

## 7. 附录

### 7.1 完整示例：采购申请模块

```python
# backend/apps/procurement/services.py

from apps.common.services.metadata_driven import MetadataDrivenService
from apps.system.models import BusinessObject, FieldDefinition

class ProcurementService(MetadataDrivenService):
    """采购服务"""

    def __init__(self):
        super().__init__('ProcurementRequest')

    def approve_request(self, request_id: str, user):
        """审批采购申请"""
        instance = self.get(request_id)

        # 检查状态
        if instance.custom_fields.get('status') != 'pending':
            raise ValueError('只能审批待审批的申请')

        # 更新状态
        return self.update(
            request_id,
            {'status': 'approved', 'approved_by': str(user.id)},
            user=user
        )

    def reject_request(self, request_id: str, reason: str, user):
        """拒绝采购申请"""
        instance = self.get(request_id)

        if instance.custom_fields.get('status') != 'pending':
            raise ValueError('只能拒绝待审批的申请')

        return self.update(
            request_id,
            {
                'status': 'rejected',
                'rejection_reason': reason,
                'rejected_by': str(user.id)
            },
            user=user
        )
```

### 7.2 元数据初始化脚本

```python
# backend/apps/procurement/metadata.py

from apps.system.models import BusinessObject, FieldDefinition, PageLayout

def initialize_procurement_metadata():
    """初始化采购申请元数据"""

    # 创建业务对象
    business_object, created = BusinessObject.objects.get_or_create(
        code='ProcurementRequest',
        defaults={
            'name': '采购申请',
            'description': '企业采购申请单',
            'table_name': 'procurement_requests',
            'enable_workflow': True,
            'default_ordering': '-created_at'
        }
    )

    if not created:
        print("业务对象已存在")
        return

    # 创建字段定义
    fields = [
        {
            'code': 'request_no',
            'name': '申请单号',
            'field_type': 'text',
            'is_required': True,
            'is_unique': True,
            'max_length': 50,
            'is_searchable': True,
            'sortable': True,
            'sort_order': 1
        },
        {
            'code': 'requester',
            'name': '申请人',
            'field_type': 'user',
            'is_required': True,
            'default_value': 'current',
            'sort_order': 2
        },
        {
            'code': 'department',
            'name': '申请部门',
            'field_type': 'department',
            'is_required': True,
            'default_value': 'current',
            'sort_order': 3
        },
        {
            'code': 'request_date',
            'name': '申请日期',
            'field_type': 'date',
            'is_required': True,
            'default_value': 'TODAY',
            'sort_order': 4
        },
        {
            'code': 'items',
            'name': '采购项目',
            'field_type': 'textarea',
            'is_required': True,
            'sort_order': 5
        },
        {
            'code': 'amount',
            'name': '申请金额',
            'field_type': 'number',
            'is_required': True,
            'min_value': 0,
            'decimal_places': 2,
            'sort_order': 6
        },
        {
            'code': 'tax_amount',
            'name': '税额',
            'field_type': 'formula',
            'is_readonly': True,
            'formula_expression': 'amount * 0.13',
            'decimal_places': 2,
            'sort_order': 7
        },
        {
            'code': 'total_amount',
            'name': '总金额',
            'field_type': 'formula',
            'is_readonly': True,
            'formula_expression': 'amount + tax_amount',
            'decimal_places': 2,
            'sort_order': 8
        },
        {
            'code': 'status',
            'name': '状态',
            'field_type': 'choice',
            'is_required': True,
            'default_value': 'draft',
            'options': {
                'draft': '草稿',
                'pending': '待审批',
                'approved': '已批准',
                'rejected': '已拒绝'
            },
            'sort_order': 9
        },
        {
            'code': 'urgency',
            'name': '紧急程度',
            'field_type': 'choice',
            'is_required': True,
            'default_value': 'normal',
            'options': {
                'low': '低',
                'normal': '普通',
                'high': '紧急',
                'urgent': '非常紧急'
            },
            'sort_order': 10
        },
        {
            'code': 'attachments',
            'name': '附件',
            'field_type': 'file',
            'sort_order': 11
        },
        {
            'code': 'remark',
            'name': '备注',
            'field_type': 'textarea',
            'sort_order': 12
        }
    ]

    for field_data in fields:
        FieldDefinition.objects.create(
            business_object=business_object,
            **field_data
        )

    # 创建表单布局
    PageLayout.objects.create(
        business_object=business_object,
        code='form',
        name='表单布局',
        layout_type='form',
        layout_config={
            'sections': [
                {
                    'title': '基本信息',
                    'fields': ['request_no', 'requester', 'department', 'request_date'],
                    'collapsible': False
                },
                {
                    'title': '采购详情',
                    'fields': ['items', 'amount', 'tax_amount', 'total_amount'],
                    'collapsible': False
                },
                {
                    'title': '其他信息',
                    'fields': ['status', 'urgency', 'attachments', 'remark'],
                    'collapsible': True
                }
            ]
        }
    )

    # 创建列表布局
    PageLayout.objects.create(
        business_object=business_object,
        code='list',
        name='列表布局',
        layout_type='list',
        layout_config={
            'columns': [
                {'field': 'request_no', 'label': '申请单号', 'width': 150},
                {'field': 'requester', 'label': '申请人', 'width': 120},
                {'field': 'department', 'label': '申请部门', 'width': 150},
                {'field': 'amount', 'label': '申请金额', 'width': 120},
                {'field': 'total_amount', 'label': '总金额', 'width': 120},
                {'field': 'status', 'label': '状态', 'width': 100},
                {'field': 'urgency', 'label': '紧急程度', 'width': 100},
                {'field': 'created_at', 'label': '创建时间', 'width': 180}
            ],
            'page_size': 20,
            'show_row_number': True
        }
    )

    print(f"初始化完成: {business_object.name}")

# 在 Django shell 中执行:
# python manage.py shell
# >>> from apps.procurement.metadata import initialize_procurement_metadata
# >>> initialize_procurement_metadata()
```

### 7.3 快速参考

| 任务 | 方法 | 示例 |
|------|------|------|
| 创建业务对象 | `BusinessObject.objects.create()` | 见示例 |
| 添加字段 | `FieldDefinition.objects.create()` | 见示例 |
| 创建布局 | `PageLayout.objects.create()` | 见示例 |
| CRUD 操作 | `MetadataDrivenService` | 见示例 |
| 字段验证 | `DynamicFieldValidator` | 见示例 |
| 前端表单 | `MetadataDrivenForm` | 见示例 |
| 前端列表 | `MetadataDrivenList` | 见示例 |

---

**版本**: 1.0.0
**更新日期**: 2026-01-16
**维护人**: GZEAMS 开发团队

如需更多帮助，请参考:
- [metadata_driven.md](./metadata_driven.md) - 元数据驱动核心架构
- [dynamic_data_service.md](./dynamic_data_service.md) - 动态数据 CRUD 服务
- [metadata_validators.md](./metadata_validators.md) - 动态字段验证器
- [prd_writing_guide.md](./prd_writing_guide.md) - PRD 编写指南
