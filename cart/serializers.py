from rest_framework import serializers

from store.serializers.product import (
    AddedProductInCartSerializer,
    ProductBriefSerializer,
    ProductDetailForCartSerializer,
    ProductForOrderContentSerializer,
    ProductServiceSerializer,
)

from .models import Cart, CartProduct, CartProductAddService


class CartProductAddServiceSerializer(serializers.ModelSerializer):
    """Serialize a selected add-on service linked to a cart item."""

    service = ProductServiceSerializer()

    class Meta:
        model = CartProductAddService
        fields = (
            "service",
            "active",
        )


class CartProductSerializer(serializers.ModelSerializer):
    """Detailed cart item with product info and attached services."""

    product = ProductDetailForCartSerializer()
    services = CartProductAddServiceSerializer(many=True)

    class Meta:
        model = CartProduct
        fields = ("product", "services", "quantity")


class CartProductForOrderSerializer(serializers.ModelSerializer):
    """Cart item representation optimized for order creation."""

    product = ProductForOrderContentSerializer()
    services = CartProductAddServiceSerializer(many=True)

    class Meta:
        model = CartProduct
        fields = ("product", "services", "quantity")


class AddedCartProductSerializer(serializers.ModelSerializer):
    """Minimal cart item payload returned right after adding to cart."""

    product = AddedProductInCartSerializer()

    class Meta:
        model = CartProduct
        fields = ("product", "quantity")


class CartProductBriefSerializer(serializers.ModelSerializer):
    """Brief cart item used in lightweight cart previews."""

    product = ProductBriefSerializer()

    class Meta:
        model = CartProduct
        fields = ("product", "quantity")


CART_SERIALIZER_FIELDS = [
    "products",
    "total_quantity",
    "total_price",
    "total_discount_price",
    "total_discount_amount",
    "total_bonuses_amount_dict",
]


class CartSerializer(serializers.ModelSerializer):
    """Full cart with detailed products and aggregated totals."""

    products = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = CART_SERIALIZER_FIELDS

    def get_products(self, obj: Cart) -> list[dict]:
        """Returns detailed cart items with images, tags, services, and additions."""
        products = (
            obj.products.select_related("product")
            .prefetch_related(
                "product___images",
                "product___images__thumb_image",
                "product___images__sd_image",
                "product___images__hd_image",
                "product___tags",
                "product___services",
                "product___additional_products",
                "product___additional_products___images",
                "product___additional_products___images__thumb_image",
                "product___additional_products___images__sd_image",
                "product___additional_products___images__hd_image",
                "_services",
                "_cart_product_add_services",
            )
            .order_by("date_added")
        )
        serializer = CartProductSerializer(products, many=True)
        return serializer.data


class CartBriefSerializer(serializers.ModelSerializer):
    """Lightweight cart with brief product info and totals."""

    products = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = CART_SERIALIZER_FIELDS

    def get_products(self, obj: Cart) -> list[dict]:
        """Returns brief cart items with essential product images."""
        products = (
            obj.products.select_related("product")
            .prefetch_related(
                "product___images",
                "product___images__thumb_image",
                "product___images__sd_image",
                "product___images__hd_image",
            )
            .order_by("date_added")
        )
        serializer = CartProductBriefSerializer(products, many=True)
        return serializer.data


class CartForOrderSerializer(serializers.ModelSerializer):
    """Cart representation tailored for order submission pipeline."""

    products = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = CART_SERIALIZER_FIELDS

    def get_products(self, obj: Cart) -> list[dict]:
        """Returns cart items with selected services for order payload."""
        products = (
            obj.products.select_related("product")
            .prefetch_related(
                "_services",
                "_cart_product_add_services",
            )
            .order_by("date_added")
        )
        serializer = CartProductForOrderSerializer(products, many=True)
        return serializer.data
