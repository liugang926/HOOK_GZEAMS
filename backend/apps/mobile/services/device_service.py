"""
Mobile Device Service.

Provides business logic for device registration, unbinding, and management.
"""
from django.utils import timezone
from apps.mobile.models import MobileDevice


class DeviceService:
    """Device management service."""

    @staticmethod
    def register_device(user, device_id: str, device_info: dict) -> MobileDevice:
        """
        Register or update a device.

        Args:
            user: User object
            device_id: Device unique identifier
            device_info: Device information dict

        Returns:
            MobileDevice instance
        """
        device, created = MobileDevice.objects.get_or_create(
            device_id=device_id,
            defaults={
                'user': user,
                'device_name': device_info.get('device_name', 'Unknown'),
                'device_type': device_info.get('device_type', 'h5'),
                'os_version': device_info.get('os_version', ''),
                'app_version': device_info.get('app_version', ''),
                'device_info': device_info,
                'is_bound': True,
                'is_active': True,
                'last_login_at': timezone.now(),
                'last_login_ip': device_info.get('ip_address'),
            }
        )

        if not created:
            # Update existing device
            device.is_bound = True
            device.is_active = True
            device.last_login_at = timezone.now()
            device.last_login_ip = device_info.get('ip_address', device.last_login_ip)
            device.os_version = device_info.get('os_version', device.os_version)
            device.app_version = device_info.get('app_version', device.app_version)
            if device_info.get('device_name'):
                device.device_name = device_info.get('device_name')
            device.save()

        return device

    @staticmethod
    def unbind_device(user, device_id: str) -> bool:
        """
        Unbind a device.

        Args:
            user: User object
            device_id: Device identifier (pk or device_id field)

        Returns:
            True if successful
        """
        import uuid
        # Try to parse as UUID to check if it's a pk
        try:
            uuid.UUID(device_id)
            # Valid UUID format, try by pk first
            try:
                device = MobileDevice.objects.get(user=user, pk=device_id)
                device.unbind()
                return True
            except MobileDevice.DoesNotExist:
                pass
        except (ValueError, AttributeError):
            # Not a UUID, continue to try device_id field
            pass

        # Try by device_id field
        try:
            device = MobileDevice.objects.get(
                user=user,
                device_id=device_id
            )
            device.unbind()
            return True
        except MobileDevice.DoesNotExist:
            return False

    @staticmethod
    def get_user_devices(user):
        """
        Get user's device list.

        Args:
            user: User object

        Returns:
            QuerySet of MobileDevice
        """
        return MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).order_by('-last_login_at')

    @staticmethod
    def check_device_limit(user, max_devices: int = 3) -> bool:
        """
        Check device limit.

        Args:
            user: User object
            max_devices: Maximum allowed devices

        Returns:
            True if under limit
        """
        active_count = MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).count()
        return active_count < max_devices

    @staticmethod
    def revoke_old_devices(user, keep_count: int = 2):
        """
        Revoke old devices, keeping the most recent ones.

        Args:
            user: User object
            keep_count: Number of devices to keep
        """
        devices = MobileDevice.objects.filter(
            user=user,
            is_bound=True
        ).order_by('-last_login_at')

        for device in devices[keep_count:]:
            device.unbind()

    @staticmethod
    def log_security_event(device, event_type: str, ip_address: str = None, location: dict = None, details: dict = None):
        """
        Log a security event for a device.

        Args:
            device: MobileDevice instance
            event_type: Type of event (login, logout, bind, unbind, sync_failed)
            ip_address: IP address
            location: Location dict {latitude, longitude, address}
            details: Additional event details

        Returns:
            DeviceSecurityLog instance
        """
        from apps.mobile.models import DeviceSecurityLog

        return DeviceSecurityLog.objects.create(
            device=device,
            event_type=event_type,
            ip_address=ip_address,
            location=location or {},
            details=details or {}
        )
