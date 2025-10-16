from typing import Any

from rest_framework import serializers

from web_pages.serializers import ProductPageSerializer

from ..models import Product, ProductAddService
from .attribute import ProductAttributeSerializer
from .catalog import BaseCatalogSerializer, CatalogBriefSerializer
from .product_image import ProductImageSerializer


class ProductServiceSerializer(serializers.ModelSerializer):
    """Serializer for additional product services."""

    price = serializers.IntegerField()

    class Meta:
        model = ProductAddService
        fields = ("id", "type", "name", "price")


class ProductShortSerializer(serializers.ModelSerializer):
    """Serializer for a short representation of Product."""

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
        ]


class BaseProductSerializer(serializers.ModelSerializer):
    """Base serializer for Product including price and bonuses."""

    price = serializers.IntegerField()
    discounted_price = serializers.IntegerField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "discounted_price",
            "bonuses_amount_dict",
        ]


class ProductSerializerWithTags(BaseProductSerializer):
    """Serializer for Product including related tags (listing, brand, colors)."""

    tags = CatalogBriefSerializer(many=True, source="_tags")

    class Meta:
        model = Product
        fields = [
            "tags",
        ]

    def to_representation(self, instance: Product) -> dict[str, Any]:
        """Return representation with extracted listing, brand, and color tags."""
        data = super().to_representation(instance)
        category = list(
            filter(lambda tag: tag["object_class"] == "listing", data["tags"])
        )
        data["listing"] = category[0] if category else None
        brand = list(
            filter(lambda tag: tag["object_class"] == "brand", data["tags"])
        )
        data["brand"] = brand[0] if brand else None
        data["color_tags"] = [tag for tag in data["tags"] if tag["color"]]
        return data


class ProductOnlySlugSerializer(serializers.ModelSerializer):
    """Serializer returning only the slug of the Product."""

    class Meta:
        model = Product
        fields = [
            "slug",
        ]


class ProductForPageSerializer(ProductSerializerWithTags):
    """Detailed serializer for Product used on product page."""

    images = ProductImageSerializer(many=True, source="_images")
    brief_attributes = ProductAttributeSerializer(many=True)
    services = ProductServiceSerializer(many=True)
    page = ProductPageSerializer()
    tags = BaseCatalogSerializer(many=True, source="_tags")

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "short_description",
            "model",
            "price",
            "discounted_price",
            "bonuses_amount_dict",
            "images",
            "tags",
            "status",
            "brief_attributes",
            "rating",
            "reviews_count",
            "youtube_link",
            "services",
            "page",
        ]


class ProductBriefSerializer(BaseProductSerializer):
    """Brief serializer for Product used in listings."""

    images = ProductImageSerializer(many=True, source="_images")
    discount_percent = serializers.FloatField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "price",
            "sku",
            "discounted_price",
            "discount_percent",
            "bonuses_amount_dict",
            "images",
        ]


class ProductForOrderContentSerializer(ProductSerializerWithTags):
    """Serializer for Product in order content context."""

    discount_percent = serializers.FloatField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "discounted_price",
            "discount_percent",
            "tags",
        ]


class AddedProductInCartSerializer(ProductSerializerWithTags):
    """Serializer for Product added to shopping cart."""

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "discounted_price",
            "tags",
        ]


class ProductCardSerializer(ProductSerializerWithTags):
    """Serializer for Product cards displayed in listings."""

    images = ProductImageSerializer(many=True, source="_images")
    specifications = ProductAttributeSerializer(
        many=True, source="_product_attributes"
    )
    shops_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "discounted_price",
            "bonuses_amount_dict",
            "images",
            "tags",
            "status",
            "specifications",
            "rating",
            "reviews_count",
            "shops_available",
        ]

    def get_shops_available(self, product: Product) -> Any:
        """Return shop availability for the product from provided context map."""
        product_shops_map = self.context.get("product_shops_map", {})
        return product_shops_map.get(product.id, None)


class ProductSerializerForSearchIndex(BaseProductSerializer):
    """Serializer for Product prepared for search indexing."""

    description = serializers.CharField(source="short_description")
    publish = serializers.IntegerField()
    tags = BaseCatalogSerializer(many=True, source="_tags")
    images = ProductImageSerializer(many=True, source="_images")
    specifications = ProductAttributeSerializer(
        many=True, source="_product_attributes"
    )

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "discounted_price",
            "bonuses_amount_dict",
            "images",
            "status",
            "specifications",
            "name_latin",
            "name_cyrillic",
            "description",
            "tags",
            "publish",
            "rating",
            "reviews_count",
        )

    def to_representation(self, instance: Product) -> dict[str, Any]:
        """Add listing, brand and their slugs for search index data."""
        data = super().to_representation(instance)
        category = list(
            filter(lambda tag: tag["object_class"] == "listing", data["tags"])
        )
        data["listing"] = category[0] if category else None
        brand = list(
            filter(lambda tag: tag["object_class"] == "brand", data["tags"])
        )
        data["brand"] = brand[0] if brand else None

        data["listing_slug"] = (
            data["listing"]["slug"] if data["listing"] else None
        )
        data["brand_slug"] = data["brand"]["slug"] if data["brand"] else None
        return data


class ProductShortCardSerializer(BaseProductSerializer):
    """Serializer for a compact product card view."""

    images = ProductImageSerializer(many=True, source="_images")

    class Meta:
        model = Product
        fields = (
            "id",
            "sku",
            "name",
            "slug",
            "price",
            "discounted_price",
            "bonuses_amount_dict",
            "images",
            "status",
        )


class ProductDetailForCartSerializer(ProductSerializerWithTags):
    """Serializer for detailed product information displayed in the cart."""

    images = ProductImageSerializer(many=True, source="_images")
    services = ProductServiceSerializer(many=True)
    additional_products = ProductCardSerializer(
        many=True, source="_additional_products"
    )
    quantity = serializers.SerializerMethodField()

    def get_quantity(self, obj: Product) -> int:
        """Return limited quantity value (max 10)."""
        return obj.quantity if obj.quantity <= 10 else 10

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "price",
            "quantity",
            "discounted_price",
            "bonuses_amount_dict",
            "images",
            "tags",
            "services",
            "additional_products",
        )
