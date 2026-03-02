# 字段验证器快速参考卡

## ✅ 已添加验证器的字段 (15个)

### Assets 模块 (7个)
```python
# AssetCategory
default_useful_life  -> MinValueValidator(0)
residual_rate       -> MinValueValidator(0)

# Asset
purchase_price          -> MinValueValidator(0) ✓ (已存在)
current_value           -> MinValueValidator(0) ✓ (新增)
accumulated_depreciation -> MinValueValidator(0) ✓ (新增)
useful_life             -> MinValueValidator(0) ✓ (新增)
residual_rate           -> MinValueValidator(0) ✓ (新增)
```

### Depreciation 模块 (4个)
```python
# DepreciationPolicy
useful_life_months    -> MinValueValidator(1) ✓ (新增)
residual_rate         -> MinValueValidator(0) ✓ (新增)
min_depreciation_amount -> MinValueValidator(0) ✓ (新增)
min_value_threshold   -> MinValueValidator(0) ✓ (新增)
```

## ⚠️ 需要手动添加的字段 (约40个)

### Finance 模块 (~9个)
```python
# Voucher
debit_amount   -> MinValueValidator(0)
credit_amount  -> MinValueValidator(0)
entry_count    -> MinValueValidator(0)

# VoucherEntry
line_no        -> MinValueValidator(1)
amount         -> MinValueValidator(0)

# IntegrationLog
response_status -> MinValueValidator(100), MaxValueValidator(599)
execution_time  -> MinValueValidator(0)
retry_count     -> MinValueValidator(0)
```

### DepreciationRecord 模块 (7个)
```python
purchase_price          -> MinValueValidator(0)
residual_value          -> MinValueValidator(0)
useful_life             -> MinValueValidator(1)
used_months             -> MinValueValidator(0)
depreciation_amount     -> MinValueValidator(0)
accumulated_depreciation -> MinValueValidator(0)
net_value               -> MinValueValidator(0)
```

### Inventory 模块 (~24个)
```python
# InventoryTask (5个)
total_assets      -> MinValueValidator(0)
scanned_assets    -> MinValueValidator(0)
found_assets      -> MinValueValidator(0)
missing_assets    -> MinValueValidator(0)
difference_count  -> MinValueValidator(0)

# InventorySnapshot (3个)
expected_quantity -> MinValueValidator(0)
actual_quantity   -> MinValueValidator(0)
scan_count        -> MinValueValidator(0)

# InventoryDifference (3个)
expected_quantity   -> MinValueValidator(0)
actual_quantity     -> MinValueValidator(0)
quantity_difference -> MinValueValidator(0)

# RFIDDevice (4个)
port         -> MinValueValidator(1), MaxValueValidator(65535)
read_power   -> MinValueValidator(0), MaxValueValidator(30)
scan_duration -> MinValueValidator(1)
antenna_count -> MinValueValidator(1)

# RFIDBatchScan (6个)
scan_duration       -> MinValueValidator(1)
read_power          -> MinValueValidator(0), MaxValueValidator(30)
total_scanned       -> MinValueValidator(0)
unique_assets       -> MinValueValidator(0)
progress_percentage -> MinValueValidator(0), MaxValueValidator(100)
elapsed_seconds     -> MinValueValidator(0)
```

## 📋 快速命令

### 检查字段
```bash
# 运行自动检查脚本
python scripts/add_validators_helper.py

# 查看已添加的验证器
grep -r "MinValueValidator" backend/apps/*/models.py
```

### 数据清洗
```bash
# 备份数据库
pg_dump -h localhost -U username -d database > backup.sql

# 执行清洗
psql -h localhost -U username -d database -f scripts/clean_negative_values.sql
```

### 运行测试
```bash
# 测试验证器
cd backend
python manage.py test apps.assets.tests.test_validators -v 2
```

### 创建迁移
```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## 🎯 完成标准

- [x] Assets 模块验证器
- [x] DepreciationPolicy 验证器
- [ ] Finance 模块验证器
- [ ] DepreciationRecord 验证器
- [ ] Inventory 模块验证器
- [ ] 所有模块通过测试
- [ ] 数据清洗完成
- [ ] 生产环境部署

## 📊 进度

**完成度**: 27% (15/55 字段)
**状态**: 部分完成
**下一步**: 解决文件编码问题，添加剩余验证器

---
**最后更新**: 2026-01-16
