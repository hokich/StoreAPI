from typing import TypedDict, cast

from django.db import models


class CounterDict(TypedDict):
    first_week: int
    second_week: int
    third_week: int


def get_default_counter_dict() -> CounterDict:
    return {"first_week": 0, "second_week": 0, "third_week": 0}


class RankingIndex(models.Model):
    """Stores a rolling 3-week ranking index and its weekly counters."""

    _index = models.DecimalField(
        "Index", max_digits=15, decimal_places=5, default=0
    )
    _index_counter = models.JSONField(
        "Counter", default=get_default_counter_dict, blank=True
    )

    @property
    def index(self) -> float:
        """Returns the index as a float."""
        return float(self._index)

    def index_counter_increment(self, count: int = 1) -> None:
        """Increments the current (first week) counter by the given count."""
        _index_counter: CounterDict = cast(CounterDict, self._index_counter)
        _index_counter["first_week"] += count
        self._index_counter = _index_counter
        self.save()

    def update_index(self) -> None:
        """Recomputes the index using weighted weekly counters and rotates windows."""
        _index_counter: CounterDict = cast(CounterDict, self._index_counter)
        self._index = (
            _index_counter["first_week"] * 0.5
            + _index_counter["second_week"] * 0.3
            + _index_counter["third_week"] * 0.2
        )
        self.save()
        self._update_index_counters()

    def _update_index_counters(self) -> None:
        """Shifts weekly counters: first → second, second → third, resets first."""
        _index_counter: CounterDict = cast(CounterDict, self._index_counter)
        _index_counter["third_week"] = _index_counter["second_week"]
        _index_counter["second_week"] = _index_counter["first_week"]
        _index_counter["first_week"] = 0
        self._index_counter = _index_counter
        self.save()
