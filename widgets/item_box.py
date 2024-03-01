# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from ..common import CLOSE_ICON_PATH


class ItemBox(QWidget):
    """Displays tag-like labels with × icons. Pressing on the × deletes the tag."""

    class ItemButton(QPushButton):
        _close_icon = QIcon(QPixmap(CLOSE_ICON_PATH))

        def __init__(self, item_box: "ItemBox", text: str):
            super().__init__(text)
            self.item_box = item_box
            self.setStyleSheet(
                """
                QPushButton {
                    background-color: #eef0f2;
                    color: #292c31;
                    border-radius: 12px;
                    padding: 3px 6px;
                    border: 1px solid #d0d2d4;
                }
            """
            )
            self.setIcon(self._close_icon)
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            qconnect(self.clicked, lambda: self.item_box.remove_item(text))

    def __init__(self, parent: QWidget, initial_values: list[str]):
        super().__init__(parent=parent)
        self.items = dict.fromkeys(initial_values)
        self.setLayout(self._make_layout())

    def values(self) -> list[str]:
        return list(self.items)

    def _make_layout(self) -> QLayout:
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        for text in self.items:
            self._add_item(text)
        self.layout.addStretch()
        return self.layout

    def count(self) -> int:
        # The last element in the layout is a stretch.
        return self.layout.count() - 1

    def _add_item(self, text: str) -> None:
        b = self.items[text] = self.ItemButton(self, text)
        self.layout.insertWidget(self.count(), b)

    def remove_item(self, text: str) -> None:
        if widget := self.items.pop(text, None):
            widget.deleteLater()

    def new_item(self, edit: QLineEdit) -> None:
        separators = (",", " ", ";")
        if (text := edit.text()).endswith(separators):
            text = text.strip("".join(separators))
            if text and text not in self.items:
                self._add_item(text)
            edit.setText("")
