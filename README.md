# GZEAMS - Workflow & Asset Management System

## Overview

GZEAMS (Global Zonal Enterprise Asset Management System) is a comprehensive workflow and asset management solution designed to streamline business processes, manage fixed assets, and ensure compliance. This system provides a robust backend with a flexible workflow engine, integrated monitoring, enhanced security, and a user-friendly frontend.

## Key Features

- **Dynamic Workflow Engine**: Define and manage complex multi-stage approval workflows.
- **Asset Lifecycle Management**: Track assets from acquisition to disposal.
- **User & Role Management**: Granular permission control and role-based access.
- **Notifications**: Real-time alerts and in-app notifications for workflow events.
- **Audit Logging**: Comprehensive, immutable logs for security and compliance.
- **Performance Monitoring**: Real-time API, system, and cache performance metrics.
- **SLA Dashboard**: Monitor Service Level Agreement compliance and identify bottlenecks.
- **Security Hardening**: Input validation, rate limiting, and secure coding practices.
- **User Experience Optimization**: Customizable preferences, onboarding, and enhanced feedback.

## Architecture

### Backend (Django/Python)

- **Framework**: Django REST Framework
- **Database**: PostgreSQL
- **Cache/Broker**: Redis
- **Background Tasks**: Celery
- **Core Modules**: Workflows, Assets, Accounts, Notifications, Permissions

### Frontend (Vue.js/TypeScript)

- **Framework**: Vue.js 3
- **Language**: TypeScript
- **UI Library**: Element Plus
- **Build Tool**: Vite

## Getting Started

### Prerequisites

- Docker & Docker Compose (recommended for local development and production)
- Python 3.9+
- Node.js 16+
- Git

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/gzeams.git
   cd gzeams
   ```

2. **Environment Variables**:
   Create a `.env` file in the project root based on `.env.example`.

3. **Docker Compose (Recommended)**:
   ```bash
   docker compose up --build -d
   ```
   This will set up PostgreSQL, Redis, Django backend, and Celery worker.

4. **Database Migrations**:
   ```bash
   docker compose exec web python backend/manage.py migrate
   docker compose exec web python backend/manage.py createsuperuser # Create an admin user
   ```

5. **Collect Static Files**:
   ```bash
   docker compose exec web python backend/manage.py collectstatic --noinput
   ```

6. **Frontend Development**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The frontend will be available at `http://localhost:5173` (or similar).

7. **Access Backend API**: `http://localhost:8000/api/` (default)

### Production Deployment

Refer to the [Production Deployment Guide](/docs/deployment/production-setup.md) for detailed instructions.

## Documentation

- [API Reference](/docs/api/)
  - [Monitoring API](/docs/api/monitoring-api.md)
  - [SLA Dashboard API](/docs/api/sla-dashboard-api.md)
- [Security Documentation](/docs/security/)
  - [Audit Logging](/docs/security/audit-logging.md)
  - [Security Hardening Guide (Placeholder)]()
- [Deployment Guide](/docs/deployment/production-setup.md)
- [Performance Baselines](/docs/reports/performance-baseline.md)
- [Sprint Reports](/docs/reports/)

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue on GitHub or contact the development team.

---

**Last Updated**: 2026-03-24