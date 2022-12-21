# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import base64
import os
from gettext import gettext as _
from typing import Any, Iterable

from anki.sound import SoundOrVideoTag
from aqt import mw, gui_hooks
from aqt import sound

WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')


def get_previewer_css_relpath() -> str:
    addon_package = mw.addonManager.addonFromModule(__name__)
    return f"/_addons/{addon_package}/web/previewer.css"


def get_previewer_html() -> str:
    with open(os.path.join(WEB_DIR, 'previewer.html'), encoding='utf8') as f:
        return f.read()


def make_play_buttons(audio_file_paths: Iterable[str]) -> str:
    return ''.join(
        """
        <button class="cropro__play_button" title="{}" onclick='pycmd("cropro__play_file:{}");'></button>
        """.format(_(f"Play file: {os.path.basename(f)}"), os.path.abspath(f), )
        for f in audio_file_paths
    )


def image_as_base64_src(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        return (
            f'data:image/{os.path.splitext(file_path)[-1]};base64,'
            f'{base64.b64encode(f.read()).decode("ascii")}'
        )


def make_images(img_file_paths: Iterable[str]) -> str:
    return ''.join([
        f'<img alt="image:{os.path.basename(f)}" src="{image_as_base64_src(f)}"/>'
        for f in img_file_paths
    ])


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
