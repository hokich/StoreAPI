import random
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PilImage
from PIL import ImageDraw


ColorType = tuple[int, int, int]


def _random_color() -> ColorType:
    """Generates a random RGB color."""
    return (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


def _create_gradient(
    width: int,
    height: int,
    start_color: ColorType,
    end_color: ColorType,
) -> PilImage.Image:
    """Creates an image with a vertical linear gradient."""
    base = PilImage.new("RGB", (width, height), start_color)
    top = PilImage.new("RGB", (width, height), end_color)
    mask = PilImage.new("L", (width, height))

    draw = ImageDraw.Draw(mask)
    for i in range(height):
        draw.line((0, i, width, i), fill=255 * i // height)

    base.paste(top, (0, 0), mask)
    return base


def create_test_image() -> SimpleUploadedFile:
    """Creates a test image with a random gradient and returns it as a SimpleUploadedFile."""
    width, height = 2000, 1500
    start_color = _random_color()
    end_color = _random_color()

    img = _create_gradient(width, height, start_color, end_color)
    img_io = BytesIO()
    img.save(img_io, format="JPEG")
    img_io.seek(0)

    return SimpleUploadedFile(
        "test.jpg", img_io.read(), content_type="image/jpeg"
    )
