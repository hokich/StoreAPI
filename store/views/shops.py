from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from ..models import Shop
from ..serializers.shop import ShopSerializer, ShopShortSerializer


class ShopsListViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """ViewSet for listing shops with optional pickup and brief filters."""

    serializer_class = ShopSerializer
    queryset = Shop.objects.filter(lat__isnull=False, long__isnull=False)

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Returns a list of shops with optional pickup, city, and brief parameters."""
        pickup_param = request.query_params.get("pickup", "0")
        is_pickup = pickup_param.lower() in ["true", "1"]
        brief_param = request.query_params.get("brief", "0")
        is_brief = brief_param.lower() in ["true", "1"]
        city_id = request.query_params.get("city")
        queryset = self.get_queryset()
        if is_pickup:
            queryset = queryset.filter(pickup=True)
        if city_id:
            queryset = queryset.filter(city_obj__id=city_id)

        serializer = ShopSerializer(queryset, many=True)
        if is_brief:
            serializer = ShopShortSerializer(queryset, many=True)
        return ResponseService.success(serializer.data)
