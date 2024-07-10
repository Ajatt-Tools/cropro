# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from collections.abc import Iterable, Sequence
from typing import NamedTuple, Optional

from anki.collection import Collection
from anki.notes import NoteId
from aqt import mw


class NameId(NamedTuple):
    name: str
    id: int


NO_MODEL = NameId("None (create new if needed)", -1)
WHOLE_COLLECTION = NameId("Whole collection", -1)


def sorted_decks_and_ids(col: Collection) -> list[NameId]:
    return sorted(NameId(deck.name, deck.id) for deck in col.decks.all_names_and_ids())


def note_type_names_and_ids(col: Collection) -> Iterable[NameId]:
    return (NameId(note_type.name, note_type.id) for note_type in col.models.all_names_and_ids())


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
    def col(self) -> Collection:
        ret = self._opened_cols[self.name]
        assert ret is not mw.col, "The other collection can't be the same as the current one."
        return ret

    @property
    def media_dir(self):
        return self.col.media.dir()

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

    def open_collection(self, name: str) -> None:
        assert name, "Name can't be empty."
        assert name != mw.col.name(), "Can't open the current collection as other collection."
        if name not in self._opened_cols:
            col_file_path = os.path.join(mw.pm.base, name, "collection.anki2")
            assert os.path.isfile(col_file_path), "Collection file must exist."
            self._opened_cols[name] = Collection(col_file_path)
        self._current_name = name

    def deck_names_and_ids(self) -> list[NameId]:
        return sorted_decks_and_ids(self.col)

    def find_notes(self, deck: NameId, filter_text: str) -> Sequence[NoteId]:
        if deck == WHOLE_COLLECTION:
            return self.col.find_notes(query=filter_text)
        else:
            return self.col.find_notes(query=f'"deck:{deck.name}" {filter_text}')

    def get_note(self, note_id: NoteId):
        assert note_id > 0, "Note ID must be greater than 0."
        return self.col.get_note(note_id)
