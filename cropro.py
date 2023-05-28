"""
Anki Add-on: Cross-Profile Search and Import

This add-on allows you to find and import notes from another profile into your currently loaded profile.
For example, you can make a "sentence bank" profile where you store thousands of cards generated by subs2srs,
and then use this add-on to search for and import cards with certain words into your main profile.
This helps keep your main profile uncluttered and free of large amounts of unneeded media.

GNU AGPL
Copyright (c) 2021-2023 Ren Tatsumoto
Copyright (c) 2018 Russel Simmons
Original concept by CalculusAce, with help from Matt VS Japan (@mattvsjapan)

TODO:
- Handle case where user has only one profile
- Review duplicate checking: check by first field, or all fields?
- When matching model is found, verify field count (or entire map?)
"""

import json
import os.path
from collections import defaultdict

import anki.notes
from aqt import mw, gui_hooks, addcards
from aqt.qt import *
from aqt.utils import showInfo, disable_help_button, restoreGeom, saveGeom

from .ajt_common.about_menu import menu_root_entry
from .collection_manager import CollectionManager, sorted_decks_and_ids, get_other_profile_names, NameId
from .common import ADDON_NAME, LogDebug
from .config import config
from .note_importer import import_note, ImportResult, copy_media_files, import_card_info, get_matching_model
from .widgets import SearchResultLabel, DeckCombo, ComboBox, ProfileNameLabel, StatusBar, NoteList, WIDGET_HEIGHT

logDebug = LogDebug()


#############################################################################
# UI layout
#############################################################################


class MainDialogUI(QDialog):
    name = "cropro_dialog"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_bar = StatusBar()
        self.search_result_label = SearchResultLabel()
        self.into_profile_label = ProfileNameLabel()
        self.current_profile_deck_combo = DeckCombo()
        self.edit_button = QPushButton('Edit')
        self.import_button = QPushButton('Import')
        self.search_term_edit = QLineEdit()
        self.other_profile_names_combo = ComboBox()
        self.other_profile_deck_combo = DeckCombo()
        self.filter_button = QPushButton('Filter')
        self.note_list = NoteList()
        self.note_type_selection_combo = ComboBox()
        self.init_ui()

    def init_ui(self):
        self.search_term_edit.setPlaceholderText('<text to filter by>')
        self.setLayout(self.make_main_layout())
        self.setWindowTitle(ADDON_NAME)
        self.set_default_sizes()

    def make_filter_row(self) -> QLayout:
        filter_row = QHBoxLayout()
        filter_row.addWidget(self.search_term_edit)
        filter_row.addWidget(self.filter_button)
        return filter_row

    def make_main_layout(self) -> QLayout:
        main_vbox = QVBoxLayout()
        main_vbox.addLayout(self.make_other_profile_settings_box())
        main_vbox.addLayout(self.make_filter_row())
        main_vbox.addWidget(self.search_result_label)
        main_vbox.addWidget(self.note_list)
        main_vbox.addLayout(self.status_bar)
        main_vbox.addLayout(self.make_input_row())
        return main_vbox

    def make_other_profile_settings_box(self) -> QLayout:
        other_profile_deck_row = QHBoxLayout()
        other_profile_deck_row.addWidget(QLabel('Import From Profile:'))
        other_profile_deck_row.addWidget(self.other_profile_names_combo)
        other_profile_deck_row.addWidget(QLabel('Deck:'))
        other_profile_deck_row.addWidget(self.other_profile_deck_combo)
        return other_profile_deck_row

    def set_default_sizes(self):
        combo_min_width = 120
        self.setMinimumSize(680, 500)
        for w in (
                self.edit_button,
                self.import_button,
                self.filter_button,
                self.search_term_edit,
        ):
            w.setMinimumHeight(WIDGET_HEIGHT)
        for combo in (
                self.other_profile_names_combo,
                self.other_profile_deck_combo,
                self.current_profile_deck_combo,
                self.note_type_selection_combo,
        ):
            combo.setMinimumWidth(combo_min_width)
            combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def make_input_row(self) -> QLayout:
        import_row = QHBoxLayout()
        import_row.addWidget(QLabel('Into Profile:'))
        import_row.addWidget(self.into_profile_label)
        import_row.addWidget(QLabel('Deck:'))
        import_row.addWidget(self.current_profile_deck_combo)
        import_row.addWidget(QLabel('Map to Note Type:'))
        import_row.addWidget(self.note_type_selection_combo)
        import_row.addStretch(1)
        import_row.addWidget(self.edit_button)
        import_row.addWidget(self.import_button)
        return import_row


#############################################################################
# UI logic
#############################################################################


class WindowState:
    def __init__(self, window: MainDialogUI):
        self._window = window
        self._json_filepath = os.path.join(os.path.dirname(__file__), 'user_files', 'window_state.json')
        self._map = {
            "from_profile": self._window.other_profile_names_combo,
            "from_deck": self._window.other_profile_deck_combo,
            "to_deck": self._window.current_profile_deck_combo,
            "note_type": self._window.note_type_selection_combo,
        }
        self._state = defaultdict(dict)

    def save(self):
        for key, widget in self._map.items():
            self._state[mw.pm.name][key] = widget.currentText()
        with open(self._json_filepath, 'w', encoding='utf8') as of:
            json.dump(self._state, of, indent=4, ensure_ascii=False)
        saveGeom(self._window, self._window.name)
        logDebug(f'saved window state.')

    def _load(self) -> bool:
        if self._state:
            return True
        elif os.path.isfile(self._json_filepath):
            with open(self._json_filepath, encoding='utf8') as f:
                self._state.update(json.load(f))
            return True
        else:
            return False

    def restore(self):
        if self._load() and (profile_settings := self._state.get(mw.pm.name)):
            for key, widget in self._map.items():
                if (value := profile_settings[key]) in widget.all_items():
                    widget.setCurrentText(value)
        restoreGeom(self._window, self._window.name, adjustSize=True)


class MainDialog(MainDialogUI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.window_state = WindowState(self)
        self.other_col = CollectionManager()
        self.connect_elements()
        disable_help_button(self)

    def connect_elements(self):
        qconnect(self.other_profile_deck_combo.currentIndexChanged, self.update_notes_list)
        qconnect(self.edit_button.clicked, self.new_edit_win)
        qconnect(self.import_button.clicked, self.do_import)
        qconnect(self.filter_button.clicked, self.update_notes_list)
        qconnect(self.search_term_edit.editingFinished, self.update_notes_list)
        qconnect(self.other_profile_names_combo.currentIndexChanged, self.open_other_col)

    def show(self):
        super().show()
        self.populate_ui()
        self.search_term_edit.setFocus()

    def populate_ui(self):
        self.status_bar.hide()
        self.populate_note_type_selection_combo()
        self.populate_current_profile_decks()
        # 1) If the combo box is emtpy the window is opened for the first time.
        # 2) If it happens to contain the current profile name, the user has switched profiles.
        if self.other_profile_names_combo.count() == 0 or self.other_profile_names_combo.findText(mw.pm.name) != -1:
            self.populate_other_profile_names()
        self.open_other_col()
        self.into_profile_label.setText(mw.pm.name or 'Unknown')
        self.window_state.restore()

    def clear_other_profiles_list(self):
        return self.other_profile_names_combo.clear()

    def populate_other_profile_names(self):
        logDebug("populating other profiles.")

        other_profile_names = get_other_profile_names()
        if not other_profile_names:
            msg: str = 'This add-on only works if you have multiple profiles.'
            showInfo(msg)
            logDebug(msg)
            self.hide()
            return

        self.other_profile_names_combo.clear()
        self.other_profile_names_combo.addItems(other_profile_names)

    def populate_note_type_selection_combo(self):
        self.note_type_selection_combo.clear()
        self.note_type_selection_combo.addItem(*NameId.none_type())
        for note_type in mw.col.models.all_names_and_ids():
            self.note_type_selection_combo.addItem(note_type.name, note_type.id)

    def open_other_col(self):
        col_name = self.other_profile_names_combo.currentText()

        if not self.other_col.is_opened or col_name != self.other_col.name:
            self.other_col.open(col_name)
            self.populate_other_profile_decks()

    def populate_current_profile_decks(self):
        logDebug("populating current profile decks...")
        self.current_profile_deck_combo.set_decks(sorted_decks_and_ids(mw.col))

    def populate_other_profile_decks(self):
        logDebug("populating other profile decks...")
        self.other_profile_deck_combo.set_decks([
            self.other_col.col_name_and_id(), *self.other_col.deck_names_and_ids(),
        ])

    def update_notes_list(self):
        self.search_term_edit.setFocus()
        self.search_result_label.hide()
        self.open_other_col()

        if not self.search_term_edit.text() and not config['allow_empty_search']:
            return

        if self.other_profile_deck_combo.count() < 1:
            return

        note_ids = self.other_col.find_notes(self.other_profile_deck_combo.current_deck(), self.search_term_edit.text())
        limited_note_ids = note_ids[:config['max_displayed_notes']]

        self.note_list.set_notes(
            map(self.other_col.get_note, limited_note_ids),
            hide_fields=config['hidden_fields'],
            media_dir=self.other_col.media_dir,
            previewer=config['preview_on_right_side'],
        )

        self.search_result_label.set_count(len(note_ids), len(limited_note_ids))

    def do_import(self):
        logDebug('beginning import')

        # get selected notes
        notes = self.note_list.selected_notes()

        # clear the selection
        self.note_list.clear_selection()

        logDebug(f'importing {len(notes)} notes')

        results = []

        for note in notes:
            results.append(import_note(
                other_note=note,
                other_col=self.other_col.col,
                model_id=self.note_type_selection_combo.currentData(),
                deck_id=self.current_profile_deck_combo.currentData(),
            ))

        self.status_bar.set_status(results.count(ImportResult.success), results.count(ImportResult.dupe))
        mw.reset()

    def new_edit_win(self):
        EditWindow().open(self)

    def done(self, result_code: int):
        self.window_state.save()
        self.other_col.close_all()
        return super().done(result_code)


#############################################################################
# Edit Logic & UI
#############################################################################

class EditWindow:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.correct_win = False
        self.selected_note = None
        self.cropro_win = None
        self.cur_media = None
        self.add_window = None

    def open(self, cropro_win: MainDialog):
        if len(cropro_win.note_list.selected_notes()) > 0:
            self.cropro_win = cropro_win

            logDebug("Preparing add window")
            # Open a new add-window and update it
            self.add_window = addcards.AddCards(mw)
            self.add_window.addButton.setText('Import')
            self.add_window.historyButton.hide()
            self.add_window.helpButton.setText('Anki Help')

            # Save the note for selection change case
            self.selected_note = self.cropro_win.note_list.selected_notes()[0]
            # Copy so no overwrite to original note
            transfer_note = self.selected_note
            transfer_note.NotetypeId = get_matching_model(self.cropro_win.note_type_selection_combo.currentData(),
                                                          self.selected_note.note_type())
            if not config.get('copy_tags'):
                transfer_note.tags = []

            # Overwriting the collection for media to load
            # Overwrites mw.col.media as well so saves a copy of that
            self.cur_media = mw.col.media
            self.set_media(self.add_window)
            # Update it with the current note data (only the first of the selected)
            self.add_window.set_note(transfer_note, self.cropro_win.current_profile_deck_combo.currentData())

            # Add a listeners for the add window
            # Two times as add because a note can't be shared without/before the hook
            self.add_window.leaveEvent = self.reset_media
            self.add_window.enterEvent = self.set_media

            qconnect(self.add_window.addButton.clicked, self.add_from_our_window)
            qconnect(self.add_window.windowHandle().visibilityChanged, self.on_close)
            gui_hooks.add_cards_will_add_note.append(self.do_add_import)

    def do_add_import(self, problem, note: anki.notes.Note):
        if self.correct_win and self.add_window:
            logDebug("Importing note")
            note.col.media = self.cur_media
            copy_media_files(note, self.selected_note)

            if config.get('tag_exported_cards') and (tag := config.get('exported_tag')):
                self.selected_note.add_tag(tag)

            if config['copy_card_data']:
                import_card_info(note, self.selected_note, self.cropro_win.other_col.col)

            self.correct_win = False
            self.cropro_win.note_list.clear_selection()
            self.cropro_win.status_bar.set_status(1, 0)
            mw.reset()
            self.add_window.ifCanClose(self.add_window.close)

    def set_media(self, add_window: addcards.AddCards):
        try: add_window.col
        except AttributeError:
            add_window = self.add_window
        add_window.col.media = self.cropro_win.other_col.col.media
        mw.reset()

    def reset_media(self, add_window: addcards.AddCards):
        try: add_window.col
        except AttributeError:
            add_window = self.add_window
        add_window.col.media = self.cur_media
        mw.reset()

    def add_from_our_window(self):
        self.reset_media(self.add_window)
        self.correct_win = True

    def on_close(self):
        self.correct_win = False
        self.reset_media(self.add_window)
        mw.reset()


######################################################################
# Entry point
######################################################################

def init():
    # init dialog
    d = mw._cropro_main_dialog = MainDialog(parent=mw)
    # get AJT menu
    root_menu = menu_root_entry()
    # create a new menu item
    action = QAction(ADDON_NAME, root_menu)
    # set it to call show function when it's clicked
    qconnect(action.triggered, d.show)
    # and add it to the tools menu
    root_menu.addAction(action)
    # react to anki's state changes
    gui_hooks.profile_will_close.append(d.close)
    gui_hooks.profile_did_open.append(d.clear_other_profiles_list)
