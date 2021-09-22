# -*- coding: utf-8 -*-

# Cross-Profile Search and Import add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.

import os
from typing import Optional, List

from anki.collection import Collection
from anki.decks import DeckNameId
from aqt import mw


def sorted_decks(col: Collection) -> List[DeckNameId]:
    return sorted(col.decks.all_names_and_ids(), key=lambda deck: deck.name)


class CollectionManager:
    def __init__(self):
        self.col: Optional[Collection] = None

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

    @property
    def decks(self):
        return sorted_decks(self.col)

    def find_notes(self, deck_id: int, filter_text: str):
        return self.col.find_notes(query=f'did:{deck_id} {filter_text}')

    def get_note(self, note_id):
        return self.col.get_note(note_id)
