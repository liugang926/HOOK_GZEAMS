# Frontend Field Key Contract

Updated: 2026-02-24

## Scope

This contract defines how frontend runtime pages resolve field values when metadata uses `field.code` (usually `snake_case`) and API payloads may use `camelCase`.

Applicable modules:

- `frontend/src/components/engine/valueAccessor.ts`
- `frontend/src/components/common/BaseDetailPage.vue`
- `frontend/src/utils/fieldKey.ts`

## Canonical Rules

1. Metadata canonical key is `field.code`.
2. Runtime data key is `field.dataKey` when present.
3. When `field.dataKey` is missing, derive it from `field.code`:
   - `asset_code -> assetCode`
4. Read operations must support both `snake_case` and `camelCase`.
5. Read operations may fallback to:
   - wrapped payload: `{ success, data: {...} }`
   - custom field bags: `customFields` and `custom_fields`

## Read Precedence

For flat field keys (non-nested paths), read precedence is:

1. `field.code`
2. `field.dataKey` (or derived dataKey)
3. `camel/snake` aliases of the above
4. same precedence inside `data` wrapper (if enabled)
5. same precedence inside custom field bags (if enabled)

Default behavior treats empty values (`undefined`, `null`, `''`) as missing and continues fallback.

## Write Contract

For form runtime:

1. Canonical write target is `field.code`.
2. If record already contains `dataKey`, mirror value to `dataKey`.
3. If record stores value in `customFields`, mirror value into `customFields[field.code]`.
4. Submit payload uses `dataKey` by default, unless field currently resides in `customFields`.

## Shared Utility

All new field key resolution logic should use `frontend/src/utils/fieldKey.ts`:

- `toDataKey(fieldCode)`
- `buildFieldKeyCandidates(fieldCode, dataKey?)`
- `resolveFieldValue(record, options)`

Avoid duplicating conversion and fallback logic in components.

## Test Coverage

Unit tests: `frontend/src/utils/fieldKey.test.ts`

Validated cases:

- snake/camel alias resolution
- wrapped response fallback
- custom fields fallback
- empty-value fallback behavior

