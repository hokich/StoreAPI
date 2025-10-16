from django.contrib import admin

from .models import ArticlePage, CatalogPage, ProductPage, SimplePage


@admin.register(ProductPage)
class ProductPageAdmin(admin.ModelAdmin):
    """Admin panel configuration for product pages."""

    pass


@admin.register(CatalogPage)
class CatalogPageAdmin(admin.ModelAdmin):
    """Admin panel configuration for catalog pages."""

    pass


@admin.register(SimplePage)
class SimplePageAdmin(admin.ModelAdmin):
    """Admin panel configuration for simple (static) pages."""

    pass


@admin.register(ArticlePage)
class ArticlePageAdmin(admin.ModelAdmin):
    """Admin panel configuration for article pages."""

    pass
