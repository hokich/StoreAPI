from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from images.views import LocalImageByUrl


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/v1/",
        include(
            [
                path("store/", include("store.urls")),
                path("search/", include("search.urls")),
                path("banners/", include("banners.urls")),
                path("web-pages/", include("web_pages.urls")),
                path("customer/", include("customer.urls")),
                path("blog/", include("blog.urls")),
                path("short-links/", include("short_links.urls")),
            ]
        ),
    ),
    path(
        "editorjs/image_by_url/",
        LocalImageByUrl.as_view(),
        name="editorjs_image_by_url",
    ),
    path("editorjs/", include("django_editorjs_fields.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
