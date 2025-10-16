from rest_framework import serializers

from images.serializers import ImageSerializer
from store.serializers.product import ProductCardSerializer
from web_pages.serializers import ArticlePageSerializer

from .models import Article


class ArticleSerializer(serializers.ModelSerializer):
    """Full article serializer with related image, page, and products."""

    image = ImageSerializer()
    page = ArticlePageSerializer()
    products = ProductCardSerializer(many=True, source="article_products")

    class Meta:
        model = Article
        fields = (
            "id",
            "name",
            "slug",
            "image",
            "views_count",
            "created_at",
            "page",
            "products",
        )


class ArticleBriefSerializer(serializers.ModelSerializer):
    """Short article serializer for list or preview views."""

    image = ImageSerializer()
    description = serializers.CharField(source="page.description")

    class Meta:
        model = Article
        fields = (
            "id",
            "name",
            "slug",
            "image",
            "created_at",
            "description",
        )
