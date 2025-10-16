from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from favorites.serializers import (
    FavoriteProductBriefSerializer,
    FavoriteProductCardSerializer,
)
from favorites.services import (
    add_product_to_favorites,
    clear_favorites,
    delete_product_from_favorites,
    get_brief_favorites_product,
    get_favorites_product,
)
from store.models import Product
from store.views.catalog import ProductPagination
from utils.exceptions import InvalidDataException
from utils.response_service import ResponseService

from ..models import Customer


class FavoritesViewSet(viewsets.ViewSet):
    """Favorites endpoints: brief/detail lists, add/remove items, clear list."""

    @action(detail=False, methods=["get"], url_path="brief")
    def get_brief_products(self, request: Request) -> Response:
        """Returns a brief favorites list for the given customer."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        products = get_brief_favorites_product(customer.id)

        serializer = FavoriteProductBriefSerializer(products, many=True)

        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail_products(self, request: Request) -> Response:
        """Returns a paginated detailed favorites list for the customer."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        products = get_favorites_product(customer.id)

        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(products, request)
        serializer = FavoriteProductCardSerializer(
            paginated_products, many=True
        )

        return ResponseService.success(
            {
                "count": products.count(),
                "items": serializer.data,
            }
        )

    @action(detail=False, methods=["post"], url_path="add")
    def add_product(self, request: Request) -> Response:
        """Adds a product to the customer's favorites."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        product = Product.get_product_by_pk(product_id, publish=True)

        add_product_to_favorites(customer.id, product.id)
        return ResponseService.success({})

    @action(detail=False, methods=["post"], url_path="delete")
    def delete_product(self, request: Request) -> Response:
        """Removes a product from the customer's favorites."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)

        delete_product_from_favorites(customer.id, product_id)
        return ResponseService.success({})

    @action(detail=False, methods=["post"])
    def clear(self, request: Request) -> Response:
        """Clears all favorite products for the given customer."""
        customer_session_id = request.data.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        clear_favorites(customer.id)
        return ResponseService.success({})
