from typing import Any, List, Optional, Tuple, Union

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import Catalog, City, ListingAttribute, Product, ProductDay, Shop


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    pass


@admin.register(ProductDay)
class ProductDayAdmin(admin.ModelAdmin):
    """Admin configuration for ProductDay model."""

    pass


@admin.register(Catalog)
class CatalogAdmin(admin.ModelAdmin):
    """Admin configuration for Catalog model."""

    list_display = ["name", "slug", "icon", "background", "id"]
    readonly_fields = ["popular", "image", "background"]
    list_filter = ["object_class"]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    """Admin configuration for Shop model."""

    list_display = (
        "name",
        "city_obj",
        "code",
        "working_from",
        "working_to",
        "schedule_list",
        "pickup",
        "address",
        "phone",
    )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """Admin configuration for City model."""

    list_display = ("name", "order")


class ListingNameFilter(admin.SimpleListFilter):
    """Custom admin filter by listing name."""

    title: str = "Listing Name"
    parameter_name: str = "listing"

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> List[Tuple[Any, str]]:
        """Returns available listing names for filtering."""
        listings = set(c.listing for c in model_admin.model.objects.all())
        return [(c.id, c.name) for c in listings]

    def queryset(
        self, request: HttpRequest, queryset: QuerySet[Any]
    ) -> Optional[QuerySet[Any]]:
        """Filters queryset by selected listing."""
        if self.value():
            return queryset.filter(listing__id__exact=self.value())
        return queryset


@admin.register(ListingAttribute)
class ListingAttributeAdmin(admin.ModelAdmin):
    """Admin configuration for ListingAttribute model."""

    list_display: Tuple[str, ...] = (
        "get_listing_name",
        "get_attribute_name",
        "get_popular_index",
        "order",
    )
    list_editable: Tuple[str, ...] = ("order",)
    list_filter: Tuple[admin.SimpleListFilter, ...] = (ListingNameFilter,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[ListingAttribute]:
        """Returns queryset ordered by listing name and order."""
        queryset: QuerySet[ListingAttribute] = super().get_queryset(request)
        return queryset.order_by("listing__name", "order")

    def get_listing_name(self, obj: ListingAttribute) -> str:
        """Returns listing name."""
        return obj.listing.name

    get_listing_name.short_description = "Listing Name"  # type: ignore[attr-defined]

    def get_attribute_name(self, obj: ListingAttribute) -> str:
        """Returns attribute name."""
        return obj.attribute.name

    get_attribute_name.short_description = "Attribute Name"  # type: ignore[attr-defined]

    def get_popular_index(self, obj: ListingAttribute) -> Union[int, str]:
        """Returns popular index value."""
        return obj.popular._index

    get_popular_index.short_description = "Popular Index"  # type: ignore[attr-defined]
