from .base import Catalog


class FreeTag(Catalog):
    """Represents a free tag as a proxy model of Catalog."""

    class Meta:
        proxy = True
