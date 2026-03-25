# 多语言模型设计

## 任务概述

为 GZEAMS 低代码平台设计完整的多语言（i18n）支持，包括后端翻译模型、前端多语言组件，以及与元数据驱动的集成方案。

---

## 1. 设计背景

### 1.1 多语言需求

| 场景 | 说明 | 示例 |
|------|------|------|
| **业务对象名称** | 资产分类、部门等需要多语言显示 | Asset Category → 资产分类 |
| **字段标签** | 表单字段标签的国际化 | Purchase Price → 采购价格 |
| **枚举选项** | 状态、类型等选项的翻译 | Status: Active → 启用 |
| **验证消息** | 错误提示的本地化 | This field is required → 此字段必填 |
| **动态内容** | 用户录入的多语言内容 | 资产备注、描述 |

### 1.2 设计目标

1. **统一管理** - 集中管理所有翻译内容
2. **动态加载** - 按需加载语言包，减少初始体积
3. **实时切换** - 无刷新切换语言
4. **元数据集成** - 与元数据驱动无缝集成
5. **可扩展性** - 支持添加新语言

---

## 2. 后端多语言模型

### 2.1 数据模型设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          多语言模型架构                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│ │                    Language (语言表)                                │ │
│ │  - code: 'zh-CN', 'en-US'                                          │ │
│ │  - name: '简体中文', 'English'                                     │ │
│ │  - is_active: bool                                                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│ │                    Translation (翻译表)                             │ │
│ │  - key: 翻译键 (唯一)                                              │ │
│ │  - namespace: 命名空间 (用于分组)                                  │ │
│ │  - context: 上下文 (可选，用于区分同词不同义)                      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│ │                    TranslationText (翻译内容)                       │ │
│ │  - translation: ForeignKey → Translation                          │ │
│  │  - language: ForeignKey → Language                               │ │
│  │  - text: 翻译文本                                                │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 国际化数据模型定义

#### Language 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 (继承自 BaseModel) |
| code | string | max=10, unique, indexed | 语言代码 (zh-CN, en-US, ja-JP) |
| name | string | max=50 | 语言名称 (简体中文, English) |
| native_name | string | max=50 | 本地语言名称 |
| flag | string | max=10, nullable | 语言图标 (🇨🇳, 🇺🇸, 🇯🇵) |
| sort_order | integer | default=0 | 排序顺序 |
| is_default | boolean | default=False | 是否默认语言 |
| is_active | boolean | default=True, indexed | 是否启用 |
| organization | ForeignKey | indexed | 组织外键 (继承自 BaseModel) |
| is_deleted | boolean | default=False, indexed | 软删除标记 (继承自 BaseModel) |
| deleted_at | datetime | nullable | 删除时间 (继承自 BaseModel) |
| created_at | datetime | auto_now_add | 创建时间 (继承自 BaseModel) |
| updated_at | datetime | auto_now | 更新时间 (继承自 BaseModel) |
| created_by | ForeignKey | nullable | 创建人 (继承自 BaseModel) |
| custom_fields | JSONB | default={} | 动态字段 (继承自 BaseModel) |

#### Translation 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 (继承自 BaseModel) |
| key | string | max=200, unique, indexed | 翻译键 (asset.status.idle) |
| namespace | string | max=50, indexed | 命名空间 (asset, common) |
| context | string | max=100, nullable | 上下文 (区分同词不同义) |
| default_text | string | max=500, nullable | 默认文本 (回退值) |
| type | string | max=20, choices | 翻译类型 (label/message/enum/placeholder/tooltip/title/description) |
| is_system | boolean | default=False | 是否系统翻译 (不可删除) |
| organization | ForeignKey | indexed | 组织外键 (继承自 BaseModel) |
| is_deleted | boolean | default=False, indexed | 软删除标记 (继承自 BaseModel) |
| deleted_at | datetime | nullable | 删除时间 (继承自 BaseModel) |
| created_at | datetime | auto_now_add | 创建时间 (继承自 BaseModel) |
| updated_at | datetime | auto_now | 更新时间 (继承自 BaseModel) |
| created_by | ForeignKey | nullable | 创建人 (继承自 BaseModel) |
| custom_fields | JSONB | default={} | 动态字段 (继承自 BaseModel) |

#### TranslationText 模型

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK | 主键 (继承自 BaseModel) |
| translation | ForeignKey | indexed, CASCADE | 关联翻译键 (Translation.texts) |
| language | ForeignKey | indexed, CASCADE | 语言 (Language.translations) |
| text | text | NOT NULL | 翻译文本 |
| is_machine_translated | boolean | default=False | 是否机器翻译 |
| quality_score | integer | nullable, min=1, max=5 | 翻译质量评分 |
| organization | ForeignKey | indexed | 组织外键 (继承自 BaseModel) |
| is_deleted | boolean | default=False, indexed | 软删除标记 (继承自 BaseModel) |
| deleted_at | datetime | nullable | 删除时间 (继承自 BaseModel) |
| created_at | datetime | auto_now_add | 创建时间 (继承自 BaseModel) |
| updated_at | datetime | auto_now | 更新时间 (继承自 BaseModel) |
| created_by | ForeignKey | nullable | 创建人 (继承自 BaseModel) |
| custom_fields | JSONB | default={} | 动态字段 (继承自 BaseModel) |

**Unique Constraint:** `['translation', 'language']`

### 2.2 Language 模型

#### 模型定义

| 组件类型 | 说明 |
|---------|------|
| **基类** | `BaseModel` (apps.common.models) |
| **表名** | `system_language` |
| **管理器** | `LanguageManager` (自定义) |

#### 字段声明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `code` | `CharField(10)` | `unique=True` | ISO 639-1 + ISO 3166-1 语言代码 (如: zh-CN, en-US) |
| `name` | `CharField(50)` | - | 语言名称 (如: 简体中文, English) |
| `native_name` | `CharField(50)` | - | 本地语言名称 |
| `flag` | `CharField(10)` | `blank=True` | 语言图标 (如: 🇨🇳, 🇺🇸) |
| `sort_order` | `IntegerField` | `default=0` | 排序顺序 |
| `is_active` | `BooleanField` | `default=True` | 是否启用 |
| `is_default` | `BooleanField` | `default=False` | 是否为默认语言 |

#### 继承的公共字段

| 字段 | 来源 | 说明 |
|------|------|------|
| `id` | BaseModel | UUID 主键 |
| `organization` | BaseModel | 组织外键 |
| `is_deleted` | BaseModel | 软删除标记 |
| `deleted_at` | BaseModel | 删除时间 |
| `created_at` | BaseModel | 创建时间 |
| `updated_at` | BaseModel | 更新时间 |
| `created_by` | BaseModel | 创建人 |
| `custom_fields` | BaseModel | JSONB 动态字段 |

#### 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__str__` | - | `str` | 返回格式: `{flag} {name} ({code})` |
| `save` | `*args, **kwargs` | - | 覆盖父类方法，确保只有一个默认语言 |

#### LanguageManager 方法

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_default` | - | `Language` | 获取默认语言，无默认时返回第一个启用的语言 |
| `get_active` | - | `QuerySet` | 获取所有启用的语言 |
| `get_by_code` | `code: str` | `Language` | 根据代码获取语言 |

### 2.3 Translation 模型

#### 模型定义

| 组件类型 | 说明 |
|---------|------|
| **基类** | `BaseModel` (apps.common.models) |
| **表名** | `system_translation` |
| **关联关系** | `texts` -> `TranslationText` (related_name) |

#### 字段声明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `key` | `CharField(200)` | `unique=True, db_index=True` | 翻译键 (如: asset.status.idle) |
| `namespace` | `CharField(50)` | `db_index=True` | 命名空间 (如: asset, common) |
| `context` | `CharField(100)` | `blank=True` | 上下文 (区分同词不同义) |
| `default_text` | `CharField(500)` | `blank=True` | 默认文本 (回退值) |
| `type` | `CharField(20)` | `choices` | 翻译类型 (label/message/enum/placeholder/tooltip/title/description) |
| `is_system` | `BooleanField` | `default=False` | 是否为系统翻译 (不可删除) |

#### 翻译类型选项

| 值 | 显示名称 | 说明 |
|----|---------|------|
| `label` | 标签 | 字段标签、按钮文本 |
| `message` | 消息 | 提示消息、错误信息 |
| `enum` | 枚举 | 枚举值翻译 |
| `placeholder` | 占位符 | 输入框占位符 |
| `tooltip` | 提示 | 工具提示 |
| `title` | 标题 | 页面/区块标题 |
| `description` | 描述 | 详细描述 |

#### 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__str__` | - | `str` | 返回格式: `{namespace}.{key}` |
| `get_translations` | - | `dict` | 获取所有语言的翻译 `{code: text}` |
| `get_translation` | `language_code: str` | `str` | 获取指定语言的翻译，不存在时返回 `default_text` |

### 2.4 TranslationText 模型

#### 模型定义

| 组件类型 | 说明 |
|---------|------|
| **基类** | `BaseModel` (apps.common.models) |
| **表名** | `system_translation_text` |
| **唯一约束** | `['translation', 'language']` |

#### 字段声明

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `translation` | `ForeignKey` | `on_delete=CASCADE, related_name='texts'` | 关联的翻译键 |
| `language` | `ForeignKey` | `on_delete=CASCADE, related_name='translations'` | 语言 |
| `text` | `TextField` | - | 翻译文本 |
| `is_machine_translated` | `BooleanField` | `default=False` | 是否为机器翻译 |
| `quality_score` | `IntegerField` | `null=True, blank=True` | 翻译质量评分 (1-5) |

#### 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__str__` | - | `str` | 返回格式: `{key} ({code}): {text[:50]}` |

### 2.5 支持多语言的枚举字段

#### 字段类声明

| 字段类 | 基类 | 用途 | 配置参数 |
|--------|------|------|----------|
| `TranslatedCharField` | `CharField` | 翻译字符字段显示值 | `source_field`, `namespace` |
| `TranslatedChoiceFieldMixin` | `Mixin` | 为枚举字段提供翻译能力 | `translation_namespace` |
| `TranslatedEnumField` | `TranslatedChoiceFieldMixin + CharField` | 翻译枚举字段 | `choices`, `translation_namespace` |

#### TranslatedCharField 配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `source_field` | `str` | 是 | 源字段名 |
| `namespace` | `str` | 是 | 翻译命名空间 |

#### TranslatedEnumField 配置

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `choices` | `tuple` | 是 | 枚举选项列表 |
| `translation_namespace` | `str` | 是 | 翻译命名空间 |

#### 使用示例

```python
# TranslatedEnumField 示例
class Asset(BaseModel):
    class Status(models.TextChoices):
        IDLE = 'idle'
        IN_USE = 'in_use'

    status = TranslatedEnumField(
        choices=Status.choices,
        translation_namespace='asset.status'
    )
```

---

## 3. 多语言枚举配置

### 3.1 枚举翻译存储

对于状态、类型等枚举值，翻译键格式建议：

```
{namespace}.{enum_field}.{value}
```

示例：

| 翻译键 | 中文 | 英文 | 日文 |
|--------|------|------|------|
| `asset.status.idle` | 闲置 | Idle | 遊休 |
| `asset.status.in_use` | 使用中 | In Use | 使用中 |
| `asset.status.scrap` | 报废 | Scrapped | 廃棄 |
| `asset.type.equipment` | 设备 | Equipment | 設備 |
| `asset.type.vehicle` | 车辆 | Vehicle | 車両 |

### 3.2 枚举翻译同步

#### EnumTranslationService 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `sync_enum_translations` | `model_class, field_name, namespace, enum_class=None` | - | 同步指定枚举字段的翻译 |
| `sync_all_enums` | - | - | 同步所有预定义的枚举翻译 |

#### sync_enum_translations 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model_class` | `Model` | 是 | 模型类 |
| `field_name` | `str` | 是 | 字段名 |
| `namespace` | `str` | 是 | 翻译命名空间 |
| `enum_class` | `class` | 否 | 枚举类 (不提供时从字段提取) |

#### 预定义枚举同步

| 模型 | 字段 | 命名空间 |
|------|------|----------|
| `Asset` | `status` | `asset` |
| `Asset` | `asset_type` | `asset` |

---

## 4. 元数据集成

### 4.1 BusinessObject 多语言

#### 新增字段

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name_translations` | `JSONField` | `{}` | 名称翻译 `{lang_code: name}` |
| `description_translations` | `JSONField` | `{}` | 描述翻译 `{lang_code: description}` |

#### 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_name` | `lang_code: str = None` | `str` | 获取指定语言的名称，不存在时返回 `name` |
| `get_description` | `lang_code: str = None` | `str` | 获取指定语言的描述，不存在时返回 `description` |

### 4.2 FieldDefinition 多语言

#### 新增字段

| 字段名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `label_translations` | `JSONField` | `{}` | 标签翻译 `{lang_code: label}` |
| `placeholder_translations` | `JSONField` | `{}` | 占位符翻译 |
| `help_text_translations` | `JSONField` | `{}` | 帮助文本翻译 |
| `options_translations` | `JSONField` | `{}` | 选项翻译 `{lang_code: {value: label}}` |

#### 方法声明

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_label` | `lang_code: str = None` | `str` | 获取指定语言的标签 |
| `get_placeholder` | `lang_code: str = None` | `str` | 获取指定语言的占位符 |
| `get_help_text` | `lang_code: str = None` | `str` | 获取指定语言的帮助文本 |
| `get_options_translated` | `lang_code: str = None` | `dict` | 获取翻译后的选项字典 |

---

## 5. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/system/models.py` | Language、Translation、TranslationText 模型 |
| `backend/apps/common/models.py` | TranslatedCharField、TranslatedEnumField |
| `backend/apps/system/services/enum_translation_service.py` | 枚举翻译同步服务 |
| `backend/apps/common/services/i18n_service.py` | 多语言服务 (详见 i18n_service.md) |

---

## 6. 迁移步骤

```bash
# 1. 生成迁移文件
python manage.py makemigrations system

# 2. 执行迁移
python manage.py migrate

# 3. 创建默认语言
python manage.py create_default_languages

# 4. 同步枚举翻译
python manage.py sync_enum_translations
```

---

## 7. 与现有代码的关系

### 7.1 兼容性

- **不影响现有代码** - 现有字段继续可用
- **渐进式迁移** - 可逐步为字段添加多语言支持
- **向后兼容** - 未翻译内容使用默认值

### 7.2 替换关系

| 原有方式 | 新方式 | 迁移建议 |
|---------|-------|---------|
| 硬编码标签 | `label_translations` | 逐步迁移 |
| choices 定义 | 翻译键系统 | 重新定义 |
| 前端 i18n 文件 | 后端翻译服务 | 统一管理 |
