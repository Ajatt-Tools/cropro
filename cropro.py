"""
Anki Add-on: Cross-Profile Search and Import
version 0.2.1
URL: https://ankiweb.net/shared/info/310394744
GitHub: https://github.com/rsimmons/anki-cropro

This add-on allows you to find and import notes from another profile into your currently loaded profile.
For example, you can make a "sentence bank" profile where you store thousands of cards generated by subs2srs,
and then use this add-on to search for and import cards with certain words into your main profile.
This helps keep your main profile uncluttered and free of large amounts of unneeded media.

GNU AGPL
Copyright (c) 2021 Ren Tatsumoto
Copyright (c) 2018 Russel Simmons
Original concept by CalculusAce, with help from Matt VS Japan (@mattvsjapan)

TODO:
- Handle case where user has only one profile
- Review duplicate checking: check by first field, or all fields?
- When matching model is found, verify field count (or entire map?)
"""

import json
import os.path
from anki.utils import htmlToTextLine
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo
from typing import Optional, TextIO

from .ajt_common import menu_root_entry
from .collection_manager import CollectionManager, sorted_decks_and_ids
from .config import config
from .note_importer import invalid_note_type, import_note, ImportResult
from .previewer import CroProPreviewer
from .widgets import SearchResultLabel, DeckCombo

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


def blocked_field(field_name: str) -> bool:
    field_name = field_name.lower()
    return any(badword.lower() in field_name for badword in config['bad_fields'])


#############################################################################
# UI layout
#############################################################################


class MainDialogUI(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(parent=mw, *args, **kwargs)

        self.statSuccessLabel = QLabel()
        self.statNoMatchingModelLabel = QLabel()
        self.statDupeLabel = QLabel()
        self.search_result_label = SearchResultLabel()
        self.into_profile_label = self.makeProfileNameLabel()
        self.currentProfileDeckCombo = DeckCombo()
        self.importButton = QPushButton('Import')
        self.tagCheckBox = QCheckBox("Tag cards as exported")
        self.filterEdit = QLineEdit()
        self.otherProfileNamesCombo = QComboBox()
        self.otherProfileDeckCombo = DeckCombo()
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
        main_vbox.addWidget(self.search_result_label)
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
                self.currentProfileDeckCombo,
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
        import_row.addWidget(QLabel('Map to Note Type:'))
        import_row.addWidget(self.note_type_selection_combo)
        import_row.addWidget(self.tagCheckBox)
        import_row.addStretch(1)
        import_row.addWidget(self.importButton)

        return import_row


#############################################################################
# UI logic
#############################################################################


class WindowState:
    def __init__(self, window: MainDialogUI):
        self.window = window
        self.json_filepath = os.path.join(os.path.dirname(__file__), 'window_state.json')
        self.map = {
            'other_profile_name': self.window.otherProfileNamesCombo,
            'other_profile_deck_name': self.window.otherProfileDeckCombo,
            'current_profile_deck': self.window.currentProfileDeckCombo,
            'current_profile_note_type': self.window.note_type_selection_combo,
        }
        self.state = dict()

    def save(self):
        for key, widget in self.map.items():
            self.state[key] = widget.currentText()
        with open(self.json_filepath, 'w') as of:
            json.dump(self.state, of, indent=4, ensure_ascii=False)

    def restore(self):
        if list(self.state.keys()) == list(self.map.keys()):
            for key, widget in self.map.items():
                widget.setCurrentText(self.state[key])
        else:
            if not os.path.isfile(self.json_filepath):
                return
            with open(self.json_filepath) as f:
                self.state = json.load(f)
            for key, widget in self.map.items():
                widget.setCurrentText(self.state[key])


class MainDialog(MainDialogUI):
    def __init__(self):
        super().__init__()
        self.window_state = WindowState(self)
        self.other_col = CollectionManager()
        self.connectElements()
        self.noteList.setAlternatingRowColors(True)
        self.noteList.setSelectionMode(QAbstractItemView.ExtendedSelection)

    def connectElements(self):
        qconnect(self.noteList.itemDoubleClicked, self.previewCard)
        qconnect(self.otherProfileDeckCombo.currentIndexChanged, self.updateNotesList)
        qconnect(self.importButton.clicked, self.doImport)
        qconnect(self.filterButton.clicked, self.updateNotesList)
        qconnect(self.filterEdit.editingFinished, self.updateNotesList)
        qconnect(self.otherProfileNamesCombo.currentIndexChanged, self.openOtherCol)

    def previewCard(self):
        a = CroProPreviewer(
            parent=self,
            mw=mw,
            col=self.other_col.col,
            selected_nids=self.getSelectedNoteIDs(),
        )
        a.open()

    def show(self):
        super().show()
        self.populate_ui()

    def populate_ui(self):
        self.statSuccessLabel.hide()
        self.statDupeLabel.hide()
        self.populate_note_type_selection_combo()
        self.populate_current_profile_decks()
        # 1) If the combo box is emtpy the window is opened for the first time.
        # 2) If it happens to contain the current profile name the user has switched profiles.
        if self.otherProfileNamesCombo.count() == 0 or self.otherProfileNamesCombo.findText(mw.pm.name) != -1:
            self.populate_other_profile_names()
            self.tagCheckBox.setChecked(config['tag_exported_cards'])
            self.into_profile_label.setText(mw.pm.name or 'Unknown')
        if not self.other_col.opened:
            self.openOtherCol()
        self.window_state.restore()

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

    def populate_note_type_selection_combo(self):
        self.note_type_selection_combo.clear()
        self.note_type_selection_combo.addItem(*invalid_note_type())
        for note_type in mw.col.models.all_names_and_ids():
            self.note_type_selection_combo.addItem(note_type.name, note_type.id)

    def openOtherCol(self):
        self.other_col.open(self.otherProfileNamesCombo.currentText())
        self.populate_other_profile_decks()

    def populate_current_profile_decks(self):
        logDebug("populating current profile decks...")
        self.currentProfileDeckCombo.set_decks(sorted_decks_and_ids(mw.col))

    def populate_other_profile_decks(self):
        logDebug("populating other profile decks...")
        self.otherProfileDeckCombo.set_decks([
            self.other_col.col_name_and_id(), *self.other_col.deck_names_and_ids(),
        ])

    def updateNotesList(self):
        self.noteList.clear()

        if not self.filterEdit.text() and not config['allow_empty_search']:
            return

        if not self.other_col.opened:
            self.openOtherCol()

        if self.otherProfileDeckCombo.count() < 1:
            return

        note_ids = self.other_col.find_notes(self.otherProfileDeckCombo.current_deck(), self.filterEdit.text())
        limited_note_ids = note_ids[:config['max_displayed_notes']]

        for note_id in limited_note_ids:
            note = self.other_col.get_note(note_id)
            item = QListWidgetItem()
            item.setText(' | '.join(
                htmlToTextLine(field_content)
                for field_name, field_content in note.items()
                if not blocked_field(field_name) and field_content.strip())
            )
            item.setData(Qt.UserRole, note_id)
            self.noteList.addItem(item)

        self.search_result_label.set_count(len(note_ids), len(limited_note_ids))

    def getSelectedNoteIDs(self):
        return [item.data(Qt.UserRole) for item in self.noteList.selectedItems()]

    def doImport(self):
        logDebug('beginning import')

        # get the note ids of all selected notes
        note_ids = self.getSelectedNoteIDs()

        # clear the selection
        self.noteList.clearSelection()

        logDebug(f'importing {len(note_ids)} notes')

        results = []

        for nid in note_ids:
            results.append(import_note(
                other_note=self.other_col.get_note(nid),
                model_id=self.note_type_selection_combo.currentData(),
                deck_id=self.currentProfileDeckCombo.currentData(),
                tag_exported=self.tagCheckBox.isChecked(),
            ))

        if successes := results.count(ImportResult.success):
            mw.requireReset()
            self.statSuccessLabel.setText(f'{successes} notes successfully imported')
            self.statSuccessLabel.show()
        else:
            self.statSuccessLabel.hide()

        if dupes := results.count(ImportResult.dupe):
            self.statDupeLabel.setText(f'{dupes} notes were duplicates, and skipped')
            self.statDupeLabel.show()
        else:
            self.statDupeLabel.hide()

    def reject(self):
        self.window_state.save()
        self.other_col.close()
        QDialog.reject(self)


######################################################################
# Entry point
######################################################################

# init dialog
dialog: MainDialog = MainDialog()


def init():
    # get AJT menu
    root_menu = menu_root_entry()
    # create a new menu item
    action = QAction('Cross Profile Search and Import', root_menu)
    # set it to call show function when it's clicked
    qconnect(action.triggered, dialog.show)
    # and add it to the tools menu
    root_menu.addAction(action)
