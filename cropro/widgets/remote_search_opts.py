# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import dataclasses
import enum
from collections.abc import Sequence

from aqt.qt import *

from .utils import CroProComboBox


@dataclasses.dataclass
class RemoteComboBoxItem:
    http_arg: Union[str, int, None]
    visible_name: str = ""

    def __post_init__(self):
        self.visible_name = (self.visible_name or str(self.http_arg)).capitalize()


class RemoteNotesSortMethod(enum.Enum):
    none = None
    len_desc = "sentence_length:desc"
    len_asc = "sentence_length:asc"


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

    def __init__(self) -> None:
        # https://apiv2.immersionkit.com/openapi.json
        super().__init__()
        self._category_combo = new_combo_box(
            [
                RemoteComboBoxItem(None, "all"),
                "anime",
                "drama",
                "games",
                "literature",
                "news",
            ],
            key="category",
        )
        self._sort_combo = new_combo_box(
            [
                RemoteComboBoxItem(RemoteNotesSortMethod.none.value, "none"),
                RemoteComboBoxItem(RemoteNotesSortMethod.len_desc.value, "Longer"),
                RemoteComboBoxItem(RemoteNotesSortMethod.len_asc.value, "Shorter"),
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
            key="wk",
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
    def category_combo(self) -> CroProComboBox:
        return self._category_combo

    @property
    def sort_combo(self) -> CroProComboBox:
        return self._sort_combo

    def sort_method(self) -> RemoteNotesSortMethod:
        return RemoteNotesSortMethod(self._sort_combo.currentData().http_arg)

    @property
    def jlpt_level_combo(self) -> CroProComboBox:
        return self._jlpt_level_combo

    @property
    def wanikani_level_combo(self) -> CroProComboBox:
        return self._wanikani_level_combo
