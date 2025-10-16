from collections import defaultdict
from typing import Any, Optional

from django.db.models import (
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.request import Request
from rest_framework.response import Response

from search.services.client import MeiliSearchClient
from utils.cache import cache_response
from utils.exceptions import InvalidDataException, PageNotFoundException
from utils.response_service import ResponseService

from ..models import (
    Brand,
    Catalog,
    Category,
    Collection,
    Listing,
    Product,
    ProductInShop,
    Selection,
    Shop,
)
from ..serializers.catalog import (
    BaseCatalogSerializer,
    CatalogForPageSerializer,
    CatalogTreeSerializer,
    CategoryCardSerializer,
    CollectionSerializer,
)
from ..serializers.product import (
    ProductCardSerializer,
    ProductOnlySlugSerializer,
    ProductShortSerializer,
)
from ..serializers.shop import ShopShortSerializer
from ..services.attribute import get_products_attributes_queryset_for_prefetch
from ..services.catalog import (
    get_favorite_brands_list,
    get_selection_categories_with_listings_json,
    get_selection_listings_with_products_json,
)
from ..services.product import (
    AvailabilityItem,
    FiltersDict,
    FiltersRangeDict,
    RangesList,
    form_filters_by_products_list,
    get_products_for_listing,
    sort_products,
)


PRODUCTS_PAGE_SIZE = 36

SECTIONS_PAGE_SIZE = 10


class CatalogTreeViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Returns the catalog tree of non-empty categories ordered by popularity."""

    serializer_class = CatalogTreeSerializer
    queryset = Catalog.get_no_empty_categories_list().order_by(
        "-popular___index"
    )

    @cache_response(prefix="catalog_tree", timeout=60 * 60 * 24)
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Lists the catalog tree."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponseService.success(serializer.data)


class FavoriteBrandsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Returns a curated list of favorite brands."""

    serializer_class = BaseCatalogSerializer
    queryset = get_favorite_brands_list()

    @cache_response(prefix="favorite_brands", timeout=60 * 60 * 24)
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Lists favorite brands."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return ResponseService.success(serializer.data)


class ProductPagination(PageNumberPagination):
    """Pagination for products with a fixed page size."""

    page_size = PRODUCTS_PAGE_SIZE
    max_page_size = PRODUCTS_PAGE_SIZE

    def paginate_queryset(self, *args: Any, **kwargs: Any) -> Any:
        """Paginates the queryset and converts 404 to a handled error."""
        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound:
            raise PageNotFoundException({"message": "Page does not exist."})


class SelectionItemsPagination(PageNumberPagination):
    """Pagination for selection/grouped items with a fixed page size."""

    page_size = SECTIONS_PAGE_SIZE
    max_page_size = SECTIONS_PAGE_SIZE

    def paginate_queryset(self, *args: Any, **kwargs: Any) -> Any:
        """Paginates the queryset and converts 404 to a handled error."""
        try:
            return super().paginate_queryset(*args, **kwargs)
        except NotFound:
            raise PageNotFoundException({"message": "Page does not exist."})


class CatalogViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """Provides catalog pages and related product listings."""

    serializer_class = CatalogForPageSerializer
    lookup_field = "slug"

    def get_object(
        self,
    ) -> Category | Listing | Collection | Brand | Selection | Catalog:
        """Resolves and returns a catalog entity by type and slug."""
        type_catalog = self.request.GET.get("type")
        slug = self.kwargs.get("slug")

        if not type_catalog:
            raise InvalidDataException({"message": "Catalog type is required"})

        if type_catalog == "category":
            return Catalog.get_object_by_kwargs(
                slug=slug, object_class__in=["category", "listing"]
            )
        elif type_catalog == "collection":
            parent_id = self.request.GET.get("parent")
            if not parent_id:
                raise InvalidDataException(
                    {"message": "Parent id is required for collection."}
                )
            return Catalog.get_object_by_kwargs(
                slug=slug, object_class="collection", parent_id=parent_id
            )
        elif type_catalog == "brand":
            return Brand.get_object_by_slug(slug)
        elif type_catalog == "selection":
            return Selection.get_object_by_slug(slug)

        raise InvalidDataException({"message": "Invalid catalog type"})

    def retrieve(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns catalog info and products count where applicable."""
        catalog = self.get_object()

        # Increment popularity index on each request
        catalog.popular.index_counter_increment()

        serializer = self.get_serializer(catalog)
        catalog_data = {
            "catalog": serializer.data,
        }
        if catalog.object_class in ["listing", "collection"]:

            query = request.GET.get("query")
            shops_ids = request.GET.getlist("shops")
            city_id = request.GET.get("city")

            products_qs = self.get_products_queryset()

            if city_id:
                # Narrow shops by city
                city_shops_qs = Shop.objects.filter(
                    city_obj__id=city_id, pickup=True
                )
                if shops_ids:
                    city_shops_qs = city_shops_qs.filter(id__in=shops_ids)

                # Subquery: product availability in selected shops
                product_stock_subquery = ProductInShop.objects.filter(
                    product=OuterRef("pk"),
                    shop__in=city_shops_qs,
                    quantity__gt=0,
                )

                # Annotate products with shop stock flag
                products_qs = products_qs.annotate(
                    has_shop_stock=Exists(product_stock_subquery)
                )

                availability_filters = request.GET.getlist("availability") or [
                    "in_stock",
                    "preorder",
                ]
                apply_availability = set(availability_filters) != {
                    "in_stock",
                    "preorder",
                    "unavailable",
                }
                if apply_availability:
                    availability_q = Q()

                    if "in_stock" in availability_filters:
                        availability_q |= Q(
                            has_shop_stock=True,
                            quantity__gte=1,  # >= 1,
                        )

                    if "preorder" in availability_filters:
                        availability_q |= Q(
                            has_shop_stock=False,
                            quantity__gte=1,  # >= 1
                        )

                    if "unavailable" in availability_filters:
                        availability_q |= Q(
                            quantity=0,
                        )

                    products_qs = products_qs.filter(availability_q)

            if query:
                ms_client = MeiliSearchClient()
                ms_products = ms_client.search_products(
                    query,
                    limit=10000,
                    attributes_to_retrieve=["id"],
                )["hits"]
                products_qs = products_qs.filter(
                    id__in=[p["id"] for p in ms_products]
                )

            if catalog.object_class == "collection":
                filters_dict = catalog.active_filters
            else:
                filters_dict = self._form_filters_dict_from_get_params(request)

            products_qs = get_products_for_listing(
                listing=(
                    catalog
                    if catalog.object_class == "listing"
                    else catalog.parent
                ),
                products_qs=products_qs,
                filters_dict=filters_dict,
            )

            catalog_data["products_count"] = products_qs.count()
        elif catalog.object_class in ["brand"]:
            catalog_data["products_count"] = (
                catalog.get_available_products_count()
            )
        elif catalog.object_class in ["selection"]:
            products = self.get_products_queryset().filter(
                quantity__gte=1, _tags=catalog  # >= 1,
            )

            catalog_data["products_count"] = products.count()
        return ResponseService.success(catalog_data)

    @action(detail=True, methods=["get"], url_path="children-categories")
    def children_categories(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns non-empty child categories for a category."""
        catalog = self.get_object()
        if catalog.object_class != "category":
            raise InvalidDataException(
                {
                    "message": "Children categories are available only for category."
                }
            )
        queryset = (
            catalog.get_no_empty_children_categories()
            .select_related("parent", "image")
            .prefetch_related("children")
        )
        serializer = CategoryCardSerializer(queryset, many=True)
        return ResponseService.success(serializer.data)

    def _form_filters_dict_from_get_params(
        self, request: Request
    ) -> FiltersDict:
        """Builds a filters dictionary from GET parameters."""
        filters_dict = FiltersDict(
            prices=[],
            tags=[],
            attributes={},
        )
        filters_dict["prices"] = [
            FiltersRangeDict(
                min=float(price_str.split("-")[0]),
                max=float(price_str.split("-")[1]),
            )
            for price_str in request.GET.getlist("price")
        ]
        filters_dict["tags"] = [tag for tag in request.GET.getlist("tag")]
        for key in request.GET.keys():
            if key in [
                "price",
                "tag",
                "listing",
                "page",
                "sort",
                "type",
                "parent",
                "query",
                "shops",
                "city",
                "availability",
            ]:
                continue
            if key.startswith("range-"):
                attribute_name = key.replace("range-", "")
                values = request.GET.getlist(key)
                ranges_list: RangesList = [
                    {
                        "min": float(value_str.split("-")[0]),
                        "max": float(value_str.split("-")[1]),
                    }
                    for value_str in values
                ]
                filters_dict["attributes"][attribute_name] = ranges_list
                continue
            query_values: list[str] = request.GET.getlist(key)
            filters_dict["attributes"][key] = query_values
        return filters_dict

    def get_products_queryset(self) -> "QuerySet[Product]":
        """Returns the base queryset for published products with prefetches."""
        return (
            Product.objects.filter(publish=True)
            .select_related("_product_page")
            .prefetch_related(
                "_images",
                "_images__thumb_image",
                "_images__sd_image",
                "_images__hd_image",
                "_tags",
                Prefetch(
                    "_product_attributes",
                    queryset=get_products_attributes_queryset_for_prefetch(),
                ),
            )
        )

    @action(detail=True, methods=["get"], url_path="additional-products")
    def additional_products(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns additional products for a listing."""
        catalog = self.get_object()
        if catalog.object_class != "listing":
            raise InvalidDataException(
                {
                    "message": "Additional products are available only for listing."
                }
            )
        serializer = ProductShortSerializer(
            catalog.additional_products, many=True
        )
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"])
    @cache_response(prefix="catalog_products", timeout=60 * 60 * 4)
    def products(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns products with filters, availability, sorting, and pagination."""
        catalog = self.get_object()
        if catalog.object_class not in ["listing", "collection"]:
            raise InvalidDataException(
                {
                    "message": "Products are available only for listing or collection."
                }
            )

        query = request.GET.get("query")
        shops_ids = request.GET.getlist("shops")
        city_id = request.GET.get("city")

        products_qs = self.get_products_queryset()

        # --- Search via Meilisearch ---
        if query:
            ms_client = MeiliSearchClient()
            ms_products = ms_client.search_products(
                query,
                limit=10000,
                attributes_to_retrieve=["id"],
            )["hits"]
            products_qs = products_qs.filter(
                id__in=[p["id"] for p in ms_products]
            )

        # --- Apply listing and filters ---
        filters_dict = self._form_filters_dict_from_get_params(request)
        listing = (
            catalog.parent if catalog.object_class == "collection" else catalog
        )
        if catalog.object_class == "collection":
            filters_dict = catalog.active_filters

        products_qs = get_products_for_listing(
            listing=listing, products_qs=products_qs
        )

        # --- Price range calculation ---
        prods_qs_with_discounted_price = products_qs.annotate(
            _discounted_price=F("price") * (100 - F("discount_percent")) / 100
        )
        min_price = int(
            prods_qs_with_discounted_price.aggregate(Min("_discounted_price"))[
                "_discounted_price__min"
            ]
            or 0
        )
        max_price = int(
            prods_qs_with_discounted_price.aggregate(Max("_discounted_price"))[
                "_discounted_price__max"
            ]
            or 0
        )
        filters_data = form_filters_by_products_list(listing, products_qs)
        filters_data["default_prices"] = FiltersRangeDict(
            min=min_price, max=max_price
        )

        # --- Re-apply filters and sorting ---
        products_qs = get_products_for_listing(
            listing=listing,
            products_qs=products_qs,
            filters_dict=filters_dict,
        )

        # --- Shop availability and availability filtering ---
        city_shops_qs: Optional[QuerySet] = None
        if city_id:
            city_shops_qs = Shop.objects.filter(
                city_obj__id=city_id, pickup=True
            )
            if shops_ids:
                city_shops_qs = city_shops_qs.filter(id__in=shops_ids)

            # Annotate availability in shops
            product_stock_subquery = ProductInShop.objects.filter(
                product=OuterRef("pk"),
                shop__in=city_shops_qs,
                quantity__gt=0,
            )
            products_qs = products_qs.annotate(
                has_shop_stock=Exists(product_stock_subquery)
            )

            availability_counts = products_qs.aggregate(
                in_stock=Count(
                    "id",
                    filter=Q(has_shop_stock=True, quantity__gte=1),
                ),
                preorder=Count(
                    "id",
                    filter=Q(has_shop_stock=False, quantity__gte=1),
                ),
                unavailable=Count("id", filter=Q(quantity=0)),
            )

            filters_data["availability"] = [
                AvailabilityItem(
                    slug="in_stock",
                    name="В наличии",
                    products_count=availability_counts["in_stock"],
                ),
                AvailabilityItem(
                    slug="preorder",
                    name="Под заказ",
                    products_count=availability_counts["preorder"],
                ),
                AvailabilityItem(
                    slug="unavailable",
                    name="Отсутствуют",
                    products_count=availability_counts["unavailable"],
                ),
            ]

            # Filter by availability
            availability_filters = request.GET.getlist("availability") or [
                "in_stock",
                "preorder",
            ]
            if set(availability_filters) != {
                "in_stock",
                "preorder",
                "unavailable",
            }:
                availability_q = Q()
                if "in_stock" in availability_filters:
                    availability_q |= Q(has_shop_stock=True, quantity__gte=1)
                if "preorder" in availability_filters:
                    availability_q |= Q(has_shop_stock=False, quantity__gte=1)
                if "unavailable" in availability_filters:
                    availability_q |= Q(quantity=0)
                products_qs = products_qs.filter(availability_q)

        products_qs = sort_products(products_qs, sort=request.GET.get("sort"))

        # --- Pagination ---
        paginator = ProductPagination()
        paginated_products = paginator.paginate_queryset(products_qs, request)

        # --- Shops for visible products ---
        product_shops_map: dict[int, list] = {}
        if city_id and city_shops_qs:
            visible_ids = [p.id for p in paginated_products]
            product_in_shop_qs = ProductInShop.objects.filter(
                product_id__in=visible_ids,
                shop__in=city_shops_qs,
                quantity__gt=0,
            ).select_related("shop__city_obj")

            product_shops_map = defaultdict(list)
            for pis in product_in_shop_qs:
                product_shops_map[pis.product_id].append(
                    ShopShortSerializer(pis.shop).data
                )

        # --- Serialization and response ---
        serialized_products = ProductCardSerializer(
            paginated_products,
            many=True,
            context={
                "request": request,
                "product_shops_map": product_shops_map,
            },
        ).data

        return ResponseService.success(
            {
                "products": {
                    "count": products_qs.count(),
                    "items": serialized_products,
                },
                "filters": filters_data,
            }
        )

    @action(detail=True, methods=["get"], url_path="all-products-for-schema")
    @cache_response(prefix="catalog_products_for_schema", timeout=60 * 60 * 4)
    def all_products_for_schema(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns a limited list of products (slugs) for structured data."""
        catalog = self.get_object()
        if catalog.object_class not in ["listing", "collection"]:
            raise InvalidDataException(
                {
                    "message": "Products are available only for listing or collection."
                }
            )

        products_qs = Product.objects.filter(publish=True).prefetch_related(
            "_tags",
        )

        listing = catalog
        if catalog.object_class == "collection":
            listing = catalog.parent
            products_qs = get_products_for_listing(
                listing=listing,
                products_qs=products_qs,
                filters_dict=catalog.active_filters,
            )
        else:
            products_qs = get_products_for_listing(
                listing=listing,
                products_qs=products_qs,
            )

        serialized_products = ProductOnlySlugSerializer(
            products_qs[:PRODUCTS_PAGE_SIZE], many=True
        ).data
        return ResponseService.success(serialized_products)

    @action(detail=True, methods=["get"])
    @method_decorator(cache_page(60 * 60 * 2))
    def collections(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns collections for a listing ordered by popularity."""
        catalog = self.get_object()
        if catalog.object_class != "listing":
            raise InvalidDataException(
                {"message": "Collections are available only for listing."}
            )
        collections_qs = catalog.children.all().order_by("-popular___index")
        serializer = CollectionSerializer(collections_qs, many=True)
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"], url_path="popular-products")
    def popular_products(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns popular products for a category."""
        catalog = self.get_object()
        if catalog.object_class != "category":
            raise InvalidDataException(
                {
                    "message": "Popular products are available only for category."
                }
            )
        products_qs = catalog.get_popular_products()
        serializer = ProductCardSerializer(products_qs, many=True)
        return ResponseService.success(serializer.data)

    @action(detail=True, methods=["get"], url_path="selection-categories")
    @cache_response(prefix="selection_products", timeout=60 * 60 * 2)
    def selection_categories(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns selection categories with listings as JSON."""
        catalog = self.get_object()
        categories_with_listings_json = (
            get_selection_categories_with_listings_json(catalog)
        )
        return ResponseService.success(categories_with_listings_json)

    @action(detail=True, methods=["get"], url_path="selection-products")
    @cache_response(prefix="selection_products", timeout=60 * 60 * 2)
    def selection_products(
        self, request: Request, slug: Optional[str] = None
    ) -> Response:
        """Returns selection listings with products and paginates the result."""
        catalog = self.get_object()
        listings_with_products_json = (
            get_selection_listings_with_products_json(catalog)
        )

        pagination = SelectionItemsPagination()
        paginated_listings = pagination.paginate_queryset(
            listings_with_products_json, request
        )

        return ResponseService.success(
            {
                "count": len(listings_with_products_json),
                "items": paginated_listings,
            }
        )
