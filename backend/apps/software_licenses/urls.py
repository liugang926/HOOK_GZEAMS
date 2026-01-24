from rest_framework import routers
from apps.software_licenses.viewsets import (
    SoftwareViewSet,
    SoftwareLicenseViewSet,
    LicenseAllocationViewSet,
)

app_router = routers.DefaultRouter()

# Software catalog endpoints
app_router.register(r'software', SoftwareViewSet, basename='software')

# Software License endpoints
app_router.register(r'licenses', SoftwareLicenseViewSet, basename='software-license')

# License Allocation endpoints
app_router.register(r'license-allocations', LicenseAllocationViewSet, basename='license-allocation')

urlpatterns = app_router.urls
