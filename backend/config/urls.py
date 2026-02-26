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

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

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
    path('api/system/', include('apps.system.urls')),  # Dynamic routing + metadata
    path('api/workflows/', include('apps.workflows.urls')),

    # ============================================================
    # BUSINESS OBJECT ENDPOINTS (Hybrid approach)
    # ============================================================
    # Keep assets URL for statistics endpoint and other special actions
    # Main CRUD uses: /api/system/objects/{code}/
    # Special endpoints use: /api/assets/statistics/, etc.
    path('api/assets/', include('apps.assets.urls')),

    # Integration remains a dedicated domain module (not a business object CRUD route)
    path('api/integration/', include('apps.integration.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Django debug toolbar URLs
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls)),]

# Custom admin site config
admin.site.site_header = 'GZEAMS Administration'
admin.site.site_title = 'GZEAMS Admin Portal'
admin.site.index_title = 'Welcome to GZEAMS'
