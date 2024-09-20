# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import json
import pathlib

from cropro.config import CroProConfig


class NoAnkiConfig(CroProConfig):
    """
    Loads the default config without starting Anki.
    """

    def _set_underlying_dicts(self) -> None:
        path = pathlib.Path(__file__).parent.parent.joinpath("cropro", "config.json")
        with open(path) as f:
            self._default_config = self._config = json.load(f)
