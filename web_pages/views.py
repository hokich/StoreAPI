from typing import Any

from rest_framework.generics import RetrieveAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from .models import SimplePage
from .serializers import SimplePageSerializer


class GetSimplePageView(RetrieveAPIView):
    """
    API endpoint for retrieving a simple page by its slug.
    """

    queryset = SimplePage.objects.all()
    serializer_class = SimplePageSerializer
    lookup_field = "slug"
    lookup_url_kwarg = "slug"

    def retrieve(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Returns a simple page serialized response wrapped in ResponseService.success()."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseService.success(serializer.data)
