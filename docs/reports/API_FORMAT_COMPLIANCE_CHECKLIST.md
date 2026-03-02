# API响应格式规范检查清单

## 文档信息

| 项目 | 说明 |
|------|------|
| 文档版本 | v1.0 |
| 创建日期 | 2026-01-17 |
| 适用范围 | 所有PRD中的API接口定义 |
| 参考标准 | CLAUDE.md API Response Standards |

---

## 一、成功响应格式检查

### 1.1 单条记录响应 (GET /api/resources/{id}/, POST, PUT, PATCH)

**标准格式**:
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        ...
    }
}
```

**检查清单**:

| 检查项 | 要求 | 示例文件 | 状态 |
|--------|------|----------|------|
| success字段 | 必须包含，值为true | phase1_1_asset_category/api.md | ⬜ |
| message字段 | 推荐包含操作描述 | phase1_4_asset_crud/backend.md | ✅ |
| data字段 | 必须包含，包装实际数据 | phase1_2_multi_organization/api.md | ⬜ |
| 数据嵌套 | 实际数据必须在data对象内 | 所有PRD | ⬜ |

### 1.2 列表响应 (GET /api/resources/)

**标准格式**:
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "url",
        "previous": null,
        "results": [...]
    }
}
```

**检查清单**:

| 检查项 | 要求 | 状态 |
|--------|------|------|
| success字段 | 必须包含，值为true | ⬜ |
| data字段 | 必须包含，包装分页数据 | ⬜ |
| count字段 | 总记录数 | ⬜ |
| next字段 | 下一页URL | ⬜ |
| previous字段 | 上一页URL | ⬜ |
| results字段 | 数据数组 | ⬜ |
| ❌ 禁止 | 直接返回DRF原生格式 {count, next, results} | ⬜ |

---

## 二、错误响应格式检查

### 2.1 标准错误响应

**标准格式**:
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {...}
    }
}
```

**检查清单**:

| 检查项 | 要求 | 状态 |
|--------|------|------|
| success字段 | 必须包含，值为false | ⬜ |
| error对象 | 必须包含，包装错误信息 | ⬜ |
| error.code | 错误码（见标准错误码表） | ⬜ |
| error.message | 错误描述信息 | ⬜ |
| error.details | 可选，详细错误信息 | ⬜ |

### 2.2 标准错误码

| 错误码 | HTTP状态 | 说明 | 使用场景 |
|--------|----------|------|----------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 | 字段验证失败、格式错误 |
| UNAUTHORIZED | 401 | 未授权访问 | 未登录、token无效 |
| PERMISSION_DENIED | 403 | 权限不足 | 无权限访问资源 |
| NOT_FOUND | 404 | 资源不存在 | 记录不存在 |
| METHOD_NOT_ALLOWED | 405 | 方法不允许 | 不支持的HTTP方法 |
| CONFLICT | 409 | 资源冲突 | 唯一约束冲突 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 | 跨组织访问 |
| SOFT_DELETED | 410 | 资源已软删除 | 访问已删除记录 |
| RATE_LIMIT_EXCEEDED | 429 | 请求频率超限 | 触发限流 |
| SERVER_ERROR | 500 | 服务器内部错误 | 未捕获异常 |

**禁止使用的自定义错误码**:
- ❌ duplicate_code → 使用 VALIDATION_ERROR
- ❌ invalid_parent → 使用 VALIDATION_ERROR
- ❌ has_children → 使用 VALIDATION_ERROR + details说明

---

## 三、批量操作响应检查

### 3.1 批量删除/恢复/更新

**请求格式**:
```json
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}
```

**标准响应 (全部成功)**:
```json
{
    "success": true,
    "message": "批量删除完成",
    "summary": {
        "total": 3,
        "succeeded": 3,
        "failed": 0
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": true},
        {"id": "uuid3", "success": true}
    ]
}
```

**标准响应 (部分失败)**:
```json
{
    "success": false,
    "message": "批量删除完成（部分失败）",
    "summary": {
        "total": 3,
        "succeeded": 2,
        "failed": 1
    },
    "results": [
        {"id": "uuid1", "success": true},
        {"id": "uuid2", "success": false, "error": "记录不存在"},
        {"id": "uuid3", "success": true}
    ]
}
```

**检查清单**:

| 检查项 | 要求 | 状态 |
|--------|------|------|
| success字段 | 部分失败时为false | ⬜ |
| message字段 | 描述操作结果 | ⬜ |
| summary对象 | 必须包含 | ⬜ |
| summary.total | 总数 | ⬜ |
| summary.succeeded | 成功数 | ⬜ |
| summary.failed | 失败数 | ⬜ |
| results数组 | 每个ID的结果 | ⬜ |

---

## 四、常见违规模式与修正

### 4.1 DRF原生分页格式

**❌ 错误**:
```json
{
    "count": 100,
    "next": null,
    "results": [...]
}
```

**✅ 正确**:
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

### 4.2 缺少success字段

**❌ 错误**:
```json
{
    "id": "uuid",
    "code": "ASSET001"
}
```

**✅ 正确**:
```json
{
    "success": true,
    "data": {
        "id": "uuid",
        "code": "ASSET001"
    }
}
```

### 4.3 自定义错误码

**❌ 错误**:
```json
{
    "success": false,
    "error_code": "duplicate_code",
    "error_message": "编码已存在"
}
```

**✅ 正确**:
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求数据验证失败",
        "details": {
            "code": ["该编码已存在"]
        }
    }
}
```

---

## 五、API文档修正优先级

### 🔴 高优先级 (立即修正)

1. **所有列表端点**: 添加 `success` 和 `data` 包装器
2. **所有成功响应**: 确保 `success: true` 字段存在
3. **所有错误响应**: 使用标准 `error` 对象结构
4. **自定义错误码**: 替换为10种标准错误码

### 🟡 中优先级 (2周内)

5. **批量操作响应**: 确保包含 `summary` 对象
6. **message字段**: 为所有操作添加描述性消息
7. **HTTP状态码**: 确保与错误码对应关系正确

### 🟢 低优先级 (持续改进)

8. 创建API响应格式自动化验证工具
9. 更新API文档生成模板
10. 建立API变更审查流程

---

## 六、修正文件清单

| Phase | 文件 | 主要问题 | 优先级 |
|-------|------|---------|--------|
| Phase 1 | phase1_1_asset_category/api.md | Tree API缺少包装 | 🔴 |
| Phase 1 | phase1_4_asset_crud/api.md | 列表使用total非count | 🔴 |
| Phase 2 | phase2_4_org_enhancement/api.md | 部分端点缺少success | 🟡 |
| Phase 3 | phase3_2_workflow_engine/api.md | 任务列表DRF原生格式 | 🔴 |
| Phase 4 | phase4_5_inventory_reconciliation/api.md | 自定义错误码 | 🔴 |
| Phase 5 | phase5_0_integration_framework/api.md | 集成日志格式不统一 | 🟡 |

---

**检查清单版本**: v1.0
**最后更新**: 2026-01-17
**下次审查**: PRD修正后
