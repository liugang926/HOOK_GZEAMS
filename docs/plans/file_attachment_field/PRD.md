# PRD: 动态对象文件/附件字段支持

## 文档信息

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-01-29 |
| 涉及阶段 | Phase: 动态对象增强 |
| 功能模块 | 低代码引擎 - 字段类型扩展 |

---

## 一、功能概述与业务场景

### 1.1 背景

当前 GZEAMS 低代码平台支持多种字段类型（文本、数字、日期、选择、引用等），但**缺少文件/附件类型的完整支持**。这使得业务对象无法存储合同扫描件、产品图片、审批凭证等关键文件信息。

### 1.2 业务场景

| 场景 | 描述 | 字段类型 |
|------|------|----------|
| 合同管理 | 存储合同扫描件、盖章页 PDF | `file` |
| 商品管理 | 商品主图、详情图（需压缩、裁剪） | `image` |
| 审批流程 | 上传审批凭证、验收单据 | `file` |
| 资产盘点 | 资产照片、现场实拍图 | `image` |
| 档案管理 | 人事档案、证件扫描件 | `file` |

### 1.3 核心需求

1. **动态字段配置** - 管理员可在字段管理中添加 `file`/`image` 类型字段
2. **智能文件处理** - 超大文件自动压缩、图片裁剪、水印添加
3. **统一存储管理** - 所有文件通过 `SystemFile` 模型统一管理
4. **多场景适配** - 列表展示、详情查看、只读/编辑模式
5. **工作流支持** - 流程实例可独立附件，同时能访问业务对象附件

---

## 二、用户角色与权限

| 角色 | 权限 |
|------|------|
| 系统管理员 | 配置文件字段类型、设置大小/格式限制 |
| 业务用户 | 上传、查看、下载自己权限范围内的文件 |
| 审批人 | 查看流程附件，根据节点权限决定是否可删除 |
| 只读用户 | 仅查看/下载，不可上传/删除 |

---

## 三、公共模型引用声明

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |

**SystemFile 模型继承：**
```python
class SystemFile(BaseModel):
    # 已存在模型，无需新建
    # 自动获得: org, is_deleted, deleted_at, created_at, updated_at, created_by
```

---

## 四、数据模型设计

### 4.1 SystemFile 模型（已存在，需增强）

```python
class SystemFile(BaseModel):
    """统一文件管理模型"""

    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)
    file_type = models.CharField(max_length=100, blank=True)
    file_extension = models.CharField(max_length=20, blank=True)

    # 新增字段
    thumbnail_path = models.CharField(max_length=500, blank=True, null=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    is_compressed = models.BooleanField(default=False)
    original_file_id = models.UUIDField(null=True, blank=True)  # 压缩文件关联原始文件

    # 关联对象（便于查询）
    object_code = models.CharField(max_length=100, blank=True)
    instance_id = models.UUIDField(null=True, blank=True)
    field_code = models.CharField(max_length=100, blank=True)
```

### 4.2 动态对象存储结构

```python
# DynamicObjectInstance.custom_fields 存储示例
{
    "contract_files": ["uuid-1", "uuid-2"],           # 文件 ID 数组
    "product_images": ["uuid-3", "uuid-4", "uuid-5"], # 图片 ID 数组
    "amount": 10000
}
```

### 4.3 字段定义配置结构

```python
# FieldDefinition.options 结构
{
    "maxCount": 10,              # 最多上传数量
    "maxSize": 5242880,          # 单文件最大 5MB
    "allowedTypes": [            # 允许的 MIME 类型
        "application/pdf",
        "image/*",
        "application/msword"
    ],

    # 超大文件处理策略
    "oversizeAction": "auto-compress",  # auto-compress | reject | warn

    # 压缩配置
    "compress": {
        "maxWidth": 1920,
        "maxHeight": 1080,
        "quality": 0.85,
        "targetSize": 2097152
    },

    # 裁剪配置（图片专用）
    "crop": {
        "enabled": true,
        "aspectRatio": "16:9",     # 1:1 | 4:3 | 16:9 | free
        "forceCrop": false
    },

    # 水印配置
    "watermark": {
        "enabled": true,
        "text": "CONFIDENTIAL",
        "position": "bottom-right"
    },

    # 缩略图配置
    "thumbnail": {
        "enabled": true,
        "size": [200, 200]
    },

    # 其他功能开关
    "isSortable": true,           # 允许拖拽排序（图片专用）
    "allowBatchDownload": true,   # 允许批量打包下载
    "autoRotate": false           # 自动校正证件方向
}
```

---

## 五、API 接口设计

### 5.1 通用文件管理 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/system-files/upload/` | POST | 上传文件，返回 SystemFile 记录 |
| `/api/system-files/?ids=xxx,yyy` | GET | 批量获取文件元数据 |
| `/api/system-files/{id}/` | GET | 获取单个文件详情 |
| `/api/system-files/{id}/download/` | GET | 下载文件 |
| `/api/system-files/{id}/` | DELETE | 删除文件（软删除） |
| `/api/system-files/batch-delete/` | POST | 批量删除文件 |

### 5.2 上传请求格式

```http
POST /api/system-files/upload/
Content-Type: multipart/form-data

{
    "file": <binary>,
    "object_code": "contract",      # 可选，关联对象
    "instance_id": "uuid",          # 可选，关联实例
    "field_code": "contract_files"  # 可选，关联字段
}
```

### 5.3 上传响应格式

```json
{
    "success": true,
    "data": {
        "id": "uuid-string",
        "file_name": "contract.pdf",
        "file_path": "/uploads/2025/01/xxx.pdf",
        "file_size": 1048576,
        "file_type": "application/pdf",
        "file_extension": ".pdf",
        "url": "/media/uploads/2025/01/xxx.pdf",
        "thumbnail_url": "/media/uploads/2025/01/thumb_xxx.jpg",
        "created_at": "2025-01-29T10:00:00Z"
    }
}
```

### 5.4 动态对象实例中的文件操作

文件通过 `custom_fields` 自动序列化展开：

```http
GET /api/objects/contract/instances/{id}/

Response:
{
    "success": true,
    "data": {
        "id": "uuid",
        "contract_files": [
            {
                "id": "uuid-1",
                "file_name": "contract.pdf",
                "url": "/media/...",
                "file_size": 1048576
            }
        ]
    }
}
```

---

## 六、前端组件设计

### 6.1 组件架构

```
FieldRenderer.vue
    ├── AttachmentUpload.vue   # 通用文件上传（file/attachment 类型）
    │   ├── 文件选择
    │   ├── 进度显示
    │   ├── 类型校验
    │   └── 上传/删除操作
    │
    ├── ImageField.vue         # 图片专用组件
    │   ├── 图片预览（缩略图）
    │   ├── 拖拽排序
    │   ├── 裁剪器（cropperjs）
    │   ├── Lightbox 大图预览
    │   └── 自动压缩提示
    │
    └── FileDisplayField.vue   # 只读展示组件
        ├── 文件列表
        ├── 下载链接
        └── 缩略图展示
```

### 6.2 字段类型映射

| fieldType | 组件 | 用途 |
|-----------|------|------|
| `file` | AttachmentUpload.vue | 通用文件上传 |
| `attachment` | AttachmentUpload.vue | 附件上传（别名） |
| `image` | ImageField.vue | 图片专用（预览/裁剪/排序） |

### 6.3 图片处理流程

```
用户选择图片
    ↓
前端检查文件大小
    ↓
超过 maxSize？
    ├─ 是 → oversizeAction = "auto-compress"
    │        ├─ compressor.js 压缩
    │        ├─ 显示压缩进度
    │        └─ 压缩后预览
    │
    └─ 否 → 直接使用
    ↓
crop.enabled = true？
    ├─ 是 → cropperjs 裁剪器
    │        └─ 用户确认裁剪
    │
    └─ 否 → 跳过
    ↓
watermark.enabled = true？
    ├─ 是 → canvas 叠加水印
    └─ 否 → 跳过
    ↓
上传到 /api/system-files/upload/
    ↓
后端处理（缩略图生成）
    ↓
返回 {id, url, name, size}
    ↓
存储到 form[field] = [id1, id2, ...]
```

---

## 七、特殊场景支持

| 场景 | 配置 | 实现方式 |
|------|------|----------|
| 证件自动校正 | `autoRotate: true` | 前端图像检测 |
| PDF 首页预览 | `pdfPreview: true` | 后端 pdf2image |
| 视频首帧 | `videoThumbnail: true` | 后端 ffmpeg |
| 文档预览 | `officePreview: true` | 集成 OnlyOffice |
| 多图拼接 | `mergeImages: true` | 前端 canvas |
| 批量下载 | `allowBatchDownload: true` | 后端 zip 打包 |

---

## 八、错误代码

| 错误代码 | HTTP 状态 | 描述 |
|---------|-----------|------|
| `FILE_TOO_LARGE` | 413 | 文件超过配置的最大大小 |
| `FILE_TYPE_NOT_ALLOWED` | 400 | 文件类型不在允许列表中 |
| `FILE_COUNT_EXCEEDED` | 400 | 文件数量超过 maxCount |
| `FILE_NOT_FOUND` | 404 | 文件不存在或已删除 |
| `STORAGE_QUOTA_EXCEEDED` | 507 | 存储空间不足 |
| `UPLOAD_FAILED` | 500 | 上传处理失败 |

---

## 九、测试用例

### 9.1 模型层测试

| 用例 | 描述 |
|------|------|
| `test_system_file_creation` | 创建文件记录 |
| `test_soft_delete_file` | 软删除文件 |
| `test_file_organization_isolation` | 组织隔离验证 |

### 9.2 API 测试

| 用例 | 描述 |
|------|------|
| `test_file_upload_success` | 成功上传文件 |
| `test_file_upload_too_large` | 超大文件被拒绝/压缩 |
| `test_file_upload_invalid_type` | 无效文件类型被拒绝 |
| `test_batch_file_metadata` | 批量获取文件元数据 |
| `test_file_download` | 下载文件 |
| `test_file_delete` | 删除文件 |

### 9.3 前端组件测试

| 用例 | 描述 |
|------|------|
| `test_attachment_upload_component` | 文件上传组件渲染 |
| `test_image_crop_functionality` | 图片裁剪功能 |
| `test_image_drag_sort` | 图片拖拽排序 |
| `test_file_validation` | 文件类型/大小校验 |
| `test_compression_warning` | 压缩提示显示 |

---

## 十、依赖项

### 10.1 后端依赖

```python
# requirements.txt 新增
Pillow~=10.0.0          # 图片处理
python-magic~=0.4.27    # 文件类型检测
pdf2image~=1.16.0       # PDF 转图片（可选）
```

### 10.2 前端依赖

```json
{
  "compressorjs": "^1.2.1",      // 前端图片压缩
  "cropperjs": "^1.6.1",         // 图片裁剪
  "vue-cropperjs": "^4.1.0"      // Vue 裁剪组件
}
```
