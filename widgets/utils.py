# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Iterable

from aqt.qt import *

from ..collection_manager import NameId

WIDGET_MIN_HEIGHT = 29
COMBO_MIN_WIDTH = 120


class CroProPushButton(QPushButton):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setMinimumHeight(WIDGET_MIN_HEIGHT)


class CroProLineEdit(QLineEdit):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setMinimumHeight(WIDGET_MIN_HEIGHT)


class SpinBox(QSpinBox):
    def __init__(self, min_val: int, max_val: int, step: int, value: int):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.setValue(value)


class ProfileNameLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        font = QFont()
        font.setBold(True)
        self.setFont(font)


class CroProComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaximumHeight(WIDGET_MIN_HEIGHT)
        self.setMinimumWidth(COMBO_MIN_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def all_items(self) -> Iterable[str]:
        """Returns an iterable of all items stored in the combo box."""
        for i in range(self.count()):
            yield self.itemText(i)


class DeckCombo(CroProComboBox):
    def set_decks(self, decks: Iterable[NameId]):
        self.clear()
        for deck_name, deck_id in decks:
            self.addItem(deck_name, deck_id)

    def current_deck(self) -> NameId:
        return NameId(self.currentText(), self.currentData())
