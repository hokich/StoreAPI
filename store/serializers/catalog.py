from typing import Optional

from rest_framework import serializers

from images.serializers import ImageSerializer
from web_pages.serializers import CatalogPageSerializer

from ..models import Catalog, Collection


class CatalogShortSerializer(serializers.ModelSerializer):
    """Serializer for a compact representation of Catalog."""

    class Meta:
        model = Catalog
        fields = (
            "id",
            "name",
            "slug",
            "object_class",
        )


class CatalogBriefSerializer(serializers.ModelSerializer):
    """Serializer for a brief representation of Catalog with extra fields."""

    class Meta:
        model = Catalog
        fields = (
            "id",
            "name",
            "short_name",
            "slug",
            "color",
            "object_class",
        )


BASE_CATALOG_FIELDS = [
    "id",
    "name",
    "slug",
    "color",
    "object_class",
    "image",
    "parent",
    "active_filters",
]


class BaseCatalogSerializer(serializers.ModelSerializer):
    """Base serializer for Catalog with image and parent."""

    image = ImageSerializer()
    parent = serializers.SerializerMethodField()

    class Meta:
        model = Catalog
        fields = BASE_CATALOG_FIELDS

    def get_parent(self, instance: Catalog) -> Optional[dict]:
        """Return serialized parent catalog or None if no parent."""
        if instance.parent:
            return BaseCatalogSerializer(instance.parent).data
        else:
            return None


class CatalogForPageSerializer(BaseCatalogSerializer):
    """Serializer for Catalog including its attached page."""

    page = CatalogPageSerializer()

    class Meta:
        model = Catalog
        # TODO: Add fields seo data and breadcrumbs
        fields = BASE_CATALOG_FIELDS + ["page"]


class CategoryCardSerializer(serializers.ModelSerializer):
    """Serializer for category cards with children preview."""

    image = ImageSerializer()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Catalog
        fields = BASE_CATALOG_FIELDS + ["children"]

    def get_children(self, instance: Catalog) -> list:
        """Return serialized non-empty child categories, otherwise an empty list."""
        if instance.children.exists():
            return BaseCatalogSerializer(
                instance.get_no_empty_children_categories(
                    with_collections=True
                ),
                many=True,
            ).data
        else:
            return []


class CatalogTreeSerializer(BaseCatalogSerializer):
    """Serializer for Catalog tree with icon, background and children."""

    background = ImageSerializer()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Catalog
        fields = BASE_CATALOG_FIELDS + ["children", "icon", "background"]

    def get_children(self, instance: Catalog) -> list:
        """Return serialized non-empty child categories as cards, otherwise empty list."""
        if instance.children.exists():
            return CategoryCardSerializer(
                instance.get_no_empty_children_categories(
                    with_collections=True
                ),
                many=True,
            ).data
        else:
            return []

    def to_representation(self, instance: Catalog) -> dict:
        """Return default representation using the parent implementation."""
        return super(CatalogTreeSerializer, self).to_representation(instance)


class CatalogSerializerForSearchIndex(BaseCatalogSerializer):
    """Serializer for Catalog tailored for search indexing."""

    def to_representation(self, instance: Catalog) -> dict:
        """Adjust image for collections to inherit parent's image when needed."""
        rep = super(CatalogSerializerForSearchIndex, self).to_representation(
            instance
        )
        if instance.object_class == "collection":
            rep["image"] = (
                ImageSerializer(instance.parent.image).data
                if instance.parent and instance.parent.image
                else None
            )
        return rep

    class Meta:
        model = Catalog
        fields = BASE_CATALOG_FIELDS + ["name_latin", "name_cyrillic"]


class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for Collection with precomputed products count."""

    products_count = serializers.IntegerField(
        source="get_collection_products_count"
    )

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "short_name",
            "slug",
            "products_count",
        )
