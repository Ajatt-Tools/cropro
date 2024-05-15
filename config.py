# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional

from .ajt_common.addon_config import AddonConfigManager, ConfigSubViewBase


class RemoteFieldsConfig(ConfigSubViewBase):
    _view_key: str = "remote_fields"

    @property
    def sentence_kanji(self) -> str:
        return self["sentence_kanji"]

    @property
    def sentence_furigana(self) -> str:
        return self["sentence_furigana"]

    @property
    def sentence_eng(self) -> str:
        return self["sentence_eng"]

    @property
    def sentence_audio(self) -> str:
        return self["sentence_audio"]

    @property
    def image(self) -> str:
        return self["image"]

    @property
    def notes(self) -> str:
        return self["notes"]


class CroProConfig(AddonConfigManager):
    def __init__(self, default: bool = False):
        super().__init__(default)
        self._remote_fields = RemoteFieldsConfig(default)

    @property
    def remote_fields(self) -> RemoteFieldsConfig:
        return self._remote_fields

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
    def allow_empty_search(self) -> bool:
        """
        Perform search with empty search bar.
        Could be used to transfer all notes at once, although not really practical.
        """
        return self["allow_empty_search"]

    @property
    def search_the_web(self) -> bool:
        """
        Whether to search the web or a local collection.
        """
        return self["search_the_web"]

    @search_the_web.setter
    def search_the_web(self, value: bool) -> None:
        self["search_the_web"] = bool(value)

    @property
    def sentence_min_length(self) -> bool:
        """
        Minimum count of letters in the sentence for the card to be shown
        """
        return self["sentence_min_length"]

    @sentence_min_length.setter
    def sentence_min_length(self, new_value: int) -> None:
        self["sentence_min_length"] = new_value

    @property
    def sentence_max_length(self) -> bool:
        """
        Maximum count of letters in the sentence for the card to be shown
        """
        return self["sentence_max_length"]

    @sentence_max_length.setter
    def sentence_max_length(self, new_value: int) -> None:
        self["sentence_max_length"] = new_value

    @property
    def max_displayed_notes(self) -> int:
        """
        Minimum count of letters in the sentence for the card to be shown
        """
        return self["sentence_min_length"]

    @sentence_min_length.setter
    def sentence_min_length(self, new_value: int) -> None:
        self["sentence_min_length"] = new_value

    @property
    def sentence_max_length(self) -> bool:
        """
        Maximum count of letters in the sentence for the card to be shown
        """
        return self["sentence_max_length"]

    @sentence_max_length.setter
    def sentence_max_length(self, new_value: int) -> None:
        self["sentence_max_length"] = new_value

    @property
    def notes_per_page(self) -> int:
        """
        How many search results to display on one page
        """
        return self["notes_per_page"]

    @notes_per_page.setter
    def notes_per_page(self, new_value: int) -> None:
        self["notes_per_page"] = new_value

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
    def hidden_fields(self) -> list[str]:
        """
        A list of fields that won't be displayed in the note list.
        """
        return self["hidden_fields"]

    @hidden_fields.setter
    def hidden_fields(self, new_values: list[str]) -> None:
        self["hidden_fields"] = new_values

    @property
    def preview_on_right_side(self) -> bool:
        """
        Whether to preview notes or not.
        """
        return self["preview_on_right_side"]

    @property
    def enable_debug_log(self) -> bool:
        return self["enable_debug_log"]

    @property
    def copy_card_data(self) -> bool:
        """
        Copy review-related info, such as due date and interval.
        """
        return self["copy_card_data"]

    @property
    def copy_tags(self) -> bool:
        return self["copy_tags"]

    @property
    def skip_duplicates(self) -> bool:
        """
        If a note is a duplicate, it won't be imported.
        """
        return self["skip_duplicates"]

    @property
    def call_add_cards_hook(self) -> bool:
        """
        Call the `add_cards_did_add_note` hook after a note is imported.
        """
        return self["call_add_cards_hook"]


config = CroProConfig()
