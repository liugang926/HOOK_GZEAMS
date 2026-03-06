# Relation Group Scope Strategy

## Goal
- Keep related-object group expansion persistence stable across pages.
- Avoid state collision between real object pages and layout designer preview.
- Reuse the same scope protocol for reference lookup preferences/recent records.

## Canonical Rules
1. Business record pages (`detail` / `edit`) share one scope per record.
2. Designer preview uses an isolated virtual scope and must never reuse real record id.

## Scope Builders
- `buildRecordRelationGroupScopeId(recordId, fallbackCode?)`
  - Primary: `recordId`
  - Fallback: `record:${fallbackCode}`
- `buildDesignerRelationGroupScopeId({ mode, layoutId })`
  - Format: `designer-preview:${mode}:${layoutId}`
  - Defaults: `mode=edit`, `layoutId=draft`
- `buildReferenceLookupScopeId({ routeName, routePath, hostObjectCode, hostRecordId, layoutId, layoutMode })`
  - Business pages: `object-detail:*` / `object-edit:*` / `object-create:*`
  - Redirected edit route support: query `action=edit` maps to `object-edit:*`
  - Designer: same isolated scope family `designer-preview:*`

## Applied Entry Points
- `DynamicDetailPage` -> passes `relationGroupScopeId` to `BaseDetailPage`.
- `AssetDetail` / `VoucherDetail` -> passes explicit `relationGroupScopeId`.
- `WysiwygLayoutDesigner` -> passes designer preview scope id.
- `ReferenceField` -> builds `lookupPreferenceScopeId` and passes into `ReferenceLookupDialog`.
- `ReferenceLookupDialog` -> persists column profile/order/width + recent ids with `scope`.
- `useColumnConfig` (list column manager) remains backend-scoped by `user + org + object` and does not use local browser key.
- `scopedStorage.ts` -> unified browser storage key build + scoped/legacy migration primitive.

## Legacy Key Migration
- Lookup columns/profile/recent use one-time read migration:
1. If scoped key is missing but legacy unscoped key exists, move legacy value into scoped key.
2. Remove legacy key after migration/write/clear.
- Related-group expansion also migrates legacy `_record` key into explicit page scope key.
- This keeps old local data usable while converging all new writes to scoped keys.

## Scope Smoke
- Command: `npm run test:e2e:scope-smoke`
- Includes:
1. detail related group persistence
2. designer related group scoped persistence
3. reference lookup detail/edit scope isolation
4. reference lookup advanced dialog baseline

## Verification Baseline
- Unit: `relationGroupScope.test.ts`
- Unit: `referenceLookupScope.test.ts`
- Unit: `referenceLookupColumnsPreference.test.ts`
- Unit: `referenceLookupRecent.test.ts`
- Unit: `BaseDetailPage.relationGroups.spec.ts`
- E2E: `detail-related-groups-persistence.spec.ts`
- E2E: `designer-related-groups-scope-persistence-regression.spec.ts`
- E2E: `reference-lookup-scope-isolation.spec.ts`
