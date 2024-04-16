# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import logging
import os
import pathlib

from aqt import mw

from .config import config

ADDON_NAME = "Cross Profile Search and Import"
ADDON_NAME_SHORT = "CroPro"
SUBS2SRS_LINK = "https://aur.archlinux.org/packages/subs2srs"
EXAMPLE_DECK_LINK = "https://tatsumoto.neocities.org/blog/setting-up-anki.html#import-an-example-mining-deck"
ADDON_GUIDE_LINK = "https://tatsumoto.neocities.org/blog/cross-profile-search-and-import.html"

ADDON_DIR_PATH = mw.addonManager.addonsFolder(mw.addonManager.addonFromModule(__name__))
WEB_DIR_PATH = os.path.join(ADDON_DIR_PATH, "web")
USER_FILES_DIR_PATH = os.path.join(ADDON_DIR_PATH, "user_files")
IMG_DIR_PATH = os.path.join(ADDON_DIR_PATH, "img")

WINDOW_STATE_FILE_PATH = os.path.join(USER_FILES_DIR_PATH, "window_state.json")
CLOSE_ICON_PATH = os.path.join(IMG_DIR_PATH, "close.png")
PLAY_ICON_PATH = os.path.join(IMG_DIR_PATH, "play-button.svg")
CONFIG_MD_PATH = os.path.join(ADDON_DIR_PATH, "config.md")

for directory in (WEB_DIR_PATH, USER_FILES_DIR_PATH, IMG_DIR_PATH):
    assert os.path.isdir(directory), f"Path to directory must be valid: {directory}"

for file in (CLOSE_ICON_PATH, PLAY_ICON_PATH, CONFIG_MD_PATH):
    assert os.path.isfile(file), f"Path to file must be valid: {file}"


class LogDebug:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.logger = mw.addonManager.get_logger(__name__)
        self.logger.setLevel(logging.DEBUG)

    def write(self, msg: str) -> None:
        if not config.enable_debug_log:
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
