from rest_framework import status
from rest_framework.response import Response
from typing import Any, Dict, List, Optional


class BaseResponse:
    """
    Standardized API response builder.

    Provides consistent response format for all endpoints.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Operation successful",
        http_status: int = status.HTTP_200_OK
    ) -> Response:
        """Build a success response."""
        response = {'success': True, 'message': message}
        if data is not None:
            response['data'] = data
        return Response(response, status=http_status)

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Created successfully"
    ) -> Response:
        """Build a 201 Created response."""
        response = {'success': True, 'message': message}
        if data is not None:
            response['data'] = data
        return Response(response, status=status.HTTP_201_CREATED)

    @staticmethod
    def no_content(message: str = "No content") -> Response:
        """Build a 204 No Content response."""
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Dict] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST
    ) -> Response:
        """Build an error response."""
        response = {
            'success': False,
            'error': {'code': code, 'message': message}
        }
        if details is not None:
            response['error']['details'] = details
        return Response(response, status=http_status)

    @staticmethod
    def validation_error(
        details: Dict,
        message: str = "Validation failed"
    ) -> Response:
        """Build a validation error response."""
        return BaseResponse.error(
            code='VALIDATION_ERROR',
            message=message,
            details=details,
            http_status=status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def unauthorized(message: str = "Authentication required") -> Response:
        """Build a 401 Unauthorized response."""
        return BaseResponse.error(
            code='UNAUTHORIZED',
            message=message,
            http_status=status.HTTP_401_UNAUTHORIZED
        )

    @staticmethod
    def permission_denied(message: str = "Permission denied") -> Response:
        """Build a 403 Permission Denied response."""
        return BaseResponse.error(
            code='PERMISSION_DENIED',
            message=message,
            http_status=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def not_found(resource: str = "Resource") -> Response:
        """Build a 404 Not Found response."""
        return BaseResponse.error(
            code='NOT_FOUND',
            message=f"{resource} not found",
            http_status=status.HTTP_404_NOT_FOUND
        )

    @staticmethod
    def organization_mismatch(message: str = "Organization mismatch") -> Response:
        """Build a 403 Organization Mismatch response."""
        return BaseResponse.error(
            code='ORGANIZATION_MISMATCH',
            message=message,
            http_status=status.HTTP_403_FORBIDDEN
        )

    @staticmethod
    def soft_deleted(message: str = "Resource has been deleted") -> Response:
        """Build a 410 Gone response for soft-deleted resources."""
        return BaseResponse.error(
            code='SOFT_DELETED',
            message=message,
            http_status=status.HTTP_410_GONE
        )

    @staticmethod
    def server_error(message: str = "Internal server error") -> Response:
        """Build a 500 Server Error response."""
        return BaseResponse.error(
            code='SERVER_ERROR',
            message=message,
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    @staticmethod
    def paginated(
        count: int,
        next_url: Optional[str],
        previous_url: Optional[str],
        results: List[Any]
    ) -> Response:
        """Build a paginated list response."""
        return Response({
            'success': True,
            'data': {
                'count': count,
                'next': next_url,
                'previous': previous_url,
                'results': results
            }
        }, status=status.HTTP_200_OK)


# Convenience functions for direct import (backward compatibility)
def success_response(
    data: Any = None,
    message: str = "Operation successful",
    http_status: int = status.HTTP_200_OK
) -> Response:
    """Create a success response using DRF Response class."""
    return BaseResponse.success(data, message, http_status)


def error_response(
    code: str = "ERROR",
    message: str = "An error occurred",
    details: Optional[Dict] = None,
    http_status: int = status.HTTP_400_BAD_REQUEST
) -> Response:
    """Create an error response using DRF Response class."""
    return BaseResponse.error(code, message, details, http_status)
