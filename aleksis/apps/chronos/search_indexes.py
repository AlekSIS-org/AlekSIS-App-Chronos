from aleksis.core.util.search import Indexable, SearchIndex

from .models import Room


class RoomIndex(SearchIndex, Indexable):
    """Haystack index for searching rooms."""

    model = Room
