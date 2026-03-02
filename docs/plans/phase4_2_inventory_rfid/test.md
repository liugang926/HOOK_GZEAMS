# Phase 4.2: RFID批量盘点 - 测试方案

## 测试概览

| 测试类型 | 框架 | 覆盖范围 |
|---------|------|----------|
| 适配器测试 | pytest | RFIDReaderAdapter测试 |
| 服务测试 | pytest | RFIDInventoryService测试 |
| API测试 | pytest | RFID API测试 |
| Celery任务测试 | pytest + pytest-celery | 异步任务测试 |

---

## 1. RFID适配器测试

```python
# tests/inventory/test_rfid_adapter.py

import pytest
from unittest.mock import Mock, patch
from apps.inventory.services.rfid.adapter import GenericLLRPReader, RFIDReaderAdapter


class TestGenericLLRPReader:
    """通用LLRP读写器测试"""

    @pytest.fixture
    def reader(self):
        return GenericLLRPReader()

    def test_initial_state(self, reader):
        """测试初始状态"""
        assert reader.connected is False
        assert reader.reading is False
        assert len(reader.read_tags) == 0

    @patch('socket.socket')
    def test_connect_success(self, mock_socket, reader):
        """测试连接成功"""
        mock_sock = Mock()
        mock_socket.return_value = mock_sock

        result = reader.connect('192.168.1.100', 5084)

        assert result is True
        assert reader.connected is True

    def test_should_report_new_tag(self, reader):
        """测试新标签应该上报"""
        epc = "3034A2B3C4D5E6F708192A3B4C5D6E7F"

        assert reader._should_report(epc) is True

    def test_should_not_report_duplicate_tag(self, reader):
        """测试短时间内重复标签不应上报"""
        epc = "3034A2B3C4D5E6F708192A3B4C5D6E7F"

        reader.read_tags.add(epc)
        reader.last_read_time[epc] = time.time()

        assert reader._should_report(epc) is False

    def test_should_report_after_dedup_interval(self, reader):
        """测试去重间隔后应该上报"""
        import time
        epc = "3034A2B3C4D5E6F708192A3B4C5D6E7F"

        reader.read_tags.add(epc)
        reader.last_read_time[epc] = time.time() - 10  # 10秒前

        assert reader._should_report(epc) is True
```

---

## 2. RFID服务测试

```python
# tests/inventory/test_rfid_service.py

import pytest
from apps.inventory.services.rfid.inventory_service import RFIDInventoryService
from apps.inventory.models import InventoryTask
from apps.assets.models import Asset


class TestRFIDInventoryService:
    """RFID盘点服务测试"""

    @pytest.fixture
    def reader_config(self):
        return {
            'type': 'generic',
            'host': '192.168.1.100',
            'port': 5084,
            'duration': 30
        }

    @pytest.fixture
    def service(self, reader_config):
        return RFIDInventoryService(reader_config)

    def test_get_reader_generic(self, service):
        """测试获取通用读写器"""
        reader = service.get_reader()

        assert isinstance(reader, GenericLLRPReader)

    def test_get_reader_impinj(self):
        """测试获取Impinj读写器"""
        config = {'type': 'impinj'}
        service = RFIDInventoryService(config)

        reader = service.get_reader()
        assert reader.__class__.__name__ == 'ImpinjReader'

    @pytest.fixture
    def asset_with_epc(self, db, organization):
        """带EPC的资产"""
        asset = Asset.objects.create(
            organization=organization,
            asset_code='RFID001',
            asset_name='RFID测试资产',
            rfid_epc='3034A2B3C4D5E6F708192A3B4C5D6E7F'
        )
        return asset

    def test_process_tag_found(self, service, asset_with_epc, inventory_task):
        """测试处理找到的标签"""
        result = service._process_tag(
            asset_with_epc.rfid_epc,
            inventory_task
        )

        assert result is not None
        assert result['asset_id'] == asset_with_epc.id
        assert result['epc'] == asset_with_epc.rfid_epc

    def test_process_tag_not_found(self, service, inventory_task):
        """测试处理未找到的标签"""
        result = service._process_tag(
            'UNKNOWN_EPC_CODE',
            inventory_task
        )

        assert result is not None
        assert result['status'] == 'unknown'

    @patch('apps.inventory.services.rfid.inventory_service.RFIDInventoryService.get_reader')
    def test_test_connection_success(self, mock_get_reader, service):
        """测试连接成功"""
        mock_reader = Mock()
        mock_reader.connect.return_value = True
        mock_reader.get_reader_info.return_value = {'connected': True}
        mock_get_reader.return_value = mock_reader

        result = service.test_connection()

        assert result['success'] is True
        assert result['info'] is not None
```

---

## 3. Celery任务测试

```python
# tests/inventory/test_rfid_tasks.py

import pytest
from celery import shared_task, current_task
from unittest.mock import Mock, patch
from apps.inventory.tasks.rfid_tasks import rfid_inventory_task


@pytest.mark.django_db
class TestRFIDInventoryTask:
    """RFID Celery任务测试"""

    @patch('apps.inventory.tasks.rfid_tasks.RFIDInventoryService')
    def test_rfid_task_success(self, mock_service_class):
        """测试任务执行成功"""
        # Mock service
        mock_service = Mock()
        mock_service.start_inventory.return_value = {
            'total_scanned': 100,
            'results': []
        }
        mock_service_class.return_value = mock_service

        # 执行任务
        result = rfid_inventory_task(1, {'type': 'generic'})

        assert result['status'] == 'completed'
        assert result['total_scanned'] == 100

    @patch('apps.inventory.tasks.rfid_tasks.RFIDInventoryService')
    def test_rfid_task_failure(self, mock_service_class):
        """测试任务执行失败"""
        mock_service = Mock()
        mock_service.start_inventory.side_effect = Exception("连接失败")
        mock_service_class.return_value = mock_service

        with pytest.raises(Exception):
            rfid_inventory_task(1, {'type': 'generic'})
```

---

## 测试执行

```bash
# RFID模块测试
pytest tests/inventory/test_rfid_*.py -v

# 完整测试套件
npm run test:phase4.2
```

---

## 后续任务

1. Phase 4.3: 实现盘点快照和差异处理
2. Phase 5.1: 实现万达宝M18采购对接
