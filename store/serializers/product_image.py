from rest_framework import serializers

from images.serializers import ImageSerializer

from ..models import ProductImage


class ProductImageOnlySdSrcSerializer(serializers.ModelSerializer):
    """Serializer returning only the SD image URL of a product image."""

    class Meta:
        model = ProductImage

    def to_representation(self, instance: ProductImage) -> dict:
        """Return only the URL of the SD image."""
        return instance.sd_image.image.url


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for ProductImage including all image resolutions."""

    thumb = ImageSerializer(source="thumb_image")
    sd = ImageSerializer(source="sd_image")
    hd = ImageSerializer(source="hd_image")

    class Meta:
        model = ProductImage
        fields = ["id", "thumb", "sd", "hd", "is_main"]
