from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from ..models import City
from ..serializers.city import CitySerializer


class CitiesListViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):

    serializer_class = CitySerializer
    queryset = City.objects.all()

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponseService.success(serializer.data)
