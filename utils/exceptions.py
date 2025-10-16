import logging
import traceback
from typing import Any, Dict, Optional

from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.views import exception_handler

from utils.response_service import ResponseService


logger = logging.getLogger(__name__)


def app_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    """Application-wide DRF exception handler that returns standardized responses."""
    # First, call DRF's default exception handler to get a Response
    response = exception_handler(exc, context)

    # Handle validation errors
    if isinstance(exc, ValidationError):
        valid_exc = ValidationErrorException(exc.args)
        logger.error(
            f"{valid_exc.message} {valid_exc.code}: {str(valid_exc.context)}"
        )

        def extract_first_error(detail: Any) -> Dict[str, Any]:
            """Extracts the first human-readable validation error from nested details."""
            if isinstance(detail, dict):
                for field, value in detail.items():
                    return extract_first_error(value) | {"fields": [field]}
            elif isinstance(detail, list):
                for item in detail:
                    return extract_first_error(item)
            else:
                return {"message": str(detail)}
            return {"message": "Validation error."}

        error_data = extract_first_error(exc.detail)

        return ResponseService.failure(
            valid_exc.message,
            valid_exc.code,
            error_data,
            status=status.HTTP_400_BAD_REQUEST,
        )

    # If DRF returned None, the exception isn't handled by DRF
    if response is None:
        if isinstance(exc, AppBaseException):
            logger.error(f"{exc.message} {exc.code}: {str(exc.context)}")
            return ResponseService.failure(
                exc.message, exc.code, exc.context, status=exc.http_status
            )

        # Get traceback info
        tb = traceback.extract_tb(exc.__traceback__)
        # Use the last frame where the error occurred
        last_trace = tb[-1]
        filename = last_trace.filename
        line_no = last_trace.lineno

        logger.error(
            f"Internal Error: {exc}, File: {filename}, Line: {line_no}"
        )

        # For all unhandled exceptions, return HTTP 500
        internal_exc = InternalErrorException()
        return ResponseService.failure(
            internal_exc.message,
            internal_exc.code,
            internal_exc.context,
            status=internal_exc.http_status,
        )
    return response


class AppBaseException(Exception):
    """Base application exception with code, HTTP status, and optional context."""

    def __init__(
        self,
        message: str,
        code: int,
        http_status: int = 500,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.context = context or {}


class ImageInvalidFormatException(AppBaseException):
    """Raised when an uploaded image has an invalid format."""

    def __init__(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            "ImageInvalidFormat", 2000, status.HTTP_400_BAD_REQUEST, context
        )


class ParentCatalogIsNotCategoryException(AppBaseException):
    """Raised when a parent catalog is expected to be a category but is not."""

    def __init__(self) -> None:
        super().__init__(
            "ParentCatalogIsNotCategory",
            5000,
            status.HTTP_400_BAD_REQUEST,
        )


class ProductIsNotPublishedException(AppBaseException):
    """Raised when a product is not published."""

    def __init__(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            "ProductIsNotPublished", 4000, status.HTTP_400_BAD_REQUEST, context
        )


class ProductIsNotInStockException(AppBaseException):
    """Raised when a product is out of stock."""

    def __init__(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            "ProductIsNotInStock", 4001, status.HTTP_400_BAD_REQUEST, context
        )


class ParentCatalogIsNotListingException(AppBaseException):
    """Raised when a parent catalog is expected to be a listing but is not."""

    def __init__(self) -> None:
        super().__init__(
            "ParentCatalogIsNotListing",
            5001,
            status.HTTP_400_BAD_REQUEST,
        )


class InternalErrorException(AppBaseException):
    """Generic internal server error."""

    def __init__(
        self,
        context: Optional[Any] = None,
    ) -> None:
        super().__init__(
            "InternalError",
            6000,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            context,
        )


class ObjectAlreadyExistsException(AppBaseException):
    """Raised when attempting to create an object that already exists."""

    def __init__(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            "ObjectAlreadyExists", 6002, status.HTTP_409_CONFLICT, context
        )


class ObjectDoesNotExistException(AppBaseException):
    """Raised when a requested object is not found."""

    def __init__(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            "ObjectDoesNotExist", 6003, status.HTTP_404_NOT_FOUND, context
        )


class ValidationErrorException(AppBaseException):
    """Raised for validation errors."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "ValidationError", 6004, status.HTTP_400_BAD_REQUEST, context
        )


class InvalidDataException(AppBaseException):
    """Raised when provided data is invalid."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "InvalidData", 6005, status.HTTP_400_BAD_REQUEST, context
        )


class PhoneInvalidException(AppBaseException):
    """Raised when a phone number is invalid."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "PhoneInvalid", 6006, status.HTTP_400_BAD_REQUEST, context
        )


class EmailInvalidException(AppBaseException):
    """Raised when an email address is invalid."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "EmailInvalid", 6007, status.HTTP_400_BAD_REQUEST, context
        )


class PageNotFoundException(AppBaseException):
    """Raised when a requested page is not found."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "PageNotFound", 7001, status.HTTP_404_NOT_FOUND, context
        )


class CustomerCartIsEmptyException(AppBaseException):
    """Raised when a customer's cart is empty."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "CustomerCartIsEmpty",
            11001,
            status.HTTP_400_BAD_REQUEST,
            context,
        )


class ProductNotInStockException(AppBaseException):
    """Raised when a specific product is not available in stock."""

    def __init__(self, context: Optional[Any] = None) -> None:
        super().__init__(
            "ProductNotInStock",
            13000,
            status.HTTP_404_NOT_FOUND,
            context,
        )
