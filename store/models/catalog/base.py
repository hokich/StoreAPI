from typing import TYPE_CHECKING, Any, Optional

from cachetools import TTLCache, cached
from colorfield.fields import ColorField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count, Exists, OuterRef, Q, QuerySet

from utils.exceptions import ObjectDoesNotExistException
from utils.translit import to_cyrillic, to_latin
from web_pages.models import CatalogPage

from ...managers import CatalogManager


if TYPE_CHECKING:
    from .. import ListingAttribute, Product


class Catalog(models.Model):
    """Represents a generic catalog node (category, listing, collection, selection, brand, freetag)."""

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=255)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="children",
        verbose_name="Parent catalog",
    )
    name = models.CharField(max_length=255, verbose_name="Name")
    short_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="Short name"
    )
    color = ColorField(blank=True, null=True, verbose_name="Color")
    object_class = models.CharField(max_length=20)
    popular = models.OneToOneField(
        "ranking_index.RankingIndex",
        on_delete=models.CASCADE,
        related_name="+",
    )
    active_filters = models.JSONField(
        default=dict, blank=True, null=True, verbose_name="Active filters"
    )
    updated_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Last updated at"
    )
    icon = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="Icon"
    )
    background = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Background image",
    )
    image = models.OneToOneField(
        "images.Image",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
        verbose_name="Image",
    )
    _additional_products = models.ManyToManyField(
        "Product",
        blank=True,
        verbose_name="Additional products in category",
    )

    # Cached page reference (assigned lazily in the `page` property).
    _page: Optional[CatalogPage] = None

    objects = CatalogManager()

    class Meta:
        verbose_name = "Catalog"
        verbose_name_plural = "Catalogs"
        ordering = ["-popular___index"]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "parent"], name="unique_slug_parent"
            ),
        ]

    def __str__(self) -> str:
        """Returns a readable representation with name and slug."""
        return f"{self.name} | {self.slug}"

    @property
    def page(self) -> Optional[CatalogPage]:
        """Returns an attached CatalogPage or a transient one if not persisted."""
        if not self._page:
            try:
                self._page = self._catalog_page
            except ObjectDoesNotExist:
                self._page = CatalogPage(catalog=self)
        return self._page

    @property
    def name_latin(self) -> str:
        """Returns the catalog name transliterated to Latin."""
        return to_latin(self.name)

    @property
    def name_cyrillic(self) -> str:
        """Returns the catalog name transliterated to Cyrillic."""
        return to_cyrillic(self.name)

    @property
    def listing_attributes(self) -> "QuerySet[ListingAttribute]":
        """Returns listing attributes ordered by `order` and popularity index."""
        return (
            self._listing_attributes.all()
            .select_related("popular")
            .prefetch_related("_possible_values")
            .order_by("order", "-popular___index")
        )

    @property
    def additional_products(self) -> models.QuerySet["Product"]:
        """Returns additional (manually attached) products that are published."""
        return self._additional_products.filter(publish=True)

    @property
    @cached(cache=TTLCache(maxsize=360, ttl=60 * 15))
    def all_listings(self) -> list:
        """Returns a flattened list of listings from this node's children (cached 15 min)."""
        from .. import Category, Listing

        res = []
        for category in self.children.all():
            match category:
                case Category():
                    _r = category.all_listings
                    if _r:
                        res.extend(_r)
                case Listing():
                    res.append(category)
                case _:
                    pass
        return res

    def get_available_products_count(self) -> int:
        """Returns the number of available products (published with quantity ≥ 1)."""
        return self._products.filter(
            publish=True,
            quantity__gte=1,
        ).count()

    def get_catalogs_chain(self) -> list["Catalog"]:
        """Returns a parent chain from root to this node (for breadcrumbs/URLs)."""
        chain_list = [self]
        category = self
        while True:
            if category.parent:
                chain_list.append(category.parent)
                category = category.parent
            else:
                return list(reversed(chain_list))

    def get_no_empty_children_categories(
        self, with_collections: bool = False
    ) -> "models.QuerySet[Catalog]":
        """
        Returns child catalogs that have children or non-zero products;
        optionally include collections.
        """
        has_children = Catalog.objects.filter(parent=OuterRef("pk"))
        qs_filter = Q(Exists(has_children)) | Q(product_count__gt=0)
        if with_collections:
            qs_filter |= Q(object_class="collection")
        return (
            self.children.all()
            .select_related("image", "parent")
            .annotate(product_count=Count("_products"))
            .filter(qs_filter)
            .order_by("-popular___index")
        )

    @classmethod
    def get_no_empty_categories_list(cls) -> "models.QuerySet[Catalog]":
        """Returns top-level catalogs (listing/category) that are non-empty or have children."""
        has_children = cls.objects.filter(parent=OuterRef("pk"))
        return (
            cls.objects.select_related("parent", "image")
            .prefetch_related("children")
            .annotate(product_count=Count("_products"))
            .filter(object_class__in=["listing", "category"], parent=None)
            .filter(Q(Exists(has_children)) | Q(product_count__gt=0))
        )

    @classmethod
    def get_object_by_pk(cls, pk: int) -> "Catalog":
        """Returns a catalog by primary key or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Catalog object with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_object_by_slug(cls, slug: str) -> "Catalog":
        """Returns a catalog by slug limited to the subclass's object_class, else raises ObjectDoesNotExistException."""
        model_name = cls.__name__.lower()
        if model_name == "catalog":
            raise ValueError(
                "Method 'get_object_by_slug' should be called from subclass of 'Catalog' model."
            )
        try:
            return cls.objects.get(slug=slug, object_class=model_name)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Object with slug '{slug}' and class '{model_name}' does not exist."
                }
            )

    @classmethod
    def get_object_by_kwargs(cls, slug: str, **kwargs: Any) -> "Catalog":
        """Returns a catalog by slug and extra filters or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(slug=slug, **kwargs)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {
                    "message": f"Object with slug '{slug}' and kwargs '{kwargs}' does not exist."
                }
            )
