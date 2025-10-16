import re
from typing import Optional, TypedDict

from django.conf import settings
from django.utils.encoding import force_str

from customer.models import Customer
from store.models import Shop
from telegram.services import send_message_from_telegram_bot
from utils.exceptions import ValidationErrorException

from .models import CustomerInfoTypedDict, Order, OrderContentTypedDict


class CreateOrderTypedDict(TypedDict, total=True):
    customer: Customer
    customer_info: CustomerInfoTypedDict
    content: OrderContentTypedDict
    type: str
    reception_method: Optional[str]
    payment_method: Optional[str]
    shop_id: Optional[int]
    city: Optional[str]
    street: Optional[str]
    house: Optional[str]
    apartment: Optional[str]
    comment: Optional[str]
    is_callback: Optional[bool]


def create_new_order(order_data: CreateOrderTypedDict) -> Order:
    """
    Creates a new order from the provided data.

    :param order_data: Dict payload that matches CreateOrderTypedDict.
    :return: Created Order instance.
    :raises ValidationErrorException: if a required field is missing or
        an invalid value is provided for type, reception_method, or payment_method.
    """
    reception_method = order_data["reception_method"]
    # Validate reception_method
    if (
        reception_method is not None
        and reception_method not in Order.ReceptionMethod.values
    ):
        raise ValidationErrorException(
            {"message": f"Invalid reception method: {reception_method}"}
        )

    payment_method = order_data["payment_method"]
    # Validate payment_method
    if (
        payment_method is not None
        and payment_method not in Order.PaymentMethod.values
    ):
        raise ValidationErrorException(
            {"message": f"Invalid payment method: {payment_method}"}
        )

    # Validate type
    if order_data["type"] not in Order.Type.values:
        raise ValidationErrorException(
            {"message": f"Invalid order type: {order_data['type']}"}
        )

    # If shop_id is provided for pickup, validate the shop
    shop = None
    if (
        reception_method == Order.ReceptionMethod.PICK_UP
        and order_data["shop_id"]
    ):
        shop = Shop.get_shop_by_pk(order_data["shop_id"])

    order_fields = {
        "customer": order_data["customer"],
        "customer_info": order_data["customer_info"],
        "content": order_data["content"],
        "content_for_receipt": order_data["content"],
        "type": order_data["type"],
        "reception_method": reception_method,
        "payment_method": payment_method,
        "comment": order_data.get("comment", ""),
        "is_callback": order_data.get("is_callback", False),
    }

    if reception_method == Order.ReceptionMethod.DELIVERY:
        order_fields.update(
            {
                "city": order_data["city"],
                "street": order_data["street"],
                "house": order_data["house"],
                "apartment": order_data["apartment"],
            }
        )
    if shop:
        order_fields["shop"] = shop

    return Order.objects.create(**order_fields)


class UpdateOrderTypedDict(TypedDict, total=False):
    customer: Optional[Customer]
    customer_info: Optional[CustomerInfoTypedDict]
    content: Optional[OrderContentTypedDict]
    type: Optional[str]
    reception_method: Optional[str]
    city: Optional[str]
    street: Optional[str]
    house: Optional[str]
    apartment: Optional[str]
    comment: Optional[str]
    is_callback: Optional[bool]


def update_order(order: Order, update_data: UpdateOrderTypedDict) -> Order:
    """
    Updates an existing order with the provided data.

    :param order: Order instance to update.
    :param update_data: Dict payload that matches UpdateOrderTypedDict.
    :return: Updated Order instance.
    :raises ValidationErrorException: if an invalid value is provided for type
        or reception_method.
    """
    # type
    if "type" in update_data:
        if update_data["type"] not in Order.Type.values:
            raise ValidationErrorException(
                {"message": f"Invalid order type: {update_data['type']}"}
            )
        order.type = update_data["type"]

    # reception_method
    if "reception_method" in update_data:
        if update_data["reception_method"] not in Order.ReceptionMethod.values:
            raise ValidationErrorException(
                {
                    "message": f"Invalid reception method: {update_data['reception_method']}"
                }
            )
        order.reception_method = update_data["reception_method"]

    if "customer" in update_data:
        order.customer = update_data["customer"]

    if "customer_info" in update_data:
        order.customer_info = update_data["customer_info"]

    if "content" in update_data:
        order.content = update_data["content"]

    if "city" in update_data:
        order.city = update_data["city"]

    if "street" in update_data:
        order.street = update_data["street"]

    if "house" in update_data:
        order.house = update_data["house"]

    if "apartment" in update_data:
        order.apartment = update_data["apartment"]

    if "comment" in update_data:
        order.comment = update_data["comment"]

    if "is_callback" in update_data:
        order.is_callback = update_data["is_callback"]

    order.save()

    return order


def forming_order_text_msg(
    products_names: list[str],
    total_price: int | float,
    customer_name: str,
    customer_phone: str,
    custom_text: Optional[str] = None,
) -> str:
    """
    Builds a Telegram-friendly HTML message about a new order.
    """
    text = "<b>New order!</b>\nContents:"
    for product in products_names:
        text += "\n<i>- " + product + "</i>"
    text += "\n\nTotal price:"
    price_orig = force_str(str(round(total_price)))
    price_new = re.sub(r"^(-?\d+)(\d{3})", r"\g<1> \g<2>", price_orig)
    text += "\n" + price_new + "₽"
    text += "\n\nContacts:"
    first_name = customer_name
    text += (
        f'\n<i>{customer_phone}{f" - {first_name}" if first_name else ""}</i>'
    )
    if custom_text:
        text += f"\n\n<b>{custom_text}</b>"
    return text


def send_new_order_notification_in_telegram_chat(
    order: Order, custom_text: Optional[str] = None
) -> None:
    """
    Sends a new-order notification to the configured Telegram chat.
    """
    product_names = [
        cart_product["product"]["name"]
        for cart_product in order.content.get("products")
    ]
    text_msg = forming_order_text_msg(
        product_names,
        order.content["total_discount_price"],
        order.customer_info["first_name"],
        order.customer_info["phone"],
        custom_text,
    )
    try:
        send_message_from_telegram_bot(settings.TG_ORDERS_CHAT_ID, text_msg)
    except Exception as e:
        print("Error sending new order message", e)
