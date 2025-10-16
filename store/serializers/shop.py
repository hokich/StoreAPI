from typing import Optional

from rest_framework import serializers

from ..models import ProductInShop, Shop
from .city import CitySerializer


class ShopSerializer(serializers.ModelSerializer):
    """Serializer for detailed representation of a shop."""

    working_from = serializers.SerializerMethodField()
    working_to = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "address",
            "city",
            "street",
            "house",
            "region",
            "postcode",
            "working_from",
            "working_to",
            "schedule_list",
            "phone",
            "lat",
            "long",
        ]

    def get_working_from(self, obj: Shop) -> Optional[str]:
        """Return opening time formatted as HH:MM."""
        return obj.working_from.strftime("%H:%M") if obj.working_from else None

    def get_working_to(self, obj: Shop) -> Optional[str]:
        """Return closing time formatted as HH:MM."""
        return obj.working_to.strftime("%H:%M") if obj.working_to else None


class ShopBriefSerializer(serializers.ModelSerializer):
    """Serializer for a short version of a shop with working hours."""

    working_from = serializers.SerializerMethodField()
    working_to = serializers.SerializerMethodField()

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "address",
            "working_from",
            "working_to",
        ]

    def get_working_from(self, obj: Shop) -> Optional[str]:
        """Return opening time formatted as HH:MM."""
        return obj.working_from.strftime("%H:%M") if obj.working_from else None

    def get_working_to(self, obj: Shop) -> Optional[str]:
        """Return closing time formatted as HH:MM."""
        return obj.working_to.strftime("%H:%M") if obj.working_to else None


class ShopShortSerializer(serializers.ModelSerializer):
    """Serializer for compact shop representation with city information."""

    city = CitySerializer(source="city_obj")

    class Meta:
        model = Shop
        fields = ["id", "name", "city", "street", "house", "region"]


class ProductInShopSerializer(serializers.ModelSerializer):
    """Serializer for representing product availability in a specific shop."""

    shop = ShopBriefSerializer()
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = ProductInShop
        fields = [
            "shop",
            "quantity",
        ]

    def get_quantity(self, instance: ProductInShop) -> int:
        """Return product quantity limited to a maximum of 20."""
        return instance.quantity if instance.quantity <= 20 else 20
