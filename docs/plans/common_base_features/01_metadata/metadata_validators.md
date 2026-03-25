# 动态字段验证器

## 任务概述

实现基于`FieldDefinition`的动态字段验证器，为低代码平台提供完整的字段验证能力。

---

## 1. 设计目标

### 1.1 核心功能

- 基于`FieldDefinition`的自动验证
- 支持所有字段类型的验证规则
- 支持自定义验证表达式
- 支持跨字段验证
- 支持唯一性验证
- 支持关联字段验证
- 提供详细的验证错误信息

### 1.2 验证规则类型

| 规则类型 | 说明 | 字段类型 |
|---------|------|---------|
| 必填验证 | 字段不能为空 | 所有类型 |
| 类型验证 | 验证数据类型 | 所有类型 |
| 长度验证 | 字符串长度限制 | text, textarea |
| 范围验证 | 数值范围限制 | number, integer, float, date |
| 正则验证 | 正则表达式匹配 | text, email, url |
| 选项验证 | 值必须在选项中 | choice, multi_choice |
| 唯一性验证 | 字段值必须唯一 | 所有类型 |
| 关联验证 | 关联对象必须存在 | reference, user, department |
| 表达式验证 | 自定义验证表达式 | 所有类型 |
| 跨字段验证 | 多字段联合验证 | 所有类型 |

---

## 2. 文件结构

```
backend/apps/common/validators/
├── __init__.py
├── base.py                     # 验证器基类
├── dynamic_field.py            # 动态字段验证器
├── type_validators.py          # 类型验证器
└── expression_validators.py    # 表达式验证器
```

---

## 3. DynamicFieldValidator

### 3.1 实现代码

```python
# backend/apps/common/validators/dynamic_field.py

from typing import Dict, List, Any, Optional, Callable
from django.core.exceptions import ValidationError
from django.db.models import Q
from apps.system.models import FieldDefinition, DynamicData
from apps.common.models import get_current_organization
import re
import json


class FieldValidationError(ValidationError):
    """字段验证错误"""

    def __init__(self, field_code: str, message: str, error_code: str = 'invalid'):
        self.field_code = field_code
        self.error_code = error_code
        super().__init__(
            {field_code: [message]},
            code=error_code
        )


class DynamicFieldValidator:
    """
    动态字段验证器

    基于 FieldDefinition 进行字段验证
    """

    def __init__(self, field_definitions: List[FieldDefinition]):
        """
        初始化验证器

        Args:
            field_definitions: 字段定义列表
        """
        self.field_definitions = field_definitions
        self.field_def_map = {fd.code: fd for fd in field_definitions}
        self.custom_validators = {}
        self.cross_field_validators = []

    def validate(
        self,
        data: Dict[str, Any],
        instance: Optional[DynamicData] = None,
        action: str = 'create'
    ) -> Dict[str, Any]:
        """
        验证数据

        Args:
            data: 待验证的数据
            instance: 实例（用于更新场景）
            action: 操作类型（create/update）

        Returns:
            验证后的数据

        Raises:
            ValidationError: 验证失败
        """
        errors = {}
        validated_data = {}

        # 逐字段验证
        for field_def in self.field_definitions:
            field_code = field_def.code

            # 跳过只读字段
            if field_def.is_readonly and action == 'create':
                continue

            # 获取字段值
            value = data.get(field_code)

            try:
                # 验证字段
                validated_value = self.validate_field(
                    field_def,
                    value,
                    data,
                    instance,
                    action
                )
                validated_data[field_code] = validated_value

            except FieldValidationError as e:
                errors[field_code] = e.message

        # 执行跨字段验证
        cross_field_errors = self._validate_cross_fields(
            validated_data,
            instance,
            action
        )
        errors.update(cross_field_errors)

        # 如果有错误，抛出异常
        if errors:
            raise ValidationError(errors)

        return validated_data

    def validate_field(
        self,
        field_def: FieldDefinition,
        value: Any,
        data: Dict[str, Any],
        instance: Optional[DynamicData] = None,
        action: str = 'create'
    ) -> Any:
        """
        验证单个字段

        Args:
            field_def: 字段定义
            value: 字段值
            data: 完整数据（用于跨字段验证）
            instance: 实例
            action: 操作类型

        Returns:
            验证后的值

        Raises:
            FieldValidationError: 验证失败
        """
        field_code = field_def.code

        # 1. 必填验证
        if field_def.is_required and (value is None or value == ''):
            raise FieldValidationError(
                field_code,
                f'{field_def.name}不能为空',
                'required'
            )

        # 空值且非必填，跳过后续验证
        if value is None or value == '':
            return None

        # 2. 类型验证
        value = self._validate_type(field_def, value)

        # 3. 长度验证
        if field_def.max_length:
            self._validate_length(field_def, value)

        # 4. 范围验证
        if field_def.min_value is not None or field_def.max_value is not None:
            self._validate_range(field_def, value)

        # 5. 正则验证
        if field_def.validation_regex:
            self._validate_regex(field_def, value)

        # 6. 选项验证
        if field_def.field_type in ['choice', 'multi_choice']:
            self._validate_options(field_def, value)

        # 7. 唯一性验证
        if field_def.is_unique:
            self._validate_uniqueness(field_def, value, instance, action)

        # 8. 关联验证
        if field_def.field_type in ['reference', 'user', 'department']:
            value = self._validate_reference(field_def, value)

        # 9. 自定义表达式验证
        if field_def.validation_expression:
            self._validate_expression(field_def, value, data)

        # 10. 自定义验证器
        if field_code in self.custom_validators:
            value = self.custom_validators[field_code](value, data, instance)

        return value

    def _validate_type(self, field_def: FieldDefinition, value: Any) -> Any:
        """类型验证"""
        field_type = field_def.field_type

        try:
            if field_type in ['text', 'textarea', 'email', 'url', 'choice']:
                return str(value)

            elif field_type == 'number':
                return float(value)

            elif field_type == 'integer':
                return int(value)

            elif field_type == 'float':
                return float(value)

            elif field_type == 'boolean':
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    if value.lower() in ['true', '1', 'yes']:
                        return True
                    if value.lower() in ['false', '0', 'no']:
                        return False
                return bool(value)

            elif field_type == 'date':
                from datetime import datetime
                if isinstance(value, str):
                    return datetime.fromisoformat(value).date()
                return value

            elif field_type == 'datetime':
                from datetime import datetime
                if isinstance(value, str):
                    return datetime.fromisoformat(value)
                return value

            elif field_type == 'time':
                from datetime import time
                if isinstance(value, str):
                    # 解析时间字符串
                    return time.fromisoformat(value)
                return value

            elif field_type == 'multi_choice':
                if isinstance(value, str):
                    # 尝试JSON解析
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        # 按逗号分割
                        return [v.strip() for v in value.split(',')]
                return value

            elif field_type in ['reference', 'user', 'department']:
                return str(value)

            else:
                return value

        except (ValueError, TypeError) as e:
            raise FieldValidationError(
                field_def.code,
                f'{field_def.name}的类型不正确，应为{field_type}类型',
                'invalid_type'
            )

    def _validate_length(self, field_def: FieldDefinition, value: Any):
        """长度验证"""
        if not isinstance(value, str):
            return

        max_length = field_def.max_length
        if max_length and len(value) > max_length:
            raise FieldValidationError(
                field_def.code,
                f'{field_def.name}的长度不能超过{max_length}个字符',
                'max_length'
            )

    def _validate_range(self, field_def: FieldDefinition, value: Any):
        """范围验证"""
        field_type = field_def.field_type

        if field_type in ['number', 'integer', 'float']:
            num_value = float(value)

            if field_def.min_value is not None and num_value < field_def.min_value:
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}不能小于{field_def.min_value}',
                    'min_value'
                )

            if field_def.max_value is not None and num_value > field_def.max_value:
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}不能大于{field_def.max_value}',
                    'max_value'
                )

        elif field_type in ['date', 'datetime']:
            from datetime import datetime

            if field_def.min_value:
                min_date = datetime.fromisoformat(field_def.min_value)
                if value < min_date:
                    raise FieldValidationError(
                        field_def.code,
                        f'{field_def.name}不能早于{field_def.min_value}',
                        'min_date'
                    )

            if field_def.max_value:
                max_date = datetime.fromisoformat(field_def.max_value)
                if value > max_date:
                    raise FieldValidationError(
                        field_def.code,
                        f'{field_def.name}不能晚于{field_def.max_value}',
                        'max_date'
                    )

    def _validate_regex(self, field_def: FieldDefinition, value: Any):
        """正则验证"""
        if not isinstance(value, str):
            return

        pattern = field_def.validation_regex
        if not pattern:
            return

        try:
            if not re.match(pattern, value):
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}的格式不正确',
                    'invalid_format'
                )
        except re.error:
            # 正则表达式错误，跳过验证
            pass

    def _validate_options(self, field_def: FieldDefinition, value: Any):
        """选项验证"""
        options = field_def.options or {}

        if field_def.field_type == 'choice':
            if value not in options:
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}的值必须是有效选项之一',
                    'invalid_choice'
                )

        elif field_def.field_type == 'multi_choice':
            if not isinstance(value, list):
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}必须是数组',
                    'invalid_type'
                )

            valid_options = set(options.keys())
            invalid_values = set(value) - valid_options

            if invalid_values:
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}包含无效选项：{", ".join(invalid_values)}',
                    'invalid_choice'
                )

    def _validate_uniqueness(
        self,
        field_def: FieldDefinition,
        value: Any,
        instance: Optional[DynamicData],
        action: str
    ):
        """唯一性验证"""
        # 获取业务对象
        business_object = field_def.business_object

        # 构建查询
        queryset = DynamicData.objects.filter(
            business_object=business_object
        ).filter(
            Q(**{f'custom_fields__{field_def.code}': value})
        )

        # 排除当前实例
        if instance and action == 'update':
            queryset = queryset.exclude(id=instance.id)

        # 组织过滤
        org_id = get_current_organization()
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        if queryset.exists():
            raise FieldValidationError(
                field_def.code,
                f'{field_def.name}的值"{value}"已存在',
                'unique'
            )

    def _validate_reference(self, field_def: FieldDefinition, value: Any) -> str:
        """关联字段验证"""
        if value is None:
            return None

        value = str(value)

        if field_def.field_type == 'reference':
            # 验证关联对象是否存在
            if field_def.reference_to:
                # TODO: 根据引用类型验证对象是否存在
                pass

        elif field_def.field_type == 'user':
            from apps.accounts.models import User
            if not User.objects.filter(id=value).exists():
                raise FieldValidationError(
                    field_def.code,
                    f'所选用户不存在',
                    'invalid_reference'
                )

        elif field_def.field_type == 'department':
            from apps.organizations.models import Department
            if not Department.objects.filter(id=value).exists():
                raise FieldValidationError(
                    field_def.code,
                    f'所选部门不存在',
                    'invalid_reference'
                )

        return value

    def _validate_expression(
        self,
        field_def: FieldDefinition,
        value: Any,
        data: Dict[str, Any]
    ):
        """自定义表达式验证"""
        expression = field_def.validation_expression
        if not expression:
            return

        try:
            from simpleeval import simple_eval

            # 构建验证上下文
            context = {
                'value': value,
                'field': field_def.code,
                'data': data,
                **data,
            }

            # 添加内置函数
            context.update({
                'len': len,
                'startswith': lambda s, p: str(s).startswith(p) if s else False,
                'endswith': lambda s, p: str(s).endswith(p) if s else False,
                'contains': lambda s, p: p in str(s) if s else False,
                'matches': lambda s, p: bool(re.match(p, str(s))) if s else False,
                'in': lambda v, arr: v in arr if arr else False,
                'between': lambda v, min_v, max_v: min_v <= v <= max_v,
            })

            # 计算表达式
            result = simple_eval(expression, names=context)

            # 结果应该为 True
            if not result:
                raise FieldValidationError(
                    field_def.code,
                    f'{field_def.name}的值不符合验证规则',
                    'validation_failed'
                )

        except Exception as e:
            # 表达式错误，记录但不阻止
            import logging
            logging.warning(f"Validation expression error for {field_def.code}: {e}")

    def _validate_cross_fields(
        self,
        data: Dict[str, Any],
        instance: Optional[DynamicData],
        action: str
    ) -> Dict[str, str]:
        """跨字段验证"""
        errors = {}

        for validator in self.cross_field_validators:
            try:
                validator(data, instance, action)
            except FieldValidationError as e:
                errors[e.field_code] = str(e)

        return errors

    def add_custom_validator(self, field_code: str, validator: Callable):
        """
        添加自定义验证器

        Args:
            field_code: 字段编码
            validator: 验证函数，签名为 (value, data, instance) -> validated_value
        """
        self.custom_validators[field_code] = validator

    def add_cross_field_validator(self, validator: Callable):
        """
        添加跨字段验证器

        Args:
            validator: 验证函数，签名为 (data, instance, action) -> None
        """
        self.cross_field_validators.append(validator)

    @staticmethod
    def create_required_field_validator(field_code: str, required_when: str):
        """
        创建条件必填验证器

        Args:
            field_code: 字段编码
            required_when: 条件表达式

        Returns:
            验证函数
        """
        def validator(value, data, instance):
            if value is None or value == '':
                try:
                    from simpleeval import simple_eval
                    context = {'data': data, **data}
                    is_required = simple_eval(required_when, names=context)

                    if is_required:
                        raise FieldValidationError(
                            field_code,
                            f'该字段在当前条件下不能为空',
                            'required'
                        )
                except Exception:
                    pass

            return value

        return validator

    @staticmethod
    def create_dependency_validator(
        field_code: str,
        depends_on: str,
        dependency_expression: str
    ):
        """
        创建字段依赖验证器

        Args:
            field_code: 字段编码
            depends_on: 依赖字段编码
            dependency_expression: 依赖关系表达式

        Returns:
            验证函数
        """
        def validator(value, data, instance):
            dependency_value = data.get(depends_on)

            try:
                from simpleeval import simple_eval
                context = {
                    'value': value,
                    'dependency': dependency_value,
                    'data': data,
                    **data,
                }

                is_valid = simple_eval(dependency_expression, names=context)

                if not is_valid:
                    raise FieldValidationError(
                        field_code,
                        f'该字段的值与{depends_on}不匹配',
                        'dependency_violation'
                    )
            except Exception:
                pass

            return value

        return validator


class CommonFieldValidators:
    """
    常用字段验证器集合
    """

    @staticmethod
    def email_validator(value, data, instance):
        """邮箱验证"""
        if value and '@' not in value:
            raise FieldValidationError('email', '请输入有效的邮箱地址', 'invalid_email')
        return value

    @staticmethod
    def phone_validator(value, data, instance):
        """手机号验证"""
        if value:
            pattern = r'^1[3-9]\d{9}$'
            if not re.match(pattern, str(value)):
                raise FieldValidationError('phone', '请输入有效的手机号', 'invalid_phone')
        return value

    @staticmethod
    def id_card_validator(value, data, instance):
        """身份证号验证"""
        if value:
            # 简单验证18位身份证
            pattern = r'^\d{17}[\dXx]$'
            if not re.match(pattern, str(value)):
                raise FieldValidationError('id_card', '请输入有效的身份证号', 'invalid_id_card')
        return value

    @staticmethod
    def url_validator(value, data, instance):
        """URL验证"""
        if value:
            pattern = r'^https?://[^\s/$.?#].[^\s]*$'
            if not re.match(pattern, str(value)):
                raise FieldValidationError('url', '请输入有效的URL地址', 'invalid_url')
        return value

    @staticmethod
    def positive_number_validator(value, data, instance):
        """正数验证"""
        if value is not None:
            num = float(value)
            if num <= 0:
                raise FieldValidationError(
                    'amount',
                    '请输入大于0的数值',
                    'invalid_positive'
                )
        return value

    @staticmethod
    def date_range_validator(
        start_field: str = 'start_date',
        end_field: str = 'end_date'
    ):
        """
        日期范围验证器

        Args:
            start_field: 开始日期字段
            end_field: 结束日期字段

        Returns:
            跨字段验证函数
        """
        def validator(data, instance, action):
            start_value = data.get(start_field)
            end_value = data.get(end_field)

            if start_value and end_value:
                from datetime import datetime
                start_dt = datetime.fromisoformat(start_value) if isinstance(start_value, str) else start_value
                end_dt = datetime.fromisoformat(end_value) if isinstance(end_value, str) else end_value

                if start_dt > end_dt:
                    raise FieldValidationError(
                        end_field,
                        f'{start_field}不能晚于{end_field}',
                        'invalid_range'
                    )

        return validator

    @staticmethod
    def password_strength_validator(value, data, instance):
        """密码强度验证"""
        if value:
            if len(str(value)) < 8:
                raise FieldValidationError('password', '密码长度至少8位', 'too_short')

            # 检查是否包含数字和字母
            has_digit = any(c.isdigit() for c in str(value))
            has_alpha = any(c.isalpha() for c in str(value))

            if not (has_digit and has_alpha):
                raise FieldValidationError(
                    'password',
                    '密码必须包含数字和字母',
                    'weak_password'
                )
        return value
```

### 3.2 使用示例

```python
# 基本使用
from apps.common.validators.dynamic_field import DynamicFieldValidator
from apps.system.models import FieldDefinition

field_definitions = FieldDefinition.objects.filter(
    business_object__code='Asset'
)

validator = DynamicFieldValidator(field_definitions)

# 验证数据
data = {
    'asset_code': 'ASSET001',
    'asset_name': '办公电脑',
    'purchase_price': 5000,
    'quantity': 10
}

try:
    validated_data = validator.validate(data)
    print("验证通过:", validated_data)
except ValidationError as e:
    print("验证失败:", e.message_dict)

# 添加自定义验证器
def validate_quantity(value, data, instance):
    if value and value < 0:
        raise FieldValidationError('quantity', '数量不能为负数', 'invalid_quantity')
    return value

validator.add_custom_validator('quantity', validate_quantity)

# 添加跨字段验证器
def validate_price_and_quantity(data, instance, action):
    price = data.get('purchase_price', 0)
    quantity = data.get('quantity', 0)
    total = price * quantity
    if total > 1000000:
        raise FieldValidationError(
            'purchase_price',
            '总价超过100万，需要特殊审批',
            'exceeds_limit'
        )

validator.add_cross_field_validator(validate_price_and_quantity)

# 使用条件必填验证器
from apps.common.validators.dynamic_field import DynamicFieldValidator

validator = DynamicFieldValidator(field_definitions)

# 添加条件必填：当类型为"贵重物品"时，保险金额必填
required_validator = DynamicFieldValidator.create_required_field_validator(
    'insurance_amount',
    "data.get('asset_type') == 'valuable'"
)
validator.add_custom_validator('insurance_amount', required_validator)
```

---

## 4. 内置验证规则

### 4.1 字段类型默认规则

| 字段类型 | 默认验证规则 |
|---------|-------------|
| text | 字符串类型，可选长度限制 |
| textarea | 字符串类型，可选长度限制 |
| number | 数值类型，可选范围限制 |
| integer | 整数类型，可选范围限制 |
| float | 浮点类型，可选范围限制 |
| boolean | 布尔类型（true/false/1/0） |
| date | 日期类型（ISO 8601格式） |
| datetime | 日期时间类型（ISO 8601格式） |
| time | 时间类型（ISO 8601格式） |
| email | 邮箱格式 |
| url | URL格式 |
| choice | 值必须在选项中 |
| multi_choice | 值数组，每个值必须在选项中 |
| file | 文件路径字符串 |
| image | 图片路径字符串 |
| reference | 关联对象ID（UUID格式） |
| user | 用户ID（UUID格式） |
| department | 部门ID（UUID格式） |
| formula | 只读，无需验证 |

### 4.2 FieldDefinition 验证相关字段

```python
# apps/system/models.py

class FieldDefinition(BaseModel):
    # ... 其他字段

    # 验证相关
    is_required = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)

    # 类型限制
    max_length = models.IntegerField(null=True, blank=True)
    min_value = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)
    max_value = models.DecimalField(null=True, blank=True, max_digits=20, decimal_places=4)

    # 验证规则
    validation_regex = models.CharField(max_length=500, null=True, blank=True)
    validation_expression = models.CharField(max_length=1000, null=True, blank=True)
    validation_message = models.CharField(max_length=500, null=True, blank=True)

    # 选项限制
    options = models.JSONField(default=dict, blank=True)

    # 关联限制
    reference_to = models.CharField(max_length=100, null=True, blank=True)
```

---

## 5. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/common/validators/__init__.py` | 验证器模块导出 |
| `backend/apps/common/validators/base.py` | 验证器基类 |
| `backend/apps/common/validators/dynamic_field.py` | 动态字段验证器 |
| `backend/apps/common/validators/type_validators.py` | 类型验证器 |
| `backend/apps/common/validators/expression_validators.py` | 表达式验证器 |

---

## 6. 前端集成

### 6.1 验证规则导出

```python
# backend/apps/system/views.py

from rest_framework.decorators import action
from apps.common.validators.dynamic_field import DynamicFieldValidator

class BusinessObjectViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['get'])
    def validation_rules(self, request, pk=None):
        """获取验证规则（供前端使用）"""
        business_object = self.get_object()
        field_definitions = business_object.field_definitions.filter(is_active=True)

        rules = []
        for fd in field_definitions:
            rule = {
                'field': fd.code,
                'label': fd.name,
                'required': fd.is_required,
                'readonly': fd.is_readonly,
                'unique': fd.is_unique,
            }

            # 类型规则
            if fd.field_type in ['text', 'textarea']:
                if fd.max_length:
                    rule['maxLength'] = fd.max_length
            elif fd.field_type in ['number', 'integer', 'float']:
                if fd.min_value is not None:
                    rule['minimum'] = float(fd.min_value)
                if fd.max_value is not None:
                    rule['maximum'] = float(fd.max_value)

            # 正则规则
            if fd.validation_regex:
                rule['pattern'] = fd.validation_regex

            # 选项规则
            if fd.options:
                rule['enum'] = list(fd.options.keys())

            rules.append(rule)

        return Response({'success': True, 'data': rules})
```

### 6.2 前端验证规则转换

```javascript
// frontend/src/utils/validation.js

/**
 * 将后端验证规则转换为前端表单验证规则
 */
export function convertValidationRules(backendRules) {
    const rules = {}

    backendRules.forEach(rule => {
        const fieldRules = []

        // 必填验证
        if (rule.required) {
            fieldRules.push({
                required: true,
                message: `${rule.label}不能为空`,
                trigger: 'blur'
            })
        }

        // 长度验证
        if (rule.maxLength) {
            fieldRules.push({
                max: rule.maxLength,
                message: `${rule.label}不能超过${rule.maxLength}个字符`,
                trigger: 'blur'
            })
        }

        // 数值范围验证
        if (rule.minimum !== undefined) {
            fieldRules.push({
                type: 'number',
                min: rule.minimum,
                message: `${rule.label}不能小于${rule.minimum}`,
                trigger: 'blur'
            })
        }

        if (rule.maximum !== undefined) {
            fieldRules.push({
                type: 'number',
                max: rule.maximum,
                message: `${rule.label}不能大于${rule.maximum}`,
                trigger: 'blur'
            })
        }

        // 正则验证
        if (rule.pattern) {
            fieldRules.push({
                pattern: new RegExp(rule.pattern),
                message: `${rule.label}格式不正确`,
                trigger: 'blur'
            })
        }

        // 选项验证
        if (rule.enum) {
            fieldRules.push({
                type: 'enum',
                enum: rule.enum,
                message: `${rule.label}的值必须是有效选项之一`,
                trigger: 'change'
            })
        }

        rules[rule.field] = fieldRules
    })

    return rules
}
```
