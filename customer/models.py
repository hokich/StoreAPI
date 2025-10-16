from typing import TYPE_CHECKING, Iterator, Optional

from django.db import models

from utils.exceptions import ObjectDoesNotExistException


if TYPE_CHECKING:
    from django.db.models import QuerySet

    from orders.models import Order
    from store.models import City


class Customer(models.Model):
    """Represents a store customer with contact and delivery information."""

    session_id = models.CharField(
        max_length=255, unique=True, verbose_name="Session ID"
    )

    phone = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Phone",
    )
    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
        verbose_name="Email",
    )

    first_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="First name"
    )
    last_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Last name"
    )
    patronymic = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Middle name"
    )
    date_birth = models.DateField(
        blank=True, null=True, verbose_name="Date of birth"
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

    city_obj = models.ForeignKey(
        "store.City",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="City (object)",
    )

    yandex_uids = models.JSONField(
        default=list, blank=True, null=True, verbose_name="Yandex ClientIDs"
    )

    cart = models.OneToOneField(
        "cart.Cart",
        on_delete=models.PROTECT,
        related_name="customer",
        verbose_name="Cart",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created at",
    )

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self: "Customer") -> str:
        return self.session_id

    @property
    def orders(self) -> "QuerySet[Order]":
        """Returns all orders linked to this customer."""
        return self._orders.all()

    @property
    def clean_first_name(self) -> Optional[str]:
        """Returns first name or None if placeholder value."""
        return self.first_name if self.first_name != "ИМЯ" else None

    @property
    def clean_last_name(self) -> Optional[str]:
        """Returns last name or None if placeholder value."""
        return self.last_name if self.last_name != "ФАМИЛИЯ" else None

    @property
    def clean_patronymic(self) -> Optional[str]:
        """Returns middle name or None if placeholder value."""
        return self.patronymic if self.patronymic != "ОТЧЕСТВО" else None

    @property
    def full_name(self) -> str:
        """Returns the full formatted customer name."""
        parts: Iterator[str] = filter(
            None, [self.last_name, self.first_name, self.patronymic]
        )
        return " ".join(part.strip() for part in parts if part.strip())

    def set_city_obj(self, city: Optional["City"] = None) -> None:
        """Sets the related city object."""
        self.city_obj = city
        self.save()

    @classmethod
    def get_customer_by_pk(cls, pk: int) -> "Customer":
        """Returns a customer by PK or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Customer with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_customer_by_session_id(cls, session_id: str) -> "Customer":
        """Returns a customer by session ID or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(session_id=session_id)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Customer with session_id '{session_id}' does not exist."
                }
            )

    @classmethod
    def find_customer_by_phone(cls, phone: str) -> "Customer":
        """Finds a customer by phone number (returns first match or None)."""
        return cls.objects.filter(phone=phone).first()

    @classmethod
    def find_customer_by_session_id(
        cls, session_id: str
    ) -> Optional["Customer"]:
        """Finds a customer by session ID (returns first match or None)."""
        return cls.objects.filter(session_id=session_id).first()
