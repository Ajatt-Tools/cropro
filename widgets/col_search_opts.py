# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


from collections.abc import Iterable
from collections.abc import Sequence

from aqt import AnkiQt
from aqt.qt import *


try:
    from .remote_search_opts import RemoteSearchOptions
    from ..remote_search import get_request_url
    from .utils import CroProComboBox, NameIdComboBox, CroProLineEdit, CroProPushButton
    from ..collection_manager import NameId
except ImportError:
    from utils import CroProComboBox, NameIdComboBox, CroProLineEdit, CroProPushButton
    from collection_manager import NameId
    from remote_search_opts import RemoteSearchOptions
    from remote_search import get_request_url


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


class ColSearchOptions(QWidget):
    def __init__(self, ankimw: AnkiQt):
        super().__init__()
        self.ankimw = ankimw
        self._other_profile_names_combo = CroProComboBox()
        self._other_profile_deck_combo = NameIdComboBox()
        self.selected_profile_changed = self._other_profile_names_combo.currentIndexChanged
        self.selected_deck_changed = self._other_profile_deck_combo.currentIndexChanged
        self._setup_layout()

    def _setup_layout(self) -> None:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Import From Profile:"))
        layout.addWidget(self._other_profile_names_combo)
        layout.addWidget(QLabel("Deck:"))
        layout.addWidget(self._other_profile_deck_combo)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @property
    def other_profile_names_combo(self) -> QComboBox:
        return self._other_profile_names_combo

    @property
    def other_profile_deck_combo(self) -> QComboBox:
        return self._other_profile_deck_combo

    def current_deck(self) -> NameId:
        return self._other_profile_deck_combo.current_item()

    def decks_populated(self) -> bool:
        return self._other_profile_deck_combo.count() > 0

    def clear_combos(self) -> None:
        self._other_profile_names_combo.clear()
        self._other_profile_deck_combo.clear()

    def needs_to_repopulate_profile_names(self) -> bool:
        """
        The content of the profile name selector is outdated and the combo box needs to be repopulated.
        1) If the combo box is empty, the window is opened for the first time.
        2) If it happens to contain the current profile name, the user has switched profiles.
        """
        return (
            self._other_profile_names_combo.count() == 0
            or self._other_profile_names_combo.findText(self.ankimw.pm.name) != -1
        )

    def set_profile_names(self, other_profile_names: Sequence[str]):
        """
        Populate profile selector with a list of profile names, excluding the current profile.
        """
        assert self.ankimw.pm.name not in other_profile_names
        self._other_profile_names_combo.set_texts(other_profile_names)

    def selected_profile_name(self) -> str:
        """
        The name of the other collection to search notes in (and import notes from).
        """
        return self._other_profile_names_combo.currentText()

    def set_decks(self, decks: Iterable[NameId]):
        """
        A list of decks to search in.
        The user can limit search to a certain deck in the other collection.
        """
        return self._other_profile_deck_combo.set_items(decks)
