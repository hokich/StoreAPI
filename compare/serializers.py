from rest_framework import serializers

from store.serializers.product import (
    ProductBriefSerializer,
    ProductCardSerializer,
)

from .models import CompareProduct


class CompareProductCardSerializer(serializers.ModelSerializer):
    """Serializer that returns full product card data for comparison items."""

    class Meta:
        model = CompareProduct

    def to_representation(self, instance: CompareProduct) -> dict:
        """Returns detailed product data using ProductCardSerializer."""
        product_serializer = ProductCardSerializer(instance.product)
        return product_serializer.data


class CompareProductBriefSerializer(serializers.ModelSerializer):
    """Serializer that returns brief product data for comparison items."""

    class Meta:
        model = CompareProduct

    def to_representation(self, instance: CompareProduct) -> dict:
        """Returns brief product data using ProductBriefSerializer."""
        product_serializer = ProductBriefSerializer(instance.product)
        return product_serializer.data
