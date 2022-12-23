# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os.path
import re
from typing import Iterable, Collection, Optional

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt.qt import *
from aqt.webview import AnkiWebView

from .collection_manager import NameId
from .web import get_previewer_css_relpath, get_previewer_html, make_play_buttons, make_images

WIDGET_HEIGHT = 29


class SpinBox(QSpinBox):
    def __init__(self, min_val: int, max_val: int, step: int, value: int):
        super().__init__()
        self.setRange(min_val, max_val)
        self.setSingleStep(step)
        self.setValue(value)


class ProfileNameLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        font = QFont()
        font.setBold(True)
        self.setFont(font)


class ComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMaximumHeight(WIDGET_HEIGHT)

    def all_items(self) -> Iterable[str]:
        """Returns an iterable of all items stored in the combo box."""
        for i in range(self.count()):
            yield self.itemText(i)


class DeckCombo(ComboBox):
    def set_decks(self, decks: Iterable[NameId]):
        self.clear()
        for deck_name, deck_id in decks:
            self.addItem(deck_name, deck_id)

    def current_deck(self) -> NameId:
        return NameId(self.currentText(), self.currentData())


class SearchResultLabel(QLabel):
    def __init__(self, *args, ):
        super().__init__(*args, )
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

    def set_count(self, found: int, displayed: int):
        if found == 0:
            self.setText(f'No notes found')
            self.setStyleSheet('QLabel { color: red; }')
        elif displayed == found:
            self.setText(f'{found} notes found')
            self.setStyleSheet('QLabel { color: green; }')
        else:
            self.setText(f'{found} notes found (displaying first {displayed})')
            self.setStyleSheet('QLabel { color: orange; }')
        if self.isHidden():
            self.show()


class StatusBar(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._add_success_label()
        self._add_dupes_label()
        self.addStretch()
        self.hide()

    def _add_dupes_label(self):
        self._dupes_label = QLabel()
        self._dupes_label.setStyleSheet('QLabel { color: #FF8C00; }')
        self.addWidget(self._dupes_label)

    def _add_success_label(self):
        self._success_label = QLabel()
        self._success_label.setStyleSheet('QLabel { color: #228B22; }')
        self.addWidget(self._success_label)

    def hide(self):
        self._dupes_label.hide()
        self._success_label.hide()

    def set_status(self, successes: int, dupes: int):
        if successes:
            self._success_label.setText(f'{successes} notes successfully imported.')
            self._success_label.show()
        else:
            self._success_label.hide()

        if dupes:
            self._dupes_label.setText(f'{dupes} notes were duplicates, and skipped.')
            self._dupes_label.show()
        else:
            self._dupes_label.hide()


class ItemBox(QWidget):
    """Displays tag-like labels with × icons. Pressing on the × deletes the tag."""

    class ItemButton(QPushButton):
        _close_icon = QIcon(QPixmap(os.path.join(os.path.dirname(__file__), 'img', 'close.png')))

        def __init__(self, item_box: 'ItemBox', text: str):
            super().__init__(text)
            self.item_box = item_box
            self.setStyleSheet('''
                QPushButton {
                    background-color: #eef0f2;
                    color: #292c31;
                    border-radius: 12px;
                    padding: 3px 6px;
                    border: 0px;
                }
            ''')
            self.setIcon(self._close_icon)
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            qconnect(self.clicked, lambda: self.item_box.remove_item(text))

    def __init__(self, parent: QWidget, initial_values: list[str]):
        super().__init__(parent=parent)
        self.items = dict.fromkeys(initial_values)
        self.setLayout(self._make_layout())

    def values(self) -> list[str]:
        return list(self.items)

    def _make_layout(self) -> QLayout:
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        for text in self.items:
            self._add_item(text)
        self.layout.addStretch()
        return self.layout

    def count(self) -> int:
        # The last element in the layout is a stretch.
        return self.layout.count() - 1

    def _add_item(self, text: str) -> None:
        b = self.items[text] = self.ItemButton(self, text)
        self.layout.insertWidget(self.count(), b)

    def remove_item(self, text: str) -> None:
        if widget := self.items.pop(text, None):
            widget.deleteLater()

    def new_item(self, edit: QLineEdit) -> None:
        separators = (',', ' ', ';')
        if (text := edit.text()).endswith(separators):
            text = text.strip(''.join(separators))
            if text and text not in self.items:
                self._add_item(text)
            edit.setText('')


class NotePreviewer(AnkiWebView):
    """Previews a note in a Form Layout using a webview."""
    _media_tag_regex = re.compile(r'\[sound:([^\[\]]+?\.[^\[\]]+?)]')
    _image_tag_regex = re.compile(r'<img [^<>]*src="([^"<>]+)"[^<>]*>')

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._note_media_dir: Optional[str] = None
        self.set_title("Note previewer")
        self.disable_zoom()
        self.setProperty("url", QUrl("about:blank"))
        self.setMinimumSize(200, 320)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def load_note(self, note: Note, note_media_dir: str) -> None:
        self._note_media_dir = note_media_dir
        rows: list[str] = []
        for field_name, field_content in note.items():
            rows.append(
                f'<div class="name">{field_name}</div>'
                f'<div class="content">{self._create_html_row_for_field(field_content)}</div>'
            )
        self.stdHtml(
            get_previewer_html().replace('<!--CONTENT-->', ''.join(rows)),
            js=[],
            css=[get_previewer_css_relpath(), ]
        )

    def _create_html_row_for_field(self, field_content: str) -> str:
        """Creates a row for the previewer showing the current note's field."""
        if audio_files := re.findall(self._media_tag_regex, field_content):
            return (
                '<div class="cropro__button_list">'
                f'{make_play_buttons(os.path.join(self._note_media_dir, f) for f in audio_files)}'
                '</div>'
            )
        elif image_files := re.findall(self._image_tag_regex, field_content):
            return (
                '<div class="cropro__image_list">'
                f'{make_images(os.path.join(self._note_media_dir, f) for f in image_files)}'
                '</div>'
            )
        else:
            return (
                '<span class="cropro__text_item">'
                f'{html_to_text_line(field_content)}'
                '</span>'
            )


class NoteList(QWidget):
    """Lists notes and previews them."""
    _role = Qt.ItemDataRole.UserRole

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._note_list = QListWidget(self)
        self._previewer = NotePreviewer(self)
        self._other_media_dir = None
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

        self._previewer.setHidden(True)

    def _on_current_item_changed(self, current: QListWidgetItem, _previous: QListWidgetItem):
        if current is None or self._enable_previewer is False:
            self._previewer.setHidden(True)
        else:
            self._previewer.setHidden(False)
            self._previewer.load_note(current.data(self._role), self._other_media_dir)

    def selected_notes(self) -> Collection[Note]:
        return [item.data(self._role) for item in self._note_list.selectedItems()]

    def clear_selection(self):
        return self._note_list.clearSelection()

    def clear(self):
        self._note_list.clear()

    def set_notes(self, notes: Iterable[Note], hide_fields: list[str], media_dir: str, previewer: bool = True):
        self._other_media_dir = media_dir
        self._enable_previewer = previewer

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
