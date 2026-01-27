from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    ValidationError as DRFValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied as DRFPermissionDenied,
    Throttled,
    NotFound,
    MethodNotAllowed
)
from django.http import Http404
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from apps.common.responses.base import BaseResponse

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.

    Handles:
    - Validation errors
    - Authentication errors
    - Permission denied
    - Not found errors
    - Throttling errors
    - Integrity errors
    - Unexpected errors

    Returns:
        Response with standardized error format
    """
    # Handle DRF Authentication failures
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return BaseResponse.unauthorized(str(exc.detail))

    # Handle DRF Permission denied
    if isinstance(exc, DRFPermissionDenied):
        return BaseResponse.permission_denied(str(exc.detail))

    # Handle DRF Throttling
    if isinstance(exc, Throttled):
        return BaseResponse.error(
            code='RATE_LIMIT_EXCEEDED',
            message=f'Request was throttled. Expected available in {exc.wait} seconds.',
            http_status=status.HTTP_429_TOO_MANY_REQUESTS
        )

    # Handle DRF NotFound
    if isinstance(exc, NotFound):
        return BaseResponse.not_found(str(exc.detail))

    # Handle DRF MethodNotAllowed
    if isinstance(exc, MethodNotAllowed):
        return BaseResponse.error(
            code='METHOD_NOT_ALLOWED',
            message=str(exc.detail),
            http_status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    # Handle DRF validation errors
    if isinstance(exc, DRFValidationError):
        details = exc.detail if isinstance(exc.detail, dict) else {'detail': exc.detail}
        return BaseResponse.validation_error(details, message='Validation failed')

    # Handle Django 404
    if isinstance(exc, Http404):
        return BaseResponse.not_found('Resource')

    # Handle Django validation error
    if isinstance(exc, DjangoValidationError):
        message = str(exc.message_dict if hasattr(exc, 'message_dict') else exc.message)
        return BaseResponse.validation_error({}, message=message)

    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        return BaseResponse.error(
            code='CONFLICT',
            message='Data conflict, possibly violating unique constraint',
            http_status=status.HTTP_409_CONFLICT
        )

    # Handle Python permission errors
    if isinstance(exc, PermissionError):
        return BaseResponse.permission_denied('Insufficient permissions')

    # Log unexpected errors
    logger.error(f"Unexpected exception: {exc}", exc_info=True)

    # Fall back to default DRF handler
    return exception_handler(exc, context)
