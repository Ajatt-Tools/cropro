# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable, Sequence

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt.qt import *

from ..remote_search import RemoteNote
from .note_previewer import NotePreviewer

WIDGET_MIN_HEIGHT = 29
COMBO_MIN_WIDTH = 120


class NoteList(QSplitter):
    """Lists notes and previews them."""

    _role = Qt.ItemDataRole.UserRole

    def __init__(self):
        super().__init__()
        self._note_list = QListWidget(self)
        self._previewer = NotePreviewer(self)
        self._enable_previewer = True
        self._setup_ui()
        self.itemDoubleClicked = self._note_list.itemDoubleClicked
        qconnect(self._note_list.currentItemChanged, self._on_current_item_changed)

    def _setup_ui(self):
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        self.setOrientation(Qt.Orientation.Horizontal)

        self.addWidget(self._note_list)
        self.addWidget(self._previewer)
        self.setCollapsible(0, False)
        self.setCollapsible(1, True)
        self.setSizes([200, 100])

        self._note_list.setAlternatingRowColors(True)
        self._note_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._note_list.setContentsMargins(0, 0, 0, 0)

        self._previewer.setHidden(True)

    def _on_current_item_changed(self, current: QListWidgetItem, _previous: QListWidgetItem):
        if current is None or self._enable_previewer is False:
            self._previewer.unload_note()
        else:
            self._previewer.load_note(current.data(self._role))

    def set_focus(self) -> None:
        """
        Focus the note list. This method is called from a keyboard shortcut.
        """
        self._note_list.setFocus()
        # if there's no selected notes, select the first note in the list.
        if not self._note_list.selectedItems() and self._note_list.count() > 0:
            self._note_list.setCurrentRow(0)

    def selected_notes(self) -> Sequence[Note]:
        return [item.data(self._role) for item in self._note_list.selectedItems()]

    def clear_selection(self):
        return self._note_list.clearSelection()

    def clear_notes(self):
        self._previewer.unload_note()
        self._note_list.clear()

    def set_notes(
        self,
        notes: Iterable[Union[Note, RemoteNote]],
        hide_fields: list[str],
        previewer_enabled: bool = True,
    ):
        self._enable_previewer = previewer_enabled

        def is_hidden(field_name: str) -> bool:
            field_name = field_name.lower()
            return any(hidden_field.lower() in field_name for hidden_field in hide_fields)

        self.clear_notes()
        for note in notes:
            item = QListWidgetItem()
            item.setText(
                " | ".join(
                    html_to_text_line(field_content)
                    for field_name, field_content in note.items()
                    if not is_hidden(field_name) and field_content.strip()
                )
            )
            item.setData(self._role, note)
            self._note_list.addItem(item)
