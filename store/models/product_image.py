from django.db import models

from utils.exceptions import ObjectDoesNotExistException


class ProductImage(models.Model):
    """Represents an image set associated with a product."""

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="_images",
        verbose_name="Product",
    )

    thumb_image = models.OneToOneField(
        "images.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Thumbnail",
    )
    sd_image = models.OneToOneField(
        "images.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="SD",
    )
    hd_image = models.OneToOneField(
        "images.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="HD",
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name="Main image",
    )

    class Meta:
        verbose_name = "Product image"
        verbose_name_plural = "Product images"
        ordering = ["-is_main", "-pk"]

    @classmethod
    def get_product_image_by_pk(cls, product_image_id: int) -> "ProductImage":
        """Returns a product image by its primary key or raises ObjectDoesNotExistException if not found."""
        try:
            return cls.objects.get(pk=product_image_id)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Product image with pk '{product_image_id}' does not exist."
                }
            )
