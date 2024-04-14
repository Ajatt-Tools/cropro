# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable
from collections.abc import Sequence

from aqt.qt import *

try:
    from ..collection_manager import NameId
except ImportError:
    from collection_manager import NameId

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


class CroProSpinBox(QSpinBox):
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
    def __init__(self, parent=None, key: str = None):
        super().__init__(parent)
        self.key = key  # can be used to describe itself
        self.setMaximumHeight(WIDGET_MIN_HEIGHT)
        self.setMinimumWidth(COMBO_MIN_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_texts(self, texts: Sequence[str]):
        self.clear()
        self.addItems(texts)

    def all_texts(self) -> Iterable[str]:
        """Returns an iterable of all items stored in the combo box."""
        for i in range(self.count()):
            yield self.itemText(i)


class NameIdComboBox(CroProComboBox):
    def set_items(self, items: Iterable[NameId]):
        self.clear()
        for item_name, item_id in items:
            self.addItem(item_name, item_id)

    def current_item(self) -> NameId:
        return NameId(self.currentText(), self.currentData())
