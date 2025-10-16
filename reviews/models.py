from django.db import models

from utils.exceptions import ObjectDoesNotExistException


class Review(models.Model):
    """Represents a customer review for a product."""

    customer = models.ForeignKey(
        "customer.Customer",
        on_delete=models.CASCADE,
        verbose_name="Customer",
    )
    first_name = models.CharField(max_length=100, verbose_name="First name")
    rating = models.SmallIntegerField(verbose_name="Rating")
    comment = models.TextField(max_length=500, verbose_name="Comment")
    phone = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Phone"
    )
    advantages = models.TextField(
        max_length=500, blank=True, null=True, verbose_name="Advantages"
    )
    disadvantages = models.TextField(
        max_length=500, blank=True, null=True, verbose_name="Disadvantages"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Publication date"
    )
    is_publish = models.BooleanField(default=0, verbose_name="Published?")
    reply = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="_replies",
        verbose_name="Reply to",
    )

    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-created_at"]

    @classmethod
    def get_review_by_pk(cls, pk: int) -> "Review":
        """Returns a review by its primary key or raises an exception if not found."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Review with pk '{pk}' does not exist."}
            )
