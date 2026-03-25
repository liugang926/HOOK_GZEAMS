# Runtime Default Bootstrap

This runbook defines the standard environment bootstrap for metadata, menu classification, and default layouts.

## Goal

Every new environment must converge to the same backend-owned defaults:

- hardcoded business objects are registered
- metadata fields are synced
- default layouts are created
- menu classification is normalized
- form/detail/search section titles use i18n payloads instead of hardcoded text

## Standard Bootstrap Chain

Use the backend container as the only bootstrap entrypoint:

```bash
docker compose exec -T backend python manage.py bootstrap_defaults
```

`bootstrap_defaults` runs these commands in order:

```bash
python manage.py register_core_models --sync-fields
python manage.py sync_metadata
python manage.py create_default_layouts
python manage.py update_menu_config
```

In Docker startup, this chain is already wired through `docker-entrypoint.sh`.

## New Environment Procedure

For a fresh environment:

```bash
docker compose up -d
docker compose exec -T backend python manage.py bootstrap_defaults
docker compose exec -T backend python manage.py verify_runtime_defaults
```

If the environment must always rebuild system defaults during development:

```bash
docker compose exec -T backend python manage.py bootstrap_defaults --force-layouts
docker compose exec -T backend python manage.py verify_runtime_defaults
```

## Verification Standard

Use:

```bash
docker compose exec -T backend python manage.py verify_runtime_defaults
```

The command fails with a non-zero exit code when any business object is missing one of these published default layouts:

- `form`
- `detail`
- `search`

It also validates that the runtime-generated default `list` layout can still be produced from metadata.

It also fails when:

- `form/detail/search` layouts do not contain sections
- the runtime-generated `list` layout does not contain columns
- `form/detail` section titles are missing `translationKey` payloads

You can scope validation to one object:

```bash
docker compose exec -T backend python manage.py verify_runtime_defaults --object-code Asset
```

## CI/CD Recommendation

After deployment migrations, run:

```bash
python manage.py bootstrap_defaults
python manage.py verify_runtime_defaults
```

This should be treated as a release gate. If `verify_runtime_defaults` fails, the deployment should fail.

## Development Override Rule

Current project phase allows system-generated defaults to overwrite published default layouts during regeneration. The recommended explicit development refresh is:

```bash
docker compose exec -T backend python manage.py sync_metadata --force
docker compose exec -T backend python manage.py bootstrap_defaults --force-layouts
docker compose exec -T backend python manage.py verify_runtime_defaults
```

This rule is intended for active development only. Production should keep `bootstrap_defaults` non-destructive unless the deployment plan explicitly allows forced regeneration.
