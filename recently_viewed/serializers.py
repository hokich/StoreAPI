from rest_framework import serializers

from store.serializers.product import ProductCardSerializer

from .models import RecentlyViewed


class RecentlyViewedProductSerializer(serializers.ModelSerializer):
    """Serializer for recently viewed products."""

    class Meta:
        fields = "__all__"
        model = RecentlyViewed

    def to_representation(self, instance: RecentlyViewed) -> dict:
        """Return product data representation for the recently viewed item."""
        product_serializer = ProductCardSerializer(instance.product)
        return product_serializer.data
