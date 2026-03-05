"""
URL configuration for the metadata-driven low-code engine.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.system.viewsets import (
    BusinessObjectViewSet,
    FieldDefinitionViewSet,
    PageLayoutViewSet,
    DynamicDataViewSet,
    DynamicSubTableDataViewSet,
    UserColumnPreferenceViewSet,
    TabConfigViewSet,
    ObjectRouterViewSet,  # Dynamic object routing
    LanguageViewSet,  # i18n
    TranslationViewSet,  # i18n
)
from apps.system.viewsets.system_file import SystemFileViewSet
from apps.system.viewsets.menu import MenuViewSet  # Dynamic menu system

# Conditionally import business rule viewsets (may not be available)
try:
    from apps.system.viewsets.business_rule import (
        BusinessRuleViewSet,
        RuleExecutionViewSet,
    )
    BUSINESS_RULE_VIEWS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    BUSINESS_RULE_VIEWS_AVAILABLE = False
    BusinessRuleViewSet = None
    RuleExecutionViewSet = None

# Conditionally import config package viewsets
try:
    from apps.system.viewsets.config_package import (
        ConfigPackageViewSet,
        ConfigImportLogViewSet,
    )
    CONFIG_PACKAGE_VIEWS_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    CONFIG_PACKAGE_VIEWS_AVAILABLE = False
    ConfigPackageViewSet = None
    ConfigImportLogViewSet = None

router = DefaultRouter()
router.register(r'business-objects', BusinessObjectViewSet, basename='business-object')
router.register(r'field-definitions', FieldDefinitionViewSet, basename='field-definition')
router.register(r'page-layouts', PageLayoutViewSet, basename='page-layout')
router.register(r'dynamic-data', DynamicDataViewSet, basename='dynamic-data')
router.register(r'sub-table-data', DynamicSubTableDataViewSet, basename='sub-table-data')
router.register(r'column-preferences', UserColumnPreferenceViewSet, basename='columnpreference')
router.register(r'tab-configs', TabConfigViewSet, basename='tabconfig')
router.register(r'system-files', SystemFileViewSet, basename='system-file')  # File upload/management
router.register(r'menu', MenuViewSet, basename='menu')  # Dynamic menu
# i18n routes
router.register(r'languages', LanguageViewSet, basename='language')
router.register(r'translations', TranslationViewSet, basename='translation')

# Conditionally register business rule routes
if BUSINESS_RULE_VIEWS_AVAILABLE:
    router.register(r'rules', BusinessRuleViewSet, basename='business-rule')  # Business rules
    router.register(r'rule-executions', RuleExecutionViewSet, basename='rule-execution')  # Rule logs

# Conditionally register config package routes
if CONFIG_PACKAGE_VIEWS_AVAILABLE:
    router.register(r'config-packages', ConfigPackageViewSet, basename='config-package')
    router.register(r'config-imports', ConfigImportLogViewSet, basename='config-import')

# Note: ObjectRouterViewSet is registered separately with custom patterns below
# to support {code} parameter instead of DefaultRouter's standard <pk> pattern

app_name = 'system'

urlpatterns = [
    path('', include(router.urls)),
    # Custom dynamic object routing patterns with {code} parameter
    # These must come after the router to avoid conflicts
    path('objects/<str:code>/', ObjectRouterViewSet.as_view({'get': 'list', 'post': 'create'}), name='object-router-list'),
    path('objects/<str:code>/metadata/', ObjectRouterViewSet.as_view({'get': 'metadata'}), name='object-router-metadata'),
    path('objects/<str:code>/fields/', ObjectRouterViewSet.as_view({'get': 'fields'}), name='object-router-fields'),
    path('objects/<str:code>/relations/', ObjectRouterViewSet.as_view({'get': 'relations'}), name='object-router-relations'),
    path('objects/<str:code>/runtime/', ObjectRouterViewSet.as_view({'get': 'runtime'}), name='object-router-runtime'),
    path('objects/<str:code>/schema/', ObjectRouterViewSet.as_view({'get': 'schema'}), name='object-router-schema'),
    path('objects/<str:code>/deleted/', ObjectRouterViewSet.as_view({'get': 'deleted'}), name='object-router-deleted'),
    path('objects/<str:code>/batch-get/', ObjectRouterViewSet.as_view({'post': 'batch_get'}), name='object-router-batch-get'),
    path('objects/<str:code>/batch-delete/', ObjectRouterViewSet.as_view({'post': 'batch_delete'}), name='object-router-batch-delete'),
    path('objects/<str:code>/batch-restore/', ObjectRouterViewSet.as_view({'post': 'batch_restore'}), name='object-router-batch-restore'),
    path('objects/<str:code>/batch-update/', ObjectRouterViewSet.as_view({'post': 'batch_update'}), name='object-router-batch-update'),
    # Current user convenience endpoints (User only)
    path('objects/<str:code>/me/', ObjectRouterViewSet.as_view({'get': 'me'}), name='object-router-me'),
    path('objects/<str:code>/me/profile/', ObjectRouterViewSet.as_view({'put': 'me_profile', 'patch': 'me_profile'}), name='object-router-me-profile'),
    path('objects/<str:code>/me/change-password/', ObjectRouterViewSet.as_view({'post': 'me_change_password'}), name='object-router-me-change-password'),
    path('objects/<str:code>/<uuid:id>/', ObjectRouterViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='object-router-detail'),
    path('objects/<str:code>/<uuid:id>/restore/', ObjectRouterViewSet.as_view({'post': 'restore'}), name='object-router-restore'),
    path(
        'objects/<str:code>/<uuid:id>/related/<str:relation_code>/',
        ObjectRouterViewSet.as_view({'get': 'related'}),
        name='object-router-related',
    ),
    # Generic custom-action pass-through (kept at the end to avoid shadowing standard routes)
    path('objects/<str:code>/<uuid:id>/<path:action_path>/', ObjectRouterViewSet.as_view({
        'get': 'detail_action',
        'post': 'detail_action',
        'put': 'detail_action',
        'patch': 'detail_action',
        'delete': 'detail_action',
    }), name='object-router-detail-action'),
    path('objects/<str:code>/<path:action_path>/', ObjectRouterViewSet.as_view({
        'get': 'collection_action',
        'post': 'collection_action',
        'put': 'collection_action',
        'patch': 'collection_action',
        'delete': 'collection_action',
    }), name='object-router-collection-action'),
]
