from .base import Catalog


class Listing(Catalog):
    """Represents a product listing as a proxy model of Catalog."""

    class Meta:
        proxy = True
