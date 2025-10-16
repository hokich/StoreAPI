import datetime

from django.db import models
from django.utils import timezone

from utils.exceptions import ObjectDoesNotExistException


class Shop(models.Model):
    """Represents a physical store location."""

    code = models.CharField(max_length=100, unique=True, verbose_name="Code")
    code2 = models.CharField(max_length=100, unique=True, verbose_name="Code2")
    name = models.CharField(max_length=100, verbose_name="Name")
    address = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Address"
    )
    city = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="City"
    )
    street = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Street"
    )
    house = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="House"
    )
    region = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Region"
    )
    postcode = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="Postcode"
    )
    city_obj = models.ForeignKey(
        "City",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="City object",
    )
    working_from = models.TimeField(verbose_name="Opens at")
    working_to = models.TimeField(verbose_name="Closes at")
    schedule_list = models.JSONField(
        default=list,
        null=True,
        blank=True,
        verbose_name="Work schedule as list of strings",
    )
    pickup = models.BooleanField(default=True, verbose_name="Pickup available")
    phone = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Phone number"
    )
    lat = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Latitude"
    )
    long = models.CharField(
        max_length=15, blank=True, null=True, verbose_name="Longitude"
    )
    order = models.SmallIntegerField(
        blank=True, null=True, verbose_name="Display order"
    )

    class Meta:
        verbose_name = "Shop"
        verbose_name_plural = "Shops"
        ordering = ["order"]

    def __str__(self) -> str:
        """Returns the shop name as a string representation."""
        return self.name

    @property
    def opening_hours_str(self) -> str:
        """Returns the shop working hours as a formatted string."""
        return f"Mon-Sun from {self.working_from.strftime('%H:%M')} to {self.working_to.strftime('%H:%M')}"

    @property
    def is_can_pick_up_now(self) -> bool:
        """Checks if pickup is currently possible based on working hours."""
        if not self.pickup:
            return False
        now = timezone.now()
        working_to_today = datetime.datetime.combine(now, self.working_to)
        almost_closing_time = working_to_today - datetime.timedelta(minutes=30)
        return now.hour >= 5 and now <= almost_closing_time

    @classmethod
    def get_shop_by_pk(cls, shop_id: int) -> "Shop":
        """Returns a shop by its primary key or raises ObjectDoesNotExistException if not found."""
        try:
            return cls.objects.get(pk=shop_id)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Shop with pk '{shop_id}' does not exist."}
            )


class ProductInShop(models.Model):
    """Represents a product and its quantity available in a specific shop."""

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="_product_in_shops",
        verbose_name="Product",
    )
    shop = models.ForeignKey(
        "Shop", on_delete=models.CASCADE, verbose_name="Shop"
    )
    quantity = models.PositiveSmallIntegerField(
        default=0, verbose_name="Quantity"
    )

    class Meta:
        verbose_name = "Product in shop"
        verbose_name_plural = "Products in shops"
        ordering = ["shop__order"]

    def __str__(self) -> str:
        """Returns a readable string with quantity, product, and shop name."""
        return (
            f"{self.quantity} pcs of {self.product.name} in {self.shop.name}"
        )
