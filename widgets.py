# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import re
from typing import Iterable, Collection

from anki.notes import Note
from anki.sound import SoundOrVideoTag
from anki.utils import html_to_text_line
from aqt import sound
from aqt.qt import *

from .collection_manager import NameId

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


class PreferencesButton(QPushButton):
    _icon = QIcon(os.path.join(os.path.dirname(__file__), 'img', 'gear.svg'))

    def __init__(self, *args):
        super().__init__(*args)
        self.setText('Preferences')
        self.setIcon(self._icon)
        self.setMaximumHeight(WIDGET_HEIGHT)


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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

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
    def __init__(self):
        super().__init__()
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


class AudioButtonList(QWidget):
    """Displays play buttons."""
    _play_icon = QIcon(QPixmap(os.path.join(os.path.dirname(__file__), 'img', 'play-button.svg')))

    def __init__(self, video_tags: list[SoundOrVideoTag], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(layout := QHBoxLayout())
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        for tag in video_tags:
            layout.addWidget(button := QPushButton())
            qconnect(button.clicked, functools.partial(sound.av_player.play_tags, [tag, ]), )
            button.setIcon(QIcon(self._play_icon))
            button.setIconSize(QSize(16, 16))
            button.setFixedSize(QSize(32, 32))
            button.setStyleSheet('''
                QPushButton {
                    background-color: #eef0f2;
                    color: #292c31;
                    border-radius: 16px;
                    padding: 8px 7px 8px 9px;
                    border: 0px;
                    outline: 0px;
                }
                QPushButton:pressed {
                    background-color: #ced0d2;
                }
            ''')
        layout.addStretch()


class NoteList(QWidget):
    """Lists notes and previews them."""
    _role = Qt.ItemDataRole.UserRole
    _media_tag_regex = re.compile(r'\[sound:([^\[\]]+?\.[^\[\]]+?)]')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._note_list = QListWidget()
        self._previewer = QTableWidget()
        self._other_media_dir = None
        self._setup_ui()
        self.itemDoubleClicked = self._note_list.itemDoubleClicked
        qconnect(self._note_list.currentItemChanged, self._preview_note)

    def _setup_ui(self):
        self.setLayout(layout := QHBoxLayout())
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        layout.addWidget(splitter := QSplitter(Qt.Horizontal))
        splitter.addWidget(self._note_list)
        splitter.addWidget(self._previewer)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)

        self._note_list.setAlternatingRowColors(True)
        self._note_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self._previewer.horizontalHeader().setStretchLastSection(True)
        self._previewer.horizontalHeader().hide()
        # don't stretch rows with the mouse
        self._previewer.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._previewer.setHidden(True)

    def _preview_note(self, current: QListWidgetItem, _previous: QListWidgetItem):
        self._previewer.setHidden(current is None)
        self._previewer.setRowCount(0)
        if current is None:
            return

        note: Note = current.data(self._role)

        self._previewer.setRowCount(len(note.keys()))
        self._previewer.setColumnCount(1)

        for row, field_content in enumerate(note.values()):
            self._add_field(row, field_content)

        self._previewer.setVerticalHeaderLabels(list(note.keys()))
        self._previewer.resizeRowsToContents()
        self._previewer.resizeColumnsToContents()

    def _add_field(self, row: int, field_text: str):
        self._previewer.removeCellWidget(row, 0)

        if audio_files := re.findall(self._media_tag_regex, field_text):
            tags = [SoundOrVideoTag(filename=os.path.join(self._other_media_dir, f)) for f in audio_files]
            self._previewer.setCellWidget(row, 0, AudioButtonList(tags))
        else:
            table_item = QTableWidgetItem(field_text)
            table_item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            self._previewer.setItem(row, 0, table_item)

    def selected_notes(self) -> Collection[Note]:
        return [item.data(self._role) for item in self._note_list.selectedItems()]

    def clear_selection(self):
        return self._note_list.clearSelection()

    def clear(self):
        self._note_list.clear()

    def set_notes(self, notes: Iterable[Note], hide_fields: list[str], media_dir: str):
        self._other_media_dir = media_dir

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
