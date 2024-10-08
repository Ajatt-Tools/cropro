# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import dataclasses
from collections.abc import Sequence

from aqt.qt import *

from .utils import CroProComboBox


@dataclasses.dataclass
class RemoteComboBoxItem:
    http_arg: Union[str, int, None]
    visible_name: str = ""

    def __post_init__(self):
        self.visible_name = (self.visible_name or str(self.http_arg)).capitalize()


def new_combo_box(add_items: Sequence[Union[RemoteComboBoxItem, str]], key: str) -> CroProComboBox:
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
        self._wanikani_level_combo = new_combo_box(
            [
                RemoteComboBoxItem(None, "all"),
                *map(str, range(1, 61)),
            ],
            key="wanikani",
        )
        self._setup_layout()

    def _setup_layout(self) -> None:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self._category_combo)
        layout.addWidget(QLabel("Sort:"))
        layout.addWidget(self._sort_combo)
        layout.addWidget(QLabel("JLPT:"))
        layout.addWidget(self._jlpt_level_combo)
        layout.addWidget(QLabel("WaniKani:"))
        layout.addWidget(self._wanikani_level_combo)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

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
