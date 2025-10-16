from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from cart.serializers import (
    AddedCartProductSerializer,
    CartBriefSerializer,
    CartSerializer,
)
from cart.services import (
    add_product_to_cart,
    clear_cart,
    delete_product_from_cart,
    set_cart_product_services,
)
from store.models import Product
from store.serializers.product import ProductServiceSerializer
from utils.cache import clear_cache_by_prefix, generate_cache_key
from utils.exceptions import InvalidDataException, ProductNotInStockException
from utils.response_service import ResponseService

from ..models import Customer


class CartViewSet(viewsets.ViewSet):
    """Cart endpoints: brief/detail views, add/delete products, set services, clear cart."""

    @action(detail=False, methods=["get"], url_path="brief")
    def get_brief_cart(self, request: Request) -> Response:
        """Returns a lightweight cart representation for a customer."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        serializer = CartBriefSerializer(customer.cart)
        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail_cart(self, request: Request) -> Response:
        """Returns a detailed cart representation for a customer."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        serializer = CartSerializer(customer.cart)
        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["get"], url_path="product-services")
    def get_cart_product_active_services(self, request: Request) -> Response:
        """Returns active services for a specific product in the customer's cart."""
        customer_session_id = request.GET.get("customer")
        product_id = request.GET.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)

        cart_product = customer.cart.products.filter(product__id=product_id)

        if not cart_product.exists():
            return ResponseService.success([])
        cart_product = cart_product.first()

        serializer = ProductServiceSerializer(
            cart_product._services.all(), many=True
        )
        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["post"], url_path="add")
    def add_product(self, request: Request) -> Response:
        """Adds a product to the cart (or updates its quantity)."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        quantity = request.data.get("quantity", 1)
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})
        # Validate that quantity is a number
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise InvalidDataException(
                {"message": "Quantity must be a valid positive integer"}
            )

        customer = Customer.get_customer_by_session_id(customer_session_id)
        product = Product.get_product_by_pk(
            product_id,
            publish=True,
        )

        if not product.quantity:
            clear_cache_by_prefix(
                generate_cache_key("catalog_products", product.listing.slug)
            )
            raise ProductNotInStockException()

        added_product = add_product_to_cart(
            customer.cart.id, product.id, quantity=quantity
        )
        serializer = AddedCartProductSerializer(added_product)
        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["post"], url_path="delete")
    def delete_product(self, request: Request) -> Response:
        """Removes a product from the customer's cart."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        deleted_product_data = delete_product_from_cart(
            customer.cart.id, product_id
        )
        return ResponseService.success(deleted_product_data)

    @action(detail=False, methods=["post"], url_path="set-services")
    def set_services(self, request: Request) -> Response:
        """Sets selected service IDs for a given product in the cart."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        services_ids = request.data.get("services", [])
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)

        set_cart_product_services(customer.cart.id, product_id, services_ids)

        return ResponseService.success({})

    @action(detail=False, methods=["post"], url_path="clear")
    def clear_cart(self, request: Request) -> Response:
        """Clears the customer's cart."""
        customer_session_id = request.data.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        clear_cart(customer.cart.id)
        return ResponseService.success({})
