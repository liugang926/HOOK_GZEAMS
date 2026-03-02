# IT资产管理模块 - 已重构

> 本模块已重新设计并拆分为更合理的功能模块

## 变更说明 (2026-01-24)

原IT资产管理模块PRD (v1.0) 包含的功能过多且架构不够合理。经过分析讨论，已将其重构为以下模块：

| 原功能 | 新的处理方式 | 理由 |
|--------|-------------|------|
| **ITAssetInfo硬件配置扩展表** | 使用 `Asset.custom_fields` 存储 | 避免表join，统一使用元数据能力 |
| **软件许可证管理** | → [软件许可证管理模块](../software_license_management/) | 独立业务价值，通用性强 |
| **配置变更历史** | 系统级审计日志 | 不应在业务模块实现 |
| **IT维护记录** | 通用维护记录功能 | 所有资产类型都需要，不限于IT |

## 新的模块结构

```
docs/plans/
├── software_license_management/    # 软件许可证管理 (核心功能)
│   └── SOFTWARE_LICENSE_MANAGEMENT_PRD.md
├── maintenance/                     # 通用维护记录 (待创建)
│   └── MAINTENANCE_PRD.md
└── it_asset_management/
    ├── README.md                   # 本文件
    └── archive/
        └── IT_ASSET_MANAGEMENT_PRD_v1.0_deprecated.md  # 旧版PRD存档
```

## 硬件配置信息管理

对于IT设备的硬件配置信息（CPU、内存、硬盘等），建议两种方式：

### 方式1: 使用custom_fields (推荐)

```python
# 在Asset的custom_fields中存储IT硬件信息
asset.custom_fields = {
    'cpu_model': 'Intel Core i7-12700K',
    'cpu_cores': 12,
    'ram_capacity': 32,
    'ram_type': 'DDR5',
    'disk_type': 'NVMe',
    'disk_capacity': 1024,
    'mac_address': '00:1A:2B:3C:4D:5E',
    'ip_address': '192.168.1.100',
    'os_name': 'Windows 11 Pro',
}
```

### 方式2: 通过系统元数据引擎定义

在 `BusinessObject` 和 `FieldDefinition` 中为特定资产类别定义专用字段，前端通过 `DynamicForm` 自动渲染。

## 后端代码处理

已存在的 `backend/apps/it_assets/` 模块可以：

1. **保留软件许可证相关代码**: `Software`, `SoftwareLicense`, `LicenseAllocation` 模型
2. **迁移或废弃ITAssetInfo**: 建议废弃，使用custom_fields替代
3. **迁移或废弃配置变更**: 建议废弃，使用系统审计日志
4. **迁移或重构维护记录**: 改为通用功能，移到 `apps/maintenance/`

## 相关链接

- [软件许可证管理PRD](../software_license_management/SOFTWARE_LICENSE_MANAGEMENT_PRD.md)
- [后端代码](../../../backend/apps/it_assets/)
- [旧版PRD存档](archive/IT_ASSET_MANAGEMENT_PRD_v1.0_deprecated.md)
