/**
 * Mock field definitions data for testing
 */

export const mockFieldDefinitions = [
  {
    id: 'field-001',
    code: 'asset_code',
    label: '资产编码',
    object_id: 'bo-001',
    field_type: 'text',
    is_required: true,
    is_unique: true,
    config: { max_length: 50, placeholder: '请输入资产编码' },
    sort_order: 1
  },
  {
    id: 'field-002',
    code: 'asset_name',
    label: '资产名称',
    object_id: 'bo-001',
    field_type: 'text',
    is_required: true,
    config: { max_length: 200, placeholder: '请输入资产名称' },
    sort_order: 2
  },
  {
    id: 'field-003',
    code: 'category',
    label: '资产分类',
    object_id: 'bo-001',
    field_type: 'reference',
    is_required: true,
    config: { target_object: 'asset_category' },
    sort_order: 3
  },
  {
    id: 'field-004',
    code: 'purchase_date',
    label: '采购日期',
    object_id: 'bo-001',
    field_type: 'date',
    is_required: false,
    config: {},
    sort_order: 4
  },
  {
    id: 'field-005',
    code: 'price',
    label: '价格',
    object_id: 'bo-001',
    field_type: 'number',
    is_required: true,
    config: { min: 0, precision: 2 },
    sort_order: 5
  },
  {
    id: 'field-006',
    code: 'status',
    label: '状态',
    object_id: 'bo-001',
    field_type: 'select',
    is_required: true,
    config: { options: ['在用', '闲置', '报废', '维修中'] },
    sort_order: 6
  }
]
