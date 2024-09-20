# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from types import SimpleNamespace
from typing import cast

from aqt import AnkiQt
from aqt.qt import *

from cropro.collection_manager import NameId
from cropro.widgets.col_search_opts import ColSearchOptions


class App(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_opts = ColSearchOptions(cast(AnkiQt, SimpleNamespace(pm=SimpleNamespace(name="Dummy"))))
        self.search_opts.set_decks([NameId("1", 1), NameId("2", 1)])
        self.search_opts.set_profile_names(["first", "second"])
        self.initUI()

    def initUI(self) -> None:
        self.setMinimumSize(640, 480)
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.search_opts)
        layout.addStretch(1)

    def hideEvent(self, _event: QHideEvent) -> None:
        print(self.search_opts.selected_profile_name())
        print(self.search_opts.current_deck())


def main() -> None:
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    main()
