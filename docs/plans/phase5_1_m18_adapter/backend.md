# Phase 5.1: 万达宝M18适配器 - 后端实现

## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法、组织隔离 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 公共字段过滤 |

---

## 功能概述与业务场景

### 业务背景

万达宝M18是一套成熟的ERP系统，涵盖采购管理、财务核算、库存管理和人力资源等模块。本适配器基于Phase 5.0的通用集成框架实现，专门负责与万达宝M18系统的数据对接，支持采购订单、收货单、供应商主数据等核心业务数据的双向同步。

### 核心业务场景

| 场景 | 说明 | 同步方向 | 优先级 |
|------|------|----------|--------|
| 采购订单同步 | M18采购订单 → 资产系统采购单 | Pull | P0 |
| 收货单同步 | M18收货单 → 资产卡片 + 入库单 | Pull | P0 |
| 供应商主数据同步 | M18供应商 → 资产系统供应商 | Pull | P1 |
| 折旧数据推送 | 资产折旧记录 → M18财务凭证 | Push | P2 |
| 物料主数据同步 | M18物料 → 资产分类/品牌 | Pull | P2 |

### M18系统特点

- **认证方式**: OAuth2 (Client Credentials + Resource Owner Password)
- **API风格**: RESTful API
- **数据格式**: JSON
- **分页方式**: 页码+页大小 (page/pageSize)
- **限流策略**: 100次/分钟（需实现请求队列）

---

## 用户角色与权限

### 角色定义（继承Phase 5.0）

M18适配器使用通用集成框架的角色权限体系，无需额外定义。所有权限控制通过IntegrationConfig的组织隔离和框架的权限管理实现。

**权限说明**：
- 系统管理员和集成管理员：可创建和管理M18集成配置
- 业务用户：可查看M18同步任务和日志
- 审计员：可查看完整的M18集成审计日志

---

## 公共模型引用声明

**本模块严格遵循GZEAMS公共基类架构规范，所有核心组件均继承相应的公共基类。**

M18适配器基于Phase 5.0通用集成框架，所有框架组件（IntegrationConfig、IntegrationSyncTask、IntegrationLog等）已继承公共基类：

| 组件类型 | 基类 | 引用路径 | 使用场景 |
|---------|------|---------|---------|
| **Model** | BaseModel | apps.common.models.BaseModel | 集成配置、同步任务、日志（框架已提供） |
| **Serializer** | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 配置序列化（框架已提供） |
| **ViewSet** | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 配置管理（框架已提供） |
| **Service** | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 业务服务（框架已提供） |
| **Filter** | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 日志查询（框架已提供） |

**M18适配器特有组件**：

本模块新增的M18特定组件同样继承公共基类：

```python
# 示例：M18同步服务（继承BaseCRUDService）
class M18SyncService(BaseCRUDService):
    """M18同步服务 - 继承BaseCRUDService"""
    def __init__(self, config):
        self.config = config
        self.adapter = AdapterFactory.create(config)  # 使用框架工厂
        super().__init__(IntegrationSyncTask)
```

---

## 数据模型设计

### 1. M18特有常量定义

```python
# backend/apps/integration/constants.py (扩展)

class M18APIEndpoint:
    """M18 API端点常量"""
    BASE = '/api'
    OAUTH_TOKEN = '/oauth/token'
    COMPANY_INFO = '/bas/company/current'
    PURCHASE_ORDER = '/po/purchaseOrder'
    GOODS_RECEIPT = '/po/goodsReceipt'
    SUPPLIER = '/bc/supplier'
    MATERIAL = '/bc/material'
    WAREHOUSE = '/wh/warehouse'

class M18SyncBusinessType:
    """M18同步业务类型"""
    PURCHASE_ORDER = 'purchase_order'
    GOODS_RECEIPT = 'goods_receipt'
    SUPPLIER = 'supplier'
    MATERIAL = 'material'
    DEPRECIATION_VOUCHER = 'depreciation_voucher'
```

### 2. M18数据映射模板（预定义）

```python
# backend/apps/integration/mappings/m18_default_mappings.py

M18_PURCHASE_ORDER_MAPPING = {
    'field_mappings': {
        # 基础字段映射
        'po_code': 'poNo',
        'supplier_code': 'supplierCode',
        'supplier_name': 'supplierName',
        'order_date': 'orderDate',
        'delivery_date': 'deliveryDate',
        'total_amount': 'totalAmount',
        'currency': 'currency',
        'status': 'status',
        'remark': 'remark',
        # 明细映射
        'items': 'lineItems',
        'item_line_no': 'lineNo',
        'item_material_code': 'materialCode',
        'item_material_name': 'materialName',
        'item_quantity': 'quantity',
        'item_unit': 'unit',
        'item_price': 'unitPrice',
        'item_amount': 'amount'
    },
    'value_mappings': {
        'status': {
            '1': 'draft',        # 草稿
            '2': 'submitted',    # 已提交
            '3': 'approved',     # 已审核
            '4': 'closed',       # 已关闭
            '5': 'cancelled'     # 已取消
        }
    },
    'transform_rules': [
        {
            'field': 'order_date',
            'type': 'date_format',
            'from_format': 'YYYYMMDD',
            'to_format': 'YYYY-MM-DD'
        }
    ]
}

M18_GOODS_RECEIPT_MAPPING = {
    'field_mappings': {
        'receipt_code': 'grNo',
        'po_code': 'poNo',
        'receipt_date': 'receiptDate',
        'supplier_code': 'supplierCode',
        'warehouse_code': 'warehouseCode',
        'items': 'lineItems',
        'item_line_no': 'lineNo',
        'item_material_code': 'materialCode',
        'item_actual_qty': 'actualQty',
        'item_location': 'location'
    }
}

M18_SUPPLIER_MAPPING = {
    'field_mappings': {
        'supplier_code': 'supplierCode',
        'supplier_name': 'supplierName',
        'contact': 'contact',
        'phone': 'phone',
        'email': 'email',
        'address': 'address',
        'tax_number': 'taxNo'
    }
}
```

**注意**：模型定义（IntegrationConfig、IntegrationSyncTask、IntegrationLog）已在Phase 5.0框架中提供，M18适配器无需新增模型，仅使用框架提供的模型和预定义的映射模板。

---

## API接口设计

### 标准 CRUD 端点（继承 BaseModelViewSet 自动提供）

详见 `common_base_features/api.md` 中的标准 API 规范。

M18适配器使用框架提供的IntegrationConfig、IntegrationSyncTask、IntegrationLog模型，均继承自BaseModel，因此自动获得以下标准端点：

**集成配置标准端点**：
- `GET /api/integration/configs/` - 列表查询（分页、过滤、搜索）
- `GET /api/integration/configs/{id}/` - 获取单条记录
- `POST /api/integration/configs/` - 创建新记录
- `PUT /api/integration/configs/{id}/` - 完整更新
- `PATCH /api/integration/configs/{id}/` - 部分更新
- `DELETE /api/integration/configs/{id}/` - 软删除
- `GET /api/integration/configs/deleted/` - 查看已删除记录
- `POST /api/integration/configs/{id}/restore/` - 恢复已删除记录

**批量操作端点**：
- `POST /api/integration/configs/batch-delete/` - 批量软删除
- `POST /api/integration/configs/batch-restore/` - 批量恢复
- `POST /api/integration/configs/batch-update/` - 批量更新

**同步任务标准端点**：
- `GET /api/integration/sync-tasks/` - 列表查询（通过system_type=m18过滤）
- `GET /api/integration/sync-tasks/{id}/` - 获取单条记录
- 以及其他标准CRUD和批量操作端点

**集成日志标准端点**：
- `GET /api/integration/logs/` - 列表查询（通过system_type=m18过滤）
- `GET /api/integration/logs/{id}/` - 获取单条记录
- 以及其他标准CRUD和批量操作端点

**标准响应格式**：
- 成功响应：`{success: true, message: "...", data: {...}}`
- 列表响应：`{success: true, data: {count, next, previous, results}}`
- 错误响应：`{success: false, error: {code, message, details}}`
- 批量操作响应：`{success/failed, message, summary: {total, succeeded, failed}, results: [...]}`

**标准错误码**：
- `VALIDATION_ERROR` (400) - 请求数据验证失败
- `UNAUTHORIZED` (401) - 未授权访问
- `PERMISSION_DENIED` (403) - 权限不足
- `NOT_FOUND` (404) - 资源不存在
- `ORGANIZATION_MISMATCH` (403) - 组织不匹配
- `SOFT_DELETED` (410) - 资源已删除
- `SERVER_ERROR` (500) - 服务器内部错误

### 1. M18专用API端点

#### 1.1 测试M18连接

```http
POST /api/integration/configs/{id}/test_connection/
```

**功能**：使用框架提供的测试接口，M18适配器自动实现M18特定的测试逻辑（调用公司信息API）。

**响应示例**：

```json
{
    "success": true,
    "message": "连接成功",
    "data": {
        "response_time_ms": 245,
        "details": {
            "company_name": "示例公司",
            "api_version": "2.0",
            "server_time": "2024-01-15T10:30:00Z"
        }
    }
}
```

**错误响应示例**：

```json
{
    "success": false,
    "error": {
        "code": "SERVER_ERROR",
        "message": "M18连接失败",
        "details": {
            "error_code": "AUTH_FAILED",
            "error_message": "认证失败，请检查用户名和密码"
        }
    }
}
```

#### 1.2 手动触发M18采购订单同步

```http
POST /api/integration/configs/{id}/sync_now/
Content-Type: application/json

{
    "sync_params": {
        "module_type": "procurement",
        "direction": "pull",
        "business_type": "purchase_order",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    }
}
```

**响应示例**：

```json
{
    "success": true,
    "message": "同步任务已创建",
    "data": {
        "task_id": "sync-task-uuid-xxx",
        "status": "pending"
    }
}
```

#### 1.3 查询M18同步日志

```http
GET /api/integration/logs/?system_type=m18&business_type=purchase_order&created_at_from=2024-01-01
```

**使用框架提供的日志查询接口**，通过system_type=m18过滤M18相关日志。

---

## 前端组件设计

### 1. M18配置表单扩展

**路由**：`/integration/configs/create?system_type=m18`

**组件位置**：`frontend/src/views/integration/M18ConfigForm.vue`

**功能特性**：

基于框架的通用配置表单，扩展M18特定字段：

```vue
<template>
  <el-form :model="form" :rules="rules" ref="formRef">
    <!-- M18连接配置 -->
    <el-form-item label="API地址" prop="connection_config.api_url">
      <el-input v-model="form.connection_config.api_url" placeholder="https://m18.example.com/api" />
    </el-form-item>

    <el-form-item label="用户名" prop="connection_config.username">
      <el-input v-model="form.connection_config.username" />
    </el-form-item>

    <el-form-item label="密码" prop="connection_config.password">
      <el-input v-model="form.connection_config.password" type="password" show-password />
    </el-form-item>

    <el-form-item label="客户端ID" prop="connection_config.client_id">
      <el-input v-model="form.connection_config.client_id" placeholder="GZEAMS" />
    </el-form-item>

    <!-- 测试连接按钮 -->
    <el-form-item>
      <el-button @click="testConnection" :loading="testing">
        测试连接
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref } from 'vue'
import { testConnectionAPI } from '@/api/integration'

const testing = ref(false)

const testConnection = async () => {
  testing.value = true
  try {
    const result = await testConnectionAPI(form.value)
    ElMessage.success(`连接成功: ${result.details.company_name}`)
  } catch (error) {
    ElMessage.error('连接失败: ' + error.message)
  } finally {
    testing.value = false
  }
}
</script>
```

### 2. M18同步任务监控

**路由**：`/integration/m18/tasks`

**组件位置**：`frontend/src/views/integration/M18SyncTasks.vue`

**功能特性**：
- 显示M18相关同步任务（system_type=m18）
- 支持按业务类型过滤（采购订单、收货单、供应商等）
- 实时显示同步进度
- 错误详情展示

### 3. M18数据映射配置界面

**路由**：`/integration/configs/:id/mappings?system_type=m18`

**组件位置**：`frontend/src/views/integration/M18MappingConfig.vue`

**功能特性**：
- 预加载M18默认映射模板
- 可视化编辑字段映射关系
- 测试映射转换结果

---

## 测试用例

### 1. M18适配器单元测试

```python
# backend/apps/integration/tests/test_m18_adapter.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
class TestM18Adapter:
    """M18适配器单元测试"""

    def test_adapter_initialization(self, organization, user):
        """测试适配器初始化"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            connection_config={
                'api_url': 'https://test.m18.com/api',
                'username': 'test_user',
                'password': 'test_pass',
                'client_id': 'GZEAMS'
            },
            created_by=user
        )

        adapter = M18Adapter(config)

        assert adapter.adapter_type == 'm18'
        assert adapter.adapter_name == '万达宝M18'
        assert adapter.config == config

    @patch('apps.integration.adapters.m18_adapter.requests.post')
    def test_oauth_authentication(self, mock_post, organization, user):
        """测试OAuth认证"""
        # Mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_token',
            'expires_in': 7200
        }
        mock_post.return_value = mock_response

        # 创建适配器
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            connection_config={
                'api_url': 'https://test.m18.com/api',
                'username': 'test_user',
                'password': 'test_pass'
            },
            created_by=user
        )

        adapter = M18Adapter(config)
        token = adapter._get_token()

        assert token == 'test_token'
        mock_post.assert_called_once()

    @patch('apps.integration.adapters.m18_adapter.requests.get')
    def test_pull_purchase_orders(self, mock_get, organization, user):
        """测试拉取采购订单"""
        # Mock响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'poNo': 'PO001',
                    'supplierCode': 'S001',
                    'orderDate': '20240115',
                    'totalAmount': 10000.00,
                    'status': '3'
                }
            ]
        }
        mock_get.return_value = mock_response

        # 创建适配器
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            connection_config={
                'api_url': 'https://test.m18.com/api'
            },
            created_by=user
        )

        adapter = M18Adapter(config)
        orders = adapter.pull_purchase_orders(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert len(orders) == 1
        assert orders[0]['poNo'] == 'PO001'

    def test_map_purchase_order_to_local(self, organization, user):
        """测试采购订单映射到本地格式"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            created_by=user
        )

        # 创建映射模板
        DataMappingTemplate.objects.create(
            organization=organization,
            system_type='m18',
            business_type='purchase_order',
            template_name='M18采购订单映射',
            field_mappings=M18_PURCHASE_ORDER_MAPPING['field_mappings'],
            value_mappings=M18_PURCHASE_ORDER_MAPPING['value_mappings']
        )

        adapter = M18Adapter(config)

        # M18格式数据
        m18_data = {
            'poNo': 'PO001',
            'supplierCode': 'S001',
            'supplierName': '测试供应商',
            'orderDate': '20240115',
            'totalAmount': 10000.00,
            'status': '3'
        }

        # 映射到本地格式
        local_data = adapter.map_to_local('purchase_order', m18_data)

        assert local_data['po_code'] == 'PO001'
        assert local_data['supplier_code'] == 'S001'
        assert local_data['order_date'] == '2024-01-15'
        assert local_data['status'] == 'approved'
```

### 2. M18同步服务集成测试

```python
# backend/apps/integration/tests/test_m18_sync.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.services.m18_sync_service import M18SyncService
from apps.procurement.models import PurchaseOrder, Supplier


@pytest.mark.django_db
class TestM18SyncService:
    """M18同步服务集成测试"""

    @patch('apps.integration.factory.AdapterFactory.create')
    def test_sync_purchase_orders(self, mock_adapter_factory, organization, user, integration_config):
        """测试同步采购订单"""
        # Mock适配器
        mock_adapter = Mock()
        mock_adapter.pull_purchase_orders.return_value = [
            {
                'poNo': 'PO001',
                'supplierCode': 'S001',
                'orderDate': '20240115',
                'totalAmount': 10000.00,
                'status': '3'
            }
        ]
        mock_adapter.map_to_local.return_value = {
            'po_code': 'PO001',
            'supplier_code': 'S001',
            'order_date': '2024-01-15',
            'total_amount': 10000.00,
            'status': 'approved'
        }
        mock_adapter_factory.return_value = mock_adapter

        # 创建供应商
        Supplier.objects.create(
            organization=organization,
            supplier_code='S001',
            supplier_name='测试供应商',
            created_by=user
        )

        # 执行同步
        service = M18SyncService(integration_config)
        result = service.sync_purchase_orders(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert result['total'] == 1
        assert result['success'] == 1
        assert result['failed'] == 0

        # 验证本地订单已创建
        assert PurchaseOrder.objects.filter(po_code='PO001').exists()

    @patch('apps.integration.factory.AdapterFactory.create')
    def test_sync_suppliers(self, mock_adapter_factory, organization, user, integration_config):
        """测试同步供应商"""
        # Mock适配器
        mock_adapter = Mock()
        mock_adapter.pull_suppliers.return_value = [
            {
                'supplierCode': 'S001',
                'supplierName': '测试供应商',
                'contact': '张三',
                'phone': '13800138000',
                'email': 'test@example.com'
            }
        ]
        mock_adapter.map_to_local.return_value = {
            'supplier_code': 'S001',
            'supplier_name': '测试供应商',
            'contact': '张三',
            'phone': '13800138000',
            'email': 'test@example.com'
        }
        mock_adapter_factory.return_value = mock_adapter

        # 执行同步
        service = M18SyncService(integration_config)
        result = service.sync_suppliers()

        assert result['total'] == 1
        assert result['success'] == 1

        # 验证本地供应商已创建
        assert Supplier.objects.filter(supplier_code='S001').exists()
```

### 3. M18 Celery任务测试

```python
# backend/apps/integration/tests/test_m18_tasks.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.tasks.m18_tasks import sync_m18_purchase_orders


@pytest.mark.django_db
class TestM18CeleryTasks:
    """M18 Celery异步任务测试"""

    @patch('apps.integration.tasks.m18_tasks.M18SyncService')
    def test_sync_purchase_orders_task(self, mock_service_class, organization, user, integration_config):
        """测试采购订单同步Celery任务"""
        # Mock服务
        mock_service = Mock()
        mock_service.sync_purchase_orders.return_value = {
            'total': 50,
            'success': 48,
            'failed': 2,
            'errors': [
                {'po_no': 'PO049', 'error': '供应商不存在'}
            ]
        }
        mock_service_class.return_value = mock_service

        # 执行任务
        result = sync_m18_purchase_orders(
            config_id=str(integration_config.id),
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert result['total'] == 50
        assert result['success'] == 48
        assert result['failed'] == 2
```

---

## 后续任务

1. **Phase 5.2**: 实现财务凭证集成（基于通用框架）
   - 凭证格式定义
   - 折旧数据推送到M18
   - 凭证状态同步

2. **Phase 5.3**: 实现其他ERP适配器（SAP、金蝶、用友等）

---

## 附录：M18适配器实现要点

### A.1 M18 OAuth2认证流程

```python
def _get_token(self) -> str:
    """获取M18访问令牌（OAuth2）"""
    # 如果token未过期，直接返回
    if self._access_token and self._token_expires_at:
        if datetime.now() < self._token_expires_at:
            return self._access_token

    # 获取新token
    base_url = self.connection_config.get('api_url', '').rstrip('/')
    url = f"{base_url}/oauth/token"

    response = requests.post(
        url,
        json={
            'username': self.connection_config.get('username'),
            'password': self.connection_config.get('password'),
            'grant_type': 'password',
            'client_id': self.connection_config.get('client_id', 'GZEAMS')
        },
        headers={'Content-Type': 'application/json'},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        self._access_token = data.get('access_token')
        expires_in = data.get('expires_in', 3600)
        self._token_expires_at = datetime.now().timestamp() + expires_in - 60
        return self._access_token

    raise Exception(f"获取M18 token失败: {response.text}")
```

### A.2 M18分页查询处理

```python
def pull_purchase_orders(
    self,
    start_date: str = None,
    end_date: str = None,
    status: str = None
) -> List[Dict]:
    """拉取采购订单（自动分页）"""
    all_orders = []
    page = 1
    page_size = 100  # M18默认分页大小

    while True:
        params = {
            'page': page,
            'pageSize': page_size
        }

        if start_date:
            params['orderDateFrom'] = start_date
        if end_date:
            params['orderDateTo'] = end_date
        if status:
            params['status'] = status

        response = self.make_request('GET', '/po/purchaseOrder', params=params)
        orders = response.get('data', [])

        if not orders:
            break

        all_orders.extend(orders)

        # 如果返回数量少于page_size，说明是最后一页
        if len(orders) < page_size:
            break

        page += 1

    return all_orders
```

### A.3 与NIIMBOT基准系统对齐

本项目严格遵循NIIMBOT基准系统的架构设计：

| NIIMBOT特性 | GZEAMS M18实现 | 基类支持 |
|------------|---------------|---------|
| 多组织数据隔离 | IntegrationConfig继承BaseModel | ✅ BaseModel |
| 软删除机制 | is_deleted + deleted_at | ✅ BaseModel |
| 完整审计日志 | created_at + created_by | ✅ BaseModel |
| 批量操作 | batch-delete/restore/update | ✅ BatchOperationMixin |
| 动态字段扩展 | custom_fields (JSONB) | ✅ BaseModel |
| 适配器模式 | BaseIntegrationAdapter | ✅ 框架提供 |
| 数据映射 | DataMappingTemplate | ✅ 框架提供 |
| 任务调度 | IntegrationSyncTask + Celery | ✅ 框架提供 |
| 日志审计 | IntegrationLog | ✅ 框架提供 |

---

**文档版本**: v2.0 (基于公共基类架构重构)
**最后更新**: 2026-01-15
**维护者**: GZEAMS开发团队
**审核状态**: 待审核
