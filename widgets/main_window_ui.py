# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import AnkiQt
from aqt.qt import *

from .note_list import NoteList
from .search_bar import CroProSearchWidget
from .search_result_label import SearchResultLabel
from .status_bar import StatusBar
from .utils import ProfileNameLabel, NameIdComboBox, CroProPushButton

WIN_MIN_WIDTH = 900
WIN_MIN_HEIGHT = 480


class MainWindowUI(QMainWindow):
    name = "cropro_dialog"

    def __init__(self, ankimw: AnkiQt, window_title: str):
        super().__init__(parent=ankimw)
        self.setWindowTitle(window_title)
        self.search_bar = CroProSearchWidget(ankimw=ankimw)
        self.status_bar = StatusBar()
        self.search_result_label = SearchResultLabel()
        self.into_profile_label = ProfileNameLabel()
        self.current_profile_deck_combo = NameIdComboBox()
        self.edit_button = CroProPushButton("Edit")
        self.import_button = CroProPushButton("Import")
        self.page_prev = QPushButton('🞀')
        self.note_list = NoteList()
        self.page_skip = QPushButton('🞂')
        self.note_type_selection_combo = NameIdComboBox()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget(self)
        central_widget.setLayout(self.make_main_layout())
        self.setCentralWidget(central_widget)
        self.setMinimumSize(WIN_MIN_WIDTH, WIN_MIN_HEIGHT)

    def make_main_layout(self) -> QLayout:
        main_vbox = QVBoxLayout()
        main_vbox.addWidget(self.search_bar)
        main_vbox.addWidget(self.search_result_label)
        main_vbox.addLayout(self.make_note_row())
        main_vbox.addLayout(self.status_bar)
        main_vbox.addLayout(self.make_input_row())
        return main_vbox
    
    def make_note_row(self) -> QLayout:
        note_row = QHBoxLayout()
        self.page_prev.setFixedWidth(17)
        self.page_prev.setFixedHeight(45)
        self.page_prev.setEnabled(False)
        self.page_prev.setToolTip("Previous Page")
        self.page_skip.setFixedWidth(17)
        self.page_skip.setFixedHeight(45)
        self.page_skip.setEnabled(False)
        self.page_skip.setToolTip("Next Page")
        note_row.addWidget(self.page_prev)
        note_row.addWidget(self.note_list)
        note_row.addWidget(self.page_skip)
        note_row.setStretch(1, 1)
        return note_row


    def make_input_row(self) -> QLayout:
        import_row = QHBoxLayout()
        import_row.addWidget(QLabel("Into Profile:"))
        import_row.addWidget(self.into_profile_label)
        import_row.addWidget(QLabel("Deck:"))
        import_row.addWidget(self.current_profile_deck_combo)
        import_row.addWidget(QLabel("Map to Note Type:"))
        import_row.addWidget(self.note_type_selection_combo)
        import_row.addWidget(self.edit_button)
        import_row.addWidget(self.import_button)
        return import_row
