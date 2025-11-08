# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing
from collections.abc import Iterable, Sequence
from itertools import islice

from anki.notes import Note
from aqt.qt import *

from ..ajt_common.utils import clamp, q_emit
from ..config import config
from ..debug_log import LogDebug
from ..remote_search import RemoteNote
from .note_list import NoteList

logDebug = LogDebug(config)


class PageNavButton(QPushButton):
    def __init__(self, text: str, tooltip: str) -> None:
        super().__init__(text)
        self.setFixedWidth(17)
        self.setFixedHeight(45)
        self.setToolTip(tooltip)


def to_chunks(iterable: Iterable, chunk_size: int) -> Iterable[Sequence]:
    # batched('ABCDEFG', 3) → ABC DEF G
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least one")
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, chunk_size)):
        yield batch


class NoteListStatus(typing.NamedTuple):
    found_count: int
    displayed_count: int
    current_page_num: int
    total_pages_count: int


class PagedNoteList(QWidget):
    _note_list: NoteList
    _page_prev_btn: QPushButton
    _page_next_btn: QPushButton
    _notes: list[Sequence[Union[Note, RemoteNote]]]
    _current_page_num: int

    status_changed = pyqtSignal(NoteListStatus)

    def __init__(self) -> None:
        super().__init__()
        self._notes = []
        self._current_page_num = 0
        self._page_prev_btn = PageNavButton("🞀", "Previous Page")
        self._page_next_btn = PageNavButton("🞂", "Next Page")
        self._note_list = NoteList()
        self.setLayout(self._create_main_layout())
        self._connect_widgets()
        self._set_buttons_enabled()

    def _create_main_layout(self) -> QLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._page_prev_btn)
        layout.addWidget(self._note_list)
        layout.addWidget(self._page_next_btn)
        layout.setStretch(1, 1)
        return layout

    def set_focus(self) -> None:
        return self._note_list.set_focus()

    def clear_notes(self) -> None:
        self._note_list.clear_notes()
        self._notes.clear()

    def selected_notes(self) -> Sequence[Union[Note, RemoteNote]]:
        return self._note_list.selected_notes()

    def note_count(self) -> int:
        return sum(len(chunk) for chunk in self._notes)

    def clear_selection(self) -> None:
        return self._note_list.clear_selection()

    def _connect_widgets(self) -> None:
        qconnect(self._page_prev_btn.clicked, lambda: self.flip_page(-1))
        qconnect(self._page_next_btn.clicked, lambda: self.flip_page(+1))

    def set_notes(self, notes: Sequence[Union[Note, RemoteNote]]) -> None:
        self._notes = [*to_chunks(notes, config.notes_per_page)]
        self.set_page(0)

    def get_visible_notes(self) -> Sequence[Union[Note, RemoteNote]]:
        return self._notes[self._current_page_num] if self._notes else []

    def set_page(self, page_num: int):
        self._current_page_num = clamp(min_val=0, val=page_num, max_val=len(self._notes) - 1)
        self._note_list.set_notes(
            notes=self.get_visible_notes(),
            hide_fields=config.hidden_fields,
            is_previewer_enabled=config.preview_on_right_side,
        )
        self._set_buttons_enabled()
        q_emit(
            self.status_changed,
            NoteListStatus(
                found_count=self.note_count(),
                displayed_count=len(self.get_visible_notes()),
                current_page_num=self._current_page_num + 1,  # count from 1
                total_pages_count=len(self._notes),
            ),
        )
        logDebug(f"Page set. Current page #{self._current_page_num + 1}/{len(self._notes)}.")

    def flip_page(self, step: int) -> None:
        self.set_page(step + self._current_page_num)

    def _set_buttons_enabled(self):
        self._page_prev_btn.setEnabled(self._current_page_num > 0)
        self._page_next_btn.setEnabled(self._current_page_num < len(self._notes) - 1)
