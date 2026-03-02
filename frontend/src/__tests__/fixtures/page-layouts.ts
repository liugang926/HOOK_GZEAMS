/**
 * Mock page layouts data for testing
 */

export const mockPageLayouts = [
  {
    id: 'layout-001',
    code: 'asset_form',
    name: '资产表单',
    object_code: 'asset',
    layout_type: 'form',
    config: {
      sections: [
        {
          id: 'section-1',
          title: '基本信息',
          fields: [
            { field_code: 'asset_code', required: true },
            { field_code: 'asset_name', required: true },
            { field_code: 'category', required: true }
          ]
        },
        {
          id: 'section-2',
          title: '详细信息',
          fields: [
            { field_code: 'purchase_date', required: false },
            { field_code: 'price', required: true },
            { field_code: 'status', required: true }
          ]
        }
      ]
    }
  },
  {
    id: 'layout-002',
    code: 'asset_list',
    name: '资产列表',
    object_code: 'asset',
    layout_type: 'list',
    config: {
      columns: [
        { field_code: 'asset_code', width: 120, fixed: 'left' },
        { field_code: 'asset_name', width: 200 },
        { field_code: 'category', width: 150 },
        { field_code: 'status', width: 100 },
        { field_code: 'price', width: 120 }
      ]
    }
  }
]
