# 动态数据CRUD服务

## 任务概述

实现基于元数据的动态数据CRUD服务，支持DynamicData的完整生命周期管理，包括字段验证、关联处理、公式计算等功能。

---

## 1. 设计目标

### 1.1 核心功能

- 基于`BusinessObject`和`FieldDefinition`的CRUD操作
- 动态字段的自动验证
- 关联字段的自动处理
- 公式字段的自动计算
- 布局字段过滤（基于PageLayout）
- 多组织数据隔离
- 软删除支持

### 1.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    动态数据CRUD服务架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              MetadataDrivenService                        │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │ │
│  │  │   create() │  │   update()   │  │    delete()     │  │ │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │ │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │ │
│  │  │    get()    │  │    query()   │  │   paginate()    │  │ │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              字段处理层                                   │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐    │ │
│  │  │ DynamicFieldValidator │  │ DynamicFieldProcessor  │    │ │
│  │  └──────────────────┘  └────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           ↓                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              数据访问层                                   │ │
│  │  ┌──────────────────┐  ┌────────────────────────────┐    │ │
│  │  │   DynamicData    │  │   custom_fields (JSONB)    │    │ │
│  │  └──────────────────┘  └────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 文件结构

```
backend/apps/common/services/
├── __init__.py
├── base_crud.py                # 已有：BaseCRUDService
└── metadata_driven.py          # 新增：MetadataDrivenService
```

---

## 3. MetadataDrivenService

### 3.1 类结构

#### DynamicFieldProcessor 类

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `process_reference_field` | `field_def, value, user` | `Any` | 处理关联字段 (提取ID) |
| `process_user_field` | `field_def, value, user` | `Optional[str]` | 处理用户选择字段 (`'current'` → 当前用户ID) |
| `process_department_field` | `field_def, value, user` | `Optional[str]` | 处理部门选择字段 (`'current'` → 当前用户部门) |
| `calculate_formula_field` | `field_def, form_data, instance` | `Any` | 计算公式字段 (使用 simpleeval) |
| `_build_formula_context` | `field_def, form_data, instance` | `Dict[str, Any]` | 构建公式计算上下文 (内置函数和常量) |
| `process_multi_choice_field` | `field_def, value` | `List[str]` | 处理多选字段 (JSON解析或逗号分割) |
| `format_field_value` | `field_def, value, for_display` | `Any` | 格式化字段值 (选项翻译、日期格式化等) |

#### 公式计算内置常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `NOW` | `timezone.now()` | 当前日期时间 |
| `TODAY` | `timezone.now().date()` | 当前日期 |
| `TRUE` | `True` | 布尔值真 |
| `FALSE` | `False` | 布尔值假 |
| `NULL` | `None` | 空值 |

#### 公式计算内置函数

| 函数 | 说明 |
|------|------|
| `abs(x)` | 绝对值 |
| `round(x)` | 四舍五入 |
| `min(x)` | 最小值 |
| `max(x)` | 最大值 |
| `sum(x)` | 求和 |
| `len(x)` | 长度 |
| `avg(x)` | 平均值 |
| `count(x)` | 非空值计数 |
| `days_between(d1, d2)` | 日期差 (天数) |
| `years_between(d1, d2)` | 日期差 (年数) |

#### MetadataDrivenService 类

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__init__` | `business_object_code: str` | - | 初始化服务，加载元数据 |
| `_load_metadata` | - | - | 加载 BusinessObject 和 FieldDefinition |
| `create` | `data, user, **kwargs` | `DynamicData` | 创建动态数据 (验证→处理字段→计算公式→保存) |
| `update` | `instance_id, data, user` | `DynamicData` | 更新动态数据 |
| `delete` | `instance_id, user` | `bool` | 软删除动态数据 |
| `get` | `instance_id, allow_deleted` | `DynamicData` | 获取单条数据 (支持已删除) |
| `query` | `filters, search, search_fields, order_by, include_deleted` | `QuerySet` | 查询动态数据 (支持过滤、搜索、排序) |
| `paginate` | `queryset, page, page_size, filters, search` | `Dict` | 分页查询 |
| `batch_delete` | `ids, user` | `Dict[str, Any]` | 批量软删除 |
| `_calculate_formula_fields` | `custom_fields, instance` | `Dict[str, Any]` | 计算所有公式字段 |
| `_serialize_instance` | `instance` | `Dict[str, Any]` | 序列化实例 (展开 custom_fields) |
| `_trigger_workflow` | `instance, action, user` | - | 触发工作流 (TODO) |
| `for_business_object` | `business_object_code: str` (class method) | `MetadataDrivenService` | 工厂方法 |

#### 字段类型处理映射

| 字段类型 | 处理方法 |
|---------|----------|
| `reference` | `process_reference_field` |
| `user` | `process_user_field` |
| `department` | `process_department_field` |
| `multi_choice` | `process_multi_choice_field` |
| `formula` | `calculate_formula_field` |

#### query 方法过滤器类型映射

| 字段类型 | 查询方式 |
|---------|----------|
| `text`, `textarea`, `email` | `icontains` (模糊匹配) |
| `choice`, `reference`, `user`, `department` | 精确匹配 |
| `number`, `integer`, `float`, `date`, `datetime` | 支持范围查询 `{from, to}` |

#### paginate 返回格式

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | `int` | 总记录数 |
| `total_pages` | `int` | 总页数 |
| `current_page` | `int` | 当前页码 |
| `page_size` | `int` | 每页数量 |
| `has_next` | `bool` | 是否有下一页 |
| `has_previous` | `bool` | 是否有上一页 |
| `results` | `list` | 结果列表 |

#### batch_delete 返回格式

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | `int` | 总数 |
| `succeeded` | `int` | 成功数 |
| `failed` | `int` | 失败数 |
| `results` | `list` | 详细结果 `[{id, success, error}]` |

### 3.2 使用示例

```python
# 创建服务实例
from apps.common.services.metadata_driven import MetadataDrivenService

asset_service = MetadataDrivenService('Asset')

# 创建数据
asset_data = {
    'asset_code': 'ASSET001',
    'asset_name': '办公电脑',
    'category': 'electronics',
    'purchase_date': '2026-01-01',
    'purchase_price': 5000.00,
}
new_asset = asset_service.create(asset_data, user=request.user)

# 查询数据
queryset = asset_service.query(
    filters={'category': 'electronics'},
    search='电脑'
)

# 更新数据
updated_asset = asset_service.update(
    str(new_asset.id),
    {'asset_name': '办公电脑（更新）', 'status': 'in_use'},
    user=request.user
)

# 分页查询
page_result = asset_service.paginate(
    page=1,
    page_size=20,
    filters={'status': 'in_use'}
)

# 批量删除
result = asset_service.batch_delete(
    ids=['id1', 'id2', 'id3'],
    user=request.user
)
```

---

## 4. 与ViewSet集成

### 4.1 在ViewSet中使用服务

```python
# backend/apps/system/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.services.metadata_driven import MetadataDrivenService
from apps.common.serializers.metadata_driven import MetadataDrivenSerializer


class DynamicDataViewSet(viewsets.ModelViewSet):
    """动态数据 ViewSet"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service = None

    def dispatch(self, request, *args, **kwargs):
        """在请求分发时初始化服务"""
        business_object_code = kwargs.get('object_code')
        if business_object_code:
            self.service = MetadataDrivenService(business_object_code)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """获取查询集"""
        if self.service:
            filters = dict(self.request.query_params)
            search = filters.pop('search', None)
            return self.service.query(filters=filters, search=search)
        return DynamicData.objects.none()

    def get_serializer_class(self):
        """获取序列化器类"""
        if self.service:
            return MetadataDrivenSerializer.for_business_object(
                self.service.business_object_code
            )
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        """创建数据"""
        if not self.service:
            return Response({'detail': 'Service not initialized'}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        instance = self.service.create(
            serializer.validated_data,
            user=request.user
        )

        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        """更新数据"""
        if not self.service:
            return Response({'detail': 'Service not initialized'}, status=400)

        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        instance = self.service.update(
            str(instance.id),
            request.data,
            user=request.user
        )

        output_serializer = self.get_serializer(instance)
        return Response(output_serializer.data)

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """批量删除"""
        if not self.service:
            return Response({'detail': 'Service not initialized'}, status=400)

        ids = request.data.get('ids', [])
        result = self.service.batch_delete(ids, user=request.user)

        return Response(result)
```

---

## 5. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/common/services/metadata_driven.py` | MetadataDrivenService |
| `backend/apps/common/services/dynamic_field_processor.py` | DynamicFieldProcessor |

---

## 6. API接口示例

### 6.1 创建动态数据

```http
POST /api/dynamic/asset/
Content-Type: application/json

{
    "asset_code": "ASSET001",
    "asset_name": "办公电脑",
    "category": "electronics",
    "purchase_date": "2026-01-01",
    "purchase_price": 5000.00
}
```

### 6.2 查询动态数据

```http
GET /api/dynamic/asset/?page=1&page_size=20&category=electronics&search=电脑
```

### 6.3 更新动态数据

```http
PUT /api/dynamic/asset/{id}/
Content-Type: application/json

{
    "asset_name": "办公电脑（更新）",
    "status": "in_use"
}
```

### 6.4 批量删除

```http
POST /api/dynamic/asset/batch-delete/
Content-Type: application/json

{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```
