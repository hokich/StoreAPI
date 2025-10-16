from rest_framework import serializers

from images.serializers import ImageSerializer
from store.serializers.catalog import CatalogBriefSerializer

from .models import Banner


class BannerSerializer(serializers.ModelSerializer):
    """Serializes Banner model with related images and catalog tags."""

    tags = CatalogBriefSerializer(many=True, source="_tags")
    home_mobile_image = ImageSerializer()
    home_desktop_image = ImageSerializer()
    catalog_mobile_image = ImageSerializer()
    catalog_desktop_image = ImageSerializer()
    header_desktop_image = ImageSerializer()

    class Meta:
        model = Banner
        fields = (
            "id",
            "name",
            "url",
            "date_end",
            "tags",
            "is_on_all_pages",
            "home_mobile_image",
            "home_desktop_image",
            "catalog_mobile_image",
            "catalog_desktop_image",
            "header_desktop_image",
        )
