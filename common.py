# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import Optional, TextIO

from aqt import mw, gui_hooks

from .config import config

ADDON_NAME = "Cross Profile Search and Import"
DEBUG_LOG_FILE_PATH = os.path.join(mw.pm.base, "cropro.log")
ADDON_DIR_PATH = mw.addonManager.addonsFolder(mw.addonManager.addonFromModule(__name__))
WEB_DIR_PATH = os.path.join(ADDON_DIR_PATH, "web")
WINDOW_STATE_FILE_PATH = os.path.join(ADDON_DIR_PATH, "user_files", "window_state.json")
CLOSE_ICON_PATH = os.path.join(ADDON_DIR_PATH, "img", "close.png")

for file in (WEB_DIR_PATH, WINDOW_STATE_FILE_PATH, CLOSE_ICON_PATH):
    assert os.path.isfile(file), f"Path must be valid: {file}"


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
        print("CroPro debug:", str(msg))
        if not config.enable_debug_log:
            return
        if not self._logfile:
            print(f'CroPro debug: opening log file "{DEBUG_LOG_FILE_PATH}"')
            self._logfile = open(DEBUG_LOG_FILE_PATH, "a")
        self._logfile.write(str(msg) + "\n")
        self._logfile.flush()

    def __call__(self, *args, **kwargs):
        return self.write(*args, **kwargs)

    def close(self):
        if self._logfile and not self._logfile.closed:
            self.write("closing debug log.")
            self._logfile = self._logfile.close()
