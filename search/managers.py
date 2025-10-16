from typing import TYPE_CHECKING, Any

from django.db import models

from ranking_index.services import create_ranking_index


if TYPE_CHECKING:
    from .models import SearchQuery


class SearchQueryManager(models.Manager):
    """Custom manager for the SearchQuery model."""

    def create(self, **kwargs: Any) -> "SearchQuery":
        """
        Overrides the default `create` method for the SearchQuery model.
        Automatically assigns a new popularity ranking index upon creation.
        """
        search_query = super().create(
            popular=create_ranking_index(),
            **kwargs,
        )
        return search_query
