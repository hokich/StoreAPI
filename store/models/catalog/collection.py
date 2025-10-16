from django.db.models import QuerySet

from utils.exceptions import ObjectDoesNotExistException

from ..product import Product
from .base import Catalog


class Collection(Catalog):
    """Represents a product collection as a proxy model of Catalog."""

    class Meta:
        proxy = True

    def get_collection_products(self) -> "QuerySet[Product]":
        """Returns all published products that belong to this collection."""
        from ...services.product import get_products_by_filter

        products = Product.objects.filter(publish=True)

        return get_products_by_filter(
            products,
            listing=self.parent,
            tags_slugs=self.active_filters.get("tags"),
            prices=self.active_filters.get("prices"),
            attributes=self.active_filters.get("attributes"),
        )

    def get_collection_products_count(self) -> int:
        """Returns the number of products in this collection."""
        return self.get_collection_products().count()

    @classmethod
    def get_collection_by_slug_and_parent(
        cls, slug: str, parent_id: int
    ) -> "Collection":
        """Returns a collection by its slug and parent ID or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(slug=slug, parent_id=parent_id)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Collection object with slug '{slug}' and parent_id '{parent_id}' does not exist."
                }
            )
