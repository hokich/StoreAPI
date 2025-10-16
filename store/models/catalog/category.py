from django.db.models import Prefetch, QuerySet

from .. import Product
from .base import Catalog


class Category(Catalog):
    """Represents a product category as a proxy model of Catalog."""

    class Meta:
        proxy = True

    def get_popular_products(self) -> "QuerySet[Product]":
        """Returns up to 50 most popular published products with stock from this category and its children."""
        from ...services.attribute import (
            get_products_attributes_queryset_for_prefetch,
        )

        products_qs = (
            Product.objects.filter(
                publish=True,
                quantity__gte=1,
                _tags__id__in=self.children.all().values_list("pk", flat=True),
            )
            .exclude(popular___index=0)
            .prefetch_related(
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
        )
        return products_qs.order_by("-popular___index")[:50]
