from .base import Catalog


class Selection(Catalog):
    """Represents a product selection within the catalog."""

    class Meta:
        proxy = True
