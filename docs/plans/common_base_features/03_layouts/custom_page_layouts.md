# 自定义页面布局完整规范

## 概述

自定义页面布局是 GZEAMS 低代码平台的高级功能，允许管理员和用户基于默认布局进行个性化定制。通过继承、覆盖和扩展机制，实现不同层级（用户级、角色级、组织级、全局级）的布局自定义，满足多样化的业务需求和使用偏好。

自定义布局遵循以下核心原则：

1. **非破坏性**：自定义布局不会修改默认布局，始终保持原始配置的完整性
2. **优先级明确**：按照用户级 > 角色级 > 组织级 > 全局级的优先级自动选择最合适的布局
3. **增量配置**：仅存储与默认布局的差异部分，减少数据冗余
4. **灵活继承**：支持基于任意布局创建自定义版本，实现布局复用和演化

---

## 1. 自定义布局类型与优先级

### 1.0 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 1.1 自定义布局层级

```python
from django.db import models
from apps.common.models import BaseModel

class UserLayoutPreference(BaseModel):
    """
    用户布局偏好模型

    存储用户/角色/组织/全局级别的自定义布局配置
    """
    SCOPE_CHOICES = [
        ('user', '用户级'),
        ('role', '角色级'),
        ('org', '组织级'),
        ('global', '全局级'),
    ]

    # 布局范围
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        verbose_name='布局范围',
        help_text='自定义布局的作用域'
    )

    # 关联用户（用户级布局）
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_layouts',
        verbose_name='用户',
        help_text='用户级布局时必填'
    )

    # 关联角色（角色级布局）
    role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_layouts',
        verbose_name='角色',
        help_text='角色级布局时必填'
    )

    # 关联组织（组织级布局）
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_layouts',
        verbose_name='组织',
        help_text='组织级布局时必填'
    )

    # 基础布局
    base_layout = models.ForeignKey(
        'system.PageLayout',
        on_delete=models.CASCADE,
        related_name='custom_layouts',
        verbose_name='基础布局',
        help_text='继承的默认布局或其他布局'
    )

    # 自定义配置（JSON）
    custom_config = models.JSONField(
        default=dict,
        verbose_name='自定义配置',
        help_text='与基础布局的差异配置'
    )

    # 布局元数据
    name = models.CharField(
        max_length=100,
        verbose_name='布局名称',
        help_text='自定义布局的显示名称'
    )

    description = models.TextField(
        blank=True,
        verbose_name='布局描述'
    )

    # 布局状态
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    # 排序权重
    priority = models.IntegerField(
        default=0,
        verbose_name='优先级',
        help_text='同一作用域内的优先级，数值越大优先级越高'
    )

    # 分享信息
    is_shared = models.BooleanField(
        default=False,
        verbose_name='是否分享',
        help_text='是否分享给其他用户'
    )

    shared_with = models.ManyToManyField(
        'accounts.User',
        blank=True,
        related_name='shared_layouts',
        verbose_name='分享给',
        help_text='分享给哪些用户'
    )

    class Meta:
        db_table = 'system_user_layout_preference'
        verbose_name = '用户布局偏好'
        verbose_name_plural = '用户布局偏好'
        unique_together = [
            ['scope', 'base_layout', 'user'],
            ['scope', 'base_layout', 'role'],
            ['scope', 'base_layout', 'organization']
        ]
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['scope', 'is_active']),
            models.Index(fields=['user', 'base_layout']),
            models.Index(fields=['role', 'base_layout']),
            models.Index(fields=['organization', 'base_layout']),
        ]

    def __str__(self):
        scope_display = self.get_scope_display()
        if self.scope == 'user':
            return f"{self.user.username} - {self.base_layout.name}"
        elif self.scope == 'role':
            return f"{self.role.name} - {self.base_layout.name}"
        elif self.scope == 'org':
            return f"{self.organization.name} - {self.base_layout.name}"
        else:
            return f"全局 - {self.base_layout.name}"

    def get_merged_config(self):
        """获取合并后的完整配置"""
        base_config = self.base_layout.layout_config.copy()
        self._merge_config(base_config, self.custom_config)
        return base_config

    def _merge_config(self, base, custom):
        """递归合并配置"""
        for key, value in custom.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
```

### 1.2 布局优先级规则

```python
class LayoutSelector:
    """
    布局选择器

    根据当前上下文（用户、角色、组织）自动选择最合适的布局
    """

    # 优先级顺序（从高到低）
    PRIORITY_ORDER = ['user', 'role', 'org', 'global']

    @staticmethod
    def select_layout(user, business_object, layout_type):
        """
        选择最合适的布局

        优先级：用户级 > 角色级 > 组织级 > 全局级 > 默认布局
        """
        from .models import UserLayoutPreference, PageLayout

        # 1. 查找用户级自定义布局
        user_layout = UserLayoutPreference.objects.filter(
            scope='user',
            user=user,
            base_layout__business_object=business_object,
            base_layout__layout_type=layout_type,
            is_active=True
        ).order_by('-priority').first()

        if user_layout:
            return user_layout

        # 2. 查找角色级自定义布局
        user_roles = user.roles.all()
        role_layout = UserLayoutPreference.objects.filter(
            scope='role',
            role__in=user_roles,
            base_layout__business_object=business_object,
            base_layout__layout_type=layout_type,
            is_active=True
        ).order_by('-priority').first()

        if role_layout:
            return role_layout

        # 3. 查找组织级自定义布局
        org_layout = UserLayoutPreference.objects.filter(
            scope='org',
            organization=user.organization,
            base_layout__business_object=business_object,
            base_layout__layout_type=layout_type,
            is_active=True
        ).order_by('-priority').first()

        if org_layout:
            return org_layout

        # 4. 查找全局级自定义布局
        global_layout = UserLayoutPreference.objects.filter(
            scope='global',
            base_layout__business_object=business_object,
            base_layout__layout_type=layout_type,
            is_active=True
        ).order_by('-priority').first()

        if global_layout:
            return global_layout

        # 5. 返回默认布局
        try:
            return PageLayout.objects.get(
                business_object=business_object,
                layout_type=layout_type,
                is_default=True,
                is_published=True
            )
        except PageLayout.DoesNotExist:
            return None
```

---

## 2. 自定义布局继承机制

### 2.1 继承规则

自定义布局支持基于任意布局（默认布局或其他自定义布局）创建新的自定义版本：

```python
class LayoutInheritanceManager:
    """布局继承管理器"""

    @staticmethod
    def create_custom_layout(base_layout, scope, custom_config, **kwargs):
        """
        创建自定义布局

        Args:
            base_layout: 基础布局（PageLayout实例）
            scope: 作用域（'user', 'role', 'org', 'global'）
            custom_config: 自定义配置（仅包含与基础布局的差异）
            **kwargs: 其他参数（user, role, organization, name, description等）
        """
        from .models import UserLayoutPreference

        # 验证作用域对应的参数
        if scope == 'user' and 'user' not in kwargs:
            raise ValueError("用户级布局必须指定user参数")
        if scope == 'role' and 'role' not in kwargs:
            raise ValueError("角色级布局必须指定role参数")
        if scope == 'org' and 'organization' not in kwargs:
            raise ValueError("组织级布局必须指定organization参数")

        # 创建自定义布局
        custom_layout = UserLayoutPreference.objects.create(
            base_layout=base_layout,
            scope=scope,
            custom_config=custom_config,
            **kwargs
        )

        return custom_layout

    @staticmethod
    def get_inheritance_chain(layout):
        """
        获取布局继承链

        返回从默认布局到当前布局的完整继承路径
        """
        chain = []
        current = layout

        while current:
            chain.append(current)
            if isinstance(current, UserLayoutPreference):
                current = current.base_layout
            else:
                break

        return list(reversed(chain))
```

### 2.2 配置合并策略

```python
class ConfigMerger:
    """配置合并器"""

    @staticmethod
    def merge(base_config, custom_config):
        """
        递归合并配置

        策略：
        1. 基础类型字段：直接覆盖
        2. 列表字段：根据key字段合并（支持新增、修改、删除）
        3. 字典字段：递归合并
        """
        result = base_config.copy()

        for key, custom_value in custom_config.items():
            if key not in result:
                # 新增字段
                result[key] = custom_value
            elif isinstance(result[key], dict) and isinstance(custom_value, dict):
                # 字典字段：递归合并
                result[key] = ConfigMerger.merge(result[key], custom_value)
            elif isinstance(result[key], list) and isinstance(custom_value, list):
                # 列表字段：智能合并
                result[key] = ConfigMerger._merge_list(result[key], custom_value)
            else:
                # 基础类型：直接覆盖
                result[key] = custom_value

        return result

    @staticmethod
    def _merge_list(base_list, custom_list):
        """
        合并列表

        支持以下操作：
        1. 修改：根据id或key字段匹配并更新
        2. 新增：没有匹配项时添加到列表
        3. 删除：标记为_deleted的项会被移除
        """
        result = []
        base_dict = {}

        # 构建基础列表字典（根据id或key字段）
        for item in base_list:
            item_key = item.get('id') or item.get('key') or item.get('field')
            if item_key:
                base_dict[item_key] = item
            else:
                result.append(item)

        # 处理自定义列表
        for custom_item in custom_list:
            item_key = custom_item.get('id') or custom_item.get('key') or custom_item.get('field')

            if item_key in base_dict:
                # 修改现有项
                if custom_item.get('_deleted'):
                    # 标记为删除，不添加到结果
                    continue
                else:
                    # 合并更新
                    merged_item = base_dict[item_key].copy()
                    merged_item.update(custom_item)
                    result.append(merged_item)
                    del base_dict[item_key]
            else:
                # 新增项
                if not custom_item.get('_deleted'):
                    result.append(custom_item)

        # 添加未被修改的基础项
        result.extend(base_dict.values())

        return result
```

### 2.3 配置差异计算

```python
class ConfigDiffCalculator:
    """配置差异计算器"""

    @staticmethod
    def calculate_diff(base_config, custom_config):
        """
        计算配置差异

        返回仅包含差异部分的配置（用于存储到custom_config字段）
        """
        diff = {}
        all_keys = set(base_config.keys()) | set(custom_config.keys())

        for key in all_keys:
            base_value = base_config.get(key)
            custom_value = custom_config.get(key)

            if custom_value is None:
                # 字段被删除（标记为_deleted）
                diff[key] = {'_deleted': True}
            elif base_value is None:
                # 新增字段
                diff[key] = custom_value
            elif isinstance(base_value, dict) and isinstance(custom_value, dict):
                # 字典字段：递归计算差异
                nested_diff = ConfigDiffCalculator.calculate_diff(base_value, custom_value)
                if nested_diff:
                    diff[key] = nested_diff
            elif isinstance(base_value, list) and isinstance(custom_value, list):
                # 列表字段：计算列表差异
                list_diff = ConfigDiffCalculator._calculate_list_diff(base_value, custom_value)
                if list_diff:
                    diff[key] = list_diff
            elif base_value != custom_value:
                # 基础类型：值不同
                diff[key] = custom_value

        return diff

    @staticmethod
    def _calculate_list_diff(base_list, custom_list):
        """
        计算列表差异

        返回包含新增、修改、删除标记的列表
        """
        diff = []
        base_dict = {}

        # 构建基础列表字典
        for item in base_list:
            item_key = item.get('id') or item.get('key') or item.get('field')
            if item_key:
                base_dict[item_key] = item

        # 处理自定义列表
        for custom_item in custom_list:
            item_key = custom_item.get('id') or custom_item.get('key') or custom_item.get('field')

            if item_key in base_dict:
                base_item = base_dict[item_key]
                if base_item != custom_item:
                    # 修改项：仅包含差异字段
                    item_diff = {'id': item_key}
                    for field_key in set(base_item.keys()) | set(custom_item.keys()):
                        base_field_value = base_item.get(field_key)
                        custom_field_value = custom_item.get(field_key)
                        if base_field_value != custom_field_value:
                            item_diff[field_key] = custom_field_value
                    diff.append(item_diff)
                del base_dict[item_key]
            else:
                # 新增项
                diff.append(custom_item)

        # 标记删除项
        for deleted_item in base_dict.values():
            item_key = deleted_item.get('id') or deleted_item.get('key') or deleted_item.get('field')
            diff.append({
                'id': item_key,
                '_deleted': True
            })

        return diff if diff else None
```

---

## 3. 自定义布局配置存储

### 3.1 自定义配置存储结构

自定义配置仅存储与基础布局的差异部分，采用增量存储策略：

```json
{
  "sections": [
    {
      "id": "section_basic_info",
      "fields": [
        {
          "field": "code",
          "readonly": true,
          "span": 2
        },
        {
          "field": "custom_field",
          "required": true
        },
        {
          "field": "unnecessary_field",
          "_deleted": true
        }
      ]
    },
    {
      "id": "section_custom_section",
      "title": "自定义区块",
      "columns": 2,
      "fields": [
        "custom_field_1",
        "custom_field_2"
      ]
    }
  ],
  "actions": [
    {
      "key": "custom_action",
      "label": "自定义操作",
      "type": "primary",
      "handler": "handleCustomAction"
    },
    {
      "key": "default_action",
      "_deleted": true
    }
  ],
  "title": "自定义标题",
  "icon": "CustomIcon"
}
```

### 3.2 配置缓存策略

```python
from django.core.cache import cache
from django.utils.encoding import force_str

class LayoutCacheManager:
    """布局缓存管理器"""

    CACHE_PREFIX = 'layout_config'
    CACHE_TIMEOUT = 3600  # 1小时

    @staticmethod
    def get_cache_key(user_id, layout_id):
        """生成缓存键"""
        return f"{LayoutCacheManager.CACHE_PREFIX}:{user_id}:{layout_id}"

    @staticmethod
    def get_merged_config(user, layout):
        """获取合并后的配置（带缓存）"""
        cache_key = LayoutCacheManager.get_cache_key(user.id, layout.id)

        # 尝试从缓存获取
        config = cache.get(cache_key)
        if config is not None:
            return config

        # 计算合并后的配置
        if isinstance(layout, UserLayoutPreference):
            config = layout.get_merged_config()
        else:
            config = layout.layout_config

        # 缓存配置
        cache.set(cache_key, config, LayoutCacheManager.CACHE_TIMEOUT)

        return config

    @staticmethod
    def invalidate_cache(user_id, layout_id):
        """清除缓存"""
        cache_key = LayoutCacheManager.get_cache_key(user_id, layout_id)
        cache.delete(cache_key)

    @staticmethod
    def invalidate_layout_cache(layout_id):
        """清除布局相关的所有缓存"""
        # 清除该布局的所有用户缓存
        keys = cache.keys(f"{LayoutCacheManager.CACHE_PREFIX}:*:{layout_id}")
        cache.delete_many(keys)
```

---

## 4. 自定义布局管理功能

### 4.1 布局重置功能

```python
class LayoutResetManager:
    """布局重置管理器"""

    @staticmethod
    def reset_to_default(user, business_object, layout_type):
        """
        重置为默认布局

        删除用户的所有自定义配置，恢复到默认布局
        """
        from .models import UserLayoutPreference, PageLayout

        # 删除用户级自定义布局
        UserLayoutPreference.objects.filter(
            scope='user',
            user=user,
            base_layout__business_object=business_object,
            base_layout__layout_type=layout_type
        ).delete()

        # 清除缓存
        try:
            default_layout = PageLayout.objects.get(
                business_object=business_object,
                layout_type=layout_type,
                is_default=True
            )
            LayoutCacheManager.invalidate_cache(user.id, default_layout.id)
        except PageLayout.DoesNotExist:
            pass

    @staticmethod
    def reset_to_base_layout(custom_layout):
        """
        重置到基础布局

        清除特定自定义布局的配置
        """
        custom_layout.custom_config = {}
        custom_layout.save()

        # 清除缓存
        if custom_layout.user:
            LayoutCacheManager.invalidate_cache(
                custom_layout.user.id,
                custom_layout.base_layout.id
            )
```

### 4.2 布局导入导出

```python
class LayoutImportExportManager:
    """布局导入导出管理器"""

    @staticmethod
    def export_layout(layout):
        """
        导出布局配置

        返回包含完整配置和元数据的字典
        """
        export_data = {
            'version': '1.0',
            'exported_at': timezone.now().isoformat(),
            'layout_type': layout.base_layout.layout_type if isinstance(layout, UserLayoutPreference) else layout.layout_type,
            'business_object': layout.base_layout.business_object.code if isinstance(layout, UserLayoutPreference) else layout.business_object.code,
            'base_layout_name': layout.base_layout.name if isinstance(layout, UserLayoutPreference) else layout.name,
            'custom_config': layout.custom_config if isinstance(layout, UserLayoutPreference) else layout.layout_config,
            'metadata': {
                'name': layout.name,
                'description': layout.description,
                'scope': layout.scope if isinstance(layout, UserLayoutPreference) else None,
            }
        }

        return export_data

    @staticmethod
    def import_layout(import_data, target_user=None, target_organization=None):
        """
        导入布局配置

        Args:
            import_data: 导出的布局数据
            target_user: 目标用户（可选）
            target_organization: 目标组织（可选）

        Returns:
            创建的UserLayoutPreference实例
        """
        from .models import UserLayoutPreference, PageLayout, BusinessObject

        # 验证导入数据
        if import_data.get('version') != '1.0':
            raise ValueError("不支持的导入数据版本")

        # 查找基础布局
        try:
            business_object = BusinessObject.objects.get(code=import_data['business_object'])
            base_layout = PageLayout.objects.get(
                business_object=business_object,
                name=import_data['base_layout_name']
            )
        except (BusinessObject.DoesNotExist, PageLayout.DoesNotExist):
            raise ValueError("找不到基础布局")

        # 确定作用域
        metadata = import_data['metadata']
        scope = metadata.get('scope', 'user')

        # 创建自定义布局
        custom_layout = UserLayoutPreference.objects.create(
            base_layout=base_layout,
            scope=scope,
            custom_config=import_data['custom_config'],
            name=metadata['name'],
            description=metadata.get('description', ''),
            user=target_user if scope == 'user' else None,
            organization=target_organization if scope == 'org' else None,
        )

        return custom_layout

    @staticmethod
    def export_to_file(layout, file_path):
        """导出布局到文件"""
        import json

        export_data = LayoutImportExportManager.export_layout(layout)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def import_from_file(file_path, target_user=None, target_organization=None):
        """从文件导入布局"""
        import json

        with open(file_path, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        return LayoutImportExportManager.import_layout(
            import_data,
            target_user,
            target_organization
        )
```

### 4.3 布局分享功能

```python
class LayoutShareManager:
    """布局分享管理器"""

    @staticmethod
    def share_layout(custom_layout, target_users):
        """
        分享布局给其他用户

        Args:
            custom_layout: 要分享的自定义布局
            target_users: 目标用户列表
        """
        custom_layout.is_shared = True
        custom_layout.save()
        custom_layout.shared_with.set(target_users)

    @staticmethod
    def unshare_layout(custom_layout):
        """取消分享"""
        custom_layout.is_shared = False
        custom_layout.save()
        custom_layout.shared_with.clear()

    @staticmethod
    def get_shared_layouts(user):
        """获取分享给用户的布局列表"""
        from .models import UserLayoutPreference

        return UserLayoutPreference.objects.filter(
            is_shared=True,
            shared_with=user,
            is_active=True
        ).select_related('base_layout', 'user')

    @staticmethod
    def copy_shared_layout(shared_layout, target_user):
        """
        复制分享的布局

        将分享的布局复制为目标用户的自定义布局
        """
        # 创建新的自定义布局
        new_layout = UserLayoutPreference.objects.create(
            base_layout=shared_layout.base_layout,
            scope='user',
            user=target_user,
            custom_config=shared_layout.custom_config.copy(),
            name=f"{shared_layout.name}（副本）",
            description=shared_layout.description,
            is_active=True
        )

        return new_layout
```

---

## 5. API 接口设计

### 5.1 自定义布局 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/system/custom-layouts/` | 获取自定义布局列表 |
| GET | `/api/system/custom-layouts/{id}/` | 获取自定义布局详情 |
| POST | `/api/system/custom-layouts/` | 创建自定义布局 |
| PUT | `/api/system/custom-layouts/{id}/` | 更新自定义布局 |
| PATCH | `/api/system/custom-layouts/{id}/` | 部分更新自定义布局 |
| DELETE | `/api/system/custom-layouts/{id}/` | 删除自定义布局 |
| GET | `/api/system/custom-layouts/active/` | 获取当前用户的活跃布局 |
| POST | `/api/system/custom-layouts/{id}/reset/` | 重置为默认布局 |
| POST | `/api/system/custom-layouts/{id}/export/` | 导出布局配置 |
| POST | `/api/system/custom-layouts/import/` | 导入布局配置 |
| POST | `/api/system/custom-layouts/{id}/share/` | 分享布局 |
| POST | `/api/system/custom-layouts/{id}/unshare/` | 取消分享 |
| GET | `/api/system/custom-layouts/shared/` | 获取分享给当前用户的布局 |
| POST | `/api/system/custom-layouts/{id}/copy/` | 复制布局 |

### 5.2 Serializer 定义

```python
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import UserLayoutPreference

class UserLayoutPreferenceSerializer(BaseModelSerializer):
    """
    用户布局偏好序列化器
    """
    base_layout_name = serializers.CharField(
        source='base_layout.name',
        read_only=True
    )

    base_layout_type = serializers.CharField(
        source='base_layout.layout_type',
        read_only=True
    )

    business_object_name = serializers.CharField(
        source='base_layout.business_object.name',
        read_only=True
    )

    merged_config = serializers.SerializerMethodField()
    scope_display = serializers.CharField(
        source='get_scope_display',
        read_only=True
    )

    shared_with_users = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = UserLayoutPreference
        fields = BaseModelSerializer.Meta.fields + [
            'scope',
            'scope_display',
            'user',
            'role',
            'organization',
            'base_layout',
            'base_layout_name',
            'base_layout_type',
            'business_object_name',
            'custom_config',
            'merged_config',
            'name',
            'description',
            'is_active',
            'priority',
            'is_shared',
            'shared_with',
            'shared_with_users'
        ]
        read_only_fields = ['merged_config']

    def get_merged_config(self, obj):
        """获取合并后的完整配置"""
        return obj.get_merged_config()

    def get_shared_with_users(self, obj):
        """获取分享用户列表"""
        return [
            {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.get_full_name()
            }
            for user in obj.shared_with.all()
        ]

    def validate_custom_config(self, value):
        """验证自定义配置"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("自定义配置必须是JSON对象")

        return value

    def validate(self, attrs):
        """验证数据"""
        scope = attrs.get('scope')
        user = attrs.get('user')
        role = attrs.get('role')
        organization = attrs.get('organization')

        # 验证作用域对应的参数
        if scope == 'user' and not user:
            raise serializers.ValidationError("用户级布局必须指定user")
        if scope == 'role' and not role:
            raise serializers.ValidationError("角色级布局必须指定role")
        if scope == 'org' and not organization:
            raise serializers.ValidationError("组织级布局必须指定organization")

        return attrs


class CustomLayoutExportSerializer(serializers.Serializer):
    """布局导出序列化器"""
    file = serializers.FileField(write_only=True)
    data = serializers.DictField(read_only=True)

    def validate_file(self, value):
        """验证文件格式"""
        import json

        try:
            data = json.load(value)
            if data.get('version') != '1.0':
                raise serializers.ValidationError("不支持的文件版本")
            return data
        except json.JSONDecodeError:
            raise serializers.ValidationError("无效的JSON文件")
        except Exception as e:
            raise serializers.ValidationError(f"文件解析失败: {str(e)}")
```

### 5.3 ViewSet 定义

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from apps.common.viewsets.base import BaseModelViewSet
from .models import UserLayoutPreference
from .serializers import UserLayoutPreferenceSerializer, CustomLayoutExportSerializer
from .services import (
    LayoutSelector,
    LayoutInheritanceManager,
    LayoutResetManager,
    LayoutImportExportManager,
    LayoutShareManager,
    LayoutCacheManager
)

class UserLayoutPreferenceViewSet(BaseModelViewSet):
    """
    用户布局偏好视图集
    """
    queryset = UserLayoutPreference.objects.select_related(
        'user',
        'role',
        'organization',
        'base_layout',
        'base_layout__business_object'
    ).prefetch_related('shared_with').all()

    serializer_class = UserLayoutPreferenceSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        user = self.request.user

        # 只显示当前用户有权限访问的布局
        # 1. 用户自己创建的布局
        # 2. 分享给当前用户的布局
        queryset = queryset.filter(
            models.Q(user=user) |
            models.Q(is_shared=True, shared_with=user)
        )

        # 过滤作用域
        scope = self.request.query_params.get('scope')
        if scope:
            queryset = queryset.filter(scope=scope)

        # 过滤基础布局
        base_layout_id = self.request.query_params.get('base_layout')
        if base_layout_id:
            queryset = queryset.filter(base_layout_id=base_layout_id)

        # 过滤启用状态
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取当前用户的活跃布局"""
        business_object_code = request.query_params.get('business_object')
        layout_type = request.query_params.get('layout_type')

        if not business_object_code or not layout_type:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '缺少business_object或layout_type参数'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # 查找业务对象
        from apps.system.models import BusinessObject
        try:
            business_object = BusinessObject.objects.get(code=business_object_code)
        except BusinessObject.DoesNotExist:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '业务对象不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # 选择布局
        layout = LayoutSelector.select_layout(request.user, business_object, layout_type)

        if not layout:
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '未找到合适的布局'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # 序列化布局
        if isinstance(layout, UserLayoutPreference):
            serializer = self.get_serializer(layout)
        else:
            from apps.system.serializers import PageLayoutSerializer
            serializer = PageLayoutSerializer(layout)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """重置为默认布局"""
        custom_layout = self.get_object()

        # 重置布局
        LayoutResetManager.reset_to_base_layout(custom_layout)

        return Response({
            'success': True,
            'message': '布局已重置'
        })

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """导出布局配置"""
        custom_layout = self.get_object()

        # 导出配置
        export_data = LayoutImportExportManager.export_layout(custom_layout)

        return Response({
            'success': True,
            'data': export_data
        })

    @action(detail=False, methods=['post'])
    def import(self, request):
        """导入布局配置"""
        serializer = CustomLayoutExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        import_data = serializer.validated_data['file']

        # 导入布局
        try:
            custom_layout = LayoutImportExportManager.import_layout(
                import_data,
                target_user=request.user
            )
        except ValueError as e:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # 序列化结果
        result_serializer = self.get_serializer(custom_layout)

        return Response({
            'success': True,
            'message': '布局导入成功',
            'data': result_serializer.data
        })

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """分享布局"""
        custom_layout = self.get_object()

        # 验证权限
        if custom_layout.user != request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': '只有布局创建者才能分享'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # 获取目标用户
        target_user_ids = request.data.get('user_ids', [])
        if not target_user_ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '缺少user_ids参数'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        from apps.accounts.models import User
        target_users = User.objects.filter(id__in=target_user_ids)

        if not target_users.exists():
            return Response({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': '目标用户不存在'
                }
            }, status=status.HTTP_404_NOT_FOUND)

        # 分享布局
        LayoutShareManager.share_layout(custom_layout, target_users)

        return Response({
            'success': True,
            'message': '布局分享成功'
        })

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """取消分享"""
        custom_layout = self.get_object()

        # 验证权限
        if custom_layout.user != request.user:
            return Response({
                'success': False,
                'error': {
                    'code': 'PERMISSION_DENIED',
                    'message': '只有布局创建者才能取消分享'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # 取消分享
        LayoutShareManager.unshare_layout(custom_layout)

        return Response({
            'success': True,
            'message': '已取消分享'
        })

    @action(detail=False, methods=['get'])
    def shared(self, request):
        """获取分享给当前用户的布局"""
        shared_layouts = LayoutShareManager.get_shared_layouts(request.user)

        serializer = self.get_serializer(shared_layouts, many=True)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """复制布局"""
        shared_layout = self.get_object()

        # 验证是否为分享的布局
        if not shared_layout.is_shared:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': '只能复制分享的布局'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # 复制布局
        new_layout = LayoutShareManager.copy_shared_layout(
            shared_layout,
            request.user
        )

        # 序列化结果
        serializer = self.get_serializer(new_layout)

        return Response({
            'success': True,
            'message': '布局复制成功',
            'data': serializer.data
        })
```

---

## 6. 前端组件实现

### 6.1 布局自定义组件

#### LayoutCustomizer.vue
```vue
<template>
  <div class="layout-customizer">
    <el-dialog
      v-model="visible"
      title="自定义布局"
      width="80%"
      :close-on-click-modal="false"
      @close="handleClose"
    >
      <el-tabs v-model="activeTab">
        <!-- 字段配置 -->
        <el-tab-pane label="字段配置" name="fields">
          <layout-field-config
            :fields="mergedConfig.sections"
            :base-fields="baseConfig.sections"
            @update="handleFieldsUpdate"
          />
        </el-tab-pane>

        <!-- 操作按钮配置 -->
        <el-tab-pane label="操作按钮" name="actions">
          <layout-action-config
            :actions="mergedConfig.actions"
            :base-actions="baseConfig.actions"
            @update="handleActionsUpdate"
          />
        </el-tab-pane>

        <!-- 显示规则 -->
        <el-tab-pane label="显示规则" name="visibility">
          <layout-visibility-config
            :rules="customConfig.visibility_rules"
            @update="handleVisibilityUpdate"
          />
        </el-tab-pane>

        <!-- 预览 -->
        <el-tab-pane label="预览" name="preview">
          <dynamic-form
            :layout-config="mergedConfig"
            :business-object="businessObject"
            :readonly="true"
          />
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="handleClose">取消</el-button>
        <el-button @click="handleReset">重置</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import DynamicForm from './DynamicForm.vue'
import LayoutFieldConfig from './LayoutFieldConfig.vue'
import LayoutActionConfig from './LayoutActionConfig.vue'
import LayoutVisibilityConfig from './LayoutVisibilityConfig.vue'
import { layoutApi } from '@/api/system'

const props = defineProps({
  modelValue: Boolean,
  baseLayout: Object,
  customLayout: Object,
  businessObject: String
})

const emit = defineEmits(['update:modelValue', 'saved'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const activeTab = ref('fields')
const customConfig = ref({})
const baseConfig = computed(() => props.baseLayout?.layout_config || {})
const mergedConfig = computed(() => {
  return ConfigMerger.merge(baseConfig.value, customConfig.value)
})

const handleFieldsUpdate = (fields) => {
  customConfig.value.sections = fields
}

const handleActionsUpdate = (actions) => {
  customConfig.value.actions = actions
}

const handleVisibilityUpdate = (rules) => {
  customConfig.value.visibility_rules = rules
}

const handleSave = async () => {
  try {
    // 计算差异
    const diff = ConfigDiffCalculator.calculate_diff(
      baseConfig.value,
      mergedConfig.value
    )

    // 保存自定义布局
    if (props.customLayout) {
      await layoutApi.updateCustomLayout(props.customLayout.id, {
        custom_config: diff
      })
    } else {
      await layoutApi.createCustomLayout({
        base_layout: props.baseLayout.id,
        scope: 'user',
        custom_config: diff,
        name: `${props.baseLayout.name}（自定义）`
      })
    }

    ElMessage.success('保存成功')
    emit('saved')
    handleClose()
  } catch (error) {
    ElMessage.error('保存失败：' + error.message)
  }
}

const handleReset = () => {
  customConfig.value = {}
  ElMessage.success('已重置为默认配置')
}

const handleClose = () => {
  visible.value = false
}
</script>
```

### 6.2 布局管理组件

#### LayoutManager.vue
```vue
<template>
  <div class="layout-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的自定义布局</span>
          <el-button type="primary" @click="handleCreate">
            新建自定义布局
          </el-button>
        </div>
      </template>

      <el-table :data="customLayouts" v-loading="loading">
        <el-table-column prop="name" label="布局名称" />
        <el-table-column prop="scope_display" label="作用域" />
        <el-table-column prop="base_layout_name" label="基础布局" />
        <el-table-column prop="is_active" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_shared" label="分享状态">
          <template #default="{ row }">
            <el-tag v-if="row.is_shared" type="success">已分享</el-tag>
            <el-tag v-else type="info">未分享</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300">
          <template #default="{ row }">
            <el-button
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              @click="handlePreview(row)"
            >
              预览
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 布局自定义对话框 -->
    <layout-customizer
      v-model="customizerVisible"
      :base-layout="selectedBaseLayout"
      :custom-layout="selectedCustomLayout"
      :business-object="businessObject"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import LayoutCustomizer from './LayoutCustomizer.vue'
import { layoutApi } from '@/api/system'

const props = defineProps({
  businessObject: String,
  layoutType: String
})

const loading = ref(false)
const customLayouts = ref([])
const customizerVisible = ref(false)
const selectedBaseLayout = ref(null)
const selectedCustomLayout = ref(null)

const fetchCustomLayouts = async () => {
  loading.value = true
  try {
    const response = await layoutApi.getCustomLayouts({
      base_layout__business_object__code: props.businessObject,
      base_layout__layout_type: props.layoutType
    })
    customLayouts.value = response.data.results
  } catch (error) {
    ElMessage.error('加载失败：' + error.message)
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  // 获取默认布局作为基础
  try {
    const response = await layoutApi.getDefaultLayout(
      props.businessObject,
      props.layoutType
    )
    selectedBaseLayout.value = response.data
    selectedCustomLayout.value = null
    customizerVisible.value = true
  } catch (error) {
    ElMessage.error('获取默认布局失败')
  }
}

const handleEdit = async (row) => {
  selectedBaseLayout.value = row.base_layout
  selectedCustomLayout.value = row
  customizerVisible.value = true
}

const handlePreview = (row) => {
  // 预览布局
  selectedBaseLayout.value = row.base_layout
  selectedCustomLayout.value = row
  customizerVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该自定义布局吗？', '提示', {
      type: 'warning'
    })

    await layoutApi.deleteCustomLayout(row.id)
    ElMessage.success('删除成功')
    fetchCustomLayouts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

const handleSaved = () => {
  fetchCustomLayouts()
}

onMounted(() => {
  fetchCustomLayouts()
})
</script>
```

---

## 7. 使用示例

### 7.1 创建用户级自定义布局

```python
from apps.system.models import PageLayout, BusinessObject, UserLayoutPreference
from apps.accounts.models import User

# 获取基础布局
asset_object = BusinessObject.objects.get(code='asset')
base_layout = PageLayout.objects.get(
    business_object=asset_object,
    layout_type='form',
    is_default=True
)

# 定义自定义配置（仅包含差异部分）
custom_config = {
    "sections": [
        {
            "id": "section_basic_info",
            "fields": [
                {
                    "field": "code",
                    "readonly": true,  # 修改为只读
                    "span": 2
                },
                {
                    "field": "custom_field",  # 新增字段
                    "required": true
                },
                {
                    "field": "unnecessary_field",
                    "_deleted": True  # 删除字段
                }
            ]
        }
    ],
    "actions": [
        {
            "key": "custom_submit",
            "label": "自定义提交",
            "type": "primary",
            "handler": "handleCustomSubmit"
        }
    ]
}

# 创建用户级自定义布局
user = User.objects.get(username='testuser')
custom_layout = UserLayoutPreference.objects.create(
    base_layout=base_layout,
    scope='user',
    user=user,
    custom_config=custom_config,
    name='我的资产表单',
    description='个性化定制的资产表单布局',
    is_active=True,
    priority=0
)

# 获取合并后的完整配置
merged_config = custom_layout.get_merged_config()
```

### 7.2 创建角色级自定义布局

```python
from apps.accounts.models import Role

# 获取角色
role = Role.objects.get(name='资产管理员')

# 创建角色级自定义布局
role_custom_layout = UserLayoutPreference.objects.create(
    base_layout=base_layout,
    scope='role',
    role=role,
    custom_config={
        "sections": [
            {
                "id": "section_approval",
                "title": "审批信息",
                "fields": ["approval_status", "approval_comment"]
            }
        ]
    },
    name='资产管理员布局',
    description='资产管理员专用的资产表单布局',
    is_active=True,
    priority=10
)
```

### 7.3 布局导入导出

```python
from apps.system.services import LayoutImportExportManager

# 导出布局
export_data = LayoutImportExportManager.export_layout(custom_layout)

# 保存到文件
LayoutImportExportManager.export_to_file(
    custom_layout,
    '/path/to/custom_layout.json'
)

# 从文件导入
new_layout = LayoutImportExportManager.import_from_file(
    '/path/to/custom_layout.json',
    target_user=some_user
)
```

### 7.4 布局分享

```python
from apps.system.services import LayoutShareManager
from apps.accounts.models import User

# 分享布局给其他用户
target_users = User.objects.filter(username__in=['user1', 'user2'])
LayoutShareManager.share_layout(custom_layout, target_users)

# 获取分享给用户的布局
shared_layouts = LayoutShareManager.get_shared_layouts(user)

# 复制分享的布局
copied_layout = LayoutShareManager.copy_shared_layout(
    shared_layouts.first(),
    user
)
```

---

## 8. 最佳实践

### 8.1 自定义布局设计原则

1. **最小化差异**：自定义配置应仅包含必要的修改，减少维护成本
2. **明确命名**：为自定义布局设置清晰的名称和描述，便于识别
3. **合理分层**：根据业务需求选择合适的作用域（用户级、角色级、组织级、全局级）
4. **版本控制**：重大变更时创建新版本，保留历史记录
5. **权限控制**：严格控制布局编辑和分享权限

### 8.2 性能优化建议

1. **缓存策略**：合并后的配置应进行缓存，避免重复计算
2. **按需加载**：大型布局配置采用懒加载策略
3. **增量更新**：仅更新变化的部分，减少网络传输
4. **预编译**：常用布局预编译为静态配置，提升加载速度

### 8.3 用户体验优化

1. **可视化编辑器**：提供拖拽式布局编辑器，降低配置门槛
2. **实时预览**：编辑时实时预览效果
3. **版本对比**：支持布局版本对比功能
4. **一键重置**：提供快速恢复默认配置的功能
5. **模板库**：提供常用布局模板，快速创建自定义布局

---

## 9. 总结

自定义页面布局是 GZEAMS 低代码平台的关键功能，通过以下机制实现灵活的布局定制：

1. **多层级自定义**：支持用户级、角色级、组织级、全局级四种作用域
2. **优先级明确**：自动选择最合适的布局，确保用户体验一致性
3. **增量存储**：仅存储差异配置，减少数据冗余
4. **灵活继承**：支持基于任意布局创建自定义版本
5. **配置合并**：智能合并基础配置和自定义配置
6. **缓存优化**：合并后的配置自动缓存，提升性能
7. **导入导出**：支持布局配置的分享和复用
8. **可视化管理**：提供直观的布局管理界面

通过合理使用自定义布局功能，可以在不修改默认布局的情况下，满足不同用户、角色和组织的个性化需求，大幅提升系统的灵活性和用户体验。
