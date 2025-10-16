from django.test import TestCase

from ranking_index.models import RankingIndex
from ranking_index.services import create_ranking_index


class CreateRankingIndexTests(TestCase):
    def test_create_ranking_index(self) -> None:
        """Test creating a ranking index."""
        index_item = create_ranking_index()
        self.assertIsInstance(index_item, RankingIndex)
        self.assertIsNotNone(index_item.pk)
        self.assertEqual(index_item.index, 0)
