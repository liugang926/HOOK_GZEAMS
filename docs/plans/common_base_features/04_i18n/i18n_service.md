# 多语言服务层设计

## 任务概述

提供统一的多语言服务层（TranslationService），集中处理所有翻译逻辑，包括后端翻译查询、缓存管理、前端语言包生成等。

---

## 1. 设计目标

### 1.1 核心功能

| 功能 | 说明 |
|------|------|
| 统一翻译接口 | `get_text(namespace, key, lang, default)` |
| 翻译缓存 | 减少数据库查询 |
| 批量加载 | 支持批量获取翻译，减少查询次数 |
| 缺失翻译处理 | 自动记录缺失的翻译键 |
| 语言包生成 | 为前端生成完整的语言包 JSON |
| 热重载支持 | 开发环境支持翻译热更新 |

### 1.2 设计原则

1. **高性能** - 缓存优先，批量查询
2. **易用性** - 简单的 API 调用
3. **可扩展** - 支持自定义翻译来源
4. **容错性** - 翻译缺失时返回默认值

---

## 国际化服务API模型

### GetTranslation 请求模型

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| namespace | string | 是 | - | 翻译命名空间 (如: asset, common) |
| key | string | 是 | - | 翻译键 (如: status.idle) |
| language | string | 否 | 从 context 获取 | 语言代码 (如: zh-CN, en-US) |
| default | string | 否 | key | 默认值 (翻译不存在时返回) |
| use_cache | boolean | 否 | true | 是否使用缓存 |

### GetTranslation 响应模型

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| data.translation | string | 翻译后的文本 |
| data.is_cached | boolean | 是否来自缓存 |

### SetTranslation 请求模型

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| key | string | 是 | 翻译键 (完整路径: namespace.key) |
| namespace | string | 是 | 命名空间 |
| translations | object | 是 | 翻译对象 {language_code: text} |
| context | string | 否 | 上下文 (区分同词不同义) |
| type | string | 否 | 翻译类型 (label/message/enum) |
| default_text | string | 否 | 默认文本 |

### SetTranslation 响应模型

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| data.id | UUID | 翻译记录 ID |
| data.key | string | 翻译键 |
| data.namespace | string | 命名空间 |
| data.translations_count | integer | 创建的翻译数量 |

### GetLanguagePack 请求模型

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| lang | string | 否 | zh-CN | 语言代码 |
| use_cache | boolean | 否 | true | 是否使用缓存 |

### GetLanguagePack 响应模型

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| data.language | string | 语言代码 |
| data.translations | object | 嵌套翻译字典 {namespace: {key: text}} |
| data.count | integer | 翻译条目总数 |

### SyncTranslations 请求模型

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| namespace | string | 是 | 命名空间 |
| translations | object | 是 | 翻译对象 {key: {lang: text}} |
| overwrite | boolean | 否 | 是否覆盖已存在的翻译 (默认 false) |

### SyncTranslations 响应模型

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 操作是否成功 |
| data.created | integer | 新创建的翻译数量 |
| data.updated | integer | 更新的翻译数量 |
| data.skipped | integer | 跳过的翻译数量 |
| data.errors | array | 错误列表 (如果有) |

---

## 2. 文件结构

```
backend/apps/common/services/
├── i18n_service.py              # 核心多语言服务
├── translation_cache.py         # 翻译缓存管理
└── enum_translation_service.py  # 枚举翻译同步服务
```

---

## 3. TranslationService 实现

### 3.1 核心服务类

#### TranslationCache 类

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `_make_key` | `*parts: str` | `str` | 生成缓存键 |
| `get_translation` | `namespace, key, lang_code` | `Optional[str]` | 获取单个翻译缓存 |
| `set_translation` | `namespace, key, lang_code, text` | - | 设置单个翻译缓存 |
| `get_namespace` | `namespace, lang_code` | `Optional[Dict]` | 获取命名空间的所有翻译缓存 |
| `set_namespace` | `namespace, lang_code, translations` | - | 设置命名空间的所有翻译缓存 |
| `get_language_pack` | `lang_code` | `Optional[Dict]` | 获取语言包缓存 |
| `set_language_pack` | `lang_code, pack` | - | 设置语言包缓存 |
| `invalidate_namespace` | `namespace` | - | 清除命名空间缓存 |
| `invalidate_language` | `lang_code` | - | 清除语言相关缓存 |
| `invalidate_all` | - | - | 清除所有翻译缓存 |

#### TranslationCache 配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `CACHE_PREFIX` | `'i18n'` | 缓存键前缀 |
| `CACHE_TIMEOUT` | `3600` | 缓存过期时间 (秒) |

#### TranslationService 类

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_current_language` | - | `str` | 获取当前语言代码 |
| `set_current_language` | `lang_code: str` | - | 设置当前语言 |
| `clear_current_language` | - | - | 清除当前语言设置 |
| `get_text` | `namespace, key, lang_code, default, use_cache` | `str` | 获取翻译文本 |
| `get_text_auto` | `key, lang_code, default, use_cache` | `str` | 自动解析命名空间的翻译获取 |
| `get_namespace` | `namespace, lang_code, use_cache` | `Dict[str, str]` | 获取命名空间的所有翻译 |
| `get_language_pack` | `lang_code, use_cache` | `Dict[str, Dict]` | 获取前端语言包 (嵌套字典格式) |
| `translate_object` | `instance, lang_code, fields` | `Dict` | 翻译模型实例的多语言字段 |
| `translate_queryset` | `queryset, lang_code, fields` | `List[Dict]` | 翻译查询集的多语言字段 |
| `create_translation` | `namespace, key, translations, context, type, default_text` | `Translation` | 创建或更新翻译 |
| `sync_translations_from_file` | `namespace, file_path, lang_code` | - | 从文件同步翻译 (支持 JSON/YAML) |

#### get_language_pack 返回格式

```json
{
  "asset": {
    "status": {
      "idle": "闲置",
      "in_use": "使用中"
    }
  },
  "common": {
    "buttons": {
      "save": "保存",
      "cancel": "取消"
    }
  }
}
```

### 3.2 使用示例

```python
# 在 ViewSet 中使用
from apps.common.services.i18n_service import TranslationService

class AssetViewSet(BaseModelViewSet):
    def list(self, request, *args, **kwargs):
        """获取资产列表，翻译状态显示"""
        response = super().list(request, *args, **kwargs)

        # 获取用户语言
        lang_code = request.META.get('HTTP_ACCEPT_LANGUAGE', 'zh-CN')

        # 翻译状态值
        for item in response.data['results']:
            status = item['status']
            item['status_display'] = TranslationService.get_text(
                'asset.status',
                status,
                lang_code,
                default=status
            )

        return response

    @action(detail=False, methods=['get'])
    def language_pack(self, request):
        """获取前端语言包"""
        lang_code = request.query_params.get('lang', 'zh-CN')
        pack = TranslationService.get_language_pack(lang_code)
        return Response({
            'success': True,
            'data': pack
        })
```

---

## 4. DRF 集成

### 4.1 TranslatedFieldMixin

#### 序列化器类声明

| 序列化器类 | 基类 | 说明 |
|-----------|------|------|
| `TranslatedFieldMixin` | `Mixin` | 为序列化器自动添加翻译后的字段 |
| `TranslatedModelSerializer` | `TranslatedFieldMixin + ModelSerializer` | 自动处理 `*_translations` 字段的模型序列化器 |

#### TranslatedFieldMixin 方法

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__init__` | `*args, **kwargs` | - | 接收 `lang_code` 参数 |
| `to_representation` | `instance` | `dict` | 自动翻译多语言字段，添加 `{field}_i18n` 字段 |
| `get_language_from_context` | - | `str` | 从请求上下文获取语言，默认 `'zh-CN'` |

---

## 5. API 端点

### 5.1 翻译管理 API

#### TranslationViewSet 端点

| 端点 | 方法 | 说明 | 请求参数 | 响应 |
|------|------|------|----------|------|
| `/api/translations/language_pack/` | GET | 获取前端语言包 | `lang: str` | `{success, data: {language, translations}}` |
| `/api/translations/namespaces/` | GET | 获取所有命名空间 | - | `{success, data: [str]}` |
| `/api/translations/languages/` | GET | 获取所有启用的语言 | - | `{success, data: [{code, name, native_name, flag, is_default}]}` |
| `/api/translations/sync/` | POST | 同步翻译 | `namespace, translations: {}` | `{success, message}` |
| `/api/translations/clear_cache/` | POST | 清除翻译缓存 | - | `{success, message}` |

#### languages 端点响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `str` | 语言代码 |
| `name` | `str` | 语言名称 |
| `native_name` | `str` | 本地语言名称 |
| `flag` | `str` | 语言图标 (emoji) |
| `is_default` | `bool` | 是否为默认语言 |

---

## 6. 输出产物

| 文件 | 说明 |
|------|------|
| `backend/apps/common/services/i18n_service.py` | 核心多语言服务 |
| `backend/apps/common/services/translation_cache.py` | 翻译缓存管理 |
| `backend/apps/common/serializers/translation.py` | 翻译序列化器 |
| `backend/apps/system/viewsets/translation.py` | 翻译管理 API |

---

## 7. 使用场景总结

| 场景 | 使用方式 | 示例 |
|------|---------|------|
| 单个翻译 | `TranslationService.get_text()` | 获取状态翻译 |
| 批量翻译 | `TranslationService.get_namespace()` | 获取模块所有翻译 |
| 前端语言包 | `TranslationService.get_language_pack()` | 生成前端 i18n 数据 |
| 字段翻译 | `TranslatedModelSerializer` | 自动翻译序列化字段 |
| 枚举翻译 | `TranslatedEnumField` | 翻译 choices 选项 |
