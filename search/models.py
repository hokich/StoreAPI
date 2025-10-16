from typing import Optional

from django.db import models

from utils.exceptions import ObjectDoesNotExistException

from .managers import SearchQueryManager


class SearchQuery(models.Model):
    """Represents a search query entered by a user."""

    text = models.CharField(max_length=255, unique=True, verbose_name="Text")
    is_publish = models.BooleanField(
        default=True, verbose_name="Is published?"
    )
    is_moderation = models.BooleanField(
        default=False, verbose_name="Is approved?"
    )
    count_requests = models.IntegerField(
        default=1, verbose_name="Number of requests"
    )
    popular = models.OneToOneField(
        "ranking_index.RankingIndex",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Popularity index",
    )
    catalog = models.ForeignKey(
        "store.Catalog",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Catalog",
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created at"
    )

    objects = SearchQueryManager()

    class Meta:
        verbose_name = "Search query"
        verbose_name_plural = "Search queries"
        ordering = ["-created_at"]

    @classmethod
    def get_query_by_pk(cls, pk: int) -> "SearchQuery":
        """Returns a search query by its primary key or raises an exception if not found."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Search query with pk '{pk}' does not exist."}
            )

    @classmethod
    def find_query_by_text(cls, text: str) -> Optional["SearchQuery"]:
        """Finds a search query by its text or returns None if not found."""
        try:
            return cls.objects.get(text=text)
        except cls.DoesNotExist:
            return None

    def increment_count_requests(self, count: int = 1) -> None:
        """Increments the number of times this search query was requested."""
        self.count_requests += count
        self.save()
