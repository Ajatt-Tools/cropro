from typing import Protocol, Optional

import anki.notes
import aqt
from anki.notes import Note, NoteId
from aqt import mw, gui_hooks, addcards
from aqt.qt import *

from .collection_manager import CollectionManager
from .common import LogDebug
from .config import config
from .note_importer import copy_media_files, remove_media_files, import_card_info, get_matching_model
from .widgets import DeckCombo, ComboBox, NoteList, StatusBar

logDebug = LogDebug()


class CropProWindow(Protocol):
    current_profile_deck_combo: DeckCombo
    note_type_selection_combo: ComboBox
    other_col: CollectionManager
    note_list: NoteList
    status_bar: StatusBar


def current_add_dialog() -> Optional[addcards.AddCards]:
    # noinspection PyProtectedMember
    return aqt.dialogs._dialogs['AddCards'][1]


class AddDialogLauncher:
    def __init__(self, cropro: CropProWindow):
        super().__init__()
        self.cropro = cropro
        self.add_window: Optional[addcards.AddCards] = None
        self.new_note: Optional[Note] = None
        self.other_note: Optional[Note] = None
        self.block_close_cb: bool = False
        gui_hooks.add_cards_will_add_note.append(self.on_add_import)

    def create_window(self, other_note: Note = None) -> NoteId:
        if other_note is None:
            self.add_window = aqt.dialogs.open('AddCards', mw)
            self.add_window.activateWindow()
            return self.add_window.editor.note.id

        self.other_note = other_note
        logDebug("Preparing add window")

        if self.cropro.current_profile_deck_combo.currentData() is None:
            raise Exception(f'deck was not found: {self.cropro.current_profile_deck_combo.currentData()}')

        mw.col.decks.select(self.cropro.current_profile_deck_combo.currentData())

        model = get_matching_model(self.cropro.note_type_selection_combo.currentData(), other_note.note_type())

        mw.col.models.setCurrent(model)
        mw.col.models.update(model)

        self.new_note = anki.notes.Note(mw.col, model)

        # fill out card beforehand, so we can be sure of other_note's id
        for key in self.new_note.keys():
            if key in other_note:
                self.new_note[key] = str(other_note[key])

        # Copy media just yet, so it can still be deleted later but causes no unwanted behaviour
        copy_media_files(self.new_note, other_note)

        if 'tags' in other_note and config.get('copy_tags'):
            self.new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

        if tag := config.tag_original_notes():
            other_note.add_tag(tag)
            other_note.flush()

        def open_window():
            self.add_window = aqt.dialogs.open('AddCards', mw)

            self.add_window.editor.set_note(self.new_note)

            self.add_window.activateWindow()
            # Modify Bottom Button Bar against confusion
            self.add_window.addButton.setText('Import')
            self.add_window.historyButton.hide()
            self.add_window.helpButton.setText('Anki Help')

            aqt.dialogs.open('AddCards', mw)

            self.add_window.setAndFocusNote(self.add_window.editor.note)

        if current_add_dialog() is not None:
            current_add_dialog().closeWithCallback(open_window)
        else:
            open_window()

            def on_visibility_changed():
                if not self.block_close_cb and self.new_note:
                    return remove_media_files(self.new_note)

            # Remove Media on close if not in saving progress
            qconnect(self.add_window.windowHandle().visibilityChanged, on_visibility_changed)

        return self.new_note.id

    def on_add_import(self, problem: Optional[str], note: Note) -> str:
        if self.other_note and current_add_dialog() and current_add_dialog() is self.add_window:
            logDebug("Importing edited note")
            if config['copy_card_data']:
                import_card_info(note, self.other_note, self.cropro.other_col.col)
            self.cropro.note_list.clear_selection()
            self.cropro.status_bar.set_import_status(1, 0)
            mw.reset()
            self.block_close_cb = True  # Block media removal
            self.add_window.close()
        self.other_note = None
        self.add_window = None
        return problem
