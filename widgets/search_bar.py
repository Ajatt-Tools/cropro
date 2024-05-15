# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from types import SimpleNamespace
from typing import cast

from aqt import AnkiQt
from aqt.qt import *


try:
    from .col_search_opts import ColSearchOptions
    from .remote_search_opts import RemoteSearchOptions
    from ..remote_search import get_request_url
    from .utils import CroProComboBox, NameIdComboBox, CroProLineEdit, CroProPushButton
    from ..collection_manager import NameId
except ImportError:
    from utils import CroProComboBox, NameIdComboBox, CroProLineEdit, CroProPushButton
    from collection_manager import NameId
    from remote_search_opts import RemoteSearchOptions
    from remote_search import get_request_url
    from col_search_opts import ColSearchOptions


class CroProSearchBar(QWidget):
    """
    Shows a search bar and a submit button.
    """

    # noinspection PyArgumentList
    search_requested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._search_term_edit = CroProLineEdit()
        self._search_button = CroProPushButton("Search")
        self._setup_layout()
        self._connect_elements()

    def focus_search_edit(self) -> None:
        return self._search_term_edit.setFocus()

    def search_text(self) -> str:
        return self._search_term_edit.text().strip()

    def set_search_text(self, search_text: str) -> None:
        return self._search_term_edit.setText(search_text.strip())

    def clear_search_text(self) -> None:
        return self._search_term_edit.clear()

    def _setup_layout(self) -> None:
        self._search_term_edit.setPlaceholderText("<text to filter by>")
        layout = QHBoxLayout()
        layout.addWidget(self._search_term_edit)
        layout.addWidget(self._search_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def _connect_elements(self):
        def handle_search_requested():
            if text := self.search_text():
                # noinspection PyUnresolvedReferences
                self.search_requested.emit(text)

        qconnect(self._search_button.clicked, handle_search_requested)
        qconnect(self._search_term_edit.editingFinished, handle_search_requested)


class CroProSearchWidget(QWidget):
    """
    Search bar and search options (profile selector, deck selector, search bar, search button).
    """

    # noinspection PyArgumentList
    search_requested = pyqtSignal(str)

    def __init__(self, ankimw: AnkiQt):
        super().__init__()
        self.ankimw = ankimw
        self.opts = ColSearchOptions(ankimw)
        self.remote_opts = RemoteSearchOptions()
        self.bar = CroProSearchBar()
        self._setup_layout()
        self._connect_elements()
        self._web_mode = False
        self.setEnabled(False)  # disallow search until profiles and decks are set.

    def set_web_mode(self, is_web: bool) -> None:
        self._web_mode = is_web
        self.remote_opts.setVisible(is_web)
        self.opts.setVisible(not is_web)
        self.setEnabled(is_web or self.opts.other_profile_names_combo.count() > 0)
        self.bar.focus_search_edit()

    def clear_all(self) -> None:
        """
        Clear contents of all widgets in the search bar.
        Called when profile opens to ensure that there's no conflicting data from the previously opened profile.
        """
        self.opts.clear_combos()
        self.bar.clear_search_text()

    def _setup_layout(self) -> None:
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.bar)
        layout.addWidget(self.opts)
        layout.addWidget(self.remote_opts)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.bar.focus_search_edit()

    def get_request_args(self, min_length: int, max_length: int) -> dict[str, str]:
        assert self._web_mode, "Web mode must be enabled."
        args = {}
        widgets = (
            self.remote_opts.sort_combo,
            self.remote_opts.category_combo,
            self.remote_opts.jlpt_level_combo,
            self.remote_opts.wanikani_level_combo,
        )
        if keyword := self.bar.search_text():
            args["keyword"] = keyword
            for widget in widgets:
                if param := widget.currentData().http_arg:
                    args[widget.key] = param
            if min_length > 0:
                args["min_length"] = min_length
            if max_length > 0:
                args["max_length"] = max_length
        return args

    def _connect_elements(self):
        def handle_search_requested():
            if text := self.bar.search_text():
                # noinspection PyUnresolvedReferences
                self.search_requested.emit(text)

        qconnect(self.opts.selected_deck_changed, handle_search_requested)
        qconnect(self.bar.search_requested, handle_search_requested)
        qconnect(self.opts.selected_profile_changed, lambda row_idx: self.setEnabled(row_idx >= 0 or self._web_mode))


# Debug
##########################################################################


def on_search_requested(text: str):
    print(text)


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_bar = CroProSearchWidget(cast(AnkiQt, SimpleNamespace(pm=SimpleNamespace(name="Dummy"))))
        self.initUI()
        qconnect(self.search_bar.search_requested, on_search_requested)
        # self.search_bar.set_profile_names(["User 1", "subs2srs", "dumpster"])
        # self.search_bar.set_decks([NameId("History", 1), NameId("Math", 2)])

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
