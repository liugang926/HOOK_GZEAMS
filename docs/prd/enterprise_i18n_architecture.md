# 企业级国际化架构 PRD

## 1. 概述

### 1.1 背景

当前系统采用前端静态 JSON 文件管理翻译，这种方式适用于固定 UI 文本，但不适用于低代码平台的动态元数据（业务对象、字段定义、字典项、菜单等）。随着产品面向企业客户，需要一套**可审计、可扩展、数据库驱动**的国际化架构。

### 1.2 目标

- **动态内容多语言**：业务对象、字段、字典、菜单等支持多语言配置
- **可扩展性**：支持任意语言扩展，无需修改代码
- **可审计性**：翻译变更有记录可追溯
- **集中管理**：提供统一的翻译管理界面
- **向后兼容**：现有静态翻译继续生效，渐进式迁移

### 1.3 范围

| 内容类型 | 处理方式 | 说明 |
|---------|---------|------|
| 按钮、提示、状态 | 前端静态 JSON | 保持不变 |
| 业务对象名称 | 数据库 Translation 表 | 新增 |
| 字段标签/描述 | 数据库 Translation 表 | 新增 |
| 字典类型/项 | 数据库 Translation 表 | 新增 |
| 菜单标题 | 数据库 Translation 表 | 新增 |
| 部门/组织名称 | 数据库 Translation 表 | 新增 |

---

## 2. 核心模型设计

### 2.1 Translation 模型

```python
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Translation(models.Model):
    """
    通用翻译表 - 存储任意模型任意字段的多语言翻译
    """
    # 关联到任意模型
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        verbose_name="内容类型"
    )
    object_id = models.PositiveIntegerField(verbose_name="对象ID")
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # 翻译字段标识
    field_name = models.CharField(
        max_length=50, 
        verbose_name="字段名",
        help_text="如: name, label, description"
    )
    
    # 语言标识 (遵循 BCP 47 标准)
    locale = models.CharField(
        max_length=10, 
        verbose_name="语言代码",
        help_text="如: en-US, zh-CN, ja-JP"
    )
    
    # 翻译值
    value = models.TextField(verbose_name="翻译值")
    
    # 审计字段
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_translations'
    )
    updated_by = models.ForeignKey(
        'accounts.User', 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='updated_translations'
    )
    
    class Meta:
        db_table = 'core_translation'
        unique_together = ['content_type', 'object_id', 'field_name', 'locale']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['locale']),
        ]
        verbose_name = "翻译"
        verbose_name_plural = "翻译"
    
    def __str__(self):
        return f"{self.content_type}:{self.object_id}.{self.field_name}[{self.locale}]"
```

### 2.2 Language 模型

```python
class Language(models.Model):
    """
    系统支持的语言配置
    """
    code = models.CharField(
        max_length=10, 
        unique=True,
        verbose_name="语言代码",
        help_text="如: en-US, zh-CN"
    )
    name = models.CharField(
        max_length=50, 
        verbose_name="语言名称",
        help_text="如: English, 简体中文"
    )
    native_name = models.CharField(
        max_length=50, 
        verbose_name="本地名称",
        help_text="如: English, 中文"
    )
    is_default = models.BooleanField(
        default=False, 
        verbose_name="默认语言"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="启用状态"
    )
    sort_order = models.IntegerField(
        default=0, 
        verbose_name="排序"
    )
    
    class Meta:
        db_table = 'core_language'
        ordering = ['sort_order', 'code']
        verbose_name = "语言"
        verbose_name_plural = "语言"
```

---

## 3. 后端服务设计

### 3.1 TranslationService

```python
# apps/core/services/translation_service.py

class TranslationService:
    """翻译服务 - 提供统一的翻译读写接口"""
    
    @classmethod
    def get_translation(cls, obj, field_name: str, locale: str) -> str | None:
        """
        获取对象指定字段的翻译
        
        Args:
            obj: 任意 Django 模型实例
            field_name: 字段名 (如 'name', 'label')
            locale: 语言代码 (如 'en-US')
            
        Returns:
            翻译值，如果不存在则返回 None
        """
        pass
    
    @classmethod
    def get_translations(cls, obj, locale: str) -> dict:
        """
        获取对象所有字段的翻译
        
        Returns:
            {"name": "Asset", "description": "Fixed asset management"}
        """
        pass
    
    @classmethod
    def set_translation(cls, obj, field_name: str, locale: str, value: str, user=None):
        """
        设置对象指定字段的翻译
        """
        pass
    
    @classmethod
    def set_translations(cls, obj, locale: str, translations: dict, user=None):
        """
        批量设置对象多个字段的翻译
        
        Args:
            translations: {"name": "Asset", "description": "..."}
        """
        pass
    
    @classmethod
    def delete_translations(cls, obj, locale: str = None):
        """
        删除对象的翻译 (当对象删除时调用)
        
        Args:
            locale: 如果指定则只删除该语言，否则删除全部
        """
        pass
    
    @classmethod
    def get_localized_value(cls, obj, field_name: str, locale: str) -> str:
        """
        获取本地化后的值 (优先翻译，无翻译则返回原值)
        
        这是 API 响应中最常用的方法
        """
        translation = cls.get_translation(obj, field_name, locale)
        if translation:
            return translation
        return getattr(obj, field_name, '')
    
    @classmethod
    def bulk_get_translations(cls, model_class, object_ids: list, locale: str) -> dict:
        """
        批量获取翻译 (用于列表页优化)
        
        Returns:
            {
                1: {"name": "Asset", "description": "..."},
                2: {"name": "Location", "description": "..."},
            }
        """
        pass
```

### 3.2 TranslatableMixin

```python
# apps/core/mixins.py

class TranslatableMixin:
    """
    为模型添加翻译能力的 Mixin
    
    使用方式:
        class BusinessObject(TranslatableMixin, models.Model):
            translatable_fields = ['name', 'description']
    """
    
    translatable_fields = ['name']  # 子类覆盖
    
    def get_translations(self, locale: str) -> dict:
        """获取该对象在指定语言下的所有翻译"""
        return TranslationService.get_translations(self, locale)
    
    def get_localized_name(self, locale: str) -> str:
        """获取本地化名称"""
        return TranslationService.get_localized_value(self, 'name', locale)
    
    def set_translations(self, locale: str, translations: dict, user=None):
        """设置翻译"""
        TranslationService.set_translations(self, locale, translations, user)
```

### 3.3 LocalizedSerializerMixin

```python
# apps/core/serializers.py

class LocalizedSerializerMixin:
    """
    Serializer Mixin - 自动处理本地化字段输出
    """
    
    localized_fields = ['name']  # 子类覆盖
    
    def get_locale(self) -> str:
        request = self.context.get('request')
        if request:
            # 优先从 Header 获取
            locale = request.headers.get('Accept-Language', '')
            if locale:
                return locale.split(',')[0].strip()
            # 其次从 Query 参数获取
            locale = request.query_params.get('locale', '')
            if locale:
                return locale
        return 'zh-CN'  # 默认中文
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        locale = self.get_locale()
        
        # 如果不是默认语言，尝试获取翻译
        if not locale.startswith('zh'):
            translations = TranslationService.get_translations(instance, locale)
            for field in self.localized_fields:
                if field in translations and translations[field]:
                    data[field] = translations[field]
        
        return data
```

---

## 4. API 设计

### 4.1 翻译管理 API

```
# 获取对象的所有翻译
GET /api/core/translations/{content_type}/{object_id}/

Response:
{
    "object": {"id": 1, "name": "资产"},
    "translations": {
        "en-US": {"name": "Asset", "description": "Fixed assets"},
        "ja-JP": {"name": "資産", "description": "固定資産"}
    }
}

# 设置/更新翻译
PUT /api/core/translations/{content_type}/{object_id}/

Request:
{
    "locale": "en-US",
    "translations": {
        "name": "Asset",
        "description": "Fixed assets management"
    }
}

# 批量翻译 (用于导入/AI翻译)
POST /api/core/translations/bulk/

Request:
{
    "content_type": "metadata.businessobject",
    "locale": "en-US",
    "items": [
        {"object_id": 1, "translations": {"name": "Asset"}},
        {"object_id": 2, "translations": {"name": "Location"}}
    ]
}

# 导出翻译 (用于离线翻译)
GET /api/core/translations/export/?content_type=metadata.businessobject&locale=en-US

Response: (CSV/Excel)
object_id,field_name,original_value,translation
1,name,资产,Asset
2,name,位置,Location

# 导入翻译
POST /api/core/translations/import/

Request: multipart/form-data (CSV/Excel file)
```

### 4.2 语言管理 API

```
# 获取可用语言列表
GET /api/core/languages/

Response:
{
    "items": [
        {"code": "zh-CN", "name": "简体中文", "nativeName": "中文", "isDefault": true},
        {"code": "en-US", "name": "英语", "nativeName": "English", "isDefault": false}
    ]
}

# 添加语言
POST /api/core/languages/

# 设置默认语言
PUT /api/core/languages/{code}/set-default/
```

### 4.3 业务 API 响应增强

所有返回可翻译内容的 API 将自动根据 `Accept-Language` 头返回对应语言：

```
# 请求
GET /api/metadata/business-objects/
Accept-Language: en-US

# 响应 (自动返回英文)
{
    "items": [
        {"id": 1, "code": "Asset", "name": "Asset", "description": "Fixed assets"},
        {"id": 2, "code": "Location", "name": "Location", "description": "Storage locations"}
    ]
}
```

---

## 5. 前端设计

### 5.1 翻译管理界面

#### 5.1.1 翻译列表页

- **路由**: `/admin/translations`
- **功能**:
  - 按内容类型筛选（业务对象、字段、字典等）
  - 按语言筛选
  - 搜索原文/译文
  - 显示翻译完成度统计
  - 批量导入/导出

#### 5.1.2 对象翻译弹窗

在业务对象、字段定义、字典项等编辑页面增加「多语言」按钮：

```vue
<template>
  <el-dialog title="多语言设置" v-model="visible">
    <el-tabs v-model="activeLocale">
      <el-tab-pane 
        v-for="lang in languages" 
        :key="lang.code" 
        :label="lang.nativeName"
        :name="lang.code"
      >
        <el-form>
          <el-form-item v-for="field in translatableFields" :key="field">
            <template #label>
              {{ field }} 
              <span class="original-value">原文: {{ originalValues[field] }}</span>
            </template>
            <el-input v-model="translations[lang.code][field]" />
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>
```

### 5.2 useLocalization Composable

```typescript
// composables/useLocalization.ts

export function useLocalization() {
  const localeStore = useLocaleStore()
  
  /**
   * 获取本地化值 - 用于从 API 响应中获取已翻译的值
   * API 响应应该已经根据 Accept-Language 返回了正确的语言
   */
  const getLocalizedValue = (item: any, field: string = 'name'): string => {
    return item?.[field] || ''
  }
  
  /**
   * 配置 Axios 请求头
   */
  const configureAxios = (axios: AxiosInstance) => {
    axios.interceptors.request.use(config => {
      config.headers['Accept-Language'] = localeStore.locale
      return config
    })
  }
  
  return { getLocalizedValue, configureAxios }
}
```

### 5.3 语言切换组件增强

```vue
<!-- components/LanguageSwitcher.vue -->
<template>
  <el-dropdown @command="handleChange">
    <span class="language-trigger">
      <el-icon><Globe /></el-icon>
      {{ currentLanguage?.nativeName }}
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item 
          v-for="lang in activeLanguages" 
          :key="lang.code"
          :command="lang.code"
          :class="{ active: lang.code === locale }"
        >
          {{ lang.nativeName }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
// 从 API 获取可用语言列表，而非硬编码
const { data: languages } = await languageApi.getList()
const activeLanguages = computed(() => languages.value?.filter(l => l.isActive))
</script>
```

---

## 6. 需要改造的模型

### 6.1 第一优先级（核心元数据）

| 模型 | 可翻译字段 | 影响范围 |
|------|-----------|---------|
| `BusinessObject` | name, description | 动态表单/列表标题 |
| `FieldDefinition` | label, placeholder, help_text | 表单字段标签 |
| `DictionaryType` | name, description | 字典分类 |
| `DictionaryItem` | display_name, description | 下拉选项文本 |

### 6.2 第二优先级（导航与组织）

| 模型 | 可翻译字段 | 影响范围 |
|------|-----------|---------|
| `Menu` | title | 侧边栏菜单 |
| `Department` | name | 组织架构 |
| `Role` | name, description | 角色管理 |

### 6.3 第三优先级（业务扩展）

| 模型 | 可翻译字段 | 影响范围 |
|------|-----------|---------|
| `AssetCategory` | name | 资产分类 |
| `Location` | name | 存放地点 |
| `WorkflowDefinition` | name, description | 流程名称 |

---

## 7. 数据迁移策略

### 7.1 初始化语言数据

```python
# 初始化两种语言
Language.objects.bulk_create([
    Language(code='zh-CN', name='简体中文', native_name='中文', is_default=True, sort_order=1),
    Language(code='en-US', name='英语', native_name='English', is_default=False, sort_order=2),
])
```

### 7.2 现有数据处理

1. **不自动生成翻译**：现有数据只有中文，不自动填充英文
2. **提供批量翻译工具**：管理员可导出待翻译内容，翻译后导入
3. **可选 AI 翻译**：集成翻译 API（如 DeepL、Google Translate）辅助翻译

### 7.3 向后兼容

- 无翻译时返回原语言值
- 前端静态 JSON 继续生效
- API 默认返回默认语言（中文）

---

## 8. 实施计划

### Phase 1: 基础设施（3天）

- [ ] 创建 Translation、Language 模型
- [ ] 实现 TranslationService
- [ ] 实现 TranslatableMixin
- [ ] 实现 LocalizedSerializerMixin
- [ ] 创建翻译管理 API

### Phase 2: 核心模型迁移（3天）

- [ ] BusinessObject 添加翻译支持
- [ ] FieldDefinition 添加翻译支持
- [ ] DictionaryType/Item 添加翻译支持
- [ ] 修改对应 Serializer

### Phase 3: 前端适配（2天）

- [ ] 配置 Axios Accept-Language 头
- [ ] 创建翻译管理界面
- [ ] 修改语言切换组件从 API 获取语言列表
- [ ] 动态组件使用 API 返回的本地化值

### Phase 4: 导航与扩展（2天）

- [ ] Menu 翻译支持
- [ ] Department 翻译支持
- [ ] 精简前端静态 JSON 文件

### Phase 5: 工具与优化（2天）

- [ ] 翻译导入/导出功能
- [ ] 翻译完成度统计
- [ ] 性能优化（缓存）
- [ ] AI 翻译集成（可选）

---

## 9. 技术考量

### 9.1 性能优化

1. **缓存策略**：
   - 使用 Django 缓存框架缓存常用翻译
   - 缓存 Key: `translation:{content_type}:{object_id}:{locale}`
   - 翻译更新时清除相关缓存

2. **批量查询优化**：
   - 列表页使用 `bulk_get_translations` 一次性获取所有翻译
   - 避免 N+1 查询问题

3. **前端缓存**：
   - 语言列表缓存到 localStorage
   - 常用翻译可缓存到内存

### 9.2 扩展性

1. **新增语言**：只需在 Language 表添加记录
2. **新增可翻译模型**：继承 TranslatableMixin，配置 translatable_fields
3. **新增可翻译字段**：更新 translatable_fields 列表

### 9.3 审计

- Translation 表记录 created_by, updated_by
- 可集成到系统审计日志
- 支持翻译变更历史查询

---

## 10. 验收标准

### 功能验收

- [ ] 可在管理界面为业务对象、字段、字典添加多语言翻译
- [ ] 切换语言后，动态内容（菜单、表单标签、字典选项）正确显示对应语言
- [ ] 无翻译时 graceful fallback 到默认语言
- [ ] 可批量导入/导出翻译

### 性能验收

- [ ] 列表页加载时间增加不超过 10%
- [ ] 翻译查询有缓存机制

### 兼容性验收

- [ ] 现有功能无回归
- [ ] 前端静态翻译继续正常工作

---

## 11. 现有代码整合

> **重要**：系统已存在 `apps/common/services/i18n_service.py`（502 行），包含 `TranslationCache`、`TranslationService`、`TranslatedFieldMixin`。本 PRD 需与现有代码整合，而非重新实现。

### 11.1 现有代码资产

| 类/函数 | 功能 | 整合策略 |
|--------|------|---------|
| `TranslationCache` | Redis 缓存管理 | ✅ 直接复用 |
| `TranslationService.get_text()` | namespace/key 翻译获取 | ✅ 直接复用 |
| `TranslationService.get_language_pack()` | 前端语言包生成 | ✅ 直接复用 |
| `TranslationService.translate_object()` | 模型实例翻译 | ⚠️ 需扩展支持 GenericForeignKey |
| `TranslationService.create_translation()` | 创建/更新翻译 | ⚠️ 需扩展支持动态对象 |
| `TranslatedFieldMixin` | Serializer Mixin | ⚠️ 需扩展支持 Translation 表查询 |
| `get_available_languages()` | 硬编码语言列表 | ❌ 改为从 Language 模型查询 |

### 11.2 整合方案

#### 11.2.1 扩展 TranslationService

```python
# 在现有 TranslationService 中添加以下方法

class TranslationService:
    # ... 保留现有方法 ...
    
    @staticmethod
    def get_object_translation(
        obj,
        field_name: str,
        lang_code: Optional[str] = None
    ) -> Optional[str]:
        """
        通过 GenericForeignKey 获取动态对象翻译
        
        Args:
            obj: 任意 Django 模型实例
            field_name: 字段名 (如 'name', 'label')
            lang_code: 语言代码
            
        Returns:
            翻译值，无翻译时返回 None
        """
        from django.contrib.contenttypes.models import ContentType
        from apps.system.models import Translation
        
        lang_code = lang_code or get_current_language()
        content_type = ContentType.objects.get_for_model(obj)
        
        translation = Translation.objects.filter(
            content_type=content_type,
            object_id=obj.pk,
            field_name=field_name,
            language_code=lang_code,
            is_deleted=False
        ).first()
        
        return translation.text if translation else None
    
    @staticmethod
    def get_localized_value(
        obj,
        field_name: str,
        lang_code: Optional[str] = None
    ) -> str:
        """
        获取本地化值（优先翻译，无翻译则返回原值）
        """
        translation = TranslationService.get_object_translation(obj, field_name, lang_code)
        if translation:
            return translation
        return getattr(obj, field_name, '') or ''
    
    @staticmethod
    def get_available_languages() -> List[Dict[str, Any]]:
        """
        从 Language 模型获取可用语言（替代硬编码）
        """
        try:
            from apps.system.models import Language
            return list(Language.objects.filter(is_active=True).order_by('sort_order').values(
                'code', 'name', 'native_name', 'flag_emoji', 'is_default'
            ))
        except Exception:
            # Fallback to hardcoded
            return [
                {'code': 'zh-CN', 'name': 'Chinese', 'native_name': '简体中文', 'is_default': True},
                {'code': 'en-US', 'name': 'English', 'native_name': 'English', 'is_default': False},
            ]
```

#### 11.2.2 扩展 LocalizedSerializerMixin

```python
# 继承现有 TranslatedFieldMixin 并扩展

class LocalizedSerializerMixin(TranslatedFieldMixin):
    """
    扩展的 Serializer Mixin，支持 Translation 表查询
    """
    
    localized_fields = ['name']  # 子类覆盖
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang_code = self.get_language_from_context()
        
        # 如果不是默认语言且有配置 localized_fields
        if lang_code != 'zh-CN' and hasattr(self, 'localized_fields'):
            for field in self.localized_fields:
                translated = TranslationService.get_object_translation(
                    instance, field, lang_code
                )
                if translated:
                    data[field] = translated
        
        return data
```

### 11.3 待修改文件清单

| 文件 | 修改内容 |
|------|---------|
| `apps/common/services/i18n_service.py` | 添加 `get_object_translation`, `get_localized_value`, 修改 `get_available_languages` |
| `apps/system/models.py` | 添加 `Language`, `Translation` 模型 |
| `apps/system/serializers/__init__.py` | 添加 `LocalizedSerializerMixin` |

---

## 12. 补充设计（审查发现）

> 以下为 PRD 审查中发现的遗漏项，需补充设计。

### 12.1 用户语言偏好

在 `User` 模型添加语言偏好字段：

```python
# apps/accounts/models.py

class User(AbstractUser):
    # ... 现有字段 ...
    preferred_language = models.CharField(
        max_length=10,
        default='zh-CN',
        verbose_name="首选语言",
        help_text="用户界面首选语言"
    )
```

**使用场景**：
- 用户登录后自动设置语言
- API 响应根据用户偏好返回对应语言
- 邮件/通知使用用户偏好语言

### 12.2 对象删除时翻译级联清理

使用 Django Signal 自动清理翻译：

```python
# apps/system/signals.py

from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from apps.system.models import Translation

@receiver(post_delete)
def cleanup_translations(sender, instance, **kwargs):
    """
    当对象被删除时，自动清理其关联的翻译
    """
    # 只处理有 translatable_fields 属性的模型
    if not hasattr(sender, 'translatable_fields'):
        return
    
    content_type = ContentType.objects.get_for_model(sender)
    Translation.objects.filter(
        content_type=content_type,
        object_id=instance.pk
    ).delete()
```

### 12.3 Translation 模型 unique_together 修正

修正 NULL 唯一性问题：

```python
class Translation(BaseModel):
    # ... 其他字段 ...
    
    class Meta:
        db_table = 'translations'
        # 使用条件唯一约束避免 NULL 问题
        constraints = [
            # namespace/key 模式约束
            models.UniqueConstraint(
                fields=['namespace', 'key', 'language_code'],
                condition=models.Q(namespace__isnull=False, key__isnull=False),
                name='unique_namespace_key_lang'
            ),
            # GenericForeignKey 模式约束
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'field_name', 'language_code'],
                condition=models.Q(content_type__isnull=False, object_id__isnull=False),
                name='unique_gfk_field_lang'
            ),
        ]
```

### 12.4 后端验证错误国际化

ValidationError 消息国际化支持：

```python
# apps/common/validators.py

from apps.common.services.i18n_service import TranslationService

def get_validation_message(key: str, **kwargs) -> str:
    """
    获取本地化的验证错误消息
    """
    message = TranslationService.get_text('validation', key)
    if kwargs:
        message = message.format(**kwargs)
    return message

# 使用示例
raise ValidationError(get_validation_message('required', field='资产名称'))
```

### 12.5 翻译导出格式规范

| 字段 | 类型 | 说明 |
|------|------|------|
| namespace | string | 命名空间 |
| key | string | 翻译键 |
| content_type | string | 模型类型 (可选) |
| object_id | int | 对象 ID (可选) |
| field_name | string | 字段名 (可选) |
| language_code | string | 语言代码 |
| original_text | string | 原文 (中文) |
| translated_text | string | 译文 |
| context | string | 上下文提示 |
| type | string | 类型: label/message/enum |

**导出文件格式**：UTF-8 BOM 编码的 CSV，或 XLSX

### 12.6 API 路径统一

**统一使用 `/api/system/translations/`**：

```
GET    /api/system/translations/           # 翻译列表
POST   /api/system/translations/           # 创建翻译
PUT    /api/system/translations/{id}/      # 更新翻译
DELETE /api/system/translations/{id}/      # 删除翻译
POST   /api/system/translations/bulk/      # 批量操作
GET    /api/system/translations/export/    # 导出
POST   /api/system/translations/import/    # 导入
GET    /api/system/translations/object/{content_type}/{object_id}/  # 对象翻译快捷接口

GET    /api/system/languages/              # 语言列表
POST   /api/system/languages/              # 添加语言
PATCH  /api/system/languages/{id}/set-default/  # 设置默认语言
```

### 12.7 修正后的时间估算

| 阶段 | 工作内容 | 时间 |
|------|---------|------|
| Phase 1 | 后端基础设施（整合现有代码） | 2 天 |
| Phase 2 | 核心模型迁移 + 数据迁移 | 2 天 |
| Phase 3 | 前端适配 + 翻译管理界面 | 2 天 |
| Phase 4 | 导航与扩展 | 1.5 天 |
| Phase 5 | 工具、优化、清理 | 2 天 |
| **总计** | | **9.5 天** |

---

## 附录 A: 现有翻译改善范围清单

> 本附录详细列出需要从静态 JSON 迁移到数据库驱动的所有内容，以及仍存在硬编码中文的 UI 组件。

---

### A.1 需迁移到 Translation 表的动态内容

#### A.1.1 业务对象 (BusinessObject)

系统预置业务对象清单，需在 Translation 表中添加英文翻译：

| 编码 | 中文名称 | 建议英文翻译 | 可翻译字段 |
|------|---------|-------------|-----------|
| Asset | 资产 | Asset | name, description |
| Location | 存放地点 | Location | name, description |
| AssetCategory | 资产分类 | Asset Category | name, description |
| Supplier | 供应商 | Supplier | name, description |
| Department | 部门 | Department | name, description |
| User | 用户 | User | name, description |
| InventoryTask | 盘点任务 | Inventory Task | name, description |
| MaintenanceRecord | 维护记录 | Maintenance Record | name, description |
| AssetPickup | 资产领用 | Asset Pickup | name, description |
| AssetReturn | 资产退库 | Asset Return | name, description |
| AssetLoan | 资产借出 | Asset Loan | name, description |
| AssetTransfer | 资产调拨 | Asset Transfer | name, description |
| Consumable | 耗材 | Consumable | name, description |
| WorkflowDefinition | 工作流定义 | Workflow Definition | name, description |
| SoftwareLicense | 软件许可证 | Software License | name, description |
| ITAsset | IT资产 | IT Asset | name, description |

#### A.1.2 字段定义 (FieldDefinition)

每个业务对象的字段标签需迁移，示例（资产对象字段）：

| 字段编码 | 中文标签 | 建议英文翻译 | 可翻译字段 |
|---------|---------|-------------|-----------|
| asset_name | 资产名称 | Asset Name | label, placeholder, help_text |
| asset_code | 资产编码 | Asset Code | label, placeholder |
| category | 资产分类 | Category | label, placeholder |
| location | 存放地点 | Location | label, placeholder |
| status | 状态 | Status | label |
| purchase_date | 购买日期 | Purchase Date | label |
| purchase_price | 购买价格 | Purchase Price | label |
| warranty_date | 保修截止日期 | Warranty End Date | label |
| responsible_person | 责任人 | Responsible Person | label |
| department | 所属部门 | Department | label |
| serial_number | 序列号 | Serial Number | label |
| model | 型号 | Model | label |
| brand | 品牌 | Brand | label |
| description | 描述 | Description | label, placeholder |
| images | 图片 | Images | label |
| attachments | 附件 | Attachments | label |

> **注**：系统中约有 **150+ 字段定义**，需逐一添加翻译。建议使用批量导入功能。

#### A.1.3 字典类型 (DictionaryType)

| 字典编码 | 中文名称 | 建议英文翻译 |
|---------|---------|-------------|
| ASSET_STATUS | 资产状态 | Asset Status |
| ASSET_TYPE | 资产类型 | Asset Type |
| MAINTENANCE_TYPE | 维护类型 | Maintenance Type |
| WORKFLOW_STATUS | 工作流状态 | Workflow Status |
| APPROVAL_STATUS | 审批状态 | Approval Status |
| LOAN_STATUS | 借出状态 | Loan Status |
| RETURN_STATUS | 退库状态 | Return Status |
| PICKUP_STATUS | 领用状态 | Pickup Status |
| INVENTORY_RESULT | 盘点结果 | Inventory Result |
| DEPRECIATION_METHOD | 折旧方法 | Depreciation Method |
| CONSUMABLE_TYPE | 耗材类型 | Consumable Type |
| PRIORITY | 优先级 | Priority |
| SEVERITY | 严重程度 | Severity |

#### A.1.4 字典项 (DictionaryItem)

示例（资产状态字典项）：

| 字典类型 | 项编码 | 中文显示 | 建议英文翻译 |
|---------|-------|---------|-------------|
| ASSET_STATUS | idle | 空闲 | Idle |
| ASSET_STATUS | in_use | 在用 | In Use |
| ASSET_STATUS | maintenance | 维修中 | Under Maintenance |
| ASSET_STATUS | borrowed | 借出 | On Loan |
| ASSET_STATUS | disposed | 已报废 | Disposed |
| ASSET_STATUS | lost | 丢失 | Lost |
| ASSET_STATUS | pending_pickup | 待领用 | Pending Pickup |
| ASSET_STATUS | pending_return | 待退库 | Pending Return |

> **注**：系统中约有 **100+ 字典项**，需逐一添加翻译。

#### A.1.5 菜单项 (Menu)

后端菜单配置需迁移：

| 菜单编码 | 中文标题 | 建议英文翻译 | 父级菜单 |
|---------|---------|-------------|---------|
| dashboard | 工作台 | Dashboard | - |
| assets | 资产管理 | Asset Management | - |
| asset_list | 资产卡片 | Asset List | assets |
| asset_category | 资产分类 | Asset Categories | assets |
| location | 存放地点 | Locations | assets |
| supplier | 供应商 | Suppliers | assets |
| asset_status_log | 资产状态日志 | Asset Status Logs | assets |
| consumables | 耗材管理 | Consumables | - |
| inventory | 盘点管理 | Inventory | - |
| workflow | 工作流 | Workflow | - |
| workflow_definitions | 工作流定义 | Workflow Definitions | workflow |
| workflow_instances | 工作流实例 | Workflow Instances | workflow |
| system | 系统管理 | System | - |
| business_objects | 业务对象管理 | Business Objects | system |
| field_definitions | 字段定义管理 | Field Definitions | system |
| page_layouts | 页面布局管理 | Page Layouts | system |
| dictionary_types | 数据字典管理 | Dictionary Types | system |
| sequence_rules | 编号规则管理 | Sequence Rules | system |
| system_config | 系统配置管理 | System Config | system |
| it_assets | IT资产管理 | IT Asset Management | - |
| software_licenses | 软件许可证 | Software Licenses | - |

#### A.1.6 部门/组织 (Department)

用户自定义部门需支持多语言：

| 示例部门 | 中文名称 | 建议英文翻译 |
|---------|---------|-------------|
| headquarters | 总公司 | Headquarters |
| tech_dept | 技术部 | Technology Department |
| hr_dept | 人力资源部 | HR Department |
| finance_dept | 财务部 | Finance Department |
| sales_dept | 销售部 | Sales Department |

> **注**：部门数据由用户创建，需在部门管理界面提供多语言输入。

---

### A.2 前端静态 JSON 保留范围

以下内容继续使用前端静态 JSON 翻译：

#### A.2.1 通用 UI 文本 (common.json)

| 分类 | 示例 Key | 中文 | 英文 |
|-----|---------|------|------|
| 按钮 | common.actions.save | 保存 | Save |
| 按钮 | common.actions.cancel | 取消 | Cancel |
| 按钮 | common.actions.delete | 删除 | Delete |
| 按钮 | common.actions.edit | 编辑 | Edit |
| 按钮 | common.actions.create | 新建 | Create |
| 按钮 | common.actions.search | 搜索 | Search |
| 按钮 | common.actions.export | 导出 | Export |
| 按钮 | common.actions.import | 导入 | Import |
| 状态 | common.status.loading | 加载中... | Loading... |
| 状态 | common.status.success | 操作成功 | Success |
| 状态 | common.status.error | 操作失败 | Failed |
| 状态 | common.status.enabled | 启用 | Enabled |
| 状态 | common.status.disabled | 禁用 | Disabled |
| 提示 | common.messages.confirmDelete | 确定删除吗？ | Confirm delete? |
| 提示 | common.messages.saveSuccess | 保存成功 | Saved successfully |
| 表单 | common.validation.required | 此字段必填 | This field is required |
| 表格 | common.table.noData | 暂无数据 | No data |
| 分页 | common.pagination.total | 共 {total} 条 | Total {total} items |

#### A.2.2 登录页 (login.json)

| Key | 中文 | 英文 |
|-----|------|------|
| login.title | 系统登录 | System Login |
| login.username | 用户名 | Username |
| login.password | 密码 | Password |
| login.rememberMe | 记住我 | Remember me |
| login.submit | 登录 | Login |
| login.forgotPassword | 忘记密码 | Forgot password |

#### A.2.3 表单验证 (form.json)

| Key | 中文 | 英文 |
|-----|------|------|
| form.validation.required | 请输入{field} | Please enter {field} |
| form.validation.email | 请输入有效的邮箱 | Please enter valid email |
| form.validation.phone | 请输入有效的手机号 | Please enter valid phone |
| form.validation.minLength | 最少{min}个字符 | Minimum {min} characters |
| form.validation.maxLength | 最多{max}个字符 | Maximum {max} characters |

---

### A.3 仍存在硬编码中文的 Vue 组件

> 以下组件仍有硬编码中文文本，需在 Phase 5 全面清理：

#### A.3.1 系统管理模块 (views/system/)

| 文件 | 硬编码内容 | 处理方式 |
|------|-----------|---------|
| `DepartmentList.vue` | '总公司', '技术部' 等 mock 数据 | 删除 mock 数据或使用 $t() |
| `DictionaryItemForm.vue` | 图标选择标签如 'Check (勾选)' | 改用静态 JSON 翻译 |
| `BusinessRuleList.vue` | '暂无规则' 回退文本 | 使用 $t() 替代 |

#### A.3.2 软件许可证模块 (views/softwareLicenses/)

| 文件 | 硬编码内容 | 处理方式 |
|------|-----------|---------|
| `SoftwareLicenseList.vue` | '操作', '批量删除' 回退文本 | 确保 $t() 有对应 key |
| `SoftwareForm.vue` | '加载失败' 回退文本 | 确保 $t() 有对应 key |
| `SoftwareCatalog.vue` | '操作', '批量删除' 回退文本 | 确保 $t() 有对应 key |
| `AllocationList.vue` | '确认', '确定', '取消' 回退文本 | 确保 $t() 有对应 key |

#### A.3.3 移动端模块 (views/mobile/)

| 文件 | 硬编码内容 | 处理方式 |
|------|-----------|---------|
| `UnifiedScan.vue` | '扫码', '返回' | 使用 $t() |

#### A.3.4 资产操作模块 (views/assets/operations/)

| 文件 | 状态 | 说明 |
|------|-----|------|
| `LoanList.vue` | ✅ 大部分已国际化 | 部分 $t() 已添加 |
| `ReturnList.vue` | ✅ 大部分已国际化 | 部分 $t() 已添加 |
| `PickupList.vue` | 待检查 | 需验证国际化完整性 |
| `TransferList.vue` | 待检查 | 需验证国际化完整性 |

---

### A.4 静态 JSON 缺失 Key 清单

以下 Key 在代码中使用但 JSON 文件中缺失或不完整：

#### A.4.1 common.json 缺失

```
common.actions.batchDelete
common.labels.operation
common.messages.confirmTitle
common.messages.cancelSuccess
```

#### A.4.2 assets.json 缺失

```
assets.loan.messages.confirmCancel
assets.loan.messages.returnSuccess
assets.loan.messages.returnFailed
assets.return.messages.confirmApprove
assets.return.messages.approveSuccess
assets.return.messages.confirmReject
assets.return.messages.rejectReasonRequired
assets.return.messages.rejectSuccess
assets.return.listTitle
assets.return.createButton
assets.search.keywordPlaceholder
```

#### A.4.3 menu.json 需要补充

```
menu.routes.integrationConfigs
menu.routes.softwareCreate
menu.routes.softwareEdit
menu.routes.softwareLicenseCreate
menu.routes.softwareLicenseEdit
menu.routes.allocationCreate
```

---

### A.5 翻译工作量估算

| 分类 | 数量 | 工作量 |
|------|-----|-------|
| 业务对象名称 | ~20 个 | 0.5 天 |
| 字段定义标签 | ~150 个 | 2 天 |
| 字典类型 | ~15 个 | 0.5 天 |
| 字典项 | ~100 个 | 1 天 |
| 菜单项 | ~40 个 | 0.5 天 |
| 静态 JSON 补全 | ~50 个 key | 0.5 天 |
| 硬编码中文清理 | ~30 个组件 | 2 天 |
| **总计** | | **7 天** |

---

### A.6 实施优先级

#### 高优先级（用户可见，影响体验）

1. ✅ 菜单项翻译 - 用户每次使用都会看到
2. ✅ 业务对象名称 - 动态表单/列表标题
3. ✅ 字典项翻译 - 下拉选项、状态显示

#### 中优先级（管理员可见）

4. 字段定义标签 - 动态表单字段标签
5. 字典类型名称 - 字典管理界面
6. 部门名称 - 组织架构

#### 低优先级（内部使用）

7. 静态 JSON 补全
8. 硬编码中文清理
9. 错误消息国际化
