# Phase 1.1: 资产分类体系 - 后端实现

## 1. 功能概述与业务场景

### 1.1 业务场景

资产分类是固定资产管理的核心基础模块，主要解决以下业务需求：

1. **标准分类管理**：建立符合国家标准的固定资产分类体系，支持多级分类树形结构
2. **折旧策略配置**：为每个分类配置默认折旧方法、使用年限、净残值率等财务参数
3. **分类统计分析**：按分类维度统计资产数量、价值和折旧情况
4. **自定义扩展**：支持企业在标准分类基础上扩展自定义分类

### 1.2 核心价值

- **统一标准**：基于国标建立分类体系，确保资产管理规范化
- **自动计算**：分类级折旧配置，新资产自动继承折旧参数
- **灵活扩展**：支持标准分类+自定义分类的混合模式
- **数据隔离**：多组织环境下分类数据的完全隔离

---

## 2. 用户角色与权限

| 角色 | 权限范围 | 说明 |
|------|---------|------|
| **系统管理员** | 全部权限 | 可管理所有分类，包括系统预置分类 |
| **资产管理员** | 查看、管理自定义分类 | 只能管理本组织的自定义分类，不能修改系统分类 |
| **普通用户** | 仅查看 | 可查看分类树和分类详情 |
| **财务人员** | 查看、导出 | 可查看分类和导出分类统计报表 |

---

## 3. 公共模型引用声明

本模块完全遵循 **Common Base Features** 规范，所有组件继承公共基类：

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化、custom_fields 展开 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作、已删除记录管理 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 标准 CRUD 方法、复杂查询、分页 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、创建人过滤、软删除状态过滤 |

---

## 4. 数据模型设计

### 4.1 AssetCategory（资产分类）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| **基础信息** |
| code | string | max_length=50, unique, db_index | 分类编码 |
| name | string | max_length=100 | 分类名称 |
| parent_id | uuid | ForeignKey(self) | 上级分类，支持多级分类 |
| **折旧配置** |
| depreciation_method | string | choices[straight_line, double_declining, sum_of_years, no_depreciation], default=straight_line | 折旧方法 |
| default_useful_life | int | default=60 | 使用年限(月)，如60个月=5年 |
| residual_rate | decimal | max_digits=5, decimal_places=2, default=5.00 | 预计净残值率(%)，范围0-100 |
| **分类属性** |
| is_custom | boolean | default=False | 是否自定义（系统预置False，用户自定义True） |
| sort_order | int | default=0 | 排序号，数值越小越靠前 |
| is_active | boolean | default=True | 是否启用（禁用后不可用于新资产） |

*注: 继承 BaseModel 自动获得 organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields*

**数据库索引**:
- `organization + code` (unique where is_deleted=False)
- `organization + parent`
- `organization + is_active`

**核心方法**:
- `full_name` (property): 完整路径名称，如 "电子设备 > 计算机设备 > 笔记本电脑"
- `level` (property): 分类层级，根节点为0
- `has_children` (property): 是否有子分类
- `get_children()`: 获取直接子分类（仅启用的）
- `get_all_children()`: 递归获取所有子孙分类
- `get_ancestors()`: 获取所有祖先分类（路径）
- `delete()`: 重写删除方法，有子分类或关联资产时禁止删除（调用软删除）

### 4.2 数据迁移（添加唯一约束）

**迁移文件**: `apps/assets/migrations/0002_add_category_constraints.py`

| 操作 | 参数 |
|------|------|
| AddConstraint | model_name=assetcategory<br>constraint=UniqueConstraint(fields=['organization', 'code'], condition=Q(is_deleted=False), name='unique_category_code_per_org') |

*依赖*: `0001_initial` (assets), `0001_initial` (organizations)*

---

## 5. API 接口设计

### 5.1 接口概览

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/assets/categories/` | 获取分类列表 | 全部用户 |
| POST | `/api/assets/categories/` | 创建分类 | 管理员 |
| GET | `/api/assets/categories/{id}/` | 获取分类详情 | 全部用户 |
| PUT | `/api/assets/categories/{id}/` | 更新分类 | 管理员 |
| DELETE | `/api/assets/categories/{id}/` | 删除分类 | 管理员 |
| GET | `/api/assets/categories/tree/` | 获取分类树 | 全部用户 |
| GET | `/api/assets/categories/custom/` | 获取自定义分类 | 管理员 |
| POST | `/api/assets/categories/custom/` | 创建自定义分类 | 管理员 |
| POST | `/api/assets/categories/{id}/add_child/` | 添加子分类 | 管理员 |
| GET | `/api/assets/categories/deleted/` | 查询已删除分类 | 管理员 |
| POST | `/api/assets/categories/{id}/restore/` | 恢复已删除分类 | 管理员 |
| POST | `/api/assets/categories/batch-delete/` | 批量删除 | 管理员 |
| POST | `/api/assets/categories/batch-restore/` | 批量恢复 | 管理员 |
| POST | `/api/assets/categories/batch-update/` | 批量更新 | 管理员 |

### 5.2 序列化器设计

#### AssetCategorySerializer

| 字段 | 类型 | 说明 |
|------|------|------|
| **公共字段** (继承 BaseModelSerializer) |
| id, organization, is_deleted, deleted_at | - | 自动序列化 |
| created_at, updated_at, created_by | - | 自动序列化 |
| custom_fields | - | 自动处理 |
| **业务字段** |
| code, name, parent | string/uuid | 基础信息 |
| depreciation_method, default_useful_life, residual_rate | - | 折旧配置 |
| is_custom, sort_order, is_active | - | 分类属性 |
| **计算属性** (read_only) |
| full_name | string | 完整路径名称 |
| level | int | 分类层级 |
| has_children | boolean | 是否有子分类 |

#### AssetCategoryTreeSerializer（递归结构）

| 字段 | 类型 | 说明 |
|------|------|------|
| 包含 AssetCategorySerializer 所有字段 | - | - |
| children | SerializerMethodField | 递归子节点 |

#### AssetCategoryCreateSerializer（带业务验证）

| 验证方法 | 规则 |
|---------|------|
| validate_code() | 同组织下编码唯一性检查 |
| validate_parent() | 禁止自引用、禁止循环引用 |
| validate_residual_rate() | 范围 0-100 |
| validate_default_useful_life() | 必须 ≥ 0 |

*所有序列化器继承 BaseModelSerializer，自动获得公共字段序列化能力*

### 5.3 ViewSet 设计

#### AssetCategoryViewSet

| 继承 | 自动获得功能 |
|------|-------------|
| BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作、审计字段、已删除记录管理 |

**基本配置**:
- `queryset`: AssetCategory.objects.all()
- `serializer_class`: AssetCategorySerializer
- `filterset_class`: AssetCategoryFilter
- `search_fields`: ['code', 'name']
- `ordering_fields`: ['code', 'sort_order', 'created_at']

**序列化器映射** (get_serializer_class):
| action | serializer |
|--------|-----------|
| create, update, partial_update | AssetCategoryCreateSerializer |
| tree | AssetCategoryTreeSerializer |
| 其他 | AssetCategorySerializer |

**自定义接口**:

| 接口 | 方法 | 说明 |
|------|------|------|
| `/tree/` | GET | 获取分类树（使用 CategoryService.get_category_tree()） |
| `/custom/` | GET/POST | 自定义分类管理（使用 CategoryService） |
| `/{id}/add_child/` | POST | 添加子分类（使用 CategoryService.add_child_category()） |
| `destroy()` | DELETE | 重写删除方法，调用模型的业务验证删除 |

**自动获得接口** (继承自 BaseModelViewSetWithBatch):
- `/batch-delete/` - 批量软删除
- `/batch-restore/` - 批量恢复
- `/batch-update/` - 批量更新
- `/deleted/` - 查询已删除记录
- `/{id}/restore/` - 恢复单条记录

### 5.4 过滤器设计

#### AssetCategoryFilter

| 继承 | 自动获得功能 |
|------|-------------|
| BaseModelFilter | 时间范围过滤(created_at, updated_at)、创建人过滤、软删除状态过滤 |

**业务字段过滤**:

| 字段 | 过滤器类型 | 查找方式 | 说明 |
|------|-----------|---------|------|
| code | CharFilter | icontains | 分类编码（模糊） |
| name | CharFilter | icontains | 分类名称（模糊） |
| parent | UUIDFilter | exact | 父分类ID |
| depreciation_method | ChoiceFilter | exact | 折旧方法 |
| is_custom | BooleanFilter | exact | 是否自定义分类 |
| is_active | BooleanFilter | exact | 是否启用 |
| sort_order | NumberFilter | exact | 排序号 |
| level | NumberFilter (自定义) | - | 层级（0=根节点） |

**自定义过滤方法**:
- `filter_level()`: value=0返回根节点(parent__isnull=True)，其他返回非根节点

---

## 6. 服务层设计

### CategoryService

| 继承 | 自动获得功能 |
|------|-------------|
| BaseCRUDService | create(), update(), delete(), restore(), get(), query(), paginate(), batch_delete() |

**核心方法**:

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| get_category_tree() | organization, include_inactive=False | List[Dict] | 获取分类树（嵌套结构） |
| _build_tree_node() | category | Dict | 递归构建树节点（私有） |
| get_custom_categories() | organization | List[AssetCategory] | 获取自定义分类列表 |
| create_custom_category() | data, user, organization | AssetCategory | 创建自定义分类（@transaction.atomic） |
| add_child_category() | parent_id, data, user, organization | AssetCategory | 添加子分类（@transaction.atomic） |
| get_root_categories() | organization | List[AssetCategory] | 获取所有根分类 |
| get_categories_by_depreciation_method() | method, organization | List[AssetCategory] | 根据折旧方法查询分类 |
| export_categories_to_excel() | organization | BytesIO | 导出分类到Excel |

**业务验证规则** (create_custom_category):
- 父分类必须存在且属于当前组织
- 父分类不能是自定义分类（系统分类才能作为父类）
- 分类编码在同组织下必须唯一
- 默认值: depreciation_method='straight_line', default_useful_life=60, residual_rate=5.00

**业务验证规则** (add_child_category):
- 父分类必须存在且属于当前组织
- 分类编码在同组织下必须唯一

**导出字段** (export_categories_to_excel):
- 分类编码、分类名称、完整路径、层级
- 折旧方法、使用年限(月)、净残值率(%)
- 是否自定义、是否启用、排序号

---

## 7. URL 路由配置

```python
# backend/config/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assets.views import AssetCategoryViewSet

router = DefaultRouter()
router.register(
    r'assets/categories',
    AssetCategoryViewSet,
    basename='asset-category'
)

urlpatterns = [
    path('api/', include(router.urls)),
]
```

---

## 8. 数据迁移（预置分类数据）

**迁移文件**: `apps/assets/migrations/0003_load_standard_categories.py`

| 操作 | 说明 |
|------|------|
| RunPython | 执行 load_standard_categories() 函数加载国标分类数据 |

**依赖**: `0001_initial` (organizations), `0002_add_category_constraints` (assets)

**预置分类结构** (国标GB/T 14885):

| 编码 | 名称 | 折旧方法 | 使用年限(月) | 净残值率 | 父分类 |
|------|------|---------|-------------|---------|--------|
| **01 - 土地房屋及构筑物** |
| 01 | 土地房屋及构筑物 | straight_line | 240 | 5.00 | - |
| 0101 | 房屋及建筑物 | straight_line | 240 | 5.00 | 01 |
| 0102 | 土地 | no_depreciation | 0 | 0 | 01 |
| **02 - 通用设备** |
| 02 | 通用设备 | straight_line | 60 | 5.00 | - |
| 0201 | 计算机设备 | straight_line | 60 | 5.00 | 02 |
| 020101 | 台式机 | straight_line | 60 | 5.00 | 0201 |
| 020102 | 笔记本电脑 | straight_line | 60 | 5.00 | 0201 |
| 020103 | 服务器 | straight_line | 60 | 5.00 | 0201 |
| 0202 | 办公设备 | straight_line | 60 | 5.00 | 02 |
| 020201 | 打印机 | straight_line | 60 | 5.00 | 0202 |
| **03 - 专用设备** |
| 03 | 专用设备 | straight_line | 120 | 5.00 | - |
| 0301 | 仪器仪表 | straight_line | 60 | 5.00 | 03 |
| 0302 | 机械设备 | straight_line | 120 | 5.00 | 03 |
| **04 - 交通运输设备** |
| 04 | 交通运输设备 | straight_line | 48 | 5.00 | - |
| 0401 | 车辆 | straight_line | 48 | 5.00 | 04 |

*注: 所有预置分类 is_custom=False, is_active=True*

---

## 9. 测试用例

### 9.1 模型测试

```python
# apps/assets/tests/test_models.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.assets.models import AssetCategory
from apps.organizations.models import Organization


class AssetCategoryModelTest(TestCase):
    """资产分类模型测试"""

    def setUp(self):
        """测试数据准备"""
        self.org = Organization.objects.create(name='测试组织')

    def test_create_root_category(self):
        """测试创建根分类"""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备',
            depreciation_method='straight_line',
            default_useful_life=60,
            residual_rate=5.00
        )

        self.assertEqual(category.code, '01')
        self.assertEqual(category.name, '电子设备')
        self.assertIsNone(category.parent)
        self.assertEqual(category.level, 0)
        self.assertFalse(category.has_children)

    def test_create_child_category(self):
        """测试创建子分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        child = AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=parent
        )

        self.assertEqual(child.level, 1)
        self.assertEqual(child.full_name, '电子设备 > 计算机设备')
        self.assertTrue(parent.has_children)

    def test_full_name_property(self):
        """测试完整路径名称"""
        root = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        child1 = AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=root
        )

        child2 = AssetCategory.objects.create(
            organization=self.org,
            code='010101',
            name='笔记本电脑',
            parent=child1
        )

        expected = '电子设备 > 计算机设备 > 笔记本电脑'
        self.assertEqual(child2.full_name, expected)

    def test_get_ancestors(self):
        """测试获取祖先路径"""
        root = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        child1 = AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=root
        )

        child2 = AssetCategory.objects.create(
            organization=self.org,
            code='010101',
            name='笔记本电脑',
            parent=child1
        )

        ancestors = child2.get_ancestors()
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0], root)
        self.assertEqual(ancestors[1], child1)

    def test_delete_category_with_children(self):
        """测试删除有子分类的分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=parent
        )

        # 尝试删除父分类
        with self.assertRaises(ValidationError) as context:
            parent.delete()

        self.assertIn('子分类', str(context.exception))

    def test_soft_delete(self):
        """测试软删除"""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        # 软删除
        category.soft_delete()

        # 验证软删除标记
        self.assertTrue(category.is_deleted)
        self.assertIsNotNone(category.deleted_at)

        # 验证默认查询不包含已删除记录
        queryset = AssetCategory.objects.filter(id=category.id)
        self.assertNotIn(category, queryset)
```

### 9.2 API 测试

```python
# apps/assets/tests/test_api.py

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.organizations.models import Organization
from apps.assets.models import AssetCategory
from apps.accounts.models import User


class AssetCategoryAPITest(TestCase):
    """资产分类 API 测试"""

    def setUp(self):
        """测试数据准备"""
        self.client = APIClient()

        # 创建测试数据
        self.org = Organization.objects.create(name='测试组织')
        self.user = User.objects.create(
            username='testuser',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_list_categories(self):
        """测试获取分类列表"""
        # 创建测试分类
        AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        url = reverse('assetcategory-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']), 1)

    def test_create_category(self):
        """测试创建分类"""
        url = reverse('assetcategory-list')
        data = {
            'code': '01',
            'name': '电子设备',
            'depreciation_method': 'straight_line',
            'default_useful_life': 60,
            'residual_rate': 5.00
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

        # 验证数据库
        category = AssetCategory.objects.get(code='01')
        self.assertEqual(category.name, '电子设备')

    def test_create_category_duplicate_code(self):
        """测试创建重复编码的分类"""
        # 创建第一个分类
        AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        # 尝试创建重复编码
        url = reverse('assetcategory-list')
        data = {
            'code': '01',
            'name': '办公设备'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_get_category_tree(self):
        """测试获取分类树"""
        # 创建测试分类
        root = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=root
        )

        url = reverse('assetcategory-tree')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        tree = response.data['data']
        self.assertEqual(len(tree), 1)
        self.assertEqual(len(tree[0]['children']), 1)

    def test_create_custom_category(self):
        """测试创建自定义分类"""
        url = reverse('assetcategory-custom')
        data = {
            'code': '99',
            'name': '自定义分类',
            'depreciation_method': 'straight_line'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证自定义标记
        category = AssetCategory.objects.get(code='99')
        self.assertTrue(category.is_custom)

    def test_add_child_category(self):
        """测试添加子分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        url = reverse('assetcategory-add-child', args=[parent.id])
        data = {
            'code': '0101',
            'name': '计算机设备'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 验证父子关系
        child = AssetCategory.objects.get(code='0101')
        self.assertEqual(child.parent, parent)

    def test_delete_category_with_validation(self):
        """测试删除分类（带业务验证）"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=parent
        )

        url = reverse('assetcategory-detail', args=[parent.id])
        response = self.client.delete(url)

        # 应该返回400错误（有子分类）
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_categories(self):
        """测试过滤查询"""
        AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备',
            depreciation_method='straight_line'
        )
        AssetCategory.objects.create(
            organization=self.org,
            code='02',
            name='土地',
            depreciation_method='no_depreciation'
        )

        url = reverse('assetcategory-list')
        response = self.client.get(url, {
            'depreciation_method': 'straight_line'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)
```

### 9.3 服务层测试

```python
# apps/assets/tests/test_services.py

from django.test import TestCase
from apps.assets.services import CategoryService
from apps.organizations.models import Organization
from apps.assets.models import AssetCategory
from apps.accounts.models import User


class CategoryServiceTest(TestCase):
    """分类服务测试"""

    def setUp(self):
        """测试数据准备"""
        self.org = Organization.objects.create(name='测试组织')
        self.user = User.objects.create(
            username='testuser',
            organization=self.org
        )
        self.service = CategoryService()

    def test_get_category_tree(self):
        """测试获取分类树"""
        # 创建测试分类
        root = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        child = AssetCategory.objects.create(
            organization=self.org,
            code='0101',
            name='计算机设备',
            parent=root
        )

        tree = self.service.get_category_tree(organization=self.org)

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['code'], '01')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['code'], '0101')

    def test_create_custom_category(self):
        """测试创建自定义分类"""
        data = {
            'code': '99',
            'name': '自定义分类'
        }

        category = self.service.create_custom_category(
            data=data,
            user=self.user,
            organization=self.org
        )

        self.assertEqual(category.code, '99')
        self.assertTrue(category.is_custom)
        self.assertEqual(category.created_by, self.user)

    def test_create_custom_category_with_duplicate_code(self):
        """测试创建重复编码的自定义分类"""
        AssetCategory.objects.create(
            organization=self.org,
            code='99',
            name='已存在的分类'
        )

        data = {
            'code': '99',
            'name': '自定义分类'
        }

        with self.assertRaises(ValueError) as context:
            self.service.create_custom_category(
                data=data,
                user=self.user,
                organization=self.org
            )

        self.assertIn('已存在', str(context.exception))

    def test_add_child_category(self):
        """测试添加子分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备'
        )

        data = {
            'code': '0101',
            'name': '计算机设备'
        }

        child = self.service.add_child_category(
            parent_id=parent.id,
            data=data,
            user=self.user,
            organization=self.org
        )

        self.assertEqual(child.parent, parent)
        self.assertEqual(child.level, 1)

    def test_get_custom_categories(self):
        """测试获取自定义分类"""
        # 系统分类
        AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='系统分类',
            is_custom=False
        )

        # 自定义分类
        AssetCategory.objects.create(
            organization=self.org,
            code='99',
            name='自定义分类',
            is_custom=True
        )

        customs = self.service.get_custom_categories(organization=self.org)

        self.assertEqual(len(customs), 1)
        self.assertEqual(customs[0].code, '99')

    def test_export_categories_to_excel(self):
        """测试导出分类到Excel"""
        AssetCategory.objects.create(
            organization=self.org,
            code='01',
            name='电子设备',
            depreciation_method='straight_line',
            default_useful_life=60
        )

        output = self.service.export_categories_to_excel(
            organization=self.org
        )

        # 验证返回字节流
        self.assertTrue(len(output.read()) > 0)
```

---

## 10. 实施检查清单

### 10.1 后端实施清单

- [ ] 创建 `AssetCategory` 模型（继承 BaseModel）
- [ ] 创建模型迁移文件（添加唯一约束）
- [ ] 创建 `AssetCategorySerializer`（继承 BaseModelSerializer）
- [ ] 创建 `AssetCategoryTreeSerializer`（递归树形结构）
- [ ] 创建 `AssetCategoryCreateSerializer`（带业务验证）
- [ ] 创建 `AssetCategoryFilter`（继承 BaseModelFilter）
- [ ] 创建 `CategoryService`（继承 BaseCRUDService）
- [ ] 创建 `AssetCategoryViewSet`（继承 BaseModelViewSetWithBatch）
- [ ] 实现 `tree()` 自定义接口
- [ ] 实现 `custom()` 自定义接口
- [ ] 实现 `add_child()` 自定义接口
- [ ] 重写 `destroy()` 方法添加业务验证
- [ ] 配置 URL 路由
- [ ] 创建数据迁移文件（预置国标分类）
- [ ] 执行数据库迁移 `python manage.py migrate`
- [ ] 验证自动获得的接口（批量操作、软删除管理）
- [ ] 编写单元测试（模型、API、服务层）
- [ ] 运行测试并确保全部通过

### 10.2 测试验证清单

- [ ] 模型测试
  - [ ] 创建根分类
  - [ ] 创建子分类
  - [ ] 测试完整路径名称
  - [ ] 测试层级计算
  - [ ] 测试祖先路径
  - [ ] 测试软删除
  - [ ] 测试删除业务验证（有子分类）
- [ ] API 测试
  - [ ] 列表查询
  - [ ] 创建分类
  - [ ] 更新分类
  - [ ] 删除分类（软删除）
  - [ ] 获取分类树
  - [ ] 创建自定义分类
  - [ ] 添加子分类
  - [ ] 过滤查询
  - [ ] 批量操作（删除、恢复、更新）
  - [ ] 已删除记录管理
- [ ] 服务层测试
  - [ ] get_category_tree()
  - [ ] create_custom_category()
  - [ ] add_child_category()
  - [ ] get_custom_categories()
  - [ ] export_categories_to_excel()

---

## 11. 输出产物清单

| 文件路径 | 说明 |
|---------|------|
| `backend/apps/assets/models.py` | AssetCategory 模型（继承 BaseModel） |
| `backend/apps/assets/serializers.py` | 序列化器（继承 BaseModelSerializer） |
| `backend/apps/assets/filters.py` | AssetCategoryFilter（继承 BaseModelFilter） |
| `backend/apps/assets/services/category_service.py` | CategoryService（继承 BaseCRUDService） |
| `backend/apps/assets/views.py` | AssetCategoryViewSet（继承 BaseModelViewSetWithBatch） |
| `backend/config/urls.py` | URL 路由配置 |
| `backend/apps/assets/migrations/0002_add_category_constraints.py` | 添加唯一约束迁移 |
| `backend/apps/assets/migrations/0003_load_standard_categories.py` | 预置国标分类数据 |
| `backend/apps/assets/tests/test_models.py` | 模型单元测试 |
| `backend/apps/assets/tests/test_api.py` | API 集成测试 |
| `backend/apps/assets/tests/test_services.py` | 服务层单元测试 |

---

## 12. 核心优势总结

### 12.1 开箱即用的功能

通过使用公共基类，资产分类模块自动获得：

1. **序列化器自动功能**
   - 自动序列化 BaseModel 的所有公共字段
   - 自动处理组织关联嵌套序列化
   - 自动处理用户信息嵌套序列化
   - 支持 custom_fields 动态字段展开

2. **ViewSet 自动功能**
   - **组织隔离**：自动应用当前组织过滤
   - **软删除**：自动过滤已删除记录，删除时使用软删除
   - **审计字段**：自动设置 created_by、updated_by
   - **批量操作**：开箱即用的批量删除/恢复/更新接口
   - **已删除记录查询**：`/deleted/` 和 `/{id}/restore/` 接口

3. **Service 层自动功能**
   - **CRUD 基础方法**：create、update、delete、restore、get
   - **复杂查询**：query 方法支持过滤、搜索、排序
   - **分页查询**：paginate 方法自动处理分页
   - **批量操作**：batch_delete 方法
   - **组织隔离**：所有操作自动应用组织过滤

4. **过滤器自动功能**
   - 时间范围过滤（created_at、updated_at）
   - 创建人过滤（created_by）
   - 软删除状态过滤（is_deleted）
   - 支持所有标准查询操作符

### 12.2 业务价值

1. **统一标准**：基于国标建立分类体系，确保资产管理规范化
2. **自动计算**：分类级折旧配置，新资产自动继承折旧参数
3. **灵活扩展**：支持标准分类+自定义分类的混合模式
4. **数据隔离**：多组织环境下分类数据的完全隔离
5. **完整性保证**：有子分类或关联资产的分类禁止删除
6. **可追溯性**：完整的审计日志记录所有变更

---

## 13. 后续集成点

1. **资产管理模块（Phase 1.4）**：资产创建时从分类继承折旧参数
2. **折旧计算模块（Phase 5.3）**：按分类折旧方法计算资产折旧
3. **统计报表模块**：按分类维度统计资产数量和价值
4. **数据导出功能**：导出分类树和分类统计报表

---

---

## 14. API接口规范

### 14.1 统一响应格式

本模块遵循GZEAMS统一API响应格式规范。

#### 14.1.1 成功响应
```json
{
    "success": true,
    "message": "操作成功",
    "data": {...}
}
```

#### 14.1.2 列表响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

#### 14.1.3 错误响应
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### 14.2 标准错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| VALIDATION_ERROR | 400 | 验证失败 |
| UNAUTHORIZED | 401 | 未授权 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 已删除 |
| SERVER_ERROR | 500 | 服务器错误 |

**文档版本**: v1.0
**最后更新**: 2026-01-15
**状态**: 已完成重构
