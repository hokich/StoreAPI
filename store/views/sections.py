from typing import Any

from django.db.models import F, Prefetch, QuerySet
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response

from utils.response_service import ResponseService

from ..models import Product
from ..serializers.product import ProductCardSerializer
from ..services.attribute import get_products_attributes_queryset_for_prefetch


class ProductsSectionsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Provides endpoints for product sections: bestsellers, best prices, new arrivals."""

    serializer_class = ProductCardSerializer
    queryset = Product.objects.filter(
        publish=True,
        quantity__gte=1,  # >= 1
    ).prefetch_related(
        "_images",
        "_images__thumb_image",
        "_images__sd_image",
        "_images__hd_image",
        "_tags",
        Prefetch(
            "_product_attributes",
            queryset=get_products_attributes_queryset_for_prefetch(),
        ),
    )

    def get_queryset(self) -> QuerySet[Product]:
        """Returns a queryset tailored to the current action."""
        if self.action == "bestsellers":
            return self.queryset.filter(_tags__slug="hit").order_by(
                "-sales___index"
            )
        elif self.action == "best_prices":
            return (
                self.queryset.filter(
                    _tags__slug="luchshaya-cena",
                )
                .annotate(
                    _discount_amount=F("price") * F("discount_percent") / 100
                )
                .order_by("-_discount_amount")
            )
        elif self.action == "new_arrival":
            return self.queryset.filter(
                _tags__slug="novinka",
            ).order_by("-created_at")
        return self.queryset

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Disabled: use specific section endpoints."""
        raise NotFound()

    @action(detail=False, methods=["get"])
    def bestsellers(self, request: Request) -> Response:
        """Returns top-selling products."""
        queryset = self.get_queryset()[:100]
        return ResponseService.success(
            self.get_serializer(queryset, many=True).data
        )

    @action(detail=False, methods=["get"], url_path="best-prices")
    def best_prices(self, request: Request) -> Response:
        """Returns products with the best prices (highest discount amount)."""
        queryset = self.get_queryset()[:100]
        return ResponseService.success(
            self.get_serializer(queryset, many=True).data
        )

    @action(detail=False, methods=["get"], url_path="new-arrival")
    def new_arrival(self, request: Request) -> Response:
        """Returns newly arrived products."""
        queryset = self.get_queryset()[:100]
        return ResponseService.success(
            self.get_serializer(queryset, many=True).data
        )
