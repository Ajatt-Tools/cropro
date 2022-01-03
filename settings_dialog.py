from typing import Iterable, Dict

from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom

from .widgets import ItemBox
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


class CroProSettingsDialog(QDialog):
    name = 'cropro_settings_dialog'

    def __init__(self, parent: QDialog) -> None:
        QDialog.__init__(self, parent)
        self._setup_ui()
        restoreGeom(self, self.name, adjustSize=True)
        self.exec()
        saveGeom(self, self.name)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(300)
        self.setWindowTitle("CroPro Settings")
        self.setLayout(self._make_layout())
        self.connect_widgets()
        self.add_tooltips()

    def _make_layout(self) -> QLayout:
        self.hidden_fields_box = ItemBox(parent=self, initial_values=config['hidden_fields'])
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.checkboxes: Dict[str, QCheckBox] = {
            key: QCheckBox(key.replace('_', ' ').capitalize())
            for key in fetch_toggleables()
        }

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

        layout = QFormLayout()
        layout.addRow("Max displayed notes", self.max_notes_edit)
        layout.addRow("Tag original cards with", self.tag_edit)
        layout.addRow("Hide fields matching", self.hidden_fields_edit)
        return layout

    def connect_widgets(self):
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)
        qconnect(self.hidden_fields_edit.textChanged, lambda: self.hidden_fields_box.new_item(self.hidden_fields_edit))

    def add_tooltips(self) -> None:
        self.hidden_fields_edit.setToolTip(
            "Hide fields whose names contain these words.\n"
            "Press space or comma to commit."
        )

    def accept(self) -> None:
        config[self.max_notes_edit.config_key] = self.max_notes_edit.value()
        config['exported_tag'] = self.tag_edit.text()
        config['hidden_fields'] = self.hidden_fields_box.values()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        write_config()
        QDialog.accept(self)
