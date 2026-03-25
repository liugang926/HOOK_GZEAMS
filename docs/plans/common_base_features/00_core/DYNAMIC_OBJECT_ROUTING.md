# 动态对象路由系统 PRD

## 文档信息
| 项目 | 说明 |
|------|------|
| 功能名称 | 动态对象路由系统 |
| 功能代码 | DYNAMIC_OBJECT_ROUTING |
| 文档版本 | 1.0.0 |
| 创建日期 | 2026-01-27 |
| 审核状态 | ✅ 草稿 |

## 目录
1. [需求概述](#1-需求概述)
2. [后端实现](#2-后端实现)
3. [前端实现](#3-前端实现)
4. [API接口](#4-api接口)
5. [权限设计](#5-权限设计)
6. [标准对象自动注册](#6-标准对象自动注册)
7. [迁移计划](#7-迁移计划)
8. [附录](#8-附录)

## 1. 需求概述

### 1.1 业务背景

当前系统每个业务对象都需要独立配置URL路由：

**现状问题**:
| 问题 | 说明 | 影响 |
|------|------|------|
| 新增对象需配置urls.py | 每个新对象都要写路由配置 | 开发效率低 |
| 前端API调用分散 | 每个对象独立的API文件 | 维护成本高 |
| 不符合低代码原则 | 配置对象后仍需编码 | 违背平台定位 |

### 1.2 目标

**核心目标**: 实现完全动态的对象路由系统

1. **零代码扩展**: 新增业务对象无需编写路由代码
2. **统一API入口**: 所有对象通过 `/api/objects/{code}/` 访问
3. **自动注册**: 系统启动时自动注册标准对象
4. **双模式支持**: 支持硬编码对象和动态对象

### 1.3 功能范围

#### 本次实现范围
- ✅ 统一动态路由 `/api/objects/{code}/`
- ✅ ObjectRegistry 对象注册中心
- ✅ ObjectRouterViewSet 统一路由视图集
- ✅ 前端动态API客户端
- ✅ 标准对象自动注册
- ✅ 元数据接口 `/api/objects/{code}/metadata/`

#### 不在范围
- ❌ 工作流引擎路由（保留独立路由）
- ❌ 组织架构路由（保留独立路由）
- ❌ 认证路由（保留独立路由）

## 2. 后端实现

### 2.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 2.2 核心组件设计

#### 2.2.1 ObjectRegistry（对象注册中心）

```python
# backend/apps/system/services/object_registry.py

from typing import Dict, Optional, Type
from django.core.cache import cache
from django.utils.module_loading import import_string
from apps.system.models import BusinessObject, FieldDefinition

class ObjectMeta:
    """Business object metadata"""
    code: str
    name: str
    model_class: Optional[Type]
    viewset_class: Optional[Type]
    is_hardcoded: bool
    django_model_path: Optional[str]

class ObjectRegistry:
    """
    Business object registration center

    Functions:
    1. Auto-register standard objects on application startup
    2. Runtime object metadata caching
    3. Object code to model/ViewSet mapping
    """

    _registry: Dict[str, ObjectMeta] = {}

    @classmethod
    def register(cls, code: str, **metadata) -> ObjectMeta:
        """Register business object"""
        meta = ObjectMeta(code=code, **metadata)
        cls._registry[code] = meta
        return meta

    @classmethod
    def get(cls, code: str) -> Optional[ObjectMeta]:
        """Get from in-memory registry"""
        return cls._registry.get(code)

    @classmethod
    def get_or_create_from_db(cls, code: str) -> Optional[ObjectMeta]:
        """Get or create object metadata from database"""
        # Check cache first
        cache_key = f"object_meta:{code}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Get BusinessObject from database
        try:
            bo = BusinessObject.objects.get(code=code, is_active=True)
            meta = cls._build_meta_from_business_object(bo)
            cache.set(cache_key, meta, timeout=3600)
            return meta
        except BusinessObject.DoesNotExist:
            return None

    @classmethod
    def auto_register_standard_objects(cls):
        """Auto-register standard objects on application startup"""
        standard_objects = [
            # Asset Module
            {'code': 'Asset', 'name': '资产卡片', 'model': 'apps.assets.models.Asset'},
            {'code': 'AssetCategory', 'name': '资产分类', 'model': 'apps.assets.models.AssetCategory'},
            {'code': 'AssetPickup', 'name': '资产领用单', 'model': 'apps.assets.models.AssetPickup'},
            {'code': 'AssetTransfer', 'name': '资产调拨单', 'model': 'apps.assets.models.AssetTransfer'},
            {'code': 'AssetReturn', 'name': '资产归还单', 'model': 'apps.assets.models.AssetReturn'},
            {'code': 'AssetLoan', 'name': '资产借用单', 'model': 'apps.assets.models.AssetLoan'},
            {'code': 'Supplier', 'name': '供应商', 'model': 'apps.assets.models.Supplier'},
            {'code': 'Location', 'name': '存放地点', 'model': 'apps.assets.models.Location'},
            # Consumables Module
            {'code': 'Consumable', 'name': '低值易耗品', 'model': 'apps.consumables.models.Consumable'},
            {'code': 'ConsumableCategory', 'name': '易耗品分类', 'model': 'apps.consumables.models.ConsumableCategory'},
            {'code': 'ConsumableStock', 'name': '易耗品库存', 'model': 'apps.consumables.models.ConsumableStock'},
            {'code': 'ConsumablePurchase', 'name': '易耗品采购', 'model': 'apps.consumables.models.ConsumablePurchase'},
            {'code': 'ConsumableIssue', 'name': '易耗品领用', 'model': 'apps.consumables.models.ConsumableIssue'},
            # Lifecycle Module
            {'code': 'PurchaseRequest', 'name': '采购申请', 'model': 'apps.lifecycle.models.PurchaseRequest'},
            {'code': 'AssetReceipt', 'name': '资产入库单', 'model': 'apps.lifecycle.models.AssetReceipt'},
            {'code': 'Maintenance', 'name': '维修记录', 'model': 'apps.lifecycle.models.Maintenance'},
            {'code': 'MaintenancePlan', 'name': '维修计划', 'model': 'apps.lifecycle.models.MaintenancePlan'},
            {'code': 'MaintenanceTask', 'name': '维修任务', 'model': 'apps.lifecycle.models.MaintenanceTask'},
            {'code': 'DisposalRequest', 'name': '处置申请', 'model': 'apps.lifecycle.models.DisposalRequest'},
            # Inventory Module
            {'code': 'InventoryTask', 'name': '盘点任务', 'model': 'apps.inventory.models.InventoryTask'},
            {'code': 'InventorySnapshot', 'name': '盘点快照', 'model': 'apps.inventory.models.InventorySnapshot'},
            {'code': 'InventoryItem', 'name': '盘点明细', 'model': 'apps.inventory.models.InventoryItem'},
            # IT Asset Management
            {'code': 'ITAsset', 'name': 'IT设备', 'model': 'apps.it_assets.models.ITAsset'},
            # Software License
            {'code': 'SoftwareLicense', 'name': '软件许可', 'model': 'apps.software_licenses.models.SoftwareLicense'},
            # Leasing Management
            {'code': 'LeasingContract', 'name': '租赁合同', 'model': 'apps.leasing.models.LeasingContract'},
            # Insurance Management
            {'code': 'InsurancePolicy', 'name': '保险单', 'model': 'apps.insurance.models.InsurancePolicy'},
            # Finance Module
            {'code': 'DepreciationRecord', 'name': '折旧记录', 'model': 'apps.depreciation.models.DepreciationRecord'},
            {'code': 'FinanceVoucher', 'name': '财务凭证', 'model': 'apps.finance.models.FinanceVoucher'},
        ]

        for obj_def in standard_objects:
            cls._ensure_business_object_exists(obj_def)

    @classmethod
    def _ensure_business_object_exists(cls, obj_def: dict):
        """Ensure BusinessObject record exists in database"""
        from apps.system.models import BusinessObject

        bo, created = BusinessObject.objects.get_or_create(
            code=obj_def['code'],
            defaults={
                'name': obj_def['name'],
                'is_hardcoded': True,
                'django_model_path': obj_def['model'],
                'enable_workflow': True,
                'enable_version': True,
                'enable_soft_delete': True,
            }
        )
        if created:
            # Sync field definitions
            cls._sync_model_fields(bo)

    @classmethod
    def _sync_model_fields(cls, business_object: BusinessObject):
        """Sync field definitions for hardcoded models"""
        from apps.system.models import ModelFieldDefinition

        if not business_object.is_hardcoded or not business_object.django_model_path:
            return

        try:
            model_class = import_string(business_object.django_model_path)

            # Iterate model fields and create ModelFieldDefinition
            for field in model_class._meta.get_fields():
                if field.name.startswith('_'):
                    continue

                ModelFieldDefinition.objects.get_or_create(
                    business_object=business_object,
                    field_name=field.name,
                    defaults=ModelFieldDefinition.from_django_field(
                        business_object, field
                    ).__dict__
                )
        except ImportError:
            pass
```

#### 2.2.2 ObjectRouterViewSet（统一路由视图集）

```python
# backend/apps/system/viewsets/object_router.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.system.services.object_registry import ObjectRegistry
from apps.common.viewsets.metadata_driven import MetadataDrivenViewSet
from apps.common.responses.base import BaseResponse

class ObjectRouterViewSet(viewsets.ViewSet):
    """
    Unified dynamic object routing ViewSet

    URL: /api/objects/{code}/

    Route to corresponding business object based on object_code
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._delegate_viewset = None
        self._object_meta = None

    def initial(self, request, *args, **kwargs):
        """Initialize: Get corresponding ViewSet based on object_code"""
        super().initial(request, *args, **kwargs)

        object_code = kwargs.get('code')
        if not object_code:
            return BaseResponse.error('INVALID_REQUEST', 'object_code is required')

        # Get object metadata
        self._object_meta = ObjectRegistry.get_or_create_from_db(object_code)
        if not self._object_meta:
            return BaseResponse.not_found(f"Business object '{object_code}'")

        # Create delegated ViewSet instance
        self._delegate_viewset = self._create_delegate_viewset(
            self._object_meta, request
        )

    def _create_delegate_viewset(self, meta, request):
        """Create delegate ViewSet"""
        if meta.is_hardcoded and meta.django_model_path:
            return self._get_hardcoded_viewset(meta, request)
        else:
            return self._get_dynamic_viewset(meta, request)

    def _get_hardcoded_viewset(self, meta, request):
        """Get ViewSet for hardcoded objects"""
        viewset_map = {
            'Asset': 'apps.assets.viewsets.AssetViewSet',
            'AssetCategory': 'apps.assets.viewsets.AssetCategoryViewSet',
            'AssetPickup': 'apps.assets.viewsets.AssetPickupViewSet',
            'AssetTransfer': 'apps.assets.viewsets.AssetTransferViewSet',
            'AssetReturn': 'apps.assets.viewsets.AssetReturnViewSet',
            'AssetLoan': 'apps.assets.viewsets.AssetLoanViewSet',
            'Supplier': 'apps.assets.viewsets.SupplierViewSet',
            'Location': 'apps.assets.viewsets.LocationViewSet',
            'Consumable': 'apps.consumables.viewsets.ConsumableViewSet',
            'ConsumableCategory': 'apps.consumables.viewsets.ConsumableCategoryViewSet',
            # ... more mappings
        }

        viewset_path = viewset_map.get(meta.code)
        if viewset_path:
            from django.utils.module_loading import import_string
            viewset_class = import_string(viewset_path)
            viewset = viewset_class()
            viewset.request = request
            viewset.format_kwarg = None
            return viewset

        # If no ViewSet configured, use generic dynamic ViewSet
        return self._get_dynamic_viewset(meta, request)

    def _get_dynamic_viewset(self, meta, request):
        """Get dynamic ViewSet"""
        viewset = MetadataDrivenViewSet()
        viewset.business_object_code = meta.code
        viewset.request = request
        viewset.format_kwarg = None
        viewset.initial(request)
        return viewset

    # Delegate all standard methods
    def list(self, request, *args, **kwargs):
        return self._delegate_viewset.list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return self._delegate_viewset.retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return self._delegate_viewset.create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self._delegate_viewset.update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return self._delegate_viewset.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return self._delegate_viewset.destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='metadata')
    def metadata(self, request, *args, **kwargs):
        """Get object metadata"""
        if not self._object_meta:
            return BaseResponse.not_found('BusinessObject')

        from apps.system.models import FieldDefinition, PageLayout

        fields = FieldDefinition.objects.filter(
            business_object__code=self._object_meta.code,
            is_active=True
        )

        layouts = PageLayout.objects.filter(
            business_object__code=self._object_meta.code,
            is_deleted=False
        )

        return BaseResponse.success({
            'code': self._object_meta.code,
            'name': self._object_meta.name,
            'is_hardcoded': self._object_meta.is_hardcoded,
            'fields': [self._serialize_field(f) for f in fields],
            'layouts': {
                'form': next((l.layout_config for l in layouts if l.layout_type == 'form'), None),
                'list': next((l.layout_config for l in layouts if l.layout_type == 'list'), None),
            }
        })

    def _serialize_field(self, field):
        """Serialize field definition"""
        return {
            'code': field.code,
            'name': field.name,
            'field_type': field.field_type,
            'is_required': field.is_required,
            'is_readonly': field.is_readonly,
            'is_searchable': field.is_searchable,
            'sortable': field.sortable,
            'show_in_filter': field.show_in_filter,
            'options': field.options,
        }
```

### 2.3 URL配置更新

```python
# backend/config/urls.py

from django.urls import path, include
from apps.system.viewsets.object_router import ObjectRouterViewSet

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),

    # System-level routes (preserve)
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/system/', include('apps.system.urls')),
    path('api/workflows/', include('apps.workflows.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/permissions/', include('apps.permissions.urls')),

    # Unified dynamic object routing (new)
    path('api/objects/<str:code>/', ObjectRouterViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('api/objects/<str:code>/<uuid:id>/', ObjectRouterViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    path('api/objects/<str:code>/metadata/', ObjectRouterViewSet.as_view({
        'get': 'metadata'
    })),
]
```

### 2.4 应用启动钩子

```python
# backend/config/apps.py

from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'config'
    verbose_name = 'Core'

    def ready(self):
        """Execute on application startup"""
        # Import signals
        import config.signals

        # Auto-register standard business objects
        from apps.system.services.object_registry import ObjectRegistry
        ObjectRegistry.auto_register_standard_objects()
```

## 3. 前端实现

### 3.1 统一动态API客户端

```typescript
// frontend/src/api/dynamic.ts

import request from '@/utils/request'

export interface ObjectMetadata {
    code: string
    name: string
    is_hardcoded: boolean
    fields: FieldDefinition[]
    layouts: {
        form?: any
        list?: any
        detail?: any
    }
}

export interface FieldDefinition {
    code: string
    name: string
    field_type: string
    is_required: boolean
    is_readonly: boolean
    is_searchable: boolean
    sortable: boolean
    show_in_filter: boolean
    options?: any[]
}

class DynamicAPI {
    private baseUrl = '/api/objects'

    list(code: string, params?: any) {
        return request({
            url: `${this.baseUrl}/${code}/`,
            method: 'get',
            params
        })
    }

    get(code: string, id: string, params?: any) {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'get',
            params
        })
    }

    create(code: string, data: any) {
        return request({
            url: `${this.baseUrl}/${code}/`,
            method: 'post',
            data
        })
    }

    update(code: string, id: string, data: any) {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'put',
            data
        })
    }

    delete(code: string, id: string) {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'delete'
        })
    }

    batchDelete(code: string, ids: string[]) {
        return request({
            url: `${this.baseUrl}/${code}/batch-delete/`,
            method: 'post',
            data: { ids }
        })
    }

    getMetadata(code: string): Promise<ObjectMetadata> {
        return request({
            url: `${this.baseUrl}/${code}/metadata/`,
            method: 'get'
        })
    }
}

export const dynamicApi = new DynamicAPI()

export function createObjectClient(code: string) {
    return {
        list: (params?: any) => dynamicApi.list(code, params),
        get: (id: string, params?: any) => dynamicApi.get(code, id, params),
        create: (data: any) => dynamicApi.create(code, data),
        update: (id: string, data: any) => dynamicApi.update(code, id, data),
        delete: (id: string) => dynamicApi.delete(code, id),
        batchDelete: (ids: string[]) => dynamicApi.batchDelete(code, ids),
        getMetadata: () => dynamicApi.getMetadata(code)
    }
}

// Predefined standard object APIs (backward compatible)
export const assetApi = createObjectClient('Asset')
export const assetPickupApi = createObjectClient('AssetPickup')
export const assetTransferApi = createObjectClient('AssetTransfer')
export const consumableApi = createObjectClient('Consumable')
export const inventoryTaskApi = createObjectClient('InventoryTask')
```

### 3.2 动态页面组件

```vue
<!-- frontend/src/views/dynamic/DynamicListPage.vue -->
<template>
  <BaseListPage
    :title="objectMetadata?.name || '加载中...'"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :batch-delete-method="batchDelete"
    v-if="objectMetadata"
  >
    <template v-for="field in slotFields" #[field.slotName]="slotProps">
      <FieldRenderer
        :field-type="field.type"
        :value="slotProps.row[field.fieldCode]"
        :options="field.options"
      />
    </template>
  </BaseListPage>
  <el-skeleton v-else :rows="5" animated />
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { createObjectClient } from '@/api/dynamic'

const route = useRoute()
const objectCode = ref(route.params.code as string)
const objectMetadata = ref<ObjectMetadata | null>(null)
const apiClient = computed(() => createObjectClient(objectCode.value))

const columns = computed(() => {
    if (!objectMetadata.value) return []
    const listLayout = objectMetadata.value.layouts.list
    return listLayout?.columns || []
})

const searchFields = computed(() => {
    if (!objectMetadata.value) return []
    return objectMetadata.value.fields.filter(f => f.is_searchable)
})

const filterFields = computed(() => {
    if (!objectMetadata.value) return []
    return objectMetadata.value.fields.filter(f => f.show_in_filter)
})

const fetchData = (params: any) => apiClient.value.list(params)
const batchDelete = (data: any) => apiClient.value.batchDelete(data.ids)

onMounted(async () => {
    objectMetadata.value = await apiClient.value.getMetadata()
})
</script>
```

## 4. API接口

### 4.1 统一动态端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/objects/{code}/` | 列表查询 |
| POST | `/api/objects/{code}/` | 创建记录 |
| GET | `/api/objects/{code}/{id}/` | 获取详情 |
| PUT | `/api/objects/{code}/{id}/` | 更新记录 |
| PATCH | `/api/objects/{code}/{id}/` | 部分更新 |
| DELETE | `/api/objects/{code}/{id}/` | 删除记录 |
| GET | `/api/objects/{code}/metadata/` | 获取元数据 |
| POST | `/api/objects/{code}/batch-delete/` | 批量删除 |

### 4.2 保留的静态端点

| 路由 | 说明 |
|------|------|
| `/api/auth/` | 认证相关 |
| `/api/organizations/` | 组织架构 |
| `/api/system/business-objects/` | 元数据管理 |
| `/api/system/field-definitions/` | 字段定义 |
| `/api/system/page-layouts/` | 页面布局 |
| `/api/workflows/` | 工作流引擎 |

## 5. 权限设计

### 5.1 权限格式

动态对象权限格式: `{object_code}.{action}`

| 权限代码 | 说明 |
|---------|------|
| `Asset.view` | 查看资产 |
| `Asset.add` | 创建资产 |
| `Asset.change` | 编辑资产 |
| `Asset.delete` | 删除资产 |

### 5.2 权限检查

在 ObjectRouterViewSet 中动态检查权限：

```python
def check_permissions(self, request):
    """Dynamic permission check"""
    if self._object_meta:
        permission_code = f"{self._object_meta.code}.{self.action}"
        # Check if user has this permission
        if not request.user.has_perm(permission_code):
            self.permission_denied(request)
```

## 6. 标准对象自动注册

### 6.1 标准对象清单

完整清单见 2.2.1 节 ObjectRegistry.auto_register_standard_objects()

### 6.2 注册时机

应用启动时自动执行：`config/apps.py.ready()`

### 6.3 字段同步

对于硬编码对象，自动同步模型字段到 ModelFieldDefinition

## 7. 迁移计划

### 7.1 阶段1：核心基础设施

| 任务 | 文件 | 工作量 |
|------|------|--------|
| 创建 ObjectRegistry | apps/system/services/object_registry.py | 4h |
| 创建 ObjectRouterViewSet | apps/system/viewsets/object_router.py | 3h |
| 更新 URL 配置 | config/urls.py | 1h |
| 添加启动钩子 | config/apps.py | 1h |

### 7.2 阶段2：前端适配

| 任务 | 文件 | 工作量 |
|------|------|--------|
| 创建动态 API 客户端 | frontend/src/api/dynamic.ts | 2h |
| 创建动态页面组件 | frontend/src/views/dynamic/ | 6h |
| 更新路由配置 | frontend/src/router/index.ts | 1h |

### 7.3 阶段3：现有模块迁移

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 移除静态路由 | 删除各模块的 urls.py | 2h |
| 更新前端 API 调用 | 使用 dynamicApi | 4h |
| 验证功能 | 完整测试 | 4h |

## 8. 附录

### 8.1 相关文档

| 文档 | 路径 |
|------|------|
| PRD编写指南 | docs/plans/common_base_features/prd_writing_guide.md |
| API规范 | docs/plans/common_base_features/api.md |
| 元数据引擎 | docs/plans/phase1_3_business_metadata/overview.md |

### 8.2 变更历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-01-27 | 初始版本 |
