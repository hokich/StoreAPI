from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from compare.serializers import (
    CompareProductBriefSerializer,
    CompareProductCardSerializer,
)
from compare.services import (
    add_product_to_compare,
    clear_compare,
    delete_product_from_compare,
    get_brief_compare_product,
    get_compare_products,
)
from store.models import Listing, Product
from store.serializers.attribute import ListingAttributeSerializer
from utils.exceptions import InvalidDataException
from utils.response_service import ResponseService

from ..models import Customer


class CompareViewSet(viewsets.ViewSet):
    """Compare endpoints: brief/detail lists, add/remove items, clear list."""

    @action(detail=False, methods=["get"], url_path="brief")
    def get_brief_products(self, request: Request) -> Response:
        """Returns a brief compare list for the given customer."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        products = get_brief_compare_product(customer.id)

        serializer = CompareProductBriefSerializer(products, many=True)

        return ResponseService.success(serializer.data)

    @action(detail=False, methods=["get"], url_path="detail")
    def get_detail_products(self, request: Request) -> Response:
        """Returns detailed compare items and grouped listing attributes."""
        customer_session_id = request.GET.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        customer = Customer.get_customer_by_session_id(customer_session_id)
        products = get_compare_products(customer.id)

        all_tags_ids = products.values_list(
            "product___tags", flat=True
        ).distinct()

        listings = Listing.objects.filter(
            id__in=all_tags_ids, object_class="listing"
        )

        listings_with_attributes = []
        for listing in listings:
            listing_attributes = listing.listing_attributes
            listings_with_attributes.append(
                {
                    "id": listing.id,
                    "slug": listing.slug,
                    "name": listing.name,
                    "productsCount": products.filter(
                        product___tags=listing.id
                    ).count(),
                    "attributes": ListingAttributeSerializer(
                        listing_attributes, many=True
                    ).data,
                }
            )

        products_serializer = CompareProductCardSerializer(products, many=True)

        return ResponseService.success(
            {
                "products": products_serializer.data,
                "categories": listings_with_attributes,
            }
        )

    @action(detail=False, methods=["post"], url_path="add")
    def add_product(self, request: Request) -> Response:
        """Adds a product to the customer's compare list."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        product = Product.get_product_by_pk(product_id, publish=True)

        add_product_to_compare(customer.id, product.id)
        return ResponseService.success({})

    @action(detail=False, methods=["post"], url_path="delete")
    def delete_product(self, request: Request) -> Response:
        """Removes a product from the customer's compare list."""
        customer_session_id = request.data.get("customer")
        product_id = request.data.get("product")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})
        if not product_id:
            raise InvalidDataException({"message": "Product is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)

        delete_product_from_compare(customer.id, product_id)
        return ResponseService.success({})

    @action(detail=False, methods=["post"])
    def clear(self, request: Request) -> Response:
        """Clears all compared products for the given customer."""
        customer_session_id = request.data.get("customer")
        if not customer_session_id:
            raise InvalidDataException({"message": "Customer is required"})

        customer = Customer.get_customer_by_session_id(customer_session_id)
        clear_compare(customer.id)
        return ResponseService.success({})
