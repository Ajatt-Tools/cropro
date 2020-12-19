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

from anki.models import NoteType
from anki.utils import htmlToTextLine
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from anki import Collection
from anki.notes import Note

#############################################################################
# BEGIN OPTIONS
#############################################################################

config: dict = mw.addonManager.getConfig(__name__)

max_displayed_notes = config.get('max_displayed_notes', 100)
enable_debug_log = config.get('enable_debug_log', True)
tag_exported_cards = config.get('tag_exported_cards', True)

#############################################################################
# END OPTIONS
#############################################################################

logfile: Optional[TextIO] = None


def logDebug(msg):
    if not enable_debug_log:
        return

    print('CroPro debug:', str(msg))

    global logfile
    if not logfile:
        fn = os.path.join(mw.pm.base, 'cropro.log')
        print(f'opening log file: {fn}')
        logfile = open(fn, 'a')
    logfile.write(str(msg) + '\n')
    logfile.flush()

def getOtherProfileNames() -> list:
    profiles = mw.pm.profiles()
    profiles.remove(mw.pm.name)
    return profiles


def openProfileCollection(name) -> Collection:
    # NOTE: this code is based on aqt/profiles.py; we can't really re-use what's there
    collectionFilename = os.path.join(mw.pm.base, name, 'collection.anki2')
    return Collection(collectionFilename)


def getProfileDecks(col: Collection):
    return sorted(col.decks.all(), key=lambda deck: deck["name"])


def equalModels(type1: NoteType, type2: NoteType):
    def getKeys(note_type: NoteType):
        return [field['name'] for field in note_type['flds']]

    return getKeys(type1) == getKeys(type2)


def copyNoteModel(model: NoteType):
    # do deep copy just to be safe. model is a dict, but might be nested
    model_copy = deepcopy(model)
    model_copy['id'] = 0
    return model_copy


def findMatchingModel(reference_model: NoteType) -> NoteType:
    # find the model name of the note
    required_model_name = reference_model.get('name')
    logDebug(f'model name: {required_model_name}')

    # find a model in current profile that matches the name of model from other profile
    matching_model: NoteType = mw.col.models.byName(required_model_name)
    if matching_model:
        logDebug(f"matching model found. id = {matching_model['id']}.")
        if not equalModels(matching_model, reference_model):
            logDebug("models have mismatching fields. copying the other model.")
            matching_model = copyNoteModel(reference_model)
            matching_model['name'] += ' cropro'
    else:
        logDebug('no matching model, copying')
        matching_model = copyNoteModel(reference_model)

    return matching_model


class MainDialogUI(QDialog):
    def __init__(self):
        super(MainDialogUI, self).__init__(parent=mw)

        self.noteCountLabel = QLabel('')
        self.currentProfileDeckCombo = QComboBox()
        self.importButton = QPushButton('Import')
        self.tagCheckBox = QCheckBox("Tag cards as exported")
        self.filterEdit = QLineEdit()
        self.otherProfileNamesCombo = QComboBox()
        self.otherProfileDeckCombo = QComboBox()
        self.otherProfileCollection: Optional[Collection] = None
        self.filterButton = QPushButton('Filter')
        self.noteListView = QListView()
        self.initUI()

    def initUI(self):
        self.filterEdit.setPlaceholderText('<text to filter by>')

        self.setLayout(self.makeMainLayout())
        self.setWindowTitle('Cross Profile Search and Import')

    def makeStatsRow(self):
        statsRow = QVBoxLayout()

        self.statSuccessLabel = QLabel()
        self.statSuccessLabel.setStyleSheet('QLabel { color : green; }')
        self.statSuccessLabel.hide()
        statsRow.addWidget(self.statSuccessLabel)

        self.statNoMatchingModelLabel = QLabel()
        self.statNoMatchingModelLabel.setStyleSheet('QLabel { color : red; }')
        self.statNoMatchingModelLabel.hide()
        statsRow.addWidget(self.statNoMatchingModelLabel)

        self.statDupeLabel = QLabel()
        self.statDupeLabel.setStyleSheet('QLabel { color : orange; }')
        self.statDupeLabel.hide()
        statsRow.addWidget(self.statDupeLabel)

        return statsRow

    def makeFilterRow(self):
        filterRow = QHBoxLayout()
        filterRow.addWidget(self.filterEdit)
        filterRow.addWidget(self.filterButton)
        return filterRow

    def makeMainLayout(self):
        mainVbox = QVBoxLayout()
        mainVbox.addLayout(self.makeOtherProfileDeckCombo())

        mainVbox.addLayout(self.makeFilterRow())
        mainVbox.addWidget(self.noteCountLabel)
        mainVbox.addWidget(self.noteListView)
        mainVbox.addLayout(self.makeStatsRow())
        mainVbox.addLayout(self.makeInputRow())
        return mainVbox

    def makeOtherProfileDeckCombo(self):
        otherProfileDeckRow = QHBoxLayout()
        otherProfileDeckRow.addWidget(QLabel('Import From Profile:'))
        otherProfileDeckRow.addWidget(self.otherProfileNamesCombo)
        otherProfileDeckRow.addWidget(QLabel('Deck:'))
        otherProfileDeckRow.addWidget(self.otherProfileDeckCombo)
        otherProfileDeckRow.addStretch(1)
        return otherProfileDeckRow

    def makeProfileNameLabel(self):
        currentProfileNameLabel = QLabel(mw.pm.name)
        currentProfileNameLabelFont = QFont()
        currentProfileNameLabelFont.setBold(True)
        currentProfileNameLabel.setFont(currentProfileNameLabelFont)
        return currentProfileNameLabel

    def makeInputRow(self):
        importRow = QHBoxLayout()
        importRow.addWidget(QLabel('Into Profile:'))
        importRow.addWidget(self.makeProfileNameLabel())
        importRow.addWidget(QLabel('Deck:'))
        importRow.addWidget(self.currentProfileDeckCombo)

        importRow.addWidget(self.importButton)
        importRow.addStretch(1)
        importRow.addWidget(self.tagCheckBox)
        return importRow


class MainDialog(MainDialogUI):
    def __init__(self):
        super().__init__()
        # TODO: this most likely should be a QListWidget instead
        self.noteListModel = QStandardItemModel(self.noteListView)
        self.connectElements()
        self.otherProfileNames: Optional[list] = None

    def connectElements(self):
        self.noteListView.setResizeMode(self.noteListView.Fixed)
        self.noteListView.setEditTriggers(self.noteListView.NoEditTriggers)
        self.noteListView.setModel(self.noteListModel)
        self.noteListView.setSelectionMode(self.noteListView.ExtendedSelection)

        self.noteListView.doubleClicked.connect(self.doImport)
        self.otherProfileDeckCombo.currentIndexChanged.connect(self.updateNotesList)
        self.importButton.clicked.connect(self.doImport)
        self.filterButton.clicked.connect(self.updateNotesList)
        self.otherProfileNamesCombo.currentIndexChanged.connect(self.otherProfileComboChange)

    def show(self):
        super().show()
        self.populateUI()

    def populateUI(self):
        if not self.otherProfileNames:
            self.otherProfileNames = getOtherProfileNames()
            if not self.otherProfileNames:
                msg: str = 'This add-on only works if you have multiple profiles.'
                showInfo(msg)
                logDebug(msg)
                self.hide()
                return

            self.otherProfileNamesCombo.addItems(self.otherProfileNames)
            self.populateCurrentProfileDecks()
            self.tagCheckBox.setChecked(tag_exported_cards)

    def otherProfileComboChange(self):
        newProfileName = self.otherProfileNamesCombo.currentText()
        self.handleSelectOtherProfile(newProfileName)

    def populateCurrentProfileDecks(self):
        selected_deck_id = mw.col.decks.selected()
        for index, deck in enumerate(getProfileDecks(mw.col)):
            self.currentProfileDeckCombo.addItem(deck['name'], deck['id'])
            if deck['id'] == selected_deck_id:
                self.currentProfileDeckCombo.setCurrentIndex(index)

    def updateNotesList(self):
        otherProfileDeckName = self.otherProfileDeckCombo.currentText()
        self.noteListModel.clear()
        foundNoteCount = 0
        displayedNoteCount = 0
        if otherProfileDeckName:
            # deck was selected, fill list

            # build query string
            query = 'deck:"' + otherProfileDeckName + '"'  # quote name in case it has spaces

            # get filter text, if any
            filterText = self.filterEdit.text()
            if filterText:
                query += ' "%s"' % filterText

            noteIds = self.otherProfileCollection.findNotes(query)
            foundNoteCount = len(noteIds)
            limitedNoteIds = noteIds[:max_displayed_notes]
            displayedNoteCount = len(limitedNoteIds)
            # TODO: we could try to do this in a single sqlite query, but would be brittle
            for noteId in limitedNoteIds:
                note = self.otherProfileCollection.getNote(noteId)
                item = QStandardItem()
                # item.setText(htmlToTextLine(note.fields[0]))
                item.setText(' | '.join(htmlToTextLine(f) for f in note.fields))
                item.setData(noteId)
                self.noteListModel.appendRow(item)
        else:
            # deck was unselected, leave list cleared
            pass

        if displayedNoteCount == foundNoteCount:
            self.noteCountLabel.setText('%d notes found' % foundNoteCount)
        else:
            self.noteCountLabel.setText('%d notes found (displaying first %d)' % (foundNoteCount, displayedNoteCount))

    def handleSelectOtherProfile(self, name):
        # Close current collection object, if any
        if self.otherProfileCollection:
            self.otherProfileCollection.close()
            self.otherProfileCollection = None

        self.otherProfileCollection = openProfileCollection(name)
        self.otherProfileDeckCombo.clear()
        other_profile_decks = [deck['name'] for deck in getProfileDecks(self.otherProfileCollection)]
        self.otherProfileDeckCombo.addItems(other_profile_decks)

    def copyMediaFiles(self, new_note: Note, other_note: Note) -> Note:
        # check if there are any media files referenced by the note
        media_references = self.otherProfileCollection.media.filesInStr(other_note.mid, other_note.joinedFields())

        for filename in media_references:
            logDebug(f'media file: {filename}')
            filepath = os.path.join(self.otherProfileCollection.media.dir(), filename)

            # referenced media might not exist, in which case we skip it
            if not os.path.exists(filepath):
                continue

            logDebug('copying from %s' % filepath)
            this_col_filename = mw.col.media.addFile(filepath)
            # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
            # in which case we need to update the note.
            if this_col_filename != filename:
                logDebug(f'name conflict. new filename: {this_col_filename}')
                new_note.fields = [field.replace(filename, this_col_filename) for field in new_note.fields]

        return new_note


    def doImport(self):
        logDebug('beginning import')

        # get the note ids of all selected notes
        note_ids = [self.noteListModel.itemFromIndex(idx).data() for idx in self.noteListView.selectedIndexes()]

        # clear the selection
        self.noteListView.clearSelection()

        logDebug('importing %d notes' % len(note_ids))

        statSuccess = 0
        statDupe = 0

        for nid in note_ids:
            # load the note
            logDebug('import note id %d' % nid)
            otherNote: Note = self.otherProfileCollection.getNote(nid)

            # find a model in current profile that matches the name of model from other profile
            matching_model: NoteType = self.findMatchingModel(otherNote.model())
            mw.col.models.add(matching_model)

            # create a new note object
            newNote = Note(mw.col, matching_model)
            logDebug('new note %s %s' % (newNote.id, newNote.mid))

            # set the deck that the note will generate cards into
            current_profile_deck_id = self.currentProfileDeckCombo.currentData()
            logDebug(f'current profile deck id: {current_profile_deck_id}')
            newNote.model()['did'] = current_profile_deck_id

            # copy field values into new note object
            newNote.fields = otherNote.fields[:]  # list of strings, so clone it

            # copy field tags into new note object
            # TODO: add a switch
            newNote.tags = [tag for tag in otherNote.tags if tag != 'leech']

            if self.tagCheckBox.isChecked():
                # TODO: control the tag
                otherNote.addTag('exported')
                otherNote.flush()

            # check if note is dupe of existing one
            if newNote.dupeOrEmpty():
                logDebug(f"note #{newNote['id']} is duplicate. skipping.")
                statDupe += 1
                continue

            self.copyMediaFiles(newNote, otherNote)

            mw.col.addNote(newNote)

            statSuccess += 1

        if statSuccess:
            mw.requireReset()
            self.statSuccessLabel.setText('%d notes successfully imported' % statSuccess)
            self.statSuccessLabel.show()
        else:
            self.statSuccessLabel.hide()

        if statDupe:
            self.statDupeLabel.setText('%d notes were duplicates, and skipped' % statDupe)
            self.statDupeLabel.show()
        else:
            self.statDupeLabel.hide()

    def reject(self):
        if self.otherProfileCollection:
            self.otherProfileCollection.close()

        mw.maybeReset()

        QDialog.reject(self)


dialog: MainDialog = MainDialog()


def addMenuItem():
    a = QAction(mw)
    a.setText('Cross Profile Search and Import')
    mw.form.menuTools.addAction(a)
    a.triggered.connect(dialog.show)


addMenuItem()
