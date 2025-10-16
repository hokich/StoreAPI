import json
import logging
import os
from datetime import datetime
from secrets import token_urlsafe
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.http import JsonResponse
from django_editorjs_fields.config import (
    IMAGE_UPLOAD_PATH,
    IMAGE_UPLOAD_PATH_DATE,
)
from django_editorjs_fields.utils import storage
from django_editorjs_fields.views import ImageByUrl
from rest_framework.request import Request as RequestDRF


LOGGER = logging.getLogger("django_editorjs_fields")


class LocalImageByUrl(ImageByUrl):
    """Uploads an image by a given URL and returns its storage URL."""

    def post(
        self, request: RequestDRF, *args: Any, **kwargs: Any
    ) -> JsonResponse:
        """Downloads an image from the provided URL, validates content type, stores it, and returns the file URL."""
        try:
            body = json.loads(request.body.decode())
            url = body.get("url")

            if not url:
                return JsonResponse(
                    {"success": 0, "message": "No URL provided."}
                )

            req = Request(
                url,
                headers={
                    "User-Agent": request.META.get(
                        "HTTP_USER_AGENT", "Mozilla/5.0"
                    )
                },
            )
            with urlopen(req, timeout=10) as response:
                content_type = response.info().get_content_type()
                allowed_types = [
                    "image/jpeg",
                    "image/jpg",
                    "image/pjpeg",
                    "image/x-png",
                    "image/png",
                    "image/webp",
                    "image/gif",
                ]
                if content_type not in allowed_types:
                    return JsonResponse(
                        {
                            "success": 0,
                            "message": "You can only upload images.",
                        }
                    )

                extension = content_type.split("/")[-1]
                raw_data = response.read()

            filename = f"{token_urlsafe(8)}.{extension}"

            upload_path = IMAGE_UPLOAD_PATH
            if IMAGE_UPLOAD_PATH_DATE:
                upload_path += datetime.now().strftime(IMAGE_UPLOAD_PATH_DATE)

            full_path = os.path.join(upload_path, filename)

            saved_path = storage.save(full_path, ContentFile(raw_data))
            file_url = storage.url(saved_path)

            return JsonResponse({"success": 1, "file": {"url": file_url}})
        except (HTTPError, URLError) as e:
            LOGGER.error(f"Download failed: {e}")
            return JsonResponse({"success": 0, "message": str(e)})
        except Exception as e:
            LOGGER.error(f"Internal error: {e}")
            return JsonResponse(
                {"success": 0, "message": "Internal server error."}
            )
