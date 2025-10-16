from django.db import models


class ProductReview(models.Model):
    """Represents a link between a product and a review."""

    product = models.ForeignKey(
        "store.Product",
        on_delete=models.CASCADE,
        verbose_name="Product",
    )
    review = models.ForeignKey(
        "reviews.Review",
        on_delete=models.CASCADE,
        verbose_name="Review",
    )

    class Meta:
        verbose_name = "Product review"
        verbose_name_plural = "Product reviews"
        ordering = ["-review__created_at"]
