from django.db import models


class RecentlyViewed(models.Model):
    """Represents a product recently viewed by a customer."""

    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="_viewed_products",
    )
    product = models.ForeignKey("store.Product", on_delete=models.CASCADE)
    date_viewed = models.DateTimeField(auto_now=True, verbose_name="View date")

    class Meta:
        verbose_name = "Recently viewed product"
        verbose_name_plural = "Recently viewed products"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product"],
                name="unique_customer_recently_product",
            ),
        ]
        ordering = ["-date_viewed"]
