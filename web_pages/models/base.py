from abc import ABCMeta, abstractmethod
from typing import Optional

from django.db import models
from django_editorjs_fields import EditorJsJSONField

from utils.exceptions import ObjectDoesNotExistException


class AbstractModelMeta(ABCMeta, type(models.Model)):  # type: ignore
    """Custom metaclass combining Django's Model metaclass and ABCMeta."""

    pass


class BasePage(models.Model, metaclass=AbstractModelMeta):
    """Abstract base model for SEO pages with meta fields and editable content."""

    _h1 = models.CharField("H1", max_length=255, blank=True, null=True)
    _title = models.CharField("Title", max_length=255, blank=True, null=True)
    _description = models.TextField("Description", blank=True, null=True)
    head = models.TextField("Head", null=True, blank=True)
    # Example robots tag:
    # (1, '<meta name="robots" content="all" />'),
    # <meta name="robots" content="noindex, nofollow" />
    robots = models.CharField("Robots", max_length=255, null=True, blank=True)

    _rich_content = EditorJsJSONField(
        plugins=[
            "@editorjs/paragraph",
            "@editorjs/header",
            "@editorjs/image",
            "@editorjs/link",
            "@editorjs/list",
        ],
        tools={
            "Image": {
                "class": "ImageTool",
                "inlineToolbar": True,
                "config": {
                    "endpoints": {
                        "byFile": "/editorjs/image_upload/",
                        "byUrl": "/editorjs/image_by_url/",
                    }
                },
            },
            "Header": {
                "class": "Header",
                "inlineToolbar": True,
                "config": {
                    "placeholder": "Enter heading",
                    "levels": [1, 2, 3, 4],
                    "defaultLevel": 2,
                },
            },
            "List": {
                "class": "List",
                "inlineToolbar": True,
            },
        },
        placeholder="Enter text",
        i18n={
            "messages": {
                "blockTunes": {
                    "delete": {"Delete": "Delete"},
                    "moveUp": {"Move up": "Move up"},
                    "moveDown": {"Move down": "Move down"},
                }
            },
        },
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True

    @property
    @abstractmethod
    def title(self) -> str:
        """Abstract property for the page title."""
        pass

    @property
    @abstractmethod
    def h1(self) -> str:
        """Abstract property for the main page header."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Abstract property for the page description."""
        pass

    @property
    def rich_content(self) -> Optional[dict]:
        """Returns the rich content if available and contains blocks."""
        if not self._rich_content:
            return None
        if not self._rich_content.get("blocks"):
            return None
        return self._rich_content

    @rich_content.setter
    def rich_content(self, value: Optional[dict] = None) -> None:
        """Sets the rich content field."""
        self._rich_content = value

    @classmethod
    def get_page_by_pk(cls, pk: int) -> "BasePage":
        """Finds a page by primary key or raises ObjectDoesNotExistException."""
        try:
            return cls.objects.get(pk=pk)
        except cls.DoesNotExist:
            raise ObjectDoesNotExistException(
                {"message": f"Page with pk={pk} does not exist"}
            )
