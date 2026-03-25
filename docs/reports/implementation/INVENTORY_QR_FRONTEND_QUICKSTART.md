# Inventory QR Frontend - Quick Start Guide

## Installation

1. **Install dependencies** (including the new @zxing/library):
```bash
cd frontend
npm install
```

2. **Start development server**:
```bash
npm run dev
```

3. **Access the application**:
```
http://localhost:5173
```

## Route Configuration

Add these routes to your router configuration (`src/router/index.js`):

```javascript
const inventoryRoutes = [
  {
    path: '/inventory',
    redirect: '/inventory/tasks'
  },
  {
    path: '/inventory/tasks',
    name: 'InventoryTasks',
    component: () => import('@/views/inventory/TaskList.vue'),
    meta: { title: '盘点任务', icon: 'List' }
  },
  {
    path: '/inventory/tasks/:id/execute',
    name: 'InventoryTaskExecute',
    component: () => import('@/views/inventory/ScanInventory.vue'),
    meta: { title: '执行盘点' }
  },
  {
    path: '/inventory/tasks/:id',
    name: 'InventoryTaskDetail',
    component: () => import('@/views/inventory/TaskDetail.vue'),
    meta: { title: '盘点详情' }
  },
  {
    path: '/inventory/tasks/:id/differences',
    name: 'InventoryDifferences',
    component: () => import('@/views/inventory/Reconciliation.vue'),
    meta: { title: '差异处理' }
  }
]
```

## File Structure

```
frontend/src/
├── api/
│   └── inventory.js                    # API methods (250 lines)
├── components/
│   └── inventory/
│       ├── QRScanner.vue               # QR scanner (646 lines)
│       ├── ScanResult.vue              # Scan result form (237 lines)
│       ├── InventoryProgress.vue       # Progress display (311 lines)
│       ├── AssetList.vue               # Asset list (183 lines)
│       ├── DifferenceList.vue          # Differences list (175 lines)
│       ├── ScanRecordList.vue          # Scan records (218 lines)
│       └── TaskOverview.vue            # Task overview (246 lines)
├── views/
│   └── inventory/
│       ├── TaskList.vue                # Task list (347 lines)
│       ├── ScanInventory.vue           # Scan interface (282 lines)
│       ├── TaskDetail.vue              # Task details (304 lines)
│       └── Reconciliation.vue          # Difference handling (590 lines)
└── utils/
    └── inventory/
        ├── constants.js                # Constants (230 lines)
        └── helpers.js                  # Helper functions (470 lines)
```

## Key Features

### 1. QR Code Scanning
- Browser-based camera integration
- Multi-device support
- Manual input fallback
- Real-time validation
- Audio/vibration feedback

### 2. Task Management
- Create, start, complete inventory tasks
- Real-time progress tracking
- Task status monitoring
- Difference detection

### 3. Mobile Optimized
- Touch-friendly UI
- Camera access
- Responsive design
- Offline-ready structure

## Usage Examples

### Start Inventory Task
```javascript
import { startTask } from '@/api/inventory'

// Start task (generates asset snapshot)
await startTask(taskId)
```

### Record Scan
```javascript
import { recordScan } from '@/api/inventory'

// Record asset scan
await recordScan(taskId, {
  asset_id: assetId,
  scan_method: 'qr',
  status: 'normal',
  actual_location: '',
  photos: [],
  remark: ''
})
```

### Complete Task
```javascript
import { completeTask } from '@/api/inventory'

// Complete inventory
await completeTask(taskId)
```

## Helper Functions

```javascript
import {
  formatDate,
  calculateProgress,
  validateQRCode,
  playBeep,
  vibrate
} from '@/utils/inventory/helpers'

// Format date
formatDate(new Date(), 'datetime') // "2026/01/16 11:30"

// Calculate progress
calculateProgress(150, 200) // 75

// Validate QR code
const result = validateQRCode(qrData)
if (result.valid) {
  console.log(result.data)
}

// Play feedback
playBeep(1000, 150) // frequency, duration
vibrate(200) // 200ms
```

## Constants

```javascript
import {
  TaskStatus,
  TaskStatusLabel,
  DifferenceType,
  ScanMethod
} from '@/utils/inventory/constants'

// Task status
TaskStatus.IN_PROGRESS // "in_progress"
TaskStatusLabel[TaskStatus.IN_PROGRESS] // "进行中"

// Difference type
DifferenceType.EXTRA // "extra"
DifferenceType.MISSING // "missing"

// Scan method
ScanMethod.QR // "qr"
ScanMethod.MANUAL // "manual"
```

## Component Usage

### QRScanner Component
```vue
<QRScanner
  :task-id="taskId"
  :continuous="true"
  @scanned="handleScanned"
  @error="handleError"
/>
```

### InventoryProgress Component
```vue
<InventoryProgress
  :statistics="statistics"
  :task="task"
/>
```

### AssetList Component
```vue
<AssetList
  :task-id="taskId"
  type="scanned"
  :assets="assets"
  @refresh="fetchData"
/>
```

## Development Notes

1. **Camera Permissions**: Requires HTTPS or localhost
2. **Browser Support**: Chrome 90+, Firefox 88+, Safari 14+
3. **Mobile Testing**: Test on actual devices for camera access
4. **Offline Mode**: Structure ready, requires Service Worker (Phase 1.8)

## Troubleshooting

### Camera not working
- Check HTTPS/localhost requirement
- Verify browser camera permissions
- Ensure @zxing/library is installed

### QR code not detected
- Improve lighting conditions
- Hold camera steady
- Ensure QR code is in focus
- Try manual input fallback

### API errors
- Check backend is running
- Verify API endpoint URLs
- Check network tab in DevTools
- Review console error messages

## Next Steps

1. Test QR scanning on target devices
2. Integrate with backend API
3. Implement TaskCreate.vue
4. Add router configuration
5. Test offline mode (Phase 1.8)
6. Add RFID support (Phase 4.2)

## Support

For issues or questions:
- Check implementation report: `INVENTORY_QR_FRONTEND_IMPLEMENTATION_REPORT.md`
- Review PRD: `docs/plans/phase4_1_inventory_qr/frontend.md`
- Check backend API: Backend Phase 4.1 implementation
