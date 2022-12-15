# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import Optional, NamedTuple

from anki.collection import Collection
from anki.notes import NoteId
from aqt import mw


class NameId(NamedTuple):
    name: str
    id: int

    @classmethod
    def none_type(cls) -> 'NameId':
        return cls('None (create new if needed)', -1)


def sorted_decks_and_ids(col: Collection) -> list[NameId]:
    return sorted(NameId(deck.name, deck.id) for deck in col.decks.all_names_and_ids())


def get_other_profile_names() -> list[str]:
    profiles = mw.pm.profiles()
    profiles.remove(mw.pm.name)
    return profiles


class CollectionManager:
    """This class keeps other collections (profiles) open and can switch between them."""

    def __init__(self):
        self._opened_cols: dict[str, Collection] = {}
        self._current_name: Optional[str] = None

    @property
    def name(self) -> Optional[str]:
        if not self.is_opened:
            raise RuntimeError("Collection vanished or was never opened.")
        return self._current_name

    @property
    def col(self):
        return self._opened_cols[self.name]

    @property
    def media_dir(self):
        return os.path.join(os.path.dirname(self.col.path), 'collection.media')

    @staticmethod
    def col_name_and_id() -> NameId:
        return NameId("Whole collection", -1)

    @property
    def is_opened(self) -> bool:
        return (self._current_name is not None) and (self._current_name in self._opened_cols)

    def close(self):
        if self.is_opened:
            self._opened_cols.pop(self._current_name).close()
            self._current_name = None

    def close_all(self):
        for col in self._opened_cols.values():
            col.close()
        self._current_name = None
        self._opened_cols.clear()

    def open(self, name: str) -> None:
        if name not in self._opened_cols:
            self._opened_cols[name] = Collection(os.path.join(mw.pm.base, name, 'collection.anki2'))
        self._current_name = name

    def deck_names_and_ids(self) -> list[NameId]:
        return sorted_decks_and_ids(self.col)

    def find_notes(self, deck: NameId, filter_text: str):
        if deck == self.col_name_and_id():
            return self.col.find_notes(query=filter_text)
        else:
            return self.col.find_notes(query=f'"deck:{deck.name}" {filter_text}')

    def get_note(self, note_id: NoteId):
        return self.col.get_note(note_id)
