from utils.exceptions import ObjectAlreadyExistsException

from .models import ShortLink


def create_short_link(slug: str, link: str) -> ShortLink:
    """Creates a new short link."""
    slug_lower = slug.lower()

    if ShortLink.objects.filter(slug=slug_lower).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"ShortLink with slug '{slug}' already exists."}
        )

    short_link = ShortLink.objects.create(slug=slug_lower, link=link)
    return short_link


def update_short_link(link_id: int, slug: str, link: str) -> ShortLink:
    """Updates an existing short link."""
    short_link = ShortLink.get_link_by_pk(link_id)
    slug_lower = slug.lower()

    if ShortLink.objects.exclude(pk=link_id).filter(slug=slug_lower).exists():
        raise ObjectAlreadyExistsException(
            {"message": f"ShortLink with slug '{slug}' already exists."}
        )

    short_link.slug = slug_lower
    short_link.link = link
    short_link.save()
    return short_link
