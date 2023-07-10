import anki.notes
import aqt
from aqt import mw, gui_hooks
from aqt.qt import *

from .config import config
from .note_importer import copy_media_files, remove_media_files, import_card_info, get_matching_model
from .common import LogDebug

logDebug = LogDebug()


class AddWindow:
    def __init__(self, cropro_self):
        super(AddWindow, self).__init__()
        self.add_window = None
        self.cropro = cropro_self
        self.new_note = None
        self.other_note = None

    def create_window(self, other_note=None):
        if other_note is not None:
            self.other_note = other_note
            logDebug("Preparing add window")

            collection = mw.col

            if self.cropro.current_profile_deck_combo.currentData() is None:
                raise Exception('deck was not found: {}'.format(self.cropro.current_profile_deck_combo.currentData()))

            collection.decks.select(self.cropro.current_profile_deck_combo.currentData())

            model = get_matching_model(self.cropro.note_type_selection_combo.currentData(), other_note.note_type())

            collection.models.setCurrent(model)
            collection.models.update(model)

            self.new_note = anki.notes.Note(collection, model)

            # fill out card beforehand, so we can be sure of other_note's id
            for key in self.new_note.keys():
                if key in other_note:
                    self.new_note[key] = str(other_note[key])

            # Copy media just yet, so it can still be deleted later but causes no unwanted behaviour
            copy_media_files(self.new_note, other_note)

            if 'tags' in other_note and config.get('copy_tags'):
                self.new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

            if config.get('tag_exported_cards') and (tag := config.get('exported_tag')):
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

            current_window = aqt.dialogs._dialogs['AddCards'][1]

            if current_window is not None:
                current_window.closeWithCallback(open_window)
            else:
                open_window()

            # Remove Media on close if not in saving progress
            qconnect(self.add_window.windowHandle().visibilityChanged, lambda: remove_media_files(self.new_note) if not hasattr(self, 'block_close_cb') and self.new_note else 0)
            qconnect(self.add_window.addButton.clicked, self.add_import)

            return self.new_note.id

        else:
            self.add_window = aqt.dialogs.open('AddCards', mw)
            self.add_window.activateWindow()

            return self.add_window.editor.note.id

    def add_import(self):
        def do_add_import(problem, note: anki.notes.Note):
            logDebug("Importing edited note")

            if config['copy_card_data']:
                import_card_info(note, self.other_note, self.cropro.other_col.col)

            self.cropro.note_list.clear_selection()
            self.cropro.status_bar.set_status(1, 0)
            mw.reset()

            self.block_close_cb = True  # Block media removal
            self.add_window.ifCanClose(self.add_window.close)

        gui_hooks.add_cards_will_add_note.append(do_add_import)

