from rest_framework import serializers

from .models import ArticlePage, CatalogPage, ProductPage, SimplePage


class SimplePageSerializer(serializers.ModelSerializer):
    """Serializer for static pages such as Home, About, Delivery, etc."""

    class Meta:
        model = SimplePage
        fields = (
            "slug",
            "h1",
            "title",
            "description",
            "head",
            "robots",
            "rich_content",
        )


class ProductPageSerializer(serializers.ModelSerializer):
    """Serializer for product-specific SEO pages."""

    class Meta:
        model = ProductPage
        fields = (
            "h1",
            "title",
            "description",
            "head",
            "robots",
            "rich_content",
        )


class CatalogPageSerializer(serializers.ModelSerializer):
    """Serializer for catalog pages (category, listing, collection, selection, brand)."""

    class Meta:
        model = CatalogPage
        fields = (
            "h1",
            "title",
            "description",
            "head",
            "robots",
            "rich_content",
        )


class ArticlePageSerializer(serializers.ModelSerializer):
    """Serializer for blog article SEO pages."""

    class Meta:
        model = ArticlePage
        fields = (
            "h1",
            "title",
            "description",
            "head",
            "robots",
            "rich_content",
        )
