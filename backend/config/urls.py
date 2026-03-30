"""
URL configuration for GZEAMS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.common.viewsets.health import (
    HealthCheckAPIView,
    LivenessAPIView,
    HealthMetricsAPIView,
    ReadinessAPIView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    path('api/health/', HealthCheckAPIView.as_view(), name='health-check'),
    path('api/health/live/', LivenessAPIView.as_view(), name='health-live'),
    path('api/health/ready/', ReadinessAPIView.as_view(), name='health-ready'),
    path('api/health/metrics/', HealthMetricsAPIView.as_view(), name='health-metrics'),

    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ============================================================
    # SYSTEM-LEVEL ENDPOINTS (Keep - Not business objects)
    # ============================================================
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/permissions/', include('apps.permissions.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/sso/', include('apps.sso.urls')),
    path('api/search/', include('apps.search.urls')),
    path('api/objects/', include('apps.assets.tag_urls')),
    path('api/system/', include('apps.system.urls')),  # Dynamic routing + metadata
    path('api/workflows/', include('apps.workflows.urls')),
    path('api/sla/', include('apps.workflows.sla_urls')),

    # ============================================================
    # BUSINESS OBJECT ENDPOINTS (Hybrid approach)
    # ============================================================
    # Keep assets URL for statistics endpoint and other special actions
    # Main CRUD uses: /api/system/objects/{code}/
    # Special endpoints use: /api/assets/statistics/, etc.
    path('api/assets/', include('apps.assets.urls')),
    path('api/consumables/', include('apps.consumables.urls')),
    path('api/inventory/', include('apps.inventory.urls')),
    path('api/lifecycle/', include('apps.lifecycle.urls')),
    path('api/it-assets/', include('apps.it_assets.urls')),
    path('api/software-licenses/', include('apps.software_licenses.urls')),
    path('api/leasing/', include('apps.leasing.urls')),
    path('api/insurance/', include('apps.insurance.urls')),
    path('api/finance/', include('apps.finance.urls')),
    path('api/depreciation/', include('apps.depreciation.urls')),
    path('api/mobile/', include('apps.mobile.urls')),
    path('api/projects/', include('apps.projects.urls')),

    # Integration remains a dedicated domain module (not a business object CRUD route)
    path('api/integration/', include('apps.integration.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]

# Custom admin site config
admin.site.site_header = 'GZEAMS Administration'
admin.site.site_title = 'GZEAMS Admin Portal'
admin.site.index_title = 'Welcome to GZEAMS'
