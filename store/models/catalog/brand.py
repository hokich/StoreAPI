from .base import Catalog


class Brand(Catalog):
    """Represents a brand as a proxy model of Catalog."""

    class Meta:
        proxy = True
