# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import Optional, List, NamedTuple

from anki.collection import Collection
from aqt import mw


class NameId(NamedTuple):
    name: str
    id: int


def sorted_decks_and_ids(col: Collection) -> List[NameId]:
    return sorted(NameId(deck.name, deck.id) for deck in col.decks.all_names_and_ids())


class CollectionManager:
    def __init__(self):
        self.col: Optional[Collection] = None

    @staticmethod
    def col_name_and_id() -> NameId:
        return NameId("Whole collection", -1)

    @staticmethod
    def _load(name: str) -> Collection:
        return Collection(os.path.join(mw.pm.base, name, 'collection.anki2'))

    @property
    def opened(self) -> bool:
        return self.col is not None

    def close(self):
        if self.opened:
            self.col.close()
            self.col = None

    def open(self, name: str) -> None:
        self.close()
        self.col = self._load(name)

    def deck_names_and_ids(self) -> List[NameId]:
        return sorted_decks_and_ids(self.col)

    def find_notes(self, deck: NameId, filter_text: str):
        if deck == self.col_name_and_id():
            return self.col.find_notes(query=filter_text)
        else:
            return self.col.find_notes(query=f'"deck:{deck.name}" {filter_text}')

    def get_note(self, note_id):
        return self.col.getNote(note_id)
