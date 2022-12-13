# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

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

    def done(self, result_code):
        self.mw.col = self.current_col
        return super().done(result_code)
