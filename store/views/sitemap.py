from typing import Any

from django.db.models import Count, Exists, OuterRef, Q
from requests import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.response_service import ResponseService

from ..models import Brand, Catalog, Collection, Product, Selection


class SitemapDataAPIView(APIView):
    """Provides aggregated slugs for sitemap generation."""

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Returns slugs for brands, selections, categories, listings, collections, and products."""
        brands = Brand.objects.filter(object_class="brand").values_list(
            "slug", flat=True
        )
        products = Product.objects.filter(publish=True).values_list(
            "slug", flat=True
        )

        has_children = Catalog.objects.filter(parent=OuterRef("pk"))
        categories_qs = (
            Catalog.objects.select_related("parent")
            .prefetch_related("children")
            .annotate(product_count=Count("_products"))
            .filter(object_class__in=["listing", "category"])
            .filter(Q(Exists(has_children)) | Q(product_count__gt=0))
        )

        categories = categories_qs.filter(object_class="category").values_list(
            "slug", flat=True
        )
        listings = categories_qs.filter(object_class="listing").values_list(
            "slug", flat=True
        )

        collections = Collection.objects.filter(
            object_class="collection"
        ).values("slug", "parent__slug")
        selections = Selection.objects.filter(
            object_class="selection"
        ).values_list("slug", flat=True)

        return ResponseService.success(
            {
                "brands": list(brands),
                "selections": list(selections),
                "categories": list(categories),
                "listings": list(listings),
                "collections": [
                    {
                        "slug": collection["slug"],
                        "parent": collection["parent__slug"],
                    }
                    for collection in collections
                ],
                "products": list(products),
            }
        )
