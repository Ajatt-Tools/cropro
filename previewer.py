# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import itertools
from typing import Optional, Iterable

from anki.cards import Card
from anki.collection import Collection
from anki.notes import Note
from aqt import AnkiQt, QDialog
from aqt.browser.previewer import Previewer


def get_cards(selected_notes: Iterable[Note]) -> list[Card]:
    return list(itertools.chain(*map(Note.cards, selected_notes)))


class CroProPreviewer(Previewer):
    def __init__(self, parent: QDialog, mw: AnkiQt, col: Collection, selected_notes: Iterable[Note]):
        super().__init__(parent=parent, mw=mw, on_close=lambda: None)
        self.current_col = self.mw.col
        self.mw.col = col
        self.cards = get_cards(selected_notes)
        self.idx = 0

    def card(self) -> Optional[Card]:
        self.idx = inc if (inc := self.idx + 1) < len(self.cards) else 0
        return self.cards[self.idx]

    def card_changed(self) -> bool:
        return False

    def done(self, result_code):
        self.mw.col = self.current_col
        return super().done(result_code)
