from search.services.client import MeiliSearchClient


def run() -> None:
    """Reindexes all catalogs and products in MeiliSearch."""
    meili_client = MeiliSearchClient()
    meili_client.index_catalogs()
    meili_client.index_all_products()
