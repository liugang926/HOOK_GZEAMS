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
docker-compose up -d

# Run database migrations
docker-compose exec backend python manage.py migrate

# Sync low-code metadata schemas
docker-compose exec backend python manage.py sync_schemas

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

### Development

```bash
# Backend development (view logs)
docker-compose logs -f backend

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

## Contributing

Please read our development standards in [CLAUDE.md](./CLAUDE.md) before contributing.

## License

[Your License Here]

## Primary Reference

[NIIMBOT Hook Fixed Assets](https://yzcweixin.niimbot.com/) - QR code login required
