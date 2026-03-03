# i18n Parity Report (en-US vs zh-CN)

Date: 2026-03-03  
Scope: `frontend/src/locales/*.json`

## Summary

- Checked files: `14`
- Missing keys in `zh-CN` (vs `en-US`): `0`
- Placeholder mismatches: `0`
- Suspicious literal values (`???` or `\uFFFD`): `0`
- `extraInTarget`: `0` (full parity after latest alignment)

## Key Findings

1. `system.json` structural drift root cause was fixed.
- Root cause: `permission/configPackage/workflow/file` were mistakenly nested under `sequenceRule` in `zh-CN/system.json`.
- Action taken: moved these blocks back to top-level namespace alignment with `en-US/system.json`.
- Current state:
  - `missingInTarget`: `0`
  - `extraInTarget`: `0` (added corresponding keys to `en-US/system.json`)

2. `itAssets.json` key path mismatch was fully corrected.
- Before: `itAssets.form.*` and related blocks were missing in `zh-CN`.
- Action taken:
  - mirrored `form/maintenance/configChange/common` into `itAssets.*` path in `zh-CN`
  - removed legacy top-level duplicate blocks (`form/maintenance/configChange/common`)
- Current state:
  - `missingInTarget`: `0`
  - `extraInTarget`: `0`

3. `layout designer` question-mark texts were fixed in `zh-CN/system.json`.
- `system.pageLayout.designer.*` translated and restored.
- `common` high-frequency `???` values fixed:
  - `detailPage.saveSuccess`
  - `detailPage.saveFailed`
  - `messages.formValidationFailed`
- Placeholder contract fixed:
  - `system.fieldDefinition.tips.formula`: `{字段编码}` -> `{fieldCode}`

## Tooling Added

- Script: `frontend/scripts/i18n-locale-parity-check.mjs`
- npm scripts:
  - `npm run i18n:parity`
  - `npm run i18n:parity:strict`

## Recommended Next Batch

1. Add an optional mojibake detector (e.g., CJK corruption heuristic) to parity script because current suspicious-value checks only catch `???` and `\uFFFD`.
2. Keep `i18n:parity:all:strict` in CI as the long-term gate to prevent structural drift from reappearing.
