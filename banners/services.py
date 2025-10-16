import datetime
from typing import Optional, TypedDict

from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone

from images.services import create_image, validate_image_proportions
from utils.exceptions import ImageInvalidFormatException
from utils.translit import to_chpu

from .models import Banner


BANNER_IMAGE_RATIOS = {
    "home_mobile": {"width": 1, "height": 2},
    "home_desktop": {"width": 2, "height": 1},
    "catalog_mobile": {"width": 8, "height": 3},
    "catalog_desktop": {"width": 10, "height": 1},
    "header_desktop": {"width": 36, "height": 1},
}

BANNER_IMAGE_SIZES = {
    "home_mobile": {"width": 960, "height": 1920},
    "home_desktop": {"width": 1920, "height": 960},
    "catalog_mobile": {"width": 1920, "height": 720},
    "catalog_desktop": {"width": 1920, "height": 192},
    "header_desktop": {"width": 2560, "height": 71},
}


def create_banner(
    name: str,
    url: Optional[str] = None,
    date_start: Optional[datetime.date] = None,
    date_end: Optional[str] = None,
    is_on_all_pages: bool = False,
    is_active: bool = True,
) -> Banner:
    """Creates a new banner with optional schedule and URL."""
    now_date = timezone.now().date()
    return Banner.objects.create(
        name=name,
        url=url,
        date_start=date_start if date_start else now_date,
        date_end=date_end,
        is_on_all_pages=is_on_all_pages,
        is_active=is_active,
    )


class UpdateBannerParamsDict(TypedDict, total=True):
    name: str
    url: Optional[str]
    date_start: Optional[str]
    date_end: Optional[str]
    is_on_all_pages: bool
    is_active: bool


def update_banner(
    banner_id: int, banner_data: UpdateBannerParamsDict
) -> Banner:
    """Updates existing banner fields and saves changes."""
    banner = Banner.get_banner_by_pk(banner_id)
    banner.name = banner_data["name"]
    banner.url = banner_data["url"]
    banner.date_start = banner_data["date_start"]
    banner.date_end = banner_data["date_end"]
    banner.is_on_all_pages = banner_data["is_on_all_pages"]
    banner.is_active = banner_data["is_active"]
    banner.save()
    return banner


def set_tags_for_banner(banner_id: int, tags_ids: list[int]) -> None:
    """Assigns tag IDs to a specific banner."""
    banner = Banner.get_banner_by_pk(banner_id)
    banner._tags.set(tags_ids)


def delete_banner(banner_id: int) -> None:
    """Deletes banner and all its linked images."""
    banner = Banner.get_banner_by_pk(banner_id)
    if banner.home_mobile_image:
        banner.home_mobile_image.delete()
    if banner.home_desktop_image:
        banner.home_desktop_image.delete()
    if banner.catalog_mobile_image:
        banner.catalog_mobile_image.delete()
    if banner.catalog_desktop_image:
        banner.catalog_desktop_image.delete()
    if banner.header_desktop_image:
        banner.header_desktop_image.delete()
    banner.delete()


def set_banner_home_mobile_image(
    banner_id: int, image_file: Optional[UploadedFile] = None
) -> Banner:
    """Sets or removes the home (mobile) banner image."""
    banner = Banner.get_banner_by_pk(banner_id)

    if image_file is None:
        if banner.home_mobile_image:
            banner.home_mobile_image.delete()
        banner.home_mobile_image = None
        banner.save()
        return banner

    size = BANNER_IMAGE_SIZES["home_mobile"]

    if banner.home_mobile_image:
        banner.home_mobile_image.delete()

    image = create_image(
        name=f"home_m_{to_chpu(banner.name)}",
        object_type="banner",
        image_file=image_file,
        max_width=size["width"],
        max_height=size["height"],
    )

    banner.home_mobile_image = image
    banner.save()
    return banner


def set_banner_home_desktop_image(
    banner_id: int, image_file: Optional[UploadedFile] = None
) -> Banner:
    """Sets or removes the home (desktop) banner image."""
    banner = Banner.get_banner_by_pk(banner_id)

    if image_file is None:
        if banner.home_desktop_image:
            banner.home_desktop_image.delete()
        banner.home_desktop_image = None
        banner.save()
        return banner

    size = BANNER_IMAGE_SIZES["home_desktop"]

    if banner.home_desktop_image:
        banner.home_desktop_image.delete()

    image = create_image(
        name=f"home_d_{to_chpu(banner.name)}",
        object_type="banner",
        image_file=image_file,
        max_width=size["width"],
        max_height=size["height"],
    )

    banner.home_desktop_image = image
    banner.save()
    return banner


def set_banner_catalog_mobile_image(
    banner_id: int, image_file: Optional[UploadedFile] = None
) -> Banner:
    """Sets or removes the catalog (mobile) banner image."""
    banner = Banner.get_banner_by_pk(banner_id)

    if image_file is None:
        if banner.catalog_mobile_image:
            banner.catalog_mobile_image.delete()
        banner.catalog_mobile_image = None
        banner.save()
        return banner

    ratio = BANNER_IMAGE_RATIOS["catalog_mobile"]
    size = BANNER_IMAGE_SIZES["catalog_mobile"]

    if not validate_image_proportions(
        image_file, ratio["width"], ratio["height"]
    ):
        raise ImageInvalidFormatException(
            {
                "message": f"Image proportions are invalid. Expected {ratio['width']}:{ratio['height']} ratio."
            }
        )

    if banner.catalog_mobile_image:
        banner.catalog_mobile_image.delete()

    image = create_image(
        name=f"tag_m_{to_chpu(banner.name)}",
        object_type="banner",
        image_file=image_file,
        max_width=size["width"],
        max_height=size["height"],
    )

    banner.catalog_mobile_image = image
    banner.save()
    return banner


def set_banner_catalog_desktop_image(
    banner_id: int, image_file: Optional[UploadedFile] = None
) -> Banner:
    """Sets or removes the catalog (desktop) banner image."""
    banner = Banner.get_banner_by_pk(banner_id)

    if image_file is None:
        if banner.catalog_desktop_image:
            banner.catalog_desktop_image.delete()
        banner.catalog_desktop_image = None
        banner.save()
        return banner

    ratio = BANNER_IMAGE_RATIOS["catalog_desktop"]
    size = BANNER_IMAGE_SIZES["catalog_desktop"]

    if not validate_image_proportions(
        image_file, ratio["width"], ratio["height"]
    ):
        raise ImageInvalidFormatException(
            {
                "message": f"Image proportions are invalid. Expected {ratio['width']}:{ratio['height']} ratio."
            }
        )

    if banner.catalog_desktop_image:
        banner.catalog_desktop_image.delete()

    image = create_image(
        name=f"tag_d_{to_chpu(banner.name)}",
        object_type="banner",
        image_file=image_file,
        max_width=size["width"],
        max_height=size["height"],
    )

    banner.catalog_desktop_image = image
    banner.save()
    return banner


def set_banner_header_desktop_image(
    banner_id: int, image_file: Optional[UploadedFile] = None
) -> Banner:
    """Sets or removes the header (desktop) banner image."""
    banner = Banner.get_banner_by_pk(banner_id)

    if image_file is None:
        if banner.header_desktop_image:
            banner.header_desktop_image.delete()
        banner.header_desktop_image = None
        banner.save()
        return banner

    ratio = BANNER_IMAGE_RATIOS["header_desktop"]
    size = BANNER_IMAGE_SIZES["header_desktop"]

    if not validate_image_proportions(
        image_file, ratio["width"], ratio["height"]
    ):
        raise ImageInvalidFormatException(
            {
                "message": f"Image proportions are invalid. Expected {ratio['width']}:{ratio['height']} ratio."
            }
        )

    if banner.header_desktop_image:
        banner.header_desktop_image.delete()

    image = create_image(
        name=f"header_d_{to_chpu(banner.name)}",
        object_type="banner",
        image_file=image_file,
        max_width=size["width"],
        max_height=size["height"],
    )

    banner.header_desktop_image = image
    banner.save()
    return banner
