# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from types import SimpleNamespace
from typing import cast

from aqt import AnkiQt
from aqt.qt import *

from ..remote_search import CroProWebSearchArgs
from .col_search_opts import ColSearchOptions
from .remote_search_opts import RemoteSearchOptions
from .utils import CroProLineEdit, CroProPushButton


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

    def _connect_elements(self) -> None:
        def handle_search_requested() -> None:
            # noinspection PyUnresolvedReferences
            self.search_requested.emit(self.search_text())

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.bar)
        layout.addWidget(self.opts)
        layout.addWidget(self.remote_opts)
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.bar.focus_search_edit()

    def get_request_args(self) -> CroProWebSearchArgs:
        assert self._web_mode, "Web mode must be enabled."
        args: CroProWebSearchArgs = {}
        widgets = (
            self.remote_opts.sort_combo,
            self.remote_opts.category_combo,
            self.remote_opts.jlpt_level_combo,
            self.remote_opts.wanikani_level_combo,
        )
        # https://apiv2.immersionkit.com/openapi.json
        if keyword := self.bar.search_text():
            args["q"] = keyword
            for widget in widgets:
                if param := widget.currentData().http_arg:
                    args[widget.key] = param
        return args

    def _connect_elements(self) -> None:
        def handle_search_requested() -> None:
            # noinspection PyUnresolvedReferences
            self.search_requested.emit(self.bar.search_text())

        def handle_deck_changed() -> None:
            if text := self.bar.search_text():
                # Make sure that search isn't triggered when the window state is restored.
                # noinspection PyUnresolvedReferences
                self.search_requested.emit(text)

        qconnect(self.bar.search_requested, handle_search_requested)
        qconnect(self.opts.selected_deck_changed, handle_deck_changed)
        qconnect(self.opts.selected_profile_changed, lambda row_idx: self.setEnabled(row_idx >= 0 or self._web_mode))
