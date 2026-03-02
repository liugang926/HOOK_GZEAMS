# Common Base Features: 实施步骤

## 任务概述

本模块分阶段实施，确保不影响现有功能，逐步迁移到统一的公共基类体系。

---

## 实施阶段模型

### 阶段时间估算模型

| 阶段 | 名称 | 工作量 | 依赖 | 产出物 |
|------|------|--------|------|--------|
| Phase 1 | 后端基类实现 | 14.5h | - | BaseModelSerializer, ViewSet, Filter, Service |
| Phase 2 | API规范实现 | 6.5h | Phase 1 | BaseResponse, ExceptionHandler, 错误码 |
| Phase 3 | 前端组件实现 | 11h | Phase 2 | BaseListPage, BaseFormPage, BaseDetailPage |
| Phase 4 | 迁移试点 | 8h | Phase 3 | 试点模块迁移验证 |
| Phase 5 | 全面迁移 | 24h | Phase 4 | 所有模块迁移完成 |
| Phase 6 | 文档与测试 | 12h | Phase 5 | 单元测试、集成测试、文档 |

### 迁移检查清单模型

| 检查项 | 后端要求 | 前端要求 | 验证方法 |
|--------|---------|---------|---------|
| Serializer | 继承BaseModelSerializer | - | 单元测试 |
| ViewSet | 继承BaseModelViewSetWithBatch | - | API测试 |
| Filter | 继承BaseModelFilter | - | 过滤测试 |
| Service | 继承BaseCRUDService | - | Service测试 |
| 页面 | - | 使用BaseListPage/FormPage | 功能测试 |
| API | 符合api.md规范 | - | 接口测试 |

### 风险评估模型

| 风险 | 概率 | 影响 | 应对措施 | 责任人 |
|------|------|------|---------|--------|
| 现有代码不兼容 | 低 | 高 | 保留旧代码路径，逐步迁移 | 后端Leader |
| 性能下降 | 中 | 中 | 性能基准测试对比 | 性能组 |
| 学习成本 | 低 | 低 | 提供详细文档和示例 | 培训组 |
| 调试困难 | 中 | 中 | 添加详细的日志记录 | 开发组 |

---

## 1. 实施阶段划分

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        实施阶段规划                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │   Phase 1      │  │   Phase 2      │  │   Phase 3      │            │
│  │   后端基类      │  │   API 规范     │  │   前端组件     │            │
│  │                │  │                │  │                │            │
│  │ - Serializer   │  │ - Response     │  │ - ListPage     │            │
│  │ - ViewSet      │  │ - Exception    │  │ - FormPage     │            │
│  │ - Filter       │  │ - Error Codes  │  │ - DetailPage   │            │
│  │ - Service      │  │ - Batch Ops    │  │                │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │   Phase 4      │  │   Phase 5      │  │   Phase 6      │            │
│  │   迁移试点      │  │   全面迁移      │  │   文档与测试   │            │
│  │                │  │                │  │                │            │
│  │ - 选择1-2个模块 │  │ - 所有模块迁移  │  │ - 单元测试     │            │
│  │   进行试点迁移  │  │ - 清理旧代码    │  │ - 集成测试     │            │
│  │ - 验证方案      │  │ - 性能优化      │  │ - 开发文档     │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Phase 1: 后端基类实现（P0）

### 2.1 任务清单

| 序号 | 任务 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| 1.1 | 创建 `apps/common/serializers/` 目录 | 0.5h | P0 |
| 1.2 | 实现 `BaseModelSerializer` | 2h | P0 |
| 1.3 | 创建 `apps/common/viewsets/` 目录 | 0.5h | P0 |
| 1.4 | 实现 `BaseModelViewSet` | 3h | P0 |
| 1.5 | 实现 `BatchOperationMixin` | 2h | P0 |
| 1.6 | 创建 `apps/common/filters/` 目录 | 0.5h | P0 |
| 1.7 | 实现 `BaseModelFilter` | 1.5h | P0 |
| 1.8 | 创建 `apps/common/services/base_crud.py` | 0.5h | P0 |
| 1.9 | 实现 `BaseCRUDService` | 3h | P0 |
| 1.10 | 更新 Django settings 配置 | 1h | P0 |

**合计工作量**: ~14.5 小时

### 2.2 实施步骤

#### 步骤 1: 创建目录结构

```bash
# 在 backend/apps/common/ 下创建
mkdir -p serializers
mkdir -p viewsets
mkdir -p filters
```

#### 步骤 2: 实现各基类（代码见 backend.md）

#### 步骤 3: 更新配置

```python
# backend/config/settings.py
INSTALLED_APPS += [
    'apps.common.serializers',
    'apps.common.viewsets',
    'apps.common.filters',
]
```

---

## 3. Phase 2: API 规范实现（P0）

### 3.1 任务清单

| 序号 | 任务 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| 2.1 | 创建 `apps/common/responses/` 目录 | 0.5h | P0 |
| 2.2 | 实现 `BaseResponse` 类 | 2h | P0 |
| 2.3 | 创建 `apps/common/handlers/` 目录 | 0.5h | P0 |
| 2.4 | 实现 `custom_exception_handler` | 2h | P0 |
| 2.5 | 定义业务异常类 | 1h | P0 |
| 2.6 | 配置 DRF 异常处理器 | 0.5h | P0 |

**合计工作量**: ~6.5 小时

### 3.2 实施步骤

#### 步骤 1: 实现响应类（代码见 api.md）

#### 步骤 2: 实现异常处理器（代码见 api.md）

#### 步骤 3: 配置 DRF

```python
# backend/config/settings.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.common.handlers.exceptions.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

## 4. Phase 3: 前端组件实现（P2）

### 4.1 任务清单

| 序号 | 任务 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| 3.1 | 创建 `frontend/src/components/common/` 目录 | 0.5h | P2 |
| 3.2 | 实现 `BaseListPage.vue` | 4h | P2 |
| 3.3 | 实现 `BaseFormPage.vue` | 3h | P2 |
| 3.4 | 实现 `BaseDetailPage.vue` | 2h | P2 |
| 3.5 | 实现 `BaseAuditInfo.vue` | 1h | P2 |
| 3.6 | 更新组件导出 | 0.5h | P2 |

**合计工作量**: ~11 小时

### 4.2 实施步骤

#### 步骤 1: 创建目录

```bash
# 在 frontend/src/components/ 下创建
mkdir common
```

#### 步骤 2: 实现各组件（代码见 frontend.md）

#### 步骤 3: 更新导出

```javascript
// frontend/src/components/common/index.js
export { default as BaseListPage } from './BaseListPage.vue'
export { default as BaseFormPage } from './BaseFormPage.vue'
export { default as BaseDetailPage } from './BaseDetailPage.vue'
export { default as BaseAuditInfo } from './BaseAuditInfo.vue'
```

---

## 5. Phase 4: 迁移试点（P1）

### 5.1 选择试点模块

建议选择以下模块之一作为试点：

| 模块 | 理由 | 复杂度 |
|------|------|--------|
| `assets` | 核心模块，使用广泛 | 中 |
| `organizations` | 相对独立，依赖少 | 低 |
| `consumables` | 新模块，代码量小 | 低 |

### 5.2 迁移步骤

#### 步骤 1: 备份现有代码

```bash
# 创建备份分支
git checkout -b backup/common-base-features-migration
git push origin backup/common-base-features-migration
```

#### 步骤 2: 迁移 Serializers

```python
# 旧代码
class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'organization', 'created_at', ...]

# 新代码
from apps.common.serializers.base import BaseModelSerializer

class AssetSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Asset
        fields = BaseModelSerializer.Meta.fields + ['code', 'name', ...]
```

#### 步骤 3: 迁移 ViewSets

```python
# 旧代码
class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def perform_create(self, serializer):
        serializer.save(
            organization_id=get_current_org(),
            created_by=self.request.user
        )

    def perform_destroy(self, instance):
        instance.soft_delete()

# 新代码
from apps.common.viewsets.base import BaseModelViewSetWithBatch

class AssetViewSet(BaseModelViewSetWithBatch):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    # 自动获得所有公共功能
```

#### 步骤 4: 迁移 Filters

```python
# 旧代码
class AssetFilter(filters.FilterSet):
    created_at_from = filters.DateTimeFilter(...)
    created_at_to = filters.DateTimeFilter(...)

# 新代码
from apps.common.filters.base import BaseModelFilter

class AssetFilter(BaseModelFilter):
    # 公共字段自动继承
    code = filters.CharFilter(...)
    class Meta(BaseModelFilter.Meta):
        model = Asset
        fields = BaseModelFilter.Meta.fields + ['code', ...]
```

#### 步骤 5: 迁移 Services

```python
# 旧代码
class AssetService:
    def create(self, data, user):
        return Asset.objects.create(
            organization_id=get_current_org(),
            created_by=user,
            **data
        )

# 新代码
from apps.common.services.base_crud import BaseCRUDService

class AssetService(BaseCRUDService):
    def __init__(self):
        super().__init__(Asset)

    # CRUD 方法自动获得，只需实现业务方法
    def get_by_code(self, code):
        return self.model_class.objects.get(code=code)
```

#### 步骤 6: 测试验证

```bash
# 运行单元测试
pytest apps/assets/tests/

# 手动测试 API
# 1. 创建记录
# 2. 查询列表
# 3. 更新记录
# 4. 批量删除
# 5. 软删除恢复
```

---

## 6. Phase 5: 全面迁移（P1）

### 6.1 迁移顺序

| 批次 | 模块 | 理由 |
|------|------|------|
| 1 | organizations, accounts | 基础模块，优先迁移 |
| 2 | assets, consumables | 核心业务模块 |
| 3 | inventory, procurement | 扩展业务模块 |
| 4 | workflows, notifications | 支撑模块 |
| 5 | lifecycle, mobile | 新模块 |

### 6.2 迁移检查清单

每个模块迁移后，确认以下内容：

- [ ] Serializer 继承 `BaseModelSerializer`
- [ ] ViewSet 继承 `BaseModelViewSetWithBatch`
- [ ] Filter 继承 `BaseModelFilter`
- [ ] Service 继承 `BaseCRUDService`
- [ ] API 使用 `BaseResponse` 返回
- [ ] 单元测试通过
- [ ] 手动功能测试通过

---

## 7. Phase 6: 文档与测试（P1）

### 7.1 测试清单

| 测试类型 | 覆盖范围 |
|---------|---------|
| 单元测试 | 各基类方法 |
| 集成测试 | 基类与业务模块集成 |
| API 测试 | 批量操作、软删除等接口 |
| 性能测试 | 大数据量查询性能 |

### 7.2 文档更新

| 文档 | 更新内容 |
|------|---------|
| `docs/architecture/technical-architecture.md` | 添加公共功能模块说明 |
| `docs/development/backend.md` | 更新后端开发规范 |
| `docs/development/frontend.md` | 更新前端开发规范 |
| `README.md` | 更新项目结构说明 |

---

## 8. 风险与应对

### 8.1 潜在风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 现有代码不兼容 | 高 | 保留旧代码路径，逐步迁移 |
| 性能下降 | 中 | 进行性能基准测试对比 |
| 学习成本 | 低 | 提供详细文档和示例 |
| 调试困难 | 中 | 添加详细的日志记录 |

### 8.2 回滚方案

```bash
# 如果迁移出现问题，可以快速回滚
git checkout main
git branch -D migration-branch
```

---

## 9. 验收标准

### 9.1 功能验收

- [ ] 新建模块可使用所有公共基类
- [ ] 批量操作接口正常工作
- [ ] 软删除/恢复功能正常
- [ ] API 响应格式统一
- [ ] 错误处理机制正常

### 9.2 代码质量验收

- [ ] 代码通过 pylint/flake8 检查
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试用例通过
- [ ] 代码审查通过

---

## 10. 时间估算

| 阶段 | 工作量 | 负责人 |
|------|--------|--------|
| Phase 1: 后端基类 | 14.5h | 后端开发 |
| Phase 2: API 规范 | 6.5h | 后端开发 |
| Phase 3: 前端组件 | 11h | 前端开发 |
| Phase 4: 迁移试点 | 8h | 全栈开发 |
| Phase 5: 全面迁移 | 24h | 全栈开发 |
| Phase 6: 文档与测试 | 12h | 全栈开发 |
| **总计** | **76h** | - |

---

## 11. 后续优化方向

### 11.1 短期优化（3个月内）

1. 添加更多公共字段到 Filter
2. 优化批量操作性能
3. 添加更多前端公共组件

### 11.2 长期优化（6个月内）

1. 实现 AuditLog 审计日志
2. 实现 BaseCache 缓存策略
3. 实现 BaseSearch 全文搜索
