from rest_framework import serializers

from store.models import City


class CitySerializer(serializers.ModelSerializer):
    """Serializer for the City model."""

    class Meta:
        model = City
        fields = ["id", "name"]
