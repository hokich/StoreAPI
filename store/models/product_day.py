from django.db import models


class ProductDay(models.Model):
    """Represents a product that is featured as the 'product of the day'."""

    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    show_date = models.DateField("Show date")

    def __str__(self) -> str:
        """Returns the product name as string representation."""
        return self.product.name

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "show_date"],
                name="unique_product_show_date",
            ),
        ]
        verbose_name = "Product of the day"
        verbose_name_plural = "Products of the day"

    @classmethod
    def clean_products_day(cls) -> None:
        """Deletes all product of the day records."""
        cls.objects.all().delete()
