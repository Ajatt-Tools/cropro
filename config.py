# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Optional

from .ajt_common.addon_config import AddonConfigManager


class CroProConfig(AddonConfigManager):
    def tag_original_notes(self) -> Optional[str]:
        """
        Tag that is added to original notes (in the other profile)
        to mark that they have been copied to the current profile.
        """
        if self['tag_original_notes'] and (tag := self['exported_tag']):
            return tag

    @property
    def allow_empty_search(self) -> bool:
        return self["allow_empty_search"]

    @property
    def search_the_web(self) -> bool:
        return self["search_the_web"]

    @search_the_web.setter
    def search_the_web(self, value: bool):
        self["search_the_web"] = bool(value)

    @property
    def max_displayed_notes(self) -> int:
        return self["max_displayed_notes"]


config = CroProConfig()
