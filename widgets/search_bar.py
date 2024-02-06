# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


from collections.abc import Iterable

from aqt import AnkiQt
from aqt.qt import *

from .utils import CroProComboBox, DeckCombo, CroProLineEdit, CroProPushButton
from ..collection_manager import NameId


class SearchBar(QWidget):
    search_requested = pyqtSignal()

    def __init__(self, mw: AnkiQt):
        super().__init__()
        self.mw = mw
        self.other_profile_names_combo = CroProComboBox()
        self.selected_profile_changed = self.other_profile_names_combo.currentIndexChanged
        self.other_profile_deck_combo = DeckCombo()
        self.search_term_edit = CroProLineEdit()
        self.filter_button = CroProPushButton("Filter")
        self._setup_layout()
        self._connect_elements()

    def search_text(self) -> str:
        return self.search_term_edit.text()

    def current_deck(self) -> NameId:
        return self.other_profile_deck_combo.current_deck()

    def decks_populated(self) -> bool:
        return self.other_profile_deck_combo.count() > 0

    def clear_profiles_list(self) -> None:
        return self.other_profile_names_combo.clear()

    def needs_to_repopulate_profile_names(self) -> bool:
        """
        The content of the profile name selector is outdated and the combo box needs to be repopulated.
        1) If the combo box is empty, the window is opened for the first time.
        2) If it happens to contain the current profile name, the user has switched profiles.
        """
        return (
                self.other_profile_names_combo.count() == 0
                or self.other_profile_names_combo.findText(self.mw.pm.name) != -1
        )

    def set_profile_names(self, other_profile_names: list[str]):
        """
        Populate profile selector with a list of profile names, excluding the current profile.
        """
        assert (self.mw.pm.name not in other_profile_names)
        self.other_profile_names_combo.clear()
        self.other_profile_names_combo.addItems(other_profile_names)

    def selected_profile_name(self) -> str:
        """
        The name of the other collection to search notes in (and import notes from).
        """
        return self.other_profile_names_combo.currentText()

    def set_decks(self, decks: Iterable[NameId]):
        """
        A list of decks to search in.
        The user can limit search to a certain deck in the other collection.
        """
        return self.other_profile_deck_combo.set_decks(decks)

    def focus(self):
        self.search_term_edit.setFocus()

    def _setup_layout(self) -> None:
        self.setLayout(layout := QVBoxLayout())
        layout.addLayout(self._make_other_profile_settings_box())
        layout.addLayout(self._make_filter_row())
        self.search_term_edit.setPlaceholderText('<text to filter by>')
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        self.focus()

    def _make_other_profile_settings_box(self) -> QLayout:
        layout = QHBoxLayout()
        layout.addWidget(QLabel('Import From Profile:'))
        layout.addWidget(self.other_profile_names_combo)
        layout.addWidget(QLabel('Deck:'))
        layout.addWidget(self.other_profile_deck_combo)
        return layout

    def _make_filter_row(self) -> QLayout:
        layout = QHBoxLayout()
        layout.addWidget(self.search_term_edit)
        layout.addWidget(self.filter_button)
        return layout

    def _connect_elements(self):
        qconnect(self.other_profile_deck_combo.currentIndexChanged, self.search_requested)
        qconnect(self.filter_button.clicked, self.search_requested)
        qconnect(self.search_term_edit.editingFinished, self.search_requested)
