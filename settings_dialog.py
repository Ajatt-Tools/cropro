from typing import Iterable, Dict

from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom, disable_help_button

from .config import config, write_config


def fetch_toggleables() -> Iterable[str]:
    for key, value in config.items():
        if type(value) == bool:
            yield key


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
        self.setMinimumWidth(400)
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
        for key, checkbox in self.checkboxes.items():
            layout.addWidget(checkbox)
            checkbox.setChecked(config.get(key))
        layout.addWidget(self.button_box)
        return layout

    def add_tooltips(self) -> None:
        pass

    def accept(self) -> None:
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        write_config()
        QDialog.accept(self)
