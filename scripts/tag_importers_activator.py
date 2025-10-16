from tags_importers.services import (
    activating_importers,
    deactivating_importers,
)


def run() -> None:
    """Deactivates and then reactivates all tag importers."""
    deactivating_importers()
    activating_importers()
