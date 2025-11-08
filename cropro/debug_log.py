# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import logging
import pathlib

from aqt import mw

from .common import ADDON_NAME_SHORT
from .config import CroProConfig


class LogDebug:
    _instance = None
    _cfg: CroProConfig

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: CroProConfig):
        if mw is None:
            # anki isn't running
            self.logger = logging.getLogger(name=f"{ADDON_NAME_SHORT} (no anki)")
        else:
            self.logger = mw.addonManager.get_logger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self._cfg = config

    def write(self, msg: str) -> None:
        if not self._cfg.enable_debug_log:
            # if disabled, don't write anything.
            return
        self.logger.debug(msg)

    def __call__(self, msg: str) -> None:
        return self.write(msg)

    def read_contents(self) -> str:
        """
        Return the contents of the log file, if it exists.
        """
        try:
            with open(self.cropro_log_path(), encoding="utf-8") as lf:
                return lf.read()
        except FileNotFoundError:
            return "<Log file doesn't exist>"

    @staticmethod
    def cropro_log_dir() -> pathlib.Path:
        return mw.addonManager.logs_folder(__name__)

    @classmethod
    def cropro_log_path(cls) -> pathlib.Path:
        """
        Return path to the log file, it can be found.
        """
        for entry in cls.cropro_log_dir().iterdir():
            if entry.is_file() and entry.name.endswith(".log"):
                return entry
        raise FileNotFoundError("No log file found.")
