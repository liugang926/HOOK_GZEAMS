# 实施计划：动态对象文件/附件字段支持

## 文档信息

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-01-29 |
| 预计工期 | 分 3 个阶段实施 |

---

## 一、阶段划分

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 1 | 基础文件上传/管理功能 | P0 |
| Phase 2 | 图片增强功能（压缩/裁剪/预览） | P1 |
| Phase 3 | 高级特性（水印/批量下载/特殊场景） | P2 |

---

## 二、Phase 1: 基础文件上传/管理 (P0)

### 2.1 后端实施

#### 新建文件

| 文件路径 | 说明 |
|---------|------|
| `backend/apps/system/viewsets/system_file.py` | SystemFileViewSet |
| `backend/apps/system/serializers/system_file.py` | SystemFileSerializer |
| `backend/apps/system/services/file_storage.py` | 文件存储服务 |

#### 修改文件

| 文件路径 | 修改内容 |
|---------|----------|
| `backend/apps/system/models.py` | SystemFile 模型增加新字段 |
| `backend/apps/system/urls.py` | 添加 system-files 路由 |

#### 实施步骤

1. **SystemFile 模型扩展**
   - 添加 `thumbnail_path`, `width`, `height`, `is_compressed` 字段
   - 运行 migration

2. **SystemFileSerializer**
   ```python
   class SystemFileSerializer(BaseModelSerializer):
       class Meta(BaseModelSerializer.Meta):
           model = SystemFile
           fields = BaseModelSerializer.Meta.fields + [
               'file_name', 'file_path', 'file_size',
               'file_type', 'file_extension', 'url',
               'thumbnail_url', 'width', 'height'
           ]
   ```

3. **SystemFileViewSet**
   - 继承 `BaseModelViewSetWithBatch`
   - 实现 `upload()` action
   - 实现 `download()` action
   - 实现 `batch_delete()` action

4. **路由注册**
   ```python
   # urls.py
   router.register(r'system-files', SystemFileViewSet, basename='system-file')
   ```

### 2.2 前端实施

#### 新建文件

| 文件路径 | 说明 |
|---------|------|
| `frontend/src/api/systemFile.ts` | 文件上传/管理 API |
| `frontend/src/utils/imageProcessor.ts` | 图片处理工具 |
| `frontend/src/components/engine/fields/FileDisplayField.vue` | 只读展示组件 |

#### 修改文件

| 文件路径 | 修改内容 |
|---------|----------|
| `frontend/src/components/engine/fields/AttachmentUpload.vue` | 重构为完整实现 |
| `frontend/src/components/engine/FieldRenderer.vue` | 确认类型映射 |

#### 实施步骤

1. **API 层** (`systemFile.ts`)
   ```typescript
   export interface SystemFile {
     id: string
     fileName: string
     url: string
     fileSize: number
     fileType: string
     thumbnailUrl?: string
   }

   export const uploadFile = (file: File, options?: UploadOptions): Promise<SystemFile>
   export const getFileMetadata = (ids: string[]): Promise<SystemFile[]>
   export const deleteFile = (id: string): Promise<void>
   ```

2. **AttachmentUpload.vue 重构**
   - 实现真实的文件上传逻辑
   - 添加进度条显示
   - 添加文件类型/大小校验
   - 支持多文件上传

3. **FileDisplayField.vue（新建）**
   - 只读模式展示文件列表
   - 显示文件名、大小
   - 提供下载链接

---

## 三、Phase 2: 图片增强功能 (P1)

### 3.1 后端实施

#### 新建文件

| 文件路径 | 说明 |
|---------|------|
| `backend/apps/system/services/image_processor.py` | 图片处理服务 |

#### 实施步骤

1. **图片处理服务**
   - 生成缩略图 (Pillow)
   - 调整图片尺寸
   - 图片格式转换

2. **上传接口增强**
   - 自动生成缩略图
   - 返回缩略图 URL

### 3.2 前端实施

#### 新建文件

| 文件路径 | 说明 |
|---------|------|
| `frontend/src/components/engine/fields/ImageField.vue` | 图片专用组件 |

#### 安装依赖

```bash
npm install compressorjs cropperjs vue-cropperjs
```

#### 实施步骤

1. **ImageField.vue 组件**
   - 图片缩略图展示
   - 点击预览大图 (Element Plus `el-image-viewer`)
   - 拖拽排序 (Sortable.js)
   - 删除确认

2. **图片裁剪**
   - 集成 `vue-cropperjs`
   - 支持固定比例裁剪
   - 支持自由裁剪

3. **图片压缩**
   - 集成 `compressorjs`
   - 超过 maxSize 自动压缩
   - 显示压缩前后大小对比

---

## 四、Phase 3: 高级特性 (P2)

### 4.1 水印功能

#### 前端
- Canvas 叠加文本水印
- 可配置位置（9宫格位置）
- 可配置透明度

#### 后端
- PIL 图片水印处理
- 批量水印处理

### 4.2 批量下载

#### 后端
- 实现 `/api/system-files/batch-download/`
- 打包为 ZIP 返回

#### 前端
- 添加批量下载按钮
- 触发 ZIP 下载

### 4.3 特殊场景

| 功能 | 实现方式 |
|------|----------|
| PDF 首页预览 | 后端 pdf2image |
| 视频首帧 | 后端 ffmpeg |
| 证件自动校正 | 前端图像检测 |
| 多图拼接 | 前端 canvas |

---

## 五、文件清单

### 5.1 后端文件

```
backend/apps/system/
├── models.py                              # 修改：SystemFile 增加字段
├── urls.py                                # 修改：添加路由
├── serializers/
│   └── system_file.py                     # 新建
├── viewsets/
│   └── system_file.py                     # 新建
└── services/
    ├── file_storage.py                    # 新建
    └── image_processor.py                 # 新建 (Phase 2)
```

### 5.2 前端文件

```
frontend/src/
├── api/
│   └── systemFile.ts                      # 新建
├── components/engine/
│   ├── FieldRenderer.vue                  # 修改：确认映射
│   └── fields/
│       ├── AttachmentUpload.vue           # 修改：重构
│       ├── ImageField.vue                 # 新建 (Phase 2)
│       └── FileDisplayField.vue           # 新建
└── utils/
    └── imageProcessor.ts                  # 新建
```

---

## 六、依赖清单

### 6.1 后端依赖

```python
# requirements.txt
Pillow~=10.0.0          # 图片处理 (Phase 1+)
python-magic~=0.4.27    # 文件类型检测 (Phase 1)
pdf2image~=1.16.0       # PDF 转图片 (Phase 3，可选)
```

### 6.2 前端依赖

```json
{
  "compressorjs": "^1.2.1",      // 图片压缩 (Phase 2)
  "cropperjs": "^1.6.1",         // 图片裁剪 (Phase 2)
  "vue-cropperjs": "^4.1.0",     // Vue 裁剪组件 (Phase 2)
  "sortablejs": "^1.15.0",       // 拖拽排序 (Phase 2)
  "v-viewer": "^3.0.0"           // 图片预览 (Phase 2)
}
```

---

## 七、测试计划

### 7.1 单元测试

| 测试文件 | 测试内容 |
|---------|----------|
| `backend/apps/system/tests/test_system_file_api.py` | API 端点测试 |
| `backend/apps/system/tests/test_image_processor.py` | 图片处理测试 |

### 7.2 集成测试

| 场景 | 测试内容 |
|------|----------|
| 上传文件 | 成功上传、大小校验、类型校验 |
| 查看文件 | 列表展示、缩略图显示 |
| 下载文件 | 单文件下载、批量下载 |
| 删除文件 | 软删除、关联数据清理 |
| 图片裁剪 | 裁剪、比例锁定 |
| 图片压缩 | 超大文件自动压缩 |

---

## 八、上线检查清单

- [ ] Migration 运行成功
- [ ] API 路由注册成功
- [ ] 前端组件渲染正常
- [ ] 文件上传功能正常
- [ ] 文件下载功能正常
- [ ] 图片预览功能正常
- [ ] 错误提示正确显示
- [ ] 权限控制生效
- [ ] 组织隔离生效
- [ ] 软删除正常工作

---

## 九、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 存储空间不足 | 无法上传 | 配置存储配额、清理旧文件 |
| 大文件上传超时 | 上传失败 | 前端分片上传、后端异步处理 |
| 恶意文件上传 | 安全风险 | 文件类型严格校验、病毒扫描 |
| 并发上传冲突 | 数据不一致 | 使用事务、乐观锁 |
