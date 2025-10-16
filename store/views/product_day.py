from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from ..models import ProductDay
from ..serializers.product_day import ProductDaySerializer


class ProductsDayViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ViewSet for listing 'Product of the Day' items."""

    serializer_class = ProductDaySerializer
    queryset = ProductDay.objects.filter(
        product__publish=True,
        product__quantity__gte=1,  # >= 1
    ).prefetch_related(
        "product",
        "product___images",
        "product___images__thumb_image",
        "product___images__sd_image",
        "product___images__hd_image",
    )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Returns a list of 'Product of the Day' entries."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponseService.success(serializer.data)
