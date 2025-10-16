from typing import Optional

from django.db import models
from django.db.models import QuerySet
from pandas import DataFrame

from store.models.product import Product


class TagImporter(models.Model):
    """Represents an importer that assigns tags to products based on SKU lists."""

    name = models.CharField(max_length=100, verbose_name="Name")

    items_list = models.JSONField(default=list, verbose_name="List of SKUs")

    tags = models.ManyToManyField(
        "store.Catalog", blank=False, related_name="+"
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Date added"
    )
    date_start = models.DateField(
        blank=True, null=True, verbose_name="Start date"
    )
    date_end = models.DateField(blank=True, null=True, verbose_name="End date")

    active = models.BooleanField(default=False, verbose_name="Active")

    class Meta:
        verbose_name = "Tag importer"
        verbose_name_plural = "Tag importers"
        ordering = ["-created_at"]

    @property
    def tags_names_list(self) -> QuerySet[list]:
        """Returns a list of tag names associated with the importer."""
        return self.tags.all().values_list("name", flat=True)

    def activate(self) -> None:
        """Activates the importer and assigns tags to matching products."""
        products = Product.objects.filter(sku__in=self.items_list)
        for product in products:
            product._tags.add(*self.tags.all())
        self.active = True
        self.save()

    def deactivate(self) -> None:
        """Deactivates the importer and removes assigned tags from products."""
        products = Product.objects.filter(sku__in=self.items_list)
        for product in products:
            product._tags.remove(*self.tags.all())
        self.active = False
        self.save()

    @classmethod
    def find_tag_importer_by_pk(cls, pk: int) -> Optional["TagImporter"]:
        """Finds a TagImporter instance by its primary key."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            return None

    @staticmethod
    def get_items_list_from_xlsx(df: DataFrame) -> list:
        """Extracts a list of SKU strings from an Excel DataFrame."""
        return [str(val[0]) for val in df.values]
