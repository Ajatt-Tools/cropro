# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import Optional, List, NamedTuple

from anki.collection import Collection
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
    def __init__(self):
        self._col: Optional[Collection] = None
        self._name: Optional[str] = None

    @property
    def col(self):
        return self._col

    @property
    def name(self):
        return self._name if self._col else None

    @staticmethod
    def col_name_and_id() -> NameId:
        return NameId("Whole collection", -1)

    @staticmethod
    def _load(name: str) -> Collection:
        return Collection(os.path.join(mw.pm.base, name, 'collection.anki2'))

    @property
    def is_opened(self) -> bool:
        return self._col is not None

    def close(self):
        if self.is_opened:
            self._col.close()
            self._name = self._col = None

    def open(self, name: str) -> None:
        self.close()
        self._col = self._load(name)
        self._name = name

    def deck_names_and_ids(self) -> list[NameId]:
        return sorted_decks_and_ids(self._col)

    def find_notes(self, deck: NameId, filter_text: str):
        if deck == self.col_name_and_id():
            return self._col.find_notes(query=filter_text)
        else:
            return self._col.find_notes(query=f'"deck:{deck.name}" {filter_text}')

    def get_note(self, note_id):
        return self._col.get_note(note_id)
