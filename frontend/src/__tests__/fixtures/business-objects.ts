/**
 * Mock business objects data for testing
 */

export const mockBusinessObjects = [
  {
    id: 'bo-001',
    code: 'asset',
    name: '固定资产',
    module: 'assets',
    is_active: true,
    icon: 'files',
    description: '固定资产主数据',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'bo-002',
    code: 'asset_requisition',
    name: '资产领用',
    module: 'assets',
    is_active: true,
    icon: 'document-copy',
    description: '资产领用单据',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'bo-003',
    code: 'inventory_task',
    name: '盘点任务',
    module: 'inventory',
    is_active: true,
    icon: 'clipboard',
    description: '资产盘点任务',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
]

export const mockBusinessObjectDetail = {
  ...mockBusinessObjects[0],
  field_definitions: ['field-001', 'field-002', 'field-003'],
  page_layouts: ['layout-001', 'layout-002']
}
