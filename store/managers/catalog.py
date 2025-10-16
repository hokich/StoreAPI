from typing import Any

from django.db import models
from django.db.models.query import ModelIterable, QuerySet

from ranking_index.services import create_ranking_index


class CatalogModelIterable(ModelIterable):
    """Custom iterable for the `Catalog` model, allowing dynamic subclass instantiation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes a mapping of Catalog subclasses by name."""
        from ..models import Catalog

        super().__init__(*args, **kwargs)
        self.SUBCLASSES_OF_CATALOG = {
            c.__name__.lower(): c for c in Catalog.__subclasses__()
        }

    def __iter__(self) -> Any:
        """Iterates through objects and dynamically assigns their subclass type."""
        objs = super().__iter__()
        for obj in objs:
            subclass = self.SUBCLASSES_OF_CATALOG[obj.object_class]
            obj._meta.base_manager = subclass.objects
            obj._meta.model = subclass
            obj.__class__ = subclass
            yield obj


class CatalogQuerySet(QuerySet):
    """Custom QuerySet for the `Catalog` model using `CatalogModelIterable`."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._iterable_class = CatalogModelIterable


class CatalogManager(models.Manager):
    """Manager for the `Catalog` model with automatic subclass resolution and ranking index creation."""

    def get_queryset(self) -> CatalogQuerySet:
        """Overrides get_queryset to include related `_catalog_page` and return a `CatalogQuerySet`."""
        return CatalogQuerySet(self.model, using=self._db).select_related(
            "_catalog_page"
        )

    def create(self, **kwargs: Any) -> Any:
        """Overrides create to automatically set `object_class` and `popular` fields."""
        model_name = self.model._meta.model_name

        if model_name == "catalog":
            raise ValueError(
                "The base Catalog model cannot be created directly; use a subclass instead."
            )

        return super().create(
            object_class=model_name, popular=create_ranking_index(), **kwargs
        )
