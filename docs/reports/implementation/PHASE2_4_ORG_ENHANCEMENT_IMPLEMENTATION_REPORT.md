# Phase 2.4: 组织架构增强模块 - 实现报告

**项目**: GZEAMS - Hook固定资产低代码平台
**阶段**: Phase 2.4 组织架构增强与数据权限
**日期**: 2026-01-16
**状态**: 进行中 (50% 完成)

---

## 执行摘要

本报告详细记录了 Phase 2.4 组织架构增强模块的实现过程。该模块旨在解决当前组织架构存在的痛点，支持一人多部门、部门负责人设置、完整部门路径显示以及基于部门的数据权限控制。

### 核心成果
- ✅ 后端数据模型增强完成
- ✅ 序列化器实现完成
- ✅ 过滤器实现完成
- 🔄 服务层实现中
- ⏳ 视图层待实现
- ⏳ 前端组件待实现

---

## 1. 实现概述

### 1.1 项目背景

**当前痛点**:
- 一人只能属于一个部门，无法处理兼职/借调场景
- 无部门负责人概念，无法按部门分配审批流程
- 部门路径不完整，无法展示完整层级关系
- 无数据权限控制，用户可见范围过大

**目标**:
- 支持一人多部门（UserDepartment关联表）
- 支持部门负责人设置
- 支持完整部门路径显示
- 基于部门的数据权限控制
- 资产操作流程（调拨、归还、借用、领用）

### 1.2 技术栈

**后端**:
- Django 5.0
- Django REST Framework (DRF)
- PostgreSQL (JSONB for dynamic metadata)
- django-mptt (树形结构)

**前端**:
- Vue 3 (Composition API)
- Element Plus UI
- Pinia 状态管理

---

## 2. 后端实现详情

### 2.1 数据模型增强

#### 文件: `backend/apps/organizations/models.py`

##### Department模型增强

**新增字段**:

```python
# 层级字段
level = models.IntegerField(default=0, verbose_name='层级')
path = models.CharField(max_length=500, default='', verbose_name='路径')

# 完整路径显示
full_path = models.CharField(max_length=500, default='', verbose_name='完整路径')
full_path_name = models.CharField(max_length=1000, default='', verbose_name='完整路径名称')

# 部门负责人（重命名自manager）
leader = models.ForeignKey(
    'accounts.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='led_departments',
    verbose_name='部门负责人'
)

# 第三方平台同步ID
wework_dept_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
dingtalk_dept_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)
feishu_dept_id = models.CharField(max_length=50, null=True, blank=True, db_index=True)

# 外部负责人ID（同步时暂存）
wework_leader_id = models.CharField(max_length=64, null=True, blank=True)
dingtalk_leader_id = models.CharField(max_length=64, null=True, blank=True)
feishu_leader_id = models.CharField(max_length=64, null=True, blank=True)

# 排序（重命名自sort_order）
order = models.IntegerField(default=0, verbose_name='排序')
```

**新增方法**:

```python
def save(self, *args, **kwargs):
    """重写save方法，自动更新层级和路径"""
    # 更新层级和路径
    if self.parent:
        self.level = self.parent.level + 1
        self.path = f"{self.parent.path}/{self.code}"
        self.full_path_name = f"{self.parent.full_path_name}/{self.name}"
        self.full_path = f"{self.parent.full_path}/{self.name}"
    else:
        self.level = 0
        self.path = f"/{self.code}"
        self.full_path_name = self.name
        self.full_path = self.name

    super().save(*args, **kwargs)

    # 递归更新子部门路径
    self._update_children_paths()

def _update_children_paths(self):
    """更新子部门的路径"""
    for child in self.children.all():
        child.save(update_fields=['level', 'path', 'full_path', 'full_path_name'])

def get_descendant_ids(self):
    """获取所有后代部门ID"""
    ids = [self.id]
    for child in self.children.all():
        ids.extend(child.get_descendant_ids())
    return ids

def get_member_count(self):
    """获取部门成员数"""
    return UserDepartment.objects.filter(department=self).count()
```

##### UserDepartment模型 (NEW)

**模型定义**:

```python
class UserDepartment(BaseModel):
    """用户部门关联表 - 支持一人多部门"""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='用户'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='user_departments',
        verbose_name='部门'
    )

    # 是否为主部门（用于资产归属）
    is_primary = models.BooleanField(
        default=False,
        verbose_name='是否主部门',
        help_text='主部门用于资产归属'
    )

    # 是否为资产部门
    is_asset_department = models.BooleanField(
        default=False,
        verbose_name='是否资产部门',
        help_text='资产实际所在部门'
    )

    # 职位
    position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='职位'
    )

    # 是否为部门负责人
    is_leader = models.BooleanField(
        default=False,
        verbose_name='是否部门负责人'
    )

    # 企业微信同步字段
    wework_department_order = models.IntegerField(null=True, blank=True)
    is_primary_in_wework = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 确保每个用户在同一组织只有一个主部门
        if self.is_primary:
            UserDepartment.objects.filter(
                user=self.user,
                department__organization=self.department.organization,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
```

**特性**:
- ✅ 支持用户属于多个部门
- ✅ 主部门标识（每个用户在每个组织只有一个主部门）
- ✅ 资产部门标识（用于资产物理位置）
- ✅ 职位和角色跟踪
- ✅ 第三方平台同步支持

---

### 2.2 序列化器实现

#### 文件: `backend/apps/organizations/serializers/department.py`

##### DepartmentSerializer

**继承**: `BaseModelSerializer` (遵循项目规范)

**字段**:

```python
class DepartmentSerializer(BaseModelSerializer):
    leader_name = serializers.CharField(source='leader.username', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = Department
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_name', 'level', 'path',
            'full_path', 'full_path_name', 'leader', 'leader_name',
            'wework_dept_id', 'dingtalk_dept_id', 'feishu_dept_id',
            'wework_leader_id', 'dingtalk_leader_id', 'feishu_leader_id',
            'is_active', 'type', 'phone', 'email', 'description',
            'remark', 'order', 'member_count'
        ]
```

**方法**:

```python
def get_member_count(self, obj):
    """获取部门成员数"""
    return obj.get_member_count()
```

##### DepartmentTreeSerializer

**继承**: `DepartmentSerializer`

**特性**:
- ✅ 递归序列化子部门
- ✅ 使用MPTT树结构
- ✅ 支持无限层级

```python
class DepartmentTreeSerializer(DepartmentSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        """递归获取子部门"""
        children = obj.get_children().filter(is_active=True)
        return DepartmentTreeSerializer(children, many=True).data
```

##### UserDepartmentSerializer

**继承**: `BaseModelSerializer` (遵循项目规范)

**字段**:

```python
class UserDepartmentSerializer(BaseModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_real_name = serializers.CharField(source='user.real_name', read_only=True)
    department_name = serializers.CharField(source='department.full_path_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = UserDepartment
        fields = BaseModelSerializer.Meta.fields + [
            'user', 'user_name', 'user_real_name',
            'department', 'department_name', 'organization', 'organization_name',
            'is_primary', 'is_asset_department', 'position', 'is_leader',
            'wework_department_order', 'is_primary_in_wework'
        ]
```

##### UserDepartmentDetailSerializer

**继承**: `UserDepartmentSerializer`

**特性**:
- ✅ 包含嵌套的详细对象
- ✅ 用户详细信息
- ✅ 部门详细信息

```python
class UserDepartmentDetailSerializer(UserDepartmentSerializer):
    user_detail = serializers.SerializerMethodField()
    department_detail = serializers.SerializerMethodField()

    def get_user_detail(self, obj):
        """获取详细用户信息"""
        return {
            'id': str(obj.user.id),
            'username': obj.user.username,
            'real_name': obj.user.real_name,
            'email': obj.user.email,
            'phone': obj.user.phone,
        }

    def get_department_detail(self, obj):
        """获取详细部门信息"""
        return {
            'id': str(obj.department.id),
            'name': obj.department.name,
            'code': obj.department.code,
            'full_path_name': obj.department.full_path_name,
            'level': obj.department.level,
        }
```

---

### 2.3 过滤器实现

#### 文件: `backend/apps/organizations/filters/department.py`

##### DepartmentFilter

**继承**: `BaseModelFilter` (遵循项目规范)

**支持的过滤**:

```python
class DepartmentFilter(BaseModelFilter):
    # 文本搜索
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.CharFilter(lookup_expr='iexact')
    code_contains = django_filters.CharFilter(lookup_expr='icontains')

    # 部门类型
    type = django_filters.ChoiceFilter(choices=[...])

    # 状态
    is_active = django_filters.BooleanFilter()

    # 层级
    parent = django_filters.UUIDFilter()
    level = django_filters.NumberFilter()

    # 完整路径
    full_path = django_filters.CharFilter(lookup_expr='icontains')

    # 负责人
    leader = django_filters.UUIDFilter()

    # 第三方平台ID
    wework_dept_id = django_filters.CharFilter()
    dingtalk_dept_id = django_filters.CharFilter()
    feishu_dept_id = django_filters.CharFilter()

    # 根部门/叶子部门
    is_root = django_filters.BooleanFilter(method='filter_is_root')
    is_leaf = django_filters.BooleanFilter(method='filter_is_leaf')

    # 全文搜索
    search = django_filters.CharFilter(method='filter_search')
```

**自定义方法**:

```python
def filter_is_root(self, queryset, name, value):
    """过滤根部门"""
    if value is True:
        return queryset.filter(parent__isnull=True)
    elif value is False:
        return queryset.filter(parent__isnull=False)
    return queryset

def filter_is_leaf(self, queryset, name, value):
    """过滤叶子部门"""
    if value is True:
        return queryset.filter(children__isnull=True)
    elif value is False:
        return queryset.filter(children__isnull=False)
    return queryset

def filter_search(self, queryset, name, value):
    """搜索名称、编码或完整路径"""
    return queryset.filter(
        models.Q(name__icontains=value) |
        models.Q(code__icontains=value) |
        models.Q(full_path_name__icontains=value)
    )
```

##### UserDepartmentFilter

**继承**: `BaseModelFilter` (遵循项目规范)

**支持的过滤**:

```python
class UserDepartmentFilter(BaseModelFilter):
    # 用户过滤
    user = django_filters.UUIDFilter()
    user_username = django_filters.CharFilter(lookup_expr='icontains')

    # 部门过滤
    department = django_filters.UUIDFilter()
    department_name = django_filters.CharFilter(lookup_expr='icontains')

    # 标识
    is_primary = django_filters.BooleanFilter()
    is_asset_department = django_filters.BooleanFilter()
    is_leader = django_filters.BooleanFilter()

    # 职位
    position = django_filters.CharFilter(lookup_expr='icontains')

    # 搜索
    search = django_filters.CharFilter(method='filter_search')
```

**自定义方法**:

```python
def filter_search(self, queryset, name, value):
    """搜索用户名、真实姓名、部门名称或职位"""
    return queryset.filter(
        models.Q(user__username__icontains=value) |
        models.Q(user__real_name__icontains=value) |
        models.Q(department__name__icontains=value) |
        models.Q(position__icontains=value)
    )
```

---

## 3. 遵循的项目规范

### 3.1 公共基类继承

✅ **所有组件均继承对应的基类**:

| 组件类型 | 基类 | 用途 |
|---------|------|------|
| Model | `BaseModel` | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | `BaseModelSerializer` | 公共字段序列化、custom_fields序列化 |
| Filter | `BaseModelFilter` | 时间范围过滤、用户过滤 |

### 3.2 自动获得的功能

**从BaseModel继承**:
- ✅ UUID主键
- ✅ 组织隔离 (organization FK)
- ✅ 软删除 (is_deleted, deleted_at)
- ✅ 审计字段 (created_at, updated_at, created_by)
- ✅ 动态字段 (custom_fields JSONB)
- ✅ 自动组织过滤 (TenantManager)

**从BaseModelSerializer继承**:
- ✅ 自动序列化公共字段
- ✅ custom_fields自动序列化
- ✅ created_by嵌套序列化

**从BaseModelFilter继承**:
- ✅ 时间范围过滤 (created_at_from/to, updated_at_from/to)
- ✅ 用户过滤 (created_by)
- ✅ 组织过滤

---

## 4. 文件结构

### 4.1 已创建/修改的文件

```
backend/apps/organizations/
├── models.py                          ✅ 修改 (增强Department + 新增UserDepartment)
├── serializers/
│   ├── __init__.py                    ✅ 修改 (导出新序列化器)
│   └── department.py                  ✅ 修改 (增强序列化器)
└── filters/
    ├── __init__.py                    ✅ 修改 (导出新过滤器)
    └── department.py                  ✅ 修改 (增强过滤器)
```

### 4.2 待创建的文件

```
backend/apps/organizations/
├── services/
│   └── permission_service.py          ⏳ 待创建 (数据权限服务)
└── views.py                           ⏳ 待修改 (新增ViewSet)

frontend/src/
├── api/
│   └── organizations.ts               ⏳ 待创建 (API接口封装)
├── views/
│   └── organizations/
│       ├── DepartmentList.vue         ⏳ 待创建 (部门列表)
│       ├── DepartmentForm.vue         ⏳ 待创建 (部门表单)
│       └── UserDepartmentList.vue     ⏳ 待创建 (用户部门关联)
└── components/
    ├── DepartmentSelector.vue         ⏳ 待创建 (部门选择器)
    └── CustodianSelector.vue          ⏳ 待创建 (保管人选择器)
```

---

## 5. 下一步工作

### 5.1 后端待实现

1. **服务层 (Services)** - 高优先级
   - `OrgDataPermissionService`: 数据权限服务
   - `DepartmentService`: 部门业务逻辑服务
   - `UserDepartmentService`: 用户部门关联服务

2. **视图集 (ViewSets)** - 高优先级
   - `DepartmentViewSet`: 部门CRUD + 树形接口
   - `UserDepartmentViewSet`: 用户部门关联CRUD
   - 自定义action:
     - `/departments/tree/` - 获取完整部门树
     - `/departments/{id}/children/` - 获取子部门
     - `/departments/{id}/users/` - 获取部门用户
     - `/users/{id}/set-primary-department/` - 设置主部门

3. **URL路由配置**
   - 注册新的ViewSet
   - 配置自定义action路由

4. **权限配置**
   - 定义权限代码
   - 配置数据权限规则

### 5.2 前端待实现

1. **API接口封装**
   - `orgApi`: 部门和用户部门关联API

2. **页面组件**
   - `DepartmentList.vue`: 部门列表（树形显示）
   - `DepartmentForm.vue`: 部门编辑表单
   - `UserDepartmentList.vue`: 用户部门关联

3. **公共组件**
   - `DepartmentSelector.vue`: 部门选择器（带完整路径）
   - `CustodianSelector.vue`: 保管人选择器（带部门信息）

4. **路由配置**
   - 组织管理路由

---

## 6. 关键技术决策

### 6.1 为什么使用UserDepartment关联表？

**决策**: 使用显式关联表而非简单FK

**理由**:
- ✅ 支持一人多部门
- ✅ 可以附加额外属性（职位、是否负责人等）
- ✅ 灵活的主部门和资产部门标识
- ✅ 便于追溯历史记录

### 6.2 为什么重命名manager为leader？

**决策**: 统一使用leader术语

**理由**:
- ✅ 与PRD文档一致
- ✅ 语义更清晰（负责人 vs 管理员）
- ✅ 避免与User模型的manager字段混淆

### 6.3 为什么使用full_path_name字段？

**决策**: 存储冗余的完整路径名称

**理由**:
- ✅ 性能优化：避免递归查询
- ✅ 便于显示和搜索
- ✅ 自动维护（save时更新）

### 6.4 为什么继承BaseModel而非手动实现？

**决策**: 严格遵循项目规范，所有组件继承基类

**理由**:
- ✅ 统一的行为模式
- ✅ 自动获得组织隔离和软删除
- ✅ 减少代码重复
- ✅ 便于维护

---

## 7. 测试策略

### 7.1 单元测试

**模型测试**:
- 部门路径自动生成
- 用户部门唯一主部门约束
- 软删除功能
- 层级关系维护

**序列化器测试**:
- 字段验证
- 嵌套序列化
- 自定义方法

**过滤器测试**:
- 各种过滤条件
- 自定义过滤方法
- 组合过滤

### 7.2 集成测试

**API测试**:
- CRUD操作
- 树形结构API
- 批量操作
- 权限检查

### 7.3 端到端测试

**前端测试**:
- 部门列表显示
- 部门创建/编辑
- 用户部门关联
- 权限控制

---

## 8. 风险和挑战

### 8.1 已识别风险

1. **性能风险** ⚠️
   - **风险**: 深层级部门树可能导致递归查询性能问题
   - **缓解**: 使用MPTT优化树查询，考虑路径缓存

2. **数据一致性** ⚠️
   - **风险**: 部门路径更新可能失败导致不一致
   - **缓解**: 使用数据库事务，添加错误处理

3. **权限复杂度** ⚠️
   - **风险**: 数据权限逻辑可能过于复杂
   - **缓解**: 权限规则可配置，添加缓存

### 8.2 待解决问题

1. **部门迁移**: 如何处理用户移动到新部门时的历史记录？
2. **循环引用**: 如何防止部门循环引用（已通过MPTT部分解决）？
3. **并发更新**: 多用户同时修改部门树时的处理？

---

## 9. 性能考虑

### 9.1 数据库优化

**索引**:
```python
indexes = [
    models.Index(fields=['organization', 'code']),
    models.Index(fields=['organization', 'is_active']),
    models.Index(fields=['wework_dept_id']),
    models.Index(fields=['user', 'department']),
    models.Index(fields=['is_primary']),
]
```

**查询优化**:
- 使用`select_related()`减少查询次数
- 使用`prefetch_related()`预取关联对象
- MPTT自动优化树查询

### 9.2 缓存策略

**建议缓存**:
- 部门树结构（高频读取）
- 用户权限信息（会话级别）
- 部门成员数（定期更新）

---

## 10. 结论

Phase 2.4 组织架构增强模块的后端核心功能已实现50%。数据模型、序列化器和过滤器均已完成，严格遵循项目规范。

### 已完成 ✅
1. Department模型增强（层级、路径、负责人、第三方同步）
2. UserDepartment模型（一人多部门支持）
3. 序列化器（继承BaseModelSerializer）
4. 过滤器（继承BaseModelFilter）

### 进行中 🔄
1. 服务层实现

### 待完成 ⏳
1. 视图层和URL路由
2. 前端组件和API集成
3. 测试和文档
4. 部署和上线

---

**报告生成时间**: 2026-01-16
**下次更新**: 视图层和前端组件实现完成后
**维护人**: GZEAMS开发团队
