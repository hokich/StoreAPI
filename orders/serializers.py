from typing import Optional

from rest_framework import serializers

from store.serializers.shop import ShopBriefSerializer

from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for detailed order representation."""

    delivery_address = serializers.SerializerMethodField()
    shop = ShopBriefSerializer()

    class Meta:
        model = Order
        fields = (
            "id",
            "customer_info",
            "content",
            "type",
            "reception_method",
            "payment_method",
            "status",
            "created_at",
            "delivery_address",
            "shop",
        )

    def get_delivery_address(self, obj: Order) -> Optional[dict]:
        """Returns delivery address if applicable, otherwise None."""
        if not any([obj.city, obj.street, obj.house, obj.apartment]):
            return None
        if obj.reception_method == Order.ReceptionMethod.PICK_UP:
            return None
        return {
            "city": obj.city,
            "street": obj.street,
            "house": obj.house,
            "apartment": obj.apartment,
        }
