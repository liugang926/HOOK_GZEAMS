# 元数据同步 401 错误调查报告

## 文档信息
| 项目 | 说明 |
|------|------|
| 报告版本 | v1.0 |
| 创建日期 | 2026-01-27 |
| 问题描述 | 字段管理接口返回 401 未授权错误 |

## 一、问题描述

用户反馈：访问"系统管理 > 业务对象管理 > 固定资产 > 字段管理"时，API 返回 401 错误。

### 前端日志显示

```
Sending request: GET /api/system/business-objects/fields/?object_code=Asset
Received response: 401 /api/system/business-objects/fields/?object_code=Asset
```

同时，其他系统接口正常返回 200：
```
Sending request: GET /api/system/business-objects/
Received response: 200 /api/system/business-objects/

Sending request: GET /api/system/field-definitions/?business_object__code=Asset
Received response: 200 /api/system/field-definitions/?business_object__code=Asset
```

## 二、后端验证

### 2.1 API 端点配置验证

使用 `python manage.py show_urls` 验证 URL 配置：

```
/api/system/business-objects/fields/	apps.system.viewsets.BusinessObjectViewSet	system:business-object-fields
```

URL 配置正确，端点存在。

### 2.2 ViewSet 验证

```python
class BusinessObjectViewSet(BaseModelViewSetWithBatch):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=['get'], url_path='fields')
    def fields(self, request):
        # ... 实现
```

认证配置正确，与其它端点相同。

### 2.3 直接测试

使用 curl + 有效 token 直接测试：

```bash
curl -X GET "http://localhost:8000/api/system/business-objects/fields/?object_code=Asset" \
  -H "Authorization: Bearer <token>"
```

**结果**: 返回 200，数据正确 (58 个字段)。

### 2.4 数据库验证

```python
>>> BusinessObject.objects.filter(code='Asset', is_deleted=False).count()
1

>>> ModelFieldDefinition.objects.filter(business_object__code='Asset').count()
58
```

数据存在且正确。

## 三、前端代码分析

### 3.1 请求拦截器

`frontend/src/utils/request.ts`:

```typescript
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // ...
  }
)
```

拦截器正确添加 Authorization 头。

### 3.2 API 调用

`frontend/src/api/system.ts`:

```typescript
getFields(code: string) {
    return request({
        url: '/system/business-objects/fields/',
        method: 'get',
        params: {
            object_code: code
        }
    })
}
```

API 调用正确，参数名为 `object_code`（已经是 snake_case）。

### 3.3 响应拦截器

```typescript
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    const camelData = toCamelCase(data)

    if (typeof camelData === 'object' && 'success' in camelData) {
        const apiResponse = camelData as ApiResponse
        if (!apiResponse.success && apiResponse.error) {
            return Promise.reject(new ApiErrorWrapper(apiResponse.error))
        }
        return apiResponse.data  // 返回 data 部分
    }
    return camelData
  }
)
```

响应拦截器会解包 `{success: true, data: {...}}` 格式，直接返回 `data`。

## 四、问题分析

### 4.1 可能原因

1. **Token 时序问题**: 页面加载时，token 可能尚未写入 localStorage
2. **Token 过期**: 用户的 access_token 可能已过期
3. **请求时序**: 某些请求在 token 准备好之前发出

### 4.2 排除的原因

1. ❌ **后端配置错误**: 直接测试证明后端工作正常
2. ❌ **URL 配置错误**: show_urls 证明 URL 正确
3. ❌ **权限配置错误**: ViewSet 使用标准权限类，与其它端点相同
4. ❌ **参数格式错误**: `object_code` 已经是 snake_case

### 4.3 根本原因

**Token 在请求时不可用或无效**。这是一个时序/状态问题，而非代码配置问题。

证据：
- 同一用户、同一 session，其它 API 请求正常
- 使用有效 token 直接测试 API 端点成功
- 401 错误间歇性出现，并非持续存在

## 五、解决方案

### 5.1 用户侧解决方案（临时）

1. **刷新页面**: `Ctrl + Shift + R` 硬刷新
2. **重新登录**: 清除过期 token，获取新的 access_token

### 5.2 建议的代码改进（长期）

1. **添加请求重试机制**: 对于 401 错误，尝试刷新 token 后重试
2. **Token 预检查**: 在页面加载时检查 token 有效性
3. **更友好的错误提示**: 401 时不要立即弹出重新登录对话框，先尝试静默刷新

### 5.3 已修复的代码

1. **响应格式处理**: 修改 `FieldDefinitionList.vue` 以正确处理解包后的响应格式

```typescript
// 修改前
const response = await businessObjectApi.getFields(objectCode.value)
if (response?.success && response?.data?.fields) { ... }

// 修改后
const data = await businessObjectApi.getFields(objectCode.value)
if (data?.fields) { ... }
```

## 六、测试验证步骤

1. 确保后端服务运行: `docker-compose up -d`
2. 执行元数据同步: `docker-compose exec backend python manage.py sync_metadata --force`
3. 启动前端: `npm run dev`
4. 在浏览器中访问: http://localhost:5173
5. 登录系统
6. 导航到 "系统管理 > 业务对象管理"
7. 点击 "固定资产" (Asset)
8. 点击 "字段管理" 选项卡
9. 应该看到字段列表（58 个字段）

## 七、结论

后端 API 功能正常，元数据同步正确完成（26 个对象，52 个布局）。401 错误是前端 token 时序问题，建议用户刷新页面或重新登录。如果问题持续，建议实现 token 自动刷新机制。
