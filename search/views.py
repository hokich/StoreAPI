from typing import Any

from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from store.models import Product
from store.serializers.product import ProductShortCardSerializer
from utils.exceptions import InvalidDataException, PageNotFoundException
from utils.response_service import ResponseService

from .serializers import SearchQuerySerializer
from .services.search_query import (
    create_or_increment_search_query,
    get_hints_by_query,
    get_search_queries,
    search_for_page,
    search_products_and_catalogs,
)
from .services.utils import convert_layout_mixed


class ProductsForYouView(APIView):
    """Returns a list of recommended products for the user (currently empty)."""

    def get(self, request: Request) -> Response:
        return ResponseService.success([])


class OftenSearchedProductsView(APIView):
    """Handles requests for frequently searched products."""

    def get(self, request: Request) -> Response:
        """Returns top 20 most frequently searched products."""
        products = (
            Product.objects.prefetch_related(
                "_images",
                "_images__thumb_image",
                "_images__sd_image",
                "_images__hd_image",
            )
            .filter(publish=True, quantity__gte=1)
            .exclude(often_search___index=0)
            .order_by("-often_search___index")[:20]
        )
        return ResponseService.success(
            ProductShortCardSerializer(products, many=True).data
        )

    def post(self, request: Request) -> Response:
        """Increments the search frequency counter for a specific product."""
        product_id = request.data.get("id")

        if not product_id:
            raise InvalidDataException({"message": "Id is required"})

        product = Product.get_product_by_pk(product_id)
        product.often_search.index_counter_increment()
        return ResponseService.success({})


class SearchView(APIView):
    """Handles basic search for products and catalogs."""

    def get(self, request: Request) -> Response:
        """Performs search by query text."""
        query = request.GET.get("query")
        if not query:
            raise InvalidDataException({"message": "Query is required"})

        products, catalogs = search_products_and_catalogs(query)
        return ResponseService.success(
            {"products": products, "catalogs": catalogs}
        )


SEARCH_SECTIONS_PAGE_SIZE = 10


class SearchSectionsPagination(PageNumberPagination):
    """Pagination for search sections."""

    page_size = SEARCH_SECTIONS_PAGE_SIZE
    max_page_size = SEARCH_SECTIONS_PAGE_SIZE

    def paginate_queryset(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound:
            raise PageNotFoundException({"message": "Page does not exist."})


class SearchPageView(APIView):
    """Provides paginated search results with listings and categories."""

    def get(self, request: Request) -> Response:
        """Returns paginated search results for listings and categories."""
        query = request.GET.get("query")
        if not query:
            raise InvalidDataException({"message": "Query is required"})

        listings, categories, count = search_for_page(query)

        pagination = SearchSectionsPagination()
        paginated_listings = pagination.paginate_queryset(listings, request)

        return ResponseService.success(
            {
                "listings_with_products": {
                    "count": len(listings),
                    "items": paginated_listings,
                },
                "categories_with_listings": categories,
                "total_count": count,
            }
        )


class SearchQueriesView(APIView):
    """Manages popular and moderated search queries."""

    def get(self, request: Request) -> Response:
        """Returns top 4 most popular moderated search queries."""
        queryset = get_search_queries(
            is_publish=True, is_moderation=True
        ).exclude(popular___index=0)
        queries = queryset.order_by("-popular___index")[:4]
        serializer = SearchQuerySerializer(queries, many=True)
        return ResponseService.success(serializer.data)

    def post(self, request: Request) -> Response:
        """Creates a new search query or increments its usage counter."""
        query_text = request.data.get("text")
        if not query_text:
            raise InvalidDataException({"message": "Text is required"})
        create_or_increment_search_query(query_text)
        return ResponseService.success({})


class SearchHintsView(APIView):
    """Provides autocomplete and hint suggestions for search queries."""

    def get(self, request: Request) -> Response:
        """Returns hints and suggestions for the entered search text."""
        query = request.GET.get("query")
        if not query:
            raise InvalidDataException({"message": "Query is required"})

        query = query.lower()
        result = get_hints_by_query(query)

        if not result["queries"] and not result["words"]:
            query = convert_layout_mixed(query)
            result = get_hints_by_query(query)

        return ResponseService.success(result)
