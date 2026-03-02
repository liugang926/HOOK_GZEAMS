# Phase 1.1: 资产分类体系 - 实施执行清单

## 一、后端实施清单

### 1.1 模型层 (Models)

**文件路径**: `backend/apps/inventory/models.py` 或 `backend/apps/system/models.py`

- [ ] 创建 `AssetCategory` 模型，继承 `BaseModel`
  ```python
  class AssetCategory(BaseModel):
      code = models.CharField(max_length=50, unique=True)
      name = models.CharField(max_length=200)
      parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
      depreciation_method = models.CharField(max_length=50, choices=DEPRECIATION_METHODS)
      default_useful_life = models.IntegerField(help_text="默认使用年限(月)")
      residual_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="预计净残值率(%)")
      is_custom = models.BooleanField(default=False)
      sort_order = models.IntegerField(default=0)
      is_active = models.BooleanField(default=True)
  ```

- [ ] 定义 `DEPRECIATION_METHODS` 枚举
  ```python
  DEPRECIATION_METHODS = [
      ('straight_line', '直线法'),
      ('double_declining', '双倍余额递减法'),
      ('sum_of_years', '年数总和法'),
      ('no_depreciation', '不计提折旧'),
  ]
  ```

- [ ] 添加模型方法
  - [ ] `get_full_name()` - 获取完整分类名称(含上级)
  - [ ] `get_children()` - 获取子分类
  - [ ] `get_all_descendants()` - 获取所有后代分类
  - [ ] `get_tree_path()` - 获取分类树路径

- [ ] 创建数据库迁移
  ```bash
  docker-compose exec backend python manage.py makemigrations
  docker-compose exec backend python manage.py migrate
  ```

### 1.2 序列化器层 (Serializers)

**文件路径**: `backend/apps/inventory/serializers.py`

- [ ] 创建 `AssetCategoryListSerializer` (列表展示)
  ```python
  class AssetCategoryListSerializer(serializers.ModelSerializer):
      children_count = serializers.SerializerMethodField()
      full_name = serializers.SerializerMethodField()

      class Meta:
          model = AssetCategory
          fields = ['id', 'code', 'name', 'parent_id', 'children_count', 'full_name', 'is_active', 'sort_order']
  ```

- [ ] 创建 `AssetCategoryDetailSerializer` (详情)
- [ ] 创建 `AssetCategoryCreateSerializer` (新增)
- [ ] 创建 `AssetCategoryUpdateSerializer` (更新)
- [ ] 创建 `AssetCategoryTreeSerializer` (树形结构)

### 1.3 视图层 (Views)

**文件路径**: `backend/apps/inventory/views.py`

- [ ] 创建 `AssetCategoryViewSet`
  ```python
  class AssetCategoryViewSet(viewsets.ModelViewSet):
      queryset = AssetCategory.objects.filter(is_deleted=False)
      permission_classes = [IsAuthenticated]
      filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
      filterset_class = AssetCategoryFilter
      search_fields = ['name', 'code']
      ordering_fields = ['sort_order', 'created_at']
      ordering = ['sort_order', 'id']

      def get_serializer_class(self):
          if self.action == 'list':
              return AssetCategoryListSerializer
          if self.action == 'tree':
              return AssetCategoryTreeSerializer
          return AssetCategoryDetailSerializer
  ```

- [ ] 添加自定义Action
  - [ ] `@action(detail=False, methods=['get']) tree` - 获取树形结构
  - [ ] `@action(detail=True, methods=['post']) move` - 移动分类
  - [ ] `@action(detail=False, methods=['get']) statistics` - 分类统计

### 1.4 服务层 (Services)

**文件路径**: `backend/apps/inventory/services/asset_category_service.py`

- [ ] 创建 `AssetCategoryService` 服务类
  ```python
  class AssetCategoryService:
      @staticmethod
      def build_tree(queryset):
          """构建树形结构"""
          ...

      @staticmethod
      def move_category(category, new_parent=None, position=0):
          """移动分类位置"""
          ...

      @staticmethod
      def get_category_statistics(category_id):
          """获取分类统计信息"""
          ...
  ```

### 1.5 路由配置 (URLs)

**文件路径**: `backend/apps/inventory/urls.py`

- [ ] 配置 API 路由
  ```python
  router.register(r'categories', AssetCategoryViewSet, basename='asset-category')
  ```

### 1.6 数据初始化

**文件路径**: `backend/apps/inventory/fixtures/asset_categories.json`

- [ ] 创建预设分类数据文件(国标分类)
  ```python
  # 01 土地房屋及构筑物
  # 02 通用设备
  # 03 专用设备
  # 04 文物和陈列品
  # 05 图书档案
  # 06 家具用具
  ```
- [ ] 创建管理命令加载预设数据
  ```bash
  docker-compose exec backend python manage.py loaddata asset_categories
  ```

---

## 二、前端实施清单

### 2.1 API接口 (api/)

**文件路径**: `frontend/src/api/inventory/assetCategory.js`

- [ ] 创建 `assetCategory.js` API文件
  ```javascript
  import request from '@/api/index'

  export const assetCategoryApi = {
      // 获取分类列表
      list: (params) => request.get('/api/inventory/categories/', { params }),

      // 获取分类树
      tree: () => request.get('/api/inventory/categories/tree/'),

      // 获取分类详情
      detail: (id) => request.get(`/api/inventory/categories/${id}/`),

      // 创建分类
      create: (data) => request.post('/api/inventory/categories/', data),

      // 更新分类
      update: (id, data) => request.put(`/api/inventory/categories/${id}/`, data),

      // 删除分类
      delete: (id) => request.delete(`/api/inventory/categories/${id}/`),

      // 移动分类
      move: (id, data) => request.post(`/api/inventory/categories/${id}/move/`, data),

      // 获取分类统计
      statistics: (id) => request.get(`/api/inventory/categories/${id}/statistics/`)
  }
  ```

### 2.2 状态管理 (stores/)

**文件路径**: `frontend/src/stores/assetCategory.js`

- [ ] 创建 `useAssetCategoryStore` (如需要)
  ```javascript
  export const useAssetCategoryStore = defineStore('assetCategory', {
      state: () => ({
          categoryTree: [],
          currentCategory: null,
          statistics: null
      }),
      actions: {
          async fetchTree() { ... },
          async selectCategory(id) { ... }
      }
  })
  ```

### 2.3 页面组件 (views/)

**文件路径**: `frontend/src/views/inventory/`

- [ ] 创建 `AssetCategoryList.vue` (分类管理页)
  - [ ] 树形分类展示
  - [ ] 分类操作按钮(新增/编辑/删除)
  - [ ] 分类启用/禁用切换
  - [ ] 分类拖拽排序

- [ ] 创建 `AssetCategoryForm.vue` (分类表单)
  - [ ] 基础信息表单
  - [ ] 上级分类选择器
  - [ ] 折旧配置表单
  - [ ] 表单验证规则

### 2.4 公共组件 (components/)

**文件路径**: `frontend/src/components/inventory/`

- [ ] 创建 `CategoryTree.vue` (分类树组件)
  ```vue
  <template>
      <el-tree
          :data="treeData"
          :props="treeProps"
          node-key="id"
          draggable
          @node-drop="handleDrop"
      >
          <template #default="{ node, data }">
              <span class="tree-node">
                  <span>{{ data.code }} {{ data.name }}</span>
                  <span class="actions">
                      <el-button>编辑</el-button>
                      <el-button>删除</el-button>
                  </span>
              </span>
          </template>
      </el-tree>
  </template>
  ```

- [ ] 创建 `DepreciationConfig.vue` (折旧配置组件)
  - [ ] 折旧方法选择
  - [ ] 使用年限输入
  - [ ] 净残值率输入

---

## 三、测试实施清单

### 3.1 单元测试

**文件路径**: `backend/apps/inventory/tests/test_asset_category.py`

- [ ] 模型层测试
  ```python
  def test_asset_category_creation():
      category = AssetCategory.objects.create(code='01', name='测试分类')
      assert category.code == '01'
      assert str(category) == '01 测试分类'
  ```

- [ ] 序列化器测试
  ```python
  def test_category_serializer():
      serializer = AssetCategoryCreateSerializer(data={'code': '01', 'name': '测试'})
      assert serializer.is_valid()
  ```

- [ ] 视图层测试
  ```python
  def test_category_list_api(client):
      response = client.get('/api/inventory/categories/')
      assert response.status_code == 200
  ```

### 3.2 集成测试

- [ ] API接口测试
  - [ ] GET /api/inventory/categories/ - 列表查询
  - [ ] GET /api/inventory/categories/tree/ - 树形结构
  - [ ] POST /api/inventory/categories/ - 创建分类
  - [ ] PUT /api/inventory/categories/{id}/ - 更新分类
  - [ ] DELETE /api/inventory/categories/{id}/ - 删除分类

### 3.3 前端测试

**文件路径**: `frontend/src/views/inventory/__tests__/AssetCategory.spec.js`

- [ ] 组件测试
  ```javascript
  describe('AssetCategoryList', () => {
      it('should render category tree', () => { ... })
      it('should handle create action', () => { ... })
  })
  ```

---

## 四、数据迁移脚本

### 4.1 预设数据

- [ ] 创建 `asset_categories.json` fixture
- [ ] 加载国标一级分类(6个)
- [ ] 验证数据加载成功

---

## 五、执行顺序建议

1. **第一阶段**: 后端模型 + 序列化器
2. **第二阶段**: 后端视图 + API
3. **第三阶段**: 前端API封装
4. **第四阶段**: 前端页面组件
5. **第五阶段**: 测试编写
6. **第六阶段**: 集成联调

---

## 六、参考文件

| 文件 | 路径 |
|------|------|
| PRD总览 | docs/plans/phase1_1_asset_category/overview.md |
| API定义 | docs/plans/phase1_1_asset_category/api.md |
| 后端规范 | docs/plans/phase1_1_asset_category/backend.md |
| 前端规范 | docs/plans/phase1_1_asset_category/frontend.md |
| 测试计划 | docs/plans/phase1_1_asset_category/test.md |
