from typing import Any, Dict, Optional

from rest_framework.response import Response


class ResponseService:
    """Utility class for creating standardized API responses."""

    @staticmethod
    def success(data: Any, status: int = 200) -> Response:
        """Returns a successful JSON response."""
        return Response(
            {"success": True, "data": data},
            status=status,
        )

    @staticmethod
    def failure(
        message: str,
        code: int,
        context: Optional[Dict] = None,
        status: int = 400,
    ) -> Response:
        """Returns an error JSON response."""
        return Response(
            {
                "success": False,
                "error": {
                    "message": message,
                    "code": code,
                    "context": context or {},
                    "status": status,
                },
            },
            status=status,
        )
