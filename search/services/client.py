import json
from typing import Optional, Union

from django.conf import settings
from djangorestframework_camel_case.util import camelize
from meilisearch import Client

from search.services.utils import convert_layout_mixed
from store.models import Catalog, Product
from store.serializers.catalog import CatalogSerializerForSearchIndex
from store.serializers.product import ProductSerializerForSearchIndex


class MeiliSearchClient:
    """Thin wrapper around MeiliSearch client for indexing/searching products and catalogs."""

    def __init__(self) -> None:
        """Initializes a MeiliSearch client using settings."""
        self.client = Client(
            f"http://{settings.MEILISEARCH_HOST}:{settings.MEILISEARCH_PORT}",
            settings.MEILISEARCH_API_TOKEN,
        )

    def index_all_products(self) -> None:
        """Indexes all products with appropriate index settings and batched uploads."""
        index = self.client.index("products")
        index.update_typo_tolerance({"disableOnAttributes": ["sku"]})
        index.update_displayed_attributes(
            [
                "id",
                "sku",
                "name",
                "slug",
                "price",
                "discountedPrice",
                "bonusesAmountDict",
                "images",
                "listing",
                "brand",
                "status",
                "tags",
                "colorTags",
                "specifications",
            ]
        )
        index.update_searchable_attributes(
            [
                "sku",
                "name",
                "description",
                "listing",
                "brand",
                "nameLatin",
                "nameCyrillic",
            ]
        )
        index.update_pagination_settings({"maxTotalHits": 10000})
        index.update_filterable_attributes(
            ["listingSlug", "brandSlug", "status", "publish"]
        )
        index.update_faceting_settings(
            {"sortFacetValuesBy": {"listingSlug": "count"}}
        )

        products = Product.objects.all()
        step = 100
        for i in range(0, products.count(), step):
            print(f"Indexing products {i}/{products.count()}")
            products_serialized = ProductSerializerForSearchIndex(
                products[i : i + step], many=True
            ).data
            if i == 0:
                print(json.dumps(camelize(products_serialized[0]), indent=2))
            index.add_documents(camelize(products_serialized))
        print("Products indexed")

    def update_all_products(self) -> None:
        """Updates product documents one-by-one (skips items without category or brand)."""
        products = Product.objects.all()
        count = products.count()
        for num, product in enumerate(products):
            print(f"{num}/{count}")
            if not product.category or not product.brand:
                continue
            self.update_data(
                "products",
                camelize(ProductSerializerForSearchIndex(product).data),
            )

    def index_catalogs(self) -> None:
        """Indexes catalogs (category/listing/collection/brand) with minimal fields."""
        index = self.client.index("catalog")
        index.update_displayed_attributes(
            ["id", "name", "slug", "image", "objectClass", "parent"]
        )
        index.update_searchable_attributes(
            ["name", "nameLatin", "nameCyrillic"]
        )
        catalogs = Catalog.objects.filter(
            object_class__in=["category", "listing", "collection", "brand"]
        )
        print("Indexing catalogs")
        index.add_documents(
            camelize(CatalogSerializerForSearchIndex(catalogs, many=True).data)
        )
        print("Catalogs indexed")

    def index_data(self, index_name: str, documents_list: list) -> None:
        """Adds a list of documents to the specified index."""
        index = self.client.index(index_name)
        index.add_documents(documents_list)

    def update_data(self, index_name: str, data: dict) -> None:
        """Updates (upserts) a single document in the specified index."""
        index = self.client.index(index_name)
        index.update_documents([data])

    def delete_data(self, index_name: str, doc_id: Union[str, int]) -> None:
        """Deletes a document by its ID from the specified index."""
        index = self.client.index(index_name)
        index.delete_document(doc_id)

    def search_products(
        self,
        query: str,
        facets_list: Optional[list] = None,
        in_stock_only: bool = False,
        attributes_to_retrieve: Optional[list[str]] = None,
        limit: int = 20,
    ) -> dict:
        """Searches products with filters/facets and optional stock constraint; retries with layout conversion if no hits."""
        index = self.client.index("products")
        filter_str = "publish = 1"
        if in_stock_only:
            filter_str += (
                " AND (status.code = IN_STOCK OR status.code = LIMITED)"
            )
        options_dict = {
            "limit": limit,
            "facets": facets_list or [],
            "filter": filter_str,
            "attributesToRetrieve": attributes_to_retrieve or ["*"],
        }
        search_result = index.search(query, options_dict)
        if not search_result["hits"]:
            query = convert_layout_mixed(query)
        search_result = index.search(query, options_dict)
        return search_result

    def search_catalog(self, query: str, limit: int = 20) -> dict:
        """Searches catalog documents; retries with layout conversion if no hits."""
        index = self.client.index("catalog")
        search_result = index.search(query, {"limit": limit})
        if not search_result["hits"]:
            query = convert_layout_mixed(query)
        search_result = index.search(query, {"limit": limit})
        return search_result

    def get_suggestions(self, query: str, count: int = 4) -> list[str]:
        """Generates next-word suggestions from product and catalog names based on the current query."""
        completed_word = query.endswith(" ")
        cleaned_query = query.lower().strip()
        query_words = cleaned_query.split()

        # Initiate searches in products and catalogs
        product_names = [
            item["name"]
            for item in self.search_products(
                " ".join(query_words), limit=1000
            )["hits"]
        ]
        catalog_names = [
            item["name"]
            for item in self.search_catalog(" ".join(query_words), limit=100)[
                "hits"
            ]
        ]

        combined_results = set(product_names + catalog_names)
        suggestions = set()

        for name in combined_results:
            name_lower = name.lower()
            words_in_name = name_lower.split()

            # Find the next word after the last entered one
            if completed_word:
                # Indices of the last query word occurrences in the name
                indexes = [
                    i
                    for i, word in enumerate(words_in_name)
                    if word in query_words
                ]
                if indexes:
                    last_index = max(indexes)
                    # Add the word following the last matched word if applicable
                    if (
                        len(indexes) == len(query_words)
                        and last_index + 1 < len(words_in_name)
                        and words_in_name[last_index + 1] not in query_words
                    ):
                        suggestions.add(words_in_name[last_index + 1])
            else:
                # For an unfinished last word
                if cleaned_query not in name_lower:
                    continue
                split_by_query = name_lower.split(cleaned_query)[1]
                left_words = split_by_query.split(" ")
                suggestions.add(query_words[-1] + left_words[0])

            if len(suggestions) >= count:
                break

        return list(suggestions)[:count]
