---
description: Validate PRD documents against GZEAMS project standards
---

You are validating a PRD document for the GZEAMS project. Check the following:

## Required PRD Sections

The PRD MUST contain these sections:
1. **功能概述与业务场景** (Feature Overview & Business Scenarios)
2. **用户角色与权限** (User Roles & Permissions)
3. **公共模型引用声明** (Public Model Reference Declaration) - **REQUIRED**
4. **数据模型设计** (Data Model Design)
5. **API接口设计** (API Interface Design)
6. **前端组件设计** (Frontend Component Design)
7. **测试用例** (Test Cases)

## Public Model Reference Declaration Format

The PRD MUST include a table like this:

```markdown
## 公共模型引用

| 组件类型 | 基类 | 引用路径 | 自动获得功能 |
|---------|------|---------|-------------|
| Model | BaseModel | apps.common.models.BaseModel | 组织隔离、软删除、审计字段、custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | 公共字段序列化 |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | 组织过滤、软删除、批量操作 |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | 时间范围过滤、用户过滤 |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | 统一CRUD方法 |
```

## API Format Standards

API endpoints MUST follow the unified format:
- List: `GET /api/{resource}/`
- Create: `POST /api/{resource}/`
- Detail: `GET /api/{resource}/{id}/`
- Update: `PUT/PATCH /api/{resource}/{id}/`
- Delete: `DELETE /api/{resource}/{id}/`
- Batch: `POST /api/{resource}/batch-{action}/`

Error responses MUST use predefined error codes:
- VALIDATION_ERROR (400)
- UNAUTHORIZED (401)
- PERMISSION_DENIED (403)
- NOT_FOUND (404)
- CONFLICT (409)
- SERVER_ERROR (500)

## i18n Requirements

- All user-facing text MUST have i18n keys
- Keys should follow: `module.page.section.field` pattern
- Include both `en-US` and `zh-CN` translations

## Validation Process
1. Read the PRD document
2. Check each required section exists
3. Verify the Public Model Reference table is present
4. Check API format compliance
5. Check i18n key coverage
6. Report findings with:
   - Missing sections (if any)
   - Format violations (if any)
   - Overall assessment: PASS / FAIL

Begin validation now.
