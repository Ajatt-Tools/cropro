"""
Anki Add-on: Cross-Profile Search and Import
version 0.2.1
URL: https://ankiweb.net/shared/info/310394744
GitHub: https://github.com/rsimmons/anki-cropro

This add-on allows you to find and import notes from another profile into your currently loaded profile.
For example, you can make a "sentence bank" profile where you store thousands of cards generated by subs2srs,
and then use this add-on to search for and import cards with certain words into your main profile.
This helps keep your main profile uncluttered and free of large amounts of unneeded media.

MIT License
Copyright (c) 2018 Russel Simmons
Original concept by CalculusAce, with help from Matt VS Japan (@mattvsjapan)

TODO:
- Handle case where user has only one profile
- Review duplicate checking: check by first field, or all fields?
- When matching model is found, verify field count (or entire map?)
"""

import re
from copy import deepcopy
from typing import Optional, TextIO

from anki.collection import Collection
from anki.models import NoteType
from anki.notes import Note
from anki.utils import htmlToTextLine
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .previewer import CroProPreviewer

config = mw.addonManager.getConfig(__name__)

#############################################################################
# END OPTIONS
#############################################################################

logfile: Optional[TextIO] = None


def logDebug(msg):
    if not config['enable_debug_log']:
        return

    global logfile
    if not logfile:
        fn = os.path.join(mw.pm.base, 'cropro.log')
        print(f'CroPro debug: opening log file "{fn}"')
        logfile = open(fn, 'a')
    logfile.write(str(msg) + '\n')
    logfile.flush()
    print('CroPro debug:', str(msg))


def getOtherProfileNames() -> list:
    profiles = mw.pm.profiles()
    profiles.remove(mw.pm.name)
    return profiles


def openProfileCollection(name) -> Collection:
    # NOTE: this code is based on aqt/profiles.py; we can't really re-use what's there
    collection_filename = os.path.join(mw.pm.base, name, 'collection.anki2')
    return Collection(collection_filename)


def getProfileDecks(col: Collection):
    return sorted(col.decks.all(), key=lambda deck: deck["name"])


def trim(string: str) -> str:
    return re.sub("[\"\']", '', string)


def blocked_field(field_name: str) -> bool:
    for badword in config['bad_fields']:
        if badword.lower() in field_name.lower():
            return True
    return False


def get_matching_model(reference_model: NoteType) -> NoteType:
    matching_model: NoteType = mw.col.models.by_name(reference_model.get('name'))
    if matching_model:
        if matching_model.keys() == reference_model.keys():
            return matching_model
        else:
            matching_model = deepcopy(reference_model)
            matching_model['name'] += ' cropro'
    else:
        matching_model = deepcopy(reference_model)

    matching_model['id'] = 0
    return matching_model


#############################################################################
# UI layout
#############################################################################


class MainDialogUI(QDialog):
    def __init__(self, *args, **kwargs):
        super(MainDialogUI, self).__init__(parent=mw, *args, **kwargs)

        self.statSuccessLabel = QLabel()
        self.statNoMatchingModelLabel = QLabel()
        self.statDupeLabel = QLabel()
        self.noteCountLabel = QLabel()
        self.into_profile_label = self.makeProfileNameLabel()
        self.currentProfileDeckCombo = QComboBox()
        self.importButton = QPushButton('Import')
        self.tagCheckBox = QCheckBox("Tag cards as exported")
        self.filterEdit = QLineEdit()
        self.otherProfileNamesCombo = QComboBox()
        self.otherProfileDeckCombo = QComboBox()
        self.filterButton = QPushButton('Filter')
        self.noteList = QListWidget()
        self.settingsButton = QPushButton('Preferences')
        self.note_type_selection_combo = QComboBox()
        self.initUI()

    def initUI(self):
        self.filterEdit.setPlaceholderText('<text to filter by>')
        self.setLayout(self.makeMainLayout())
        self.setWindowTitle('Cross Profile Search and Import')
        self.setDefaults()

    def makeStatsRow(self):
        stats_row = QVBoxLayout()

        self.statSuccessLabel.setStyleSheet('QLabel { color : green; }')
        self.statSuccessLabel.hide()
        stats_row.addWidget(self.statSuccessLabel)

        self.statNoMatchingModelLabel.setStyleSheet('QLabel { color : red; }')
        self.statNoMatchingModelLabel.hide()
        stats_row.addWidget(self.statNoMatchingModelLabel)

        self.statDupeLabel.setStyleSheet('QLabel { color : orange; }')
        self.statDupeLabel.hide()
        stats_row.addWidget(self.statDupeLabel)

        return stats_row

    def makeFilterRow(self):
        filter_row = QHBoxLayout()
        filter_row.addWidget(self.filterEdit)
        filter_row.addWidget(self.filterButton)
        return filter_row

    def makeMainLayout(self):
        main_vbox = QVBoxLayout()
        main_vbox.addLayout(self.makeOtherProfileSettingsBox())
        main_vbox.addLayout(self.makeFilterRow())
        main_vbox.addWidget(self.noteCountLabel)
        main_vbox.addWidget(self.noteList)
        main_vbox.addLayout(self.makeStatsRow())
        main_vbox.addLayout(self.makeInputRow())
        return main_vbox

    def makeOtherProfileSettingsBox(self):
        other_profile_deck_row = QHBoxLayout()
        other_profile_deck_row.addWidget(QLabel('Import From Profile:'))
        other_profile_deck_row.addWidget(self.otherProfileNamesCombo)
        other_profile_deck_row.addWidget(QLabel('Deck:'))
        other_profile_deck_row.addWidget(self.otherProfileDeckCombo)
        other_profile_deck_row.addStretch(1)
        other_profile_deck_row.addWidget(self.settingsButton)

        return other_profile_deck_row

    def setDefaults(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'gear.svg')
        combo_min_width = 120
        self.setMinimumSize(640, 480)
        self.settingsButton.setIcon(QIcon(icon_path))

        for combo in (
                self.otherProfileNamesCombo,
                self.otherProfileDeckCombo,
                self.note_type_selection_combo,
        ):
            combo.setMinimumWidth(combo_min_width)

    @staticmethod
    def makeProfileNameLabel():
        current_profile_name_label = QLabel()
        current_profile_name_label_font = QFont()
        current_profile_name_label_font.setBold(True)
        current_profile_name_label.setFont(current_profile_name_label_font)
        return current_profile_name_label

    def makeInputRow(self):
        import_row = QHBoxLayout()

        import_row.addWidget(QLabel('Into Profile:'))
        import_row.addWidget(self.into_profile_label)
        import_row.addWidget(QLabel('Deck:'))
        import_row.addWidget(self.currentProfileDeckCombo)
        import_row.addWidget(self.importButton)
        import_row.addWidget(QLabel('Map to Note Type:'))
        import_row.addWidget(self.note_type_selection_combo)
        import_row.addStretch(1)
        import_row.addWidget(self.tagCheckBox)

        return import_row


#############################################################################
# UI logic
#############################################################################


class MainDialog(MainDialogUI):
    def __init__(self):
        super().__init__()
        self.otherProfileCollection: Optional[Collection] = None
        self.connectElements()
        self.noteList.setAlternatingRowColors(True)
        self.noteList.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def connectElements(self):
        self.noteList.itemDoubleClicked.connect(self.previewCard)
        self.otherProfileDeckCombo.currentIndexChanged.connect(self.updateNotesList)
        self.importButton.clicked.connect(self.doImport)
        self.filterButton.clicked.connect(self.updateNotesList)
        self.otherProfileNamesCombo.currentIndexChanged.connect(self.openOtherCol)

    def previewCard(self):
        a = CroProPreviewer(parent=self, mw=mw)
        a.open()

    def show(self):
        super().show()
        self.populate_ui()

    def populate_ui(self):
        self.populate_note_type_selection_combo()
        self.populate_current_profile_decks()
        # 1) If the combo box is emtpy the window is opened for the first time.
        # 2) If it happens to contain the current profile name the user has switched profiles.
        if self.otherProfileNamesCombo.count() == 0 or self.otherProfileNamesCombo.findText(mw.pm.name) != -1:
            self.populate_other_profile_names()
            self.tagCheckBox.setChecked(config['tag_exported_cards'])
            self.into_profile_label.setText(mw.pm.name or 'Unknown')

    def populate_other_profile_names(self):
        logDebug("populating other profiles.")

        other_profile_names = getOtherProfileNames()
        if not other_profile_names:
            msg: str = 'This add-on only works if you have multiple profiles.'
            showInfo(msg)
            logDebug(msg)
            self.hide()
            return

        self.otherProfileNamesCombo.clear()
        self.otherProfileNamesCombo.addItems(other_profile_names)

    def populate_current_profile_decks(self):
        logDebug("populating current profile decks.")

        self.currentProfileDeckCombo.clear()
        selected_deck_id = mw.col.decks.selected()
        for index, deck in enumerate(getProfileDecks(mw.col)):
            self.currentProfileDeckCombo.addItem(deck['name'], deck['id'])
            if deck['id'] == selected_deck_id:
                self.currentProfileDeckCombo.setCurrentIndex(index)

    def populate_note_type_selection_combo(self):
        self.note_type_selection_combo.clear()
        for note_type in mw.col.models.all_names_and_ids():
            self.note_type_selection_combo.addItem(note_type.name, note_type.id)

    def closeOtherCol(self):
        if self.otherProfileCollection is not None:
            self.otherProfileCollection.close()
            self.otherProfileCollection = None

    def openOtherCol(self):
        # Close current collection object, if any
        self.closeOtherCol()

        self.otherProfileCollection = openProfileCollection(self.otherProfileNamesCombo.currentText())
        self.otherProfileDeckCombo.clear()
        for deck in getProfileDecks(self.otherProfileCollection):
            self.otherProfileDeckCombo.addItem(deck['name'], deck['id'])

    def updateNotesList(self):
        if self.otherProfileDeckCombo.count() < 1:
            return

        if self.otherProfileCollection is None:
            self.openOtherCol()

        self.noteList.clear()
        other_profile_deck_name = self.otherProfileDeckCombo.currentText()
        other_profile_did = self.otherProfileDeckCombo.currentData()
        logDebug(f"deck id: {other_profile_did}")
        found_note_count = 0
        displayed_note_count = 0
        if other_profile_deck_name:
            # deck was selected, fill list

            # build query string
            query = f'deck:"{trim(other_profile_deck_name)}"'  # quote name in case it has spaces

            # get filter text, if any
            filter_text = self.filterEdit.text()
            if filter_text:
                query += f' "{trim(filter_text)}"'

            note_ids = self.otherProfileCollection.findNotes(query)

            found_note_count = len(note_ids)
            limited_note_ids = note_ids[:config['max_displayed_notes']]
            displayed_note_count = len(limited_note_ids)
            # TODO: we could try to do this in a single sqlite query, but would be brittle
            for noteId in limited_note_ids:
                note = self.otherProfileCollection.getNote(noteId)
                item = QListWidgetItem()
                item.setText(' | '.join(htmlToTextLine(note[field_name])
                                        for field_name in note.keys()
                                        if not blocked_field(field_name) and note[field_name].strip())
                             )
                item.setData(Qt.UserRole, noteId)
                self.noteList.addItem(item)
        else:
            # deck was unselected, leave list cleared
            pass

        if displayed_note_count == found_note_count:
            self.noteCountLabel.setText(f'{found_note_count} notes found')
        else:
            self.noteCountLabel.setText(f'{found_note_count} notes found (displaying first {displayed_note_count})')

    def copyMediaFiles(self, new_note: Note, other_note: Note) -> Note:
        # check if there are any media files referenced by the note
        media_references = self.otherProfileCollection.media.filesInStr(other_note.mid, other_note.joinedFields())

        for filename in media_references:
            logDebug(f'media file: {filename}')
            filepath = os.path.join(self.otherProfileCollection.media.dir(), filename)

            # referenced media might not exist, in which case we skip it
            if not os.path.exists(filepath):
                continue

            logDebug(f'copying from {filepath}')
            this_col_filename = mw.col.media.addFile(filepath)
            # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
            # in which case we need to update the note.
            if this_col_filename != filename:
                logDebug(f'name conflict. new filename: {this_col_filename}')
                new_note.fields = [field.replace(filename, this_col_filename) for field in new_note.fields]

        return new_note

    def getSelectedNoteIDs(self):
        return [item.data(Qt.UserRole) for item in self.noteList.selectedItems()]

    def doImport(self):
        logDebug('beginning import')

        # get the note ids of all selected notes
        note_ids = self.getSelectedNoteIDs()

        # clear the selection
        self.noteList.clearSelection()

        logDebug(f'importing {len(note_ids)} notes')

        stat_success = 0
        stat_dupe = 0

        for nid in note_ids:
            # load the note
            logDebug(f'import note id {nid}')
            other_note: Note = self.otherProfileCollection.getNote(nid)

            # find a model in current profile that matches the name of model from other profile
            matching_model: NoteType = get_matching_model(other_note.model())
            if matching_model['id'] == 0:
                mw.col.models.add(matching_model)

            # create a new note object
            new_note = Note(mw.col, matching_model)
            logDebug(f'new note id={new_note.id}, mid={new_note.mid}')

            # set the deck that the note will generate cards into
            current_profile_deck_id = self.currentProfileDeckCombo.currentData()
            logDebug(f'current profile deck id: {current_profile_deck_id}')
            new_note.model()['did'] = current_profile_deck_id

            # copy field values into new note object
            new_note.fields = other_note.fields[:]  # list of strings, so clone it

            # copy field tags into new note object
            # TODO: add a switch
            new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

            if self.tagCheckBox.isChecked():
                other_note.addTag(config.get('exported_tag'))
                other_note.flush()

            # check if note is dupe of existing one
            if new_note.dupeOrEmpty():
                logDebug(f"note #{new_note.id} is duplicate. skipping.")
                stat_dupe += 1
                continue

            self.copyMediaFiles(new_note, other_note)
            mw.col.addNote(new_note)
            stat_success += 1

        if stat_success:
            mw.requireReset()
            self.statSuccessLabel.setText(f'{stat_success} notes successfully imported')
            self.statSuccessLabel.show()
        else:
            self.statSuccessLabel.hide()

        if stat_dupe:
            self.statDupeLabel.setText(f'{stat_dupe} notes were duplicates, and skipped')
            self.statDupeLabel.show()
        else:
            self.statDupeLabel.hide()

    def reject(self):
        self.closeOtherCol()  # TODO error?
        mw.maybeReset()
        QDialog.reject(self)


######################################################################
# Entry point
######################################################################

# init dialog
dialog: MainDialog = MainDialog()


def init():
    # create a new menu item
    action = QAction('Cross Profile Search and Import', mw)
    # set it to call show function when it's clicked
    action.triggered.connect(dialog.show)
    # and add it to the tools menu
    mw.form.menuTools.addAction(action)
