from typing import Iterable, Dict, List

from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom, disable_help_button

from .config import config, write_config


def fetch_toggleables() -> Iterable[str]:
    for key, value in config.items():
        if type(value) == bool:
            yield key


def make_max_notes_spinbox() -> QSpinBox:
    box = QSpinBox()
    box.config_key = 'max_displayed_notes'
    box.setRange(10, 10_000)
    box.setValue(config[box.config_key])
    box.setSingleStep(50)
    return box


class ItemBox(QWidget):
    class ItemButton(QPushButton):
        _close_icon = QIcon(QPixmap(os.path.join(os.path.dirname(__file__), 'img', 'close.png')))

        def __init__(self, item_box: 'ItemBox', text: str):
            super().__init__(text)
            self.item_box = item_box
            self.setStyleSheet('''
                QPushButton {
                    background-color: #eef0f2;
                    color: #292c31;
                    border-radius: 12px;
                    padding: 2px 3px 3px;
                    border: 0px;
                }
            ''')
            self.setIcon(self._close_icon)
            self.setLayoutDirection(Qt.RightToLeft)
            qconnect(self.clicked, lambda: self.item_box.remove_item(text))

    def __init__(self, parent: QWidget, initial_values: List[str]):
        super().__init__(parent=parent)
        self.items = dict.fromkeys(initial_values)
        self.setLayout(self._make_layout())

    def values(self) -> List[str]:
        return list(self.items)

    def _make_layout(self) -> QLayout:
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        for text in self.items:
            self._add_item(text)
        self.layout.addStretch()
        return self.layout

    def _add_item(self, text: str) -> None:
        b = self.items[text] = self.ItemButton(self, text)
        self.layout.insertWidget(0, b)

    def remove_item(self, text: str) -> None:
        if widget := self.items.pop(text, None):
            widget.deleteLater()

    def new_item(self, edit: QLineEdit) -> None:
        separators = (',', ' ', ';')
        if (text := edit.text()).endswith(separators):
            text = text.strip(''.join(separators))
            if text and text not in self.items:
                self._add_item(text)
            edit.setText('')


class CroProSettingsDialog(QDialog):
    name = 'cropro_settings_dialog'

    def __init__(self, parent: QDialog) -> None:
        QDialog.__init__(self, parent)
        disable_help_button(self)
        self._setup_ui()
        restoreGeom(self, self.name, adjustSize=True)
        self.exec()
        saveGeom(self, self.name)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(300)
        self.setWindowTitle("CroPro Settings")
        self.setLayout(self._make_layout())
        self.add_tooltips()

    def _make_layout(self) -> QLayout:
        self.hidden_fields_box = ItemBox(parent=self, initial_values=config['hidden_fields'])
        self.checkboxes: Dict[str, QCheckBox] = {
            key: QCheckBox(key.replace('_', ' ').capitalize())
            for key in fetch_toggleables()
        }
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)

        layout = QVBoxLayout()
        layout.addLayout(self._make_form())
        layout.addWidget(self.hidden_fields_box)
        for key, checkbox in self.checkboxes.items():
            layout.addWidget(checkbox)
            checkbox.setChecked(config.get(key))
        layout.addStretch()
        layout.addWidget(self.button_box)
        return layout

    def _make_form(self) -> QFormLayout:
        self.tag_edit = QLineEdit(config['exported_tag'])
        self.max_notes_edit = make_max_notes_spinbox()
        self.hidden_fields_edit = QLineEdit()
        self.hidden_fields_edit.setPlaceholderText("New item")
        qconnect(
            self.hidden_fields_edit.textChanged,
            lambda: self.hidden_fields_box.new_item(self.hidden_fields_edit)
        )

        layout = QFormLayout()
        layout.addRow("Max displayed notes", self.max_notes_edit)
        layout.addRow("Tag original cards with", self.tag_edit)
        layout.addRow("Hide fields matching", self.hidden_fields_edit)
        return layout

    def add_tooltips(self) -> None:
        pass

    def accept(self) -> None:
        config[self.max_notes_edit.config_key] = self.max_notes_edit.value()
        config['exported_tag'] = self.tag_edit.text()
        config['hidden_fields'] = self.hidden_fields_box.values()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        write_config()
        QDialog.accept(self)
