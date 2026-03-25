# Phase 5.1: 万达宝M18适配器 - 测试计划

## 概述

本文档描述万达宝M18 ERP适配器的测试策略，包括单元测试、集成测试、Mock测试和端到端测试。

---

## 1. 单元测试

### 1.1 M18适配器测试

```python
# tests/apps/integration/adapters/test_m18_adapter.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
class TestM18Adapter:
    """M18适配器单元测试"""

    @pytest.fixture
    def mock_config(self, organization):
        """创建测试配置"""
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            is_enabled=True,
            connection_config={
                'api_url': 'https://m18-test.example.com/api',
                'api_key': 'test_api_key',
                'client_id': 'GZEAMS',
                'username': 'test_user',
                'password': 'test_password'
            }
        )
        return config

    @pytest.fixture
    def adapter(self, mock_config):
        """创建适配器实例"""
        return M18Adapter(mock_config)

    def test_adapter_initialization(self, adapter, mock_config):
        """测试适配器初始化"""
        assert adapter.adapter_type == 'm18'
        assert adapter.adapter_name == '万达宝M18'
        assert 'procurement' in adapter.supported_modules
        assert adapter.organization == mock_config.organization

    def test_get_auth_headers_without_token(self, adapter):
        """测试获取认证头（无token）"""
        adapter._access_token = None
        headers = adapter.get_auth_headers()

        assert headers['Content-Type'] == 'application/json'
        assert headers['X-API-Key'] == 'test_api_key'
        assert headers['X-Client-ID'] == 'GZEAMS'
        assert 'Authorization' not in headers

    def test_get_auth_headers_with_token(self, adapter):
        """测试获取认证头（有token）"""
        adapter._access_token = 'test_token'
        headers = adapter.get_auth_headers()

        assert headers['Authorization'] == 'Bearer test_token'

    @patch('apps.integration.adapters.m18_adapter.requests.post')
    def test_get_token_success(self, mock_post, adapter):
        """测试获取token成功"""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'access_token': 'new_token',
                'expires_in': 3600
            }
        )

        token = adapter._get_token()

        assert token == 'new_token'
        assert adapter._access_token == 'new_token'
        assert adapter._token_expires_at is not None

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert 'password' in call_args[1]['json']

    @patch('apps.integration.adapters.m18_adapter.requests.post')
    def test_get_token_failure(self, mock_post, adapter):
        """测试获取token失败"""
        mock_post.return_value = Mock(
            status_code=401,
            text='Unauthorized'
        )

        with pytest.raises(Exception) as exc_info:
            adapter._get_token()

        assert '获取M18 token失败' in str(exc_info.value)

    @patch('apps.integration.adapters.m18_adapter.requests.post')
    def test_get_token_reuse_existing(self, mock_post, adapter):
        """测试重用未过期的token"""
        adapter._access_token = 'existing_token'
        adapter._token_expires_at = datetime.now().timestamp() + 3600

        token = adapter._get_token()

        assert token == 'existing_token'
        mock_post.assert_not_called()

    @patch('apps.integration.adapters.m18_adapter.M18Adapter.make_request')
    @patch('apps.integration.adapters.m18_adapter.M18Adapter._get_token')
    def test_pull_purchase_orders(self, mock_get_token, mock_make_request, adapter):
        """测试拉取采购订单"""
        mock_get_token.return_value = 'test_token'
        mock_make_request.return_value = {
            'data': [
                {
                    'id': 'PO001',
                    'poNo': 'PO202401001',
                    'supplierCode': 'S001',
                    'supplierName': '供应商A',
                    'orderDate': '20240101',
                    'totalAmount': 10000.00,
                    'status': '3'
                }
            ]
        }

        orders = adapter.pull_purchase_orders(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert len(orders) == 1
        assert orders[0]['poNo'] == 'PO202401001'

    @patch('apps.integration.adapters.m18_adapter.M18Adapter.make_request')
    @patch('apps.integration.adapters.m18_adapter.M18Adapter._get_token')
    def test_pull_goods_receipts(self, mock_get_token, mock_make_request, adapter):
        """测试拉取收货单"""
        mock_get_token.return_value = 'test_token'
        mock_make_request.return_value = {
            'data': [
                {
                    'id': 'GR001',
                    'grNo': 'GR202401001',
                    'poNo': 'PO202401001',
                    'receiptDate': '20240115'
                }
            ]
        }

        receipts = adapter.pull_goods_receipts(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        assert len(receipts) == 1
        assert receipts[0]['grNo'] == 'GR202401001'

    @patch('apps.integration.adapters.m18_adapter.M18Adapter.map_to_local')
    def test_sync_purchase_order_create(self, mock_map_to_local, adapter, organization):
        """测试同步采购订单（新建）"""
        from apps.procurement.models import PurchaseOrder

        mock_map_to_local.return_value = {
            'po_code': 'PO202401001',
            'supplier_code': 'S001',
            'supplier_name': '供应商A',
            'order_date': '2024-01-01',
            'total_amount': 10000.00
        }

        m18_po = {
            'id': 'PO_M18_001',
            'poNo': 'PO202401001',
            'supplierCode': 'S001',
            'supplierName': '供应商A'
        }

        result = adapter.sync_purchase_order(m18_po)

        assert result['success'] is True
        assert result['external_id'] == 'PO_M18_001'
        assert result['created'] is True

    @patch('apps.integration.adapters.m18_adapter.M18Adapter.map_to_local')
    def test_sync_purchase_order_update(self, mock_map_to_local, adapter, organization):
        """测试同步采购订单（更新）"""
        from apps.procurement.models import PurchaseOrder

        # 先创建一个订单
        order = PurchaseOrder.objects.create(
            organization=organization,
            external_id='PO_M18_001',
            po_code='PO202401001',
            integration_source='m18'
        )

        mock_map_to_local.return_value = {
            'po_code': 'PO202401001_UPDATED',
            'supplier_code': 'S001',
            'supplier_name': '供应商A',
            'order_date': '2024-01-01',
            'total_amount': 15000.00
        }

        m18_po = {
            'id': 'PO_M18_001',
            'poNo': 'PO202401001',
            'supplierCode': 'S001',
            'supplierName': '供应商A'
        }

        result = adapter.sync_purchase_order(m18_po)

        assert result['success'] is True
        assert result['created'] is False

        # 验证更新
        order.refresh_from_db()
        assert order.po_code == 'PO202401001_UPDATED'

    @patch('apps.integration.adapters.m18_adapter.M18Adapter.make_request')
    @patch('apps.integration.adapters.m18_adapter.M18Adapter._get_token')
    def test_create_goods_receipt(self, mock_get_token, mock_make_request, adapter):
        """测试创建收货单"""
        mock_get_token.return_value = 'test_token'
        mock_make_request.return_value = {
            'success': True,
            'grNo': 'GR2024010001',
            'grId': '123456'
        }

        result = adapter.create_goods_receipt(
            po_id='PO001',
            items=[
                {'lineId': '1', 'qty': 10, 'location': 'A01'}
            ],
            receipt_date='2024-01-15'
        )

        assert result['success'] is True
        assert result['grNo'] == 'GR2024010001'

    def test_unsupported_business_type(self, adapter):
        """测试不支持的业务类型"""
        with pytest.raises(ValueError) as exc_info:
            adapter.pull_data('unsupported_type')

        assert '不支持的业务类型' in str(exc_info.value)
```

### 1.2 数据映射测试

```python
# tests/apps/integration/mappings/test_m18_mappings.py

import pytest
from apps.integration.mappings.m18_default_mappings import (
    M18_PURCHASE_ORDER_MAPPING,
    M18_GOODS_RECEIPT_MAPPING,
    M18_SUPPLIER_MAPPING
)


@pytest.mark.django_db
class TestM18Mappings:
    """M18数据映射测试"""

    def test_purchase_order_mapping_structure(self):
        """测试采购订单映射结构"""
        assert 'field_mappings' in M18_PURCHASE_ORDER_MAPPING
        assert 'value_mappings' in M18_PURCHASE_ORDER_MAPPING
        assert 'transform_rules' in M18_PURCHASE_ORDER_MAPPING

    def test_purchase_order_field_mappings(self):
        """测试采购订单字段映射"""
        mappings = M18_PURCHASE_ORDER_MAPPING['field_mappings']

        assert mappings['po_code'] == 'poNo'
        assert mappings['supplier_code'] == 'supplierCode'
        assert mappings['order_date'] == 'orderDate'
        assert mappings['items'] == 'lineItems'

    def test_purchase_order_value_mappings(self):
        """测试采购订单值映射"""
        mappings = M18_PURCHASE_ORDER_MAPPING['value_mappings']['status']

        assert mappings['1'] == 'draft'
        assert mappings['2'] == 'submitted'
        assert mappings['3'] == 'approved'
        assert mappings['4'] == 'closed'
        assert mappings['5'] == 'cancelled'

    def test_goods_receipt_mapping(self):
        """测试收货单映射"""
        mappings = M18_GOODS_RECEIPT_MAPPING['field_mappings']

        assert mappings['receipt_code'] == 'grNo'
        assert mappings['po_code'] == 'poNo'
        assert mappings['receipt_date'] == 'receiptDate'

    def test_supplier_mapping(self):
        """测试供应商映射"""
        mappings = M18_SUPPLIER_MAPPING['field_mappings']

        assert mappings['supplier_code'] == 'supplierCode'
        assert mappings['supplier_name'] == 'supplierName'
```

---

## 2. 集成测试

### 2.1 M18 API集成测试（使用Mock）

```python
# tests/apps/integration/integration/test_m18_integration.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig, IntegrationLog


@pytest.mark.django_db
@pytest.mark.integration
class TestM18Integration:
    """M18适配器集成测试"""

    @pytest.fixture
    def m18_config(self, organization):
        """创建M18配置"""
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18环境',
            is_enabled=True,
            connection_config={
                'api_url': 'https://m18-test.example.com/api',
                'api_key': 'test_key',
                'client_id': 'GZEAMS',
                'username': 'test_user',
                'password': 'test_password'
            }
        )

    @pytest.fixture
    def adapter(self, m18_config):
        """创建适配器"""
        return M18Adapter(m18_config)

    @patch('apps.integration.adapters.base_adapter.requests.request')
    def test_full_purchase_order_sync_flow(self, mock_request, adapter):
        """测试完整的采购订单同步流程"""
        # Mock M18 API响应
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {
                'data': [
                    {
                        'id': 'M18_PO_001',
                        'poNo': 'PO202401001',
                        'supplierCode': 'S001',
                        'supplierName': '测试供应商',
                        'orderDate': '20240101',
                        'deliveryDate': '20240115',
                        'totalAmount': 10000.00,
                        'currency': 'CNY',
                        'status': '3',
                        'lineItems': [
                            {
                                'lineNo': '1',
                                'materialCode': 'M001',
                                'materialName': '测试物料',
                                'quantity': 10,
                                'unit': 'PCS',
                                'unitPrice': 1000.00,
                                'amount': 10000.00
                            }
                        ]
                    }
                ]
            }
        )

        # 执行同步
        result = adapter.sync_purchase_orders_batch(
            start_date='2024-01-01',
            end_date='2024-01-31'
        )

        # 验证结果
        assert result['total'] == 1
        assert result['success'] == 1
        assert result['failed'] == 0

        # 验证日志已记录
        logs = IntegrationLog.objects.filter(
            organization=adapter.organization,
            integration_type='m18',
            business_type='purchase_order'
        )
        assert logs.count() > 0

    @patch('apps.integration.adapters.base_adapter.requests.request')
    def test_sync_with_partial_failure(self, mock_request, adapter):
        """测试部分失败的同步"""
        # Mock返回包含错误数据的响应
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {
                'data': [
                    {
                        'id': 'M18_PO_001',
                        'poNo': 'PO202401001',
                        'supplierCode': 'S001',
                        'supplierName': '测试供应商',
                        'orderDate': '20240101',
                        'totalAmount': 10000.00,
                        'status': '3'
                    },
                    {
                        # 缺少必填字段
                        'id': 'M18_PO_002',
                        'poNo': 'PO202401002'
                    }
                ]
            }
        )

        result = adapter.sync_purchase_orders_batch()

        assert result['total'] == 2
        assert result['success'] == 1
        assert result['failed'] == 1
        assert len(result['errors']) == 1

    @patch('apps.integration.adapters.base_adapter.requests.request')
    def test_api_error_handling(self, mock_request, adapter):
        """测试API错误处理"""
        # Mock API错误
        mock_request.return_value = Mock(
            status_code=500,
            text='Internal Server Error',
            json=lambda: {'error': 'Server error'}
        )

        with pytest.raises(Exception):
            adapter.pull_purchase_orders()

        # 验证错误日志已记录
        error_logs = IntegrationLog.objects.filter(
            organization=adapter.organization,
            status='failed'
        )
        assert error_logs.count() > 0

    @patch('apps.integration.adapters.base_adapter.requests.request')
    def test_create_goods_receipt_integration(self, mock_request, adapter):
        """测试创建收货单集成"""
        mock_request.return_value = Mock(
            status_code=200,
            json=lambda: {
                'success': True,
                'grNo': 'GR2024010001',
                'grId': 'GR_001',
                'data': {
                    'grNo': 'GR2024010001',
                    'grId': 'GR_001'
                }
            }
        )

        result = adapter.create_goods_receipt(
            po_id='PO_M18_001',
            items=[
                {
                    'lineId': '1',
                    'materialCode': 'M001',
                    'quantity': 10,
                    'uom': 'PCS',
                    'location': 'A01-01-01'
                }
            ],
            receipt_date='2024-01-15'
        )

        assert result['success'] is True
        assert result['grNo'] == 'GR2024010001'
        assert result['external_id'] == 'GR_001'
```

---

## 3. API测试

### 3.1 M18同步API测试

```python
# tests/api/integration/test_m18_api.py

import pytest
from unittest.mock import patch, Mock
from django.urls import reverse
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
@pytest.mark.api
class TestM18SyncAPI:
    """M18同步API测试"""

    @pytest.fixture
    def m18_config(self, organization):
        """创建M18配置"""
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='测试M18',
            is_enabled=True,
            connection_config={
                'api_url': 'https://test.m18.com',
                'api_key': 'test_key'
            }
        )

    def test_sync_purchase_orders_async(self, auth_client, m18_config):
        """测试异步同步采购订单"""
        with patch('apps.integration.views.m18_views.sync_m18_purchase_orders') as mock_task:
            mock_task.delay.return_value = Mock(id='celery_task_123')

            url = reverse('m18-purchase-order-sync')
            response = auth_client.post(url, {
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'async': True
            })

            assert response.status_code == 200
            assert response.data['status'] == 'pending'
            assert 'task_id' in response.data

    def test_sync_purchase_orders_sync(self, auth_client, m18_config):
        """测试同步同步采购订单"""
        with patch('apps.integration.adapters.m18_adapter.M18Adapter') as mock_adapter:
            mock_adapter.return_value.sync_purchase_orders_batch.return_value = {
                'total': 10,
                'success': 10,
                'failed': 0
            }

            url = reverse('m18-purchase-order-sync')
            response = auth_client.post(url, {
                'async': False
            })

            assert response.status_code == 200
            assert response.data['total'] == 10
            assert response.data['success'] == 10

    def test_sync_without_config(self, auth_client, organization):
        """测试没有配置时的错误处理"""
        # 删除所有M18配置
        IntegrationConfig.objects.filter(
            organization=organization,
            system_type='m18'
        ).delete()

        url = reverse('m18-purchase-order-sync')
        response = auth_client.post(url, {})

        assert response.status_code == 400
        assert '未找到启用的M18配置' in response.data['error']

    def test_create_goods_receipt(self, auth_client, m18_config):
        """测试创建收货单API"""
        with patch('apps.integration.adapters.m18_adapter.M18Adapter') as mock_adapter:
            mock_adapter.return_value.create_goods_receipt.return_value = {
                'success': True,
                'grNo': 'GR2024010001',
                'external_id': '123456'
            }

            url = reverse('m18-goods-receipt-list')
            response = auth_client.post(url, {
                'po_id': 'PO_M18_001',
                'receipt_date': '2024-01-15',
                'warehouse_code': 'WH01',
                'line_items': [
                    {
                        'line_id': '1',
                        'material_code': 'M001',
                        'quantity': 100,
                        'uom': 'PCS',
                        'location': 'A01-01-01'
                    }
                ]
            })

            assert response.status_code == 200
            assert response.data['success'] is True
            assert response.data['grNo'] == 'GR2024010001'

    def test_list_purchase_orders(self, auth_client, m18_config, organization):
        """测试获取同步的采购订单列表"""
        from apps.procurement.models import PurchaseOrder

        # 创建测试数据
        PurchaseOrder.objects.create(
            organization=organization,
            external_id='M18_PO_001',
            po_code='PO202401001',
            integration_source='m18',
            supplier_code='S001'
        )

        url = reverse('m18-purchase-order-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data['count'] == 1
```

---

## 4. Celery任务测试

### 4.1 同步任务测试

```python
# tests/apps/integration/tasks/test_m18_tasks.py

import pytest
from unittest.mock import patch, Mock
from apps.integration.tasks.m18_tasks import (
    sync_m18_purchase_orders,
    health_check_m18_configs
)


@pytest.mark.django_db
class TestM18Tasks:
    """M18 Celery任务测试"""

    @pytest.fixture
    def m18_config(self, organization):
        """创建M18配置"""
        from apps.integration.models import IntegrationConfig
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            is_enabled=True,
            connection_config={'api_url': 'https://test.m18.com'}
        )

    @patch('apps.integration.tasks.m18_tasks.M18PurchaseSyncService')
    def test_sync_purchase_orders_task(self, mock_service_class, m18_config):
        """测试采购订单同步任务"""
        mock_service = Mock()
        mock_service.execute_sync.return_value = {
            'total': 10,
            'success': 10,
            'failed': 0
        }
        mock_service_class.return_value = mock_service

        result = sync_m18_purchase_orders(str(m18_config.id), '2024-01-01', '2024-01-31')

        assert result['success'] == 10
        mock_service.execute_sync.assert_called_once()

    def test_sync_purchase_orders_retry_on_failure(self, m18_config):
        """测试任务失败时的重试"""
        with patch('apps.integration.tasks.m18_tasks.M18PurchaseSyncService') as mock_service_class:
            mock_service_class.side_effect = Exception('Network error')

            with pytest.raises(Exception):
                sync_m18_purchase_orders(str(m18_config.id))

    @patch('apps.integration.tasks.m18_tasks.AdapterFactory')
    def test_health_check_task(self, mock_factory, m18_config):
        """测试健康检查任务"""
        mock_adapter = Mock()
        mock_adapter.health_check.return_value = {
            'success': True
        }
        mock_factory.create.return_value = mock_adapter

        # 执行健康检查（不会抛出异常）
        health_check_m18_configs()

        mock_adapter.health_check.assert_called_once()
```

---

## 5. Mock服务器测试

### 5.1 M18 Mock服务器

```python
# tests/mocks/m18_mock_server.py

from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# 模拟数据存储
mock_data = {
    'purchase_orders': [
        {
            'id': 'M18_PO_001',
            'poNo': 'PO202401001',
            'supplierCode': 'S001',
            'supplierName': '测试供应商A',
            'orderDate': '20240101',
            'deliveryDate': '20240115',
            'totalAmount': 10000.00,
            'currency': 'CNY',
            'status': '3',
            'lineItems': [
                {
                    'lineNo': '1',
                    'materialCode': 'M001',
                    'materialName': '物料A',
                    'quantity': 10,
                    'unit': 'PCS',
                    'unitPrice': 1000.00,
                    'amount': 10000.00
                }
            ]
        }
    ],
    'goods_receipts': [],
    'suppliers': [
        {
            'id': 'S001',
            'supplierCode': 'S001',
            'supplierName': '测试供应商A',
            'contact': '张三',
            'phone': '13800138000',
            'email': 'zhangsan@example.com'
        }
    ]
}


@app.route('/oauth/token', methods=['POST'])
def get_token():
    """模拟OAuth token获取"""
    return jsonify({
        'access_token': 'mock_access_token',
        'token_type': 'Bearer',
        'expires_in': 3600
    })


@app.route('/po/purchaseOrder', methods=['GET'])
def get_purchase_orders():
    """获取采购订单"""
    order_date_from = request.args.get('orderDateFrom')
    order_date_to = request.args.get('orderDateTo')

    orders = mock_data['purchase_orders']

    # 简单日期过滤
    if order_date_from:
        orders = [o for o in orders if o.get('orderDate', '') >= order_date_from.replace('-', '')]
    if order_date_to:
        orders = [o for o in orders if o.get('orderDate', '') <= order_date_to.replace('-', '')]

    return jsonify({
        'success': True,
        'data': orders
    })


@app.route('/po/goodsReceipt', methods=['GET', 'POST'])
def handle_goods_receipts():
    """处理收货单"""
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'data': mock_data['goods_receipts']
        })
    else:
        data = request.json
        gr_no = f"GR{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_gr = {
            'grNo': gr_no,
            'grId': gr_no,
            'poNo': data.get('purchaseOrderId'),
            'receiptDate': data.get('receiptDate'),
            'lineItems': data.get('lineItems', [])
        }
        mock_data['goods_receipts'].append(new_gr)

        return jsonify({
            'success': True,
            'grNo': gr_no,
            'grId': gr_no,
            'data': new_gr
        })


@app.route('/bc/supplier', methods=['GET'])
def get_suppliers():
    """获取供应商"""
    return jsonify({
        'success': True,
        'data': mock_data['suppliers']
    })


@app.route('/bas/company/current', methods=['GET'])
def get_company_info():
    """获取公司信息"""
    return jsonify({
        'success': True,
        'data': {
            'companyName': '测试公司',
            'apiVersion': '1.0',
            'serverTime': datetime.now().isoformat()
        }
    })


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(port=5001, debug=True)
```

### 5.2 使用Mock服务器的测试

```python
# tests/integration/test_with_m18_mock.py

import pytest
import requests
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig


@pytest.mark.integration
@pytest.mark.parametrize("mock_server_url", ["http://localhost:5001"], indirect=True)
class TestM18WithMockServer:
    """使用Mock服务器的M18集成测试"""

    @pytest.fixture
    def m18_config(self, organization):
        """创建指向Mock服务器的配置"""
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            is_enabled=True,
            connection_config={
                'api_url': 'http://localhost:5001',
                'api_key': 'test_key',
                'client_id': 'GZEAMS',
                'username': 'test',
                'password': 'test'
            }
        )

    @pytest.fixture
    def adapter(self, m18_config):
        """创建适配器"""
        return M18Adapter(m18_config)

    def test_connection_to_mock(self, adapter):
        """测试连接Mock服务器"""
        result = adapter.test_connection()

        assert result['success'] is True
        assert '测试公司' in result['details'].get('company', '')

    def test_pull_purchase_orders_from_mock(self, adapter):
        """测试从Mock服务器拉取采购订单"""
        orders = adapter.pull_purchase_orders()

        assert len(orders) > 0
        assert orders[0]['poNo'] == 'PO202401001'

    def test_create_goods_receipt_on_mock(self, adapter):
        """测试在Mock服务器创建收货单"""
        result = adapter.create_goods_receipt(
            po_id='M18_PO_001',
            items=[{'lineId': '1', 'qty': 10}],
            receipt_date='2024-01-15'
        )

        assert result['success'] is True
        assert result['grNo'].startswith('GR')
```

---

## 6. 端到端测试场景

### 6.1 完整同步流程测试

```python
# tests/e2e/test_m18_sync_e2e.py

import pytest
from unittest.mock import patch
from apps.integration.models import IntegrationConfig, IntegrationSyncTask
from apps.procurement.models import PurchaseOrder


@pytest.mark.e2e
@pytest.mark.django_db
class TestM18SyncE2E:
    """M18同步端到端测试"""

    @pytest.fixture
    def setup_m18_environment(self, organization):
        """设置M18集成环境"""
        # 创建M18配置
        config = IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            system_name='生产环境M18',
            is_enabled=True,
            connection_config={
                'api_url': 'https://m18.company.com',
                'api_key': 'prod_key',
                'client_id': 'GZEAMS_PROD'
            },
            sync_config={
                'auto_sync': True,
                'sync_interval': 3600,
                'last_sync_at': '2024-01-01T00:00:00Z'
            }
        )

        return config

    def test_full_sync_lifecycle(self, setup_m18_environment):
        """测试完整的同步生命周期"""
        config = setup_m18_environment

        # 1. 手动触发同步
        with patch('apps.integration.adapters.m18_adapter.M18Adapter') as mock_adapter:
            mock_adapter.return_value.pull_purchase_orders.return_value = [
                {
                    'id': 'M18_PO_001',
                    'poNo': 'PO202401001',
                    'supplierCode': 'S001',
                    'supplierName': '供应商A',
                    'orderDate': '20240101',
                    'totalAmount': 10000.00,
                    'status': '3'
                }
            ]
            mock_adapter.return_value.map_to_local.return_value = {
                'po_code': 'PO202401001',
                'supplier_code': 'S001',
                'supplier_name': '供应商A',
                'order_date': '2024-01-01',
                'total_amount': 10000.00,
                'status': 'approved'
            }

            # 执行同步
            adapter = mock_adapter.return_value
            result = adapter.sync_purchase_orders_batch()

            # 2. 验证同步结果
            assert result['total'] == 1
            assert result['success'] == 1

            # 3. 验证本地数据已创建
            po = PurchaseOrder.objects.filter(
                organization=config.organization,
                external_id='M18_PO_001'
            ).first()

            assert po is not None
            assert po.po_code == 'PO202401001'
            assert po.integration_source == 'm18'

            # 4. 验证同步任务记录
            sync_tasks = IntegrationSyncTask.objects.filter(
                organization=config.organization,
                integration_config=config,
                business_type='purchase_order'
            )

            assert sync_tasks.count() > 0
            latest_task = sync_tasks.order_by('-created_at').first()
            assert latest_task.status == 'success'

    def test_sync_error_recovery(self, setup_m18_environment):
        """测试同步错误恢复"""
        config = setup_m18_environment

        with patch('apps.integration.adapters.m18_adapter.M18Adapter') as mock_adapter:
            # 第一次调用失败
            mock_adapter.return_value.pull_purchase_orders.side_effect = [
                Exception('Network error'),
                [  # 重试成功
                    {
                        'id': 'M18_PO_001',
                        'poNo': 'PO202401001',
                        'supplierCode': 'S001'
                    }
                ]
            ]
            mock_adapter.return_value.map_to_local.return_value = {
                'po_code': 'PO202401001',
                'supplier_code': 'S001'
            }

            adapter = mock_adapter.return_value

            # 第一次同步失败
            with pytest.raises(Exception):
                adapter.sync_purchase_orders_batch()

            # 验证失败日志
            from apps.integration.models import IntegrationLog
            failed_logs = IntegrationLog.objects.filter(
                organization=config.organization,
                status='failed'
            )
            assert failed_logs.count() > 0

            # 重试成功
            result = adapter.sync_purchase_orders_batch()
            assert result['success'] == 1
```

---

## 7. 性能测试

### 7.1 批量同步性能测试

```python
# tests/performance/test_m18_performance.py

import pytest
import time
from unittest.mock import patch, MagicMock
from apps.integration.adapters.m18_adapter import M18Adapter
from apps.integration.models import IntegrationConfig


@pytest.mark.django_db
@pytest.mark.performance
class TestM18Performance:
    """M18性能测试"""

    @pytest.fixture
    def m18_config(self, organization):
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='m18',
            is_enabled=True,
            connection_config={'api_url': 'https://test.m18.com'}
        )

    def test_batch_sync_100_orders(self, m18_config):
        """测试批量同步100个订单的性能"""
        # Mock 100个订单数据
        orders = [
            {
                'id': f'M18_PO_{i:04d}',
                'poNo': f'PO202401{i:04d}',
                'supplierCode': 'S001',
                'supplierName': '供应商A',
                'orderDate': '20240101',
                'totalAmount': 10000 + i * 100,
                'status': '3'
            }
            for i in range(100)
        ]

        adapter = M18Adapter(m18_config)

        with patch.object(adapter, 'pull_purchase_orders', return_value=orders):
            with patch.object(adapter, 'map_to_local') as mock_map:
                mock_map.return_value = {
                    'po_code': 'PO001',
                    'supplier_code': 'S001'
                }

                start_time = time.time()
                result = adapter.sync_purchase_orders_batch()
                end_time = time.time()

                sync_time = end_time - start_time

                assert result['success'] == 100
                assert sync_time < 10.0, f"同步100个订单耗时 {sync_time:.2f} 秒，超过预期"

    def test_concurrent_sync_performance(self, m18_config):
        """测试并发同步性能"""
        import threading

        adapter = M18Adapter(m18_config)
        results = []
        errors = []

        def sync_worker(worker_id):
            try:
                with patch.object(adapter, 'pull_purchase_orders') as mock_pull:
                    mock_pull.return_value = [
                        {'id': f'PO_{worker_id}_001', 'poNo': f'PO{worker_id}001', 'supplierCode': 'S001'}
                    ]
                    with patch.object(adapter, 'map_to_local', return_value={'po_code': 'PO001'}):
                        result = adapter.sync_purchase_orders_batch()
                        results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建10个并发线程
        threads = []
        start_time = time.time()

        for i in range(10):
            t = threading.Thread(target=sync_worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        end_time = time.time()
        concurrent_time = end_time - start_time

        assert len(errors) == 0
        assert len(results) == 10
        assert concurrent_time < 5.0, f"并发同步耗时 {concurrent_time:.2f} 秒"
```

---

## 8. 测试数据Fixture

```python
# tests/fixtures/m18_fixtures.py

import pytest
from apps.integration.models import IntegrationConfig
from apps.procurement.models import PurchaseOrder, Supplier


@pytest.fixture
def m18_purchase_order_data():
    """M18采购订单测试数据"""
    return {
        'id': 'M18_PO_001',
        'poNo': 'PO202401001',
        'supplierCode': 'S001',
        'supplierName': '测试供应商A',
        'orderDate': '20240101',
        'deliveryDate': '20240115',
        'totalAmount': 10000.00,
        'currency': 'CNY',
        'status': '3',
        'remark': '测试备注',
        'lineItems': [
            {
                'lineNo': '1',
                'materialCode': 'M001',
                'materialName': '物料A',
                'quantity': 10,
                'unit': 'PCS',
                'unitPrice': 1000.00,
                'amount': 10000.00
            }
        ]
    }


@pytest.fixture
def m18_supplier_data():
    """M18供应商测试数据"""
    return {
        'id': 'S001',
        'supplierCode': 'S001',
        'supplierName': '测试供应商A',
        'contact': '张三',
        'phone': '13800138000',
        'email': 'zhangsan@example.com',
        'address': '北京市朝阳区'
    }


@pytest.fixture
def m18_goods_receipt_data():
    """M18收货单测试数据"""
    return {
        'id': 'GR001',
        'grNo': 'GR2024010001',
        'poNo': 'PO202401001',
        'receiptDate': '20240115',
        'supplierCode': 'S001',
        'warehouseCode': 'WH01',
        'lineItems': [
            {
                'lineNo': '1',
                'materialCode': 'M001',
                'quantity': 10,
                'uom': 'PCS'
            }
        ]
    }
```

---

## 9. 测试覆盖率目标

| 模块 | 单元测试覆盖率 | 集成测试覆盖率 |
|------|---------------|---------------|
| M18Adapter | 90%+ | - |
| 数据映射 | 95%+ | - |
| Celery任务 | 80%+ | - |
| API端点 | - | 80%+ |
| 端到端流程 | - | 70%+ |

---

## 后续任务

1. 实现所有单元测试用例
2. 搭建Mock服务器用于集成测试
3. 配置CI/CD自动化测试流程
4. 实现性能监控和告警
