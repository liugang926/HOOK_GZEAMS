# GZEAMS - Hook Fixed Assets Management System

[![CI](https://github.com/liugang926/HOOK_GZEAMS/workflows/CI/badge.svg)](https://github.com/liugang926/HOOK_GZEAMS/actions)
[![codecov](https://codecov.io/gh/liugang926/HOOK_GZEAMS/branch/master/graph/badge.svg)](https://codecov.io/gh/liugang926/HOOK_GZEAMS)

## Overview

GZEAMS is a metadata-driven low-code platform for enterprise fixed asset management, built with Django 5.0 and Vue3.

## Features

- **Metadata-Driven Low-Code Engine**: Dynamic business object configuration and page layouts
- **Multi-Organization Data Isolation**: Enterprise-grade data segregation and security
- **Visual BPM Workflow**: LogicFlow-based visual workflow designer
- **Asset Inventory Management**: Professional inventory and reconciliation management
- **Third-Party Integration**: SSO support for WeChat Work, DingTalk, and Feishu

## Technology Stack

### Backend
- Django 5.0
- Django REST Framework (DRF)
- PostgreSQL (with JSONB support)
- Redis (cache/queue)
- Celery (async task processing)

### Frontend
- Vue 3 (Composition API)
- Vite
- Element Plus
- Pinia

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm

### Installation

```bash
# Clone the repository
git clone https://github.com/liugang926/HOOK_GZEAMS.git
cd HOOK_GZEAMS

# Start all services
docker compose up -d

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

The `backend` container now runs the runtime-safe bootstrap chain automatically on startup:

- `python manage.py migrate --noinput`
- `python manage.py bootstrap_defaults`
- `python manage.py collectstatic --noinput`

`bootstrap_defaults` is designed for Docker startup and will:

- register missing hardcoded business objects
- sync metadata fields
- create missing default layouts without forcing overwrites
- normalize standard menu classification for default objects

If you need to re-run it manually inside Docker:

```bash
docker compose exec backend python manage.py bootstrap_defaults
```

If you need to re-standardize an existing development environment and overwrite system default layouts:

```bash
docker compose exec -T backend python manage.py bootstrap_defaults --force-layouts
docker compose exec -T backend python manage.py verify_runtime_defaults
```

To verify that a new environment actually has the standardized defaults, run:

```bash
docker compose exec -T backend python manage.py verify_runtime_defaults
```

This command fails if default `form/list/detail/search` layouts are missing or if section titles are not stored as i18n payloads.
This command fails if published default `form/detail/search` layouts are missing, if the runtime-generated `list` layout cannot be produced, or if `form/detail` section titles are not stored as i18n payloads.

If you need to disable automatic bootstrap for a specific backend container start, set:

```bash
BOOTSTRAP_DEFAULTS_ON_STARTUP=0
```

### Development

```bash
# Backend development (view logs)
docker compose logs -f backend

# Frontend development (hot-reload)
cd frontend
npm install
npm run dev

# Production build
npm run build
```

## Documentation

See [docs/](./docs) for detailed documentation, including:
- Architecture Overview
- API Reference
- Development Guidelines
- Deployment Guide
- Health and observability runbook: [docs/operations/health-observability.md](./docs/operations/health-observability.md)
- Runtime default bootstrap: [docs/operations/runtime-default-bootstrap.md](./docs/operations/runtime-default-bootstrap.md)

## Contributing

Please read our development standards in [CLAUDE.md](./CLAUDE.md) before contributing.

## License

[Your License Here]

## Primary Reference

[NIIMBOT Hook Fixed Assets](https://yzcweixin.niimbot.com/) - QR code login required
