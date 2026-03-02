# 元数据驱动扩展架构

## 任务概述

为低代码平台添加元数据驱动的序列化器、ViewSet和过滤器，支持基于BusinessObject/FieldDefinition/PageLayout的零代码扩展能力。

---

## 核心数据模型定义

### BusinessObject 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| name | string | max=200, unique | 业务对象名称 |
| code | string | max=50, unique | 对象编码 |
| table_name | string | max=100 | 对应数据库表 |
| is_active | boolean | default=True | 是否启用 |
| description | text | nullable | 对象描述 |
| enable_workflow | boolean | default=False | 是否启用工作流 |
| enable_version | boolean | default=False | 是否启用版本控制 |
| default_ordering | string | max=100 | 默认排序 |
| organization | ForeignKey | Organization | 所属组织 |
| is_deleted | boolean | default=False | 软删除标记 |
| created_at | datetime | auto_now_add | 创建时间 |
| updated_at | datetime | auto_now=True | 更新时间 |
| created_by | ForeignKey | User | 创建人 |

### FieldDefinition 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_object | ForeignKey | BusinessObject | 所属业务对象 |
| name | string | max=100 | 字段名称 |
| code | string | max=50 | 字段编码 |
| field_type | string | max=20 | 字段类型 |
| is_required | boolean | default=False | 是否必填 |
| is_readonly | boolean | default=False | 是否只读 |
| is_unique | boolean | default=False | 是否唯一 |
| default_value | string | nullable | 默认值 |
| max_length | integer | nullable | 最大长度 |
| min_value | decimal | nullable | 最小值 |
| max_value | decimal | nullable | 最大值 |
| decimal_places | integer | nullable | 小数位数 |
| options | JSONField | nullable | 选项配置 |
| validation_regex | string | max=500, nullable | 验证正则 |
| validation_expression | string | max=1000, nullable | 验证表达式 |
| formula_expression | string | max=500, nullable | 公式表达式 |
| reference_to | string | max=100, nullable | 关联对象 |
| is_searchable | boolean | default=False | 可搜索 |
| sortable | boolean | default=False | 可排序 |
| show_in_filter | boolean | default=False | 显示在过滤器 |
| placeholder | string | max=200, nullable | 占位符 |
| description | text | nullable | 字段描述 |
| sort_order | integer | default=0 | 排序 |
| is_active | boolean | default=True | 是否启用 |

### DynamicData 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_object | ForeignKey | BusinessObject | 业务对象 |
| custom_fields | JSONField | - | 动态字段数据 |
| organization | ForeignKey | Organization | 所属组织 |
| is_deleted | boolean | default=False | 软删除标记 |
| deleted_at | datetime | nullable | 删除时间 |
| created_at | datetime | auto_now_add | 创建时间 |
| updated_at | datetime | auto_now=True | 更新时间 |
| created_by | ForeignKey | User | 创建人 |

### PageLayout 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 |
| business_object | ForeignKey | BusinessObject | 业务对象 |
| code | string | max=50 | 布局编码 |
| name | string | max=100 | 布局名称 |
| layout_type | string | max=20 | 布局类型(form/list) |
| layout_config | JSONField | - | 布局配置 |
| is_default | boolean | default=False | 是否默认 |
| organization | ForeignKey | Organization | 所属组织 |
| is_deleted | boolean | default=False | 软删除标记 |
| created_at | datetime | auto_now_add | 创建时间 |
| updated_at | datetime | auto_now=True | 更新时间 |
| created_by | ForeignKey | User | 创建人 |

---

## 1. 设计背景

### 1.1 当前架构的局限性

当前`BaseModelSerializer`、`BaseModelViewSet`等基类采用**代码继承模式**：

```python
# 当前方式：需要为每个业务对象编写代码
class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', 'category']
```

**局限性**：
- ❌ 新增业务对象必须编写代码
- ❌ 字段变更需要修改代码
- ❌ 不符合"零代码扩展"原则

### 1.2 元数据驱动模式

**目标**：通过配置BusinessObject/FieldDefinition，无需编写代码即可获得完整的CRUD能力。

```python
# 低代码方式：仅需配置元数据
BusinessObject.objects.create(code='Asset', name='资产卡片')
FieldDefinition.objects.create(
    business_object=obj,
    code='asset_code',
    name='资产编码',
    field_type='text',
    is_required=True
)
# 系统自动生成序列化器、ViewSet、过滤器...
```

### 1.3 架构对比

```
┌─────────────────────────────────────────────────────────────────┐
│                    当前架构 vs 元数据驱动架构                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  当前架构（代码继承）                                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  业务模块                                               │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐   │    │
│  │  │AssetSerializer│→│AssetViewSet │→│ AssetFilter │   │    │
│  │  └─────────────┘  └──────────────┘  └─────────────┘   │    │
│  │         ↓                  ↓                 ↓          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │       BaseModelSerializer/ViewSet/Filter        │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  元数据驱动架构（配置生成）                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  配置层（Configuration）                                 │    │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐   │    │
│  │  │BusinessObject│→│FieldDefinition│→│  PageLayout  │   │    │
│  │  └─────────────┘  └──────────────┘  └─────────────┘   │    │
│  │         ↓                  ↓                 ↓          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │       MetadataCodeGenerator（代码生成）           │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │         ↓                  ↓                 ↓          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  MetadataDrivenSerializer/ViewSet/Filter         │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 文件结构

```
backend/apps/common/
├── serializers/
│   ├── __init__.py
│   ├── base.py                 # 已有 BaseModelSerializer
│   └── metadata_driven.py      # 新增：MetadataDrivenSerializer
├── viewsets/
│   ├── __init__.py
│   ├── base.py                 # 已有 BaseModelViewSet
│   └── metadata_driven.py      # 新增：MetadataDrivenViewSet
├── filters/
│   ├── __init__.py
│   ├── base.py                 # 已有 BaseModelFilter
│   └── metadata_driven.py      # 新增：MetadataDrivenFilter
├── services/
│   ├── __init__.py
│   ├── base_crud.py            # 已有 BaseCRUDService
│   └── metadata_driven.py      # 新增：MetadataDrivenService
├── generators/
│   ├── __init__.py             # 新增目录
│   └── code_generator.py       # 新增：MetadataCodeGenerator
└── validators/
    ├── __init__.py             # 新增目录
    └── dynamic_field.py        # 新增：DynamicFieldValidator
```

---

## 3. MetadataDrivenSerializer

### 3.1 设计目标

- 基于`BusinessObject`自动生成序列化器
- 基于`FieldDefinition`动态构建字段
- 自动处理`custom_fields`的展开与序列化
- 支持关联字段的自动处理

### 3.2 实现代码

```python
# backend/apps/common/serializers/metadata_driven.py

from rest_framework import serializers
from typing import Dict, List, Any, Optional
from django.core.exceptions import ObjectDoesNotExist
from apps.system.models import BusinessObject, FieldDefinition


class FieldDefinitionMapper:
    """
    字段类型映射器
    将 FieldDefinition 的 field_type 映射到 DRF 字段类型
    """

    FIELD_TYPE_MAPPING = {
        'text': serializers.CharField,
        'textarea': serializers.CharField,
        'number': serializers.DecimalField,
        'integer': serializers.IntegerField,
        'float': serializers.FloatField,
        'boolean': serializers.BooleanField,
        'date': serializers.DateField,
        'datetime': serializers.DateTimeField,
        'time': serializers.TimeField,
        'email': serializers.EmailField,
        'url': serializers.URLField,
        'choice': serializers.ChoiceField,
        'multi_choice': serializers.MultipleChoiceField,
        'file': serializers.FileField,
        'image': serializers.ImageField,
        'reference': serializers.UUIDField,  # 关联字段存储ID
        'user': serializers.UUIDField,
        'department': serializers.UUIDField,
        'formula': serializers.ReadOnlyField,
    }

    @classmethod
    def get_field_class(cls, field_type: str) -> type:
        """获取对应的 DRF 字段类"""
        return cls.FIELD_TYPE_MAPPING.get(field_type, serializers.CharField)

    @classmethod
    def get_field_kwargs(cls, field_def: FieldDefinition) -> Dict:
        """
        根据字段定义获取字段参数

        Args:
            field_def: FieldDefinition 实例

        Returns:
            字段参数字典
        """
        kwargs = {
            'required': field_def.is_required,
            'read_only': field_def.is_readonly,
            'label': field_def.name,
            'help_text': field_def.description or '',
        }

        # 处理默认值
        if field_def.default_value is not None:
            kwargs['default'] = field_def.default_value

        # 处理字符串长度限制
        if field_def.max_length and field_def.field_type in ['text', 'textarea']:
            kwargs['max_length'] = field_def.max_length

        # 处理数值范围
        if field_def.field_type in ['number', 'integer', 'float']:
            if field_def.min_value is not None:
                kwargs['min_value'] = field_def.min_value
            if field_def.max_value is not None:
                kwargs['max_value'] = field_def.max_value
            if field_def.field_type == 'number':
                kwargs['decimal_places'] = field_def.decimal_places or 2
                kwargs['max_digits'] = field_def.max_digits or 10

        # 处理选项字段
        if field_def.field_type in ['choice', 'multi_choice']:
            choices = field_def.options or {}
            kwargs['choices'] = [(k, k) for k in choices.keys()]

        return kwargs


class MetadataDrivenSerializer(serializers.Serializer):
    """
    元数据驱动的序列化器

    基于 BusinessObject 和 FieldDefinition 动态生成序列化器
    支持两种数据源：
    1. DynamicData（完全动态数据，存储在 custom_fields）
    2. 传统 Model + custom_fields 混合模式
    """

    # 类属性，由子类或运行时设置
    business_object_code: Optional[str] = None
    business_object: Optional[BusinessObject] = None
    field_definitions: Optional[QuerySet] = None
    layout_type: str = 'form'  # form | list

    def __init__(self, *args, **kwargs):
        """
        初始化序列化器

        支持两种初始化方式：
        1. 子类设置 business_object_code
        2. 实例化时传入 business_object_code
        """
        # 提取 business_object_code 参数
        self._init_business_object_code = kwargs.pop('business_object_code', None)

        super().__init__(*args, **kwargs)

        # 初始化元数据
        self._load_metadata()

        # 动态构建字段
        if self.business_object and self.field_definitions:
            self._build_dynamic_fields()

    def _load_metadata(self):
        """加载元数据"""
        code = self._init_business_object_code or self.business_object_code

        if not code:
            return

        try:
            self.business_object = BusinessObject.objects.get(code=code)
            self.field_definitions = self.business_object.field_definitions.filter(
                is_active=True
            ).order_by('sort_order')
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                f"BusinessObject with code '{code}' does not exist"
            )

    def _build_dynamic_fields(self):
        """
        根据字段定义动态构建序列化器字段
        """
        for field_def in self.field_definitions:
            # 跳过布局中的隐藏字段
            if self.layout_type == 'form':
                # 对于表单布局，检查字段是否在表单布局中可见
                if not self._is_field_visible_in_layout(field_def, 'form'):
                    continue
            elif self.layout_type == 'list':
                # 对于列表布局，只显示列表布局中的字段
                if not self._is_field_visible_in_layout(field_def, 'list'):
                    continue

            # 获取字段类和参数
            field_class = FieldDefinitionMapper.get_field_class(field_def.field_type)
            field_kwargs = FieldDefinitionMapper.get_field_kwargs(field_def)

            # 处理关联字段
            if field_def.field_type == 'reference':
                field_kwargs['source'] = f'custom_fields.{field_def.code}'
                # 添加嵌套序列化（可选）
                if field_def.reference_to:
                    field_kwargs = self._get_reference_field_kwargs(field_def)

            # 对于动态数据，使用 custom_fields 作为 source
            elif hasattr(self, 'instance') and hasattr(self.instance, 'custom_fields'):
                field_kwargs['source'] = f'custom_fields.{field_def.code}'

            # 创建字段
            self.fields[field_def.code] = field_class(**field_kwargs)

    def _is_field_visible_in_layout(self, field_def: FieldDefinition, layout_type: str) -> bool:
        """
        检查字段在布局中是否可见

        Args:
            field_def: 字段定义
            layout_type: 布局类型（form/list）

        Returns:
            是否可见
        """
        if not self.business_object:
            return True

        # 获取对应布局
        layout = getattr(
            self.business_object,
            f'{layout_type}_layout',
            None
        )

        if not layout:
            return True

        # 解析布局配置
        layout_config = layout.layout_config or {}

        # 检查字段是否在布局中
        if layout_type == 'form':
            # 表单布局：检查字段是否在 sections 中
            sections = layout_config.get('sections', [])
            for section in sections:
                if field_def.code in section.get('fields', []):
                    return True
            return field_def.is_default_visible
        else:
            # 列表布局：检查字段是否在 columns 中
            columns = layout_config.get('columns', [])
            field_codes = [col.get('field') for col in columns]
            return field_def.code in field_codes

    def _get_reference_field_kwargs(self, field_def: FieldDefinition) -> Dict:
        """
        获取关联字段的参数

        Args:
            field_def: 字段定义

        Returns:
            字段参数字典
        """
        # TODO: 实现关联字段的嵌套序列化
        # 1. 根据 reference_to 获取关联的 BusinessObject
        # 2. 递归获取关联对象的序列化数据
        return {
            'read_only': True,
            'source': f'custom_fields.{field_def.code}_display',
            'label': field_def.name
        }

    def to_representation(self, instance):
        """
        增强序列化输出

        1. 将 custom_fields 中的字段展开到顶层
        2. 格式化字段值（根据 FieldDefinition）
        3. 处理关联字段的显示
        """
        data = super().to_representation(instance)

        # 展开 custom_fields
        if hasattr(instance, 'custom_fields') and isinstance(instance.custom_fields, dict):
            custom_fields = instance.custom_fields.copy()

            # 根据字段定义处理每个字段
            if self.field_definitions:
                for field_def in self.field_definitions:
                    field_code = field_def.code

                    # 如果字段在 custom_fields 中
                    if field_code in custom_fields:
                        value = custom_fields[field_code]

                        # 格式化字段值
                        formatted_value = self._format_field_value(field_def, value)

                        # 设置到顶层
                        data[field_code] = formatted_value

                        # 从 custom_fields 中移除（已展开）
                        # 注意：这里不修改原数据，只在输出时处理

        # 处理公式字段
        data = self._process_formula_fields(instance, data)

        return data

    def _format_field_value(self, field_def: FieldDefinition, value: Any) -> Any:
        """
        根据 FieldDefinition 格式化字段值

        Args:
            field_def: 字段定义
            value: 原始值

        Returns:
            格式化后的值
        """
        if value is None:
            return None

        field_type = field_def.field_type

        # 日期时间格式化
        if field_type in ['date', 'datetime']:
            if isinstance(value, str):
                return value
            return value.isoformat()

        # 选项字段格式化
        if field_type in ['choice', 'multi_choice']:
            options = field_def.options or {}
            if field_type == 'choice':
                # 返回选项的显示值
                return {
                    'value': value,
                    'label': options.get(value, value)
                }
            else:
                return {
                    'value': value,
                    'labels': [options.get(v, v) for v in value]
                }

        # 关联字段格式化
        if field_type == 'reference':
            # TODO: 返回关联对象的简要信息
            return {
                'id': value,
                'display': self._get_reference_display(value, field_def)
            }

        return value

    def _get_reference_display(self, value: Any, field_def: FieldDefinition) -> str:
        """获取关联字段的显示值"""
        # TODO: 根据 reference_to 查询关联对象并返回显示字段
        return str(value)

    def _process_formula_fields(self, instance, data: Dict) -> Dict:
        """
        处理公式字段

        公式字段是只读的，根据其他字段的值计算得出
        """
        if not self.field_definitions:
            return data

        for field_def in self.field_definitions:
            if field_def.field_type == 'formula' and field_def.formula_expression:
                try:
                    # 使用 simpleeval 评估公式
                    from simpleeval import simple_eval

                    # 构建公式上下文
                    context = self._build_formula_context(instance, data)

                    # 计算公式值
                    calculated_value = simple_eval(
                        field_def.formula_expression,
                        names=context
                    )

                    data[field_def.code] = calculated_value
                except Exception:
                    data[field_def.code] = None

        return data

    def _build_formula_context(self, instance, data: Dict) -> Dict:
        """构建公式计算的上下文"""
        context = {}

        # 添加字段值到上下文
        if self.field_definitions:
            for field_def in self.field_definitions:
                if field_def.code in data:
                    context[field_def.code] = data[field_def.code]

        # 添加内置函数
        context.update({
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'len': len,
        })

        return context

    def validate(self, attrs):
        """
        自定义验证

        基于 FieldDefinition 进行字段验证
        """
        # 调用动态字段验证器
        if self.field_definitions:
            from apps.common.validators.dynamic_field import DynamicFieldValidator

            validator = DynamicFieldValidator(self.field_definitions)
            validator.validate(attrs)

        return attrs

    @classmethod
    def for_business_object(cls, business_object_code: str, layout_type: str = 'form'):
        """
        工厂方法：为指定的 BusinessObject 创建序列化器类

        Args:
            business_object_code: 业务对象编码
            layout_type: 布局类型（form/list）

        Returns:
            序列化器类
        """
        class GeneratedSerializer(cls):
            business_object_code = business_object_code
            layout_type = layout_type

        GeneratedSerializer.__name__ = f'{business_object_code.title()}Serializer'
        return GeneratedSerializer


# 使用示例
if __name__ == '__main__':
    # 方式1：通过工厂方法创建
    AssetSerializer = MetadataDrivenSerializer.for_business_object('Asset', layout_type='form')

    # 方式2：直接使用
    serializer = MetadataDrivenSerializer(
        business_object_code='Asset',
        layout_type='form'
    )
```

### 3.3 使用示例

```python
# 方式1：为动态数据创建序列化器
from apps.common.serializers.metadata_driven import MetadataDrivenSerializer
from apps.system.models import DynamicData

# 工厂方法创建
AssetSerializer = MetadataDrivenSerializer.for_business_object('Asset', layout_type='form')

# 使用序列化器
data_instance = DynamicData.objects.get(business_object__code='Asset')
serializer = AssetSerializer(data_instance)
print(serializer.data)
# 输出：
# {
#     "id": "...",
#     "asset_code": "ASSET001",
#     "asset_name": "办公电脑",
#     "category": {...},
#     "purchase_date": "2026-01-01",
#     ...
# }

# 方式2：在 ViewSet 中使用
class DynamicDataViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        # 根据业务对象动态返回序列化器
        business_object_code = self.kwargs.get('object_code')
        return MetadataDrivenSerializer.for_business_object(business_object_code)
```

---

## 4. MetadataDrivenViewSet

### 4.1 设计目标

- 基于`BusinessObject`自动生成ViewSet
- 根据`FieldDefinition`配置搜索/过滤/排序
- 与`PageLayout`集成，自动处理列表/表单布局
- 支持动态数据和传统模型两种模式

### 4.2 实现代码

```python
# backend/apps/common/viewsets/metadata_driven.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from typing import Optional, Dict, List, Any
from django.db.models import Q, QuerySet
from django.core.exceptions import ObjectDoesNotExist
from apps.system.models import BusinessObject, FieldDefinition, DynamicData, PageLayout
from apps.common.serializers.metadata_driven import MetadataDrivenSerializer
from apps.common.filters.metadata_driven import MetadataDrivenFilter


class MetadataDrivenViewSet(viewsets.ModelViewSet):
    """
    元数据驱动的 ViewSet

    基于 BusinessObject 自动生成完整的 CRUD 功能
    支持动态数据（DynamicData）和传统模型两种模式
    """

    # 业务对象编码（由路由设置）
    business_object_code: Optional[str] = None

    # 运行时加载的元数据
    business_object: Optional[BusinessObject] = None
    field_definitions: Optional[QuerySet] = None
    list_layout: Optional[PageLayout] = None
    form_layout: Optional[PageLayout] = None

    # 当前操作模式
    mode: str = 'dynamic'  # dynamic | model

    def __init__(self, *args, **kwargs):
        """初始化 ViewSet"""
        super().__init__(*args, **kwargs)
        self._load_metadata()

    def _load_metadata(self):
        """加载业务对象元数据"""
        if not self.business_object_code:
            return

        try:
            self.business_object = BusinessObject.objects.get(
                code=self.business_object_code,
                is_active=True
            )

            # 加载字段定义
            self.field_definitions = self.business_object.field_definitions.filter(
                is_active=True
            ).order_by('sort_order')

            # 加载布局
            self.list_layout = getattr(self.business_object, 'list_layout', None)
            self.form_layout = getattr(self.business_object, 'form_layout', None)

            # 配置搜索字段
            self._configure_search_fields()

            # 配置排序字段
            self._configure_ordering_fields()

            # 配置过滤器
            self._configure_filters()

        except ObjectDoesNotExist:
            raise ValueError(f"BusinessObject '{self.business_object_code}' not found")

    def _configure_search_fields(self):
        """配置搜索字段"""
        if not self.field_definitions:
            return

        # 获取可搜索的字段
        searchable_fields = self.field_definitions.filter(
            is_searchable=True
        ).values_list('code', flat=True)

        self.search_fields = list(searchable_fields)

    def _configure_ordering_fields(self):
        """配置排序字段"""
        if not self.field_definitions:
            return

        # 获取可排序的字段
        sortable_fields = self.field_definitions.filter(
            sortable=True
        ).values_list('code', flat=True)

        self.ordering_fields = list(sortable_fields)
        self.ordering = self.business_object.default_ordering or ['-created_at']

    def _configure_filters(self):
        """配置过滤器后端"""
        from django_filters.rest_framework import DjangoFilterBackend

        if DjangoFilterBackend not in self.filter_backends:
            self.filter_backends = self.filter_backends + [DjangoFilterBackend]

    def get_queryset(self):
        """
        获取查询集

        支持两种模式：
        1. dynamic - 查询 DynamicData
        2. model - 查询指定的 Django 模型
        """
        if self.mode == 'dynamic':
            # 动态数据模式
            return DynamicData.objects.filter(
                business_object=self.business_object
            ).select_related('organization', 'created_by')
        else:
            # 传统模型模式（需要子类设置 queryset）
            return super().get_queryset()

    def get_serializer_class(self):
        """动态获取序列化器类"""
        # 根据 action 决定使用列表还是表单布局
        layout_type = 'list' if self.action == 'list' else 'form'

        return MetadataDrivenSerializer.for_business_object(
            self.business_object_code,
            layout_type=layout_type
        )

    def get_serializer(self, *args, **kwargs):
        """获取序列化器实例"""
        serializer_class = self.get_serializer_class()

        # 传入 business_object_code
        kwargs['business_object_code'] = self.business_object_code
        kwargs['layout_type'] = 'list' if self.action == 'list' else 'form'

        return serializer_class(*args, **kwargs)

    def get_serializer_context(self):
        """获取序列化器上下文"""
        context = super().get_serializer_context()
        context['business_object'] = self.business_object
        context['field_definitions'] = self.field_definitions
        return context

    def perform_create(self, serializer):
        """创建时设置业务对象"""
        if self.mode == 'dynamic':
            serializer.save(
                business_object=self.business_object,
                created_by=self.request.user
            )
        else:
            super().perform_create(serializer)

    def list(self, request, *args, **kwargs):
        """
        列表查询

        根据 PageLayout 配置返回指定字段
        """
        response = super().list(request, *args, **kwargs)

        # 如果有列表布局，处理输出字段
        if self.list_layout and self.business_object:
            response.data = self._apply_list_layout(response.data)

        return response

    def _apply_list_layout(self, response_data: Dict) -> Dict:
        """
        应用列表布局配置

        Args:
            response_data: 原始响应数据

        Returns:
            处理后的响应数据
        """
        if not self.list_layout:
            return response_data

        layout_config = self.list_layout.layout_config or {}
        columns = layout_config.get('columns', [])

        # 处理每条记录，只保留列表布局中配置的字段
        results = response_data.get('results', [])
        processed_results = []

        for record in results:
            processed_record = {}

            # 保留系统字段
            for sys_field in ['id', 'created_at', 'updated_at']:
                if sys_field in record:
                    processed_record[sys_field] = record[sys_field]

            # 保留布局配置的字段
            for col in columns:
                field_code = col.get('field')
                if field_code in record:
                    processed_record[field_code] = record[field_code]

            processed_results.append(processed_record)

        response_data['results'] = processed_results

        # 添加列表元数据
        response_data['layout_meta'] = {
            'columns': columns,
            'page_size': layout_config.get('page_size', 20),
            'show_row_number': layout_config.get('show_row_number', False),
        }

        return response_data

    @action(detail=False, methods=['get'])
    def metadata(self, request):
        """
        获取业务对象的元数据

        GET /api/dynamic/{object_code}/metadata/

        返回：
        - 业务对象信息
        - 字段定义列表
        - 列表布局配置
        - 表单布局配置
        """
        return Response({
            'success': True,
            'data': {
                'business_object': {
                    'code': self.business_object.code,
                    'name': self.business_object.name,
                    'description': self.business_object.description,
                    'enable_workflow': self.business_object.enable_workflow,
                    'enable_version': self.business_object.enable_version,
                },
                'field_definitions': self._serialize_field_definitions(),
                'list_layout': self._serialize_layout(self.list_layout),
                'form_layout': self._serialize_layout(self.form_layout),
            }
        })

    def _serialize_field_definitions(self) -> List[Dict]:
        """序列化字段定义"""
        if not self.field_definitions:
            return []

        return [
            {
                'code': fd.code,
                'name': fd.name,
                'field_type': fd.field_type,
                'is_required': fd.is_required,
                'is_readonly': fd.is_readonly,
                'is_searchable': fd.is_searchable,
                'sortable': fd.sortable,
                'show_in_filter': fd.show_in_filter,
                'is_unique': fd.is_unique,
                'default_value': fd.default_value,
                'options': fd.options,
                'reference_to': fd.reference_to,
                'formula_expression': fd.formula_expression,
                'placeholder': fd.placeholder,
                'description': fd.description,
            }
            for fd in self.field_definitions
        ]

    def _serialize_layout(self, layout: Optional[PageLayout]) -> Optional[Dict]:
        """序列化布局配置"""
        if not layout:
            return None

        return {
            'code': layout.code,
            'name': layout.name,
            'layout_type': layout.layout_type,
            'layout_config': layout.layout_config,
        }

    @action(detail=False, methods=['get'])
    def schema(self, request):
        """
        获取数据模式（Schema）

        用于前端动态生成表单验证规则
        """
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }

        if self.field_definitions:
            for fd in self.field_definitions:
                field_schema = self._get_field_schema(fd)
                schema['properties'][fd.code] = field_schema

                if fd.is_required:
                    schema['required'].append(fd.code)

        return Response({
            'success': True,
            'data': schema
        })

    def _get_field_schema(self, field_def: FieldDefinition) -> Dict:
        """获取字段的 JSON Schema 定义"""
        type_mapping = {
            'text': 'string',
            'textarea': 'string',
            'number': 'number',
            'integer': 'integer',
            'float': 'number',
            'boolean': 'boolean',
            'date': 'string',
            'datetime': 'string',
            'time': 'string',
            'email': 'string',
            'url': 'string',
            'choice': 'string',
            'multi_choice': 'array',
            'file': 'string',
            'image': 'string',
            'reference': 'string',
        }

        schema = {
            'type': type_mapping.get(field_def.field_type, 'string'),
            'title': field_def.name,
            'description': field_def.description or '',
        }

        # 添加约束
        if field_def.is_required:
            schema['minLength'] = 1 if schema['type'] == 'string' else None

        if field_def.max_length:
            schema['maxLength'] = field_def.max_length

        if field_def.min_value is not None:
            schema['minimum'] = field_def.min_value

        if field_def.max_value is not None:
            schema['maximum'] = field_def.max_value

        if field_def.options:
            schema['enum'] = list(field_def.options.keys())

        return schema


class MetadataDrivenViewSetMixin:
    """
    元数据驱动 ViewSet 混合类

    用于将元数据驱动功能添加到现有的 ViewSet 中
    """

    business_object_code: Optional[str] = None

    def get_metadata_driven_serializer(self, layout_type: str = 'form'):
        """获取元数据驱动的序列化器"""
        return MetadataDrivenSerializer.for_business_object(
            self.business_object_code,
            layout_type=layout_type
        )
```

### 4.3 使用示例

```python
# 方式1：在路由中动态注册
from apps.common.viewsets.metadata_driven import MetadataDrivenViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# 动态注册所有激活的业务对象
business_objects = BusinessObject.objects.filter(is_active=True)

for obj in business_objects:
    # 动态创建 ViewSet 类
    viewset_class = type(
        f'{obj.code}ViewSet',
        (MetadataDrivenViewSet,),
        {'business_object_code': obj.code}
    )

    # 注册路由
    router.register(
        f'dynamic/{obj.code.lower()}',
        viewset_class,
        basename=f'dynamic-{obj.code.lower()}'
    )

# 方式2：在 urls.py 中使用
from django.urls import path, include
from apps.common.viewsets.metadata_driven import MetadataDrivenViewSet

# 为特定业务对象创建 ViewSet
class AssetDynamicViewSet(MetadataDrivenViewSet):
    business_object_code = 'Asset'
    mode = 'dynamic'  # 使用 DynamicData 存储

urlpatterns = [
    path('api/dynamic/asset/', AssetDynamicViewSet.as_view({'get': 'list', 'post': 'create'})),
]
```

---

## 5. MetadataDrivenFilter

### 5.1 实现代码

```python
# backend/apps/common/filters/metadata_driven.py

from django_filters import rest_framework as filters
from typing import Dict, List, Any, Optional
from django.db.models import Q
from apps.system.models import BusinessObject, FieldDefinition


class MetadataDrivenFilter(filters.FilterSet):
    """
    元数据驱动的过滤器

    基于 FieldDefinition 自动生成过滤器
    支持 custom_fields 中的字段过滤
    """

    def __init__(self, *args, **kwargs):
        """初始化过滤器"""
        self.business_object_code = kwargs.pop('business_object_code', None)
        self.business_object = kwargs.pop('business_object', None)
        self.field_definitions = kwargs.pop('field_definitions', None)

        super().__init__(*args, **kwargs)

        # 动态构建过滤器
        if self.field_definitions:
            self._build_dynamic_filters()

    def _build_dynamic_filters(self):
        """根据字段定义构建过滤器"""
        filterable_fields = self.field_definitions.filter(
            show_in_filter=True
        )

        for field_def in filterable_fields:
            filter_name = field_def.code
            field_type = field_def.field_type

            # 根据字段类型选择过滤器
            if field_type in ['text', 'textarea', 'email']:
                # 文本类型：支持精确匹配和模糊搜索
                self.filters[filter_name] = filters.CharFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='icontains',
                    label=field_def.name
                )
                self.filters[f'{filter_name}__exact'] = filters.CharFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='exact',
                    label=f'{field_def.name}（精确）'
                )

            elif field_type in ['number', 'integer', 'float']:
                # 数值类型：支持范围查询
                self.filters[filter_name] = filters.NumberFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    label=field_def.name
                )
                self.filters[f'{filter_name}__gte'] = filters.NumberFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='gte',
                    label=f'{field_def.name}（≥）'
                )
                self.filters[f'{filter_name}__lte'] = filters.NumberFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='lte',
                    label=f'{field_def.name}（≤）'
                )

            elif field_type in ['date', 'datetime']:
                # 日期类型：支持范围查询
                self.filters[filter_name] = filters.DateTimeFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    label=field_def.name
                )
                self.filters[f'{filter_name}__from'] = filters.DateTimeFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='gte',
                    label=f'{field_def.name}（起始）'
                )
                self.filters[f'{filter_name}__to'] = filters.DateTimeFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    lookup_expr='lte',
                    label=f'{field_def.name}（结束）'
                )

            elif field_type in ['choice', 'multi_choice']:
                # 选项类型：支持多选
                self.filters[filter_name] = filters.MultipleChoiceFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    choices=[(k, k) for k in (field_def.options or {}).keys()],
                    label=field_def.name
                )

            elif field_type == 'boolean':
                # 布尔类型
                self.filters[filter_name] = filters.BooleanFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    label=field_def.name
                )

            elif field_type == 'reference':
                # 关联类型：按ID过滤
                self.filters[filter_name] = filters.UUIDFilter(
                    field_name=f'custom_fields__{field_def.code}',
                    label=field_def.name
                )

    @classmethod
    def for_business_object(cls, business_object_code: str):
        """
        工厂方法：为指定的 BusinessObject 创建过滤器类

        Args:
            business_object_code: 业务对象编码

        Returns:
            过滤器类
        """
        try:
            business_object = BusinessObject.objects.get(code=business_object_code)
            field_definitions = business_object.field_definitions.filter(is_active=True)
        except BusinessObject.DoesNotExist:
            raise ValueError(f"BusinessObject '{business_object_code}' not found")

        class GeneratedFilter(cls):
            class Meta:
                model = DynamicData
                fields = []

            def __init__(self, *args, **kwargs):
                kwargs['business_object_code'] = business_object_code
                kwargs['business_object'] = business_object
                kwargs['field_definitions'] = field_definitions
                super().__init__(*args, **kwargs)

        GeneratedFilter.__name__ = f'{business_object_code.title()}Filter'
        return GeneratedFilter
```

---

## 6. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/common/serializers/metadata_driven.py` | MetadataDrivenSerializer |
| `backend/apps/common/viewsets/metadata_driven.py` | MetadataDrivenViewSet |
| `backend/apps/common/filters/metadata_driven.py` | MetadataDrivenFilter |
| `backend/apps/common/generators/code_generator.py` | MetadataCodeGenerator |
| `backend/apps/common/validators/dynamic_field.py` | DynamicFieldValidator |

---

## 7. 迁移指南

### 7.1 混合模式支持

系统同时支持两种模式：

```python
# 模式1：传统模型 + 元数据扩展
class Asset(BaseModel):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)

class AssetSerializer(BaseModelSerializer):
    # 继承公共字段
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name']

# 模式2：完全元数据驱动
# 只需配置 BusinessObject 和 FieldDefinition
# 使用 MetadataDrivenSerializer 自动生成
```

### 7.2 逐步迁移

1. **Phase 1**：新模块使用元数据驱动
2. **Phase 2**：简单模块逐步迁移
3. **Phase 3**：复杂模块评估迁移
