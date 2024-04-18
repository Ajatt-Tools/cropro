# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
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


class RemoteSearchOptions(QWidget):
    """
    Search options for https://docs.immersionkit.com/public%20api/search/
    """

    def __init__(self):
        super().__init__()
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
        self._wanikani_level_combo = new_combo_box([
            RemoteComboBoxItem(None, "all"),
            *map(str, range(1, 61)),
        ], key="wanikani")
        self._min_length_spinbox = CroProSpinBox(0, 200, 1, 0)
        self._max_length_spinbox = CroProSpinBox(0, 500, 1, 0)
        self._setup_layout()

    def _setup_layout(self) -> None:
        top_layout = QVBoxLayout()
        layout_row1 = QHBoxLayout()
        layout_row1.addWidget(QLabel("Category:"))
        layout_row1.addWidget(self._category_combo)
        layout_row1.addWidget(QLabel("Sort:"))
        layout_row1.addWidget(self._sort_combo)
        layout_row1.addWidget(QLabel("JLPT:"))
        layout_row1.addWidget(self._jlpt_level_combo)
        layout_row2 = QHBoxLayout()
        layout_row2.addWidget(QLabel("WaniKani:"))
        layout_row2.addWidget(self._wanikani_level_combo)
        layout_row2.addWidget(QLabel("Min. Length:"))
        layout_row2.addWidget(self._min_length_spinbox)
        layout_row2.addWidget(QLabel("Max. Length:"))
        layout_row2.addWidget(self._max_length_spinbox)
        layout_row1.setContentsMargins(0, 0, 0, 0)
        layout_row2.setContentsMargins(0, 0, 0, 0)
        top_layout.addLayout(layout_row1)
        top_layout.addLayout(layout_row2)
        self.setLayout(top_layout)

    @property
    def category_combo(self) -> QComboBox:
        return self._category_combo

    @property
    def sort_combo(self) -> QComboBox:
        return self._sort_combo

    @property
    def jlpt_level_combo(self) -> QComboBox:
        return self._jlpt_level_combo

    @property
    def wanikani_level_combo(self) -> QComboBox:
        return self._wanikani_level_combo

    @property
    def min_length_spinbox(self) -> QSpinBox:
        return self._min_length_spinbox

    @property
    def max_length_spinbox(self) -> QSpinBox:
        return self._max_length_spinbox


# Debug
##########################################################################


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_opts = RemoteSearchOptions()
        self.initUI()

    def initUI(self):
        self.setMinimumSize(640, 480)
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.search_opts)
        layout.addStretch(1)

    def hideEvent(self, event: QHideEvent):
        print(self.search_opts.category_combo.currentText())
        print(self.search_opts.sort_combo.currentText())
        print(self.search_opts.jlpt_level_combo.currentText())
        print(self.search_opts.wanikani_level_combo.currentText())
        print(self.search_opts.min_length_spinbox.value())
        print(self.search_opts.max_length_spinbox.value())


def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    main()
