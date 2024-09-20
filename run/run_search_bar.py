# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from types import SimpleNamespace
from typing import cast

from aqt import AnkiQt
from aqt.qt import *

from cropro.widgets.search_bar import CroProSearchWidget


def on_search_requested(text: str):
    print(text)


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_bar = CroProSearchWidget(cast(AnkiQt, SimpleNamespace(pm=SimpleNamespace(name="Dummy"))))
        self.initUI()
        qconnect(self.search_bar.search_requested, on_search_requested)
        # self.search_bar.set_profile_names(["User 1", "subs2srs", "dumpster"])
        # self.search_bar.set_decks([NameId("History", 1), NameId("Math", 2)])

    def initUI(self):
        self.setMinimumSize(640, 480)
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.search_bar)
        layout.addStretch(1)


def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    main()
