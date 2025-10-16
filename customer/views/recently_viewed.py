from typing import Any

from rest_framework import mixins, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from recently_viewed.serializers import RecentlyViewedProductSerializer
from recently_viewed.services import (
    create_or_update_recently_viewed,
    get_recently_viewed,
)
from utils.exceptions import InvalidDataException
from utils.response_service import ResponseService

from ..models import Customer


class RecentlyViewedViewSet(
    viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin
):
    """
    ViewSet for managing recently viewed products.
    """

    serializer_class = RecentlyViewedProductSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Add or update a product in the customer's recently viewed list.
        """
        customer_session_id = request.data.get("customer", None)
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        product_id = request.data.get("product", None)
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        create_or_update_recently_viewed(customer.id, product_id)
        return ResponseService.success({})

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Retrieve a list of recently viewed products for the customer (limited to 20).
        """
        customer_session_id = request.GET.get("customer", None)
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        products = get_recently_viewed(customer.id)[:20]
        serializer = RecentlyViewedProductSerializer(products, many=True)
        return ResponseService.success(serializer.data)
