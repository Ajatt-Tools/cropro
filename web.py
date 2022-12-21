# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
from typing import Any

from anki.sound import SoundOrVideoTag
from aqt import mw, gui_hooks
from aqt import sound

WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')


def get_previewer_css_relpath():
    addon_package = mw.addonManager.addonFromModule(__name__)
    return f"/_addons/{addon_package}/web/previewer.css"


def get_previewer_html():
    with open(os.path.join(WEB_DIR, 'previewer.html'), 'r', encoding='utf8') as f:
        return f.read()


def handle_js_messages(handled: tuple[bool, Any], message: str, _context: Any) -> tuple[bool, Any]:
    if handled[0] is False and message.startswith('cropro__play_file:'):
        file_path = message.split(':', maxsplit=1)[-1]
        sound.av_player.play_tags([SoundOrVideoTag(file_path), ])
        return True, None
    else:
        return handled


def init():
    mw.addonManager.setWebExports(__name__, r"(img|web)/.*\.(js|css|html|png|svg)")
    gui_hooks.webview_did_receive_js_message.append(handle_js_messages)
