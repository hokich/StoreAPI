from typing import Any, Optional

from django.db.models import Case, IntegerField, Prefetch, QuerySet, When
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.request import Request
from rest_framework.response import Response

from utils.exceptions import ObjectDoesNotExistException, PageNotFoundException
from utils.response_service import ResponseService

from ..models import Product, ProductReview
from ..serializers.product import (
    ProductCardSerializer,
    ProductForPageSerializer,
)
from ..serializers.product_review import ProductReviewSerializer
from ..serializers.shop import ProductInShopSerializer
from ..services.attribute import get_products_attributes_queryset_for_prefetch


class ProductReviewsPagination(LimitOffsetPagination):
    """Paginates product reviews with a fixed page size."""

    default_limit = 5
    max_limit = 5

    def paginate_queryset(self, *args: Any, **kwargs: Any) -> Any:
        """Paginates the queryset and converts 404 into a handled error."""
        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound:
            raise PageNotFoundException({"message": "Page does not exist."})


class ProductViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """Provides product detail endpoints and related resources."""

    serializer_class = ProductForPageSerializer
    lookup_field = "slug"

    def get_queryset(self) -> QuerySet[Product]:
        """Returns the base queryset depending on the current action."""
        if self.action == "retrieve":
            return (
                Product.objects.filter(publish=True)
                .select_related("_product_page")
                .prefetch_related(
                    "_images",
                    "_images__thumb_image",
                    "_images__sd_image",
                    "_images__hd_image",
                    "_tags",
                    "_services",
                    Prefetch(
                        "_product_attributes",
                        queryset=get_products_attributes_queryset_for_prefetch(),
                    ),
                )
            )
        elif self.action == "specifications":
            return Product.objects.filter(publish=True).prefetch_related(
                Prefetch(
                    "_product_attributes",
                    queryset=get_products_attributes_queryset_for_prefetch(),
                ),
            )
        else:
            return Product.objects.filter(publish=True)

    def get_object(self) -> Product:
        """Returns a published product by slug or raises a 404-like error."""
        slug = self.kwargs.get("slug")
        try:
            return self.get_queryset().get(slug=slug)
        except Product.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Product with slug '{slug}' does not exist."}
            )

    def retrieve(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns product details and increments popularity index."""
        instance = self.get_object()
        # Increment product popularity index on each request
        instance.popular.index_counter_increment()
        serializer = self.get_serializer(instance)
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"])
    def specifications(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns grouped product specifications."""
        return ResponseService.success(
            self.get_object().get_serialized_grouped_attributes_list()
        )

    @action(detail=True, methods=["get"])
    def additional(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns additional (related) products."""
        queryset = (
            self.get_object()
            .additional_products.filter(
                publish=True,
                quantity__gte=1,  # >= 1
            )
            .prefetch_related(
                "_images",
                "_images__thumb_image",
                "_images__sd_image",
                "_images__hd_image",
                "_tags",
            )
        )
        serializer = ProductCardSerializer(queryset, many=True)
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"], url_path="same-products")
    def same_products(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns similar products."""
        return ResponseService.success(
            self.get_object().get_serialized_similar_products()
        )

    @action(detail=True, methods=["get"])
    def shops(self, request: Request, slug: Optional[str] = None) -> Response:
        """Returns product availability across pickup shops."""
        product_in_shops = (
            self.get_object()
            .product_in_shops.filter(shop__pickup=True)
            .select_related("shop")
            .annotate(
                in_stock=Case(
                    When(quantity__gt=0, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
            .order_by("-in_stock", "shop__order")
        )
        serializer = ProductInShopSerializer(product_in_shops, many=True)
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"])
    def reviews(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns published reviews for the product with pagination."""
        product = self.get_object()
        reviews = ProductReview.objects.filter(
            product=product, review__is_publish=True
        )
        paginator = ProductReviewsPagination()
        paginated_products = paginator.paginate_queryset(reviews, request)
        serializer = ProductReviewSerializer(paginated_products, many=True)
        return ResponseService.success(serializer.data)
