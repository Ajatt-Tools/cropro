from typing import Optional
from anki.cards import Card
from aqt import AnkiQt, QDialog
from aqt.previewer import Previewer


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
