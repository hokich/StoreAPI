from django.utils import timezone

from tags_importers.models import TagImporter


def activating_importers() -> None:
    """Activates tag importers whose active period has started."""
    date_now = timezone.now()
    importers = TagImporter.objects.filter(
        date_start__lte=date_now, date_end__gt=date_now, active=False
    )
    for importer in importers:
        importer.activate()


def deactivating_importers() -> None:
    """Deactivates tag importers whose active period has ended."""
    date_now = timezone.now()
    importers = TagImporter.objects.exclude(
        date_start__lte=date_now, date_end__gt=date_now
    ).filter(active=True)
    for importer in importers:
        importer.deactivate()
