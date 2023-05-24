# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import mw
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom, disable_help_button

from .ajt_common.about_menu import tweak_window, menu_root_entry
from .common import ADDON_NAME
from .config import config
from .widgets import ItemBox, SpinBox


def make_checkboxes() -> dict[str, QCheckBox]:
    return {key: QCheckBox(key.replace('_', ' ').capitalize()) for key in config.bool_keys()}


class CroProSettingsDialog(QDialog):
    name = 'cropro_settings_dialog'

    def __init__(self, *args, **kwargs) -> None:
        QDialog.__init__(self, *args, **kwargs)
        disable_help_button(self)
        self._setup_ui()
        tweak_window(self)
        restoreGeom(self, self.name, adjustSize=True)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(300)
        self.setWindowTitle(f"{ADDON_NAME} Settings")
        self.setLayout(self._make_layout())
        self.connect_widgets()
        self.add_tooltips()

    def _make_layout(self) -> QLayout:
        self.hidden_fields_box = ItemBox(parent=self, initial_values=config['hidden_fields'])
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.checkboxes = make_checkboxes()

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
        self.max_notes_edit = SpinBox(min_val=10, max_val=10_000, step=50, value=config['max_displayed_notes'])
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

    def done(self, result: int) -> None:
        saveGeom(self, self.name)
        return super().done(result)

    def accept(self) -> None:
        config['max_displayed_notes'] = self.max_notes_edit.value()
        config['exported_tag'] = self.tag_edit.text()
        config['hidden_fields'] = self.hidden_fields_box.values()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        config.write_config()
        return super().accept()


def init():
    def on_open_settings():
        dialog = CroProSettingsDialog(parent=mw)
        dialog.exec()

    root_menu = menu_root_entry()
    action = root_menu.addAction(f"{ADDON_NAME} Options...")
    qconnect(action.triggered, on_open_settings)
