# Frontend Storage Governance

## Goal
- Avoid scattered `localStorage` key access and hidden coupling.
- Keep core session/locale keys behind stable APIs.
- Make feature preference storage reusable and testable.

## Core Rule
- Do not directly call `localStorage.getItem/setItem/removeItem` for:
  - `access_token`
  - `current_org_id`
  - `locale`
  - `locale_source`
- Use:
  - `src/platform/auth/sessionPreference.ts`
  - `src/platform/i18n/localePreference.ts`

## Shared Storage Primitive
- `src/platform/storage/browserStorage.ts`
  - `readStorageString`
  - `writeStorageString`
  - `removeStorageKey`
  - `readStorageJson`
  - `writeStorageJson`

## Enforced By Lint
- `.eslintrc.json` includes `no-restricted-syntax` selectors on `src/**` to block direct access to core keys.

## Applied Modules
- Session:
  - `src/stores/user.ts`
  - `src/utils/request.ts`
- Locale:
  - `src/locales/index.ts`
  - `src/stores/locale.ts`
  - `src/components/common/LocaleSwitcher.vue`
  - `src/api/translations.ts`
  - `src/utils/getLocalizedLabel.ts`
  - `src/utils/localeText.ts`
- Feature preferences:
  - `src/composables/useFieldTypes.ts`
  - `src/views/mobile/scan/UnifiedScan.vue`
  - `src/components/common/DynamicDetailPage.vue` (`detail_debug`)
