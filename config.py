# Copyright: Ren Tatsumoto <tatsu at autistici.org>
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


config = CroProConfig()
