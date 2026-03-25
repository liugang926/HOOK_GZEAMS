"""
Scan service for managing inventory scan operations.
"""
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.common.services.base_crud import BaseCRUDService
from apps.inventory.models import InventoryScan, InventorySnapshot, InventoryTask
from apps.assets.models import Asset


class ScanService(BaseCRUDService):
    """Service for inventory scan management."""

    def __init__(self):
        super().__init__(InventoryScan)

    def record_scan(
        self,
        task_id: str,
        qr_code: str,
        scanned_by_id: str,
        organization_id: str,
        scan_method: str = InventoryScan.METHOD_QR,
        scan_status: str = 'normal',
        actual_location_id: Optional[str] = None,
        actual_location_name: Optional[str] = None,
        actual_custodian_id: Optional[str] = None,
        actual_custodian_name: Optional[str] = None,
        photos: Optional[List[str]] = None,
        remark: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> InventoryScan:
        """
        Record a scan operation.

        Args:
            task_id: Inventory task ID
            qr_code: Scanned QR code content
            scanned_by_id: User ID performing the scan
            organization_id: Organization ID
            scan_method: Scan method (qr, rfid, manual)
            scan_status: Scan status (normal, damaged, lost)
            actual_location_id: Actual location ID
            actual_location_name: Actual location name
            actual_custodian_id: Actual custodian ID
            actual_custodian_name: Actual custodian name
            photos: List of photo URLs
            remark: Optional remark
            latitude: GPS latitude
            longitude: GPS longitude

        Returns:
            Created InventoryScan instance
        """
        from apps.inventory.utils.qr_code import QRCodeGenerator

        with transaction.atomic():
            # Validate task exists and is in progress
            try:
                task = InventoryTask.objects.get(
                    id=task_id,
                    organization_id=organization_id,
                    is_deleted=False
                )
            except InventoryTask.DoesNotExist:
                raise ValidationError(_("Inventory task not found."))

            if task.status != InventoryTask.STATUS_IN_PROGRESS:
                raise ValidationError(_("Inventory task is not in progress."))

            # Parse and validate QR code
            qr_generator = QRCodeGenerator()
            qr_data = qr_generator.parse_qr_code(qr_code)

            if qr_data.get('type') != QRCodeGenerator.TYPE_ASSET:
                raise ValidationError(_("Invalid QR code type. Expected asset QR code."))

            asset_id = qr_data.get('asset_id')
            asset_code = qr_data.get('asset_code')

            # Validate asset exists
            try:
                asset = Asset.objects.get(
                    id=asset_id,
                    asset_code=asset_code,
                    organization_id=organization_id,
                    is_deleted=False
                )
            except Asset.DoesNotExist:
                raise ValidationError(_("Asset not found."))

            # Get original info from snapshot
            try:
                snapshot = InventorySnapshot.objects.get(
                    task_id=task_id,
                    asset_id=asset_id,
                    is_deleted=False
                )
            except InventorySnapshot.DoesNotExist:
                raise ValidationError(_("Asset not in inventory snapshot."))

            # Get original location and custodian
            original_location_id = snapshot.location_id
            original_location_name = snapshot.location_name
            original_custodian_id = snapshot.custodian_id
            original_custodian_name = snapshot.custodian_name

            # Check for existing scan
            existing_scan = InventoryScan.objects.filter(
                task_id=task_id,
                asset_id=asset_id,
                is_deleted=False
            ).first()

            if existing_scan:
                # Update existing scan
                existing_scan.scan_method = scan_method
                existing_scan.scan_status = scan_status
                existing_scan.original_location_id = original_location_id
                existing_scan.original_location_name = original_location_name or ''
                existing_scan.original_custodian_id = original_custodian_id
                existing_scan.original_custodian_name = original_custodian_name or ''
                existing_scan.actual_location_id = actual_location_id
                existing_scan.actual_location_name = actual_location_name or ''
                existing_scan.actual_custodian_id = actual_custodian_id
                existing_scan.actual_custodian_name = actual_custodian_name or ''
                existing_scan.photos = photos or []
                existing_scan.remark = remark or ''
                existing_scan.latitude = latitude
                existing_scan.longitude = longitude
                existing_scan.scanned_at = datetime.utcnow()
                existing_scan.save()

                # Update snapshot
                self._update_snapshot_scan(snapshot, existing_scan)

                return existing_scan
            else:
                # Create new scan
                scan = InventoryScan.objects.create(
                    id=uuid.uuid4(),
                    task_id=task_id,
                    asset_id=asset_id,
                    qr_code=qr_code,
                    scanned_by_id=scanned_by_id,
                    scanned_at=datetime.utcnow(),
                    scan_method=scan_method,
                    scan_status=scan_status,
                    original_location_id=original_location_id,
                    original_location_name=original_location_name or '',
                    original_custodian_id=original_custodian_id,
                    original_custodian_name=original_custodian_name or '',
                    actual_location_id=actual_location_id,
                    actual_location_name=actual_location_name or '',
                    actual_custodian_id=actual_custodian_id,
                    actual_custodian_name=actual_custodian_name or '',
                    photos=photos or [],
                    remark=remark or '',
                    latitude=latitude,
                    longitude=longitude,
                    organization_id=organization_id,
                )

                # Update snapshot
                self._update_snapshot_scan(snapshot, scan)

                return scan

    def _update_snapshot_scan(self, snapshot: InventorySnapshot, scan: InventoryScan) -> None:
        """Update snapshot scan information."""
        snapshot.scanned = True
        snapshot.scanned_at = scan.scanned_at
        snapshot.scan_count += 1
        snapshot.save(update_fields=['scanned', 'scanned_at', 'scan_count'])

    def batch_record_scans(
        self,
        task_id: str,
        scans_data: List[Dict[str, Any]],
        scanned_by_id: str,
        organization_id: str,
    ) -> Dict[str, Any]:
        """
        Batch record scan operations.

        Args:
            task_id: Inventory task ID
            scans_data: List of scan data dictionaries
            scanned_by_id: User ID performing the scans
            organization_id: Organization ID

        Returns:
            Dictionary with results summary
        """
        results = {
            'total': len(scans_data),
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }

        for idx, scan_data in enumerate(scans_data):
            try:
                self.record_scan(
                    task_id=task_id,
                    qr_code=scan_data.get('qr_code'),
                    scanned_by_id=scanned_by_id,
                    organization_id=organization_id,
                    scan_method=scan_data.get('scan_method', InventoryScan.METHOD_QR),
                    scan_status=scan_data.get('scan_status', 'normal'),
                    actual_location_id=scan_data.get('actual_location_id'),
                    actual_location_name=scan_data.get('actual_location_name'),
                    actual_custodian_id=scan_data.get('actual_custodian_id'),
                    actual_custodian_name=scan_data.get('actual_custodian_name'),
                    photos=scan_data.get('photos'),
                    remark=scan_data.get('remark'),
                    latitude=scan_data.get('latitude'),
                    longitude=scan_data.get('longitude'),
                )
                results['succeeded'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'index': idx,
                    'error': str(e)
                })

        return results

    def validate_qr_code(
        self,
        qr_code: str,
        organization_id: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate a QR code and return asset information.

        Args:
            qr_code: QR code content to validate
            organization_id: Organization ID
            task_id: Optional task ID to check if asset is in snapshot

        Returns:
            Dictionary with validation result and asset info
        """
        from apps.inventory.utils.qr_code import QRCodeGenerator

        qr_generator = QRCodeGenerator()

        # Parse QR code
        qr_data = qr_generator.parse_qr_code(qr_code)

        # Validate checksum
        is_valid = qr_generator.validate_qr_code(
            qr_code,
            asset_code=qr_data.get('asset_code'),
            org_id=qr_data.get('org_id')
        )

        if not is_valid:
            return {
                'valid': False,
                'error': 'Invalid QR code checksum'
            }

        # Validate type
        if qr_data.get('type') != QRCodeGenerator.TYPE_ASSET:
            return {
                'valid': False,
                'error': 'Invalid QR code type'
            }

        # Check organization
        if qr_data.get('org_id') != organization_id:
            return {
                'valid': False,
                'error': 'QR code from different organization'
            }

        # Get asset info
        asset_id = qr_data.get('asset_id')
        try:
            asset = Asset.objects.get(
                id=asset_id,
                organization_id=organization_id,
                is_deleted=False
            )

            response = {
                'valid': True,
                'asset': {
                    'id': str(asset.id),
                    'asset_code': asset.asset_code,
                    'asset_name': asset.asset_name,
                    'category_id': str(asset.asset_category_id) if asset.asset_category_id else None,
                    'location_id': str(asset.location_id) if asset.location_id else None,
                    'custodian_id': str(asset.custodian_id) if asset.custodian_id else None,
                }
            }

            # Check if in task snapshot if task_id provided
            if task_id:
                in_snapshot = InventorySnapshot.objects.filter(
                    task_id=task_id,
                    asset_id=asset_id,
                    is_deleted=False
                ).exists()
                response['in_task'] = in_snapshot

            return response

        except Asset.DoesNotExist:
            return {
                'valid': False,
                'error': 'Asset not found'
            }

    def update_scan(
        self,
        scan_id: str,
        user_id: str,
        organization_id: str,
        scan_status: Optional[str] = None,
        actual_location_id: Optional[str] = None,
        actual_location_name: Optional[str] = None,
        actual_custodian_id: Optional[str] = None,
        actual_custodian_name: Optional[str] = None,
        photos: Optional[List[str]] = None,
        remark: Optional[str] = None,
    ) -> InventoryScan:
        """
        Update an existing scan record.

        Args:
            scan_id: Scan ID to update
            user_id: User ID performing the update
            organization_id: Organization ID
            scan_status: New scan status
            actual_location_id: Actual location ID
            actual_location_name: Actual location name
            actual_custodian_id: Actual custodian ID
            actual_custodian_name: Actual custodian name
            photos: List of photo URLs
            remark: Optional remark

        Returns:
            Updated InventoryScan instance
        """
        scan = self.get_by_id(scan_id)

        if scan.organization_id != organization_id:
            raise ValidationError(_("Scan not found in organization."))

        # Update fields if provided
        if scan_status is not None:
            scan.scan_status = scan_status
        if actual_location_id is not None:
            scan.actual_location_id = actual_location_id
        if actual_location_name is not None:
            scan.actual_location_name = actual_location_name
        if actual_custodian_id is not None:
            scan.actual_custodian_id = actual_custodian_id
        if actual_custodian_name is not None:
            scan.actual_custodian_name = actual_custodian_name
        if photos is not None:
            scan.photos = photos
        if remark is not None:
            scan.remark = remark

        scan.save()

        return scan

    def get_scans_by_task(
        self,
        task_id: str,
        scanned_by_id: Optional[str] = None,
        scan_status: Optional[str] = None
    ) -> List[InventoryScan]:
        """
        Get scans for a task with optional filters.

        Args:
            task_id: Task ID
            scanned_by_id: Optional filter by scanner
            scan_status: Optional filter by status

        Returns:
            List of InventoryScan instances
        """
        queryset = InventoryScan.objects.filter(
            task_id=task_id,
            is_deleted=False
        )

        if scanned_by_id:
            queryset = queryset.filter(scanned_by_id=scanned_by_id)
        if scan_status:
            queryset = queryset.filter(scan_status=scan_status)

        return list(queryset.select_related('task', 'asset', 'scanned_by'))

    def get_scan_summary(self, task_id: str) -> Dict[str, Any]:
        """
        Get scan summary for a task.

        Args:
            task_id: Task ID

        Returns:
            Dictionary with scan summary
        """
        from django.db.models import Count

        scans = InventoryScan.objects.filter(
            task_id=task_id,
            is_deleted=False
        )

        summary = {
            'total_scans': scans.count(),
            'unique_assets': scans.values('asset_id').distinct().count(),
            'by_status': {},
            'by_method': {},
            'by_scanner': []
        }

        # Count by status
        for status, label in InventoryScan.SCAN_STATUS_CHOICES:
            count = scans.filter(scan_status=status).count()
            if count > 0:
                summary['by_status'][status] = count

        # Count by method
        for method, label in InventoryScan.SCAN_METHOD_CHOICES:
            count = scans.filter(scan_method=method).count()
            if count > 0:
                summary['by_method'][method] = count

        # Count by scanner
        scanner_stats = scans.values('scanned_by_id', 'scanned_by__username').annotate(
            count=Count('id')
        ).order_by('-count')

        summary['by_scanner'] = [
            {
                'user_id': stat['scanned_by_id'],
                'username': stat['scanned_by__username'],
                'count': stat['count']
            }
            for stat in scanner_stats
        ]

        return summary
