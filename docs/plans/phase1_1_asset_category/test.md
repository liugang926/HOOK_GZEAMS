# Phase 1.1: 资产分类体系 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，先写测试用例，再实现功能，确保可验证性。

---

## 单元测试

### 后端单元测试

```python
# apps/assets/tests/test_category_model.py

from django.test import TestCase
from apps.assets.models import AssetCategory
from apps.organizations.models import Organization


class AssetCategoryModelTest(TestCase):
    """资产分类模型测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')

    def test_create_root_category(self):
        """测试创建根分类"""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='测试分类',
            depreciation_method='straight_line',
            default_useful_life=60
        )

        self.assertEqual(category.code, 'TEST001')
        self.assertEqual(category.name, '测试分类')
        self.assertIsNone(category.parent)
        self.assertEqual(category.level, 0)
        self.assertFalse(category.is_custom)

    def test_create_child_category(self):
        """测试创建子分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='父分类'
        )

        child = AssetCategory.objects.create(
            organization=self.org,
            code='TEST002',
            name='子分类',
            parent=parent
        )

        self.assertEqual(child.parent, parent)
        self.assertEqual(child.level, 1)
        self.assertEqual(child.full_name, '父分类 > 子分类')

    def test_get_children(self):
        """测试获取子分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='父分类'
        )

        child1 = AssetCategory.objects.create(
            organization=self.org,
            code='TEST002',
            name='子分类1',
            parent=parent
        )

        child2 = AssetCategory.objects.create(
            organization=self.org,
            code='TEST003',
            name='子分类2',
            parent=parent
        )

        children = parent.get_children()
        self.assertEqual(children.count(), 2)

    def test_full_name_property(self):
        """测试完整路径名称"""
        grandparent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='一级分类'
        )

        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST002',
            name='二级分类',
            parent=grandparent
        )

        child = AssetCategory.objects.create(
            organization=self.org,
            code='TEST003',
            name='三级分类',
            parent=parent
        )

        self.assertEqual(child.full_name, '一级分类 > 二级分类 > 三级分类')

    def test_unique_code_per_organization(self):
        """测试同一组织内编码唯一"""
        AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='分类1'
        )

        # 同一组织内重复编码应失败
        with self.assertRaises(Exception):
            AssetCategory.objects.create(
                organization=self.org,
                code='TEST001',
                name='分类2'
            )

    def test_soft_delete(self):
        """测试软删除"""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='测试分类'
        )

        category.soft_delete()

        self.assertTrue(category.is_deleted)
        self.assertIsNotNone(category.deleted_at)

        # 软删除后不应出现在正常查询中
        active_categories = AssetCategory.objects.filter(
            organization=self.org,
            is_deleted=False
        )
        self.assertNotIn(category, active_categories)


class AssetCategoryAPITest(TestCase):
    """资产分类API测试"""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.org = Organization.objects.create(name='测试组织')
        self.user = User.objects.create_user(
            username='testuser',
            organization=self.org
        )

        self.client.force_authenticate(user=self.user)

    def test_get_category_tree(self):
        """测试获取分类树"""
        # 创建测试数据
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='父分类'
        )

        AssetCategory.objects.create(
            organization=self.org,
            code='TEST002',
            name='子分类',
            parent=parent
        )

        # 发送请求
        response = self.client.get('/api/assets/categories/tree/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['code'], 'TEST001')
        self.assertEqual(len(data[0]['children']), 1)

    def test_create_category(self):
        """测试创建分类"""
        data = {
            'code': 'TEST003',
            'name': '新分类',
            'depreciation_method': 'straight_line',
            'default_useful_life': 60
        }

        response = self.client.post(
            '/api/assets/categories/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertEqual(result['code'], 'TEST003')
        self.assertEqual(result['name'], '新分类')

    def test_create_custom_category(self):
        """测试创建自定义分类"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='系统分类'
        )

        data = {
            'code': 'CUSTOM001',
            'name': '自定义子分类',
            'parent_id': parent.id
        }

        response = self.client.post(
            '/api/assets/categories/',
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertTrue(result['is_custom'])

    def test_delete_category_with_children_fails(self):
        """测试删除有子分类的分类应失败"""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='TEST001',
            name='父分类'
        )

        AssetCategory.objects.create(
            organization=self.org,
            code='TEST002',
            name='子分类',
            parent=parent
        )

        response = self.client.delete(f'/api/assets/categories/{parent.id}/')

        self.assertEqual(response.status_code, 400)
```

---

## API集成测试

```python
# apps/assets/tests/test_category_api_integration.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.assets.models import AssetCategory
from apps.organizations.models import Organization


class CategoryAPIIntegrationTest(TestCase):
    """分类API集成测试（完整请求-响应循环）"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='测试组织')

        # 创建测试用户并认证
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_full_crud_cycle(self):
        """测试完整CRUD循环"""

        # 1. 创建
        create_response = self.client.post('/api/assets/categories/', {
            'code': 'TEST001',
            'name': '测试分类',
            'depreciation_method': 'straight_line',
            'default_useful_life': 60
        }, format='json')

        self.assertEqual(create_response.status_code, 201)
        category_id = create_response.json()['id']

        # 2. 读取
        get_response = self.client.get(f'/api/assets/categories/{category_id}/')
        self.assertEqual(get_response.status_code, 200)
        category_data = get_response.json()
        self.assertEqual(category_data['code'], 'TEST001')

        # 3. 更新
        update_response = self.client.put(f'/api/assets/categories/{category_id}/', {
            'name': '测试分类（已更新）',
            'default_useful_life': 72
        }, format='json')

        self.assertEqual(update_response.status_code, 200)
        updated_data = update_response.json()
        self.assertEqual(updated_data['name'], '测试分类（已更新）')
        self.assertEqual(updated_data['default_useful_life'], 72)

        # 4. 删除
        delete_response = self.client.delete(f'/api/assets/categories/{category_id}/')
        self.assertEqual(delete_response.status_code, 204)

        # 验证已软删除
        category = AssetCategory.objects.get(id=category_id)
        self.assertTrue(category.is_deleted)
```

---

## 前端组件测试

```vue
<!-- frontend/src/views/assets/__tests__/CategoryManagement.spec.vue -->
<template>
  <div class="test-container">
    <CategoryManagement />
  </div>
</template>

<script setup>
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CategoryManagement from '../CategoryManagement.vue'
import { ElMessage } from 'element-plus'

// Mock API
vi.mock('@/api/assets', () => ({
  getCategoryTree: vi.fn(() => Promise.resolve(mockCategoryTree)),
  createCategory: vi.fn(() => Promise.resolve({ id: 1 })),
  updateCategory: vi.fn(() => Promise.resolve()),
  deleteCategory: vi.fn(() => Promise.resolve())
}))

const mockCategoryTree = [
  {
    id: 1,
    code: '2001',
    name: '计算机设备',
    level: 0,
    is_custom: false,
    children: [
      {
        id: 2,
        code: '200101',
        name: '台式机',
        level: 1,
        is_custom: false,
        children: []
      }
    ]
  }
]

describe('CategoryManagement.vue', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(CategoryManagement, {
      global: {
        stubs: {
          ElPageHeader: true,
          ElCard: true,
          ElTree: true,
          ElForm: true,
          ElFormItem: true,
          ElInput: true,
          ElButton: true,
          ElDialog: true,
          ElEmpty: true
        }
      }
    })
  })

  it('渲染分类管理页面', () => {
    expect(wrapper.find('.category-management').exists()).toBe(true)
  })

  it('加载分类树数据', async () => {
    await wrapper.vm.loadCategoryTree()
    expect(wrapper.vm.categoryTree).toEqual(mockCategoryTree)
  })

  it('点击节点显示详情', async () => {
    await wrapper.vm.loadCategoryTree()
    const node = wrapper.vm.categoryTree[0]
    await wrapper.vm.handleNodeClick(null, node)

    expect(wrapper.vm.selectedCategory).toEqual(node)
    expect(wrapper.vm.isEditMode).toBe(false)
  })

  it('点击编辑进入编辑模式', async () => {
    await wrapper.vm.loadCategoryTree()
    const node = wrapper.vm.categoryTree[0]

    // 模拟点击自定义分类
    const customNode = { ...node, is_custom: true }
    await wrapper.vm.handleEdit(null, customNode)

    expect(wrapper.vm.isEditMode).toBe(true)
  })

  it('保存创建根分类', async () => {
    wrapper.vm.addRootForm = {
      code: 'TEST001',
      name: '测试分类',
      depreciation_method: 'straight_line',
      default_useful_life: 60
    }

    await wrapper.vm.handleSaveAddRoot()

    expect(createCategory).toHaveBeenCalledWith({
      ...wrapper.vm.addRootForm,
      parent_id: null
    })
  })
})
```

---

## E2E测试

```python
# tests/e2e/test_category_e2e.py

from playwright.sync_api import Page, expect


class TestCategoryE2E:
    """资产分类端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        # 登录...
        self.page.goto('http://localhost:5173/assets/categories')

    def test_view_category_tree(self):
        """测试查看分类树"""
        # 等待页面加载
        self.page.wait_for_selector('.category-management')

        # 检查分类树加载
        tree = self.page.locator('.el-tree')
        expect(tree).to_be_visible()

        # 检查根分类存在
        root_nodes = self.page.locator('.custom-tree-node')
        expect(root_nodes.count()).to_be_greater_than(0)

    def test_create_custom_category(self):
        """测试创建自定义分类"""
        # 点击"添加根分类"按钮
        self.page.click('button:has-text("添加根分类")')

        # 填写表单
        self.page.fill('input[placeholder="请输入分类编码"]', 'TEST001')
        self.page.fill('input[placeholder="请输入分类名称"]', '测试分类')
        self.page.select_option('.el-select', label='直线法')

        # 点击确定
        self.page.click('button:has-text("确定")')

        # 等待成功提示
        self.page.wait_for_selector('.el-message--success')

        # 验证新分类出现在树中
        expect(self.page.locator('.el-tree').to_contain_text('测试分类')

    def test_add_child_category(self):
        """测试添加子分类"""
        # 点击某个分类
        self.page.click('.el-tree-node:has-text("计算机设备")')

        # 点击"添加子类"按钮
        self.page.click('button:has-text("添加子类")')

        # 填写表单
        self.page.fill('input[placeholder="请输入分类编码"]', 'TEST002')
        self.page.fill('input[placeholder="请输入分类名称"]', '子分类')

        # 点击确定
        self.page.click('button:has-text("确定")')

        # 等待成功提示
        self.page.wait_for_selector('.el-message--success')

    def test_delete_custom_category(self):
        """测试删除自定义分类"""
        # 先创建一个自定义分类...

        # 点击该分类
        self.page.click('.el-tree-node:has-text("自定义分类")')

        # 点击删除按钮
        self.page.click('button:has-text("删除"):has(.el-tree-node:has-text("自定义分类"))')

        # 确认删除
        self.page.click('.el-button--primary:has-text("确定")')

        # 验证分类已被删除
        expect(self.page.locator('.el-tree')).not_to_contain_text('自定义分类')
```

---

## 验收标准检查清单

### 后端验收

- [ ] 模型 `AssetCategory` 实现完整，包含所有字段
- [ ] `full_name` 属性正确显示完整路径
- [ ] `get_children()` 方法正确返回子分类
- [ ] API 支持 CRUD 操作
- [ ] API 支持 `/tree/` 端点
- [ ] 支持创建自定义分类
- [ ] 系统分类不可编辑/删除
- [ ] 软删除正常工作
- [ ] 单元测试覆盖率 > 80%

### 前端验收

- [ ] 分类树正确展示
- [ ] 可以展开/收起节点
- [ ] 可以选中节点查看详情
- [ ] 可以添加根分类
- [ ] 可以添加子分类
- [ ] 可以编辑自定义分类
- [ ] 可以删除自定义分类
- [ ] 系统分类不显示编辑/删除按钮
- [ ] 操作有成功/失败提示

### 集成验收

- [ ] 后端 API 响应正确
- [ ] 前端正确调用 API
- [ ] 前后端数据格式一致
- [ ] 权限控制正常工作

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.assets.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.assets.tests.test_category_model

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.assets' manage.py test apps.assets.tests

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```

---

## 手动测试步骤

1. **启动系统**
   ```bash
   docker-compose up -d
   ```

2. **登录系统**
   - 访问 http://localhost:5173
   - 使用测试账号登录

3. **测试分类树展示**
   - 进入"资产分类"页面
   - 验证分类树正确显示
   - 验证可以展开/收起节点

4. **测试添加分类**
   - 点击"添加根分类"
   - 填写表单并提交
   - 验证新分类出现在树中

5. **测试添加子分类**
   - 选择一个分类
   - 点击"添加子类"
   - 填写表单并提交
   - 验证子分类出现

6. **测试编辑分类**
   - 选择自定义分类
   - 点击"编辑"
   - 修改信息并保存
   - 验证修改生效

7. **测试删除分类**
   - 选择一个无子节点的自定义分类
   - 点击"删除"
   - 确认删除
   - 验证分类已删除
