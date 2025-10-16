from typing import Any

from django.db import models

from utils.exceptions import ObjectDoesNotExistException


class ProductAddService(models.Model):
    """Represents an additional service available for a product."""

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="_services",
        verbose_name="Product",
    )

    class ServiceType(models.TextChoices):
        SETTING_UP = "Setting up", "Setup"
        WARRANTY = "Extended warranty", "Extended warranty"
        INSTALLING = "Installation", "Installation"

    type = models.CharField(
        max_length=30, choices=ServiceType.choices, verbose_name="Service type"
    )
    name = models.CharField(max_length=255, verbose_name="Service name")
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=0,
        verbose_name="Service price",
    )

    class Meta:
        verbose_name = "Additional service"
        verbose_name_plural = "Additional services"
        ordering = ["type", "price"]

    @classmethod
    def get_service_by_pk(cls, pk: int, **kwargs: Any) -> "ProductAddService":
        """Retrieve a service by its primary key."""
        try:
            return cls.objects.get(pk=pk, **kwargs)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Service with pk '{pk}' does not exist."}
            )
