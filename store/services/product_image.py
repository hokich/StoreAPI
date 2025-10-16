from django.core.files.uploadedfile import UploadedFile

from images.services import create_image

from ..models import Product, ProductImage


def create_product_image(
    product_id: int, image_file: UploadedFile, is_main: bool = False
) -> ProductImage:
    """Creates a product image in three sizes: thumbnail, sd, and hd."""
    product = Product.get_product_by_pk(product_id)

    image_thumb = create_image(
        product.slug, "product", image_file, product.name, 768, 768
    )

    image_sd = create_image(
        product.slug, "product", image_file, product.name, 1024, 1024
    )

    image_hd = create_image(
        product.slug, "product", image_file, product.name, 1920, 1920
    )

    return ProductImage.objects.create(
        product=product,
        thumb_image=image_thumb,
        sd_image=image_sd,
        hd_image=image_hd,
        is_main=is_main,
    )


def delete_product_image(product_image_id: int) -> None:
    """Deletes a product image."""
    product_image = ProductImage.get_product_image_by_pk(product_image_id)

    product_image.thumb_image.delete()
    product_image.sd_image.delete()
    product_image.hd_image.delete()
    product_image.delete()


def set_main_product_image(product_image_id: int) -> None:
    """Sets a product image as the main image."""
    product_image = ProductImage.get_product_image_by_pk(product_image_id)

    ProductImage.objects.filter(product=product_image.product).update(
        is_main=False
    )

    product_image.is_main = True
    product_image.save()
