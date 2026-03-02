# 企业级 i18n 架构实施计划

## 文档信息
| 项目 | 说明 |
|------|------|
| 计划版本 | v1.0 |
| 创建日期 | 2026-02-08 |
| 作者 | Claude (Architect Agent) |
| PRD 参考 | `docs/prd/enterprise_i18n_architecture.md` |

---

## 一、架构决策

### 1.1 混合 Translation 模型

采用**混合模式**设计，同时支持：
- **namespace/key 索引**：适用于静态内容（系统标签、按钮、提示）
- **GenericForeignKey 索引**：适用于动态对象（用户创建的部门、分类等）

**优势**：
- 统一存储和管理所有翻译
- 支持批量导入导出
- 性能优化的双重索引
- 完整的审计追踪

### 1.2 数据库驱动的 Language 模型

创建 Language 表支持动态语言扩展，而非硬编码。

### 1.3 兼容现有服务层

保持 `i18n_service.py` 接口不变，仅补全缺失的 Translation 模型。

---

## 二、实施阶段

### Phase 1: 后端基础设施 (预计 2 天)

> **重要**：复用现有 `apps/common/services/i18n_service.py` 代码

#### 1.1 创建核心模型

**文件**: `backend/apps/system/models.py`

```python
# Language 模型
class Language(BaseModel):
    code = models.CharField(max_length=10, unique=True)  # zh-CN, en-US
    name = models.CharField(max_length=50)                # 简体中文
    native_name = models.CharField(max_length=50)         # 中文
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    flag_emoji = models.CharField(max_length=10, blank=True)  # 🇨🇳, 🇺🇸

# Translation 模型 (混合模式)
class Translation(BaseModel):
    # Namespace/Key 模式 (静态内容)
    namespace = models.CharField(max_length=50, db_index=True, blank=True, default='')
    key = models.CharField(max_length=200, db_index=True, blank=True, default='')

    # GenericForeignKey 模式 (动态对象)
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    field_name = models.CharField(max_length=50, blank=True, default='')

    # 翻译内容
    language_code = models.CharField(max_length=10, db_index=True)
    text = models.TextField()

    # 元数据
    context = models.CharField(max_length=200, blank=True)
    type = models.CharField(max_length=20, default='label')
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'translations'
        # 使用条件唯一约束避免 NULL 问题
        constraints = [
            models.UniqueConstraint(
                fields=['namespace', 'key', 'language_code'],
                condition=models.Q(namespace__gt='', key__gt=''),
                name='unique_namespace_key_lang'
            ),
            models.UniqueConstraint(
                fields=['content_type', 'object_id', 'field_name', 'language_code'],
                condition=models.Q(content_type__isnull=False, object_id__isnull=False),
                name='unique_gfk_field_lang'
            ),
        ]
        indexes = [
            models.Index(fields=['namespace', 'key', 'language_code']),
            models.Index(fields=['content_type', 'object_id', 'language_code']),
        ]
```

#### 1.2 扩展现有 TranslationService

**文件**: `backend/apps/common/services/i18n_service.py`

在现有 `TranslationService` 类中添加：

```python
@staticmethod
def get_object_translation(obj, field_name: str, lang_code: Optional[str] = None) -> Optional[str]:
    """通过 GenericForeignKey 获取动态对象翻译"""
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
def get_localized_value(obj, field_name: str, lang_code: Optional[str] = None) -> str:
    """获取本地化值（优先翻译，无翻译则返回原值）"""
    translation = TranslationService.get_object_translation(obj, field_name, lang_code)
    return translation if translation else (getattr(obj, field_name, '') or '')
```

#### 1.3 创建 API 视图

**文件**: `backend/apps/system/viewsets/translation.py`

```python
class TranslationViewSet(BaseModelViewSetWithBatch):
    """翻译管理 API"""
    queryset = Translation.objects.all()
    serializer_class = TranslationSerializer
    filterset_class = TranslationFilter

    def get_locale(self):
        """从请求头获取语言代码"""
        request = self.context.get('request')
        if request:
            # 优先 Accept-Language header
            locale = request.headers.get('Accept-Language', '')
            if locale:
                return locale.split(',')[0].strip()
            # 其次 query 参数
            locale = request.query_params.get('locale', '')
            if locale:
                return locale
        return 'zh-CN'
```

#### 1.3 配置 URL

**文件**: `backend/apps/system/urls.py`

```python
router.register(r'translations', TranslationViewSet, basename='translation')
router.register(r'languages', LanguageViewSet, basename='language')
```

---

### Phase 2: 核心模型迁移 (预计 1 天)

#### 2.1 迁移策略

现有模型已有 `name_en` 字段，需要：
1. 将现有 `name_en` 数据迁移到 Translation 表
2. 保留 `name_en` 作为缓存/回退字段

#### 2.2 数据迁移脚本

```python
# backend/apps/system/migrations/0020_migrate_existing_translations.py
def migrate_existing_translations(apps, schema_editor):
    """将现有 name_en 字段迁移到 Translation 表"""
    Translation = apps.get_model('system', 'Translation')
    BusinessObject = apps.get_model('system', 'BusinessObject')
    DictionaryType = apps.get_model('system', 'DictionaryType')
    DictionaryItem = apps.get_model('system', 'DictionaryItem')

    # 迁移 BusinessObject
    for obj in BusinessObject.objects.filter(name_en__gt=''):
        Translation.objects.create(
            namespace='business_object',
            key=f'{obj.code}.name',
            language_code='en-US',
            text=obj.name_en,
            content_type=...,  # BusinessObject content type
            object_id=obj.id,
            field_name='name'
        )
```

---

### Phase 3: 前端适配 (预计 1 天)

#### 3.1 Axios 拦截器配置

**文件**: `frontend/src/utils/request.ts`

```typescript
// 在现有 axios 实例中添加 Accept-Language 头
axios.interceptors.request.use(config => {
  const localeStore = useLocaleStore()
  config.headers['Accept-Language'] = localeStore.locale
  return config
})
```

#### 3.2 翻译管理界面

**文件**: `frontend/src/views/system/TranslationList.vue`

- 翻译列表（按 namespace/key/语言筛选）
- 对象翻译弹窗（与业务对象、字段定义等集成）
- 批量导入导出功能

---

### Phase 4: 初始化数据 (预计 1 天)

#### 4.1 语言初始化

```python
Language.objects.bulk_create([
    Language(code='zh-CN', name='简体中文', native_name='中文',
             is_default=True, sort_order=1, flag_emoji='🇨🇳'),
    Language(code='en-US', name='English', native_name='English',
             is_default=False, sort_order=2, flag_emoji='🇺🇸'),
])
```

#### 4.2 核心翻译数据

按 PRD 附录 A.1 初始化：
- 业务对象名称 (~20 个)
- 字段定义标签 (~150 个)
- 字典类型/项 (~115 个)

---

## 三、文件清单

### 新增文件

| 文件路径 | 说明 |
|---------|------|
| `backend/apps/system/models.py` | 添加 Language, Translation 模型 |
| `backend/apps/system/serializers/translation.py` | Translation, Language 序列化器 |
| `backend/apps/system/viewsets/translation.py` | Translation, Language 视图 |
| `backend/apps/system/filters/translation.py` | Translation 过滤器 |
| `backend/apps/system/migrations/0020_add_i18n_models.py` | 数据库迁移 |
| `backend/apps/system/migrations/0021_migrate_existing_translations.py` | 数据迁移 |
| `frontend/src/api/translations.ts` | 翻译 API 客户端 |
| `frontend/src/views/system/TranslationList.vue` | 翻译管理页面 |
| `frontend/src/components/common/TranslationDialog.vue` | 翻译编辑弹窗 |
| `frontend/src/locales/init_translations.py` | 翻译初始化脚本 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `backend/apps/system/urls.py` | 添加翻译 API 路由 |
| `backend/apps/system/serializers/__init__.py` | 导出 TranslationSerializer |
| `backend/apps/system/viewsets/__init__.py` | 导出 TranslationViewSet |
| `frontend/src/utils/request.ts` | 添加 Accept-Language 头 |
| `frontend/src/router/index.ts` | 添加翻译管理路由 |
| `frontend/src/locales/zh-CN/system.json` | 添加翻译管理相关文本 |

---

## 四、API 设计

### 4.1 语言管理

```
GET    /api/system/languages/           # 获取语言列表
POST   /api/system/languages/           # 添加语言
PUT    /api/system/languages/{id}/      # 更新语言
PATCH  /api/system/languages/{id}/set-default/  # 设置默认语言
```

### 4.2 翻译管理

```
GET    /api/system/translations/        # 获取翻译列表
POST   /api/system/translations/        # 创建翻译
PUT    /api/system/translations/{id}/   # 更新翻译
DELETE /api/system/translations/{id}/   # 删除翻译
POST   /api/system/translations/bulk/   # 批量创建/更新
GET    /api/system/translations/export/ # 导出翻译 (CSV/Excel)
POST   /api/system/translations/import/ # 导入翻译
```

### 4.3 对象翻译快捷接口

```
GET    /api/system/translations/object/{content_type}/{object_id}/
PUT    /api/system/translations/object/{content_type}/{object_id}/
```

---

## 五、响应格式

### 5.1 语言列表响应

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "code": "zh-CN",
      "name": "简体中文",
      "nativeName": "中文",
      "isDefault": true,
      "isActive": true,
      "sortOrder": 1,
      "flagEmoji": "🇨🇳"
    }
  ]
}
```

### 5.2 翻译列表响应

```json
{
  "success": true,
  "data": {
    "count": 100,
    "results": [
      {
        "id": "uuid",
        "namespace": "asset",
        "key": "status.idle",
        "languageCode": "en-US",
        "text": "Idle",
        "context": "Asset status",
        "type": "enum",
        "contentType": null,
        "objectId": null,
        "fieldName": ""
      }
    ]
  }
}
```

---

## 六、验收标准

### 功能验收

- [ ] 可在管理界面为任意对象添加多语言翻译
- [ ] 切换语言后，API 返回对应语言内容
- [ ] 无翻译时 graceful fallback 到默认语言
- [ ] 可批量导入/导出翻译
- [ ] 翻译变更可追溯（created_by, updated_by）
- [ ] 用户语言偏好保存并自动应用

### 性能验收

- [ ] 列表页加载时间增加不超过 10%
- [ ] 翻译查询有缓存机制（Redis）
- [ ] 支持 N+1 查询优化（bulk_get_translations）

### 兼容性验收

- [ ] 现有 `name_en` 字段继续工作
- [ ] 前端静态 JSON 继续生效
- [ ] 不影响现有功能
- [ ] 对象删除时翻译自动清理

---

## 七、补充设计（审查发现）

### 7.1 用户语言偏好

在 `User` 模型添加：

```python
# apps/accounts/models.py
class User(AbstractUser):
    preferred_language = models.CharField(max_length=10, default='zh-CN')
```

### 7.2 对象删除时翻译级联清理

```python
# apps/system/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from apps.system.models import Translation

@receiver(post_delete)
def cleanup_translations(sender, instance, **kwargs):
    if not hasattr(sender, 'translatable_fields'):
        return
    content_type = ContentType.objects.get_for_model(sender)
    Translation.objects.filter(
        content_type=content_type,
        object_id=instance.pk
    ).delete()
```

### 7.3 翻译导出格式

| 字段 | 说明 |
|------|------|
| namespace | 命名空间 |
| key | 翻译键 |
| content_type | 模型类型 (可选) |
| object_id | 对象 ID (可选) |
| field_name | 字段名 (可选) |
| language_code | 语言代码 |
| original_text | 原文 |
| translated_text | 译文 |

**格式**：UTF-8 BOM CSV 或 XLSX

---

## 八、后续优化

1. **AI 翻译集成**：对接 DeepL/Google Translate API
2. **翻译记忆库**：记录专业术语翻译，保持一致性
3. **协作翻译**：多人翻译时的冲突解决机制
4. **翻译覆盖率报告**：可视化展示翻译完成度
5. **RTL 语言支持**：阿拉伯语/希伯来语布局支持
6. **翻译版本控制**：支持回滚到历史版本
