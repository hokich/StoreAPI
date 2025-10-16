from django.conf import settings
from django.db import models

from .base import BasePage


class SimplePage(BasePage):
    """Represents a static informational page (e.g. Home, About, Delivery, etc.)."""

    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Simple Page"
        verbose_name_plural = "Simple Pages"

    def __str__(self) -> str:
        return f"Page {self.slug}"

    @property
    def title(self) -> str:
        """Returns the SEO title for the static page."""
        return self._title if self._title else "STORE"

    @property
    def h1(self) -> str:
        """Returns the H1 header for the static page."""
        return self._h1 if self._h1 else "STORE"

    @property
    def description(self) -> str:
        """Returns the SEO meta description for the static page."""
        return self._description if self._description else "Store online"

    def get_absolute_url(self) -> str:
        """Returns the absolute client-side URL for the static page."""
        if self.slug == "home":
            return f"{settings.CLIENT_BASE_URL}/"
        return f"{settings.CLIENT_BASE_URL}/{self.slug}/"
