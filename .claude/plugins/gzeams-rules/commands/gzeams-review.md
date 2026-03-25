---
description: Review code changes against GZEAMS coding standards
---

You are conducting a code review for the GZEAMS project. Check the following standards:

## Backend Standards (Django)

### Model Standards
- All models MUST inherit from `BaseModel` (from `apps.common.models.BaseModel`)
- All models MUST use `TenantManager` (business data) or `GlobalMetadataManager` (metadata)
- NEVER use physical delete - always use `instance.soft_delete()`
- Check for proper `organization` field handling

### Serializer Standards
- All serializers MUST inherit from `BaseModelSerializer`
- Auto-serialized fields: id, organization, is_deleted, deleted_at, created_at, updated_at, created_by, custom_fields

### ViewSet Standards
- All ViewSets MUST inherit from `BaseModelViewSetWithBatch`
- Auto-provided: org filtering, soft delete, audit fields, batch operations

### Service Standards
- All services MUST inherit from `BaseCRUDService`
- Unified CRUD methods with org isolation

### Filter Standards
- All Filters MUST inherit from `BaseModelFilter`

## Comment Standards
- ALL comments MUST be in English
- No Chinese characters in code comments or docstrings
- This includes inline comments, docstrings, class/function descriptions

## Frontend Standards (Vue3)

### i18n Standards
- All user-facing text MUST use i18n keys: `$t('module.key')`
- Do not hardcode Chinese or English text in templates
- i18n keys should follow: `module.page.section.field` pattern

### Error Handling
- NEVER use native `alert()` - use unified error提示 components
- All API errors should be handled through global interceptors

### Component Standards
- Use Composition API only
- Follow TypeScript strict mode

## API Response Standards
- Success response: `{success: true, data: {...}, message: "..."}`
- Error response: `{success: false, error: {code: "...", message: "..."}}`
- Batch operations: `{success: true/false, summary: {total, succeeded, failed}, results: [...]}`

## Security Checks
- Check for SQL injection vulnerabilities
- Check for XSS vulnerabilities (especially in user input handling)
- Validate proper org isolation in queries
- Check for hardcoded secrets or tokens

## Review Process
1. List all changed files
2. For each file, check against the relevant standards above
3. Report any violations with:
   - File path and line number
   - Violation description
   - Suggested fix
4. Provide an overall assessment: PASS / FAIL / WARNINGS

Begin the review now.
