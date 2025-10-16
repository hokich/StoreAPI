from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from store.models import Catalog
from tags_importers.models import TagImporter


@admin.register(TagImporter)
class TagImporterAdmin(admin.ModelAdmin):
    """Admin configuration for TagImporter."""

    list_display: tuple[str, ...] = (
        "name",
        "created_at",
        "date_start",
        "date_end",
        "active",
    )

    def formfield_for_manytomany(
        self, db_field: Any, request: HttpRequest, **kwargs: Any
    ) -> Any:
        """Limits selectable tags to FreeTag and Selection catalog objects."""
        if db_field.name == "tags":
            kwargs["queryset"] = Catalog.objects.filter(
                object_class__in=["freetag", "selection"]
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)
