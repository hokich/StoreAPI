from typing import Any, List, Optional, TypedDict, Union

from django.db.models import (
    Case,
    Count,
    F,
    FloatField,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Cast, Replace

from utils.exceptions import (
    ObjectAlreadyExistsException,
    ObjectDoesNotExistException,
)
from utils.text_utils import get_word_by_counter
from utils.translit import to_chpu

from ..data import product_add_services as product_services_data
from ..models import (
    Attribute,
    AttributeValue,
    Brand,
    Catalog,
    Listing,
    ListingAttribute,
    Product,
    ProductAddService,
)
from .attribute import (
    create_attribute_value,
    create_product_attribute,
    set_product_attribute_values,
)


class CreateProductDict(TypedDict, total=False):
    """Input payload for creating a product."""

    name: str
    sku: str
    price: float
    listing_id: int
    brand_id: int
    short_description: Optional[str]
    quantity: Optional[int]
    discount_percent: Optional[float]
    model: Optional[str]
    youtube_link: Optional[str]
    bonuses: Optional[bool]
    publish: Optional[bool]
    other_tags_ids: Optional[list[int]]


def create_product(product_data: CreateProductDict) -> Product:
    """Create a product from the given data."""
    slug = _get_slug_by_name(product_data["name"])

    if Product.objects.filter(sku=product_data["sku"]).exists():
        raise ObjectAlreadyExistsException(
            {
                "message": f"Product with SKU '{product_data['sku']}' already exists."
            }
        )

    # Adding mandatory tags (Listing and Brand)
    try:
        listing = Listing.objects.get(pk=product_data["listing_id"])
        brand = Brand.objects.get(pk=product_data["brand_id"])

    except Listing.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Listing with id '{product_data['listing_id']}' does not exist."
            }
        )
    except Brand.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Brand with id '{product_data['brand_id']}' does not exist."
            }
        )

    # Adding optional tags (Selection, FreeTag)
    other_tags: list[Catalog] = []
    other_tags_ids = product_data.get("other_tags_ids", [])
    if other_tags_ids:
        other_tags = Catalog.objects.filter(
            id__in=other_tags_ids, object_class__in=["selection", "freetag"]
        )
        if len(other_tags) != len(other_tags_ids):
            raise ObjectDoesNotExistException(
                {"message": "One or more other tags do not exist."}
            )
        other_tags = list(other_tags)

    product = Product.objects.create(
        slug=slug,
        name=product_data["name"],
        sku=product_data["sku"],
        short_description=product_data.get("short_description"),
        quantity=product_data.get("quantity"),
        price=product_data["price"],
        discount_percent=product_data.get("discount_percent", 0),
        model=product_data.get("model"),
        youtube_link=product_data.get("youtube_link"),
        publish=product_data.get("publish", True),
        bonuses=product_data.get("bonuses", False),
    )

    _set_brand_in_product_attribute(product, brand.name)

    product._tags.set([listing, brand] + other_tags)

    set_product_add_services(product.id)

    return product


class UpdateProductDict(TypedDict, total=True):
    """Input payload for updating a product."""

    name: str
    sku: str
    price: float
    listing_id: int
    brand_id: int
    short_description: Optional[str]
    quantity: Optional[int]
    discount_percent: Optional[float]
    model: Optional[str]
    youtube_link: Optional[str]
    bonuses: Optional[bool]
    publish: Optional[bool]
    other_tags_ids: Optional[list[int]]


def update_product(
    product_id: int, product_data: UpdateProductDict
) -> Product:
    """Update a product with the provided data."""
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        raise ObjectDoesNotExistException(
            {"message": f"Product with ID '{product_id}' does not exist."}
        )

    slug = product.slug
    if product.name != product_data["name"]:
        slug = _get_slug_by_name(product_data["name"])

    if slug != product.slug and Product.objects.filter(slug=slug).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"Product with slug '{slug}' already exists."}
        )

    if (
        product_data["sku"] != product.sku
        and Product.objects.filter(sku=product_data["sku"]).exists()
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Product with SKU '{product_data['sku']}' already exists."
            }
        )

    product.name = product_data["name"]
    product.sku = product_data["sku"]
    product.price = product_data["price"]
    product.slug = slug
    product.short_description = product_data["short_description"]
    product.quantity = product_data.get("quantity", product.quantity)
    product.discount_percent = product_data["discount_percent"]
    product.model = product_data["model"]
    product.youtube_link = product_data["youtube_link"]
    product.bonuses = product_data["bonuses"]
    product.publish = product_data["publish"]

    # Обновление обязательных тегов (Listing и Brand)
    try:
        listing = Listing.objects.get(pk=product_data["listing_id"])
        brand = Brand.objects.get(pk=product_data["brand_id"])
    except Listing.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Listing with id '{product_data['listing_id']}' does not exist."
            }
        )
    except Brand.DoesNotExist:
        raise ObjectDoesNotExistException(
            {
                "message": f"Brand with id '{product_data['brand_id']}' does not exist."
            }
        )

    _set_brand_in_product_attribute(product, brand.name)

    # Обновление опциональных тегов (Selection, FreeTag)
    other_tags = []
    if product_data["other_tags_ids"]:
        other_tags_ids = product_data["other_tags_ids"]
        other_tags = list(Catalog.objects.filter(id__in=other_tags_ids))
        if len(other_tags) != len(other_tags_ids):
            raise ObjectDoesNotExistException(
                {"message": "One or more other tags do not exist."}
            )

    product._tags.set([listing, brand] + other_tags)

    set_product_add_services(product.id)

    product.save()
    return product


def update_product_quantity(product: Product, quantity: int) -> Product:
    """Update product quantity."""
    product.quantity = quantity
    product.save()
    return product


def update_product_price(product: Product, price: float) -> Product:
    """Update product price and refresh add-on services."""
    product.price = price
    set_product_add_services(product.id)
    product.save()
    return product


def _set_brand_in_product_attribute(product: Product, brand_name: str) -> None:
    """Ensure the product has the brand attribute set."""
    brand_attr: Attribute = Attribute.get_attribute_by_slug("brend")

    brand_prod_attr = product.product_attributes.filter(
        attribute__slug="brend"
    ).first()

    if brand_prod_attr is None:
        brand_prod_attr = create_product_attribute(
            product_id=product.id, attribute_id=brand_attr.id
        )

    try:
        attr_value: AttributeValue = AttributeValue.get_value_by_value(
            brand_name
        )
    except ObjectDoesNotExistException:
        attr_value = create_attribute_value(brand_name)

    set_product_attribute_values(
        brand_prod_attr.id,
        [attr_value.id],
    )


def _get_slug_by_name(name: str) -> str:
    """Generate a unique slug based on the product name."""
    slug = to_chpu(name)
    while _check_product_exists_by_slug(slug):
        slug = to_chpu(name, last_slug=slug)
    return slug


def _check_product_exists_by_slug(slug: str) -> bool:
    """Return True if a product with the given slug exists."""
    return Product.objects.filter(slug=slug).exists()


def _set_warranty_services(product: Product) -> None:
    """Attach warranty add-on services based on listing and price."""
    if product.listing is None:
        return

    if product.listing.slug not in product_services_data.WARRANTY:
        return

    warranty_data = product_services_data.WARRANTY[product.listing.slug]
    if isinstance(warranty_data, dict):
        for years, prices in warranty_data.items():
            price = list(
                filter(
                    lambda item: item["min"] <= product.price < item["max"],
                    prices,
                )
            )
            if not price:
                continue
            price = price[0]["price"]
            if price:
                ProductAddService.objects.create(
                    product=product,
                    type=ProductAddService.ServiceType.WARRANTY,
                    name=f"Мастер-сервис на {years} {get_word_by_counter(int(years), "год", "года", "лет")}",
                    price=price,
                )


def _set_installing_services(product: Product) -> None:
    """Attach installing services based on listing and attribute values."""
    if product.listing is None:
        return

    if product.listing.slug not in product_services_data.INSTALLING:
        return

    if product.listing.slug == "televizory":
        installing_data = product_services_data.INSTALLING[
            product.listing.slug
        ]
        if not isinstance(installing_data, list):
            return
        diagonal_attr = product.product_attributes.filter(
            attribute__slug="diagonal"
        )
        if diagonal_attr.exists():
            diagonal = int(diagonal_attr.first().value.value)
            price = list(
                filter(
                    lambda item: item["min"] <= diagonal < item["max"],
                    installing_data,
                )
            )
            if price:
                price = price[0]["price"]
                if price:
                    ProductAddService.objects.create(
                        product=product,
                        type=ProductAddService.ServiceType.INSTALLING,
                        name="Старт-мастер",
                        price=price,
                    )
    elif product.listing.slug == "kondicionery":
        installing_data = product_services_data.INSTALLING[
            product.listing.slug
        ]
        if not isinstance(installing_data, list):
            return
        btu_attr = product.product_attributes.filter(
            attribute__slug="holodoproizvoditelnost"
        )
        if btu_attr:
            btu = int(btu_attr.first().value.value)
            price = list(
                filter(
                    lambda item: item["min"] <= btu <= item["max"],
                    installing_data,
                )
            )
            if price:
                price = price[0]["price"]
                if price:
                    ProductAddService.objects.create(
                        product=product,
                        type=ProductAddService.ServiceType.INSTALLING,
                        name="Старт-мастер",
                        price=price,
                    )
    else:
        ProductAddService.objects.create(
            product=product,
            type=ProductAddService.ServiceType.INSTALLING,
            name="Старт-мастер",
            price=product_services_data.INSTALLING[product.listing.slug],
        )


def _set_setting_up_services(product: Product) -> None:
    """Attach setting-up services based on listing."""
    if product.listing is None:
        return

    if product.listing.slug not in product_services_data.SETTING_UP:
        return

    for tariff, price in product_services_data.SETTING_UP[
        product.listing.slug
    ].items():
        if price:
            ProductAddService.objects.create(
                product=product,
                type=ProductAddService.ServiceType.SETTING_UP,
                name=f"Фокс-мастер {tariff}",
                price=price,
            )


def set_product_add_services(product_id: int) -> None:
    """Rebuild all add-on services for the product."""
    product = Product.get_product_by_pk(product_id)
    # Удаляем все услуги с товара
    product.services.delete()
    # Гарантия
    _set_warranty_services(product)

    # Установка
    _set_installing_services(product)

    # Настройка
    _set_setting_up_services(product)


class FiltersRangeDict(TypedDict):
    """Numeric range used in filters."""

    min: float
    max: float


StringValuesList = List[str]

RangesList = List[FiltersRangeDict]

AttributesFiltersDict = dict[str, Union[StringValuesList, RangesList]]


class FiltersDict(TypedDict, total=False):
    """Composite filters payload (prices, tags, attributes)."""

    prices: RangesList
    tags: StringValuesList
    attributes: AttributesFiltersDict


def get_products_for_listing(
    listing: Listing,
    products_qs: QuerySet[Product],
    filters_dict: Optional[FiltersDict] = None,
) -> QuerySet[Product]:
    """Return products for a listing with optional filters applied."""
    if filters_dict:
        return get_products_by_filter(
            products_qs,
            listing=listing,
            tags_slugs=filters_dict.get("tags"),
            prices=filters_dict.get("prices"),
            attributes=filters_dict.get("attributes"),
        )
    else:
        return get_products_by_filter(
            products_qs,
            listing=listing,
        )


# TODO: Метод работает медленно, нужно оптимизировать
def get_products_by_filter(
    products: QuerySet[Product],
    listing: Catalog,
    tags_slugs: Optional[StringValuesList] = None,
    prices: Optional[RangesList] = None,
    attributes: Optional[AttributesFiltersDict] = None,
) -> QuerySet[Product]:
    """Return products filtered by tags, price ranges, and attributes."""

    products = products.filter(_tags=listing)

    qs_tags = Q()

    if tags_slugs:
        qs_filter_tags = Q()
        for tag_slug in tags_slugs:
            qs_filter_tags |= Q(_tags__slug=tag_slug)
        qs_tags = qs_filter_tags

    products = products.filter(qs_tags)

    if prices:
        qs_price = Q()
        for range_value in prices:
            qs_price |= Q(
                _discounted_price__gte=range_value["min"],
                _discounted_price__lte=range_value["max"],
            )
        products = products.annotate(
            _discounted_price=F("price") * (100 - F("discount_percent")) / 100
        ).filter(qs_price)

    if not attributes:
        products_ids = list(products.values_list("id", flat=True))
        return products.filter(id__in=products_ids).distinct()

    all_attributes_slugs = list(attributes.keys()) if attributes else []
    attributes_obj = Attribute.objects.filter(slug__in=all_attributes_slugs)
    all_attributes_dict = {a.slug: a for a in attributes_obj}

    existing_la_qs = ListingAttribute.objects.filter(
        listing=listing, attribute__in=attributes_obj
    ).select_related("attribute", "popular")
    la_by_attr_id = {la.attribute_id: la for la in existing_la_qs}

    for attribute_slug, values in attributes.items():
        attribute = all_attributes_dict[attribute_slug]

        # Инкремент индекса популярности атрибута листинга
        listing_attribute = la_by_attr_id[attribute.id]
        listing_attribute.popular.index_counter_increment()

        qs_values = Q()
        for value in values:

            if attribute.type == "NUM_RANGE" and isinstance(value, dict):
                qs_values |= Q(
                    _attributes=attribute,
                    numeric_value__gte=value["min"],
                    numeric_value__lte=value["max"],
                )
            else:
                qs_values |= Q(
                    _attributes=attribute,
                    _product_attributes___values__slug=value,
                )

        products_for_filter = products
        if attribute.type == "NUM_RANGE":
            products_for_filter = products.annotate(
                numeric_value=Case(
                    When(
                        _product_attributes__attribute=attribute,
                        _product_attributes___values__value__regex=r"^\d+(\.\d+)?$",
                        then=Cast(
                            Replace(
                                Replace(
                                    Replace(
                                        "_product_attributes___values__value",
                                        Value(","),
                                        Value("."),
                                    ),
                                    Value(" "),
                                    Value(""),
                                ),
                                Value("[^0-9.]"),
                                Value(""),
                            ),
                            FloatField(),
                        ),
                    ),
                    default=Value(None),
                    output_field=FloatField(),
                )
            )

        products_ids = list(
            products_for_filter.filter(qs_values).values_list("id", flat=True)
        )
        products = products.filter(id__in=products_ids)
    return products.distinct()


def sort_products(
    products: QuerySet[Product],
    sort: Optional[str] = None,
) -> QuerySet[Product]:
    """Sort products by price, discount, or popular status."""
    if sort:
        if sort in ["cheap", "expensive"]:
            products = products.annotate(
                discount_price=F("price") * (100 - F("discount_percent")) / 100
            )
            sort_by = (
                "-discount_price" if sort == "expensive" else "discount_price"
            )
            products = products.order_by("status_order", sort_by)
        elif sort == "discount":
            products = products.order_by(
                "status_order",
                "-discount_percent",
                "-popular___index",
                "-created_at",
            )

    return products


class AvailabilityItem(TypedDict, total=True):
    """Availability bucket with product count."""

    slug: str
    name: str
    products_count: int


class ProductsFiltersDict(TypedDict, total=True):
    """Computed filters metadata for UI."""

    attributes: List[dict[str, Any]]
    tags: List[dict[str, Any]]
    default_prices: FiltersRangeDict
    availability: Optional[list[AvailabilityItem]]


def form_filters_by_products_list(
    listing: Listing, products_list: QuerySet[Product]
) -> ProductsFiltersDict:
    """Build filters data for a listing based on the given products."""
    filters: ProductsFiltersDict = ProductsFiltersDict(
        attributes=[],
        tags=[],
        default_prices={
            "min": 0,
            "max": 0,
        },
        availability=[],
    )
    for listing_attr in listing.listing_attributes:
        attribute_dict: dict[str, Any] = {
            "attribute": {
                "id": listing_attr.attribute.pk,
                "group": listing_attr.attribute.group.name,
                "name": listing_attr.attribute.name,
                "slug": listing_attr.attribute.slug,
                "type": listing_attr.attribute.type,
                "measure_unit": listing_attr.attribute.measure_unit,
            },
            "possible_values": [],
            "empty": False,
        }

        aggregated_counts = (
            products_list.filter(_attributes=listing_attr.attribute)
            .values("_product_attributes___values")
            .annotate(product_count=Count("id"))
            .order_by()
        )

        counts_dict = {
            item["_product_attributes___values"]: item["product_count"]
            for item in aggregated_counts
        }

        not_empty_values = []
        for attribute_value in listing_attr._possible_values.all():
            products_count = counts_dict.get(attribute_value.pk, 0)

            value_dict = {
                "id": attribute_value.pk,
                "value": attribute_value.value,
                "slug": attribute_value.slug,
                "products_count": products_count,
            }

            attribute_dict["possible_values"].append(value_dict)

            if products_count != 0:
                not_empty_values.append(value_dict)
        attribute_dict["possible_values"].sort(
            key=lambda value: value["products_count"], reverse=True
        )
        if not not_empty_values:
            attribute_dict["empty"] = True
        filters["attributes"].append(attribute_dict)

    tags = Catalog.objects.filter(
        slug__in=["tovar-iz-gazety", "akcionnye-tovary"]
    )
    for tag in tags:
        filters["tags"].append(
            {
                "id": tag.id,
                "slug": tag.slug,
                "name": tag.name,
                "products_count": products_list.filter(_tags=tag).count(),
            }
        )
    return filters


def reduce_quantity_for_product(product_id: int, amount: int = 1) -> None:
    """Decrease product quantity safely (not below zero)."""
    product = Product.get_product_by_pk(product_id)

    # Обновляем количество продукта, не позволяя ему быть меньше нуля
    product.quantity = max(product.quantity - amount, 0)

    product.save()


def update_products_popularity_indexes() -> None:
    """Recalculate popularity indexes for all published products."""
    products = Product.objects.filter(publish=True)
    for product in products:
        product.popular.update_index()


def update_products_search_often_indexes() -> None:
    """Recalculate 'search often' indexes for all published products."""
    products = Product.objects.filter(publish=True)
    for product in products:
        product.often_search.update_index()
