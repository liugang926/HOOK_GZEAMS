# Phase 1.3: 核心业务单据元数据配置 - 后端实现

## 1. 功能概述与业务场景

### 1.1 业务场景

**元数据驱动低代码引擎**是GZEAMS平台的核心能力,主要解决以下业务痛点:

| 传统痛点 | 低代码解决方案 |
|---------|---------------|
| 字段变更需要修改代码、重新部署 | 元数据配置字段,实时生效 |
| 表单布局固定死板,无法灵活调整 | 可视化布局配置,拖拽式设计 |
| 主子表关联复杂,开发成本高 | 内置关系支持,自动处理 |
| 流程字段权限动态变化 | 绑定工作流引擎,节点级权限控制 |
| 新业务单据开发周期长 | 配置化创建业务对象,零代码扩展 |

### 1.2 核心价值

- **零代码扩展**: 新增业务单据类型(如资产领用单、调拨单)无需修改代码
- **可视化配置**: 拖拽式表单/列表设计器,所见即所得
- **灵活存储**: PostgreSQL JSONB动态字段存储,支持复杂嵌套结构
- **无缝集成**: 与工作流引擎深度集成,实现字段级权限控制
- **主子表支持**: 原生支持主子表关系,自动级联处理

### 1.3 应用场景

1. **资产卡片**: 固定资产主数据的动态字段配置
2. **资产领用单**: 员工领用资产的申请单据
3. **资产调拨单**: 跨部门/跨组织的资产转移单据
4. **资产盘点单**: 盘点任务单据和明细记录
5. **资产处置单**: 资产报废/处置申请单据
6. **自定义单据**: 企业可自由扩展的业务单据类型

---

## 2. 用户角色与权限

| 角色 | 权限范围 | 说明 |
|------|---------|------|
| **系统管理员** | 全部权限 | 可管理所有业务对象、字段定义、页面布局 |
| **业务配置员** | 配置业务对象和字段 | 可创建/编辑业务对象和字段定义 |
| **表单设计师** | 设计表单布局 | 可配置表单和列表布局 |
| **普通用户** | 仅使用 | 只能使用配置好的表单创建/查看数据 |
| **开发人员** | 查看和导出 | 可查看元数据配置,导出JSON配置文件 |

---

## 3. 公共模型引用声明

本模块完全遵循 **Common Base Features** 规范,所有组件继承公共基类:

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 展开 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作、已删除记录管理 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 标准 CRUD 方法、复杂查询、分页 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、创建人过滤、软删除状态过滤 |

---

## 4. 数据模型设计

### 4.1 架构说明

本文档中的所有代码示例均基于 **Common Base Features** 规范实现:

- **所有模型** 继承 `BaseModel`(已内置组织隔离、软删除、审计字段)
- **所有序列化器** 继承 `BaseModelSerializer` 或 `BaseModelWithAuditSerializer`
- **所有 ViewSet** 继承 `BaseModelViewSetWithBatch`(自动获得批量操作能力)
- **所有 Service** 继承 `BaseCRUDService`(提供标准 CRUD 方法)
- **所有过滤器** 继承 `BaseModelFilter`(提供公共字段过滤)

详细规范参考: `docs/plans/common_base_features/backend.md`

### 4.2 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      元数据驱动低代码引擎                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐        │
│  │BusinessObject│───▶│FieldDefinition│───▶│  PageLayout  │        │
│  │  业务对象    │    │   字段定义    │    │   页面布局   │        │
│  │             │    │              │    │             │        │
│  │ - 资产卡片   │    │ - 基础字段   │    │ - 表单布局   │        │
│  │ - 领用单     │    │ - 自定义字段 │    │ - 列表布局   │        │
│  │ - 调拨单     │    │ - 公式字段   │    │ - 字段权限   │        │
│  │ - 盘点单     │    │ - 关联字段   │    │ - 显示规则   │        │
│  └─────────────┘    └──────────────┘    └─────────────┘        │
│         │                    │                     │            │
│         ▼                    ▼                     ▼            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              DynamicDataRepository (动态数据仓储)           │   │
│  │  - 基于PostgreSQL JSONB存储自定义字段                      │   │
│  │  - 支持主子表关系存储                                     │   │
│  │  - 自动版本控制和审计                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 BusinessObject (业务对象)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **基础信息** |
| code | string | max_length=50, unique, db_index | 对象编码（如 Asset, AssetPickup） |
| name | string | max_length=100 | 对象名称 |
| name_en | string | max_length=100, blank | 英文名称 |
| description | text | blank | 描述 |
| **功能配置** |
| enable_workflow | boolean | default=False | 是否启用审批流程 |
| enable_version | boolean | default=True | 是否启用版本控制 |
| enable_soft_delete | boolean | default=True | 是否启用软删除 |
| **表单配置** |
| default_form_layout | ForeignKey(PageLayout) | null=True | 默认表单布局 |
| default_list_layout | ForeignKey(PageLayout) | null=True | 默认列表布局 |
| **数据表配置** |
| table_name | string | max_length=100, blank | 数据表名（留空则使用dynamic_data_{code}） |

*注: 继承 BaseModel 自动获得 organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

**数据库索引**:
- `organization + code`

**核心方法**:
- `get_table_name()`: 返回 table_name 或 `dynamic_data_{code.lower()}`
- `field_count` (property): 字段定义数量
- `layout_count` (property): 布局数量

### 4.4 FieldDefinition (字段定义)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| business_object | ForeignKey(BusinessObject) | - | 业务对象 |
| **基础信息** |
| code | string | max_length=50 | 字段编码 |
| name | string | max_length=100 | 字段名称 |
| **字段类型** (choices) |
| field_type | string | choices=[text, textarea, number, currency, date, datetime, select, multi_select, radio, checkbox, boolean, user, department, reference, formula, sub_table, file, image, rich_text, qr_code, barcode] | 字段类型 |
| **字段属性** |
| is_required | boolean | default=False | 必填 |
| is_unique | boolean | default=False | 唯一值 |
| is_readonly | boolean | default=False | 只读 |
| is_system | boolean | default=False | 系统字段（不允许删除） |
| is_searchable | boolean | default=False | 可搜索 |
| **显示配置** |
| show_in_list | boolean | default=False | 显示在列表 |
| show_in_detail | boolean | default=True | 显示在详情 |
| show_in_filter | boolean | default=False | 显示在筛选 |
| sort_order | int | default=0 | 排序号 |
| **列显示配置** |
| column_width | int | null=True | 列宽度 |
| min_column_width | int | null=True | 最小列宽 |
| fixed | string | choices=[left, right], blank | 固定列 |
| sortable | boolean | default=True | 可排序 |
| **默认值** |
| default_value | text | blank | 支持变量: {current_user}, {today}, {now}等 |
| **选项配置** (select/multi_select等) |
| options | JSONField | default=list, blank | 格式: [{"value": "v1", "label": "选项1"}] |
| **关联配置** (reference类型) |
| reference_object | string | max_length=50, blank | 关联对象编码 |
| reference_display_field | string | max_length=50, default='name', blank | 关联显示字段 |
| **数字字段配置** |
| decimal_places | int | default=0 | 小数位数 |
| min_value | decimal | max_digits=20, decimal_places=4, null=True | 最小值 |
| max_value | decimal | max_digits=20, decimal_places=4, null=True | 最大值 |
| **文本字段配置** |
| max_length | int | default=255 | 最大长度 |
| placeholder | string | max_length=200, blank | 占位符 |
| regex_pattern | string | max_length=500, blank | 正则校验 |
| **公式字段配置** |
| formula | text | blank | 计算公式（支持简单表达式: {field1} + {field2}） |
| **子表配置** |
| sub_table_fields | JSONField | default=list, blank | 子表字段定义 |

*注: 继承 BaseModel 自动获得公共字段*

**数据库索引**:
- `organization + business_object + code` (unique_together)
- `organization + business_object + code`
- `organization + field_type`

**验证方法** (clean):
- reference类型必须有 reference_object
- formula类型必须有 formula
- sub_table类型必须有 sub_table_fields

### 4.5 PageLayout (页面布局)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| business_object | ForeignKey(BusinessObject) | - | 业务对象 |
| **基础信息** |
| layout_code | string | max_length=50 | 布局编码 |
| layout_name | string | max_length=100 | 布局名称 |
| layout_type | string | choices=[form, list, detail, search] | 布局类型 |
| **布局配置** |
| layout_config | JSONField | default=dict | JSON格式的布局结构定义 |

**form类型配置示例**:
```json
{
  "sections": [{
    "title": "基础信息",
    "columns": 2,
    "collapsible": true,
    "collapsed": false,
    "fields": ["field1", "field2", "field3"]
  }]
}
```

**list类型配置示例**:
```json
{
  "columns": ["field1", "field2", "field3"],
  "default_sort": "-created_at",
  "row_actions": ["view", "edit", "delete"]
}
```

*注: 继承 BaseModel 自动获得公共字段*

**数据库索引**:
- `organization + business_object + layout_code`

### 4.6 DynamicData (动态数据)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| business_object | ForeignKey(BusinessObject) | - | 业务对象 |
| **数据编号** |
| data_no | string | max_length=50, db_index | 数据编号（自动生成，如 ASSET202401010001） |
| **状态** |
| status | string | max_length=50, default='draft' | 状态 |
| **动态字段数据** |
| dynamic_fields | JSONField | default=dict | PostgreSQL JSONB类型，支持高效查询 |

*注: 继承 BaseModel 自动获得公共字段*

**数据库索引**:
- `organization + business_object`
- `organization + business_object + created_by`
- `organization + business_object + status`

**核心方法**:
- `get_field_value(field_code)`: 获取字段值
- `set_field_value(field_code, value)`: 设置字段值
- `get_sub_table_data(field_code)`: 获取子表数据（返回 `{field_code}_items`）

### 4.7 DynamicSubTableData (动态子表数据)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **关联** |
| parent_data | ForeignKey(DynamicData) | - | 主数据 |
| field_definition | ForeignKey(FieldDefinition) | - | 字段定义 |
| **行数据** |
| row_order | int | default=0 | 行号 |
| row_data | JSONField | default=dict | 行数据 |

*注: 继承 BaseModel 自动获得公共字段*

**数据库索引**:
- `organization + parent_data + field_definition`

---

## 5. 测试用例

### 5.1 模型测试

#### 组织隔离测试
- 测试不同组织的业务对象数据完全隔离
- 验证跨组织数据访问被正确阻止
- 测试组织管理员只能管理本组织数据

#### 软删除功能测试
- 测试删除操作使用软删除而非物理删除
- 验证已删除记录在默认查询中不可见
- 测试 `/deleted/` 接口能正确列出已删除记录
- 测试 `/{id}/restore/` 接口能恢复软删除记录

#### 审计字段自动设置测试
- 验证创建时自动设置 `created_by` 和 `created_at`
- 验证更新时自动设置 `updated_at`
- 测试 `created_by` 正确关联到当前操作用户

### 5.2 API测试

#### CRUD操作测试
- 测试标准的CRUD接口符合统一响应格式
- 验证分页、搜索、过滤功能正常工作
- 测试嵌套序列化（如created_by用户信息）

#### 批量操作测试
- 测试 `POST /batch-delete/` 接口
- 测试 `POST /batch-restore/` 接口
- 测试 `POST /batch-update/` 接口
- 验证批量操作返回格式包含 success/fail 统计

#### 权限控制测试
- 测试不同角色对元数据的访问权限
- 验证未授权访问返回 403 错误
- 测试系统管理员拥有完全权限

### 5.3 边界条件测试

#### 空值处理
- 测试必填字段验证
- 测试空字符串和null值的处理
- 验证JSONB字段空值存储

#### 并发操作
- 测试并发更新同一记录的乐观锁机制
- 测试高并发下的数据一致性
- 验证批量操作的原子性

#### 数据一致性
- 测试业务对象和字段定义的关联完整性
- 验证外键约束和级联删除
- 测试动态数据与元数据的一致性

---

## 6. 序列化器设计

```python
# apps/system/serializers.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData,
    DynamicSubTableData
)


class BusinessObjectSerializer(BaseModelSerializer):
    """
    业务对象序列化器

    继承 BaseModelSerializer 自动获得:
    - id, organization, is_deleted, deleted_at
    - created_at, updated_at, created_by
    - custom_fields 处理
    """

    field_count = serializers.IntegerField(read_only=True)
    layout_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BusinessObject
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'name_en', 'description',
            'enable_workflow', 'enable_version', 'enable_soft_delete',
            'default_form_layout', 'default_list_layout', 'table_name',
            'field_count', 'layout_count'
        ]


class FieldDefinitionSerializer(BaseModelSerializer):
    """字段定义序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = FieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'code', 'name', 'field_type',
            'is_required', 'is_unique', 'is_readonly', 'is_system', 'is_searchable',
            'show_in_list', 'show_in_detail', 'show_in_filter', 'sort_order',
            'column_width', 'min_column_width', 'fixed', 'sortable',
            'default_value', 'options', 'reference_object', 'reference_display_field',
            'decimal_places', 'min_value', 'max_value',
            'max_length', 'placeholder', 'regex_pattern',
            'formula', 'sub_table_fields'
        ]


class PageLayoutSerializer(BaseModelSerializer):
    """页面布局序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = PageLayout
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'layout_code', 'layout_name',
            'layout_type', 'layout_config'
        ]


class DynamicDataSerializer(BaseModelSerializer):
    """动态数据序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = DynamicData
        fields = BaseModelSerializer.Meta.fields + [
            'business_object', 'data_no', 'status', 'dynamic_fields'
        ]


class DynamicDataDetailSerializer(BaseModelWithAuditSerializer):
    """
    动态数据详情序列化器 - 包含完整审计信息
    """

    business_object = BusinessObjectSerializer(read_only=True)

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = DynamicData
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'business_object', 'data_no', 'status', 'dynamic_fields'
        ]


class DynamicSubTableDataSerializer(BaseModelSerializer):
    """动态子表数据序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = DynamicSubTableData
        fields = BaseModelSerializer.Meta.fields + [
            'parent_data', 'field_definition', 'row_order', 'row_data'
        ]
```

---

## 6. 过滤器设计

```python
# apps/system/filters.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData
)


class BusinessObjectFilter(BaseModelFilter):
    """业务对象过滤器 - 继承公共过滤基类"""

    code = filters.CharFilter(lookup_expr='icontains', label='对象编码')
    name = filters.CharFilter(lookup_expr='icontains', label='对象名称')
    enable_workflow = filters.BooleanFilter(label='启用工作流')

    class Meta(BaseModelFilter.Meta):
        model = BusinessObject
        fields = BaseModelFilter.Meta.fields + ['code', 'name', 'enable_workflow']


class FieldDefinitionFilter(BaseModelFilter):
    """字段定义过滤器 - 继承公共过滤基类"""

    code = filters.CharFilter(lookup_expr='icontains', label='字段编码')
    name = filters.CharFilter(lookup_expr='icontains', label='字段名称')
    field_type = filters.ChoiceFilter(
        choices=FieldDefinition.FIELD_TYPE_CHOICES,
        label='字段类型'
    )

    class Meta(BaseModelFilter.Meta):
        model = FieldDefinition
        fields = BaseModelFilter.Meta.fields + ['code', 'name', 'field_type']


class DynamicDataFilter(BaseModelFilter):
    """动态数据过滤器 - 继承公共过滤基类"""

    data_no = filters.CharFilter(lookup_expr='icontains', label='数据编号')
    status = filters.CharFilter(lookup_expr='exact', label='状态')

    class Meta(BaseModelFilter.Meta):
        model = DynamicData
        fields = BaseModelFilter.Meta.fields + ['data_no', 'status']
```

---

## 7. API 接口设计

### 7.1 接口概览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/system/business-objects/` | 获取业务对象列表 | 管理员 |
| POST | `/api/system/business-objects/` | 创建业务对象 | 管理员 |
| GET | `/api/system/business-objects/{code}/` | 获取业务对象详情 | 管理员 |
| PUT | `/api/system/business-objects/{code}/` | 更新业务对象 | 管理员 |
| DELETE | `/api/system/business-objects/{code}/` | 删除业务对象 | 管理员 |
| GET | `/api/system/field-definitions/` | 获取字段定义列表 | 管理员 |
| POST | `/api/system/field-definitions/` | 创建字段定义 | 管理员 |
| GET | `/api/system/page-layouts/` | 获取页面布局列表 | 管理员 |
| POST | `/api/system/page-layouts/` | 创建页面布局 | 管理员 |
| GET | `/api/dynamic/{object_code}/` | 查询动态数据 | 全部用户 |
| POST | `/api/dynamic/{object_code}/` | 创建动态数据 | 全部用户 |
| GET | `/api/dynamic/{object_code}/{id}/` | 获取动态数据详情 | 全部用户 |
| PUT | `/api/dynamic/{object_code}/{id}/` | 更新动态数据 | 全部用户 |
| DELETE | `/api/dynamic/{object_code}/{id}/` | 删除动态数据 | 全部用户 |

### 7.2 ViewSet 设计

```python
# apps/system/views.py

from rest_framework import viewsets
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.system.models import (
    BusinessObject,
    FieldDefinition,
    PageLayout,
    DynamicData
)
from apps.system.serializers import (
    BusinessObjectSerializer,
    FieldDefinitionSerializer,
    PageLayoutSerializer,
    DynamicDataSerializer,
    DynamicDataDetailSerializer
)
from apps.system.filters import (
    BusinessObjectFilter,
    FieldDefinitionFilter,
    DynamicDataFilter
)
from apps.system.services.metadata_service import MetadataService
from apps.system.services.dynamic_data_service import DynamicDataService


class BusinessObjectViewSet(BaseModelViewSetWithBatch):
    """
    业务对象 ViewSet

    继承 BaseModelViewSetWithBatch 自动获得:
    - 组织隔离、软删除、批量操作、审计字段
    """

    queryset = BusinessObject.objects.all()
    serializer_class = BusinessObjectSerializer
    filterset_class = BusinessObjectFilter
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'created_at']


class FieldDefinitionViewSet(BaseModelViewSetWithBatch):
    """字段定义 ViewSet"""

    queryset = FieldDefinition.objects.all()
    serializer_class = FieldDefinitionSerializer
    filterset_class = FieldDefinitionFilter
    search_fields = ['code', 'name']
    ordering_fields = ['sort_order', 'created_at']


class PageLayoutViewSet(BaseModelViewSetWithBatch):
    """页面布局 ViewSet"""

    queryset = PageLayout.objects.all()
    serializer_class = PageLayoutSerializer
    search_fields = ['layout_code', 'layout_name']
    ordering_fields = ['layout_code', 'created_at']


class DynamicDataViewSet(BaseModelViewSetWithBatch):
    """动态数据 ViewSet"""

    queryset = DynamicData.objects.all()
    serializer_class = DynamicDataSerializer
    filterset_class = DynamicDataFilter
    search_fields = ['data_no']
    ordering_fields = ['created_at', 'data_no']

    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'retrieve':
            return DynamicDataDetailSerializer
        return DynamicDataSerializer

    def create(self, request, *args, **kwargs):
        """创建动态数据 - 使用 DynamicDataService"""
        business_object_code = request.data.get('business_object_code')
        if not business_object_code:
            return Response(
                {'detail': '必须提供 business_object_code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = DynamicDataService(business_object_code)
        try:
            data = request.data.get('dynamic_fields', {})
            result = service.create(data)
            serializer = DynamicDataDetailSerializer(result)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
```

---

## 8. 服务层设计

### 8.1 MetadataService(元数据服务)

```python
# apps/system/services/metadata_service.py

from typing import Dict, List, Optional, Any
from django.db import transaction
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.common.services.base_crud import BaseCRUDService


class MetadataService(BaseCRUDService):
    """
    元数据服务 - 管理业务对象、字段定义、页面布局

    继承 BaseCRUDService 获得基础 CRUD 能力
    """

    def __init__(self):
        super().__init__(BusinessObject)
        self.cache = {}

    @transaction.atomic
    def create_business_object(self, data: Dict) -> BusinessObject:
        """
        创建业务对象及完整的元数据定义

        Args:
            data: 业务对象定义数据,格式:
                {
                    "code": "Asset",
                    "name": "资产卡片",
                    "description": "固定资产主数据",
                    "enable_workflow": false,
                    "fields": [...],
                    "page_layouts": [...]
                }

        Returns:
            BusinessObject: 创建的业务对象
        """
        # 创建业务对象
        obj, created = BusinessObject.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': data['name'],
                'name_en': data.get('name_en', ''),
                'description': data.get('description', ''),
                'enable_workflow': data.get('enable_workflow', False),
                'enable_version': data.get('enable_version', True),
            }
        )

        if not created:
            # 更新现有对象
            obj.name = data['name']
            obj.description = data.get('description', '')
            obj.enable_workflow = data.get('enable_workflow', False)
            obj.save()

        # 创建/更新字段定义
        for field_data in data.get('fields', []):
            self._create_or_update_field(obj, field_data)

        # 创建/更新页面布局
        for layout_data in data.get('page_layouts', []):
            self._create_or_update_layout(obj, layout_data)

        # 清除缓存
        self._clear_cache(obj.code)

        return obj

    def _create_or_update_field(self, obj: BusinessObject, data: Dict) -> FieldDefinition:
        """创建或更新字段定义"""
        field, created = FieldDefinition.objects.get_or_create(
            business_object=obj,
            code=data['code'],
            defaults={
                'name': data['name'],
                'field_type': data.get('field_type', 'text'),
                'is_required': data.get('is_required', False),
                'is_unique': data.get('is_unique', False),
                'is_readonly': data.get('is_readonly', False),
                'is_system': data.get('is_system', False),
                'is_searchable': data.get('is_searchable', False),
                'show_in_list': data.get('show_in_list', False),
                'show_in_detail': data.get('show_in_detail', True),
                'show_in_filter': data.get('show_in_filter', False),
                'sort_order': data.get('sort_order', 0),
                'default_value': data.get('default_value', ''),
                'options': data.get('options', []),
                'reference_object': data.get('reference_object', ''),
                'reference_display_field': data.get('reference_display_field', 'name'),
                'decimal_places': data.get('decimal_places', 2),
                'max_length': data.get('max_length', 255),
                'formula': data.get('formula', ''),
                'sub_table_fields': data.get('sub_table_fields', []),
            }
        )

        if not created:
            # 更新字段
            for key, value in data.items():
                if hasattr(field, key):
                    setattr(field, key, value)
            field.save()

        return field

    def _create_or_update_layout(self, obj: BusinessObject, data: Dict) -> PageLayout:
        """创建或更新页面布局"""
        layout, created = PageLayout.objects.get_or_create(
            business_object=obj,
            layout_code=data['layout_code'],
            defaults={
                'layout_name': data.get('layout_name', data['layout_code']),
                'layout_type': data.get('layout_type', 'form'),
                'layout_config': data.get('layout_config', {}),
            }
        )

        if not created:
            layout.layout_name = data.get('layout_name', data['layout_code'])
            layout.layout_config = data.get('layout_config', {})
            layout.save()

        # 设置为默认布局
        if data.get('is_default'):
            if layout.layout_type == 'form':
                obj.default_form_layout = layout
            elif layout.layout_type == 'list':
                obj.default_list_layout = layout
            obj.save()

        return layout

    def get_business_object(self, code: str) -> Optional[BusinessObject]:
        """获取业务对象(带缓存)"""
        if code not in self.cache:
            try:
                obj = BusinessObject.objects.get(code=code)
                self.cache[code] = obj
            except BusinessObject.DoesNotExist:
                return None
        return self.cache[code]

    def get_field_definitions(self, obj_code: str) -> List[FieldDefinition]:
        """获取字段定义列表"""
        obj = self.get_business_object(obj_code)
        if not obj:
            return []
        return list(obj.field_definitions.all())

    def get_page_layout(self, obj_code: str, layout_code: str) -> Optional[PageLayout]:
        """获取页面布局"""
        obj = self.get_business_object(obj_code)
        if not obj:
            return None
        try:
            return obj.page_layouts.get(layout_code=layout_code)
        except PageLayout.DoesNotExist:
            return None

    def delete_business_object(self, code: str) -> bool:
        """删除业务对象(软删除)"""
        obj = self.get_business_object(code)
        if obj:
            obj.soft_delete()
            self._clear_cache(code)
            return True
        return False

    def _clear_cache(self, code: str = None):
        """清除缓存"""
        if code:
            self.cache.pop(code, None)
        else:
            self.cache.clear()
```

### 8.2 DynamicDataService(动态数据服务)

```python
# apps/system/services/dynamic_data_service.py

from typing import Dict, List, Any, Optional
from django.db import transaction
from django.db.models import Q
from apps.system.models import BusinessObject, DynamicData
from apps.common.services.base_crud import BaseCRUDService
import re


class DynamicDataService(BaseCRUDService):
    """
    动态数据服务 - 处理业务对象的CRUD操作

    继承 BaseCRUDService 获得基础 CRUD 能力
    """

    def __init__(self, business_object_code: str):
        super().__init__(DynamicData)
        self.bo_code = business_object_code
        self.metadata_service = MetadataService()
        self.business_object = self.metadata_service.get_business_object(business_object_code)

    def query(self, filters: Dict = None, search: str = None,
              page: int = 1, page_size: int = 20, sort: str = None) -> Dict:
        """
        查询动态数据

        Args:
            filters: 过滤条件 {"field_code": "value"}
            search: 搜索关键词(搜索可搜索字段)
            page: 页码
            page_size: 每页数量
            sort: 排序字段

        Returns:
            {"items": [], "total": 0, "page": page, "page_size": page_size}
        """
        if not self.business_object:
            raise ValueError(f"业务对象 {self.bo_code} 不存在")

        # 构建查询
        qs = DynamicData.objects.filter(
            business_object=self.business_object,
            is_deleted=False
        )

        # 应用过滤器
        if filters:
            for field_code, value in filters.items():
                # JSONB字段查询
                qs = qs.filter(**{f'dynamic_fields__{field_code}': value})

        # 应用搜索
        if search:
            searchable_fields = self.business_object.field_definitions.filter(
                is_searchable=True
            )
            search_q = Q()
            for field in searchable_fields:
                search_q |= Q(**{f'dynamic_fields__{field.code}__icontains': search})
            qs = qs.filter(search_q)

        # 应用排序
        if sort:
            if sort.startswith('-'):
                field_name = sort[1:]
                qs = qs.order_by(f'-dynamic_fields__{field_name}')
            else:
                qs = qs.order_by(f'dynamic_fields__{sort}')
        else:
            qs = qs.order_by('-created_at')

        # 分页
        total = qs.count()
        start = (page - 1) * page_size
        items = qs[start:start + page_size]

        # 格式化输出
        return {
            'items': [self._serialize_data(item) for item in items],
            'total': total,
            'page': page,
            'page_size': page_size
        }

    def get(self, data_id: int) -> Optional[Dict]:
        """获取单条数据"""
        try:
            data = DynamicData.objects.get(
                id=data_id,
                business_object=self.business_object,
                is_deleted=False
            )
            return self._serialize_data(data, include_all_fields=True)
        except DynamicData.DoesNotExist:
            return None

    def create(self, data: Dict) -> Dict:
        """
        创建动态数据

        Args:
            data: {"field_code": value, ...}

        Returns:
            创建的数据记录
        """
        if not self.business_object:
            raise ValueError(f"业务对象 {self.bo_code} 不存在")

        # 验证必填字段
        field_defs = {f.code: f for f in self.business_object.field_definitions.all()}
        for field in field_defs.values():
            if field.is_required and field.code not in data:
                raise ValueError(f"必填字段 {field.name} 不能为空")

        # 处理默认值
        for field in field_defs.values():
            if field.code not in data and field.default_value:
                data[field.code] = self._parse_default_value(field.default_value)

        # 生成数据编号
        data_no = self._generate_data_no()

        # 处理公式字段
        data = self._calculate_formulas(data, field_defs)

        # 创建记录
        dynamic_data = DynamicData.objects.create(
            business_object=self.business_object,
            data_no=data_no,
            dynamic_fields=data,
            status='draft'
        )

        return self._serialize_data(dynamic_data, include_all_fields=True)

    def update(self, data_id: int, data: Dict) -> Dict:
        """更新动态数据"""
        try:
            dynamic_data = DynamicData.objects.get(
                id=data_id,
                business_object=self.business_object,
                is_deleted=False
            )
        except DynamicData.DoesNotExist:
            raise ValueError(f"数据记录 {data_id} 不存在")

        # 获取现有数据
        current_fields = dynamic_data.dynamic_fields.copy()
        current_fields.update(data)

        # 重新计算公式
        field_defs = {f.code: f for f in self.business_object.field_definitions.all()}
        current_fields = self._calculate_formulas(current_fields, field_defs)

        # 更新
        dynamic_data.dynamic_fields = current_fields
        dynamic_data.save()

        return self._serialize_data(dynamic_data, include_all_fields=True)

    def _serialize_data(self, data: DynamicData, include_all_fields: bool = False) -> Dict:
        """序列化数据"""
        field_defs = {f.code: f for f in self.business_object.field_definitions.all()}

        result = {
            'id': data.id,
            'data_no': data.data_no,
            'status': data.status,
            'created_at': data.created_at.isoformat(),
            'updated_at': data.updated_at.isoformat(),
            'created_by': data.created_by_id,
        }

        # 添加动态字段
        for field_code, field_def in field_defs.items():
            value = data.dynamic_fields.get(field_code)

            # 只返回显示在列表的字段(如果不要求全部字段)
            if not include_all_fields and not field_def.show_in_list:
                continue

            result[field_code] = value

        return result

    def _generate_data_no(self) -> str:
        """生成数据编号"""
        from django.utils import timezone

        prefix = self.bo_code.upper()
        date_str = timezone.now().strftime('%Y%m%d')

        # 查找今日最大编号
        today_prefix = f"{prefix}{date_str}"
        max_no = DynamicData.objects.filter(
            business_object=self.business_object,
            data_no__startswith=today_prefix
        ).order_by('-data_no').first()

        if max_no:
            # 提取序号并递增
            seq = int(max_no.data_no[-4:]) + 1
        else:
            seq = 1

        return f"{today_prefix}{seq:04d}"

    def _parse_default_value(self, value: str) -> Any:
        """解析默认值(支持变量)"""
        if not isinstance(value, str):
            return value

        variables = {
            '{current_user}': self._get_current_user_id,
            '{today}': lambda: timezone.now().date().isoformat(),
            '{now}': lambda: timezone.now().isoformat(),
        }

        for var, getter in variables.items():
            if var in value:
                return value.replace(var, getter())

        return value

    def _calculate_formulas(self, data: Dict, field_defs: Dict) -> Dict:
        """计算公式字段"""
        from simpleeval import simple_eval, InvalidExpression

        for field_code, field_def in field_defs.items():
            if field_def.field_type == 'formula' and field_def.formula:
                try:
                    # 解析公式 {field1} + {field2}
                    expression = field_def.formula
                    # 替换变量
                    for fc, fv in data.items():
                        expression = re.sub(
                            rf'\{{{fc}\}}',
                            str(fv) if fv is not None else '0',
                            expression
                        )
                    # 计算
                    result = simple_eval(expression)
                    data[field_code] = result
                except (InvalidExpression, ValueError):
                    data[field_code] = 0

        return data

    def _get_current_user_id(self) -> int:
        """获取当前用户ID"""
        from apps.common.services.organization_service import get_current_request

        request = get_current_request()
        return request.user.id if request and request.user.is_authenticated else None
```

---

## 9. 管理命令

```python
# apps/system/management/commands/load_metadata.py

from django.core.management.base import BaseCommand
import json


class Command(BaseCommand):
    help = '加载业务对象元数据配置'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='backend/fixtures/business_objects_metadata.json',
            help='元数据配置文件路径'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='更新已存在的业务对象'
        )

    def handle(self, *args, **options):
        from apps.system.services.metadata_service import MetadataService

        file_path = options['file']
        update = options['update']

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'文件不存在: {file_path}')
            )
            return
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON格式错误: {e}')
            )
            return

        service = MetadataService()
        count = 0

        for obj_data in data.get('business_objects', []):
            code = obj_data.get('code')
            name = obj_data.get('name')

            try:
                # 检查是否已存在
                existing = service.get_business_object(code)

                if existing and not update:
                    self.stdout.write(
                        self.style.WARNING(f'跳过已存在的对象: {name} ({code})')
                    )
                    continue

                service.create_business_object(obj_data)
                count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 加载业务对象: {name} ({code})')
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ 加载失败 {name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n完成!共加载 {count} 个业务对象')
        )
```

---

## 10. 元数据配置文件示例

```json
// backend/fixtures/business_objects_metadata.json

{
  "business_objects": [
    {
      "code": "Asset",
      "name": "资产卡片",
      "name_en": "Asset",
      "description": "固定资产主数据",
      "enable_workflow": false,
      "enable_version": true,
      "fields": [
        {
          "code": "asset_code",
          "name": "资产编码",
          "field_type": "text",
          "is_required": true,
          "is_unique": true,
          "is_readonly": true,
          "show_in_list": true,
          "sort_order": 1
        },
        {
          "code": "asset_name",
          "name": "资产名称",
          "field_type": "text",
          "is_required": true,
          "show_in_list": true,
          "is_searchable": true,
          "sort_order": 2
        },
        {
          "code": "category_id",
          "name": "资产分类",
          "field_type": "reference",
          "reference_object": "AssetCategory",
          "is_required": true,
          "show_in_list": true,
          "sort_order": 3
        },
        {
          "code": "purchase_price",
          "name": "购置原值",
          "field_type": "currency",
          "decimal_places": 2,
          "is_required": true,
          "show_in_list": true,
          "sort_order": 10
        },
        {
          "code": "custodian_id",
          "name": "保管人",
          "field_type": "user",
          "show_in_list": true,
          "sort_order": 15
        },
        {
          "code": "location_id",
          "name": "存放地点",
          "field_type": "reference",
          "reference_object": "Location",
          "show_in_list": true,
          "sort_order": 16
        },
        {
          "code": "asset_status",
          "name": "资产状态",
          "field_type": "select",
          "options": [
            {"value": "pending", "label": "待入库"},
            {"value": "in_use", "label": "在用"},
            {"value": "idle", "label": "闲置"},
            {"value": "maintenance", "label": "维修中"},
            {"value": "scrapped", "label": "已报废"}
          ],
          "default_value": "pending",
          "show_in_list": true,
          "sort_order": 20
        }
      ],
      "page_layouts": [
        {
          "layout_code": "asset_form",
          "layout_name": "资产表单",
          "layout_type": "form",
          "is_default": true,
          "layout_config": {
            "sections": [
              {
                "title": "基础信息",
                "columns": 2,
                "fields": ["asset_code", "asset_name", "category_id", "specification", "brand", "model"]
              },
              {
                "title": "财务信息",
                "columns": 2,
                "fields": ["purchase_price", "current_value", "accumulated_depreciation", "purchase_date"]
              },
              {
                "title": "使用信息",
                "columns": 2,
                "fields": ["custodian_id", "department_id", "location_id", "asset_status"]
              }
            ]
          }
        },
        {
          "layout_code": "asset_list",
          "layout_name": "资产列表",
          "layout_type": "list",
          "is_default": true,
          "layout_config": {
            "columns": ["asset_code", "asset_name", "category_id", "custodian_id", "location_id", "asset_status", "purchase_price"],
            "default_sort": "-created_at"
          }
        }
      ]
    }
  ]
}
```

---

## 11. 实施检查清单

### 11.1 后端实施清单

- [ ] 创建核心数据模型(BusinessObject, FieldDefinition, PageLayout) - 继承 BaseModel
- [ ] 创建动态数据模型(DynamicData, DynamicSubTableData) - 继承 BaseModel
- [ ] 创建序列化器层(继承 BaseModelSerializer)
- [ ] 创建过滤器层(继承 BaseModelFilter)
- [ ] 创建视图层(继承 BaseModelViewSetWithBatch)
- [ ] 实现元数据服务(MetadataService 继承 BaseCRUDService)
- [ ] 实现动态数据服务(DynamicDataService 继承 BaseCRUDService)
- [ ] 创建管理命令(load_metadata)
- [ ] 创建元数据配置文件
- [ ] 执行数据迁移

### 11.2 测试验证清单

- [ ] 业务对象管理测试
- [ ] 字段定义管理测试
- [ ] 页面布局管理测试
- [ ] 动态数据CRUD测试
- [ ] 公式字段计算测试
- [ ] 主子表关系测试
- [ ] 组织隔离测试
- [ ] 软删除测试
- [ ] 批量操作测试

---

## 12. 输出产物清单

| 文件 | 说明 |
|------|------|
| `apps/system/models.py` | 核心元数据模型(继承 BaseModel) |
| `apps/system/serializers.py` | 序列化器(继承 BaseModelSerializer) |
| `apps/system/filters.py` | 过滤器(继承 BaseModelFilter) |
| `apps/system/views.py` | 视图集(继承 BaseModelViewSetWithBatch) |
| `apps/system/services/metadata_service.py` | 元数据服务(继承 BaseCRUDService) |
| `apps/system/services/dynamic_data_service.py` | 动态数据服务(继承 BaseCRUDService) |
| `apps/system/management/commands/load_metadata.py` | 元数据加载命令 |
| `backend/fixtures/business_objects_metadata.json` | 元数据配置文件 |
| `apps/system/migrations/0001_initial.py` | 迁移文件 |

---

## 13. 核心优势总结

### 13.1 开箱即用的功能

通过使用公共基类,元数据引擎模块自动获得:

1. **序列化器自动功能**
   - 自动序列化 BaseModel 的所有公共字段
   - 自动处理组织关联嵌套序列化
   - 自动处理用户信息嵌套序列化
   - 支持 custom_fields 动态字段展开

2. **ViewSet 自动功能**
   - **组织隔离**: 自动应用当前组织过滤
   - **软删除**: 自动过滤已删除记录,删除时使用软删除
   - **审计字段**: 自动设置 created_by、updated_by
   - **批量操作**: 开箱即用的批量删除/恢复/更新接口
   - **已删除记录查询**: `/deleted/` 和 `/{id}/restore/` 接口

3. **Service 层自动功能**
   - **CRUD 基础方法**: create、update、delete、restore、get
   - **复杂查询**: query 方法支持过滤、搜索、排序
   - **分页查询**: paginate 方法自动处理分页
   - **批量操作**: batch_delete 方法
   - **组织隔离**: 所有操作自动应用组织过滤

4. **过滤器自动功能**
   - 时间范围过滤(created_at、updated_at)
   - 创建人过滤(created_by)
   - 软删除状态过滤(is_deleted)
   - 支持所有标准查询操作符

### 13.2 业务价值

1. **零代码扩展**: 新增业务单据类型无需修改代码
2. **可视化配置**: 拖拽式表单/列表设计器,所见即所得
3. **灵活存储**: PostgreSQL JSONB动态字段存储,支持复杂嵌套结构
4. **无缝集成**: 与工作流引擎深度集成,实现字段级权限控制
5. **主子表支持**: 原生支持主子表关系,自动级联处理
6. **组织隔离**: 多组织环境下元数据和业务数据的完全隔离
7. **完整审计**: 所有数据变更的完整审计日志

---

## 14. 后续集成点

1. **前端动态表单**: 使用元数据配置渲染DynamicForm组件
2. **工作流引擎**: 字段权限与工作流节点绑定
3. **报表引擎**: 基于元数据配置生成统计报表
4. **数据导入导出**: 基于元数据配置生成导入导出模板
5. **移动端适配**: 移动端表单根据元数据自动调整布局

---

---

## 15. API接口规范

### 15.1 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 15.1.1 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 15.1.2 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 15.1.3 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 15.2 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

**文档版本**: v1.0
**最后更新**: 2026-01-15
**状态**: 已完成重构
