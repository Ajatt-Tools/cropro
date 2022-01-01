from typing import Iterable, Dict

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
        self.checkboxes: Dict[str, QCheckBox] = {
            key: QCheckBox(key.replace('_', ' ').capitalize())
            for key in fetch_toggleables()
        }
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)

        layout = QVBoxLayout()
        layout.addLayout(self._make_form())
        for key, checkbox in self.checkboxes.items():
            layout.addWidget(checkbox)
            checkbox.setChecked(config.get(key))
        layout.addWidget(self.button_box)
        return layout

    def _make_form(self) -> QFormLayout:
        self.max_notes_edit = make_max_notes_spinbox()
        layout = QFormLayout()
        layout.addRow("Max displayed notes", self.max_notes_edit)
        return layout

    def add_tooltips(self) -> None:
        pass

    def accept(self) -> None:
        config[self.max_notes_edit.config_key] = self.max_notes_edit.value()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        write_config()
        QDialog.accept(self)
