# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable, Sequence

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt.qt import *

from ..remote_search import RemoteNote
from .note_previewer import NotePreviewer

WIDGET_MIN_HEIGHT = 29
COMBO_MIN_WIDTH = 120


class NoteList(QWidget):
    """Lists notes and previews them."""
    _role = Qt.ItemDataRole.UserRole

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._note_list = QListWidget(self)
        self._previewer = NotePreviewer(self)
        self._enable_previewer = True
        self._setup_ui()
        self.itemDoubleClicked = self._note_list.itemDoubleClicked
        qconnect(self._note_list.currentItemChanged, self._on_current_item_changed)

    def _setup_ui(self):
        self.setLayout(layout := QHBoxLayout())
        self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

        layout.addWidget(splitter := QSplitter(Qt.Orientation.Horizontal))
        splitter.addWidget(self._note_list)
        splitter.addWidget(self._previewer)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        splitter.setSizes([200, 100])

        self._note_list.setAlternatingRowColors(True)
        self._note_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._note_list.setContentsMargins(0, 0, 0, 0)

        self._previewer.setHidden(True)

    def _on_current_item_changed(self, current: QListWidgetItem, _previous: QListWidgetItem):
        if current is None or self._enable_previewer is False:
            self._previewer.unload_note()
        else:
            self._previewer.load_note(current.data(self._role))

    def selected_notes(self) -> Sequence[Note]:
        return [item.data(self._role) for item in self._note_list.selectedItems()]

    def clear_selection(self):
        return self._note_list.clearSelection()

    def clear(self):
        self._previewer.unload_note()
        self._note_list.clear()

    def set_notes(self, notes: Iterable[Union[Note, RemoteNote]], hide_fields: list[str], previewer_enabled: bool = True):
        self._enable_previewer = previewer_enabled

        def is_hidden(field_name: str) -> bool:
            field_name = field_name.lower()
            return any(hidden_field.lower() in field_name for hidden_field in hide_fields)

        self.clear()
        for note in notes:
            item = QListWidgetItem()
            item.setText(' | '.join(
                html_to_text_line(field_content)
                for field_name, field_content in note.items()
                if not is_hidden(field_name) and field_content.strip())
            )
            item.setData(self._role, note)
            self._note_list.addItem(item)
