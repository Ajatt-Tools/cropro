# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom, disable_help_button

from .ajt_common.about_menu import tweak_window
from .common import ADDON_NAME, DEBUG_LOG_FILE_PATH
from .config import config
from .widgets.item_box import ItemBox
from .widgets.utils import CroProSpinBox


def make_checkboxes() -> dict[str, QCheckBox]:
    return {key: QCheckBox(key.replace("_", " ").capitalize()) for key in config.bool_keys()}


BUT_OK = QDialogButtonBox.StandardButton.Ok
BUT_CANCEL = QDialogButtonBox.StandardButton.Cancel


class CroProSettingsDialog(QDialog):
    name = "cropro_settings_dialog"

    def __init__(self, *args, **kwargs) -> None:
        QDialog.__init__(self, *args, **kwargs)
        disable_help_button(self)

        self.checkboxes = make_checkboxes()
        self.tag_edit = QLineEdit(config.tag_original_notes)
        self.max_notes_edit = CroProSpinBox(min_val=10, max_val=10_000, step=50, value=config.max_displayed_notes)

        self.hidden_fields_edit = QLineEdit()
        self.hidden_fields_edit.setPlaceholderText("New item")
        self.hidden_fields_box = ItemBox(parent=self, initial_values=config.hidden_fields)

        self.web_timeout_spinbox = CroProSpinBox(min_val=1, max_val=999, step=1, value=config.timeout_seconds)
        self.button_box = QDialogButtonBox(BUT_OK | BUT_CANCEL)

        self._setup_ui()
        self.connect_widgets()
        self.add_tooltips()

        tweak_window(self)
        restoreGeom(self, self.name, adjustSize=True)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(300)
        self.setWindowTitle(f"{ADDON_NAME} Settings")
        self.setLayout(self._make_layout())

    def _make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addLayout(self._make_form())
        layout.addStretch()
        layout.addWidget(self.button_box)
        return layout

    def _make_form(self) -> QLayout:
        layout = QFormLayout()
        layout.addRow("Max displayed notes", self.max_notes_edit)
        layout.addRow("Tag original cards with", self.tag_edit)
        layout.addRow("Web download timeout", self.web_timeout_spinbox)

        layout.addRow("Hide fields matching", self.hidden_fields_edit)
        layout.addRow(self.hidden_fields_box)

        for key, checkbox in self.checkboxes.items():
            layout.addRow(checkbox)
            checkbox.setChecked(config[key])
        return layout

    def connect_widgets(self):
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)
        qconnect(self.hidden_fields_edit.textChanged, lambda: self.hidden_fields_box.new_item(self.hidden_fields_edit))

    def add_tooltips(self) -> None:
        self.tag_edit.setToolTip(
            "When importing notes to the current collection,\n"
            "tag the original notes in the other collection\n"
            "so that you could easily find and delete them later.\n"
            "The tag that is added to the original notes is controlled by this setting.\n"
            "Left it empty to disable tagging."
        )
        self.hidden_fields_edit.setToolTip(
            "Hide fields whose names contain these words.\n" "Press space or comma to commit."
        )
        self.web_timeout_spinbox.setToolTip("Give up trying to connect to the remote server after this many seconds.")
        self.checkboxes["copy_card_data"].setToolTip(
            "Copy scheduling information of cards created from imported notes,\n"
            "such as due date, interval, queue, type, etc."
        )
        self.checkboxes["enable_debug_log"].setToolTip(
            "Write events related to this add-on to the log file.\n"
            f"The file can be found at: {DEBUG_LOG_FILE_PATH}\n"
            "Most users don't need to keep this option enabled."
        )
        self.checkboxes["skip_duplicates"].setToolTip(
            "Don't import a note if turns out to be a duplicate,\n"
            "i.e. it is already present in the current collection."
        )
        self.checkboxes["copy_tags"].setToolTip(
            "Copy tags from the original note to the imported note.\n"
            "When disabled, imported notes will contain no tags."
        )
        self.checkboxes["call_add_cards_hook"].setToolTip(
            "Call the `add_cards_did_add_note` hook after a note is imported.\n"
            "Enable this for compatibility with other add-ons\n"
            "that evaluate notes upon creation."
        )
        self.checkboxes["preview_on_right_side"].setToolTip(
            "When a note is selected,\n" "show a preview on the right side of the window."
        )
        self.checkboxes["allow_empty_search"].setToolTip(
            "Show a list of notes from the other collection\n" "even when the search bar is empty."
        )
        self.checkboxes["search_the_web"].setToolTip(
            "Instead of searching notes in a local profile,\n" "search the Internet instead."
        )

    def done(self, result: int) -> None:
        saveGeom(self, self.name)
        return super().done(result)

    def accept(self) -> None:
        config.max_displayed_notes = self.max_notes_edit.value()
        config.tag_original_notes = self.tag_edit.text()
        config.hidden_fields = self.hidden_fields_box.values()
        config.timeout_seconds = self.web_timeout_spinbox.value()
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        config.write_config()
        return super().accept()


def open_cropro_settings(parent: QWidget):
    from aqt import mw

    dialog = CroProSettingsDialog(parent=(parent or mw))
    dialog.exec()
