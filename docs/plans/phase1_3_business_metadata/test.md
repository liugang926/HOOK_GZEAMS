# Phase 1.3: 核心业务单据元数据配置 - 测试验证

## 测试策略

采用**TDD（测试驱动开发）**思路，先写测试用例，确保元数据引擎的可靠性。

---

## 单元测试

### 后端元数据服务测试

```python
# apps/system/tests/test_metadata_service.py

from django.test import TestCase
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.system.services.metadata_service import MetadataService
from apps.organizations.models import Organization


class MetadataServiceTest(TestCase):
    """元数据服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')
        self.service = MetadataService()

    def test_create_business_object(self):
        """测试创建业务对象"""
        data = {
            "code": "TestObject",
            "name": "测试对象",
            "description": "测试描述",
            "enable_workflow": False,
            "fields": [
                {
                    "code": "test_field",
                    "name": "测试字段",
                    "field_type": "text",
                    "is_required": True,
                    "sort_order": 1
                }
            ],
            "page_layouts": [
                {
                    "layout_code": "test_form",
                    "layout_name": "测试表单",
                    "layout_type": "form",
                    "layout_config": {
                        "sections": [
                            {
                                "title": "基础信息",
                                "columns": 1,
                                "fields": ["test_field"]
                            }
                        ]
                    }
                }
            ]
        }

        obj = self.service.create_business_object(data)

        # 验证业务对象
        self.assertEqual(obj.code, "TestObject")
        self.assertEqual(obj.name, "测试对象")
        self.assertFalse(obj.enable_workflow)

        # 验证字段定义
        field = obj.field_definitions.get(code="test_field")
        self.assertEqual(field.name, "测试字段")
        self.assertTrue(field.is_required)

        # 验证页面布局
        layout = obj.page_layouts.get(layout_code="test_form")
        self.assertEqual(layout.layout_type, "form")

    def test_update_existing_business_object(self):
        """测试更新已存在的业务对象"""
        # 先创建
        data = {
            "code": "TestObject",
            "name": "测试对象",
            "fields": [
                {"code": "f1", "name": "字段1", "field_type": "text"}
            ]
        }
        self.service.create_business_object(data)

        # 更新
        update_data = {
            "code": "TestObject",
            "name": "测试对象（已更新）",
            "fields": [
                {"code": "f1", "name": "字段1", "field_type": "text"},
                {"code": "f2", "name": "字段2", "field_type": "number"}
            ]
        }
        obj = self.service.create_business_object(update_data)

        # 验证更新
        self.assertEqual(obj.name, "测试对象（已更新）")
        self.assertEqual(obj.field_definitions.count(), 2)

    def test_get_business_object_with_cache(self):
        """测试缓存机制"""
        data = {
            "code": "CachedObject",
            "name": "缓存测试",
            "fields": []
        }
        self.service.create_business_object(data)

        # 第一次查询 - 从数据库
        obj1 = self.service.get_business_object("CachedObject")
        self.assertIsNotNone(obj1)

        # 第二次查询 - 从缓存
        obj2 = self.service.get_business_object("CachedObject")
        self.assertIs(obj1, obj2)  # 同一个对象引用

    def test_clear_cache(self):
        """测试缓存清除"""
        data = {
            "code": "CachedObject",
            "name": "缓存测试",
            "fields": []
        }
        self.service.create_business_object(data)
        self.service.get_business_object("CachedObject")

        # 清除缓存
        self.service._clear_cache("CachedObject")

        # 验证缓存已清除
        self.assertIsNone(self.service.cache.get("CachedObject"))

    def test_get_field_definitions(self):
        """测试获取字段定义列表"""
        data = {
            "code": "FieldTest",
            "name": "字段测试",
            "fields": [
                {"code": "f1", "name": "字段1", "field_type": "text", "sort_order": 1},
                {"code": "f2", "name": "字段2", "field_type": "number", "sort_order": 2},
            ]
        }
        self.service.create_business_object(data)

        fields = self.service.get_field_definitions("FieldTest")

        self.assertEqual(len(fields), 2)
        self.assertEqual(fields[0].code, "f1")
        self.assertEqual(fields[1].code, "f2")

    def test_delete_business_object(self):
        """测试软删除业务对象"""
        data = {
            "code": "ToDelete",
            "name": "待删除",
            "fields": []
        }
        self.service.create_business_object(data)

        result = self.service.delete_business_object("ToDelete")

        self.assertTrue(result)

        obj = BusinessObject.objects.get(code="ToDelete")
        self.assertTrue(obj.is_deleted)
```

### 动态数据服务测试

```python
# apps/system/tests/test_dynamic_data_service.py

from django.test import TestCase
from apps.system.services.metadata_service import MetadataService
from apps.system.services.dynamic_data_service import DynamicDataService
from apps.organizations.models import Organization


class DynamicDataServiceTest(TestCase):
    """动态数据服务测试"""

    def setUp(self):
        self.org = Organization.objects.create(name='测试组织')

        # 创建测试业务对象
        metadata_service = MetadataService()
        self.bo = metadata_service.create_business_object({
            "code": "TestAsset",
            "name": "测试资产",
            "fields": [
                {"code": "name", "name": "名称", "field_type": "text", "is_required": True},
                {"code": "price", "name": "价格", "field_type": "currency", "decimal_places": 2},
                {"code": "quantity", "name": "数量", "field_type": "number"},
                {"code": "total", "name": "总额", "field_type": "formula", "formula": "{price} * {quantity}"},
                {"code": "status", "name": "状态", "field_type": "select", "options": [
                    {"value": "active", "label": "激活"},
                    {"value": "inactive", "label": "停用"}
                ]}
            ]
        })

        self.service = DynamicDataService("TestAsset")

    def test_create_dynamic_data(self):
        """测试创建动态数据"""
        data = {
            "name": "测试资产1",
            "price": 100.00,
            "quantity": 5,
            "status": "active"
        }

        result = self.service.create(data)

        self.assertIn("id", result)
        self.assertEqual(result["name"], "测试资产1")
        self.assertEqual(result["price"], 100.00)
        self.assertEqual(result["total"], 500.00)  # 公式计算

    def test_create_with_required_field_missing(self):
        """测试缺少必填字段时失败"""
        data = {
            "price": 100.00
        }

        with self.assertRaises(ValueError) as ctx:
            self.service.create(data)

        self.assertIn("必填字段", str(ctx.exception))

    def test_query_with_filters(self):
        """测试带过滤条件的查询"""
        # 创建测试数据
        self.service.create({"name": "资产1", "price": 100, "quantity": 1, "status": "active"})
        self.service.create({"name": "资产2", "price": 200, "quantity": 2, "status": "inactive"})
        self.service.create({"name": "资产3", "price": 100, "quantity": 3, "status": "active"})

        # 查询status=active的数据
        result = self.service.query(filters={"status": "active"})

        self.assertEqual(result["total"], 2)

    def test_query_with_search(self):
        """测试搜索功能"""
        self.service.create({"name": "MacBook Pro", "price": 100, "quantity": 1})
        self.service.create({"name": "Dell 显示器", "price": 200, "quantity": 1})
        self.service.create({"name": "鼠标", "price": 50, "quantity": 1})

        result = self.service.query(search="显示器")

        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["name"], "Dell 显示器")

    def test_query_with_pagination(self):
        """测试分页"""
        for i in range(25):
            self.service.create({"name": f"资产{i}", "price": 100, "quantity": 1})

        result = self.service.query(page=1, page_size=10)

        self.assertEqual(result["total"], 25)
        self.assertEqual(len(result["items"]), 10)
        self.assertEqual(result["page"], 1)

    def test_get_single_data(self):
        """测试获取单条数据"""
        created = self.service.create({"name": "测试", "price": 100, "quantity": 1})
        data_id = created["id"]

        result = self.service.get(data_id)

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "测试")

    def test_update_dynamic_data(self):
        """测试更新动态数据"""
        created = self.service.create({"name": "原名", "price": 100, "quantity": 1})
        data_id = created["id"]

        updated = self.service.update(data_id, {"name": "新名", "price": 200})

        self.assertEqual(updated["name"], "新名")
        self.assertEqual(updated["price"], 200)
        self.assertEqual(updated["total"], 200)  # 公式重新计算

    def test_delete_dynamic_data(self):
        """测试软删除"""
        created = self.service.create({"name": "待删除", "price": 100, "quantity": 1})
        data_id = created["id"]

        result = self.service.delete(data_id)

        self.assertTrue(result)

        # 验证已软删除（无法通过正常查询获取）
        data = self.service.get(data_id)
        self.assertIsNone(data)

    def test_formula_calculation(self):
        """测试公式计算"""
        result = self.service.create({
            "name": "测试",
            "price": 99.99,
            "quantity": 3
        })

        # price * quantity = 99.99 * 3 = 299.97
        self.assertAlmostEqual(result["total"], 299.97, places=2)

    def test_generate_data_no(self):
        """测试生成分编号"""
        result = self.service.create({"name": "测试", "price": 100, "quantity": 1})

        self.assertIn("TESTASSET", result["data_no"])
        self.assertIn("2024", result["data_no"])


class FieldDefinitionTest(TestCase):
    """字段定义模型测试"""

    def test_field_type_choices(self):
        """测试字段类型选项"""
        from apps.system.models import FieldDefinition

        field_types = [choice[0] for choice in FieldDefinition.FIELD_TYPE_CHOICES]

        # 验证包含所有核心类型
        self.assertIn("text", field_types)
        self.assertIn("number", field_types)
        self.assertIn("select", field_types)
        self.assertIn("reference", field_types)
        self.assertIn("formula", field_types)
        self.assertIn("sub_table", field_types)
        self.assertIn("user", field_types)

    def test_unique_field_per_object(self):
        """测试同一业务对象内字段编码唯一"""
        org = Organization.objects.create(name='测试组织')

        metadata_service = MetadataService()
        bo = metadata_service.create_business_object({
            "code": "Test",
            "name": "测试",
            "fields": []
        })

        # 创建第一个字段
        FieldDefinition.objects.create(
            business_object=bo,
            code="unique_field",
            name="字段1",
            field_type="text"
        )

        # 尝试创建重复编码（应该失败）
        with self.assertRaises(Exception):
            FieldDefinition.objects.create(
                business_object=bo,
                code="unique_field",
                name="字段2",
                field_type="text"
            )
```

---

## API集成测试

```python
# apps/system/tests/test_metadata_api.py

from django.test import TestCase
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.system.services.metadata_service import MetadataService


class MetadataAPITest(TestCase):
    """元数据API集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='测试组织')

        self.user = User.objects.create_user(
            username='testuser',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        # 创建测试业务对象
        metadata_service = MetadataService()
        self.bo = metadata_service.create_business_object({
            "code": "APITest",
            "name": "API测试对象",
            "fields": [
                {"code": "title", "name": "标题", "field_type": "text", "is_required": True},
                {"code": "value", "name": "数值", "field_type": "number"}
            ]
        })

    def test_get_business_objects(self):
        """测试获取业务对象列表"""
        response = self.client.get('/api/system/business-objects/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)

    def test_get_business_object_detail(self):
        """测试获取业务对象详情"""
        response = self.client.get(f'/api/system/business-objects/{self.bo.code}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['code'], 'APITest')

    def test_get_field_definitions(self):
        """测试获取字段定义"""
        response = self.client.get('/api/system/field-definitions/', {
            'business_object': 'APITest'
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('fields', data)
        self.assertGreater(len(data['fields']), 0)

    def test_create_dynamic_data(self):
        """测试创建动态数据"""
        response = self.client.post(
            '/api/dynamic/APITest/',
            {
                "title": "测试标题",
                "value": 100
            },
            format='json'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['title'], "测试标题")

    def test_query_dynamic_data(self):
        """测试查询动态数据"""
        # 先创建数据
        self.client.post('/api/dynamic/APITest/', {"title": "测试1", "value": 100})
        self.client.post('/api/dynamic/APITest/', {"title": "测试2", "value": 200})

        # 查询
        response = self.client.get('/api/dynamic/APITest/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['items']), 2)

    def test_get_data_detail(self):
        """测试获取数据详情"""
        create_response = self.client.post(
            '/api/dynamic/APITest/',
            {"title": "详情测试", "value": 100}
        )
        data_id = create_response.json()['id']

        response = self.client.get(f'/api/dynamic/APITest/{data_id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], "详情测试")

    def test_update_data(self):
        """测试更新数据"""
        create_response = self.client.post(
            '/api/dynamic/APITest/',
            {"title": "原标题", "value": 100}
        )
        data_id = create_response.json()['id']

        response = self.client.put(
            f'/api/dynamic/APITest/{data_id}/',
            {"title": "新标题", "value": 200},
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], "新标题")

    def test_delete_data(self):
        """测试删除数据"""
        create_response = self.client.post(
            '/api/dynamic/APITest/',
            {"title": "待删除", "value": 100}
        )
        data_id = create_response.json()['id']

        response = self.client.delete(f'/api/dynamic/APITest/{data_id}/')

        self.assertEqual(response.status_code, 204)

        # 验证已删除
        get_response = self.client.get(f'/api/dynamic/APITest/{data_id}/')
        self.assertEqual(get_response.status_code, 404)
```

---

## 前端组件测试

```vue
<!-- src/components/engine/__tests__/DynamicForm.spec.vue -->
<script setup>
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import DynamicForm from '../DynamicForm.vue'
import { useDynamicForm } from '../hooks/useDynamicForm'

// Mock API
vi.mock('@/api/metadata', () => ({
  getFieldDefinitions: vi.fn(() => Promise.resolve({
    fields: [
      { code: 'name', name: '名称', field_type: 'text', is_required: true },
      { code: 'age', name: '年龄', field_type: 'number' },
      { code: 'status', name: '状态', field_type: 'select', options: [
        { value: 'active', label: '激活' },
        { value: 'inactive', label: '停用' }
      ]}
    ]
  })),
  getPageLayout: vi.fn(() => Promise.resolve({
    layout_config: {
      sections: [
        { title: '基础信息', columns: 1, fields: ['name', 'age', 'status'] }
      ]
    }
  }))
}))

describe('DynamicForm.vue', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(DynamicForm, {
      props: {
        businessObject: 'Test',
        layoutCode: 'form'
      },
      global: {
        stubs: {
          ElForm: true,
          ElFormItem: true,
          ElCard: true,
          ElRow: true,
          ElCol: true
        }
      }
    })
  })

  it('加载元数据后渲染表单', async () => {
    await wrapper.vm.loadMetadata()
    expect(wrapper.vm.fieldDefinitions.length).toBeGreaterThan(0)
  })

  it('初始化表单数据', async () => {
    await wrapper.vm.loadMetadata()
    expect(wrapper.vm.formData).toHaveProperty('name')
    expect(wrapper.vm.formData).toHaveProperty('age')
    expect(wrapper.vm.formData).toHaveProperty('status')
  })

  it('字段值变化触发更新', async () => {
    await wrapper.vm.loadMetadata()
    await wrapper.vm.handleFieldValueChange('name', '新值')

    expect(wrapper.vm.formData.name).toBe('新值')
  })
})
</script>
```

```vue
<!-- src/components/engine/fields/__tests__/SubTableField.spec.vue -->
<script setup>
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SubTableField from '../SubTableField.vue'

describe('SubTableField.vue', () => {
  const field = {
    code: 'items',
    name: '明细',
    field_type: 'sub_table',
    sub_table_fields: [
      { code: 'product', name: '产品', field_type: 'text' },
      { code: 'quantity', name: '数量', field_type: 'number', show_sum: true },
      { code: 'price', name: '单价', field_type: 'number' }
    ]
  }

  it('渲染子表', () => {
    const wrapper = mount(SubTableField, {
      props: {
        field,
        modelValue: [
          { product: '产品A', quantity: 2, price: 100 },
          { product: '产品B', quantity: 3, price: 200 }
        ]
      },
      global: {
        stubs: {
          ElTable: true,
          ElTableColumn: true,
          ElInput: true,
          ElInputNumber: true,
          ElButton: true
        }
      }
    })

    expect(wrapper.vm.localValue.length).toBe(2)
  })

  it('添加新行', () => {
    const wrapper = mount(SubTableField, {
      props: { field, modelValue: [] },
      global: { stubs: { ElTable: true, ElButton: true } }
    })

    wrapper.vm.handleAddRow()

    expect(wrapper.vm.localValue.length).toBe(1)
    expect(wrapper.vm.localValue[0]).toHaveProperty('product')
    expect(wrapper.vm.localValue[0]).toHaveProperty('quantity')
  })

  it('删除行', () => {
    const wrapper = mount(SubTableField, {
      props: {
        field,
        modelValue: [
          { product: '产品A', quantity: 1, price: 100 },
          { product: '产品B', quantity: 2, price: 200 }
        ]
      },
      global: { stubs: { ElTable: true, ElButton: true } }
    })

    wrapper.vm.handleDeleteRow(0)

    expect(wrapper.vm.localValue.length).toBe(1)
    expect(wrapper.vm.localValue[0].product).toBe('产品B')
  })

  it('计算字段合计', () => {
    const wrapper = mount(SubTableField, {
      props: {
        field,
        modelValue: [
          { product: '产品A', quantity: 2, price: 100 },
          { product: '产品B', quantity: 3, price: 200 }
        ]
      },
      global: { stubs: { ElTable: true } }
    })

    const sum = wrapper.vm.getFieldSum('quantity')
    expect(sum).toBe('5.00')
  })
})
</script>
```

---

## E2E测试

```python
# tests/e2e/test_dynamic_form_e2e.py

from playwright.sync_api import Page, expect


class TestDynamicFormE2E:
    """动态表单端到端测试"""

    def setup_method(self):
        self.page = self.browser.new_page()
        self.page.goto('http://localhost:5173/login')
        # 登录...

    def test_create_asset_with_dynamic_form(self):
        """测试使用动态表单创建资产"""
        self.page.goto('http://localhost:5173/assets/new')

        # 等待表单加载
        self.page.wait_for_selector('.dynamic-form')

        # 填写基础信息
        self.page.fill('[name="asset_name"]', '测试资产')
        self.page.select_option('[name="category_id"]', label='计算机设备')

        # 填写财务信息
        self.page.fill('[name="purchase_price"]', '5000')

        # 填写使用信息
        self.page.select_option('[name="custodian_id"]', label='张三')
        self.page.select_option('[name="asset_status"]', label='在用')

        # 提交
        self.page.click('button:has-text("保存")')

        # 验证成功提示
        self.page.wait_for_selector('.el-message--success')
        expect(self.page).to_have_url('http://localhost:5173/assets')

    def test_sub_table_functionality(self):
        """测试子表功能"""
        self.page.goto('http://localhost:5173/pickups/new')

        # 添加子表行
        self.page.click('button:has-text("+ 添加行")')

        # 填写子表数据
        self.page.fill('input[placeholder="资产"]', 'ASSET001')
        self.page.fill('input[placeholder="数量"]', '2')

        # 验证合计更新
        total = self.page.locator('.summary-row td:nth-child(3)')
        expect(total).to_have_text('2')

    def test_formula_field_calculation(self):
        """测试公式字段自动计算"""
        self.page.goto('http://localhost:5173/orders/new')

        # 填写价格和数量
        self.page.fill('[name="price"]', '100')
        self.page.fill('[name="quantity"]', '5')

        # 验证总额自动计算
        total = self.page.locator('[name="total"]').input_value()
        expect(total).toBe('500')
```

---

## 验收标准检查清单

### 后端验收

- [ ] 元数据服务 (MetadataService) 正常工作
- [ ] 动态数据服务 (DynamicDataService) 正常工作
- [ ] 业务对象创建/更新/删除正常
- [ ] 字段定义完整支持所有类型
- [ ] 页面布局配置正确解析
- [ ] 公式字段正确计算
- [ ] 子表数据正确存储和查询
- [ ] JSONB字段查询性能满足要求

### API验收

- [ ] 所有元数据API端点正常响应
- [ ] 所有动态数据API端点正常响应
- [ ] 分页功能正常
- [ ] 搜索功能正常
- [ ] 过滤功能正常
- [ ] 错误处理正确

### 前端验收

- [ ] DynamicForm 组件正确渲染
- [ ] FieldRenderer 正确分发字段
- [ ] 所有字段组件正常工作
- [ ] SubTableField 支持增删改
- [ ] 公式字段实时计算
- [ ] 字段权限正确应用
- [ ] 表单验证正常

---

## 运行测试命令

```bash
# 后端单元测试
docker-compose exec backend python manage.py test apps.system.tests

# 运行特定测试
docker-compose exec backend python manage.py test apps.system.tests.test_metadata_service

# 带覆盖率报告
docker-compose exec backend coverage run --source='apps.system' manage.py test apps.system.tests

# 前端测试
npm run test

# E2E测试
npm run test:e2e
```

---

## 性能测试

```python
# apps/system/tests/test_performance.py

from django.test import TestCase
from apps.system.services.dynamic_data_service import DynamicDataService
from apps.system.services.metadata_service import MetadataService
import time


class MetadataPerformanceTest(TestCase):
    """元数据性能测试"""

    def setUp(self):
        # 创建测试业务对象
        metadata_service = MetadataService()
        self.bo = metadata_service.create_business_object({
            "code": "PerfTest",
            "name": "性能测试",
            "fields": [
                {"code": "name", "name": "名称", "field_type": "text", "is_searchable": True},
                {"code": "value", "name": "数值", "field_type": "number"}
            ]
        })
        self.service = DynamicDataService("PerfTest")

    def test_query_performance_with_large_dataset(self):
        """测试大数据集查询性能"""
        # 创建10000条数据
        for i in range(10000):
            self.service.create({
                "name": f"测试数据{i}",
                "value": i
            })

        # 测试查询性能
        start = time.time()
        result = self.service.query(page=1, page_size=20)
        elapsed = time.time() - start

        # 应在100ms内完成
        self.assertLess(elapsed, 0.1)
        self.assertEqual(len(result['items']), 20)

    def test_search_performance(self):
        """测试搜索性能"""
        # 创建1000条数据
        for i in range(1000):
            self.service.create({
                "name": f"产品{i}",
                "value": i
            })

        start = time.time()
        result = self.service.query(search="产品500")
        elapsed = time.time() - start

        # 搜索应在200ms内完成
        self.assertLess(elapsed, 0.2)
        self.assertEqual(result['total'], 1)
```
