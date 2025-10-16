from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from .models import ShortLink
from .serializers import ShortLinkSerializer


class ShortLinkViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """ViewSet for retrieving short links by slug."""

    queryset = ShortLink.objects.all()
    serializer_class = ShortLinkSerializer
    lookup_field = "slug"

    def retrieve(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Returns the target link by its slug."""
        instance = ShortLink.get_link_by_slug(kwargs["slug"])
        serializer = self.get_serializer(instance)
        return ResponseService.success(serializer.data)
