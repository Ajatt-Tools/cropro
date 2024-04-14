# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from .item_box import ItemBox


class ItemEditBox(QGroupBox):
    def __init__(self, title: str, initial_values: list[str]):
        super().__init__()
        self.setCheckable(False)
        self.setTitle(title)
        self._hidden_fields_edit = QLineEdit()
        self._hidden_fields_edit.setPlaceholderText("New item")
        self._hidden_fields_box = ItemBox(parent=self, initial_values=initial_values)
        self._setup_ui()
        self._connect_items()

    def _setup_ui(self):
        layout = QGridLayout()
        layout.addWidget(QLabel("Hide fields matching"), 1, 1, 1, 1)
        layout.addWidget(self._hidden_fields_edit, 1, 2, 1, 1)
        layout.addWidget(self._hidden_fields_box, 2, 1, 1, 2)
        self.setLayout(layout)

    def _connect_items(self):
        qconnect(
            self._hidden_fields_edit.textChanged, lambda: self._hidden_fields_box.new_item(self._hidden_fields_edit)
        )

    def setToolTip(self, text: str) -> None:
        return self._hidden_fields_edit.setToolTip(text)

    def values(self) -> list[str]:
        return self._hidden_fields_box.values()
