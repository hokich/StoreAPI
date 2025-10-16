from django.conf import settings
from django.db import models

from .base import BasePage


class CatalogPage(BasePage):
    """Page model representing SEO and metadata for any catalog entity (category, brand, listing, etc.)."""

    catalog = models.OneToOneField(
        "store.Catalog",
        on_delete=models.CASCADE,
        related_name="_catalog_page",
    )

    class Meta:
        verbose_name = "Catalog Page"
        verbose_name_plural = "Catalog Pages"

    def __str__(self) -> str:
        return f"Catalog page {self.catalog.object_class} | {self.catalog.name} | {self.catalog.slug}"

    @property
    def title(self) -> str:
        """
        Returns the SEO title for the page based on the catalog type.
        """
        match self.catalog.object_class:
            case "category":
                text = f"{self.catalog.name} — Buy {self.catalog.name} in Berlin, Germany"
            case "listing":
                text = f"{self.catalog.name} — Buy {self.catalog.name} in Berlin, Germany"
            case "collection":
                text = (
                    f"{self.catalog.parent.name} {self.catalog.name} — "
                    f"Buy {self.catalog.parent.name} {self.catalog.name} in Berlin, Germany"
                )
            case "selection":
                text = f"{self.h1} — Buy {self.h1.lower()} in Germany"
            case "brand":
                text = (
                    f"Products by brand {self.catalog.name} — "
                    f"buy {self.catalog.name} items — Store"
                )
            case _:
                text = self.catalog.name
        return self._title if self._title else text

    @property
    def h1(self) -> str:
        """
        Returns the H1 header for the catalog page.
        """
        match self.catalog.object_class:
            case "collection":
                text = f"{self.catalog.parent.name} {self.catalog.name}"
            case "brand":
                text = f"Products by brand {self.catalog.name}"
            case _:
                text = self.catalog.name
        return self._h1 if self._h1 else text

    @property
    def description(self) -> str:
        """
        Returns the meta description for SEO, depending on catalog type.
        """
        match self.catalog.object_class:
            case "category":
                text = (
                    f"{self.catalog.name} in Store online store "
                    f"at the best prices with delivery across Germany. "
                    f"STORE ✅ Reviews ✅ Specs ✅ Articles and overviews"
                )
            case "listing":
                text = (
                    f"Buy {self.catalog.name} with delivery across Germany. "
                    f"All {self.catalog.name} come with a warranty. "
                    f"STORE ✅ Reviews ✅ Specs ✅ Articles and overviews"
                )
            case "collection":
                text = (
                    f"Buy {self.catalog.parent.name} {self.catalog.name} with delivery across Germany. "
                    f"All {self.catalog.parent.name} {self.catalog.name} come with a warranty. "
                    f"STORE ✅ Reviews ✅ Specs ✅ Articles and overviews"
                )
            case "selection":
                text = (
                    f"Buy {self.h1.lower()} with delivery across Germany. "
                    f"All {self.h1.lower()} come with a warranty. "
                    f"STORE ✅ Reviews ✅ Specs ✅ Articles and overviews"
                )
            case "brand":
                text = (
                    f"Buy {self.catalog.name} brand products. "
                    f"Affordable prices for {self.catalog.name} brand items "
                    f"in Store Germany electronics store."
                )
            case _:
                text = self.catalog.name
        return self._description if self._description else text

    def get_absolute_url(self) -> str:
        """
        Returns the absolute client-side URL for the catalog page.
        """
        if self.catalog.object_class == "selection":
            return f"{settings.CLIENT_BASE_URL}/selection/{self.catalog.slug}/"
        elif self.catalog.object_class == "brand":
            return f"{settings.CLIENT_BASE_URL}/brand/{self.catalog.slug}/"
        elif self.catalog.object_class == "collection":
            return f"{settings.CLIENT_BASE_URL}/category/{self.catalog.parent.slug}/{self.catalog.slug}/"
        else:
            return f"{settings.CLIENT_BASE_URL}/category/{self.catalog.slug}/"
