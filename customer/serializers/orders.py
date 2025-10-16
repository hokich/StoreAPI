from typing import Any, Optional, cast

from rest_framework import serializers

from cart.serializers import CartForOrderSerializer
from cart.services import add_product_to_cart, create_cart
from orders.models import CustomerInfoTypedDict, Order
from orders.services import create_new_order
from store.models import Product
from store.services.product import reduce_quantity_for_product
from utils.exceptions import (
    CustomerCartIsEmptyException,
    EmailInvalidException,
    ObjectAlreadyExistsException,
    PhoneInvalidException,
)
from utils.validation import is_email_valid, is_phone_valid

from ..models import Customer
from ..services.customer import (
    FillMissingCustomerDict,
    fill_missing_customer_data,
)


class CreateNewOrderFromCartSerializer(serializers.Serializer):
    customer = serializers.CharField(max_length=255, required=True)
    first_name = serializers.CharField(max_length=100, required=True)
    last_name = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True
    )
    email = serializers.CharField(
        max_length=255, required=False, allow_null=True, allow_blank=True
    )
    phone = serializers.CharField(max_length=20, required=True)
    reception_method = serializers.CharField(max_length=16, required=True)
    payment_method = serializers.CharField(max_length=16, required=True)
    payment_email = serializers.CharField(required=False, allow_null=True)
    shop_id = serializers.IntegerField(required=False, allow_null=True)
    city = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    street = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    house = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    apartment = serializers.CharField(
        max_length=100, required=False, allow_blank=True, allow_null=True
    )
    comment = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    is_callback = serializers.BooleanField(required=False, default=False)

    yandex_uid = serializers.JSONField(required=False, allow_null=True)

    def validate_email(self, value: str) -> str:
        if not is_email_valid(value):
            raise serializers.ValidationError("Invalid email address.")
        return value

    def validate_phone(self, value: str) -> str:
        if not is_phone_valid(value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value

    def validate_reception_method(self, value: str) -> str:
        if value not in Order.ReceptionMethod.values:
            raise serializers.ValidationError(
                f"Invalid reception method: {value}"
            )
        return value

    def create(self, validated_data: Any) -> Order:
        customer_session_id = validated_data["customer"]
        customer = Customer.get_customer_by_session_id(customer_session_id)

        customer_additional: FillMissingCustomerDict = {
            "first_name": cast(str, validated_data["first_name"]),
            "last_name": cast(Optional[str], validated_data.get("last_name")),
            "email": cast(Optional[str], validated_data.get("email")),
            "phone": cast(str, validated_data["phone"]),
        }

        if (
            validated_data["reception_method"]
            == Order.ReceptionMethod.DELIVERY
        ):
            customer_additional.update(
                {
                    "city": cast(Optional[str], validated_data.get("city")),
                    "street": cast(
                        Optional[str], validated_data.get("street")
                    ),
                    "house": cast(Optional[str], validated_data.get("house")),
                    "apartment": cast(
                        Optional[str], validated_data.get("apartment")
                    ),
                }
            )

        try:
            fill_missing_customer_data(customer, customer_additional)
        except (
            ObjectAlreadyExistsException,
            PhoneInvalidException,
            EmailInvalidException,
        ):
            pass

        customer_info: CustomerInfoTypedDict = {
            "session_id": customer.session_id,
            "phone": validated_data["phone"],
            "first_name": validated_data["first_name"],
            "last_name": validated_data.get("last_name"),
            "email": validated_data.get("email"),
        }

        if not customer.cart.products.exists():
            raise CustomerCartIsEmptyException()

        cart_content = CartForOrderSerializer(customer.cart).data

        order = create_new_order(
            {
                "customer": customer,
                "customer_info": customer_info,
                "content": cart_content,
                "type": "CART",
                "reception_method": validated_data["reception_method"],
                "payment_method": validated_data.get("payment_method"),
                "shop_id": validated_data.get("shop_id"),
                "city": validated_data.get("city"),
                "street": validated_data.get("street"),
                "house": validated_data.get("house"),
                "apartment": validated_data.get("apartment"),
                "comment": validated_data.get("comment"),
                "is_callback": validated_data.get("is_callback", False),
            }
        )

        # Decrease product quantities
        for cart_product in customer.cart.products:
            reduce_quantity_for_product(
                cart_product.product.id,
                amount=cart_product.quantity,
            )
            # Update product sales index
            cart_product.product.sales.index_counter_increment(
                cart_product.quantity
            )

        # Clear cart
        customer.cart.clean_cart()

        return order


class CreateNewOrderByOneClickSerializer(serializers.Serializer):
    customer = serializers.CharField(max_length=255, required=True)
    phone = serializers.CharField(max_length=20, required=True)
    product = serializers.IntegerField(required=True)
    yandex_uid = serializers.JSONField(required=False, allow_null=True)

    def validate_phone(self, value: str) -> str:
        if not is_phone_valid(value):
            raise serializers.ValidationError("Invalid phone number format.")
        return value

    def create(self, validated_data: Any) -> Order:
        customer_session_id = validated_data["customer"]
        customer = Customer.get_customer_by_session_id(customer_session_id)

        try:
            fill_missing_customer_data(
                customer, {"phone": validated_data["phone"]}
            )
        except (
            ObjectAlreadyExistsException,
            PhoneInvalidException,
        ):
            pass

        customer_info: CustomerInfoTypedDict = {
            "session_id": customer.session_id,
            "phone": validated_data["phone"],
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
        }

        product = Product.get_product_by_pk(
            validated_data["product"],
            publish=True,
            quantity__gte=1,  # >= 1
        )

        # Create a temporary cart
        temp_cart = create_cart()
        add_product_to_cart(temp_cart.id, product.id)
        cart_content = CartForOrderSerializer(temp_cart).data

        order = create_new_order(
            {
                "customer": customer,
                "customer_info": customer_info,
                "content": cart_content,
                "type": "ONE_CLICK",
                "reception_method": None,
                "payment_method": None,
                "city": None,
                "street": None,
                "house": None,
                "apartment": None,
                "shop_id": None,
                "comment": "One-click purchase",
                "is_callback": True,
            }
        )

        # Decrease product quantity
        reduce_quantity_for_product(product.id)

        # Update sales index
        product.sales.index_counter_increment()

        # Remove temporary cart
        temp_cart.delete()

        return order
