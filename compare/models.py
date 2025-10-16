from django.db import models


class CompareProduct(models.Model):
    """Represents a product added by a customer to the comparison list."""

    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="_compare_products",
    )
    product = models.ForeignKey(
        "store.Product", on_delete=models.CASCADE, related_name="+"
    )
    date_added = models.DateTimeField(
        auto_now_add=True, verbose_name="Date added"
    )

    class Meta:
        verbose_name = "Compared product"
        verbose_name_plural = "Compared products"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product"],
                name="unique_customer_compare_product",
            ),
        ]
        ordering = ["date_added"]
