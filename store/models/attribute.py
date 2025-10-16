from django.db import models
from django.db.models import QuerySet

from utils.exceptions import ObjectDoesNotExistException

from ..managers import ListingAttributeManager


class AttributeGroup(models.Model):
    """Represents a group of attributes."""

    name = models.CharField("Name", max_length=110, unique=True)

    class Meta:
        verbose_name = "Attribute group"
        verbose_name_plural = "Attribute groups"

    def __str__(self) -> str:
        return self.name

    @classmethod
    def get_group_by_pk(cls, pk: int) -> "AttributeGroup":
        """Get a group by ID."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Attribute Group with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_group_by_name(cls, name: str) -> "AttributeGroup":
        """Get a group by name."""
        try:
            return cls.objects.get(name=name)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Attribute Group with name '{name}' does not exist."
                }
            )


class Attribute(models.Model):
    """Represents a specific attribute belonging to an attribute group."""

    group = models.ForeignKey(
        "AttributeGroup", on_delete=models.PROTECT, related_name="attributes"
    )
    name = models.CharField(max_length=255, unique=True, verbose_name="Name")
    slug = models.SlugField(
        max_length=255, unique=True, blank=True, verbose_name="Slug"
    )
    added_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Additional name"
    )
    measure_unit = models.CharField(
        max_length=10, blank=True, null=True, verbose_name="Unit of measure"
    )
    visibility_in_filter = models.BooleanField(
        default=0, verbose_name="Visible in filter"
    )

    class AttributeType(models.TextChoices):
        NUM_INT = "NUM_INT", "Numeric"
        NUM_RANGE = "NUM_RANGE", "Numeric range"
        TEXT = "TEXT", "Text"
        BOOLEAN = "BOOLEAN", "Switch"
        LIST = "LIST", "List"
        SELECT = "SELECT", "Selectable"

    type = models.CharField(
        max_length=12,
        choices=AttributeType.choices,
        verbose_name="Attribute type",
    )

    class Meta:
        verbose_name = "Attribute"
        verbose_name_plural = "Attributes"

    def __str__(self) -> str:
        return f"{self.name} | {self.get_type_display()}"

    @classmethod
    def get_attribute_by_pk(cls, pk: int) -> "Attribute":
        """Get an attribute by ID."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Attribute with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_attribute_by_slug(cls, slug: str) -> "Attribute":
        """Get an attribute by slug."""
        try:
            return cls.objects.get(slug=slug)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Attribute with slug '{slug}' does not exist."}
            )


class AttributeValue(models.Model):
    """Represents a concrete value for an attribute."""

    value = models.CharField(max_length=100, unique=True, verbose_name="Value")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")

    class Meta:
        verbose_name = "Attribute value"
        verbose_name_plural = "Attribute values"
        ordering = ["slug"]

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def get_value_by_pk(cls, pk: int) -> "AttributeValue":
        """Get an attribute value by ID."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Attribute Value with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_value_by_value(cls, value: str) -> "AttributeValue":
        """Get an attribute value by its text value."""
        try:
            return cls.objects.get(value=value)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Attribute Value with value '{value}' does not exist."
                }
            )


class ProductAttribute(models.Model):
    """Represents a product’s attribute with one or more selected values."""

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="_product_attributes",
        verbose_name="Product",
    )
    attribute = models.ForeignKey(
        "Attribute", on_delete=models.CASCADE, verbose_name="Attribute"
    )
    _values = models.ManyToManyField(
        "AttributeValue", blank=True, verbose_name="Attribute values"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "attribute"],
                name="unique_product_attribute",
            )
        ]
        verbose_name = "Product attribute"
        verbose_name_plural = "Product attributes"
        ordering = ["attribute__pk"]

    @property
    def values(self) -> models.QuerySet["AttributeValue"]:
        return self._values.all()

    @property
    def value(self) -> "AttributeValue":
        return self.values.first()

    @property
    def values_str(self) -> str:
        return ", ".join(self.values.values_list("value", flat=True))

    @classmethod
    def get_product_attribute_by_pk(cls, pk: int) -> "ProductAttribute":
        """Get a product attribute by ID."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Product Attribute with pk '{pk}' does not exist."
                }
            )


class ListingAttribute(models.Model):
    """Represents an attribute configured for a specific catalog listing."""

    listing = models.ForeignKey(
        "Catalog", on_delete=models.CASCADE, related_name="_listing_attributes"
    )
    attribute = models.ForeignKey("Attribute", on_delete=models.CASCADE)
    _possible_values = models.ManyToManyField(
        "AttributeValue",
        blank=True,
        verbose_name="Possible attribute values",
    )

    popular = models.OneToOneField(
        "ranking_index.RankingIndex",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
    )
    order = models.PositiveSmallIntegerField(
        default=1000, verbose_name="Order"
    )

    objects = ListingAttributeManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["listing", "attribute"],
                name="unique_listing_attribute",
            )
        ]
        verbose_name = "Attribute in category"
        verbose_name_plural = "Attributes in categories"

    def __str__(self) -> str:
        return f"{self.listing.name} | {self.attribute.name}"

    @property
    def possible_values(self) -> "QuerySet[AttributeValue]":
        return self._possible_values.all()

    @classmethod
    def get_listing_attribute_by_pk(cls, pk: int) -> "ListingAttribute":
        """Get a listing attribute by ID."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Listing Attribute with pk '{pk}' does not exist."
                }
            )
