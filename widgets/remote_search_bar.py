# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import dataclasses
from collections.abc import Sequence

from aqt.qt import *

try:
    from ..remote_search import get_request_url
    from .utils import CroProComboBox, CroProLineEdit, CroProPushButton, CroProSpinBox
except ImportError:
    from utils import CroProComboBox, CroProLineEdit, CroProPushButton, CroProSpinBox
    from remote_search import get_request_url


@dataclasses.dataclass
class RemoteComboBoxItem:
    http_arg: Union[str, int, None]
    visible_name: str = ""

    def __post_init__(self):
        self.visible_name = (self.visible_name or str(self.http_arg)).capitalize()


def new_combo_box(add_items: Sequence[Union[RemoteComboBoxItem, str]], key: str):
    b = CroProComboBox(key=key)
    for item in add_items:
        if not isinstance(item, RemoteComboBoxItem):
            item = RemoteComboBoxItem(item)
        b.addItem(item.visible_name, item)
    return b


class RemoteSearchBar(QWidget):
    """
    Search bar for https://docs.immersionkit.com/public%20api/search/
    """

    # noinspection PyArgumentList
    search_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._keyword_edit = CroProLineEdit()  # keyword
        self._category_combo = new_combo_box(
            [
                RemoteComboBoxItem(None, "all"),
                "anime",
                "drama",
                "games",
                "literature",
            ],
            key="category",
        )
        self._sort_combo = new_combo_box(
            [
                RemoteComboBoxItem(None, "none"),
                "shortness",
                "longness",
            ],
            key="sort",
        )
        self._jlpt_level_combo = new_combo_box(
            [
                RemoteComboBoxItem(None, "all"),
                *map(str, range(1, 6)),
            ],
            key="jlpt",
        )

        self._search_button = CroProPushButton("Search")
        self._setup_layout()
        self._connect_elements()

    def clear_search_text(self) -> None:
        return self._keyword_edit.clear()

    @property
    def category_combo(self) -> QComboBox:
        return self._category_combo

    @property
    def sort_combo(self) -> QComboBox:
        return self._sort_combo

    @property
    def jlpt_level_combo(self) -> QComboBox:
        return self._jlpt_level_combo

    def search_text(self) -> str:
        return self._keyword_edit.text().strip()

    def get_request_args(self) -> dict[str, str]:
        args = {}
        if keyword := self.search_text():
            args["keyword"] = keyword
            for widget in (self._sort_combo, self._category_combo, self._jlpt_level_combo):
                if param := widget.currentData().http_arg:
                    args[widget.key] = param
        return args

    def get_request_url(self) -> str:
        return get_request_url(self.get_request_args())

    def set_focus(self):
        self._keyword_edit.setFocus()

    def _setup_layout(self) -> None:
        self.setLayout(layout := QVBoxLayout())
        layout.addLayout(self._make_search_settings_box())
        layout.addLayout(self._make_filter_row())
        self._keyword_edit.setPlaceholderText("<text to search the Web>")
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.set_focus()

    def _make_search_settings_box(self) -> QLayout:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self._category_combo)
        layout.addWidget(QLabel("Sort:"))
        layout.addWidget(self._sort_combo)
        layout.addWidget(QLabel("JLPT:"))
        layout.addWidget(self._jlpt_level_combo)
        return layout

    def _make_filter_row(self) -> QLayout:
        layout = QHBoxLayout()
        layout.addWidget(self._keyword_edit)
        layout.addWidget(self._search_button)
        return layout

    def _connect_elements(self):
        def handle_search_requested():
            if self.get_request_url():
                # noinspection PyUnresolvedReferences
                self.search_requested.emit(self.search_text())

        qconnect(self._search_button.clicked, handle_search_requested)
        qconnect(self._keyword_edit.editingFinished, handle_search_requested)


# Debug
##########################################################################


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_bar = RemoteSearchBar()
        self.initUI()
        qconnect(self.search_bar.search_requested, self.on_search_requested)

    def on_search_requested(self, text: str):
        print(f"Search: {text}")
        print(f"GET url: {self.search_bar.get_request_url()}")

    def initUI(self):
        self.setMinimumSize(640, 480)
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.search_bar)
        layout.addStretch(1)


def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    main()
