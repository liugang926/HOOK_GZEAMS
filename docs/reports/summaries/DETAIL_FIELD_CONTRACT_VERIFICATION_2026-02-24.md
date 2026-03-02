# Detail Field Contract Verification (2026-02-24)

## Scope

Verification target after field key contract unification:

- `Asset`
- `Supplier`
- `Location`
- `Department`
- `Consumable`

API endpoints used:

- `GET /api/system/objects/{code}/fields/?context=detail&include_relations=true`
- `GET /api/system/objects/{code}/?page=1&page_size=1`
- `GET /api/system/objects/{code}/{id}/` (when records exist)

## Result Summary

| Object | Detail Fields | Business Fields | List Count | Resolved Business Values (sampled detail) | Status |
|---|---:|---:|---:|---:|---|
| Asset | 38 | 28 | 6 | 19 | PASS |
| Supplier | 16 | 6 | 3 | 4 | PASS |
| Location | 15 | 5 | 5 | 4 | PASS |
| Department | 26 | 16 | 2 | 8 | PASS |
| Consumable | 27 | 17 | 1 | 13 | PASS |

## Conclusion

1. All target objects (`Asset`, `Supplier`, `Location`, `Department`, `Consumable`) pass detail field/value resolution checks.
2. `Department` and `Consumable` have been verified with real sampled detail records (no longer skipped).
3. Field contract unification is functioning across all sampled object types.

## Evidence

Raw verification output:

- `tmp_detail_contract_verification.json`
