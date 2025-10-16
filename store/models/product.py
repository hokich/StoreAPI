from collections import OrderedDict
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Any, Optional, Union

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import F, Prefetch, QuerySet
from django.utils import timezone

from utils.exceptions import ObjectDoesNotExistException
from utils.translit import to_chpu, to_cyrillic, to_latin
from web_pages.models import ProductPage

from ..managers import ProductManager
from .attribute import Attribute


if TYPE_CHECKING:
    from . import (
        Catalog,
        ProductAddService,
        ProductAttribute,
        ProductImage,
        ProductInShop,
    )


class Product(models.Model):
    """Represents a product in the catalog."""

    id = models.BigAutoField(primary_key=True)
    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255, verbose_name="Name")
    sku = models.CharField(max_length=255, unique=True, verbose_name="SKU")
    _tags = models.ManyToManyField("Catalog", related_name="_products")
    short_description = models.TextField(
        blank=True, null=True, verbose_name="Short description"
    )
    quantity = models.PositiveSmallIntegerField(
        default=1, verbose_name="Quantity"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Created at"
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated at")
    price = models.DecimalField(
        max_digits=9, decimal_places=2, verbose_name="Price"
    )
    discount_percent = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        default=0,
        verbose_name="Discount percent",
    )
    cost_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Cost price",
    )
    model = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Model"
    )
    youtube_link = models.URLField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Video review link",
    )
    popular = models.OneToOneField(
        "ranking_index.RankingIndex",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Popularity index",
    )
    sales = models.OneToOneField(
        "ranking_index.RankingIndex",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Sales index",
    )
    often_search = models.OneToOneField(
        "ranking_index.RankingIndex",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Search frequency index",
    )

    bonuses = models.BooleanField(
        default=False, verbose_name="Bonuses available"
    )
    publish = models.BooleanField(default=True, verbose_name="Published?")

    _additional_products = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        verbose_name="Additional products",
    )

    _attributes = models.ManyToManyField(
        "Attribute", through="ProductAttribute"
    )

    _reviews = models.ManyToManyField(
        "reviews.Review", through="ProductReview"
    )

    _page: Optional[ProductPage] = None

    objects = ProductManager()

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return self.name

    @property
    def status(self) -> dict:
        """
        Returns a stock status dict with a code and color based on current quantity.
        """
        match self.quantity:
            case 0:
                return {
                    "code": "OUT_OF_STOCK",
                    "color": "#EF1010",
                }
            case self.quantity if self.quantity < 4:
                return {
                    "code": "LIMITED",
                    "color": "#F5A124",
                }
            case _:
                return {
                    "code": "IN_STOCK",
                    "color": "#10B147",
                }

    @property
    def url(self) -> str:
        """Returns the public product URL."""
        return f"{settings.CLIENT_BASE_URL}/product/{self.slug}/"

    @property
    def page(self) -> Optional["ProductPage"]:
        """Returns the attached ProductPage or a transient one if not yet created."""
        if not self._page:
            try:
                self._page = self._product_page
            except ObjectDoesNotExist:
                self._page = ProductPage(product=self)
        return self._page

    @property
    def discounted_price(self) -> Decimal:
        """
        Price with discount applied.
        :return: Decimal
        """
        return self.price - self.discount_amount

    @property
    def discount_amount(self) -> Decimal:
        """
        Discount amount (rounded down to integer).
        """
        if self.discount_percent < Decimal("0.5"):
            return Decimal("0")
        discount = self.price * self.discount_percent / Decimal("100")
        return discount.quantize(Decimal("1"), rounding=ROUND_DOWN)

    @property
    def rating(self) -> int:
        """Average rating rounded to 1 decimal, or 0 if not available."""
        rating_avg = getattr(self, "rating_avg", None)
        return round(rating_avg, 1) if rating_avg else 0

    @property
    def reviews_count(self) -> int:
        """Published reviews count."""
        count = getattr(self, "_reviews_count", None)
        return count if count else 0

    @property
    def bonuses_amount_dict(self) -> dict[str, int] | None:
        """
        Returns a dict of bonus accruals per account level: {1: ..., 2: ..., 3: ...}.
        Returns None if the product is not eligible for bonuses.
        """
        return self.bonuses_amount_dict_from_price(price=self.discounted_price)

    @property
    def name_latin(self) -> str:
        """Product name transliterated to Latin."""
        return to_latin(self.name)

    @property
    def name_cyrillic(self) -> str:
        """Product name transliterated to Cyrillic."""
        return to_cyrillic(self.name)

    @property
    def product_attributes(
        self,
    ) -> models.QuerySet["ProductAttribute"]:
        """All product attributes (through model)."""
        return self._product_attributes.all()

    @property
    def additional_products(self) -> models.QuerySet["Product"]:
        """Published additional products that are in stock."""
        return self._additional_products.filter(publish=True, quantity__gte=1)

    @property
    def services(self) -> models.QuerySet["ProductAddService"]:
        """Additional services linked to the product."""
        return self._services.all()

    @property
    def listing(self) -> "Catalog":
        """Primary listing (category) tag."""
        return self._tags.filter(object_class="listing").first()

    @property
    def brand(self) -> Optional["Catalog"]:
        """Brand tag if available."""
        return self._tags.filter(object_class="brand").first()

    @property
    def brief_attributes(self) -> models.QuerySet["ProductAttribute"]:
        """First six non-list attributes for compact display."""
        return self._product_attributes.exclude(
            attribute__type=Attribute.AttributeType.LIST
        )[:6]

    @property
    def all_attributes(self) -> models.QuerySet["ProductAttribute"]:
        """All attributes for the product."""
        return self._product_attributes.all()

    @property
    def images(self) -> models.QuerySet["ProductImage"]:
        """All product images."""
        return self._images.all()

    @property
    def product_in_shops(self) -> models.QuerySet["ProductInShop"]:
        """Stock information per shop."""
        return self._product_in_shops.all()

    @property
    def can_accrue_bonuses(self) -> bool:
        """
        Returns True if the product participates in the bonus program.
        """
        return (
            self.bonuses
            and self.discounted_price > 0
            and self.discount_percent == 0
        )

    def bonuses_amount_dict_from_price(
        self, *, price: Decimal
    ) -> dict[str, int] | None:
        """
        Returns a dict of bonus accruals per account level based on the given price:
        {1: ..., 2: ..., 3: ...}. Returns None if the product is not eligible.
        """
        if not self.can_accrue_bonuses:
            return None

        return {
            "1": int(
                (price * Decimal("0.03")).quantize(
                    Decimal("1"), rounding=ROUND_DOWN
                )
            ),
            "2": int(
                (price * Decimal("0.05")).quantize(
                    Decimal("1"), rounding=ROUND_DOWN
                )
            ),
            "3": int(
                (price * Decimal("0.07")).quantize(
                    Decimal("1"), rounding=ROUND_DOWN
                )
            ),
        }

    def calculate_earned_bonuses(
        self, *, applied_bonuses: int, account_level: str
    ) -> int:
        """
        Calculates bonuses earned only on the portion not paid with bonuses.
        """
        discounted_total = self.discounted_price
        real_payment = discounted_total - applied_bonuses

        bonuses_dict = self.bonuses_amount_dict_from_price(price=real_payment)
        if not bonuses_dict:
            return 0
        return bonuses_dict.get(account_level, 0)

    def get_max_spendable_bonuses(self) -> int:
        """
        Maximum bonuses that can be applied to the order (rounded down).
        """
        discounted_total = self.discounted_price
        max_spend = discounted_total * Decimal("0.5")
        return int(max_spend.quantize(Decimal("1"), rounding=ROUND_DOWN))

    def set_main_image(self, product_image: "ProductImage") -> None:
        """Marks the given image as the main one for the product."""
        self.images.update(is_main=False)
        product_image.is_main = True
        product_image.save()

    def update_updated_at(self, with_tags: bool = False) -> None:
        """Updates `updated_at` (and related tag timestamps if requested)."""
        self.updated_at = timezone.now()
        if with_tags:
            self._tags.update(updated_at=timezone.now())
        self.save()

    def get_serialized_grouped_attributes_list(self) -> list[dict[str, Any]]:
        """Returns attributes grouped by their group for UI consumption."""
        from ..serializers.attribute import ProductAttributeSerializer

        groped_attrs: OrderedDict = OrderedDict()
        for product_attribute in self.all_attributes:
            attribute_json = ProductAttributeSerializer(product_attribute).data
            if product_attribute.attribute.group.name in groped_attrs:
                groped_attrs[product_attribute.attribute.group.name].append(
                    attribute_json
                )
            else:
                groped_attrs[product_attribute.attribute.group.name] = [
                    attribute_json
                ]
        return [
            {"name": group, "attributes": attributes}
            for group, attributes in groped_attrs.items()
        ]

    def get_serialized_similar_products(self) -> QuerySet["Product"]:
        """Returns serialized similar products (same listing and comparable price)."""
        from ..serializers.product import ProductCardSerializer
        from ..services.attribute import (
            get_products_attributes_queryset_for_prefetch,
        )

        products = (
            Product.objects.filter(
                publish=True,
                quantity__gte=1,  # >= 1,
                _tags=self.listing,
            )
            .exclude(pk=self.pk)
            .annotate(
                _discounted_price=F("price")
                * (100 - F("discount_percent"))
                / 100
            )
            .prefetch_related(
                "_images",
                "_images__thumb_image",
                "_images__sd_image",
                "_images__hd_image",
                "_tags",
                Prefetch(
                    "_product_attributes",
                    queryset=get_products_attributes_queryset_for_prefetch(),
                ),
            )
        )
        products = products.filter(
            _discounted_price__gte=self.discounted_price * Decimal(0.9),
            _discounted_price__lte=self.discounted_price * Decimal(1.1),
        )
        if products.count() < 8:
            products = products.filter(
                _discounted_price__gte=self.discounted_price * Decimal(0.85),
                _discounted_price__lte=self.discounted_price * Decimal(1.15),
            )
        return ProductCardSerializer(products[:20], many=True).data

    def set_additional_products(
        self, products: Union[list["Product"], list[int]]
    ) -> None:
        """Sets additional products by objects or IDs."""
        self._additional_products.set(products)

    @classmethod
    def get_product_by_pk(cls, pk: int, **kwargs: Any) -> "Product":
        """Returns a product by its primary key or raises an exception if not found."""
        try:
            return cls.objects.get(pk=pk, **kwargs)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Product with pk '{pk}' does not exist."}
            )

    @classmethod
    def get_product_by_sku(cls, sku: str) -> "Product":
        """Returns a product by SKU or raises an exception if not found."""
        try:
            return cls.objects.get(sku=sku)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Product with sku '{sku}' does not exist."}
            )

    @classmethod
    def find_product_by_sku(cls, sku: str) -> Optional["Product"]:
        """Finds a product by SKU or returns None if it doesn’t exist."""
        try:
            return cls.objects.get(sku=sku)
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_categories_by_products(
        cls, products: QuerySet["Product"]
    ) -> QuerySet["Catalog"]:
        """Returns distinct listing categories for the given products."""
        from .catalog import Catalog

        return Catalog.objects.filter(
            _products__in=products, object_class="listing"
        ).distinct()

    @classmethod
    def filter_products_list_by_query(
        cls, products: "QuerySet[Product]", query: str
    ) -> "QuerySet[Product]":
        """Filters a queryset by name (or SKU if the query is numeric), with transliteration fallback."""
        products_search = products.filter(name__icontains=query)
        if not products_search and query.isdigit():
            products_search = products.filter(sku__icontains=query)
        elif not products_search:
            query = to_chpu(query)
            products_search = products.filter(name__icontains=query)
        return products_search
