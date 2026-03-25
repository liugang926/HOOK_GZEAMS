# Phase 7.3: 资产标签系统 - 后端实现

## 1. 数据模型设计

### 1.1 TagGroup（标签组）

```python
from apps.common.models import BaseModel

class TagGroup(BaseModel):
    """标签组"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20, default='#409eff')
    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)  # 系统标签组不可删除
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'asset_tag_group'
        ordering = ['sort_order', 'id']
```

### 1.2 AssetTag（资产标签）

```python
class AssetTag(BaseModel):
    """资产标签"""
    tag_group = models.ForeignKey(TagGroup, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=50)
    color = models.CharField(max_length=20, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'asset_tag'
        ordering = ['tag_group', 'sort_order', 'id']
        unique_together = [['tag_group', 'code']]
```

### 1.3 AssetTagRelation（资产标签关联）

```python
class AssetTagRelation(BaseModel):
    """资产标签关联"""
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, related_name='tag_relations')
    tag = models.ForeignKey(AssetTag, on_delete=models.CASCADE, related_name='asset_relations')
    tagged_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    tagged_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'asset_tag_relation'
        unique_together = [['asset', 'tag']]
```

### 1.4 TagAutoRule（自动打标签规则）

```python
class TagAutoRule(BaseModel):
    """自动打标签规则"""
    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=[('condition', '条件规则'), ('schedule', '定时规则')])
    tag = models.ForeignKey(AssetTag, on_delete=models.CASCADE, related_name='auto_rules')
    condition = models.JSONField(default=dict)  # 条件表达式
    schedule = models.CharField(max_length=100, blank=True)  # cron表达式
    is_active = models.BooleanField(default=True)
    last_executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tag_auto_rule'
```

---

## 2. 序列化器

```python
class TagGroupSerializer(BaseModelSerializer):
    """标签组序列化器"""
    tags_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = TagGroup
        fields = BaseModelSerializer.Meta.fields + [
            'name', 'code', 'description', 'color', 'icon',
            'sort_order', 'is_system', 'is_active', 'tags_count'
        ]

    def get_tags_count(self, obj):
        return obj.tags.filter(is_active=True).count()


class AssetTagSerializer(BaseModelSerializer):
    """标签序列化器"""
    group_name = serializers.CharField(source='tag_group.name', read_only=True)
    group_color = serializers.CharField(source='tag_group.color', read_only=True)
    asset_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetTag
        fields = BaseModelSerializer.Meta.fields + [
            'tag_group', 'group_name', 'group_color',
            'name', 'code', 'color', 'icon', 'description',
            'sort_order', 'is_active', 'asset_count'
        ]

    def get_asset_count(self, obj):
        return obj.asset_relations.count()


class AssetTagRelationSerializer(BaseModelSerializer):
    """资产标签关联序列化器"""
    tag_detail = AssetTagSerializer(source='tag', read_only=True)
    tagged_by_detail = UserSerializer(source='tagged_by', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = AssetTagRelation
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'tag', 'tag_detail', 'tagged_by', 'tagged_by_detail',
            'tagged_at', 'notes'
        ]
```

---

## 3. ViewSet

```python
class TagGroupViewSet(BaseModelViewSetWithBatch):
    """标签组ViewSet"""
    queryset = TagGroup.objects.filter(is_active=True)
    serializer_class = TagGroupSerializer
    filterset_class = TagGroupFilter


class AssetTagViewSet(BaseModelViewSetWithBatch):
    """标签ViewSet"""
    queryset = AssetTag.objects.select_related('tag_group').filter(is_active=True)
    serializer_class = AssetTagSerializer
    filterset_class = AssetTagFilter

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """标签统计"""
        from django.db.models import Count

        tags = self.get_queryset().annotate(
            asset_count=Count('asset_relations')
        ).order_by('-asset_count')

        serializer = AssetTagSerializer(tags, many=True)
        return Response({'success': True, 'data': serializer.data})


class AssetTagRelationViewSet(BaseModelViewSetWithBatch):
    """资产标签关联ViewSet"""
    queryset = AssetTagRelation.objects.select_related('asset', 'tag', 'tagged_by')
    serializer_class = AssetTagRelationSerializer
    filterset_class = AssetTagRelationFilter

    @action(detail=False, methods=['post'])
    def batch_add(self, request):
        """批量添加标签"""
        asset_ids = request.data.get('asset_ids', [])
        tag_ids = request.data.get('tag_ids', [])
        notes = request.data.get('notes', '')

        if not asset_ids or not tag_ids:
            return Response({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': '请选择资产和标签'}
            }, status=400)

        results = []
        for asset_id in asset_ids:
            for tag_id in tag_ids:
                relation, created = AssetTagRelation.objects.get_or_create(
                    asset_id=asset_id,
                    tag_id=tag_id,
                    defaults={
                        'tagged_by': request.user,
                        'notes': notes,
                        'organization_id': request.user.organization_id
                    }
                )
                results.append({
                    'asset_id': asset_id,
                    'tag_id': tag_id,
                    'created': created
                })

        return Response({
            'success': True,
            'message': f'处理完成',
            'data': results
        })
```

---

## 4. Service

```python
class AssetTagService(BaseCRUDService):
    """资产标签服务"""

    def add_tags_to_asset(self, asset, tag_ids, user, notes=''):
        """为资产添加标签"""
        relations = []
        for tag_id in tag_ids:
            relation, created = AssetTagRelation.objects.get_or_create(
                asset=asset,
                tag_id=tag_id,
                defaults={
                    'tagged_by': user,
                    'notes': notes,
                    'organization_id': asset.organization_id
                }
            )
            relations.append(relation)
        return relations

    def remove_tags_from_asset(self, asset, tag_ids):
        """移除资产标签"""
        count = AssetTagRelation.objects.filter(
            asset=asset,
            tag_id__in=tag_ids
        ).delete()
        return count

    def get_assets_by_tags(self, tag_ids, organization):
        """按标签获取资产"""
        from django.db.models import Q

        # 每个资产都要包含所有指定标签
        queryset = Asset.objects.filter(
            organization=organization,
            is_deleted=False
        )

        for tag_id in tag_ids:
            queryset = queryset.filter(
                tag_relations__tag_id=tag_id
            )

        return queryset.distinct()

    def get_tag_statistics(self, organization):
        """获取标签统计"""
        from django.db.models import Count

        tags = AssetTag.objects.filter(
            organization=organization,
            is_active=True
        ).annotate(
            asset_count=Count('asset_relations')
        ).order_by('-asset_count')

        return tags
```

---

## 5. 自动化规则

```python
@shared_task
def apply_tag_rules():
    """执行自动打标签规则"""
    from apps.tags.models import TagAutoRule, AssetTagRelation, Asset
    from django.utils import timezone

    rules = TagAutoRule.objects.filter(
        is_active=True,
        rule_type='condition'
    )

    for rule in rules:
        if not rule.condition:
            continue

        # 解析条件并查找匹配的资产
        assets = _evaluate_condition(rule.condition)

        # 为匹配的资产打标签
        count = 0
        for asset in assets:
            relation, created = AssetTagRelation.objects.get_or_create(
                asset=asset,
                tag=rule.tag,
                defaults={
                    'tagged_by': None,
                    'notes': f'自动打标签: {rule.name}',
                    'organization_id': asset.organization_id
                }
            )
            if created:
                count += 1

        rule.last_executed_at = timezone.now()
        rule.save()

    return {'processed': len(rules)}


def _evaluate_condition(condition):
    """评估条件表达式"""
    from apps.assets.models import Asset
    from django.db.models import Q

    queryset = Asset.objects.filter(is_deleted=False)

    # field: operator: value
    # 示例: {"field": "category.name", "operator": "eq", "value": "电子设备"}
    field = condition.get('field')
    operator = condition.get('operator')
    value = condition.get('value')

    # 构建查询
    if operator == 'eq':
        queryset = queryset.filter(**{field: value})
    elif operator == 'gt':
        queryset = queryset.filter(**{f'{field}__gt': value})
    elif operator == 'lt':
        queryset = queryset.filter(**{f'{field}__lt': value})
    elif operator == 'in':
        queryset = queryset.filter(**{f'{field}__in': value})
    elif operator == 'contains':
        queryset = queryset.filter(**{f'{field}__contains': value})

    return queryset
```

---

## 6. API接口

### 6.1 标签组接口

| 接口 | 说明 |
|------|------|
| GET /api/tags/groups/ | 获取标签组列表 |
| POST /api/tags/groups/ | 创建标签组 |
| GET /api/tags/groups/{id}/ | 获取标签组详情 |
| PUT /api/tags/groups/{id}/ | 更新标签组 |
| DELETE /api/tags/groups/{id}/ | 删除标签组 |

### 6.2 标签接口

| 接口 | 说明 |
|------|------|
| GET /api/tags/ | 获取标签列表 |
| POST /api/tags/ | 创建标签 |
| GET /api/tags/statistics/ | 获取标签统计 |
| GET /api/tags/{id}/ | 获取标签详情 |
| PUT /api/tags/{id}/ | 更新标签 |
| DELETE /api/tags/{id}/ | 删除标签 |

### 6.3 资产标签关联接口

| 接口 | 说明 |
|------|------|
| GET /api/assets/{id}/tags/ | 获取资产标签 |
| POST /api/assets/{id}/tags/ | 添加标签 |
| DELETE /api/assets/{id}/tags/{tag_id}/ | 移除标签 |
| POST /api/tags/batch-add/ | 批量添加标签 |
| POST /api/tags/batch-remove/ | 批量移除标签 |
| GET /api/assets/by-tags/ | 按标签查询资产 |

---

## 7. 前端API

```javascript
// frontend/src/api/tags.js
import request from '@/utils/request'

// 标签组
export function getTagGroups(params) {
  return request({ url: '/tags/groups/', method: 'get', params })
}

export function createTagGroup(data) {
  return request({ url: '/tags/groups/', method: 'post', data })
}

// 标签
export function getTags(params) {
  return request({ url: '/tags/', method: 'get', params })
}

export function createTag(data) {
  return request({ url: '/tags/', method: 'post', data })
}

export function getTagStatistics(params) {
  return request({ url: '/tags/statistics/', method: 'get', params })
}

// 资产标签
export function getAssetTags(assetId) {
  return request({ url: `/assets/${assetId}/tags/`, method: 'get' })
}

export function addAssetTag(assetId, data) {
  return request({ url: `/assets/${assetId}/tags/`, method: 'post', data })
}

export function removeAssetTag(assetId, tagId) {
  return request({ url: `/assets/${assetId}/tags/${tagId}/`, method: 'delete' })
}

export function batchAddTags(data) {
  return request({ url: '/tags/batch-add/', method: 'post', data })
}

export function getAssetsByTags(tagIds) {
  return request({ url: '/assets/by-tags/', method: 'post', data: { tag_ids: tagIds } })
}
```

---

## 8. 前端组件

### 8.1 TagSelector

```vue
<template>
  <div class="tag-selector">
    <el-select
      :model-value="modelValue"
      :multiple="multiple"
      :collapse-tags="collapseTags"
      @change="handleChange"
    >
      <el-option-group
        v-for="group in tagGroups"
        :key="group.id"
        :label="group.name"
      >
        <el-option
          v-for="tag in group.tags"
          :key="tag.id"
          :label="tag.name"
          :value="tag.id"
        >
          <span class="tag-option">
            <span
              class="tag-color"
              :style="{ backgroundColor: tag.color || group.color }"
            ></span>
            {{ tag.name }}
          </span>
        </el-option>
      </el-option-group>
    </el-select>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: [Array, String],
  tagGroups: Array,
  multiple: {
    type: Boolean,
    default: true
  },
  collapseTags: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const handleChange = (value) => {
  emit('update:modelValue', value)
}
</script>

<style scoped>
.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
</style>
```

### 8.2 TagFilter

```vue
<template>
  <div class="tag-filter">
    <div class="filter-groups">
      <div
        v-for="group in tagGroups"
        :key="group.id"
        class="filter-group"
      >
        <div class="group-title">{{ group.name }}</div>
        <div class="group-tags">
          <el-checkbox
            v-for="tag in group.tags"
            :key="tag.id"
            :model-value="selectedTags.includes(tag.id)"
            @change="handleTagChange(tag.id)"
          >
            <span
              class="tag-label"
              :style="{ backgroundColor: tag.color || group.color }"
            >
              {{ tag.name }}
            </span>
          </el-checkbox>
        </div>
      </div>
    </div>
    <div class="filter-actions">
      <el-button size="small" @click="handleClear">清空</el-button>
      <el-button type="primary" size="small" @click="handleApply">应用</el-button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  tagGroups: Array
})

const emit = defineEmits(['change'])

const selectedTags = ref([])

const handleTagChange = (tagId) => {
  const index = selectedTags.value.indexOf(tagId)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tagId)
  }
}

const handleClear = () => {
  selectedTags.value = []
  emit('change', [])
}

const handleApply = () => {
  emit('change', selectedTags.value)
}
</script>
```

---

## 9. 初始化数据SQL

```sql
-- 插入预设标签组
INSERT INTO asset_tag_group (id, code, name, description, color, sort_order, is_system, organization_id, created_at, updated_at)
VALUES
  (1, 'usage_status', '使用状态', '资产当前使用状态', '#409eff', 1, true, {org_id}, NOW(), NOW()),
  (2, 'asset_source', '资产来源', '资产来源方式', '#67c23a', 2, true, {org_id}, NOW(), NOW()),
  (3, 'importance', '重要性', '资产重要程度', '#f56c6c', 3, true, {org_id}, NOW(), NOW()),
  (4, 'inventory', '盘点状态', '资产盘点状态', '#e6a23c', 4, true, {org_id}, NOW(), NOW()),
  (5, 'special', '特殊管理', '需要特殊管理的资产', '#909399', 5, true, {org_id}, NOW(), NOW());

-- 插入预设标签
INSERT INTO asset_tag (tag_group_id, code, name, color, sort_order, is_active, organization_id, created_at, updated_at)
VALUES
  -- 使用状态
  (1, 'in_use', '在用', '#409eff', 1, true, {org_id}, NOW(), NOW()),
  (1, 'idle', '闲置', '#909399', 2, true, {org_id}, NOW(), NOW()),
  (1, 'pending_repair', '待维修', '#e6a23c', 3, true, {org_id}, NOW(), NOW()),
  (1, 'pending_scrapped', '待报废', '#f56c6c', 4, true, {org_id}, NOW(), NOW()),

  -- 资产来源
  (2, 'purchased', '采购', '#67c23a', 1, true, {org_id}, NOW(), NOW()),
  (2, 'leased', '租赁', '#e6a23c', 2, true, {org_id}, NOW(), NOW()),
  (2, 'donated', '捐赠', '#409eff', 3, true, {org_id}, NOW(), NOW()),
  (2, 'transferred', '调入', '#909399', 4, true, {org_id}, NOW(), NOW()),

  -- 重要性
  (3, 'critical', '关键', '#f56c6c', 1, true, {org_id}, NOW(), NOW()),
  (3, 'important', '重要', '#e6a23c', 2, true, {org_id}, NOW(), NOW()),
  (3, 'normal', '一般', '#409eff', 3, true, {org_id}, NOW(), NOW()),

  -- 盘点状态
  (4, 'inventoried', '已盘点', '#67c23a', 1, true, {org_id}, NOW(), NOW()),
  (4, 'pending_inventory', '待盘点', '#e6a23c', 2, true, {org_id}, NOW(), NOW()),
  (4, 'surplus', '盘盈', '#f56c6c', 3, true, {org_id}, NOW(), NOW()),
  (4, 'deficit', '盘亏', '#909399', 4, true, {org_id}, NOW(), NOW()),

  -- 特殊管理
  (5, 'need_maintenance', '需维保', '#e6a23c', 1, true, {org_id}, NOW(), NOW()),
  (5, 'need_calibration', '需校准', '#f56c6c', 2, true, {org_id}, NOW(), NOW()),
  (5, 'license_required', '需license', '#409eff', 3, true, {org_id}, NOW(), NOW());
```

---

## 10. 错误码

| 错误码 | 说明 |
|--------|------|
| `TAG_GROUP_NOT_FOUND` | 标签组不存在 |
| `TAG_NOT_FOUND` | 标签不存在 |
| `TAG_ALREADY_EXISTS` | 标签已存在 |
| `SYSTEM_TAG_CANNOT_DELETE` | 系统标签不能删除 |
| `ASSET_TAG_LIMIT_EXCEEDED` | 资产标签数量超过限制 |
