"""
SSO Services

All services inherit from BaseCRUDService for automatic
CRUD methods and consistent behavior.
"""
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.common.services.base_crud import BaseCRUDService
from apps.sso.models import WeWorkConfig, UserMapping, OAuthState

# Role model may not exist yet, import conditionally
try:
    from apps.accounts.models import Role
    ROLE_MODEL_EXISTS = True
except ImportError:
    Role = None
    ROLE_MODEL_EXISTS = False

User = get_user_model()


class SSOService:
    """Base SSO service with common utilities."""

    @staticmethod
    def generate_state() -> str:
        """Generate random state token."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_oauth_state(platform: str, session_data: dict = None) -> str:
        """Create and store OAuth state.

        Args:
            platform: Platform type (wework/dingtalk/feishu)
            session_data: Optional session data to store

        Returns:
            State token string
        """
        state = SSOService.generate_state()
        expires_at = timezone.now() + timedelta(minutes=10)

        OAuthState.objects.create(
            state=state,
            platform=platform,
            session_data=session_data or {},
            expires_at=expires_at
        )

        return state

    @staticmethod
    def validate_and_consume_state(state: str, platform: str) -> dict:
        """Validate and consume OAuth state.

        Args:
            state: State token string
            platform: Platform type

        Returns:
            Session data if valid, empty dict otherwise
        """
        return OAuthState.consume(state, platform) or {}


class WeWorkConfigService(BaseCRUDService):
    """WeWork configuration service - inherits BaseCRUDService."""

    def __init__(self):
        super().__init__(WeWorkConfig)

    def get_enabled_config(self, organization_id: int = None) -> WeWorkConfig:
        """Get enabled WeWork configuration.

        Args:
            organization_id: Organization ID, uses current context if None

        Returns:
            WeWorkConfig instance

        Raises:
            ValueError: If no enabled config found
        """
        from apps.common.middleware import get_current_organization

        org_id = organization_id or get_current_organization()
        if not org_id:
            raise ValueError("Cannot determine organization")

        try:
            return self.model_class.objects.get(
                organization_id=org_id,
                is_enabled=True,
                is_deleted=False
            )
        except WeWorkConfig.DoesNotExist:
            raise ValueError("WeWork not configured or not enabled")

    def get_config_by_corp_id(self, corp_id: str) -> Optional[WeWorkConfig]:
        """Get configuration by corp ID.

        Args:
            corp_id: WeWork corp ID

        Returns:
            WeWorkConfig instance or None
        """
        try:
            return self.model_class.objects.get(
                corp_id=corp_id,
                is_deleted=False
            )
        except WeWorkConfig.DoesNotExist:
            return None


class UserMappingService(BaseCRUDService):
    """User mapping service - inherits BaseCRUDService."""

    def __init__(self):
        super().__init__(UserMapping)

    def get_by_platform_userid(self, platform: str,
                               platform_userid: str) -> Optional[UserMapping]:
        """Get mapping by platform user ID.

        Args:
            platform: Platform type
            platform_userid: Platform user ID

        Returns:
            UserMapping instance or None
        """
        try:
            return self.model_class.objects.get(
                platform=platform,
                platform_userid=platform_userid,
                is_deleted=False
            )
        except UserMapping.DoesNotExist:
            return None

    def get_user_mappings(self, user_id: str) -> Dict[str, UserMapping]:
        """Get all platform mappings for a user.

        Args:
            user_id: System user ID

        Returns:
            Dictionary mapping platform to UserMapping
        """
        mappings = self.model_class.objects.filter(
            system_user_id=user_id,
            is_deleted=False
        )
        return {m.platform: m for m in mappings}

    def create_or_update_mapping(
        self,
        user: User,
        platform: str,
        platform_userid: str,
        platform_name: str = None,
        platform_unionid: str = None,
        extra_data: dict = None
    ) -> UserMapping:
        """Create or update user mapping.

        Args:
            user: System user
            platform: Platform type
            platform_userid: Platform user ID
            platform_name: Platform display name
            platform_unionid: Platform UnionID
            extra_data: Extra platform data

        Returns:
            UserMapping instance
        """
        # Check if mapping exists for this platform and user
        existing = self.model_class.objects.filter(
            system_user=user,
            platform=platform,
            is_deleted=False
        ).first()

        if existing:
            # Update existing mapping
            existing.platform_userid = platform_userid
            existing.platform_unionid = platform_unionid or ''
            existing.platform_name = platform_name or ''
            existing.extra_data = extra_data or {}
            existing.save()
            return existing
        else:
            # Create new mapping
            return self.model_class.objects.create(
                system_user=user,
                platform=platform,
                platform_userid=platform_userid,
                platform_unionid=platform_unionid or '',
                platform_name=platform_name or '',
                extra_data=extra_data or {}
            )


class WeWorkSSOService(SSOService):
    """WeWork SSO service."""

    def __init__(self):
        self.config_service = WeWorkConfigService()
        self.mapping_service = UserMappingService()

    def get_config(self, organization_id: int = None) -> WeWorkConfig:
        """Get WeWork configuration.

        Args:
            organization_id: Organization ID

        Returns:
            WeWorkConfig instance
        """
        return self.config_service.get_enabled_config(organization_id)

    def get_auth_url(self, redirect_uri: str,
                     organization_id: int = None) -> str:
        """Get OAuth authorization URL.

        Args:
            redirect_uri: OAuth callback URL
            organization_id: Organization ID

        Returns:
            Authorization URL
        """
        config = self.get_config(organization_id)
        state = self.create_oauth_state('wework')

        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        return adapter.get_oauth_url(redirect_uri, state)

    def get_qr_connect_url(self, redirect_uri: str,
                           organization_id: int = None) -> str:
        """Get QR code login URL.

        Args:
            redirect_uri: OAuth callback URL
            organization_id: Organization ID

        Returns:
            QR code login URL
        """
        config = self.get_config(organization_id)
        state = self.create_oauth_state('wework')

        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        return adapter.get_qr_connect_url(redirect_uri, state)

    def handle_callback(self, code: str, state: str) -> dict:
        """Handle OAuth callback.

        Args:
            code: OAuth authorization code
            state: OAuth state token

        Returns:
            Dictionary with token and user info

        Raises:
            ValueError: If validation fails
        """
        # Validate state
        session_data = self.validate_and_consume_state(state, 'wework')
        if session_data is None:
            raise ValueError("Invalid state parameter")

        # Get configuration
        config = self.get_config()

        # Get WeWork user info
        from apps.sso.adapters.wework_adapter import WeWorkAdapter
        adapter = WeWorkAdapter(config)
        user_info = adapter.get_user_info_by_code(code)

        # Find or create system user
        user = self.get_or_create_user(user_info, config)

        # Generate JWT token
        token = self.generate_jwt_token(user)

        return {
            'token': token,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'real_name': getattr(user, 'real_name', user.username),
                'email': user.email,
                'mobile': getattr(user, 'mobile', ''),
                'avatar': getattr(user, 'avatar', ''),
                'department_id': str(user.department_id) if user.department_id else None,
                'organization_id': str(user.organization_id) if user.organization_id else None,
            }
        }

    def get_or_create_user(self, user_info: dict, config: WeWorkConfig) -> User:
        """Get or create system user from WeWork user info.

        Args:
            user_info: WeWork user info
            config: WeWork configuration

        Returns:
            User instance

        Raises:
            ValueError: If auto-create is disabled
        """
        # Find existing mapping
        mapping = self.mapping_service.get_by_platform_userid(
            'wework',
            user_info['userid']
        )

        if mapping:
            user = mapping.system_user
            # Update user info
            self._update_user_info(user, user_info)
            return user

        # Create new user
        if not config.auto_create_user:
            raise ValueError("Auto-create user is disabled, please contact admin")

        return self._create_user(user_info, config)

    def _create_user(self, user_info: dict, config: WeWorkConfig) -> User:
        """Create new user from WeWork info.

        Args:
            user_info: WeWork user info
            config: WeWork configuration

        Returns:
            User instance
        """
        username = f"ww_{user_info['userid']}"

        # Check if username exists
        if User.objects.filter(username=username).exists():
            username = f"ww_{user_info['userid']}_{secrets.token_hex(4)}"

        # Get main department
        department_id = None
        if user_info.get('main_department'):
            from apps.organizations.models import Department
            try:
                department = Department.objects.get(
                    wework_dept_id=user_info['main_department'],
                    organization=config.organization,
                    is_deleted=False
                )
                department_id = department.id
            except Department.DoesNotExist:
                pass

        user = User.objects.create(
            username=username,
            email=user_info.get('email', ''),
            mobile=user_info.get('mobile', ''),
            organization=config.organization,
            department_id=department_id,
            is_active=True,
            is_staff=False,
            is_superuser=False,
            created_by=None  # SSO created users have no creator
        )

        # Set real_name if field exists
        if hasattr(user, 'real_name'):
            user.real_name = user_info['name']
            user.save(update_fields=['real_name'])

        # Set avatar if provided
        if hasattr(user, 'avatar') and user_info.get('avatar'):
            user.avatar = user_info['avatar']
            user.save(update_fields=['avatar'])

        # Set default role
        if config.default_role_id and ROLE_MODEL_EXISTS:
            try:
                role = Role.objects.get(id=config.default_role_id)
                user.roles.add(role)
            except Role.DoesNotExist:
                pass

        # Create mapping
        self.mapping_service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid=user_info['userid'],
            platform_name=user_info['name']
        )

        return user

    def _update_user_info(self, user: User, user_info: dict):
        """Update user info from WeWork data.

        Args:
            user: User instance
            user_info: WeWork user info
        """
        update_fields = []

        if hasattr(user, 'real_name'):
            user.real_name = user_info['name']
            update_fields.append('real_name')

        if user_info.get('email') and user_info['email'] != user.email:
            user.email = user_info['email']
            update_fields.append('email')

        if hasattr(user, 'mobile') and user_info.get('mobile'):
            user.mobile = user_info['mobile']
            update_fields.append('mobile')

        if hasattr(user, 'avatar') and user_info.get('avatar'):
            user.avatar = user_info['avatar']
            update_fields.append('avatar')

        if update_fields:
            user.save(update_fields=update_fields)

        # Update mapping
        self.mapping_service.create_or_update_mapping(
            user=user,
            platform='wework',
            platform_userid=user_info['userid'],
            platform_name=user_info['name']
        )

    def generate_jwt_token(self, user) -> str:
        """Generate JWT token for user.

        Args:
            user: User instance

        Returns:
            JWT token string
        """
        try:
            from apps.accounts.auth import generate_jwt_token
            return generate_jwt_token(user)
        except ImportError:
            # Fallback: simple token generation
            import jwt
            from datetime import datetime, timedelta
            from django.conf import settings

            secret = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
            expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 60 * 24 * 7)

            payload = {
                'user_id': str(user.id),
                'username': user.username,
                'org_id': str(user.organization_id) if user.organization_id else None,
                'exp': datetime.utcnow() + timedelta(minutes=expire_minutes),
                'iat': datetime.utcnow(),
            }

            return jwt.encode(payload, secret, algorithm=algorithm)
