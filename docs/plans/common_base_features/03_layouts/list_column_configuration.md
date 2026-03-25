# 列表字段显示管理规范

## 目录
1. [概述](#1-概述)
2. [列配置数据模型](#2-列配置数据模型)
3. [列显示配置](#3-列显示配置)
4. [列排序配置](#4-列排序配置)
5. [列宽配置](#5-列宽配置)
6. [列固定配置](#6-列固定配置)
7. [用户个性化配置](#7-用户个性化配置)
8. [前端实现](#8-前端实现)
9. [后端实现](#9-后端实现)
10. [使用示例](#10-使用示例)

---

## 1. 概述

### 1.1 定义

**列表字段显示管理**是指用户对列表页面的列进行自定义配置的能力，包括：
- 列的显示/隐藏
- 列的排序（拖拽调整顺序）
- 列宽调整（拖拽调整宽度）
- 列的固定（左侧/右侧固定）
- 列的排序规则（点击列头排序）

### 1.2 使用场景

| 场景 | 说明 |
|------|------|
| **用户个性化** | 不同用户关注不同的字段，需要自定义显示的列 |
| **角色差异化** | 不同角色需要查看不同的列 |
| **屏幕适配** | 不同屏幕尺寸需要显示不同数量的列 |
| **数据导出** | 导出时使用用户配置的列顺序和可见性 |

### 1.3 配置层级

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         列配置层级优先级                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Level 1: 用户级偏好 (UserColumnPreference)                         │  │
│  │  - 仅当前用户可见                                                   │  │
│  │  - 定义: 可见性(visible), 宽度(width), 顺序(order), 冻结(fixed)      │  │
│  │  - 优先级最高 (Presentation Layer)                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Level 2: 页面默认配置 (PageLayout)                                 │  │
│  │  - 定义: 默认列宽, 默认排序, 默认隐藏列                              │  │
│  │  - 组织级/系统级默认展示策略                                         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                 │                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Level 0: 字段定义 (FieldDefinition) - Single Source of Truth       │  │
│  │  - 定义: 字段名(name), 类型(type), 可排序(sortable), 权限与脱敏      │  │
│  │  - 绝对约束: 如果字段被系统隐藏/禁用，上层配置无法强制显示             │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 列配置数据模型

### 2.1 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields处理 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |

### 2.2 ColumnItem 数据结构 (引用式)

列表配置不再全量存储字段信息，而是仅存储**对字段定义的引用**和**展示覆盖项**。

**ColumnItem 接口属性：**

| 属性 | 类型 | 必填 | 说明 | 数据源 |
|------|------|------|------|--------|
| `field_code` | string | 是 | **字段唯一标识** (对应 FieldDefinition.code) | 引用 |
| `label_override` | string | 否 | **自定义列标题** (覆盖 FieldDefinition.name) | 覆盖 |
| `visible` | boolean | 是 | 是否可见 (受限于 FieldDefinition.permission) | 展示偏好 |
| `width` | number \| string | 否 | 列宽 (覆盖默认宽度) | 展示偏好 |
| `fixed` | boolean \| 'left' \| 'right' | 否 | 列固定方式 | 展示偏好 |
| `order_index` | number | 否 | 排序权重 (决定列顺序) | 展示偏好 |

**以下属性直接由 `FieldDefinition` 决定（列表配置中不存储，仅运行时合并获取）：**
*   `type`: 字段类型 (text/date/number...)
*   `sortable`: 是否可排序 (由后端字段能力决定)
*   `filterable`: 是否可筛选
*   `permission`: 权限标识
*   `sensitivity`: 脱敏规则

### 2.2 ColumnConfig 数据结构

**ColumnConfig 接口属性：**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `configId` | string | 是 | 配置唯一标识 |
| `objectCode` | string | 是 | 业务对象编码 |
| `layoutType` | 'list' | 是 | 布局类型 |
| `scope` | string | 是 | 配置范围：user/role/organization/default |
| `scopeId` | string | 否 | 范围ID（用户ID/角色ID/组织ID） |
| `columns` | ColumnItem[] | 是 | 列配置列表 |
| `columnOrder` | string[] | 是 | 列顺序（field列表） |
| `stripe` | boolean | 是 | 斑马纹 |
| `border` | boolean | 是 | 边框 |
| `showHeader` | boolean | 是 | 显示表头 |
| `highlightCurrentRow` | boolean | 是 | 高亮当前行 |
| `size` | string | 否 | 表格尺寸：large/default/small |
| `pagination` | boolean | 是 | 是否分页 |
| `pageSize` | number | 是 | 每页数量 |
| `pageSizes` | number[] | 否 | 可选每页数量 |
| `defaultSort` | Object | 否 | 默认排序 {prop, order} |
| `createdAt` | string | 是 | 创建时间 |
| `updatedAt` | string | 是 | 更新时间 |
| `createdBy` | string | 否 | 创建人 |

---

## 3. 列显示配置

### 3.1 列可见性控制

```javascript
{
  "field_code": "asset_name",     // 引用字段
  "label_override": "资产名称",    // 可选：覆盖默认标签
  "visible": true                   // 用户偏好
}
```

### 3.2 条件可见规则

```javascript
{
  "field_code": "purchase_price",
  "visible": false  // 用户偏好：隐藏
}
```
> **注意**: 复杂的动态可见性规则 (Visible Conditions) 应在 PageLayout (Level 2) 中定义，UserConfig (Level 1) 仅存储最终的 boolean 结果或用户手动开关。

### 3.3 响应式可见性

```javascript
{
  "field": "remark",
  "label": "备注",
  "visible": true,
  "responsive": {
    "mobile": false,                // 移动端隐藏
    "tablet": true,                 // 平板端显示
    "desktop": true                 // 桌面端显示
  }
}
```

---

## 4. 列排序配置

### 4.1 列顺序配置

```javascript
{
  "columnOrder": [
    "selection",                    // 选择列
    "asset_code",                   // 资产编码
    "asset_name",                   // 资产名称
    "category",                     // 分类
    "status",                       // 状态
    "purchase_price",               // 采购价格
    "actions"                       // 操作列
  ]
}
```

### 4.2 可拖拽排序

```javascript
{
  "draggable": true,                // 启用拖拽排序
  "dragHandle": ".column-header",   // 拖拽手柄选择器
  "dragAnimation": 150,             // 拖拽动画时长（ms）
  "saveOnDrop": true,               // 拖拽释放后自动保存
  "confirmBeforeSave": false        // 保存前确认
}
```

### 4.3 列头排序（数据排序）

排序能力由 `FieldDefinition.enable_sorting` 决定，配置仅存储默认排序规则。

```javascript
{
  "field_code": "purchase_date",
  // sortable: true,  <-- 移除，由 FieldDefinition 决定
  "defaultSortOrder": null
}
```

### 4.4 多列排序

```javascript
{
  "multiSort": true,                // 启用多列排序
  "maxSortColumns": 3,              // 最多排序列数
  "sortPriority": [                 // 排序优先级
    {"prop": "category", "order": "ascending"},
    {"prop": "purchase_date", "order": "descending"}
  ]
}
```

---

## 5. 列宽配置

### 5.1 固定列宽

```javascript
{
  "field_code": "asset_code",
  "width": 150                      // 用户调整后的宽度
}
```

### 5.2 百分比列宽

```javascript
{
  "field": "asset_name",
  "label": "资产名称",
  "width": "30%",                   // 百分比宽度
  "minWidth": 200,                  // 最小宽度
  "maxWidth": 500                   // 最大宽度
}
```

### 5.3 自动列宽

```javascript
{
  "field": "remark",
  "label": "备注",
  "width": "auto",                  // 自动宽度
  "minWidth": 100,
  "maxAutoWidth": 600               // 最大自动宽度
}
```

### 5.4 列宽调整

```javascript
{
  "resizable": true,                // 全局启用列宽调整
  "resizeMode": "fit",              // fit(适应内容) | expand(扩展)
  "minColumnWidth": 80,             // 最小列宽
  "maxColumnWidth": 800,            // 最大列宽
  "resizeStep": 10,                 // 调整步长（像素）
  "saveOnResize": true,             // 调整后自动保存
  "showResizeLine": true            // 显示调整线
}
```

---

## 6. 列固定配置

### 6.1 左侧固定

```javascript
{
  "field_code": "asset_code",
  "fixed": "left"                   // 用户偏好：固定在左侧
}
```

### 6.2 右侧固定

```javascript
{
  "field": "actions",
  "label": "操作",
  "fixed": "right",                 // 右侧固定
  "fixedPriority": 1
}
```

### 6.3 多列固定

```javascript
{
  "fixedColumns": {
    "left": ["selection", "asset_code"],  // 左侧固定列
    "right": ["actions"]                   // 右侧固定列
  },
  "fixedColumnsStyle": {
    "backgroundColor": "#f5f7fa",
    "zIndex": 2
  }
}
```

---

## 7. 用户个性化配置

### 7.1 用户配置模型

```python
# apps/system/models.py
from django.db import models
from apps.common.models import BaseModel

class UserColumnPreference(BaseModel):
    """用户列表列配置偏好"""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        verbose_name='用户'
    )

    # 业务对象标识
    object_code = models.CharField(
        max_length=50,
        verbose_name='对象编码',
        help_text='如: asset, procurement_request'
    )

    # 列配置（JSON）
    column_config = models.JSONField(
        default=dict,
        verbose_name='列配置'
    )

    # 配置名称（支持多套配置）
    config_name = models.CharField(
        max_length=50,
        default='default',
        verbose_name='配置名称'
    )

    # 是否为默认配置
    is_default = models.BooleanField(
        default=True,
        verbose_name='是否默认配置'
    )

    class Meta:
        db_table = 'system_user_column_preference'
        verbose_name = '用户列配置偏好'
        verbose_name_plural = '用户列配置偏好'
        unique_together = [['user', 'object_code', 'config_name']]
        indexes = [
            models.Index(fields=['user', 'object_code']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.object_code} - {self.config_name}"
```

### 7.2 角色配置模型

```python
class RoleColumnPreference(BaseModel):
    """角色列表列配置"""

    role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        verbose_name='角色'
    )

    object_code = models.CharField(
        max_length=50,
        verbose_name='对象编码'
    )

    column_config = models.JSONField(
        default=dict,
        verbose_name='列配置'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    class Meta:
        db_table = 'system_role_column_preference'
        verbose_name = '角色列配置'
        verbose_name_plural = '角色列配置'
        unique_together = [['role', 'object_code']]


class OrganizationColumnPreference(BaseModel):
    """组织列表列配置"""

    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='column_preferences',
        verbose_name='组织'
    )

    object_code = models.CharField(
        max_length=50,
        verbose_name='对象编码'
    )

    column_config = models.JSONField(
        default=dict,
        verbose_name='列配置'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用'
    )

    class Meta:
        db_table = 'system_org_column_preference'
        verbose_name = '组织列配置'
        verbose_name_plural = '组织列配置'
        unique_together = [['organization', 'object_code']]
```

### 7.3 配置优先级服务

```python
# apps/system/services/column_config_service.py
from typing import Optional, Dict
from django.core.cache import cache
from .models import UserColumnPreference, RoleColumnPreference, OrganizationColumnPreference
from apps.system.models import PageLayout

class ColumnConfigService:
    """列配置服务 - 负责获取合并后的列配置"""

    CACHE_TIMEOUT = 3600  # 1小时

    @classmethod
    def get_column_config(cls, user, object_code: str) -> Dict:
        """
        获取用户的列配置（按优先级合并）

        优先级: 用户配置 > 角色配置 > 组织配置 > 默认配置
        """
        cache_key = f"column_config:{user.id}:{object_code}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. 获取默认配置（PageLayout）
        default_config = cls._get_default_config(object_code)

        # 2. 获取组织配置
        org_config = cls._get_org_config(user.organization, object_code)

        # 3. 获取角色配置（取第一个匹配角色的配置）
        role_config = cls._get_role_config(user.roles.all(), object_code)

        # 4. 获取用户配置
        user_config = cls._get_user_config(user, object_code)

        # 5. 按优先级合并配置
        merged_config = cls._merge_configs(
            default_config,
            org_config,
            role_config,
            user_config
        )

        # 缓存结果
        cache.set(cache_key, merged_config, cls.CACHE_TIMEOUT)

        return merged_config

    @classmethod
    def _get_default_config(cls, object_code: str) -> Dict:
        """获取默认配置（从 PageLayout）"""
        try:
            layout = PageLayout.objects.get(
                business_object__code=object_code,
                layout_type='list',
                is_default=True
            )
            return layout.layout_config.get('columns', {})
        except PageLayout.DoesNotExist:
            return {}

    @classmethod
    def _get_org_config(cls, organization, object_code: str) -> Dict:
        """获取组织配置"""
        try:
            pref = OrganizationColumnPreference.objects.get(
                organization=organization,
                object_code=object_code,
                is_active=True
            )
            return pref.column_config
        except OrganizationColumnPreference.DoesNotExist:
            return {}

    @classmethod
    def _get_role_config(cls, roles, object_code: str) -> Dict:
        """获取角色配置（取第一个匹配）"""
        for role in roles:
            try:
                pref = RoleColumnPreference.objects.get(
                    role=role,
                    object_code=object_code,
                    is_active=True
                )
                return pref.column_config
            except RoleColumnPreference.DoesNotExist:
                continue
        return {}

    @classmethod
    def _get_user_config(cls, user, object_code: str) -> Dict:
        """获取用户配置"""
        try:
            pref = UserColumnPreference.objects.get(
                user=user,
                object_code=object_code,
                is_default=True
            )
            return pref.column_config
        except UserColumnPreference.DoesNotExist:
            return {}

    @classmethod
    def _merge_configs(cls, *configs) -> Dict:
        """合并配置（后面的覆盖前面的）"""
        result = {}
        for config in configs:
            if config:
                result.update(config)
        return result

    @classmethod
    def save_user_config(cls, user, object_code: str, config: Dict, config_name: str = 'default'):
        """保存用户配置"""
        pref, created = UserColumnPreference.objects.get_or_create(
            user=user,
            object_code=object_code,
            config_name=config_name,
            defaults={'column_config': config}
        )

        if not created:
            pref.column_config = config
            pref.save()

        # 清除缓存
        cache_key = f"column_config:{user.id}:{object_code}"
        cache.delete(cache_key)

        return pref

    @classmethod
    def reset_user_config(cls, user, object_code: str) -> bool:
        """重置用户配置为默认"""
        try:
            UserColumnPreference.objects.filter(
                user=user,
                object_code=object_code
            ).delete()

            # 清除缓存
            cache_key = f"column_config:{user.id}:{object_code}"
            cache.delete(cache_key)

            return True
        except Exception:
            return False
```

---

## 8. 前端实现

### 8.1 ColumnManager 组件 (Field-Driven)

```vue
<template>
  <div class="column-manager">
    <!-- 侧滑抽屉配置列 -->
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon">
          <Icon name="setting" class="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent class="w-[400px]">
        <SheetHeader>
          <SheetTitle>列显示设置</SheetTitle>
          <SheetDescription>
            拖拽调整顺序，勾选显示的字段。
          </SheetDescription>
        </SheetHeader>
        
        <div class="py-4 h-[calc(100vh-120px)] overflow-y-auto">
          <!-- 字段列表 -->
          <draggable
            v-model="mergedColumns"
            item-key="field_code"
            handle=".drag-handle"
            @end="handleDragEnd"
          >
            <template #item="{ element: col }">
              <div class="flex items-center gap-3 p-2 border-b bg-white hover:bg-slate-50">
                <!-- 拖拽手柄 -->
                <Icon name="grip-vertical" class="drag-handle text-slate-400 cursor-move h-4 w-4" />
                
                <!-- 可见性勾选 (受限于必显规则) -->
                <Checkbox 
                  :checked="col.visible" 
                  :disabled="col.required_in_list"
                  @update:checked="(v) => handleVisibilityChange(col.field_code, v)"
                />
                
                <div class="flex-1">
                  <!-- 字段名 (优先显示 Override Label) -->
                  <div class="font-medium text-sm">
                    {{ col.label_override || col.def_name }}
                  </div>
                  <!-- 原字段名提示 -->
                  <div v-if="col.label_override" class="text-xs text-slate-400">
                    原名: {{ col.def_name }}
                  </div>
                </div>

                <!-- 字段类型图标 -->
                <Badge variant="outline" class="text-xs">
                  {{ col.def_type }}
                </Badge>
              </div>
            </template>
          </draggable>
        </div>

        <SheetFooter>
          <Button variant="outline" @click="resetToDefault">重置默认</Button>
          <Button @click="saveConfiguration">保存配置</Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useFieldStore } from '@/stores/field'
import { useUserConfigStore } from '@/stores/userConfig'
// Shadcn & Tailwind imports omitted for brevity

const props = defineProps<{ objectCode: string }>()

const fieldStore = useFieldStore()
const configStore = useUserConfigStore()

// 核心逻辑: 动态合并 FieldDefinition 与 UserPreference
const mergedColumns = computed(() => {
  const definitions = fieldStore.getFields(props.objectCode)
  const userConfig = configStore.getConfig(props.objectCode)

  return definitions.map(def => {
    // 查找该字段的用户配置
    const pref = userConfig.columns.find(c => c.field_code === def.code)
    
    return {
      // 1. 唯一标识
      field_code: def.code,
      
      // 2. 基础属性 (来自 FieldDef)
      def_name: def.name,
      def_type: def.type,
      required_in_list: def.required_in_list, // 列表必显约束
      
      // 3. 用户偏好 (User Pref)
      // 如果没有用户配置，则使用字段定义的默认可见性
      visible: pref?.visible ?? def.default_visible_in_list ?? true,
      
      // 允许用户重命名
      label_override: pref?.label_override,
      
      // 4. 排序权重 (Order)
      order_index: pref?.order_index ?? 9999
    }
  }).sort((a, b) => a.order_index - b.order_index)
})

// 保存时，只保存有变更的偏好，不保存全量 FieldDef
const saveConfiguration = () => {
    const preferences = mergedColumns.value.map((col, index) => ({
        field_code: col.field_code,
        visible: col.visible,
        order_index: index, // 按当前数组顺序保存索引
        label_override: col.label_override
    }))
    
    configStore.saveConfig(props.objectCode, preferences)
}
</script>
```

### 8.2 useColumnConfig Composable

```javascript
// frontend/src/composables/useColumnConfig.js
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const columnConfigCache = new Map()

export function useColumnConfig(objectCode) {
  const userStore = useUserStore()
  const config = ref(null)
  const loading = ref(false)

  // 获取列配置
  const fetchConfig = async () => {
    if (columnConfigCache.has(objectCode)) {
      config.value = columnConfigCache.get(objectCode)
      return config.value
    }

    loading.value = true
    try {
      const response = await fetch(`/api/system/column-config/${objectCode}/`, {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        config.value = data.data
        columnConfigCache.set(objectCode, config.value)
      }
    } catch (error) {
      console.error('获取列配置失败:', error)
    } finally {
      loading.value = false
    }

    return config.value
  }

  // 保存列配置
  const saveConfig = async (columns) => {
    loading.value = true
    try {
      const response = await fetch(`/api/system/column-config/${objectCode}/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userStore.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          columns,
          column_order: columns.filter(c => c.visible).map(c => c.field)
        })
      })

      if (response.ok) {
        const data = await response.json()
        config.value = data.data
        columnConfigCache.set(objectCode, config.value)
        ElMessage.success('配置保存成功')
      }
    } catch (error) {
      ElMessage.error('配置保存失败')
    } finally {
      loading.value = false
    }
  }

  // 重置列配置
  const resetConfig = async () => {
    loading.value = true
    try {
      const response = await fetch(`/api/system/column-config/${objectCode}/reset/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })

      if (response.ok) {
        columnConfigCache.delete(objectCode)
        await fetchConfig()
        ElMessage.success('配置已重置为默认')
      }
    } catch (error) {
      ElMessage.error('配置重置失败')
    } finally {
      loading.value = false
    }
  }

  // 应用配置到列
  const applyConfig = (columns) => {
    if (!config.value) return columns

    const columnMap = new Map(columns.map(c => [c.field, c]))
    const orderedColumns = []

    // 按配置顺序排列
    if (config.value.column_order) {
      for (const field of config.value.column_order) {
        if (columnMap.has(field)) {
          const col = columnMap.get(field)
          // 应用可见性
          if (config.value.columns && config.value.columns[field]) {
            col.visible = config.value.columns[field].visible ?? col.visible
            col.width = config.value.columns[field].width ?? col.width
          }
          orderedColumns.push(col)
          columnMap.delete(field)
        }
      }
    }

    // 添加未配置的列
    for (const col of columnMap.values()) {
      orderedColumns.push(col)
    }

    return orderedColumns
  }

  // 初始化
  if (!columnConfigCache.has(objectCode)) {
    fetchConfig()
  } else {
    config.value = columnConfigCache.get(objectCode)
  }

  return {
    columnConfig: config,
    loading,
    fetchConfig,
    saveConfig,
    resetConfig,
    applyConfig
  }
}
```

### 8.3 BaseTable 组件增强

```vue
<template>
  <div class="base-table-wrapper">
    <!-- 工具栏 -->
    <div class="table-toolbar">
      <slot name="toolbar"></slot>

      <div class="toolbar-right">
        <slot name="toolbar-actions"></slot>

        <!-- 列设置 -->
        <column-manager
          :object-code="objectCode"
          :columns="internalColumns"
          @update:columns="handleColumnsUpdate"
        />

        <!-- 刷新 -->
        <el-button :icon="Refresh" @click="$emit('refresh')" />
      </div>
    </div>

    <!-- 表格 -->
    <el-table
      ref="tableRef"
      :data="data"
      :border="border"
      :stripe="stripe"
      :height="height"
      :max-height="maxHeight"
      :default-sort="defaultSort"
      @sort-change="handleSortChange"
      @column-order-change="handleColumnOrderChange"
      @column-width-change="handleColumnWidthChange"
    >
      <!-- 选择列 -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        :fixed="selectionFixed"
        width="55"
      />

      <!-- 序号列 -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="序号"
        :fixed="indexFixed"
        width="60"
      />

      <!-- 动态列 -->
      <el-table-column
        v-for="column in visibleColumns"
        :key="column.field"
        :prop="column.field"
        :label="column.label"
        :width="column.width"
        :min-width="column.minWidth"
        :max-width="column.maxWidth"
        :fixed="column.fixed"
        :sortable="column.sortable ? 'custom' : false"
        :align="column.align || 'center'"
        :class-name="column.className"
        :label-class-name="column.labelClassName"
      >
        <template #default="{ row, column: col, $index }">
          <slot
            v-if="column.slot"
            :name="column.slot"
            :row="row"
            :column="col"
            :index="$index"
          ></slot>

          <span v-else>
            {{ formatCellValue(row, column) }}
          </span>
        </template>
      </el-table-column>

      <!-- 操作列 -->
      <el-table-column
        v-if="showActions"
        label="操作"
        :fixed="actionsFixed"
        :width="actionsWidth"
      >
        <template #default="{ row, $index }">
          <slot name="actions" :row="row" :index="$index"></slot>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      v-if="showPagination"
      v-model:current-page="internalPage"
      v-model:page-size="internalPageSize"
      :total="total"
      :page-sizes="pageSizes"
      :layout="paginationLayout"
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import ColumnManager from './ColumnManager.vue'
import { useColumnConfig } from '@/composables/useColumnConfig'

const props = defineProps({
  objectCode: {
    type: String,
    required: true
  },
  columns: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  // ... 其他 props
})

const emit = defineEmits(['refresh', 'sort-change', 'page-change', 'size-change'])

const internalColumns = ref([...props.columns])

const {
  columnConfig,
  applyConfig,
  saveConfig
} = useColumnConfig(props.objectCode)

// 应用配置到列
watch(columnConfig, () => {
  if (columnConfig.value) {
    internalColumns.value = applyConfig(props.columns)
  }
}, { immediate: true })

// 可见列
const visibleColumns = computed(() => {
  return internalColumns.value.filter(c => c.visible !== false)
})

const handleColumnsUpdate = (newColumns) => {
  internalColumns.value = newColumns
}

const handleSortChange = (sort) => {
  emit('sort-change', sort)
}

const handleColumnOrderChange = (newOrder) => {
  // 列顺序变化
}

const handleColumnWidthChange = (column, newWidth) => {
  // 列宽变化
  // 可配置自动保存
  saveConfig(internalColumns.value)
}
</script>
```

---

## 9. 后端实现

### 9.1 Serializer

```python
# apps/system/serializers.py
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import UserColumnPreference, RoleColumnPreference, OrganizationColumnPreference

class UserColumnPreferenceSerializer(BaseModelSerializer):
    """用户列配置序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = UserColumnPreference
        fields = BaseModelSerializer.Meta.fields + [
            'user',
            'object_code',
            'column_config',
            'config_name',
            'is_default'
        ]
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RoleColumnPreferenceSerializer(BaseModelSerializer):
    """角色列配置序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = RoleColumnPreference
        fields = BaseModelSerializer.Meta.fields + [
            'role',
            'object_code',
            'column_config',
            'is_active'
        ]


class OrganizationColumnPreferenceSerializer(BaseModelSerializer):
    """组织列配置序列化器"""

    class Meta(BaseModelSerializer.Meta):
        model = OrganizationColumnPreference
        fields = BaseModelSerializer.Meta.fields + [
            'organization',
            'object_code',
            'column_config',
            'is_active'
        ]
```

### 9.2 ViewSet

```python
# apps/system/viewsets.py
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from .models import UserColumnPreference
from .serializers import UserColumnPreferenceSerializer
from .services.column_config_service import ColumnConfigService

class UserColumnPreferenceViewSet(BaseModelViewSet):
    """用户列配置视图集"""

    queryset = UserColumnPreference.objects.all()
    serializer_class = UserColumnPreferenceSerializer

    def get_queryset(self):
        return UserColumnPreference.objects.filter(
            user=self.request.user
        )

    @action(detail=False, methods=['get'], url_path='(?P<object_code>[^/.]+)')
    def get_config(self, request, object_code=None):
        """获取对象的列配置"""
        config = ColumnConfigService.get_column_config(
            request.user,
            object_code
        )
        return Response(BaseResponse.success(data=config))

    @action(detail=False, methods=['post'], url_path='(?P<object_code>[^/.]+)/save')
    def save_config(self, request, object_code=None):
        """保存列配置"""
        pref = ColumnConfigService.save_user_config(
            request.user,
            object_code,
            request.data.get('column_config', {}),
            request.data.get('config_name', 'default')
        )

        serializer = UserColumnPreferenceSerializer(pref)
        return Response(BaseResponse.success(
            data=serializer.data,
            message='配置保存成功'
        ))

    @action(detail=False, methods=['post'], url_path='(?P<object_code>[^/.]+)/reset')
    def reset_config(self, request, object_code=None):
        """重置列配置"""
        success = ColumnConfigService.reset_user_config(
            request.user,
            object_code
        )

        if success:
            return Response(BaseResponse.success(message='配置已重置'))
        else:
            return Response(BaseResponse.error(message='重置失败'))
```

### 9.3 URL 配置

```python
# apps/system/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import UserColumnPreferenceViewSet

router = DefaultRouter()
router.register(r'column-config', UserColumnPreferenceViewSet, basename='column-config')

urlpatterns = [
    path('api/system/', include(router.urls)),
]
```

---

## 10. 使用示例

### 10.1 在列表页中使用

```vue
<template>
  <base-list-page
    :object-code="'asset'"
    :columns="columns"
    :data="tableData"
    @refresh="loadData"
  >
    <template #toolbar>
      <el-input
        v-model="searchForm.keyword"
        placeholder="搜索资产"
        clearable
        @change="loadData"
      />
    </template>

    <template #actions="{ row }">
      <el-button type="primary" link @click="handleView(row)">查看</el-button>
      <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
    </template>
  </base-list-page>
</template>

<script setup>
import { ref } from 'vue'
import BaseListPage from '@/components/common/BaseListPage.vue'

const columns = ref([
  { field: 'asset_code', label: '资产编码', width: 150, sortable: true },
  { field: 'asset_name', label: '资产名称', width: 200 },
  { field: 'category_name', label: '分类', width: 120 },
  { field: 'status', label: '状态', width: 100 },
  { field: 'purchase_price', label: '采购价格', width: 120, align: 'right' },
  { field: 'purchase_date', label: '采购日期', width: 120, sortable: true },
])

const tableData = ref([])

const loadData = async () => {
  // 加载数据
}
</script>
```

### 10.2 默认列配置（PageLayout）

```json
{
  "layout_code": "asset_list_default",
  "layout_name": "资产列表默认布局",
  "layout_type": "list",
  "business_object": "asset",
  "is_default": true,

  "columns": [
    {
      "field": "asset_code",
      "label": "资产编码",
      "width": 150,
      "sortable": true,
      "fixed": "left",
      "visible": true
    },
    {
      "field": "asset_name",
      "label": "资产名称",
      "width": 200,
      "visible": true
    },
    {
      "field": "category_name",
      "label": "分类",
      "width": 120,
      "visible": true
    },
    {
      "field": "status",
      "label": "状态",
      "width": 100,
      "formatType": "status",
      "formatOptions": {
        "statusMap": {
          "active": {"text": "在用", "type": "success"},
          "idle": {"text": "闲置", "type": "info"},
          "scrapped": {"text": "报废", "type": "danger"}
        }
      },
      "visible": true
    },
    {
      "field": "purchase_price",
      "label": "采购价格",
      "width": 120,
      "align": "right",
      "formatType": "currency",
      "formatOptions": {
        "currency": "¥"
      },
      "visible": true
    },
    {
      "field": "actions",
      "label": "操作",
      "width": 150,
      "fixed": "right",
      "visible": true
    }
  ],

  "column_order": [
    "selection",
    "asset_code",
    "asset_name",
    "category_name",
    "status",
    "purchase_price",
    "purchase_date",
    "actions"
  ],

  "table_settings": {
    "stripe": true,
    "border": true,
    "showHeader": true,
    "highlightCurrentRow": true
  },

  "pagination": {
    "show": true,
    "pageSize": 20,
    "pageSizes": [10, 20, 50, 100]
  },

  "defaultSort": {
    "prop": "created_at",
    "order": "descending"
  }
}
```

---

## 总结

本文档定义了 GZEAMS 系统中**列表字段显示管理**的完整规范，包括：

1. **配置层级**：用户级 > 角色级 > 组织级 > 默认级
2. **列显示配置**：可见性、条件可见、响应式可见
3. **列排序配置**：列顺序、拖拽排序、列头数据排序、多列排序
4. **列宽配置**：固定宽度、百分比宽度、自动宽度、宽度调整
5. **列固定配置**：左侧固定、右侧固定、多列固定
6. **用户个性化**：配置模型、配置服务、配置优先级合并
7. **前端实现**：ColumnManager 组件、useColumnConfig Hook、BaseTable 增强
8. **后端实现**：Serializer、ViewSet、Service 层

所有实现均遵循 GZEAMS 技术栈（Django + Vue3 + Element Plus）和项目架构规范。
