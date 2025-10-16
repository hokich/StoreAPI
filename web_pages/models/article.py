from django.conf import settings
from django.db import models

from .base import BasePage


class ArticlePage(BasePage):
    """SEO and metadata page model for a blog article."""

    article = models.OneToOneField(
        "blog.Article", on_delete=models.CASCADE, related_name="_article_page"
    )

    class Meta:
        verbose_name = "Article Page"
        verbose_name_plural = "Article Pages"

    def __str__(self) -> str:
        return f"Article page {self.article.name} | {self.article.slug}"

    @property
    def title(self) -> str:
        """Returns the SEO title for the article page."""
        text = f"{self.h1} – useful information about home appliances – Store"
        return self._title if self._title else text

    @property
    def h1(self) -> str:
        """Returns the H1 header of the article."""
        text = self.article.name
        return self._h1 if self._h1 else text

    @property
    def description(self) -> str:
        """Returns the SEO meta description for the article page."""
        text = self.h1
        return self._description if self._description else text

    def get_absolute_url(self) -> str:
        """Returns the absolute client-side URL for the article page."""
        return f"{settings.CLIENT_BASE_URL}/blog/{self.article.slug}/"
