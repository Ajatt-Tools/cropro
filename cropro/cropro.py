"""
Anki Add-on: Cross-Profile Search and Import

This add-on allows you to find and import notes from another profile into your currently loaded profile.
For example, you can make a "sentence bank" profile where you store thousands of cards generated by subs2srs,
and then use this add-on to search for and import cards with certain words into your main profile.
This helps keep your main profile uncluttered and free of large amounts of unneeded media.

GNU AGPL
Copyright (c) 2021-2024 Ren Tatsumoto
Copyright (c) 2018 Russel Simmons
Original concept by CalculusAce, with help from Matt VS Japan (@mattvsjapan)

TODO:
- Handle case where user has only one profile
- Review duplicate checking: check by first field, or all fields?
- When matching model is found, verify field count (or entire map?)
"""

import json
from collections import defaultdict
from collections.abc import Iterable, MutableMapping, Sequence
from typing import Optional

import aqt
from anki.models import NotetypeDict
from anki.notes import Note, NoteId
from aqt import AnkiQt, gui_hooks, mw
from aqt.browser import Browser
from aqt.operations import CollectionOp, QueryOp
from aqt.qt import *
from aqt.utils import disable_help_button, openHelp, openLink, restoreGeom, saveGeom, showInfo, showWarning, tooltip

from .ajt_common.about_menu import menu_root_entry
from .ajt_common.consts import COMMUNITY_LINK
from .collection_manager import (
    NO_MODEL,
    WHOLE_COLLECTION,
    CollectionManager,
    NameId,
    get_other_profile_names,
    note_type_names_and_ids,
    sorted_decks_and_ids,
)
from .common import (
    ADDON_GUIDE_LINK,
    ADDON_NAME,
    ADDON_NAME_SHORT,
    EXAMPLE_DECK_LINK,
    SUBS2SRS_LINK,
    WINDOW_STATE_FILE_PATH,
    LogDebug,
)
from .config import config
from .edit_window import AddDialogLauncher
from .note_importer import NoteImporter, NoteTypeUnavailable
from .remote_search import CroProWebClientException, CroProWebSearchClient, RemoteNote
from .settings_dialog import open_cropro_settings
from .widgets.main_window_ui import MainWindowUI
from .widgets.note_pages import NoteListStatus
from .widgets.utils import CroProComboBox

logDebug = LogDebug()


#############################################################################
# UI logic
#############################################################################


class WindowState:
    _pm_name_to_win_state: MutableMapping[str, dict[str, str]]
    _cfg_key_to_widget: dict[str, CroProComboBox]

    def __init__(self, window: MainWindowUI) -> None:
        self._window = window
        self._json_filepath = WINDOW_STATE_FILE_PATH
        self._cfg_key_to_widget = {
            # Search bar settings
            "from_profile": self._window.search_bar.opts.other_profile_names_combo,
            "from_deck": self._window.search_bar.opts.other_profile_deck_combo,
            "sort_results": self._window.search_bar.opts.sort_results_combo,
            "to_deck": self._window.current_profile_deck_combo,
            "note_type": self._window.note_type_selection_combo,
            # Web search settings
            "web_category": self._window.search_bar.remote_opts.category_combo,
            "web_sort_by": self._window.search_bar.remote_opts.sort_combo,
            "web_jlpt_level": self._window.search_bar.remote_opts.jlpt_level_combo,
            "web_wanikani_level": self._window.search_bar.remote_opts.wanikani_level_combo,
        }
        self._pm_name_to_win_state = defaultdict(dict)

    def save(self) -> None:
        self._ensure_loaded()
        self._remember_current_values()
        self._forget_missing_profiles()
        self._write_state_to_disk()
        saveGeom(self._window, self._window.name)
        logDebug(f"saved window state.")

    def _write_state_to_disk(self) -> None:
        with open(self._json_filepath, "w", encoding="utf8") as of:
            json.dump(self._pm_name_to_win_state, of,
                      indent=4, ensure_ascii=False)

    def _remember_current_values(self) -> None:
        for key, widget in self._cfg_key_to_widget.items():
            if widget.currentText():
                # A combo box should have current text.
                # Otherwise, it apparently has no items set, and the value is invalid.
                self._pm_name_to_win_state[mw.pm.name][key] = widget.currentText(
                )

    def _ensure_loaded(self) -> bool:
        """
        Attempt to read the state json from disk. Return true on success.
        """
        if self._pm_name_to_win_state:
            # Already loaded, good.
            return True
        try:
            with open(self._json_filepath, encoding="utf8") as f:
                # File exists but the state hasn't been read yet.
                self._pm_name_to_win_state.update(json.load(f))
            return True
        except FileNotFoundError:
            # There's nothing to do.
            return False

    def restore(self) -> None:
        if self._ensure_loaded() and (profile_settings := self._pm_name_to_win_state.get(mw.pm.name)):
            for key, widget in self._cfg_key_to_widget.items():
                if value := profile_settings.get(key):
                    widget.setCurrentText(value)
        restoreGeom(self._window, self._window.name, adjustSize=True)
        logDebug(f"restored window state.")

    def _forget_missing_profiles(self) -> None:
        """If the user has deleted certain profiles, remove data about them from the dictionary."""
        for pm_name_to_remove in self._pm_name_to_win_state.keys() - mw.pm.profiles():
            del self._pm_name_to_win_state[pm_name_to_remove]


def nag_about_note_type(parent) -> int:
    return showInfo(
        title="Note importer",
        text="Note type must be assigned when importing from the Internet.\n\n"
        "Notes downloaded from the Internet do not come with a built-in note type. "
        f"An example Note Type can be downloaded [from our site]({EXAMPLE_DECK_LINK}).",
        type="critical",
        textFormat="markdown",
        parent=parent or mw,
    )


class SearchLock:
    """
    Class used to indicate that a search operation is in progress.
    Until a search operation finishes, don't allow subsequent searches.
    """

    def __init__(self, cropro: MainWindowUI) -> None:
        self._cropro = cropro
        self._searching = False

    def set_searching(self, searching: bool) -> None:
        self._searching = searching
        self._cropro.search_bar.setDisabled(searching)

    def is_searching(self) -> bool:
        return self._searching


class CroProMainWindow(MainWindowUI):
    def __init__(self, ankimw: AnkiQt) -> None:
        super().__init__(ankimw=ankimw, window_title=ADDON_NAME)
        self.window_state = WindowState(self)
        self.other_col = CollectionManager()
        self.web_search_client = CroProWebSearchClient()
        self._add_window_mgr = AddDialogLauncher(self)
        self._search_lock = SearchLock(self)
        self._importer = NoteImporter(web_client=self.web_search_client)
        self.connect_elements()
        self.setup_menubar()
        disable_help_button(self)
        self._add_global_shortcuts()
        self._add_tooltips()

    def _add_global_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+k"), self,
                  activated=lambda: self.search_bar.bar.focus_search_edit())  # type: ignore
        QShortcut(QKeySequence("Ctrl+i"), self,
                  activated=lambda: self.import_button.click())  # type: ignore
        QShortcut(QKeySequence("Ctrl+l"), self,
                  activated=lambda: self.note_list.set_focus())  # type: ignore

    def _add_tooltips(self) -> None:
        self.import_button.setToolTip("Add a new card (Ctrl+I)")
        self.edit_button.setToolTip("Edit card before adding")

    def setup_menubar(self) -> None:
        menu_bar: QMenuBar = self.menuBar()

        # Options menu
        tools_menu = menu_bar.addMenu("&Tools")

        tools_menu.addAction("Add-on Options", self._open_cropro_settings)

        toggle_web_search_act = tools_menu.addAction("Search the web")
        toggle_web_search_act.setCheckable(True)
        qconnect(toggle_web_search_act.triggered,
                 self._on_toggle_web_search_triggered)
        qconnect(tools_menu.aboutToShow, lambda: toggle_web_search_act.setChecked(
            config.search_the_web))

        tools_menu.addAction("Send query to Browser",
                             self._send_query_to_browser)

        close_act = tools_menu.addAction("Close", self.close)
        close_act.setShortcut(QKeySequence("Ctrl+q"))

        # Navigation menu
        nav_menu = menu_bar.addMenu("&Navigate")
        prev_act = nav_menu.addAction(
            "Previous page", lambda: self.note_list.flip_page(-1))
        prev_act.setShortcut(QKeySequence("Ctrl+Left"))
        next_act = nav_menu.addAction(
            "Next page", lambda: self.note_list.flip_page(+1))
        next_act.setShortcut(QKeySequence("Ctrl+Right"))

        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(
            "CroPro: Manual", lambda: openLink(ADDON_GUIDE_LINK))
        help_menu.addSeparator()
        help_menu.addAction("Anki: Searching", lambda: openHelp("searching"))
        help_menu.addAction("Note fields", self.show_target_note_fields)
        help_menu.addAction("Ask question", lambda: openLink(COMMUNITY_LINK))
        help_menu.addAction("subs2srs: Create sentence bank",
                            lambda: openLink(SUBS2SRS_LINK))

    def _send_query_to_browser(self) -> None:
        search_text = self.search_bar.bar.search_text()
        if not search_text:
            return tooltip("Nothing to do.", parent=self)
        browser = aqt.dialogs.open("Browser", mw)
        browser.activateWindow()
        browser.search_for(search_text)

    def _on_toggle_web_search_triggered(self, checked: bool) -> None:
        """
        In case the checkbox has been toggled, remember the setting.
        """
        if checked == config.search_the_web:
            # State hasn't changed.
            return
        logDebug(f"Web search option changed to {checked}")
        config.search_the_web = checked
        self._ensure_enabled_search_mode()
        self.reset_cropro_status()
        # save config to disk to remember checkbox state.
        config.write_config()

    def show_target_note_fields(self) -> None:
        if note_type := self.get_target_note_type():
            names = "\n".join(
                f"* {name}" for name in mw.col.models.field_names(note_type))
            showInfo(
                text=f"## Target note type has fields:\n\n{names}",
                textFormat="markdown",
                title=ADDON_NAME,
                parent=self,
            )
        else:
            showWarning(
                text="Target note type is not assigned.",
                title=ADDON_NAME,
                parent=self,
            )

    def get_target_note_type(self) -> Optional[NotetypeDict]:
        selected_note_type = self.current_model()
        if selected_note_type.id and selected_note_type.id > 0:
            return mw.col.models.get(selected_note_type.id)

    def connect_elements(self):
        qconnect(self.search_bar.opts.selected_profile_changed,
                 self.open_other_col)
        qconnect(self.search_bar.search_requested, self.perform_search)
        qconnect(self.edit_button.clicked, self.new_edit_win)
        qconnect(self.import_button.clicked, self.do_import)
        qconnect(self.note_list.status_changed, self.set_search_result_status)

    def populate_other_profile_names(self) -> None:
        if not self.search_bar.opts.needs_to_repopulate_profile_names():
            return

        logDebug("populating other profile names.")

        other_profile_names: list[str] = get_other_profile_names()
        if not other_profile_names:
            msg: str = "This add-on only works if you have multiple profiles."
            showInfo(msg, title=ADDON_NAME)
            logDebug(msg)
            self.hide()
            return

        self.search_bar.opts.set_profile_names(other_profile_names)

    def populate_note_type_selection_combo(self) -> None:
        """
        Set note types present in this collection.
        Called when profile opens.
        """
        logDebug("populating note type selector...")
        self.note_type_selection_combo.set_items(
            (NO_MODEL, *note_type_names_and_ids(mw.col)))

    def populate_current_profile_decks(self) -> None:
        """
        Set deck names present in this collection.
        Called when profile opens.
        """
        logDebug("populating current profile decks...")
        self.current_profile_deck_combo.set_items(sorted_decks_and_ids(mw.col))

    def open_other_col(self) -> None:
        selected_profile_name = self.search_bar.opts.selected_profile_name()
        if not selected_profile_name:
            # there are no collections in the combobox
            return
        if not self.other_col.is_opened or selected_profile_name != self.other_col.name:
            # the selected collection is not opened yet
            self.reset_cropro_status()
            self.other_col.open_collection(selected_profile_name)
            self.populate_other_profile_decks()

    def reset_cropro_status(self) -> None:
        self.status_bar.hide_counters()
        self.search_result_label.hide_count()
        self.note_list.clear_notes()
        logDebug("cleared search results")

    def populate_other_profile_decks(self) -> None:
        if not self.other_col.is_opened:
            # there's nothing to fill.
            return
        logDebug("populating other profile decks...")
        self.search_bar.opts.set_decks(
            [
                WHOLE_COLLECTION,  # the "whole collection" option goes first
                *self.other_col.deck_names_and_ids(),
            ]
        )

    def _should_abort_search(self) -> bool:
        return self._search_lock.is_searching() or not self.isVisible()

    def perform_search(self, search_text: str) -> None:
        if self._should_abort_search():
            return
        if config.search_the_web:
            return self.perform_remote_search(search_text)
        else:
            return self.perform_local_search(search_text)

    def perform_remote_search(self, search_text: str) -> None:
        """
        Search notes on a remote server.
        """
        self._ensure_enabled_search_mode()
        self.reset_cropro_status()

        if not search_text:
            self.search_result_label.set_nothing_to_do()
            return

        def search_notes(_col) -> Sequence[RemoteNote]:
            return self.web_search_client.search_notes(
                self.search_bar.get_request_args(
                    config.sentence_min_length, config.sentence_max_length)
            )

        def set_search_results(notes: Sequence[RemoteNote]) -> None:
            self.note_list.set_notes(notes)
            self._search_lock.set_searching(False)

        def on_exception(exception: Exception) -> None:
            self._search_lock.set_searching(False)

            if not isinstance(exception, CroProWebClientException):
                raise exception

            self.search_result_label.set_error(exception)

        self._search_lock.set_searching(True)
        (
            QueryOp(
                parent=self,
                op=search_notes,
                success=set_search_results,
            )
            .failure(on_exception)
            .without_collection()
            .with_progress("Searching notes...")
            .run_in_background()
        )

    def perform_local_search(self, search_text: str) -> None:
        """
        Search notes in a different Anki collection.
        """
        self._ensure_enabled_search_mode()
        self.reset_cropro_status()
        self.open_other_col()

        if not (search_text or config.allow_empty_search):
            self.search_result_label.set_nothing_to_do()
            return

        if not (self.search_bar.opts.selected_profile_name() and self.search_bar.opts.decks_populated()):
            # the user has only one profile or the combo boxes haven't been populated.
            return

        def search_notes(_col) -> Sequence[NoteId]:
            return self.other_col.find_notes(self.search_bar.opts.current_deck(), search_text)

        def set_search_results(note_ids: Sequence[NoteId]) -> None:
            self.note_list.set_notes(
                self._sort_col_search_results(
                    self.other_col.get_note(note_id) for note_id in note_ids)
            )
            self._search_lock.set_searching(False)

        self._search_lock.set_searching(True)
        (
            QueryOp(
                parent=self,
                op=search_notes,
                success=set_search_results,
            )
            .without_collection()
            .with_progress("Searching notes...")
            .run_in_background()
        )

    def _sort_col_search_results(self, results: Iterable[Note]) -> Sequence[Note]:
        sort_key = self.search_bar.opts.current_sort_key()
        if sort_key is None:
            return list(results)
        return sorted(results, key=sort_key(config))

    def set_search_result_status(self, status: NoteListStatus) -> None:
        self.search_result_label.set_count(*status)

    def current_model(self) -> NameId:
        return self.note_type_selection_combo.current_item()

    def current_deck(self) -> NameId:
        return self.current_profile_deck_combo.current_item()

    def do_import(self) -> None:
        logDebug("beginning import")

        # get selected notes
        notes = self.note_list.selected_notes()

        # clear the selection
        self.note_list.clear_selection()

        logDebug(f"importing {len(notes)} notes")

        def on_failure(ex: Exception) -> None:
            logDebug("import failed")
            if isinstance(ex, NoteTypeUnavailable):
                nag_about_note_type(self)
                return
            raise ex

        def on_success(_) -> None:
            results = self._importer.move_results()
            self.status_bar.set_import_status(results)
            if config.call_add_cards_hook:
                for note in results.successes:
                    if note.id > 0:
                        gui_hooks.add_cards_did_add_note(note)
            logDebug("import finished")

        (
            CollectionOp(
                parent=self,
                op=lambda col: self._importer.import_notes(
                    col=col,
                    notes=notes,
                    model=self.current_model(),
                    deck=self.current_deck(),
                ),
            )
            .success(on_success)
            .failure(on_failure)
            .run_in_background()
        )

    def new_edit_win(self) -> None:
        if len(selected_notes := self.note_list.selected_notes()) > 0:
            self._add_window_mgr.create_window(selected_notes[-1])
        else:
            tooltip("No note selected.", period=1000, parent=self)

    def showEvent(self, event: QShowEvent) -> None:
        logDebug("show event received")
        self.status_bar.hide_counters()
        self.into_profile_label.setText(mw.pm.name or "Unknown")
        self.window_state.restore()
        self._ensure_enabled_search_mode()
        return super().showEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        logDebug("close event received")
        self.window_state.save()
        return super().closeEvent(event)

    def _ensure_enabled_search_mode(self) -> None:
        self.search_bar.set_web_mode(config.search_the_web)

    def _open_cropro_settings(self) -> None:
        open_cropro_settings(parent=self)
        # the "search_the_web" setting may have changed
        self._ensure_enabled_search_mode()
        if config.search_the_web:
            self.search_for(self.search_bar.bar.search_text())

    def on_profile_will_close(self):
        self.close()
        self.other_col.close_all()

    def on_profile_did_open(self) -> None:
        # clean state from the previous profile if it was set.
        self.search_bar.clear_all()
        self.note_list.clear_notes()
        # setup search bar
        self.populate_other_profile_names()
        self.open_other_col()
        # setup import conditions
        self.populate_current_profile_decks()
        self.populate_note_type_selection_combo()

    def search_for(self, search_text: str) -> None:
        self.show()
        self.setFocus()
        self.search_bar.bar.set_search_text(search_text)
        self.search_bar.search_requested.emit(search_text)

    def setup_browser_menu(self, browser: Browser) -> None:
        """Add a browser entry"""
        # This is the "Go" menu.
        browser.form.menuJump.addSeparator()
        action = browser.form.menuJump.addAction(
            f"Look up in {ADDON_NAME_SHORT}")
        qconnect(action.triggered, lambda: self.search_for(
            browser.current_search()))


######################################################################
# Entry point
######################################################################


def init():
    # init dialog
    d = mw._cropro_main_dialog = CroProMainWindow(ankimw=mw)
    # get AJT menu
    root_menu = menu_root_entry()
    # create a new menu item
    action = QAction(ADDON_NAME, root_menu)
    # set it to call show function when it's clicked
    qconnect(action.triggered, d.show)
    # and add it to the tools menu
    root_menu.addAction(action)
    # react to anki's state changes
    gui_hooks.profile_will_close.append(d.on_profile_will_close)
    gui_hooks.profile_did_open.append(d.on_profile_did_open)
    # add an action to the Browser's "Go" menu.
    gui_hooks.browser_menus_did_init.append(d.setup_browser_menu)
