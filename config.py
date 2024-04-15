# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional

from .ajt_common.addon_config import AddonConfigManager


class CroProConfig(AddonConfigManager):
    @property
    def notes_per_page(self) -> int:
        return self["notes_per_page"]

    @notes_per_page.setter
    def notes_per_page(self, new_value: int) -> None:
        self["notes_per_page"] = new_value

    @property
    def hidden_fields(self) -> list[str]:
        """
        A list of fields that won't be displayed in the note list.
        """
        return self["hidden_fields"]

    @hidden_fields.setter
    def hidden_fields(self, new_values: list[str]) -> None:
        self["hidden_fields"] = new_values

    @property
    def skip_duplicates(self) -> bool:
        """
        If a note is a duplicate, it won't be imported.
        """
        return self["skip_duplicates"]

    @property
    def copy_tags(self) -> bool:
        return self["copy_tags"]

    @property
    def show_note_preview(self) -> bool:
        """
        Whether to preview notes or not.
        """
        return self["show_note_preview"]

    @property
    def search_online(self) -> bool:
        """
        Whether to search the web or a local collection.
        """
        return self["search_online"]

    @search_online.setter
    def search_online(self, value: bool) -> None:
        self["search_online"] = bool(value)

    @property
    def show_extended_filters(self) -> bool:
        """
        Whether to show the filters on the top.
        """
        return self["show_extended_filters"]

    @show_extended_filters.setter
    def show_extended_filters(self, value: bool) -> None:
        self["show_extended_filters"] = bool(value)
    
    @property
    def show_help_buttons(self) -> bool:
        return self["show_help_buttons"]

    @property
    def import_source_info(self) -> bool:
        return self["import_source_info"]

    @property
    def fetch_anki_card_media(self) -> bool:
        return self["fetch_anki_card_media"]

    @property
    def allow_empty_search(self) -> bool:
        """
        Perform search with empty search bar.
        Could be used to transfer all notes at once, although not really practical.
        """
        return self["allow_empty_search"]

    @property
    def copy_card_data(self) -> bool:
        """
        Copy review-related info, such as due date and interval.
        """
        return self["copy_card_data"]

    @property
    def exported_tag(self) -> Optional[str]:
        """
        Tag that is added to original notes (in the other profile)
        to mark that they have been copied to the current profile.
        """
        return self["exported_tag"].strip()

    @exported_tag.setter
    def exported_tag(self, new_value: str) -> None:
        self["exported_tag"] = new_value.strip()

    @property
    def timeout_seconds(self) -> int:
        """
        Give up trying to connect to the remote server after this many seconds.
        """
        return self["timeout_seconds"]

    @timeout_seconds.setter
    def timeout_seconds(self, timeout: int) -> None:
        self["timeout_seconds"] = timeout

    @property
    def enable_debug_log(self) -> bool:
        return self["enable_debug_log"]

    @property
    def call_add_cards_hook(self) -> bool:
        """
        Call the `add_cards_did_add_note` hook after a note is imported.
        """
        return self["call_add_cards_hook"]


config = CroProConfig()
