from rest_framework import serializers

from store.serializers.product import (
    ProductBriefSerializer,
    ProductCardSerializer,
)

from .models import FavoriteProduct


class FavoriteProductCardSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed representation of a favorite product card.
    """

    class Meta:
        model = FavoriteProduct

    def to_representation(self, instance: FavoriteProduct) -> dict:
        product_serializer = ProductCardSerializer(instance.product)
        return product_serializer.data


class FavoriteProductBriefSerializer(serializers.ModelSerializer):
    """
    Serializer for brief representation of a favorite product.
    """

    class Meta:
        model = FavoriteProduct

    def to_representation(self, instance: FavoriteProduct) -> dict:
        product_serializer = ProductBriefSerializer(instance.product)
        return product_serializer.data
