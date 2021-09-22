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

from typing import Optional
from anki.cards import Card
from aqt import AnkiQt, QDialog
from aqt.browser.previewer import Previewer


class CroProPreviewer(Previewer):
    def __init__(self, parent: QDialog, mw: AnkiQt):
        super().__init__(parent=parent, mw=mw, on_close=lambda: None)
        self.otherCol = parent.otherProfileCollection

    def card(self) -> Optional[Card]:
        selected_note_ids = self._parent.getSelectedNoteIDs()
        note = self.otherCol.getNote(selected_note_ids[0])
        note_cards = note.cards()
        return note_cards[0]

    def card_changed(self) -> bool:
        return False

    def open(self):
        self.mw.col, self.otherCol = self.otherCol, self.mw.col
        super().open()
        self.mw.col, self.otherCol = self.otherCol, self.mw.col

    def render_card(self):
        self._render_scheduled()
