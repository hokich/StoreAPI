from typing import Optional, TypedDict

from blog.models import Article
from store.models import Catalog, Product
from utils.exceptions import ObjectAlreadyExistsException

from .models import ArticlePage, CatalogPage, ProductPage, SimplePage


def create_simple_page(
    slug: str,
    h1: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    head: Optional[str] = None,
    robots: Optional[str] = None,
    rich_content: Optional[dict] = None,
) -> SimplePage:
    """Creates a simple page."""
    if SimplePage.objects.filter(slug=slug).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"SimplePage with slug {slug} already exists"}
        )
    page = SimplePage.objects.create(
        slug=slug,
        _h1=h1,
        _title=title,
        _description=description,
        head=head,
        robots=robots,
        _rich_content=rich_content,
    )
    return page


class UpdatePageParamsDict(TypedDict, total=True):
    h1: Optional[str]
    title: Optional[str]
    description: Optional[str]
    head: Optional[str]
    robots: Optional[str]
    rich_content: Optional[dict]


def update_simple_page(
    page_id: int,
    slug: str,
    page_date: UpdatePageParamsDict,
) -> SimplePage:
    """Updates a simple page."""
    page = SimplePage.get_page_by_pk(page_id)
    if slug != page.slug and SimplePage.objects.filter(_slug=slug).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"SimplePage with slug {slug} already exists"}
        )
    page.slug = slug
    page._h1 = page_date["h1"]
    page._title = page_date["title"]
    page._description = page_date["description"]
    page.head = page_date["head"]
    page.robots = page_date["robots"]
    page.rich_content = page_date["rich_content"]
    page.save()
    return page


def create_product_page(
    product_id: int,
    h1: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    head: Optional[str] = None,
    robots: Optional[str] = None,
    rich_content: Optional[dict] = None,
) -> ProductPage:
    """Creates a product page."""
    product = Product.get_product_by_pk(product_id)
    if ProductPage.objects.filter(product=product).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"ProductPage with product {product} already exists"}
        )
    page = ProductPage.objects.create(
        product=product,
        _h1=h1,
        _title=title,
        _description=description,
        head=head,
        robots=robots,
        _rich_content=rich_content,
    )
    return page


def update_product_page(
    page_id: int,
    page_date: UpdatePageParamsDict,
) -> ProductPage:
    """Updates a product page."""
    page = ProductPage.get_page_by_pk(page_id)
    page._h1 = page_date["h1"]
    page._title = page_date["title"]
    page._description = page_date["description"]
    page.head = page_date["head"]
    page.robots = page_date["robots"]
    page.rich_content = page_date["rich_content"]
    page.save()
    return page


def create_catalog_page(
    catalog_id: int,
    h1: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    head: Optional[str] = None,
    robots: Optional[str] = None,
    rich_content: Optional[dict] = None,
) -> CatalogPage:
    """Creates a catalog page."""
    catalog = Catalog.get_object_by_pk(catalog_id)
    if CatalogPage.objects.filter(catalog=catalog).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"CatalogPage with catalog {catalog} already exists"}
        )
    page = CatalogPage.objects.create(
        catalog=catalog,
        _h1=h1,
        _title=title,
        _description=description,
        head=head,
        robots=robots,
        _rich_content=rich_content,
    )
    return page


def update_catalog_page(
    page_id: int,
    page_date: UpdatePageParamsDict,
) -> CatalogPage:
    """Updates a catalog page."""
    page = CatalogPage.get_page_by_pk(page_id)
    page._h1 = page_date["h1"]
    page._title = page_date["title"]
    page._description = page_date["description"]
    page.head = page_date["head"]
    page.robots = page_date["robots"]
    page.rich_content = page_date["rich_content"]
    page.save()
    return page


def create_article_page(
    article_id: int,
    h1: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    head: Optional[str] = None,
    robots: Optional[str] = None,
    rich_content: Optional[dict] = None,
) -> ArticlePage:
    """Creates an article page."""
    article = Article.get_article_by_pk(article_id)
    if ArticlePage.objects.filter(article=article).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"ArticlePage with catalog {article} already exists"}
        )
    page = ArticlePage.objects.create(
        article=article,
        _h1=h1,
        _title=title,
        _description=description,
        head=head,
        robots=robots,
        _rich_content=rich_content,
    )
    return page


def update_article_page(
    page_id: int,
    page_date: UpdatePageParamsDict,
) -> ArticlePage:
    """Updates an article page."""
    page = ArticlePage.get_page_by_pk(page_id)
    page._h1 = page_date["h1"]
    page._title = page_date["title"]
    page._description = page_date["description"]
    page.head = page_date["head"]
    page.robots = page_date["robots"]
    page.rich_content = page_date["rich_content"]
    page.save()
    return page
