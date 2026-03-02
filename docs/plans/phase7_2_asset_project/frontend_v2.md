# Phase 7.2: Asset Project - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement asset project functionality for grouping assets by project or initiative.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/project.ts

export interface AssetProject {
  id: string
  projectNo: string
  projectName: string
  projectType: ProjectType
  startDate: string
  endDate?: string
  budget?: number
  managerId?: string
  manager?: User
  departmentId?: string
  department?: Department
  description?: string
  status: ProjectStatus
  assetCount: number
  organizationId: string
  createdAt: string
}

export enum ProjectType {
  CONSTRUCTION = 'construction',
  RD = 'rd',
  EVENT = 'event',
  MAINTENANCE = 'maintenance',
  OTHER = 'other'
}

export enum ProjectStatus {
  PLANNING = 'planning',
  ACTIVE = 'active',
  ON_HOLD = 'on_hold',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface ProjectAsset {
  projectId: string
  assetId: string
  asset?: Asset
  allocatedAt: string
  expectedReturnDate?: string
  actualReturnDate?: string
  status: 'in_use' | 'returned' | 'lost'
}

export interface ProjectAssetAdd {
  assetIds: string[]
  expectedReturnDate?: string
}
```

### API Service

```typescript
// frontend/src/api/projects.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  AssetProject,
  ProjectAsset,
  ProjectAssetAdd,
  ProjectCreate,
  ProjectUpdate
} from '@/types/project'

export const projectApi = {
  list(filters?: any): Promise<PaginatedResponse<AssetProject>> {
    return request.get('/projects/', { params: filters })
  },

  get(id: string): Promise<AssetProject> {
    return request.get(`/projects/${id}/`)
  },

  create(data: ProjectCreate): Promise<AssetProject> {
    return request.post('/projects/', data)
  },

  update(id: string, data: ProjectUpdate): Promise<AssetProject> {
    return request.put(`/projects/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/projects/${id}/`)
  },

  // Project Assets
  getAssets(projectId: string, params?: any): Promise<PaginatedResponse<ProjectAsset>> {
    return request.get(`/projects/${projectId}/assets/`, { params })
  },

  addAssets(projectId: string, data: ProjectAssetAdd): Promise<void> {
    return request.post(`/projects/${projectId}/assets/`, data)
  },

  removeAsset(projectId: string, assetId: string): Promise<void> {
    return request.delete(`/projects/${projectId}/assets/${assetId}/`)
  },

  returnAsset(projectId: string, assetId: string, returnData: any): Promise<void> {
    return request.post(`/projects/${projectId}/assets/${assetId}/return/`, returnData)
  }
}
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/project.ts` | Project type definitions |
| `frontend/src/api/projects.ts` | Project API service |
| `frontend/src/views/projects/ProjectList.vue` | Project list page |
| `frontend/src/views/projects/ProjectForm.vue` | Project form page |
| `frontend/src/views/projects/ProjectAssets.vue` | Project assets page |
