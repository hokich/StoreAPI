from .models import RankingIndex


def create_ranking_index() -> RankingIndex:
    """Creates and returns a new ranking index instance."""
    return RankingIndex.objects.create()
