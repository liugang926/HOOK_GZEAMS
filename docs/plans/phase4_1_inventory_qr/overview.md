# Phase 4.1: QR码扫描盘点 - 总览

## 1. 功能概述与业务场景

### 1.1 功能概述

Phase 4.1 实现基于二维码的资产盘点功能,是GZEAMS资产管理系统的核心模块之一。本阶段主要实现:

- **二维码生成**: 为每个资产生成唯一二维码,包含资产完整信息和MD5校验和,确保防伪防篡改
- **标签打印**: 支持批量生成和打印资产标签PDF,适配多种标签尺寸(50×30mm/40×25mm/30×20mm)
- **盘点任务管理**: 创建、分配、执行、跟踪盘点任务,支持全盘、部门盘、分类盘、抽盘等多种盘点类型
- **扫码盘点**: 通过PDA/手机扫码快速录入盘点结果,支持离线缓存和批量上传
- **进度跟踪**: 实时显示盘点进度和统计数据(已盘/未盘/正常/异常)
- **差异处理**: 自动识别盘盈、盘亏、损坏、位置变更等差异,生成差异报告

### 1.2 业务场景

#### 场景1: 全面盘点 (Full Inventory)

**触发条件**:
- 年终/年中全面资产盘点
- 公司合并/分立时的资产核查
- 审计要求的全面盘点

**盘点范围**: 组织内所有有效资产

**业务流程**:
1. 创建盘点任务(类型=全盘)
2. 系统自动生成资产快照
3. 分配执行人和主执行人
4. 执行人通过PDA/手机扫码盘点
5. 实时跟踪盘点进度
6. 完成盘点,生成差异报告
7. 差异审批和处理

#### 场景2: 部门盘点 (Department Inventory)

**触发条件**:
- 部门主管离职/交接
- 部门合并/撤销
- 部门内部管理需要

**盘点范围**: 指定部门下的所有资产

**业务流程**:
1. 选择盘点部门
2. 创建盘点任务(类型=部门盘)
3. 部门成员执行盘点
4. 结果汇总到部门主管
5. 部门主管确认盘点结果

#### 场景3: 分类盘点 (Category Inventory)

**触发条件**:
- 特定资产类别专项盘点(如IT设备、办公家具)
- 高价值资产重点盘点
- 易耗品定期盘点

**盘点范围**: 指定资产分类下的所有资产

**业务流程**:
1. 选择资产分类
2. 创建盘点任务(类型=分类盘)
3. 专业人员/设备管理员盘点
4. 生成分类盘点报告

#### 场景4: 抽盘 (Partial Inventory)

**触发条件**:
- 日常资产抽检
- 资产管理抽查
- 内部控制检查

**盘点范围**: 随机抽取N%资产

**业务流程**:
1. 设置抽盘比例(如10%、20%)
2. 系统随机生成待盘资产列表
3. 执行人按清单盘点
4. 抽盘结果推算总体准确率

---

## 2. 用户角色与权限

### 2.1 角色定义

| 角色 | 职责 | 权限范围 |
|------|------|----------|
| **系统管理员** | 系统最高权限管理 | 全部权限,包括所有盘点任务的创建、分配、执行、完成、差异处理,以及系统配置 |
| **资产管理员** | 资产日常管理 | 创建盘点任务、分配执行人、查看所有盘点结果、处理差异、生成盘点报告 |
| **部门管理员** | 部门资产管理 | 创建本部门盘点任务、查看本部门盘点结果、分配本部门人员执行盘点 |
| **盘点执行人** | 执行盘点操作 | 查看分配给自己的任务、执行扫码盘点、提交盘点结果、查看本人盘点历史 |
| **普通用户** | 资产使用人 | 查看自己保管的资产盘点状态、确认资产信息 |

### 2.2 权限矩阵

| 操作 | 系统管理员 | 资产管理员 | 部门管理员 | 盘点执行人 | 普通用户 |
|------|-----------|-----------|-----------|-----------|---------|
| 创建盘点任务 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 分配执行人 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 开始盘点 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 执行盘点(扫码) | ✅ | ✅ | ✅ | ✅(仅分配的任务) | ❌ |
| 查看所有盘点结果 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 查看本人盘点记录 | ✅ | ✅ | ✅ | ✅ | ✅(仅保管的资产) |
| 处理盘点差异 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 完成盘点任务 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 生成盘点报告 | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |
| 批量操作(删除/恢复) | ✅ | ✅ | ✅(仅本部门) | ❌ | ❌ |

---

## 3. 公共模型引用声明

### 3.1 后端公共基类引用

本模块严格遵循GZEAMS公共基类架构,所有组件均继承对应的公共基类,确保代码一致性和可维护性。

| 基类 | 路径 | 本模块使用类 | 说明 |
|------|------|--------------|------|
| **BaseModel** | `apps/common/models.py` | InventoryTask, InventorySnapshot, InventoryScan, InventoryDifference, InventoryTaskExecutor | 提供组织隔离(organization外键)、软删除(is_deleted+deleted_at)、审计字段(created_by/updated_by/created_at/updated_at)、custom_fields JSONB动态字段支持 |
| **BaseModelSerializer** | `apps/common/serializers/base.py` | 所有盘点相关序列化器 | 自动序列化公共字段(id/org/is_deleted/deleted_at/created_at/updated_at/created_by)、审计信息、custom_fields、嵌套组织/创建人信息 |
| **BaseModelViewSetWithBatch** | `apps/common/viewsets/base.py` | InventoryTaskViewSet, InventoryScanViewSet | 自动应用组织隔离过滤(get_queryset)、软删除处理(perform_destroy调用soft_delete)、批量操作接口(batch-delete/batch-restore/batch-update)、审计字段自动设置(perform_create设置created_by/org) |
| **BaseCRUDService** | `apps/common/services/base_crud.py` | InventoryService | 提供统一CRUD方法(create/update/delete/restore/get/query/paginate)、自动组织隔离、软删除支持、分页响应标准化 |
| **BaseModelFilter** | `apps/common/filters/base.py` | InventoryTaskFilter, InventoryScanFilter | 自动支持时间范围过滤(created_at_from/to, updated_at_from/to)、创建人过滤(created_by)、软删除状态过滤(is_deleted) |

### 3.2 前端公共组件引用

| 组件类型 | 路径 | 本模块使用场景 |
|----------|------|----------------|
| **DynamicForm** | `src/components/engine/DynamicForm.vue` | 盘点任务创建/编辑表单,动态渲染表单字段 |
| **FieldRenderer** | `src/components/engine/FieldRenderer.vue` | 动态渲染盘点任务字段,根据元数据自动选择组件类型 |
| **API Client** | `src/utils/request.js` | 所有API调用,统一错误处理、请求/响应拦截、loading状态管理 |
| **BaseTable** | `src/components/common/BaseTable.vue` | 盘点任务列表、扫描记录列表,提供统一的表格功能(排序、筛选、分页) |

### 3.3 公共服务引用

| 服务 | 路径 | 说明 |
|------|------|------|
| **组织隔离** | `apps.common.models.TenantManager` | 所有查询自动应用organization过滤,确保数据隔离 |
| **软删除** | `BaseModel.soft_delete()` | 删除操作使用软删除,不物理删除数据,支持恢复 |
| **审计日志** | `BaseModel` 审计字段 | 自动记录创建人、创建时间、更新人、更新时间 |

### 3.4 架构优势

通过继承公共基类,本模块自动获得:

1. **组织隔离**: 无需手动编写organization过滤逻辑,自动确保数据安全
2. **软删除**: 删除的资产/任务不会真正删除,可随时恢复
3. **审计追踪**: 所有操作都有完整的创建人、创建时间等审计信息
4. **批量操作**: 自动获得批量删除、批量恢复、批量更新等企业级功能
5. **动态扩展**: 通过custom_fields JSONB字段支持低代码动态配置
6. **代码复用**: 减少重复代码,提高开发效率和可维护性

---

## 4. 数据模型设计

### 4.1 核心数据模型

#### 4.1.1 InventoryTask (盘点任务)

**继承**: `BaseModel`

**核心字段**:
- `task_code`: 任务编号(唯一,如PD20240115001)
- `task_name`: 任务名称
- `inventory_type`: 盘点类型(full/partial/department/category)
- `status`: 任务状态(draft/pending/in_progress/completed/cancelled)
- `planned_date`: 计划日期
- `planned_by`: 创建人(FK → User)
- `executors`: 执行人(M2M → User, through InventoryTaskExecutor)
- `total_count`: 应盘数量
- `scanned_count`: 已盘数量
- `normal_count`: 正常数量
- `surplus_count`: 盘盈数量
- `missing_count`: 盘亏数量
- `damaged_count`: 损坏数量

**自动获得**(继承BaseModel):
- `organization`: 组织(FK) - 多组织隔离
- `is_deleted`, `deleted_at` - 软删除
- `created_at`, `updated_at` - 审计时间
- `created_by` - 创建人(FK)
- `custom_fields` - JSONB动态字段

#### 4.1.2 InventorySnapshot (盘点快照)

**继承**: `BaseModel`

**核心字段**:
- `task`: 盘点任务(FK → InventoryTask)
- `asset`: 资产(FK → Asset)
- `asset_code`: 资产编码(冗余,不可变)
- `asset_name`: 资产名称(冗余,不可变)
- `asset_status`: 资产状态(冗余,不可变)
- `custodian_id`: 保管人ID(冗余,不可变)
- `custodian_name`: 保管人姓名(冗余,不可变)
- `location_id`: 存放地点ID(冗余,不可变)
- `location_name`: 存放地点(冗余,不可变)
- `snapshot_data`: 完整快照(JSON)

**设计目的**:
- 不可变记录,确保盘点结果不受后续业务变更影响
- 任务创建时一次性生成,盘点期间只读
- 用于对比盘点结果,识别差异

#### 4.1.3 InventoryScan (盘点扫描记录)

**继承**: `BaseModel`

**核心字段**:
- `task`: 盘点任务(FK → InventoryTask)
- `asset`: 资产(FK → Asset, nullable)
- `scanned_by`: 扫描人(FK → User)
- `scanned_at`: 扫描时间
- `scan_method`: 扫描方式(qr/rfid/manual)
- `scan_status`: 盘点状态(normal/damaged/missing/location_changed/surplus)
- `original_location`: 原存放地点
- `actual_location`: 实际存放地点
- `original_custodian`: 原保管人
- `actual_custodian`: 实际保管人
- `photos`: 照片(JSON数组)
- `remark`: 备注
- `latitude`, `longitude`: GPS坐标

#### 4.1.4 InventoryDifference (盘点差异)

**继承**: `BaseModel`

**核心字段**:
- `task`: 盘点任务(FK → InventoryTask)
- `asset`: 资产(FK → Asset, nullable, 盘盈时为null)
- `difference_type`: 差异类型(loss/surplus/damaged/location_mismatch/custodian_mismatch)
- `description`: 差异描述
- `status`: 处理状态(pending/confirmed/resolved/ignored)
- `resolution`: 处理方案
- `resolved_by`: 处理人(FK → User)
- `resolved_at`: 处理时间

### 4.2 资产模型扩展

在现有Asset模型(BaseModel)基础上添加二维码相关字段:

```python
class Asset(BaseModel):
    # ... 现有字段 ...

    # 二维码相关
    qr_code = models.CharField(max_length=500, blank=True)  # JSON数据
    qr_code_url = models.CharField(max_length=500, blank=True)  # 图片URL
    qr_code_printed = models.BooleanField(default=False)  # 已打印
    qr_code_printed_at = models.DateTimeField(null=True, blank=True)  # 打印时间
```

### 4.3 数据模型关系

```
InventoryTask (盘点任务)
    ├── InventoryTaskExecutor (执行人) [M2M through]
    ├── InventorySnapshot (快照) [1:N]
    │   └── Asset (资产) [FK]
    ├── InventoryScan (扫描记录) [1:N]
    │   └── Asset (资产) [FK, nullable]
    └── InventoryDifference (差异) [1:N]
        └── Asset (资产) [FK, nullable]
```

---

## 5. API接口设计

### 5.1 接口列表

#### 5.1.1 盘点任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/tasks/` | 获取任务列表(支持过滤、分页) |
| POST | `/api/inventory/tasks/` | 创建任务 |
| GET | `/api/inventory/tasks/{id}/` | 获取任务详情 |
| PUT/PATCH | `/api/inventory/tasks/{id}/` | 更新任务 |
| DELETE | `/api/inventory/tasks/{id}/` | 删除任务(软删除) |
| POST | `/api/inventory/tasks/{id}/start/` | 开始盘点 |
| POST | `/api/inventory/tasks/{id}/complete/` | 完成盘点 |

#### 5.1.2 盘点统计与查询

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/inventory/tasks/{id}/statistics/` | 获取统计信息 |
| GET | `/api/inventory/tasks/{id}/scanned_assets/` | 获取已盘资产 |
| GET | `/api/inventory/tasks/{id}/unscanned_assets/` | 获取未盘资产 |
| POST | `/api/inventory/tasks/{id}/record_scan/` | 记录扫描 |

#### 5.1.3 批量操作(自动继承)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/inventory/tasks/batch-delete/` | 批量删除 |
| POST | `/api/inventory/tasks/batch-restore/` | 批量恢复 |
| POST | `/api/inventory/tasks/batch-update/` | 批量更新 |
| GET | `/api/inventory/tasks/deleted/` | 获取已删除记录 |
| POST | `/api/inventory/tasks/{id}/restore/` | 恢复单条记录 |

#### 5.1.4 二维码接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assets/qr/generate/` | 批量生成二维码 |
| GET | `/api/assets/{id}/qr/image/` | 获取二维码图片 |
| POST | `/api/assets/qr/print_labels/` | 生成打印标签PDF |

### 5.2 统一响应格式

#### 成功响应

```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    "id": "uuid",
    "task_code": "PD20240115001",
    ...
  }
}
```

#### 列表响应(分页)

```json
{
  "success": true,
  "data": {
    "count": 100,
    "next": "http://api.example.com/api/inventory/tasks/?page=2",
    "previous": null,
    "results": [...]
  }
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据验证失败",
    "details": {
      "task_name": ["该字段不能为空"]
    }
  }
}
```

### 5.3 标准错误码

| 错误码 | HTTP状态 | 说明 |
|--------|----------|------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 |
| UNAUTHORIZED | 401 | 未授权访问 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 资源不存在 |
| task_not_found | 404 | 任务不存在 |
| task_already_started | 400 | 任务已开始,无法修改 |
| task_already_completed | 400 | 任务已完成,无法操作 |
| task_not_started | 400 | 任务未开始,无法记录扫描 |
| asset_not_found | 404 | 资产不存在 |
| invalid_qr_code | 400 | 无效的二维码 |
| checksum_mismatch | 400 | 校验和不匹配 |
| asset_not_in_task | 400 | 资产不在盘点范围内 |

---

## 6. 前端组件设计

### 6.1 页面组件

#### 6.1.1 InventoryTaskList.vue (盘点任务列表)

**路径**: `src/views/inventory/InventoryTaskList.vue`

**功能**:
- 任务列表展示(表格形式)
- 多条件过滤(状态/类型/日期范围/执行人)
- 搜索功能(任务编号/任务名称)
- 批量操作(批量删除、批量恢复)
- 任务状态标签显示
- 进度条可视化
- 操作按钮(详情/开始/执行/删除)

**关键特性**:
- 使用Element Plus Table组件
- 响应式布局,支持移动端
- 实时刷新任务状态
- 权限控制(根据角色显示不同操作)

#### 6.1.2 InventoryTaskExecute.vue (盘点任务执行)

**路径**: `src/views/inventory/InventoryTaskExecute.vue`

**功能**:
- 任务信息展示(应盘/已盘/未盘/进度)
- 二维码扫描区域
- 已盘/未盘资产列表切换
- 扫描结果确认弹窗
- 离线缓存支持
- GPS定位记录

**关键特性**:
- 集成@zxing/library实现扫码
- 支持前后摄像头切换
- 扫描成功震动反馈
- 离线缓存,网络恢复后自动上传
- 实时同步盘点进度

#### 6.1.3 InventoryTaskDetail.vue (盘点任务详情)

**路径**: `src/views/inventory/InventoryTaskDetail.vue`

**功能**:
- 任务基本信息
- 执行人列表
- 盘点统计图表
- 已盘资产列表
- 未盘资产列表
- 差异列表
- 操作日志

### 6.2 业务组件

#### 6.2.1 QRScanner.vue (二维码扫描器)

**路径**: `src/components/inventory/QRScanner.vue`

**Props**:
- `autoStart`: 是否自动启动摄像头(默认true)
- `facingMode`: 摄像头方向('environment'后置/'user'前置)

**Events**:
- `scan`: 扫描成功事件,返回二维码文本
- `error`: 扫描错误事件

**特性**:
- 基于@zxing/library
- 支持多种二维码格式
- 扫描区域高亮
- 成功震动反馈
- 错误提示

#### 6.2.2 ScanResultDialog.vue (扫描结果弹窗)

**路径**: `src/components/inventory/ScanResultDialog.vue`

**Props**:
- `modelValue`: v-model绑定(显示/隐藏)
- `scanData`: 扫描数据对象

**Events**:
- `confirm`: 确认事件,返回盘点结果
- `update:modelValue`: 更新显示状态

**功能**:
- 显示资产信息
- 选择盘点状态(正常/损坏/位置变更/丢失)
- 填写实际位置、保管人
- 上传照片
- 填写备注
- GPS定位

#### 6.2.3 ScannedAssetList.vue (已盘资产列表)

**路径**: `src/components/inventory/ScannedAssetList.vue`

**Props**:
- `taskId`: 任务ID

**功能**:
- 展示已盘资产列表
- 支持搜索、筛选
- 查看扫描详情
- 修改扫描结果(任务未完成时)

#### 6.2.4 UnscannedAssetList.vue (未盘资产列表)

**路径**: `src/components/inventory/UnscannedAssetList.vue`

**Props**:
- `taskId`: 任务ID

**功能**:
- 展示未盘资产列表
- 显示快照信息(编码/名称/保管人/位置)
- 支持搜索、筛选
- 手动录入盘点结果

### 6.3 移动端适配

**响应式设计**:
- 使用Element Plus栅格系统
- 移动端优化布局
- 触摸友好的交互
- PWA支持(可安装到桌面)

**离线支持**:
- IndexedDB缓存扫描记录
- 离线时继续扫码
- 网络恢复后自动同步
- 冲突检测与合并

---

## 7. 测试用例

### 7.1 后端测试

#### 7.1.1 模型测试

**测试类**: `TestInventoryTask`, `TestInventoryScan`, `TestInventorySnapshot`

**测试用例**:
- 创建盘点任务
- 任务进度计算
- 软删除与恢复
- 记录扫描结果
- 生成资产快照
- 差异自动识别

#### 7.1.2 服务测试

**测试类**: `TestInventoryService`

**测试用例**:
- 创建任务并生成快照
- 开始盘点任务
- 记录正常扫描
- 记录异常扫描(损坏/丢失/位置变更)
- 记录盘盈
- 完成盘点任务
- 获取统计数据
- 获取已盘/未盘资产列表

#### 7.1.3 API测试

**测试类**: `TestInventoryAPI`

**测试用例**:
- 获取任务列表(含过滤)
- 创建盘点任务
- 更新盘点任务
- 删除盘点任务(软删除)
- 批量删除任务
- 开始盘点
- 完成盘点
- 记录扫描
- 获取统计信息
- 权限控制测试

### 7.2 前端测试

#### 7.2.1 组件测试

**测试工具**: Vitest + Vue Test Utils

**测试组件**:
- QRScanner: 摄像头启动、扫码成功、错误处理
- ScanResultDialog: 表单验证、数据提交、事件触发
- ScannedAssetList: 列表渲染、搜索筛选、分页
- InventoryTaskExecute: 扫码流程、离线缓存、进度更新

#### 7.2.2 E2E测试

**测试工具**: Playwright

**测试场景**:
- 完整盘点流程(创建任务→扫码盘点→完成)
- 扫码异常处理(损坏/丢失/位置变更)
- 离线扫码与同步
- 批量操作(批量删除)
- 权限控制(不同角色访问)

---

## 8. 附录

### 8.1 二维码数据格式

```json
{
  "type": "asset",
  "version": "1.0",
  "asset_id": "123",
  "asset_code": "ZC001",
  "org_id": "1",
  "checksum": "a1b2c3d4"
}
```

**字段说明**:
- `type`: 类型,固定为"asset"
- `version`: 版本号
- `asset_id`: 资产ID(字符串)
- `asset_code`: 资产编码
- `org_id`: 组织ID
- `checksum`: 校验和(MD5前8位)

**校验和计算**:
```
checksum = MD5(asset_id:asset_code:org_id)[:8]
```

示例:
```
输入: "123:ZC001:1"
MD5: a1b2c3d4e5f6g7h8
checksum: a1b2c3d4
```

### 8.2 标签设计

#### 标签尺寸

| 尺寸 | 适用场景 |
|------|----------|
| 大号 50×30mm | 大型设备、服务器、家具 |
| 中号 40×25mm | 常规资产(电脑、打印机等) |
| 小号 30×20mm | 小型物品(手机、配件) |

#### 标签内容

```
┌─────────────────────┐
│   钩子固定资产       │
│                     │
│  [二维码图]          │
│                     │
│  资产编码: ZC001     │
│  资产名称: MacBook   │
│  购入日期: 2024-01   │
└─────────────────────┘
```

### 8.3 任务状态流转

```
draft(草稿)
    ↓
pending(待执行)
    ↓
in_progress(进行中)
    ↓
completed(已完成)

任何状态 → cancelled(已取消)
```

**状态说明**:
- **draft**: 草稿状态,可修改,未生成快照
- **pending**: 待执行,已生成快照,等待开始
- **in_progress**: 进行中,正在盘点
- **completed**: 已完成,盘点结束
- **cancelled**: 已取消,任务取消

### 8.4 盘点状态枚举

| 值 | 显示 | 颜色(Element Plus) | 说明 |
|----|------|-------------------|------|
| normal | 正常 | success | 资产正常,无差异 |
| location_changed | 位置变更 | warning | 实际位置与快照不符 |
| damaged | 损坏 | danger | 资产损坏 |
| missing | 丢失 | info | 未盘点到资产 |
| surplus | 盘盈 | primary | 扫描到不在任务中的资产 |

### 8.5 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    二维码盘点系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  二维码生成 │  │  标签打印   │  │  扫码盘点   │         │
│  │             │  │             │  │             │         │
│  │ - 自动生成  │  │ - 批量打印  │  │ - PDA扫描   │         │
│  │ - 一物一码  │  │ - 标签模板  │  │ - 手机扫描  │         │
│  │ - 编码规则  │  │ - 打印记录  │  │ - 自动识别  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    盘点管理                           │    │
│  │  InventoryTask (继承 BaseModel)                     │    │
│  │  - 盘点任务创建                                     │    │
│  │  - 盘点进度跟踪                                     │    │
│  │  - 盘点结果统计                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    盘点记录                           │    │
│  │  InventoryScan (继承 BaseModel)                     │    │
│  │  - 扫描记录                                         │    │
│  │  - 盘点状态                                         │    │
│  │  - 差异标记                                         │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.6 技术栈

**后端**:
- Django 5.0 + DRF
- PostgreSQL (JSONB)
- Redis (缓存)
- Celery (异步任务)
- qrcode (二维码生成)
- reportlab (PDF生成)

**前端**:
- Vue 3 (Composition API)
- Vite
- Element Plus
- @zxing/library (扫码)
- Pinia (状态管理)
- Vue Router
- idb (IndexedDB)

**测试**:
- pytest (后端单元测试)
- Vitest (前端单元测试)
- Playwright (E2E测试)

### 8.7 后续阶段

- **Phase 4.2**: RFID批量盘点
- **Phase 4.3**: 盘点快照和差异处理
- **Phase 4.4**: 资产领用归还
- **Phase 4.5**: 盘点对账
