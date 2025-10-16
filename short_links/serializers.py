from rest_framework import serializers

from .models import ShortLink


class ShortLinkSerializer(serializers.ModelSerializer):
    """Serializer for representing shortened links."""

    class Meta:
        model = ShortLink
        fields = [
            "link",
        ]
