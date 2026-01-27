from rest_framework import routers
from apps.depreciation.viewsets import (
    DepreciationConfigViewSet,
    DepreciationRecordViewSet,
    DepreciationRunViewSet,
)

app_router = routers.DefaultRouter()

# Depreciation configuration endpoints
app_router.register(r'configs', DepreciationConfigViewSet, basename='depreciation-config')

# Depreciation record endpoints
app_router.register(r'records', DepreciationRecordViewSet, basename='depreciation-record')

# Depreciation run endpoints
app_router.register(r'runs', DepreciationRunViewSet, basename='depreciation-run')

urlpatterns = app_router.urls
