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

from typing import Optional, List

from anki.cards import Card
from anki.collection import Collection
from aqt import AnkiQt, QDialog
from aqt.browser.previewer import Previewer


class CroProPreviewer(Previewer):
    def __init__(self, parent: QDialog, mw: AnkiQt, col: Collection, selected_nids: List):
        super().__init__(parent=parent, mw=mw, on_close=lambda: None)
        self.current_col = self.mw.col
        self.mw.col = col
        self.cards = self.get_cards(selected_nids)
        self.idx = 0

    def get_cards(self, selected_nids: List) -> List[Card]:
        cards = []
        for nid in selected_nids:
            for card in self.mw.col.getNote(nid).cards():
                cards.append(card)
        return cards

    def card(self) -> Optional[Card]:
        self.idx = inc if (inc := self.idx + 1) < len(self.cards) else 0
        return self.cards[self.idx]

    def card_changed(self) -> bool:
        return False

    def reject(self):
        self.mw.col = self.current_col
        super(CroProPreviewer, self).reject()
