# Common Base Features: 公共功能模块

> 基于 `BaseModel` 构建的统一公共功能层

---

## 模块概述

本模块为 GZEAMS 系统提供统一的公共基类、API 规范和前端组件，消除重复代码，确保系统行为一致性。

---

## 核心基类引用速查

| 组件类型 | 基类名称 | 引用路径 | 自动获得功能 |
|---------|---------|---------|-------------|
| **Model** | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| **Serializer** | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields序列化 |
| **ViewSet** | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| **Filter** | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| **Service** | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |
| **Response** | BaseResponse | apps.common.responses.base.BaseResponse | 统一API响应格式 |
| **ExceptionHandler** | custom_exception_handler | apps.common.handlers.exceptions.custom_exception_handler | 统一错误处理 |

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [overview.md](./overview.md) | 总览 - 架构设计、功能清单、设计原则 |
| [backend.md](./backend.md) | 后端 - BaseModelSerializer、BaseModelViewSet、BaseCRUDService、BaseModelFilter |
| [api.md](./api.md) | API - 统一响应格式、错误码定义、批量操作规范 |
| [frontend.md](./frontend.md) | 前端 - BaseListPage、BaseFormPage、BaseDetailPage 组件 |
| [implementation.md](./implementation.md) | 实施 - 分阶段实施步骤、迁移指南、验收标准 |
| **元数据驱动扩展** | |
| [metadata_driven.md](./metadata_driven.md) | 元数据驱动 - MetadataDrivenSerializer/ViewSet/Filter 核心架构 |
| [dynamic_data_service.md](./dynamic_data_service.md) | 动态数据服务 - MetadataDrivenService CRUD 服务 |
| [metadata_validators.md](./metadata_validators.md) | 动态验证器 - DynamicFieldValidator 字段验证 |
| [metadata_frontend.md](./metadata_frontend.md) | 元数据前端 - Vue3 元数据驱动组件与 Hooks |
| [workflow_integration.md](./workflow_integration.md) | 工作流集成 - 配置驱动的审批流程集成 |
| [reporting.md](./reporting.md) | 动态报表 - ReportLayout 与 ECharts 可视化 |
| [field_cascade.md](./field_cascade.md) | 字段级联 - visibility/options/value 级联配置 |
| [data_migration.md](./data_migration.md) | 数据迁移 - Schema 版本化与数据迁移服务 |
| [data_change_approval.md](./data_change_approval.md) | 变更审批 - 已审核单据编辑后的数据流转 |

---

## 快速开始

### 后端使用

```python
# 1. 序列化器 - 自动获得公共字段序列化
from apps.common.serializers.base import BaseModelSerializer

class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', 'status']

# 2. ViewSet - 自动获得组织隔离、软删除、批量操作
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class AssetViewSet(BaseModelViewSetWithBatch):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

# 3. Service - 自动获得 CRUD 方法
from apps.common.services.base_crud import BaseCRUDService

class AssetService(BaseCRUDService):
    def __init__(self):
        super().__init__(Asset)
```

### 前端使用

```vue
<!-- 列表页面 -->
<BaseListPage
    title="资产列表"
    :fetch-method="fetchAssets"
    :columns="columns"
    @row-click="handleRowClick"
/>

<!-- 表单页面 -->
<BaseFormPage
    title="新建资产"
    :submit-method="handleSubmit"
    :rules="rules"
>
    <template #default="{ data }">
        <el-form-item label="资产编码" prop="code">
            <el-input v-model="data.code" />
        </el-form-item>
    </template>
</BaseFormPage>
```

---

## 功能清单

### P0 - 高优先级（传统模式）

| 功能 | 状态 |
|------|------|
| BaseModelSerializer | ✅ 已设计 |
| BaseModelViewSet | ✅ 已设计 |
| BaseCRUDService | ✅ 已设计 |
| BaseModelFilter | ✅ 已设计 |
| 批量操作 Mixin | ✅ 已设计 |
| BaseResponse | ✅ 已设计 |
| BaseExceptionHandler | ✅ 已设计 |
| BasePermission | ✅ 已设计 |
| BaseCacheMixin | ✅ 已设计 |

### P0 - 高优先级（元数据驱动低代码模式）

| 功能 | 状态 |
|------|------|
| MetadataDrivenSerializer | ✅ 已设计 |
| MetadataDrivenViewSet | ✅ 已设计 |
| MetadataDrivenService | ✅ 已设计 |
| DynamicFieldValidator | ✅ 已设计 |
| 元数据前端组件 (useMetadata/useValidation/useFormula) | ✅ 已设计 |
| 工作流配置驱动集成 | ✅ 已设计 |
| ReportLayout 动态报表 | ✅ 已设计 |
| 字段级联配置 (cascade_config) | ✅ 已设计 |
| Schema 版本化与数据迁移 | ✅ 已设计 |

### P2 - 中优先级（传统模式组件）

| 功能 | 状态 |
|------|------|
| BaseListPage 组件 | ✅ 已设计 |
| BaseFormPage 组件 | ✅ 已设计 |
| BaseDetailPage 组件 | ✅ 已设计 |
| BaseAuditInfo 组件 | ✅ 已设计 |
| BaseSearchBar 组件 | ✅ 已设计 |
| BaseTable 组件 | ✅ 已设计 |
| BasePagination 组件 | ✅ 已设计 |
| BaseFileUpload 组件 | ✅ 已设计 |
| 全局错误处理 | ✅ 已设计 |

### P2 - 中优先级（元数据驱动组件）

| 功能 | 状态 |
|------|------|
| MetadataDrivenList 组件 | ✅ 已设计 |
| MetadataDrivenForm 组件 | ✅ 已设计 |
| useMetadata Hook | ✅ 已设计 |
| useValidation Hook | ✅ 已设计 |
| useFormula Hook | ✅ 已设计 |

### P1 - 中优先级（API 规范）

| 功能 | 状态 |
|------|------|
| 统一响应格式 | ✅ 已设计 |
| 错误码定义 | ✅ 已设计 |
| 异常处理机制 | ✅ 已设计 |
| 批量操作 API | ✅ 已设计 |
| API 版本控制 | ✅ 已设计 |
| 数据导入导出 | ✅ 已设计 |

---

## 实施进度

- [ ] Phase 1: 后端基类实现（预计 14.5h）
- [ ] Phase 2: API 规范实现（预计 6.5h）
- [ ] Phase 3: 前端组件实现（预计 11h）
- [ ] Phase 4: 迁移试点（预计 8h）
- [ ] Phase 5: 全面迁移（预计 24h）
- [ ] Phase 6: 文档与测试（预计 12h）

---

## 参考文档

- [BaseModel 定义](../../../backend/apps/common/models.py)
- [多组织数据隔离](../phase1_2_multi_organization/)
- [技术架构规范](../architecture/technical-architecture.md)
