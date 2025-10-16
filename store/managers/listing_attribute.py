from typing import Any

from django.db import models

from ranking_index.services import create_ranking_index


class ListingAttributeManager(models.Manager):
    """Custom manager for `ListingAttribute` with automatic ranking index assignment."""

    def create(self, **kwargs: Any) -> Any:
        """Overrides `create` to automatically assign a `popular` ranking index."""
        return super().create(popular=create_ranking_index(), **kwargs)
