# Software Licenses Module

## Overview

Manages software catalog, licenses, and asset allocations for tracking software compliance.

## Models

- `Software`: Software catalog entries with code, name, version, vendor, and type
- `SoftwareLicense`: License tracking with quantity management and expiration dates
- `LicenseAllocation`: Asset-to-license assignments with usage tracking

## Features

- **Software Catalog**: Track all software products in the organization
- **License Management**: Monitor license usage, expiration, and compliance
- **Asset Allocation**: Assign licenses to specific assets with automatic usage tracking
- **Compliance Reporting**: View over-utilized licenses and upcoming expirations

## API Endpoints

### Software Catalog
- `GET /api/software-licenses/software/` - List software
- `POST /api/software-licenses/software/` - Create software
- `GET /api/software-licenses/software/{id}/` - Get software
- `PUT /api/software-licenses/software/{id}/` - Update software
- `DELETE /api/software-licenses/software/{id}/` - Delete software
- `POST /api/software-licenses/software/batch-delete/` - Batch delete

### Software Licenses
- `GET /api/software-licenses/licenses/` - List licenses
- `POST /api/software-licenses/licenses/` - Create license
- `GET /api/software-licenses/licenses/{id}/` - Get license
- `PUT /api/software-licenses/licenses/{id}/` - Update license
- `DELETE /api/software-licenses/licenses/{id}/` - Delete license
- `GET /api/software-licenses/licenses/expiring/` - Get expiring licenses (30 days)
- `GET /api/software-licenses/licenses/compliance-report/` - Get compliance report
- `POST /api/software-licenses/licenses/batch-delete/` - Batch delete

### License Allocations
- `GET /api/software-licenses/license-allocations/` - List allocations
- `POST /api/software-licenses/license-allocations/` - Create allocation
- `GET /api/software-licenses/license-allocations/{id}/` - Get allocation
- `PUT /api/software-licenses/license-allocations/{id}/` - Update allocation
- `DELETE /api/software-licenses/license-allocations/{id}/` - Delete allocation
- `POST /api/software-licenses/license-allocations/{id}/deallocate/` - Deallocate
- `POST /api/software-licenses/license-allocations/batch-delete/` - Batch delete

## Frontend Pages

- `/software-licenses/software` - Software catalog list
- `/software-licenses/software/create` - Create software
- `/software-licenses/software/:id/edit` - Edit software
- `/software-licenses/licenses` - License list with compliance panel
- `/software-licenses/licenses/create` - Create license
- `/software-licenses/licenses/:id/edit` - Edit license
- `/software-licenses/allocations` - Allocation records

## Running Tests

```bash
cd backend
pytest apps/software_licenses/tests/
```

## Test Coverage

- Model tests: 6 tests
- API tests: 8 tests
- Integration tests: 3 tests
- Total: 17 tests (all passing)
