# PRD - Default Layout Persistence and Active Layout Consistency
Date: 2026-02-05

## 1. Background and Problem
The current default layout can be a runtime-generated template instead of a persisted entity. This causes:
- Layout designer view does not match the actual detail page
- Saving/editing behavior is inconsistent
- Low-code configurations are not traceable or governable

## 2. Goals
- Default layouts become persisted system assets
- Designer, detail pages, and preview use the same active layout resolution strategy
- Preserve low-code benefits: evolvability, governance, traceability

## 3. Non-Goals
- No approval workflow changes in this phase
- No full rewrite of the layout generator, only targeted enhancements

## 4. User Stories
- As an admin, I want new objects to automatically get editable default layouts
- As a configurator, I want the designer to match the actual detail page
- As ops, I want default layouts to be versioned and rollbackable

## 5. Scope
### 5.1 Default Layout Persistence
- New object creation should create persisted PageLayout records (form/list/detail)
- Defaults should be is_default=true and status=published
- Newly created objects are immediately editable in the designer

### 5.2 Active Layout Resolution
Unified priority order:
1. Custom published layout
2. Default published layout
3. Generated template (fallback only)

### 5.3 Designer Behavior
- Open with active layout by default
- When editing, create or clone into an editable custom layout

## 6. Functional Requirements
### Backend
- On object creation, generate default layouts if missing
- On metadata sync, ensure missing defaults are created
- Default endpoint returns generated config when no persisted default exists

### Frontend
- Designer loads active layout when no explicit layoutId
- Save flow ensures required structural fields are present (section.id/type, field.id)

## 7. UX and Behavior
- Designer header shows layout source (default/active/custom)
- If no layout exists, show message: default generated and ready to edit

## 8. Data Model
PageLayout must include:
- layout_type, layout_config
- is_default, is_active, status
- version, created_by

## 9. Compatibility and Migration
- Run a one-time default layout creation for existing objects
- Do not overwrite existing custom layouts

## 10. Risks and Mitigations
- Risk: default layout generation affects existing custom layouts
  - Mitigation: create defaults only if missing
- Risk: layout schema errors on save
  - Mitigation: frontend sanitizes structure before save

## 11. Acceptance Criteria
- New objects have persisted default layouts and are editable
- Designer view matches the actual detail page layout
- Saving layout does not trigger schema validation errors

## 12. Milestones
- M1: Default layout persistence (backend)
- M2: Designer active layout loading (frontend)
- M3: Batch creation for existing objects


## 13. Architecture Overview
### 13.1 Components
- Backend: BusinessObject, PageLayout, LayoutGenerator, Metadata Sync Service
- Frontend: Layout Designer, Active Layout Loader, Save Sanitizer

### 13.2 High-Level Diagram (Text)
BusinessObject
  -> Metadata Sync Service
     -> LayoutGenerator
        -> PageLayout (persisted default)
  -> Active Layout Resolver (API)
     -> Detail Page / Designer

## 14. API Design
### 14.1 Active Layout
- GET /api/system/page-layouts/get_active_layout/
- Params: object_code, mode
- Response: layout_config (resolved by priority)

### 14.2 Default Layout
- GET /api/system/page-layouts/default/{objectCode}/{layoutType}
- Returns persisted default if exists, otherwise generated config

### 14.3 Layout CRUD
- POST /api/system/page-layouts/
- PATCH /api/system/page-layouts/{id}/
- POST /api/system/page-layouts/{id}/publish/

## 15. Data Flow
### 15.1 New Object Creation
1. BusinessObject created
2. Metadata sync ensures default layouts exist
3. Default layouts persisted with is_default=true

### 15.2 Designer Open
1. If layoutId present -> load that layout
2. Else load active layout via get_active_layout
3. If none -> load default layout

### 15.3 Save Layout
1. Frontend sanitizes layoutConfig (section.id/type, field.id)
2. PATCH layout
3. Publish optional

## 16. Risks Matrix
| Risk | Impact | Likelihood | Mitigation |
| --- | --- | --- | --- |
| Default layout missing after object creation | High | Medium | Sync step creates missing defaults |
| Layout schema invalid on save | High | Medium | Frontend sanitizer + backend validation |
| Active layout mismatches designer | Medium | Medium | Unified active resolver + preview toggle |
| Performance: extra layout queries | Low | Low | Cache active layout per object |

## 17. Open Questions
- Should active layout be cached per org/user?
- Should default layouts be re-generated when fields change?
