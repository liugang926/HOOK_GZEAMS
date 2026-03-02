# Phase 5.0: 通用ERP集成框架 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 适配器基类测试 | pytest | BaseIntegrationAdapter |
| 工厂模式测试 | pytest | AdapterFactory |
| 数据映射测试 | pytest | 数据映射功能 |
| API测试 | pytest | 集成配置、同步任务、日志API |
| 前端测试 | Vitest | 集成管理组件 |

---

## 1. 适配器基类测试

```python
# tests/integration/test_base_adapter.py

import pytest
from unittest.mock import Mock, patch
from apps.integration.adapters.base import BaseIntegrationAdapter
from apps.integration.models import IntegrationConfig


class MockAdapter(BaseIntegrationAdapter):
    """测试用模拟适配器"""

    adapter_type = 'mock'
    adapter_name = 'Mock System'
    supported_modules = ['procurement', 'finance']

    def test_connection(self):
        return {'success': True, 'message': 'OK'}

    def get_auth_headers(self):
        return {'Authorization': 'Bearer test-token'}

    def pull_data(self, business_type, params=None):
        return [{'id': 1, 'name': 'Test'}]

    def push_data(self, business_type, data):
        return {'success': True, 'id': 'ext-123'}


class TestBaseIntegrationAdapter:
    """适配器基类测试"""

    @pytest.fixture
    def config(self, db, organization):
        return IntegrationConfig.objects.create(
            organization=organization,
            system_type='mock',
            system_name='测试系统',
            connection_config={
                'api_url': 'http://test.com/api',
                'api_key': 'test-key'
            },
            enabled_modules=['procurement']
        )

    @pytest.fixture
    def adapter(self, config):
        return MockAdapter(config)

    def test_adapter_initialization(self, adapter):
        """测试适配器初始化"""
        assert adapter.adapter_type == 'mock'
        assert adapter.adapter_name == 'Mock System'
        assert adapter.connection_config['api_url'] == 'http://test.com/api'

    def test_map_to_local(self, adapter):
        """测试映射到本地格式"""
        external_data = {
            'poNo': 'PO001',
            'supplierName': '测试供应商',
            'orderDate': '2024-01-15'
        }

        # Mock映射模板
        with patch.object(adapter, '_get_mapping_template') as mock_template:
            mock_template.return_value = Mock(
                field_mappings={
                    'po_code': 'poNo',
                    'supplier_name': 'supplierName',
                    'order_date': 'orderDate'
                },
                value_mappings=None
            )

            local_data = adapter.map_to_local('purchase_order', external_data)

            assert local_data['po_code'] == 'PO001'
            assert local_data['supplier_name'] == '测试供应商'

    def test_map_to_local_with_value_mapping(self, adapter):
        """测试带值映射的本地转换"""
        external_data = {'status': '1'}

        with patch.object(adapter, '_get_mapping_template') as mock_template:
            mock_template.return_value = Mock(
                field_mappings={'status': 'status'},
                value_mappings={'status': {'1': 'draft', '2': 'submitted'}}
            )

            local_data = adapter.map_to_local('purchase_order', external_data)

            assert local_data['status'] == 'draft'

    def test_map_to_external(self, adapter):
        """测试映射到外部格式"""
        local_data = {
            'po_code': 'PO001',
            'supplier_name': '测试供应商'
        }

        with patch.object(adapter, '_get_mapping_template') as mock_template:
            mock_template.return_value = Mock(
                field_mappings={
                    'po_code': 'poNo',
                    'supplier_name': 'supplierName'
                },
                value_mappings=None
            )

            external_data = adapter.map_to_external('purchase_order', local_data)

            assert external_data['poNo'] == 'PO001'
            assert external_data['supplierName'] == '测试供应商'

    def test_nested_field_mapping(self, adapter):
        """测试嵌套字段映射"""
        external_data = {
            'supplier': {
                'name': '测试供应商'
            }
        }

        with patch.object(adapter, '_get_mapping_template') as mock_template:
            mock_template.return_value = Mock(
                field_mappings={
                    'supplier_name': {'path': 'supplier.name'}
                },
                value_mappings=None
            )

            local_data = adapter.map_to_local('purchase_order', external_data)

            assert local_data['supplier_name'] == '测试供应商'

    def test_log_request(self, adapter):
        """测试请求日志记录"""
        from apps.integration.models import IntegrationLog

        log = adapter.log_request(
            method='GET',
            url='http://test.com/api/orders',
            request_body={'page': 1},
            business_type='purchase_order'
        )

        assert log.request_method == 'GET'
        assert log.integration_type == 'mock_purchase_order'
        assert log.action == 'pull'

    def test_health_check_success(self, adapter):
        """测试健康检查成功"""
        result = adapter.health_check()

        assert result['success'] is True
        assert adapter.config.health_status == 'healthy'
```

---

## 2. 工厂模式测试

```python
# tests/integration/test_factory.py

import pytest
from apps.integration.factory import AdapterFactory
from apps_integration.adapters.base import BaseIntegrationAdapter


class MockAdapter1(BaseIntegrationAdapter):
    adapter_type = 'mock1'
    adapter_name = 'Mock 1'

    def test_connection(self):
        pass
    def get_auth_headers(self):
        return {}
    def pull_data(self, business_type, params=None):
        return []
    def push_data(self, business_type, data):
        return {}


class MockAdapter2(BaseIntegrationAdapter):
    adapter_type = 'mock2'
    adapter_name = 'Mock 2'

    # ... 实现抽象方法


class TestAdapterFactory:
    """适配器工厂测试"""

    def test_register_adapter(self):
        """测试注册适配器"""
        AdapterFactory.register('mock1', MockAdapter1)
        assert 'mock1' in AdapterFactory._adapters
        assert AdapterFactory._adapters['mock1'] == MockAdapter1

    def test_create_adapter(self, config):
        """测试创建适配器"""
        AdapterFactory.register('mock1', MockAdapter1)

        config.system_type = 'mock1'
        adapter = AdapterFactory.create(config)

        assert isinstance(adapter, MockAdapter1)
        assert adapter.config == config

    def test_create_unsupported_adapter(self, config):
        """测试创建不支持的适配器"""
        config.system_type = 'unsupported'

        with pytest.raises(ValueError, match='不支持的集成系统类型'):
            AdapterFactory.create(config)

    def test_get_supported_systems(self):
        """测试获取支持的系统列表"""
        AdapterFactory.register('mock1', MockAdapter1)
        AdapterFactory.register('mock2', MockAdapter2)

        systems = AdapterFactory.get_supported_systems()

        assert 'mock1' in systems
        assert systems['mock1'] == 'Mock 1'
        assert 'mock2' in systems
        assert systems['mock2'] == 'Mock 2'
```

---

## 3. 数据映射测试

```python
# tests/integration/test_data_mapping.py

import pytest
from apps.integration.models import DataMappingTemplate
from apps.integration.adapters.base import BaseIntegrationAdapter


class TestDataMapping:
    """数据映射测试"""

    @pytest.fixture
    def mapping_template(self, db, organization):
        return DataMappingTemplate.objects.create(
            organization=organization,
            system_type='m18',
            business_type='purchase_order',
            template_name='M18采购订单映射',
            field_mappings={
                'po_code': 'poNo',
                'supplier_name': 'supplierName',
                'order_date': 'orderDate'
            },
            value_mappings={
                'status': {
                    'draft': '1',
                    'submitted': '2',
                    'approved': '3'
                }
            },
            transform_rules=[
                {
                    'field': 'order_date',
                    'type': 'date_format',
                    'from_format': 'YYYY-MM-DD',
                    'to_format': 'YYYYMMDD'
                }
            ]
        )

    def test_field_mapping(self, mapping_template):
        """测试字段映射"""
        assert mapping_template.field_mappings['po_code'] == 'poNo'

    def test_value_mapping(self, mapping_template):
        """测试值映射"""
        status_map = mapping_template.value_mappings['status']
        assert status_map['draft'] == '1'
        assert status_map['approved'] == '3'

    def test_transform_rules(self, mapping_template):
        """测试转换规则"""
        rule = mapping_template.transform_rules[0]
        assert rule['field'] == 'order_date'
        assert rule['type'] == 'date_format'

    def test_unique_constraint(self, organization, mapping_template):
        """测试唯一约束"""
        with pytest.raises(Exception):  # IntegrityError
            DataMappingTemplate.objects.create(
                organization=organization,
                system_type='m18',
                business_type='purchase_order',
                template_name='重复模板'
            )
```

---

## 4. API测试

```python
# tests/api/test_integration_api.py

import pytest
from django.urls import reverse
from apps.integration.models import IntegrationConfig, IntegrationSyncTask


class TestIntegrationConfigAPI:
    """集成配置API测试"""

    def test_list_configs(self, auth_client, integration_config):
        """测试获取配置列表"""
        url = reverse('integration-config-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) > 0

    def test_create_config(self, auth_client, organization):
        """测试创建配置"""
        url = reverse('integration-config-list')
        data = {
            'system_type': 'm18',
            'system_name': '测试M18',
            'connection_config': {
                'api_url': 'http://test.com/api',
                'api_key': 'test-key'
            },
            'enabled_modules': ['procurement'],
            'is_enabled': True
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == 201
        assert response.data['system_name'] == '测试M18'

    def test_update_config(self, auth_client, integration_config):
        """测试更新配置"""
        url = reverse('integration-config-detail', args=[integration_config.id])
        data = {'system_name': '更新后的名称'}
        response = auth_client.patch(url, data, format='json')

        assert response.status_code == 200
        assert response.data['system_name'] == '更新后的名称'

    def test_delete_config(self, auth_client, integration_config):
        """测试删除配置"""
        url = reverse('integration-config-detail', args=[integration_config.id])
        response = auth_client.delete(url)

        assert response.status_code == 204

    def test_connection(self, auth_client, integration_config):
        """测试连接"""
        with patch('apps.integration.adapters.m18_adapter.M18Adapter.test_connection') as mock_test:
            mock_test.return_value = {
                'success': True,
                'message': '连接成功',
                'response_time_ms': 100
            }

            url = reverse('integration-config-test', args=[integration_config.id])
            response = auth_client.post(url)

            assert response.status_code == 200
            assert response.data['success'] is True


class TestSyncTaskAPI:
    """同步任务API测试"""

    def test_list_sync_tasks(self, auth_client, sync_task):
        """测试获取任务列表"""
        url = reverse('sync-task-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) > 0

    def test_trigger_sync(self, auth_client, integration_config):
        """测试触发同步"""
        with patch('apps.integration.services.base_sync_service.BaseSyncService.execute_sync') as mock_sync:
            mock_sync.return_value = {
                'status': 'success',
                'total': 10,
                'success': 10,
                'failed': 0
            }

            url = reverse('integration-config-sync', args=[integration_config.id])
            data = {
                'module_type': 'procurement',
                'business_type': 'purchase_order',
                'direction': 'pull',
                'async': False
            }
            response = auth_client.post(url, data, format='json')

            assert response.status_code == 200

    def test_cancel_task(self, auth_client, sync_task):
        """测试取消任务"""
        sync_task.status = 'running'
        sync_task.save()

        url = reverse('sync-task-cancel', args=[sync_task.id])
        response = auth_client.post(url)

        assert response.status_code == 200
        assert response.data['status'] == 'cancelled'


class TestIntegrationLogAPI:
    """集成日志API测试"""

    def test_list_logs(self, auth_client, integration_log):
        """测试获取日志列表"""
        url = reverse('integration-log-list')
        response = auth_client.get(url)

        assert response.status_code == 200
        assert len(response.data['results']) > 0

    def test_filter_by_success(self, auth_client, integration_log):
        """测试按成功状态筛选"""
        url = reverse('integration-log-list')
        response = auth_client.get(url, {'success': True})

        assert response.status_code == 200
        assert all(log['success'] for log in response.data['results'])


class TestDataMappingAPI:
    """数据映射API测试"""

    def test_list_mappings(self, auth_client, mapping_template):
        """测试获取映射列表"""
        url = reverse('mapping-template-list')
        response = auth_client.get(url)

        assert response.status_code == 200

    def test_create_mapping(self, auth_client, organization):
        """测试创建映射"""
        url = reverse('mapping-template-list')
        data = {
            'system_type': 'm18',
            'business_type': 'purchase_order',
            'template_name': '测试映射',
            'field_mappings': {'po_code': 'poNo'},
            'value_mappings': {},
            'is_active': True
        }
        response = auth_client.post(url, data, format='json')

        assert response.status_code == 201

    def test_update_mapping(self, auth_client, mapping_template):
        """测试更新映射"""
        url = reverse('mapping-template-detail', args=[mapping_template.id])
        data = {'is_active': False}
        response = auth_client.patch(url, data, format='json')

        assert response.status_code == 200
        assert response.data['is_active'] is False
```

---

## 5. 前端测试

```typescript
// tests/frontend/integration.spec.ts

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import IntegrationList from '@/views/integration/IntegrationList.vue'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

vi.mock('@/api/integration', () => ({
  integrationApi: {
    listConfigs: vi.fn(() => Promise.resolve({ data: [] })),
    createConfig: vi.fn(),
    updateConfig: vi.fn(),
    deleteConfig: vi.fn(),
    testConnection: vi.fn(),
    triggerSync: vi.fn()
  }
}))

describe('IntegrationList', () => {
  it('renders integration list', () => {
    const wrapper = mount(IntegrationList)
    expect(wrapper.find('.integration-list').exists()).toBe(true)
  })

  it('shows supported systems', () => {
    const wrapper = mount(IntegrationList)
    const systems = wrapper.vm.supportedSystems
    expect(systems).toHaveLength(5)
    expect(systems[0].value).toBe('m18')
  })

  it('opens add dialog', async () => {
    const wrapper = mount(IntegrationList)
    await wrapper.vm.handleAdd()
    expect(wrapper.vm.configDialogVisible).toBe(true)
  })

  it('tests connection', async () => {
    const { integrationApi } = await import('@/api/integration')
    integrationApi.testConnection.mockResolvedValue({
      data: { success: true, message: '连接成功' }
    })

    const wrapper = mount(IntegrationList, {
      data() {
        return {
          configs: [{ id: '1', system_type: 'm18' }]
        }
      }
    })

    await wrapper.vm.handleTest({ id: '1' })
    expect(integrationApi.testConnection).toHaveBeenCalled()
  })
})

describe('IntegrationConfigDialog', () => {
  it('validates required fields', async () => {
    const wrapper = mount(IntegrationConfigDialog, {
      props: { modelValue: true }
    })

    const form = wrapper.find('el-form')
    expect(form.exists()).toBe(true)
  })

  it('shows correct connection form based on system type', async () => {
    const wrapper = mount(IntegrationConfigDialog, {
      props: {
        modelValue: true,
        config: { system_type: 'm18' }
      }
    })

    expect(wrapper.vm.connectionConfigComponent).toBeDefined()
  })
})
```

---

## 测试执行

```bash
# 后端测试
pytest tests/integration/ -v
pytest tests/api/test_integration_api.py -v

# 前端测试
npm run test -- integration.spec.ts
```

---

## 后续任务

1. Phase 5.1: 实现万达宝M18适配器（基于通用框架）
2. Phase 5.2: 实现财务凭证集成（基于通用框架）
3. 扩展其他ERP适配器
