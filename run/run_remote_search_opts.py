# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from cropro.widgets.remote_search_opts import RemoteSearchOptions


class App(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test")
        self.search_opts = RemoteSearchOptions()
        self.initUI()

    def initUI(self):
        self.setMinimumSize(640, 480)
        self.setLayout(layout := QVBoxLayout())
        layout.addWidget(self.search_opts)
        layout.addStretch(1)

    def hideEvent(self, event: QHideEvent):
        print(self.search_opts.category_combo.currentText())
        print(self.search_opts.sort_combo.currentText())
        print(self.search_opts.jlpt_level_combo.currentText())
        print(self.search_opts.wanikani_level_combo.currentText())


def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    app.exec()
    sys.exit()


if __name__ == "__main__":
    main()
