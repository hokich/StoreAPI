from django.db import models


class FavoriteProduct(models.Model):
    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        related_name="_favorites_products",
    )
    product = models.ForeignKey(
        "store.Product", on_delete=models.CASCADE, related_name="+"
    )
    date_added = models.DateTimeField(
        auto_now_add=True, verbose_name="Date added"
    )

    class Meta:
        verbose_name = "Favorite product"
        verbose_name_plural = "Favorite products"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "product"],
                name="unique_customer_favorite_product",
            ),
        ]
        ordering = ["-date_added"]
