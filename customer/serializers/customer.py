from rest_framework import serializers

from store.serializers.city import CitySerializer

from ..models import Customer


class CustomerBriefSerializer(serializers.ModelSerializer):
    """Brief serializer for customer data, used in listings and lightweight contexts."""

    first_name = serializers.CharField(source="clean_first_name")
    last_name = serializers.CharField(source="clean_last_name")
    patronymic = serializers.CharField(source="clean_patronymic")
    city = CitySerializer(source="city_obj")

    class Meta:
        model = Customer
        fields = (
            "id",
            "session_id",
            "first_name",
            "last_name",
            "patronymic",
            "phone",
            "email",
            "city",
        )
