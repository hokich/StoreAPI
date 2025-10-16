from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from orders.serializers import OrderSerializer
from orders.services import send_new_order_notification_in_telegram_chat
from utils.exceptions import InvalidDataException
from utils.response_service import ResponseService

from ..models import Customer
from ..serializers.orders import (
    CreateNewOrderByOneClickSerializer,
    CreateNewOrderFromCartSerializer,
)


class CreateNewOrderViewSet(viewsets.ViewSet):
    """Endpoints to create orders from cart and via one-click flow."""

    def _get_customer_for_order(self) -> Customer:
        """Resolves the customer from session or authenticated user."""
        customer_session_id = self.request.data.get("customer")
        phone = self.request.data.get("phone")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not phone:
            raise InvalidDataException({"message": "Phone is required"})

        return Customer.get_customer_by_session_id(customer_session_id)

    @action(detail=False, methods=["post"], url_path="cart")
    def new_order_by_cart(self, request: Request) -> Response:
        """Creates an order from the customer's cart and notifies Telegram."""
        customer = self._get_customer_for_order()

        data = request.data.copy()
        data["customer"] = customer.session_id

        serializer = CreateNewOrderFromCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        # Send a Telegram notification about the new order
        added_text = ""
        if order.comment:
            added_text += f"{order.comment}"

        send_new_order_notification_in_telegram_chat(
            order, custom_text=added_text
        )

        return ResponseService.success({})

    @action(detail=False, methods=["post"], url_path="one-click")
    def new_order_by_one_click(self, request: Request) -> Response:
        """Creates an order via one-click flow and notifies Telegram."""
        customer = self._get_customer_for_order()

        data = request.data.copy()
        data["customer"] = customer.session_id

        serializer = CreateNewOrderByOneClickSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()

        # Translated bot message text
        send_new_order_notification_in_telegram_chat(
            order, custom_text="One-click purchase"
        )

        return ResponseService.success(OrderSerializer(order).data)
