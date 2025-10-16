from typing import TYPE_CHECKING, Any

from django.db import models
from django.db.models import Avg, Case, Count, IntegerField, Q, When

from ranking_index.services import create_ranking_index


if TYPE_CHECKING:
    from ..models import Product


class ProductManager(models.Manager):
    """Custom manager for `Product` model with annotations and automatic ranking index creation."""

    def get_queryset(
        self, *args: Any, **kwargs: Any
    ) -> "models.QuerySet[Product]":
        """Returns a queryset annotated with product rating, review count, and status order."""
        return (
            super()
            .get_queryset()
            .annotate(
                status_order=Case(
                    When(quantity__gt=0, then=models.Value(1)),
                    When(quantity=0, then=models.Value(2)),
                    default=models.Value(3),  # Fallback for NULL quantities
                    output_field=IntegerField(),
                ),
                rating_avg=Avg(
                    "_reviews__rating", filter=Q(_reviews__is_publish=True)
                ),
                _reviews_count=Count(
                    "_reviews", filter=Q(_reviews__is_publish=True)
                ),
            )
            .order_by("status_order", "-popular___index", "-created_at")
        )

    def create(self, **kwargs: Any) -> Any:
        """Overrides `create` to automatically assign ranking indices (`popular`, `sales`, `often_search`)."""
        return super().create(
            popular=create_ranking_index(),
            sales=create_ranking_index(),
            often_search=create_ranking_index(),
            **kwargs,
        )
