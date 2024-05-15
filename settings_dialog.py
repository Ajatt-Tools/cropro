# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
from aqt import Qt
from aqt.utils import restoreGeom, saveGeom, disable_help_button, showText, openFolder
from aqt.webview import AnkiWebView

from .ajt_common.about_menu import tweak_window
from .ajt_common.anki_field_selector import AnkiFieldSelector
from .ajt_common.utils import ui_translate
from .common import ADDON_NAME, LogDebug, CONFIG_MD_PATH
from .config import config
from .widgets.item_edit import ItemEditBox
from .widgets.utils import CroProSpinBox

logDebug = LogDebug()


def make_checkboxes() -> dict[str, QCheckBox]:
    """
    Create checkboxes and set initial checked states to the values in the config.
    """
    d = {}
    for key in config.bool_keys():
        d[key] = QCheckBox(ui_translate(key))
        d[key].setChecked(config[key])
    return d


BUT_HELP = QDialogButtonBox.StandardButton.Help
BUT_OK = QDialogButtonBox.StandardButton.Ok
BUT_CANCEL = QDialogButtonBox.StandardButton.Cancel


def make_remote_field_combos() -> dict[str, QComboBox]:
    d = {}
    for field_key, field_name in config.remote_fields.items():
        d[field_key] = AnkiFieldSelector()
        d[field_key].setCurrentText(field_name)
    return d


class CroProSettingsDialog(QDialog):
    name = "cropro_settings_dialog"

    def __init__(self, *args, **kwargs) -> None:
        QDialog.__init__(self, *args, **kwargs)
        disable_help_button(self)
        self.tab_view = QTabWidget()
        self.checkboxes = make_checkboxes()
        self.tag_edit = QLineEdit(config.exported_tag)
        self.max_notes_edit = CroProSpinBox(min_val=10, max_val=10_000, step=50, value=config.notes_per_page)
        self.hidden_fields = ItemEditBox("Hidden fields", initial_values=config.hidden_fields)
        self.web_timeout_spinbox = CroProSpinBox(min_val=1, max_val=999, step=1, value=config.timeout_seconds)
        # Currently, the longest sentence has a length of 196 letters (Shirokuma Cafe Outro full sub).
        self.sentence_min_length = CroProSpinBox(min_val=0, max_val=500, step=1, value=config.sentence_min_length)
        self.sentence_max_length = CroProSpinBox(min_val=0, max_val=999, step=1, value=config.sentence_max_length)
        self._remote_fields = make_remote_field_combos()
        self.preset_fields_ajt = QPushButton("Ajatt Preset")
        self.preset_fields_srs = QPushButton("Standard Sub2Srs Preset")
        self.button_box = QDialogButtonBox(BUT_HELP | BUT_OK | BUT_CANCEL)
        self._create_tabs()
        self._setup_ui()
        self.connect_widgets()
        self.add_tooltips()

        tweak_window(self)
        restoreGeom(self, self.name, adjustSize=True)

    def _setup_ui(self) -> None:
        self.setMinimumWidth(350)
        self.setWindowTitle(f"{ADDON_NAME} Settings")
        self.setLayout(self._make_layout())

    def _make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addWidget(self.tab_view)
        layout.addWidget(self.button_box)
        return layout

    def _create_tabs(self) -> None:
        self.tab_view.addTab(self._make_general_tab(), "General")
        self.tab_view.addTab(self._make_local_tab(), "Local Search")
        self.tab_view.addTab(self._make_web_tab(), "Web Search")
        self.tab_view.addTab(self._make_hl_tab(), "High Level")

    def _make_general_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout := QFormLayout())
        layout.addRow("Notes per page", self.max_notes_edit)
        layout.addRow(self.hidden_fields)
        layout.addRow(self.checkboxes["skip_duplicates"])
        layout.addRow(self.checkboxes["copy_tags"])
        layout.addRow(self.checkboxes["preview_on_right_side"])
        layout.addRow(self.checkboxes["search_the_web"])
        return widget

    def _make_local_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout := QFormLayout())
        layout.addRow(self.checkboxes["allow_empty_search"])
        layout.addRow(self.checkboxes["copy_card_data"])
        layout.addRow("Tag original cards with", self.tag_edit)
        return widget

    def _make_web_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout := QFormLayout())
        
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("From"))
        length_layout.addWidget(self.sentence_min_length)
        length_layout.addWidget(QLabel("To"))
        length_layout.addWidget(self.sentence_max_length)
        length_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addRow("Sentence Length", length_layout)
        
        field_name_group = QGroupBox("Field names")
        field_name_group.setCheckable(False)
        field_name_group.setLayout(names_layout := QFormLayout())
        for field_key, edit_widget in self._remote_fields.items():
            names_layout.addRow(ui_translate(field_key).title(), edit_widget)
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(self.preset_fields_ajt)
        qconnect(self.preset_fields_ajt.clicked, lambda: self.set_preset({
            "sentence_kanji": "SentKanji",
            "sentence_furigana": "SentFurigana",
            "sentence_eng": "SentEng",
            "sentence_audio": "SentAudio",
            "image": "Image",
            "notes": "Notes",
        }))
        preset_layout.addWidget(self.preset_fields_srs)
        qconnect(self.preset_fields_srs.clicked, lambda: self.set_preset({
            "sentence_kanji": "Expression",
            "sentence_furigana": "Reading",
            "sentence_eng": "English",
            "sentence_audio": "Audio",
            "image": "Image",
            "notes": "ID",
        }))
        names_layout.addRow(preset_layout)
        layout.addRow(field_name_group)
        return widget
      
    def _make_hl_tab(self) -> QWidget:
        widget = QWidget()
        widget.setLayout(layout := QFormLayout())
        layout.addRow("Web download timeout", self.web_timeout_spinbox)
        layout.addRow(self.checkboxes["enable_debug_log"])
        layout.addRow(self.checkboxes["call_add_cards_hook"])
        layout.addRow(hbox := QHBoxLayout())

        show_log_b = QPushButton("Show log")
        qconnect(show_log_b.clicked, lambda: showText(logDebug.read_contents(), parent=self, copyBtn=True))
        hbox.addWidget(show_log_b)

        open_dir_b = QPushButton("Open folder")
        qconnect(open_dir_b.clicked, lambda: openFolder(str(logDebug.cropro_log_dir())))
        hbox.addWidget(open_dir_b)

        return widget

    def connect_widgets(self):
        qconnect(self.button_box.accepted, self.accept)
        qconnect(self.button_box.rejected, self.reject)
        qconnect(self.button_box.helpRequested, self.show_help)

    def add_tooltips(self) -> None:
        self.tag_edit.setToolTip(
            "When importing notes to the current collection,\n"
            "tag the original notes in the other collection\n"
            "so that you could easily find and delete them later.\n"
            "The tag that is added to the original notes is controlled by this setting.\n"
            "Left it empty to disable tagging."
        )
        self.hidden_fields.setToolTip(
            "Hide fields whose names contain these words.\n" "Press space or comma to commit."
        )
        self.web_timeout_spinbox.setToolTip("Give up trying to connect to the remote server after this many seconds.")
        self.sentence_min_length.setToolTip("0 = No limit")
        self.sentence_max_length.setToolTip("0 = No limit")
        self.checkboxes["copy_card_data"].setToolTip(
            "Copy scheduling information of cards created from imported notes,\n"
            "such as due date, interval, queue, type, etc."
        )
        self.checkboxes["enable_debug_log"].setToolTip(
            "Write events related to this add-on to the log file.\n"
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

    def set_preset(self, name_dict: dict):
        for field_key, edit_widget in self._remote_fields.items():
            edit_widget.setCurrentText(name_dict[field_key])

    def show_help(self):
        help_win = QDialog(parent=self)
        help_win.setWindowModality(Qt.WindowModality.NonModal)
        help_win.setWindowTitle(f"{ADDON_NAME} - Settings Help")
        help_win.setLayout(QVBoxLayout())

        size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(help_win.sizePolicy().hasHeightForWidth())
        help_win.setSizePolicy(size_policy)
        help_win.setMinimumSize(240, 320)

        webview = AnkiWebView(parent=help_win)
        webview.setProperty("url", QUrl("about:blank"))
        with open(CONFIG_MD_PATH) as c_help:
            webview.stdHtml(c_help.read(), js=[])
        webview.setMinimumSize(320, 480)
        webview.disable_zoom()
        help_win.layout().addWidget(webview)

        button_box = QDialogButtonBox(BUT_OK)
        help_win.layout().addWidget(button_box)
        qconnect(button_box.accepted, help_win.accept)

        help_win.exec()

    def done(self, result: int) -> None:
        saveGeom(self, self.name)
        return super().done(result)

    def accept(self) -> None:
        config.notes_per_page = self.max_notes_edit.value()
        config.exported_tag = self.tag_edit.text()
        config.hidden_fields = self.hidden_fields.values()
        config.timeout_seconds = self.web_timeout_spinbox.value()
        config.sentence_min_length = self.sentence_min_length.value()
        config.sentence_max_length = (
            self.sentence_max_length.value()
            if self.sentence_max_length.value() > self.sentence_min_length.value()
            or self.sentence_max_length.value() == 0
            else self.sentence_min_length.value() + 1
        )
        for key, checkbox in self.checkboxes.items():
            config[key] = checkbox.isChecked()
        for field_key, edit_widget in self._remote_fields.items():
            config.remote_fields[field_key] = edit_widget.currentText()
        config.write_config()
        return super().accept()


def open_cropro_settings(parent: QWidget):
    from aqt import mw

    dialog = CroProSettingsDialog(parent=(parent or mw))
    dialog.exec()
