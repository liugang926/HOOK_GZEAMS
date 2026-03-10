import re
from copy import deepcopy

from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.common.responses.base import BaseResponse
from apps.system.models import SystemConfig, SystemFile
from apps.system.serializers import SystemFileListSerializer


BRANDING_CONFIG_KEY = 'BRANDING_SETTINGS'
BRANDING_CONFIG_NAME = 'Branding Settings'
BRANDING_CONFIG_CATEGORY = 'branding'
HEX_COLOR_RE = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')

DEFAULT_BRANDING_SETTINGS = {
    'appName': 'GZEAMS',
    'appShortName': 'GZEAMS',
    'appTagline': 'Enterprise Asset Management System',
    'appIconText': 'G',
    'theme': {
        'primaryColor': '#0f172a',
        'accentColor': '#3b82f6',
        'sidebarGradientStart': '#1e293b',
        'sidebarGradientEnd': '#0f172a',
        'borderRadius': 10,
        'darkMode': False,
    },
    'assets': {
        'sidebarLogoFileId': None,
        'loginLogoFileId': None,
        'faviconFileId': None,
        'loginBackgroundFileId': None,
    },
    'login': {
        'title': 'GZEAMS',
        'subtitle': 'Secure workspace for enterprise asset operations',
        'copyright': '\u00a9 2026 GZEAMS Enterprise Asset Management System',
    },
    'loginI18n': {
        'zh-CN': {
            'title': 'GZEAMS',
            'subtitle': '\u4f01\u4e1a\u8d44\u4ea7\u8fd0\u8425\u7edf\u4e00\u5de5\u4f5c\u53f0',
            'copyright': '\u00a9 2026 GZEAMS \u4f01\u4e1a\u8d44\u4ea7\u7ba1\u7406\u7cfb\u7edf',
        },
        'en-US': {
            'title': 'GZEAMS',
            'subtitle': 'Secure workspace for enterprise asset operations',
            'copyright': '\u00a9 2026 GZEAMS Enterprise Asset Management System',
        },
    },
}

ASSET_FIELD_TO_ALIAS = {
    'sidebarLogoFileId': 'sidebarLogo',
    'loginLogoFileId': 'loginLogo',
    'faviconFileId': 'favicon',
    'loginBackgroundFileId': 'loginBackground',
}


def deep_merge(base, override):
    merged = deepcopy(base)
    if not isinstance(override, dict):
        return merged

    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class BrandingThemeSerializer(serializers.Serializer):
    primaryColor = serializers.CharField(max_length=20)
    accentColor = serializers.CharField(max_length=20)
    sidebarGradientStart = serializers.CharField(max_length=20)
    sidebarGradientEnd = serializers.CharField(max_length=20)
    borderRadius = serializers.IntegerField(min_value=0, max_value=32)
    darkMode = serializers.BooleanField()

    def validate(self, attrs):
        for color_key in (
            'primaryColor',
            'accentColor',
            'sidebarGradientStart',
            'sidebarGradientEnd',
        ):
            value = str(attrs.get(color_key, '')).strip()
            if not HEX_COLOR_RE.match(value):
                raise serializers.ValidationError({color_key: 'Invalid hex color.'})
        return attrs


class BrandingAssetsSerializer(serializers.Serializer):
    sidebarLogoFileId = serializers.UUIDField(required=False, allow_null=True)
    loginLogoFileId = serializers.UUIDField(required=False, allow_null=True)
    faviconFileId = serializers.UUIDField(required=False, allow_null=True)
    loginBackgroundFileId = serializers.UUIDField(required=False, allow_null=True)


class BrandingLoginSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=80)
    subtitle = serializers.CharField(max_length=200)
    copyright = serializers.CharField(max_length=200)


class BrandingSettingsSerializer(serializers.Serializer):
    appName = serializers.CharField(max_length=80)
    appShortName = serializers.CharField(max_length=40)
    appTagline = serializers.CharField(max_length=120, allow_blank=True)
    appIconText = serializers.CharField(max_length=4)
    theme = BrandingThemeSerializer()
    assets = BrandingAssetsSerializer()
    login = BrandingLoginSerializer()
    loginI18n = serializers.DictField(required=False)

    def validate(self, attrs):
        app_icon_text = str(attrs.get('appIconText', '')).strip()
        if not app_icon_text:
            raise serializers.ValidationError({'appIconText': 'App icon text is required.'})
        attrs['appIconText'] = app_icon_text[:4]

        login_i18n = attrs.get('loginI18n') or {}
        normalized_login_i18n = {}
        for locale, value in login_i18n.items():
            locale_serializer = BrandingLoginSerializer(data=value)
            locale_serializer.is_valid(raise_exception=True)
            normalized_login_i18n[str(locale)] = locale_serializer.validated_data
        attrs['loginI18n'] = normalized_login_i18n
        return attrs


class BrandingSettingsAPIView(APIView):
    """
    System-wide branding settings for theme, logo, favicon, and login page assets.

    GET is public so the login page can render without authentication.
    PUT/PATCH require authentication and persist a single JSON config payload.
    """

    permission_classes = [AllowAny]

    def get_permissions(self):
        if self.request.method.upper() in {'PUT', 'PATCH'}:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        data = self._build_response_payload()
        return BaseResponse.success(data=data, message='Branding settings loaded.')

    def put(self, request):
        return self._save(request, partial=False)

    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial=False):
        if not isinstance(request.data, dict):
            return BaseResponse.validation_error(
                {'body': ['Branding payload must be a JSON object.']},
                message='Invalid branding payload.',
            )

        current = self._load_persisted_settings()
        payload = deep_merge(current, request.data) if partial else request.data

        serializer = BrandingSettingsSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        normalized_data = serializer.validated_data
        self._validate_asset_ids(normalized_data.get('assets', {}))

        config, created = SystemConfig.objects.get_or_create(
            organization_id=None,
            config_key=BRANDING_CONFIG_KEY,
            defaults={
                'config_value': self._dump_config_value(normalized_data),
                'value_type': 'json',
                'name': BRANDING_CONFIG_NAME,
                'category': BRANDING_CONFIG_CATEGORY,
                'created_by': request.user,
                'updated_by': request.user,
            },
        )
        if not created:
            config.config_value = self._dump_config_value(normalized_data)
            config.value_type = 'json'
            config.name = BRANDING_CONFIG_NAME
            config.category = BRANDING_CONFIG_CATEGORY
            config.updated_by = request.user
            config.save()

        data = self._build_response_payload(normalized_data)
        return BaseResponse.success(data=data, message='Branding settings saved.')

    def _load_persisted_settings(self):
        config = SystemConfig.objects.filter(
            organization_id=None,
            config_key=BRANDING_CONFIG_KEY,
            is_deleted=False,
        ).first()
        stored = config.get_typed_value() if config else None
        if not isinstance(stored, dict):
            return deepcopy(DEFAULT_BRANDING_SETTINGS)
        return deep_merge(DEFAULT_BRANDING_SETTINGS, stored)

    def _dump_config_value(self, data):
        import json
        return json.dumps(data)

    def _validate_asset_ids(self, assets):
        file_ids = [value for value in (assets or {}).values() if value]
        if not file_ids:
            return

        existing_ids = {
            str(file_id)
            for file_id in SystemFile.objects.filter(id__in=file_ids).values_list('id', flat=True)
        }
        missing_ids = [str(file_id) for file_id in file_ids if str(file_id) not in existing_ids]
        if missing_ids:
            raise serializers.ValidationError({
                'assets': [f'Invalid system file id: {missing_ids[0]}']
            })

    def _build_response_payload(self, seed_data=None):
        base_data = deep_merge(DEFAULT_BRANDING_SETTINGS, seed_data or self._load_persisted_settings())
        asset_files = self._resolve_asset_files(base_data.get('assets', {}))
        base_data['resolvedAssets'] = asset_files
        return base_data

    def _resolve_asset_files(self, assets):
        file_id_map = {
            field_name: str(file_id)
            for field_name, file_id in (assets or {}).items()
            if file_id
        }
        if not file_id_map:
            return {}

        files = SystemFile.objects.filter(id__in=file_id_map.values())
        serialized = SystemFileListSerializer(files, many=True).data
        serialized_by_id = {
            str(item.get('id')): item for item in serialized
        }

        resolved = {}
        for field_name, file_id in file_id_map.items():
            alias = ASSET_FIELD_TO_ALIAS.get(field_name, field_name)
            resolved[alias] = serialized_by_id.get(file_id)
        return resolved
