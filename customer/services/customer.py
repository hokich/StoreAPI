import datetime
import string
from typing import Optional, TypedDict, cast

from django.utils.crypto import get_random_string

from cart.services import create_cart
from utils.exceptions import (
    EmailInvalidException,
    ObjectAlreadyExistsException,
    PhoneInvalidException,
)
from utils.validation import is_email_valid, is_phone_valid

from ..models import Customer


def _get_random_uid() -> str:
    while True:
        uid = get_random_string(8, string.ascii_letters + string.digits)
        if not Customer.objects.filter(session_id=uid).exists():
            return uid


class CreateCustomerDict(TypedDict, total=False):
    phone: Optional[str]
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    patronymic: Optional[str]
    date_birth: Optional[datetime.date]
    city: Optional[str]
    street: Optional[str]
    house: Optional[str]
    apartment: Optional[str]
    yandex_uids: Optional[str]


def create_customer(
    customer_data: Optional[CreateCustomerDict] = None,
) -> "Customer":
    """Creates a customer from the provided data."""
    session_id = _get_random_uid()

    if not customer_data:
        return Customer.objects.create(
            session_id=session_id, cart=create_cart()
        )

    phone = customer_data.get("phone")
    email = customer_data.get("email")

    if phone and not is_phone_valid(phone):
        raise PhoneInvalidException(
            {"message": f"Phone number {phone} is invalid."}
        )

    if email and not is_email_valid(email):
        raise EmailInvalidException(
            {"message": f"Contact email {email} is invalid."}
        )

    if Customer.objects.filter(phone=phone).exists():
        raise ObjectAlreadyExistsException(
            {
                "message": f"Customer with phone {phone} already exists",
                "fields": ["phone"],
            }
        )

    if Customer.objects.filter(email=email).exists():
        raise ObjectAlreadyExistsException(
            {
                "message": f"Customer with email {email} already exists",
                "fields": ["email"],
            }
        )

    return Customer.objects.create(
        session_id=session_id,
        cart=create_cart(),
        phone=phone,
        email=email,
        first_name=customer_data.get("first_name"),
        last_name=customer_data.get("last_name"),
        patronymic=customer_data.get("patronymic"),
        date_birth=customer_data.get("date_birth"),
        city=customer_data.get("city"),
        street=customer_data.get("street"),
        house=customer_data.get("house"),
        apartment=customer_data.get("apartment"),
        yandex_uids=customer_data.get("yandex_uids"),
    )


def update_customer(
    customer: Customer, update_data: CreateCustomerDict
) -> "Customer":
    """Updates an existing customer with the provided fields."""

    phone = update_data.get("phone")
    email = update_data.get("email")

    if "phone" in update_data:
        if phone and not is_phone_valid(phone):
            raise PhoneInvalidException(
                {"message": f"Phone number {phone} is invalid."}
            )
        if (
            phone
            and Customer.objects.filter(phone=phone)
            .exclude(pk=customer.id)
            .exists()
        ):
            print(
                customer,
                customer.id,
                phone,
                Customer.objects.filter(phone=phone).exclude(pk=customer.id),
            )
            raise ObjectAlreadyExistsException(
                {
                    "message": f"Customer with phone {phone} already exists",
                    "fields": ["phone"],
                }
            )
        customer.phone = phone

    if "email" in update_data:
        if email and not is_email_valid(email):
            raise EmailInvalidException(
                {"message": f"Contact email {email} is invalid."}
            )
        if (
            email
            and Customer.objects.exclude(pk=customer.id)
            .filter(email=email)
            .exists()
        ):
            raise ObjectAlreadyExistsException(
                {
                    "message": f"Customer with email {email} already exists",
                    "fields": ["email"],
                }
            )
        customer.email = email

    # Обновл`яем остальные поля, если они переданы (включая возможность установки None)
    if "first_name" in update_data:
        customer.first_name = update_data["first_name"]

    if "last_name" in update_data:
        customer.last_name = update_data["last_name"]

    if "patronymic" in update_data:
        customer.patronymic = update_data["patronymic"]

    if "date_birth" in update_data:
        customer.date_birth = update_data["date_birth"]

    if "city" in update_data:
        customer.city = update_data["city"]

    if "street" in update_data:
        customer.street = update_data["street"]

    if "house" in update_data:
        customer.house = update_data["house"]

    if "apartment" in update_data:
        customer.apartment = update_data["apartment"]

    if "yandex_uids" in update_data:
        customer.yandex_uids = update_data["yandex_uids"]

    customer.save()

    return customer


class FillMissingCustomerDict(TypedDict, total=False):
    phone: Optional[str]
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    patronymic: Optional[str]
    date_birth: Optional[datetime.date]
    city: Optional[str]
    street: Optional[str]
    house: Optional[str]
    apartment: Optional[str]


def _is_blank(v: object | None) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def _clean_str(v: object | None) -> Optional[str]:
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    return None


def fill_missing_customer_data(
    customer: "Customer", additional_data: FillMissingCustomerDict
) -> "Customer":
    """
    Fills missing customer fields from the provided payload.
    Only fields that are currently empty (None or blank string) are updated.
    Phone/email validation and conflicts are handled inside `update_customer`.
    """

    str_fields: tuple[str, ...] = (
        "phone",
        "email",
        "first_name",
        "last_name",
        "patronymic",
        "city",
        "street",
        "house",
        "apartment",
    )

    to_update: dict = {}

    for field in str_fields:
        if field not in additional_data:
            continue
        if _is_blank(getattr(customer, field, None)):
            new_val = _clean_str(additional_data.get(field))
            if new_val is not None:
                to_update[field] = new_val

    if "date_birth" in additional_data and _is_blank(
        getattr(customer, "date_birth", None)
    ):
        new_date = additional_data.get("date_birth")
        if new_date:
            to_update["date_birth"] = new_date

    if not to_update:
        return customer

    return update_customer(customer, cast(CreateCustomerDict, to_update))


def init_customer(uid: Optional[str] = None) -> tuple["Customer", bool]:
    """Initializes or creates a customer by session ID."""
    created = False
    if uid:
        # Try to find a customer by the given uid
        customer = Customer.objects.filter(session_id=uid).first()
    else:
        customer = None

    if not customer:
        # Create a new customer when not found or uid missing
        customer = create_customer()
        created = True

    return customer, created
