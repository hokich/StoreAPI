from typing import Optional, TypedDict

from django.db import models
from django.utils import timezone

from utils.exceptions import ObjectDoesNotExistException


class CustomerInfoTypedDict(TypedDict, total=True):
    session_id: str
    phone: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]


class OrderContentTypedDict(TypedDict, total=True):
    products: list[dict]
    total_quantity: int
    total_price: int
    total_discount_price: int
    total_discount_amount: int
    total_bonuses_amount_dict: int


class Order(models.Model):
    """Customer order with delivery/payment details and status tracking."""

    id = models.BigAutoField(primary_key=True)
    customer_info = models.JSONField(
        default=dict, verbose_name="Customer info"
    )
    customer = models.ForeignKey(
        "customer.Customer",
        null=True,
        on_delete=models.CASCADE,
        related_name="_orders",
        verbose_name="Customer",
    )
    content = models.JSONField(default=dict, verbose_name="Content")
    content_for_receipt = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Content for receipt",
    )

    class Type(models.TextChoices):
        CART = "CART", "Cart"
        ONE_CLICK = "ONE_CLICK", "One-click purchase"
        CALL = "CALL", "Phone call"

    type = models.CharField(
        max_length=16, choices=Type.choices, verbose_name="Type"
    )

    class ReceptionMethod(models.TextChoices):
        DELIVERY = "DELIVERY", "Delivery"
        PICK_UP = "PICKUP", "Pickup"

    reception_method = models.CharField(
        max_length=16,
        choices=ReceptionMethod.choices,
        blank=True,
        null=True,
        verbose_name="Reception method",
    )

    class PaymentMethod(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"

    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        blank=True,
        null=True,
        verbose_name="Payment method",
    )

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        PROCESSED = "PROCESSED", "Processing"
        PAID = "PAID", "Paid"
        COMPLETED = "COMPLETED", "Completed"
        CANCELED = "CANCELED", "Canceled"

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
        verbose_name="Status",
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created at"
    )

    # Delivery data
    city = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="City"
    )
    street = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Street"
    )
    house = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="House"
    )
    apartment = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Apartment"
    )

    shop = models.ForeignKey(
        "store.Shop",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Shop",
    )

    comment = models.TextField(blank=True, null=True, verbose_name="Comment")

    is_callback = models.BooleanField(default=False, verbose_name="Callback")

    spent_bonuses = models.IntegerField(
        default=0,
        verbose_name="Spent bonuses",
    )

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]

    @property
    def created_at_local(self) -> timezone.datetime:
        """Returns localized creation datetime."""
        return timezone.localtime(self.created_at)

    @classmethod
    def get_order_by_pk(cls, pk: int) -> "Order":
        """Returns order by PK or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Order with pk {pk} does not exist."}
            )

    @classmethod
    def find_order_by_pk(cls, pk: int | str) -> Optional["Order"]:
        """Finds order by PK or returns None."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            return None
