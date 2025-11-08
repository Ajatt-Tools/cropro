# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os

from aqt import mw

ADDON_NAME = "Cross Profile Search and Import"
ADDON_NAME_SHORT = "CroPro"
SUBS2SRS_LINK = "https://aur.archlinux.org/packages/subs2srs"
EXAMPLE_DECK_LINK = "https://tatsumoto.neocities.org/blog/setting-up-anki.html#import-an-example-mining-deck"
ADDON_GUIDE_LINK = "https://tatsumoto.neocities.org/blog/cross-profile-search-and-import.html"

if mw:
    ADDON_DIR_PATH = mw.addonManager.addonsFolder(mw.addonManager.addonFromModule(__name__))
else:
    ADDON_DIR_PATH = os.path.dirname(__file__)
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
