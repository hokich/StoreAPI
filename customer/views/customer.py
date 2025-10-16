from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from store.models import City
from utils.exceptions import InvalidDataException
from utils.response_service import ResponseService

from ..models import Customer
from ..serializers.customer import CustomerBriefSerializer
from ..services.customer import init_customer


class CustomerViewSet(viewsets.ViewSet):
    """
    ViewSet for initializing a Customer.
    """

    @action(detail=False, methods=["get"])
    def init(self, request: Request) -> Response:
        """
        Initializes or creates a new customer.

        If the `uid` param is provided:
        - Tries to find an existing customer by `uid`.
        - If not found, creates a new one with this `uid`.

        If the `uid` param is not provided:
        - Creates a new customer.
        """
        uid = request.GET.get("uid")

        if request.user.is_authenticated:
            created = False
            customer = request.user.customer
        else:
            customer, created = init_customer(uid)

        # Сериализация и возвращение данных покупателя
        serializer = CustomerBriefSerializer(customer)
        return ResponseService.success(
            {"customer": serializer.data, "created": created}
        )

    @action(detail=False, methods=["post"], url_path="set-city")
    def set_city(self, request: Request) -> Response:
        """
        Sets the city for the current customer.

        If the `customer` param is provided:
        - Tries to find an existing customer by `customer`.
        - If the customer is not found, returns a NotFound error.

        If the `customer` param is not provided:
        - Returns an InvalidData error.
        """
        customer_session_id = request.data.get("customer")

        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if "city" not in request.data:
            raise InvalidDataException({"message": "City is required"})

        city_id = request.data.get("city")

        customer = Customer.get_customer_by_session_id(customer_session_id)
        city = None
        if city_id:
            city = City.get_city_by_pk(city_id)

        customer.set_city_obj(city)

        return ResponseService.success({})
