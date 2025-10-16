from rest_framework import serializers

from store.serializers.catalog import BaseCatalogSerializer

from .models import SearchQuery


class SearchQuerySerializer(serializers.ModelSerializer):
    """Serializer for representing search queries with linked catalog data."""

    catalog = BaseCatalogSerializer()

    class Meta:
        model = SearchQuery
        fields = ("text", "catalog")
