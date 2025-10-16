from typing import Any

from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from .models import Banner
from .serializers import BannerSerializer


class GetActiveBannersView(ListAPIView):
    """Returns a list of currently active banners."""

    serializer_class = BannerSerializer

    def get_queryset(self) -> "QuerySet[Banner]":
        """Filters active banners by status and display period."""
        now = timezone.now().date()
        return (
            Banner.objects.select_related(
                "home_mobile_image",
                "home_desktop_image",
                "catalog_mobile_image",
                "catalog_desktop_image",
                "header_desktop_image",
            )
            .prefetch_related("_tags")
            .filter(
                is_active=True,
                date_start__lte=now,
            )
            .filter(Q(date_end__gte=now) | Q(date_end=None))
        )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Serializes and returns filtered banners."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponseService.success(serializer.data)
