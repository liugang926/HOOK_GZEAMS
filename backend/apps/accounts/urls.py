"""
URL configuration for Accounts app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.accounts import viewsets as accounts_viewsets
from apps.accounts.selector_viewsets.user_selector_viewsets import UserSelectorViewSet

router = DefaultRouter()
router.register(r'users', accounts_viewsets.UserViewSet, basename='user')
router.register(r'users/selector', UserSelectorViewSet, basename='user-selector')

app_name = 'accounts'

urlpatterns = [
    path('', include(router.urls)),
]
