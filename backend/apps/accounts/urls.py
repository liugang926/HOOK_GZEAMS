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

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from apps.accounts.models import User
from apps.accounts.serializers import UserDetailSerializer

class LoginView(APIView):
    """
    Custom login view that returns the response format expected by the frontend.

    Frontend expects: { token: "...", user: {...} }
    simplejwt returns: { access: "...", refresh: "..." }
    """
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            'success': False,
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': 'Login endpoint requires POST request. If you are seeing this error manually, please check if your browser intercepted the request or if there was a redirect (e.g. missing trailing slash).'
            }
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Username and password are required'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid username or password'
                }
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_DISABLED',
                    'message': 'This account has been disabled'
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # Use simplejwt's TokenObtainPairView to get tokens
        # Create a mock request for the view
        from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
        token_serializer = TokenObtainPairSerializer(data=request.data)
        token_serializer.is_valid(raise_exception=True)
        tokens = token_serializer.validated_data

        # Get user's primary organization
        primary_org = user.user_orgs.filter(is_primary=True, is_active=True).first()
        if not primary_org:
            primary_org = user.user_orgs.filter(is_active=True).first()

        org_data = None
        if primary_org:
            org_data = {
                'id': str(primary_org.organization.id),
                'name': primary_org.organization.name,
                'role': primary_org.role
            }

        serializer = UserDetailSerializer(user)

        # Return the format expected by frontend
        return Response({
            'success': True,
            'data': {
                'token': tokens['access'],  # Frontend expects 'token'
                'refresh_token': tokens['refresh'],
                'user': serializer.data,
                'organization': org_data
            },
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        return Response(status=status.HTTP_200_OK)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),  # Use our custom view
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='token_logout'),
]
