from rest_framework import serializers

from ..models import ProductDay
from .product import ProductCardSerializer


class ProductDaySerializer(serializers.ModelSerializer):
    """Serializer for the ProductDay model."""

    class Meta:
        model = ProductDay

    def to_representation(self, instance: ProductDay) -> dict:
        """Return serialized representation of the related product."""
        product_serializer = ProductCardSerializer(instance.product)
        return product_serializer.data
