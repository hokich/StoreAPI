from rest_framework import serializers

from ..models import (
    Attribute,
    AttributeValue,
    ListingAttribute,
    ProductAttribute,
)


class AttributeSerializer(serializers.ModelSerializer):
    """Serializer for the Attribute model."""

    group = serializers.CharField(source="group.name")

    class Meta:
        model = Attribute
        fields = ("id", "group", "slug", "name", "measure_unit", "type")


class ValueSerializer(serializers.ModelSerializer):
    """Serializer for the AttributeValue model."""

    class Meta:
        model = AttributeValue
        fields = ("value", "slug")


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for the ProductAttribute model with nested attribute and values."""

    attribute = AttributeSerializer()
    values = ValueSerializer(many=True)

    class Meta:
        model = ProductAttribute
        fields = (
            "id",
            "attribute",
            "values",
        )


class ListingAttributeSerializer(serializers.ModelSerializer):
    """Serializer for the ListingAttribute model."""

    class Meta:
        model = ListingAttribute

    def to_representation(self, instance: ListingAttribute) -> dict:
        """Return the serialized representation of the related attribute."""
        product_serializer = AttributeSerializer(instance.attribute)
        return product_serializer.data
