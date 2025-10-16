from django.conf import settings
from django.db import models

from .base import BasePage


class ProductPage(BasePage):
    """SEO and metadata page model for an individual product."""

    product = models.OneToOneField(
        "store.Product", on_delete=models.CASCADE, related_name="_product_page"
    )

    class Meta:
        verbose_name = "Product Page"
        verbose_name_plural = "Product Pages"

    def __str__(self) -> str:
        return f"Product page {self.product.name} | {self.product.slug}"

    @property
    def title(self) -> str:
        """Returns the SEO title for the product page."""
        text = f"Buy {self.h1} in Berlin and Germany – Store online"
        return self._title if self._title else text

    @property
    def h1(self) -> str:
        """Returns the H1 header for the product page."""
        text = self.product.name
        return self._h1 if self._h1 else text

    @property
    def description(self) -> str:
        """Returns the SEO meta description for the product page."""
        text = (
            f"Buy {self.h1} in Berlin with delivery – "
            f"STORE ✅ Reviews ✅ Specs ✅ Affordable prices"
        )
        return self._description if self._description else text

    def get_absolute_url(self) -> str:
        """Returns the absolute client-side URL for the product page."""
        return f"{settings.CLIENT_BASE_URL}/product/{self.product.slug}/"
