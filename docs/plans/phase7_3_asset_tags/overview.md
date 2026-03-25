# Phase 7.3: 资产标签系统 - 需求概述

## 文档信息

| 项目 | 说明 |
|------|------|
| PRD版本 | v1.0 |
| 创建日期 | 2025-01-20 |
| 模块名称 | 资产标签系统 (AssetTags) |
| 依赖模块 | Phase 1.4 Asset CRUD、Phase 1.3 Business Metadata |

---

## 1. 业务背景与痛点

### 1.1 业务场景

资产分类（一级分类）是固定的，但企业往往需要更灵活的标记方式：

| 场景 | 说明 |
|------|------|
| **多维度标记** | 同一资产可能需要从多个维度标记（如：用途、来源、状态） |
| **临时标记** | 某些标记是临时的（如：待盘点、待维修） |
| **部门自定义** | 不同部门关注的标签维度不同 |
| **快速筛选** | 通过标签组合快速筛选资产 |

### 1.2 现状痛点

| 痛点 | 描述 | 影响 |
|------|------|------|
| **分类不够灵活** | 固定分类树无法满足多维度标记需求 | 检索效率低 |
| **字段扩展受限** | 新增字段需要修改代码 | 维护成本高 |
| **无法组合筛选** | 无法按多个维度组合筛选 | 数据分析困难 |

### 1.3 解决方案

引入标签系统，实现：

1. **自定义标签** - 管理员可创建任意标签和标签组
2. **标签颜色** - 不同颜色区分标签类型/优先级
3. **标签筛选** - 支持多标签组合筛选
4. **标签统计** - 按标签统计资产数量
5. **自动化标签** - 根据条件自动打标签

---

## 2. 用户角色与权限

| 角色 | 权限 |
|------|------|
| **系统管理员** | 创建/编辑/删除标签组、标签，配置自动化规则 |
| **资产管理员** | 创建/编辑标签（限所属组织），给资产打标签 |
| **普通员工** | 查看标签，使用标签筛选 |

---

## 3. 功能范围

### 3.1 功能清单

| 功能模块 | 功能点 | 优先级 |
|---------|-------|-------|
| **标签组管理** | 创建标签组，组织标签 | P0 |
| **标签管理** | 创建标签，设置颜色、图标 | P0 |
| **资产打标签** | 为资产添加/移除标签 | P0 |
| **标签筛选** | 多标签组合筛选资产 | P0 |
| **标签统计** | 按标签统计资产数量 | P1 |
| **自动化规则** | 根据条件自动打标签 | P2 |

---

## 4. 数据模型设计

### 4.1 标签组 (TagGroup)

```python
class TagGroup(BaseModel):
    """标签组"""
    name = models.CharField(max_length=100)  # 标签组名称
    code = models.CharField(max_length=50)    # 编码
    description = models.TextField(blank=True)
    color = models.CharField(max_length=20)   # 默认颜色
    icon = models.CharField(max_length=50, blank=True)
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=False)  # 是否系统标签组
```

### 4.2 标签 (AssetTag)

```python
class AssetTag(BaseModel):
    """资产标签"""
    tag_group = models.ForeignKey(TagGroup)    # 所属标签组
    name = models.CharField(max_length=50)      # 标签名称
    code = models.CharField(max_length=50)      # 编码
    color = models.CharField(max_length=20, blank)  # 颜色
    icon = models.CharField(max_length=50, blank)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
```

### 4.3 资产标签关联 (AssetTagRelation)

```python
class AssetTagRelation(BaseModel):
    """资产标签关联"""
    asset = models.ForeignKey(Asset)
    tag = models.ForeignKey(AssetTag)
    tagged_by = models.ForeignKey(User)
    tagged_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = [['asset', 'tag']]
```

---

## 5. 前端交互设计

### 5.1 标签选择器

```vue
<TagSelector
  v-model="selectedTags"
  :groups="tagGroups"
  :multiple="true"
  :color-picker="true"
/>
```

### 5.2 资产列表标签展示

```vue
<template #tags="{ row }">
  <el-tag
    v-for="tag in row.tags"
    :key="tag.id"
    :color="tag.color"
    size="small"
  >
    {{ tag.name }}
  </el-tag>
</template>
```

### 5.3 标签筛选

```vue
<TagFilter
  v-model="filterTags"
  :groups="tagGroups"
  @change="handleFilterChange"
/>
```

---

## 6. API接口概览

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/tags/groups/ | GET | 获取标签组列表 |
| /api/tags/groups/ | POST | 创建标签组 |
| /api/tags/ | GET | 获取标签列表 |
| /api/tags/ | POST | 创建标签 |
| /api/assets/{id}/tags/ | GET | 获取资产标签 |
| /api/assets/{id}/tags/ | POST | 添加标签 |
| /api/assets/{id}/tags/{tag_id}/ | DELETE | 移除标签 |
| /api/tags/statistics/ | GET | 获取标签统计 |

---

## 7. 自动化规则（可选）

规则类型：
- **条件规则** - 满足条件时自动打标签
  ```
  IF asset.category == '电子设备' AND asset.purchase_price > 10000
  THEN add_tag('高值设备')
  ```

- **时间规则** - 定时触发
  ```
  每月1号：给所有折旧完毕的资产打上 '已提足折旧' 标签
  ```

---

## 8. 预设标签组建议

| 标签组 | 标签示例 | 颜色 |
|--------|---------|------|
| **使用状态** | 在用、闲置、待维修、待报废 | 蓝色系 |
| **资产来源** | 采购、租赁、捐赠、调入 | 绿色系 |
| **重要性** | 关键、重要、一般 | 红色系 |
| **盘点状态** | 已盘点、待盘点、盘盈、盘亏 | 黄色系 |
| **特殊管理** | 需维保、需校准、需 license | 紫色系 |
