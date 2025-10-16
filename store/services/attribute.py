from typing import Optional, TypedDict

from django.db import IntegrityError
from django.db.models import Prefetch, QuerySet

from utils.exceptions import (
    ObjectAlreadyExistsException,
    ObjectDoesNotExistException,
)
from utils.translit import to_chpu

from ..models import (
    Attribute,
    AttributeGroup,
    AttributeValue,
    Listing,
    ListingAttribute,
    Product,
    ProductAttribute,
)


def create_attribute_group(name: str) -> AttributeGroup:
    """Create an attribute group with the given name."""
    try:
        attribute_group = AttributeGroup.objects.create(name=name)
    except IntegrityError:
        raise ObjectAlreadyExistsException(
            {"message": f"Attribute Group with name '{name}' already exists."}
        )

    return attribute_group


def update_attribute_group(group_id: int, new_name: str) -> AttributeGroup:
    """Update an attribute group’s name by its ID."""
    attribute_group = AttributeGroup.get_group_by_pk(group_id)

    attribute_group.name = new_name

    try:
        attribute_group.save()
    except IntegrityError:
        raise ObjectAlreadyExistsException(
            {
                "message": f"Attribute Group with name '{new_name}' already exists."
            }
        )

    return attribute_group


def _get_attribute_slug_by_name(name: str) -> str:
    """Generate a unique slug for an attribute based on its name."""
    slug = to_chpu(name)
    while _check_attribute_exists_by_slug(slug):
        slug = to_chpu(name, last_slug=slug)
    return slug


def _check_attribute_exists_by_slug(slug: str) -> bool:
    """Return True if an attribute exists with the given slug."""
    return Attribute.objects.filter(slug=slug).exists()


def _check_attribute_exists_by_name(name: str) -> bool:
    """Return True if an attribute exists with the given name."""
    return Attribute.objects.filter(name=name).exists()


def create_attribute(
    group_id: int,
    name: str,
    attribute_type: str,
    slug: Optional[str] = None,
    added_name: Optional[str] = None,
    measure_unit: Optional[str] = None,
    visibility_in_filter: bool = False,
) -> Attribute:
    """Create an attribute with the specified parameters."""
    # Validate attribute_type against allowed values
    if attribute_type not in Attribute.AttributeType.values:
        raise ValueError(
            f"Invalid attribute type '{attribute_type}'. Must be one of {list(Attribute.AttributeType.values)}."
        )

    attribute_group = AttributeGroup.get_group_by_pk(group_id)

    if _check_attribute_exists_by_name(name):
        raise ObjectAlreadyExistsException(
            {"message": f"Attribute with name '{name}' already exists."}
        )

    if slug is None:
        slug = _get_attribute_slug_by_name(name)

    if _check_attribute_exists_by_slug(slug):
        raise ObjectAlreadyExistsException(
            {"message": f"Attribute with slug '{slug}' already exists."}
        )

    attribute = Attribute.objects.create(
        group=attribute_group,
        name=name,
        slug=slug,
        added_name=added_name,
        measure_unit=measure_unit,
        visibility_in_filter=visibility_in_filter,
        type=attribute_type,
    )

    return attribute


class UpdateAttributeDict(TypedDict, total=True):
    """Typed dict for attribute update payload."""

    group_id: int
    name: str
    attribute_type: str
    slug: Optional[str]
    added_name: Optional[str]
    measure_unit: Optional[str]
    visibility_in_filter: bool


def update_attribute(
    attribute_id: int, attribute_data: UpdateAttributeDict
) -> Attribute:
    """Update an attribute by ID with the provided data."""
    if attribute_data["attribute_type"] not in Attribute.AttributeType.values:
        raise ValueError(
            f"Invalid attribute type '{attribute_data['attribute_type']}'. Must be one of {list(Attribute.AttributeType.values)}."
        )

    attribute = Attribute.get_attribute_by_pk(attribute_id)

    if attribute.name != attribute_data[
        "name"
    ] and _check_attribute_exists_by_name(attribute_data["name"]):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Attribute with name '{attribute_data['name']}' already exists."
            }
        )

    attribute_group = AttributeGroup.get_group_by_pk(
        attribute_data["group_id"]
    )

    if (
        attribute_data["slug"] is not None
        and attribute.slug != attribute_data["slug"]
    ):
        if _check_attribute_exists_by_slug(attribute_data["slug"]):
            raise ObjectAlreadyExistsException(
                {
                    "message": f"Attribute with slug '{attribute_data['slug']}' already exists."
                }
            )

        attribute.slug = attribute_data["slug"]

    attribute.group = attribute_group
    attribute.name = attribute_data["name"]
    attribute.added_name = attribute_data["added_name"]
    attribute.measure_unit = attribute_data["measure_unit"]
    attribute.visibility_in_filter = attribute_data["visibility_in_filter"]
    attribute.type = attribute_data["attribute_type"]

    attribute.save()

    return attribute


def _get_attribute_value_slug_by_value(value: str) -> str:
    """Generate a slug for an attribute value based on its text."""
    return to_chpu(value)


def _check_attribute_value_exists_by_slug(slug: str) -> bool:
    """Return True if an attribute value exists with the given slug."""
    return AttributeValue.objects.filter(slug=slug).exists()


def _check_attribute_value_exists_by_value(value: str) -> bool:
    """Return True if an attribute value exists with the given text."""
    return AttributeValue.objects.filter(value=value).exists()


def create_attribute_value(
    value: str,
    slug: Optional[str] = None,
) -> AttributeValue:
    """Create an attribute value with the specified parameters."""
    if _check_attribute_value_exists_by_value(value):
        raise ObjectAlreadyExistsException(
            {"message": f"Attribute value '{value}' already exists."}
        )

    if slug is None:
        slug = _get_attribute_value_slug_by_value(value)

    if _check_attribute_value_exists_by_slug(slug):
        raise ObjectAlreadyExistsException(
            {"message": f"Attribute value with slug '{slug}' already exists."}
        )

    attribute_value = AttributeValue.objects.create(
        value=value,
        slug=slug,
    )

    return attribute_value


def update_attribute_value(
    value_id: int,
    new_value: Optional[str] = None,
    new_slug: Optional[str] = None,
) -> AttributeValue:
    """Update an attribute value by ID with a new value and/or slug."""
    attribute_value = AttributeValue.get_value_by_pk(value_id)

    if new_value is not None:
        if (
            _check_attribute_value_exists_by_value(new_value)
            and attribute_value.value != new_value
        ):
            raise ObjectAlreadyExistsException(
                {"message": f"Attribute value '{new_value}' already exists."}
            )
        attribute_value.value = new_value

    if new_slug is None:
        new_slug = _get_attribute_value_slug_by_value(attribute_value.value)

    if (
        _check_attribute_value_exists_by_slug(new_slug)
        and attribute_value.slug != new_slug
    ):
        raise ObjectAlreadyExistsException(
            {
                "message": f"Attribute value with slug '{new_slug}' already exists."
            }
        )

    attribute_value.slug = new_slug

    attribute_value.save()

    return attribute_value


def create_product_attribute(
    product_id: int, attribute_id: int, value_ids: Optional[list[int]] = None
) -> ProductAttribute:
    """Create a product attribute with optional linked values."""
    product = Product.get_product_by_pk(product_id)
    attribute = Attribute.get_attribute_by_pk(attribute_id)

    if ProductAttribute.objects.filter(
        product=product, attribute=attribute
    ).exists():
        raise ObjectAlreadyExistsException(
            {
                "message": f"ProductAttribute for product id '{product_id}' and attribute id '{attribute_id}' already exists."
            }
        )

    product_attribute = ProductAttribute.objects.create(
        product=product, attribute=attribute
    )

    if value_ids:
        attribute_values = AttributeValue.objects.filter(id__in=value_ids)
        if len(attribute_values) != len(value_ids):
            raise ObjectDoesNotExistException(
                {"message": "One or more attribute values do not exist."}
            )
        product_attribute._values.set(attribute_values)

    return product_attribute


def set_product_attribute_values(
    product_attribute_id: int, value_ids: list[int]
) -> ProductAttribute:
    """Set the values for a product attribute."""
    product_attribute = ProductAttribute.get_product_attribute_by_pk(
        product_attribute_id
    )

    attribute_values = AttributeValue.objects.filter(id__in=value_ids)
    if len(attribute_values) != len(value_ids):
        raise ObjectDoesNotExistException(
            {"message": "One or more attribute values do not exist."}
        )

    product_attribute._values.set(attribute_values)
    product_attribute.save()

    return product_attribute


def create_listing_attribute(
    listing_id: int,
    attribute_id: int,
    value_ids: Optional[list[int]] = None,
    order: Optional[int] = 1000,
) -> ListingAttribute:
    """Create a listing attribute with optional possible values and order."""
    listing = Listing.get_object_by_pk(listing_id)
    attribute = Attribute.get_attribute_by_pk(attribute_id)

    if ListingAttribute.objects.filter(
        listing=listing, attribute=attribute
    ).exists():
        raise ObjectAlreadyExistsException(
            {
                "message": f"ListingAttribute for listing id '{listing_id}' and attribute id '{attribute_id}' already exists."
            }
        )

    listing_attribute = ListingAttribute.objects.create(
        listing=listing, attribute=attribute, order=order
    )

    if value_ids:
        attribute_values = AttributeValue.objects.filter(id__in=value_ids)
        if len(attribute_values) != len(value_ids):
            raise ObjectDoesNotExistException(
                {"message": "One or more attribute values do not exist."}
            )
        listing_attribute._possible_values.set(attribute_values)

    return listing_attribute


def set_listing_attribute_values(
    listing_attribute_id: int, value_ids: list[int]
) -> ListingAttribute:
    """Set the possible values for a listing attribute."""
    listing_attribute = ListingAttribute.get_listing_attribute_by_pk(
        listing_attribute_id
    )

    attribute_values = AttributeValue.objects.filter(id__in=value_ids)
    if len(attribute_values) != len(value_ids):
        raise ObjectDoesNotExistException(
            {"message": "One or more attribute values do not exist."}
        )

    listing_attribute._possible_values.set(attribute_values)
    listing_attribute.save()

    return listing_attribute


def get_products_attributes_queryset_for_prefetch() -> QuerySet[Attribute]:
    """Return a queryset of product attributes suitable for prefetch_related."""
    attribute_values_qs = AttributeValue.objects.all()
    product_attributes_qs = ProductAttribute.objects.select_related(
        "attribute", "attribute__group"
    ).prefetch_related(Prefetch("_values", queryset=attribute_values_qs))
    return product_attributes_qs


def get_listing_attributes_queryset_for_prefetch() -> QuerySet[Attribute]:
    """Return a queryset of listing attributes suitable for prefetch_related."""
    attribute_values_qs = AttributeValue.objects.all()
    listing_attributes_qs = ListingAttribute.objects.select_related(
        "attribute", "attribute__group"
    ).prefetch_related(
        Prefetch("_possible_values", queryset=attribute_values_qs)
    )
    return listing_attributes_qs


def update_listings_attributes_popularity_indexes() -> None:
    """Recalculate and update popularity indexes for all listing attributes."""
    listings_attributes = ListingAttribute.objects.all()
    for listing_attribute in listings_attributes:
        listing_attribute.popular.update_index()
