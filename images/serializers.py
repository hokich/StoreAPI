from rest_framework import serializers

from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ("id", "src", "alt")

    def get_src(self, obj: Image) -> str:
        # Return only the relative image URL
        return obj.image.url
