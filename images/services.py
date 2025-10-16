import uuid
from io import BytesIO
from typing import Optional

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from PIL import Image as PilImage

from .models import Image


def create_image(
    name: str,
    object_type: str,
    image_file: UploadedFile,
    alt_text: Optional[str] = None,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
) -> Image:
    """
    Creates an Image object and saves it to the database.

    :param name: Image name
    :param object_type: Type of object the image belongs to
    :param image_file: Uploaded image file
    :param alt_text: Alt text for the image
    :param max_width: Maximum image width
    :param max_height: Maximum image height

    :return: Created Image instance
    """
    # Open the uploaded image using Pillow
    img = PilImage.open(image_file)

    # Resize the image while maintaining proportions
    if max_width and max_height:
        img.thumbnail((max_width, max_height), PilImage.Resampling.LANCZOS)

    # Detect original image format
    original_format = img.format or ""

    # Handle transparency for PNG and GIF images
    if img.mode in ("RGBA", "LA") or (
        img.mode == "P" and "transparency" in img.info
    ):
        # Keep transparency
        pass
    else:
        # Convert to RGB if no alpha channel is present
        if img.mode != "RGB":
            img = img.convert("RGB")

    # Save the processed image
    img_io = BytesIO()
    img.save(img_io, format=original_format)
    file_name = f"{name}_{uuid.uuid4().hex}"
    now = timezone.now()
    file_extension = original_format.lower()
    file_path = f"images/{object_type}/{now.year}/{now.month}/{file_name}.{file_extension}"
    img_content = ContentFile(img_io.getvalue(), name=file_path)

    image_instance = Image(alt=alt_text)
    image_instance.image.save(file_path, img_content)
    image_instance.save()
    return image_instance


def validate_image_proportions(
    image_file: UploadedFile, target_width: int, target_height: int
) -> bool:
    """
    Validates whether the uploaded image matches the expected width-to-height ratio.

    :param image_file: Uploaded image file
    :param target_width: Expected width ratio
    :param target_height: Expected height ratio

    :return: True if proportions match, otherwise False
    """
    with PilImage.open(image_file) as img:
        width, height = img.size
        return width * target_height == height * target_width
