from collections import Counter
from typing import Optional, TypedDict

from cachetools import TTLCache, cached
from django.core.files import File
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.db.models import F, Prefetch, QuerySet

from images.services import create_image
from utils.exceptions import (
    InvalidDataException,
    ObjectAlreadyExistsException,
    ParentCatalogIsNotCategoryException,
    ParentCatalogIsNotListingException,
)
from utils.translit import to_chpu

from ..models import (
    Brand,
    Catalog,
    Category,
    Collection,
    FreeTag,
    Listing,
    Product,
    Selection,
)
from ..serializers.catalog import CatalogBriefSerializer, CatalogTreeSerializer
from ..serializers.product import ProductCardSerializer
from .attribute import get_products_attributes_queryset_for_prefetch


FAVORITE_BRANDS_NAMES = [
    "RED SOLUTION",
    "WESTBURG",
    "Realme",
    "Lenovo",
    "HP",
    "JBL",
    "Sony",
    "Panasonic",
    "Sennheiser",
    "NORD",
    "Acer",
    "Asus",
    "AOC",
    "LG",
    "Razer",
    "Kingston",
    "Samsung",
    "Philips",
    "Bosch",
    "BQ",
    "Canyon",
    "Defender",
    "Gorenje",
    "Hotpoint",
    "Logitech",
    "SVEN",
    "TP-Link",
    "Tefal",
    "Xiaomi",
    "Vitek",
    "Apple",
]


def get_favorite_brands_list() -> QuerySet[Category]:
    """Return a queryset of favorite brands with related image preloaded."""
    return Brand.objects.filter(
        object_class="brand", name__in=FAVORITE_BRANDS_NAMES
    ).select_related("image")


def get_selection_categories_with_listings_json(
    catalog: "Catalog",
) -> dict:
    """Return a dict grouping listings by top-level category with product counts for a selection/brand."""
    if catalog.object_class not in ["selection", "brand"]:
        raise InvalidDataException(
            {
                "message": f"Object class '{catalog.object_class}' is not supported. Supported classes: 'selection', 'brand'."
            }
        )

    categories_json: dict = {}

    products = Product.objects.filter(
        publish=True,
        quantity__gte=1,  # >= 1
    )

    products = products.filter(_tags=catalog)

    products_ids = products.values_list("id", flat=True)

    categories_with_counts = Product.objects.filter(
        pk__in=products_ids
    ).values("_tags")

    count_dict: Counter = Counter()
    for category in categories_with_counts:
        count_dict[category["_tags"]] += 1

    listings = Product.get_categories_by_products(products).select_related(
        "parent"
    )

    for listing in listings:

        listing_json = {
            "listing": CatalogBriefSerializer(listing).data,
            "products_count": count_dict.get(listing.id, 0),
        }

        listing_catalogs_chain = listing.get_catalogs_chain()

        parent_category_name = (
            listing_catalogs_chain[0].name if listing_catalogs_chain else None
        )

        if parent_category_name:
            if parent_category_name in categories_json:
                categories_json[parent_category_name].append(listing_json)
            else:
                categories_json[parent_category_name] = [listing_json]

    return categories_json


SELECTION_DISPLAY_CATEGORIES = [
    "televizory",
    "noutbuki",
    "stiralnye-mashiny",
    "smartfony",
    "holodilniki",
    "morozilnye-lari",
    "morozilnye-kamery",
    "planshety",
    "gazovye-plity",
    "ehlektricheskie-plity",
    "kombinirovannye-plity",
    "vstraivaemye-duhovye-shkafy",
    "vstraivaemye-paneli",
    "vytyazhki",
    "posudomoechnye-mashiny",
    "mikrovolnovye-pechi",
    "multivarki",
    "ehlektropechi",
    "kuhonnye-kombajny",
    "myasorubki",
    "ehlektrochajniki",
    "akusticheskie-sistemy",
    "printery-i-mfu",
    "pylesosy",
    "kofemashiny",
    "kofevarki",
    "utyugi",
    "blendery",
    "feny",
    "ehlektrobritvy",
]


def get_selection_listings_with_products_json(
    catalog: "Catalog",
) -> list:
    """Return a list of listings each with up to 9 products and total count for a selection/brand."""
    if catalog.object_class not in ["selection", "brand"]:
        raise InvalidDataException(
            {
                "message": f"Object class '{catalog.object_class}' is not supported. Supported classes: 'selection', 'brand'."
            }
        )

    products = Product.objects.filter(
        publish=True,
        quantity__gte=1,  # >= 1
    )

    # TODO: Костыль для вывода товаров с тегом "Из газеты" на странице Акции
    if catalog.slug == "akcionnye-tovary":
        tovar_is_gazeti = FreeTag.get_object_by_slug("tovar-iz-gazety")
        products = products.filter(
            _tags__in=[catalog, tovar_is_gazeti],
        )
    else:
        products = products.filter(_tags=catalog)

    products_ids = products.values_list("id", flat=True)

    products = Product.objects.prefetch_related(
        "_images",
        "_images__thumb_image",
        "_images__sd_image",
        "_images__hd_image",
        "_tags",
        Prefetch(
            "_product_attributes",
            queryset=get_products_attributes_queryset_for_prefetch(),
        ),
    ).filter(id__in=products_ids)
    all_listings = Product.get_categories_by_products(products)
    listings_only_display_categories = all_listings.filter(
        slug__in=SELECTION_DISPLAY_CATEGORIES
    )
    listings = (
        listings_only_display_categories
        if listings_only_display_categories.exists()
        else all_listings
    )
    product_category_mappings = products.values("id", tag_id=F("_tags__id"))

    category_to_products: dict = {}
    for mapping in product_category_mappings:
        product_id = mapping["id"]
        category_id = mapping["tag_id"]
        category_to_products.setdefault(category_id, []).append(product_id)

    products_dict = products.in_bulk()

    products_groups_list = []
    for listing in listings:
        product_ids_for_category = category_to_products.get(listing.id, [])
        filtered_products = [
            products_dict[pid] for pid in product_ids_for_category
        ]

        products_groups_list.append(
            {
                "listing": CatalogBriefSerializer(listing).data,
                "products": ProductCardSerializer(
                    filtered_products[:9], many=True
                ).data,
                "products_count": len(filtered_products),
            }
        )
    return products_groups_list


@transaction.atomic
def apply_additional_products(
    category_id: int,
    additional_product_ids: list[int],
    remove: bool = False,
) -> None:
    """Add or remove a set of additional products to all products in the given listing."""
    if not additional_product_ids:
        return

    listing = Listing.get_object_by_pk(category_id)

    additional_products = Product.objects.filter(id__in=additional_product_ids)
    if not additional_products.exists():
        return

    listing_products = Product.objects.filter(
        _tags=listing, publish=True
    ).prefetch_related("_additional_products")

    for product in listing_products:
        if remove:
            product._additional_products.remove(*additional_products)
        else:
            to_add = [p for p in additional_products if p.id != product.id]
            product._additional_products.add(*to_add)


def _get_slug_by_name(
    name: str,
    parent_id: Optional[int] = None,
    object_classes_list: Optional[list[str]] = None,
) -> str:
    """Generate a unique slug for a catalog object based on its name and parent."""
    slug = to_chpu(name)
    while _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, object_classes_list
    ):
        slug = to_chpu(name, last_slug=slug)
    return slug


def _check_catalog_exists_by_slug_and_parent(
    slug: str,
    parent_id: Optional[int] = None,
    object_classes_list: Optional[list[str]] = None,
) -> bool:
    """Return True if a catalog object exists with the given slug/parent (optionally limited by classes)."""
    catalogs = Catalog.objects.filter(slug=slug, parent__id=parent_id)
    if object_classes_list:
        catalogs = catalogs.filter(object_class__in=object_classes_list)
    return catalogs.exists()


def create_category(
    name: str,
    slug: Optional[str] = None,
    parent_id: Optional[int] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
) -> Category:
    """Create a category with the specified parameters."""
    parent: Optional[Catalog] = None
    if parent_id is not None:
        parent = Catalog.get_object_by_pk(parent_id)

    if parent and parent.object_class != "category":
        raise ParentCatalogIsNotCategoryException()

    if slug is None:
        slug = _get_slug_by_name(name, parent_id, ["category", "listing"])

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["category", "listing"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Category or Listing with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    category = Category.objects.create(
        slug=slug,
        name=name,
        parent=parent,
        short_name=short_name,
        color=color,
        icon=icon,
    )

    return category


class UpdateCategoryDict(TypedDict, total=True):
    """Payload for updating a category."""

    name: str
    slug: Optional[str]
    parent_id: Optional[int]
    short_name: Optional[str]
    color: Optional[str]
    icon: Optional[str]


def update_category(
    category_id: int,
    category_data: UpdateCategoryDict,
) -> Category:
    """Update a category by ID with the provided data."""
    category = Category.get_object_by_pk(category_id)

    parent_id = category_data["parent_id"]
    if parent_id is not None:
        parent = Catalog.get_object_by_pk(parent_id)
        if parent.object_class != "category":
            raise ParentCatalogIsNotCategoryException()
        category.parent = parent
    else:
        category.parent = None

    slug = category_data["slug"]
    if slug is None:
        slug = _get_slug_by_name(
            category_data["name"],
            parent_id,
            ["category", "listing"],
        )

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["category", "listing"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Category or Listing with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    category.name = category_data["name"]
    category.slug = slug
    category.short_name = category_data["short_name"]
    category.color = category_data["color"]
    category.icon = category_data["icon"]

    category.save()

    return category


def set_category_background_image(
    category_id: int, background_file: Optional[UploadedFile | File] = None
) -> Category:
    """Set or remove a category background image."""
    category = Category.get_object_by_pk(category_id)

    if background_file is None:
        if category.background:
            category.background.delete()
        category.background = None
        category.save()
        return category

    if category.background:
        category.background.delete()

    background_image = create_image(
        name=f"{category.slug}_background",
        object_type="category",
        image_file=background_file,
        max_width=1920,
        max_height=1080,
    )

    category.background = background_image
    category.save()

    return category


def set_category_image(
    category_id: int, image_file: Optional[UploadedFile | File] = None
) -> Category:
    """Set or remove a category image."""
    category = Category.get_object_by_pk(category_id)

    if image_file is None:
        if category.image:
            category.image.delete()
        category.image = None
        category.save()
        return category

    if category.image:
        category.image.delete()

    category_image = create_image(
        name=f"{category.slug}_image",
        object_type="category",
        image_file=image_file,
        max_width=768,
        max_height=768,
        alt_text=category.name,
    )

    category.image = category_image
    category.save()

    return category


def create_listing(
    name: str,
    slug: Optional[str] = None,
    parent_id: Optional[int] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
) -> Listing:
    """Create a listing with the specified parameters."""
    parent: Optional[Catalog] = None
    if parent_id is not None:
        parent = Catalog.get_object_by_pk(parent_id)

    if parent and parent.object_class != "category":
        raise ParentCatalogIsNotCategoryException()

    if slug is None:
        slug = _get_slug_by_name(name, parent_id, ["category", "listing"])

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["category", "listing"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Category or Listing with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    listing = Listing.objects.create(
        slug=slug,
        name=name,
        parent=parent,
        short_name=short_name,
        color=color,
        icon=icon,
    )

    return listing


class UpdateListingDict(TypedDict, total=True):
    """Payload for updating a listing."""

    name: str
    slug: Optional[str]
    parent_id: Optional[int]
    short_name: Optional[str]
    color: Optional[str]
    icon: Optional[str]


def update_listing(
    listing_id: int,
    listing_data: UpdateListingDict,
) -> Listing:
    """Update a listing by ID with the provided data."""
    listing = Listing.get_object_by_pk(listing_id)

    parent_id = listing_data["parent_id"]
    if parent_id is not None:
        parent = Catalog.get_object_by_pk(parent_id)
        if parent.object_class != "category":
            raise ParentCatalogIsNotCategoryException()
        listing.parent = parent
    else:
        listing.parent = None

    slug = listing_data["slug"]
    if slug is None:
        slug = _get_slug_by_name(
            listing_data["name"],
            parent_id,
            ["category", "listing"],
        )

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["category", "listing"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Category or Listing with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    listing.name = listing_data["name"]
    listing.slug = slug
    listing.short_name = listing_data["short_name"]
    listing.color = listing_data["color"]
    listing.icon = listing_data["icon"]

    listing.save()

    return listing


def set_listing_image(
    listing_id: int, image_file: Optional[UploadedFile] = None
) -> Listing:
    """Set or remove a listing image."""
    listing = Listing.get_object_by_pk(listing_id)

    if image_file is None:
        if listing.image:
            listing.image.delete()
        listing.image = None
        listing.save()
        return listing

    if listing.image:
        listing.image.delete()

    listing_image = create_image(
        name=f"{listing.slug}_image",
        object_type="listing",
        image_file=image_file,
        max_width=768,
        max_height=768,
        alt_text=listing.name,
    )

    listing.image = listing_image
    listing.save()

    return listing


def set_listing_background_image(
    listing_id: int, image_file: Optional[UploadedFile] = None
) -> Listing:
    """Set or remove a listing background image."""
    listing = Listing.get_object_by_pk(listing_id)

    if image_file is None:
        if listing.background:
            listing.background.delete()
        listing.background = None
        listing.save()
        return listing

    if listing.background:
        listing.background.delete()

    listing_background_image = create_image(
        name=f"{listing.slug}_background",
        object_type="listing",
        image_file=image_file,
        max_width=1920,
        max_height=1080,
    )

    listing.background = listing_background_image
    listing.save()

    return listing


def create_collection(
    name: str,
    parent_id: int,
    slug: Optional[str] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
    active_filters: Optional[dict] = None,
) -> Collection:
    """Create a collection under a listing with optional filters."""
    parent = Catalog.get_object_by_pk(parent_id)

    if parent.object_class != "listing":
        raise ParentCatalogIsNotListingException()

    if slug is None:
        slug = _get_slug_by_name(name, parent_id, ["collection"])

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["collection"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Collection with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    collection = Collection.objects.create(
        slug=slug,
        name=name,
        parent=parent,
        short_name=short_name,
        color=color,
        active_filters=active_filters,
    )

    return collection


class UpdateCollectionDict(TypedDict, total=True):
    """Payload for updating a collection."""

    name: str
    parent_id: int
    slug: Optional[str]
    short_name: Optional[str]
    color: Optional[str]
    active_filters: Optional[dict]


def update_collection(
    collection_id: int,
    collection_data: UpdateCollectionDict,
) -> Collection:
    """Update a collection by ID with new parent and properties."""
    collection = Collection.get_object_by_pk(collection_id)

    parent_id = collection_data["parent_id"]
    parent = Catalog.get_object_by_pk(parent_id)

    if parent.object_class != "listing":
        raise ParentCatalogIsNotListingException()

    slug = collection_data["slug"]
    if slug is None:
        slug = _get_slug_by_name(
            collection_data["name"],
            parent_id,
            ["collection"],
        )

    if _check_catalog_exists_by_slug_and_parent(
        slug, parent_id, ["collection"]
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Collection with slug '{slug}' and parent_id '{parent_id}' already exists."
            }
        )

    collection.parent = parent
    collection.name = collection_data["name"]
    collection.slug = slug
    collection.short_name = collection_data["short_name"]
    collection.color = collection_data["color"]
    collection.active_filters = collection_data["active_filters"]

    return collection


def create_brand(
    name: str,
    slug: Optional[str] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
) -> Brand:
    """Create a brand with the specified parameters."""
    if slug is None:
        slug = _get_slug_by_name(name, None, ["brand"])

    if _check_catalog_exists_by_slug_and_parent(slug, None, ["brand"]):
        raise ObjectAlreadyExistsException(
            {"message": f"Brand with slug '{slug}' already exists."}
        )

    brand = Brand.objects.create(
        slug=slug,
        name=name,
        short_name=short_name,
        color=color,
    )

    return brand


class UpdateBrandDict(TypedDict, total=True):
    """Payload for updating a brand."""

    name: str
    slug: Optional[str]
    short_name: Optional[str]
    color: Optional[str]


def update_brand(
    brand_id: int,
    brand_data: UpdateBrandDict,
) -> Brand:
    """Update a brand by ID with the provided data."""
    brand = Brand.get_object_by_pk(brand_id)

    slug = brand.slug
    if brand.name != brand_data["name"]:
        slug = _get_slug_by_name(brand_data["name"])

    if slug != brand.slug and _check_catalog_exists_by_slug_and_parent(
        slug, None, ["brand"]
    ):
        raise ObjectAlreadyExistsException(
            {"message": f"Brand with slug '{slug}' already exists."}
        )

    brand.name = brand_data["name"]
    brand.slug = slug
    brand.short_name = brand_data["short_name"]
    brand.color = brand_data["color"]

    brand.save()

    return brand


def set_brand_image(
    brand_id: int, image_file: Optional[UploadedFile] = None
) -> Brand:
    """Set or remove a brand image."""
    brand = Brand.get_object_by_pk(brand_id)

    if image_file is None:
        if brand.image:
            brand.image.delete()
        brand.image = None
        brand.save()
        return brand

    if brand.image:
        brand.image.delete()

    if image_file is not None:
        brand_image = create_image(
            name=f"{brand.slug}_image",
            object_type="brand",
            image_file=image_file,
            max_width=768,
            max_height=768,
            alt_text=brand.name,
        )
    else:
        brand_image = None
        if brand.image:
            brand.image.delete()

    brand.image = brand_image
    brand.save()

    return brand


def create_selection(
    name: str,
    slug: Optional[str] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
) -> "Catalog":
    """Create a selection with the specified parameters."""
    if slug is None:
        slug = _get_slug_by_name(name, None, ["selection"])

    if _check_catalog_exists_by_slug_and_parent(slug, None, ["selection"]):
        raise ObjectAlreadyExistsException(
            {"message": f"Selection with slug '{slug}' already exists."}
        )

    selection = Selection.objects.create(
        slug=slug,
        name=name,
        short_name=short_name,
        color=color,
    )

    return selection


class UpdateSelectionDict(TypedDict, total=True):
    """Payload for updating a selection."""

    name: str
    slug: Optional[str]
    short_name: Optional[str]
    color: Optional[str]


def update_selection(
    selection_id: int,
    selection_data: UpdateSelectionDict,
) -> "Catalog":
    """Update a selection by ID with the provided data."""
    selection = Selection.get_object_by_pk(selection_id)

    slug = selection_data["slug"]
    if slug is None:
        slug = _get_slug_by_name(
            selection_data["name"],
            None,
            ["selection"],
        )

    if _check_catalog_exists_by_slug_and_parent(slug, None, ["selection"]):
        raise ObjectAlreadyExistsException(
            {"message": f"Selection with slug '{slug}' already exists."}
        )

    selection.name = selection_data["name"]
    selection.slug = slug
    selection.short_name = selection_data["short_name"]
    selection.color = selection_data["color"]

    selection.save()

    return selection


def create_free_tag(
    name: str,
    slug: Optional[str] = None,
    short_name: Optional[str] = None,
    color: Optional[str] = None,
) -> FreeTag:
    """Create a free tag with the specified parameters."""
    if slug is None:
        slug = _get_slug_by_name(name, None, ["freetag"])

    if _check_catalog_exists_by_slug_and_parent(slug, None, ["freetag"]):
        raise ObjectAlreadyExistsException(
            {"message": f"FreeTag with slug '{slug}' already exists."}
        )

    free_tag = FreeTag.objects.create(
        slug=slug,
        name=name,
        short_name=short_name,
        color=color,
    )

    return free_tag


class UpdateFreeTagDict(TypedDict, total=True):
    """Payload for updating a free tag."""

    name: str
    slug: Optional[str]
    short_name: Optional[str]
    color: Optional[str]


def update_free_tag(
    free_tag_id: int,
    free_tag_data: UpdateFreeTagDict,
) -> FreeTag:
    """Update a free tag by ID with the provided data."""
    free_tag = FreeTag.get_object_by_pk(free_tag_id)

    slug = free_tag_data["slug"]
    if slug is None:
        slug = _get_slug_by_name(
            free_tag_data["name"],
            None,
            ["freetag"],
        )

    if _check_catalog_exists_by_slug_and_parent(slug, None, ["freetag"]):
        raise ObjectAlreadyExistsException(
            {"message": f"FreeTag with slug '{slug}' already exists."}
        )

    free_tag.name = free_tag_data["name"]
    free_tag.slug = slug
    free_tag.short_name = free_tag_data["short_name"]
    free_tag.color = free_tag_data["color"]

    free_tag.save()

    return free_tag


@cached(cache=TTLCache(maxsize=1, ttl=60 * 60 * 4))
def get_catalog_tree() -> list:
    """Return a cached tree of non-empty categories for navigation."""
    return CatalogTreeSerializer(
        Catalog.get_no_empty_categories_list(), many=True
    ).data


def update_catalogs_popularity_indexes() -> None:
    """Recalculate and update popularity indexes for all catalogs."""
    catalogs = Catalog.objects.all()
    for catalog in catalogs:
        catalog.popular.update_index()
