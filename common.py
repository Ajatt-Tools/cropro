# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
# TODO
import os
from typing import Optional, TextIO

from aqt import mw, gui_hooks

from .config import config

ADDON_NAME = "Cross Profile Search and Import"
ADDON_NAME_SHORT = "CroPro"
DEBUG_LOG_FILE_PATH = os.path.join(mw.pm.base, "cropro.log")
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

for directory in (WEB_DIR_PATH, USER_FILES_DIR_PATH, IMG_DIR_PATH):
    assert os.path.isdir(directory), f"Path to directory must be valid: {directory}"

for file in (CLOSE_ICON_PATH, PLAY_ICON_PATH):
    assert os.path.isfile(file), f"Path to file must be valid: {file}"


class LogDebug:
    _logfile: Optional[TextIO] = None
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        gui_hooks.profile_will_close.append(self.close)

    def write(self, msg: str) -> None:
        print(f"{ADDON_NAME_SHORT} debug: {msg}")
        if not config.enable_debug_log:
            # if disabled, don't write anything to the file, but still print to stdout.
            return
        if not self._logfile:
            print(f"{ADDON_NAME_SHORT} debug: opening log file {DEBUG_LOG_FILE_PATH}")
            self._logfile = open(DEBUG_LOG_FILE_PATH, "a")
        self._logfile.write(f"{msg}\n")
        self._logfile.flush()

    def __call__(self, *args, **kwargs):
        return self.write(*args, **kwargs)

    def close(self):
        if self._logfile and not self._logfile.closed:
            self.write("closing debug log.")
            self._logfile = self._logfile.close()
