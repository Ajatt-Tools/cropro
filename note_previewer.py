# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import base64
import os.path
import re
from gettext import gettext as _
from typing import Iterable
from typing import Optional

from anki.notes import Note
from anki.sound import SoundOrVideoTag
from anki.utils import html_to_text_line
from aqt import mw
from aqt import sound
from aqt.qt import *
from aqt.webview import AnkiWebView

WEB_DIR = os.path.join(os.path.dirname(__file__), 'web')


def get_previewer_html() -> str:
    with open(os.path.join(WEB_DIR, 'previewer.html'), encoding='utf8') as f:
        return f.read()


def encode(s_bytes):
    return base64.b64encode(s_bytes).decode("ascii")


def filetype(file: str):
    return os.path.splitext(file)[-1]


class NotePreviewer(AnkiWebView):
    """Previews a note in a Form Layout using a webview."""
    _media_tag_regex = re.compile(r'\[sound:([^\[\]]+?\.[^\[\]]+?)]')
    _image_tag_regex = re.compile(r'<img [^<>]*src="([^"<>]+)"[^<>]*>')
    _css_relpath = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web/previewer.css"

    mw.addonManager.setWebExports(__name__, r"(img|web)/.*\.(js|css|html|png|svg)")

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._note_media_dir: Optional[str] = None
        self.set_title("Note previewer")
        self.disable_zoom()
        self.setProperty("url", QUrl("about:blank"))
        self.setMinimumSize(200, 320)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.set_bridge_command(self._handle_play_button_press, self)

    def load_note(self, note: Note, note_media_dir: str) -> None:
        self._note_media_dir = note_media_dir
        rows: list[str] = []
        for field_name, field_content in note.items():
            rows.append(
                f'<div class="name">{field_name}</div>'
                f'<div class="content">{self._create_html_row_for_field(field_content)}</div>'
            )
        self.stdHtml(
            get_previewer_html().replace('<!--CONTENT-->', ''.join(rows)),
            js=[],
            css=[self._css_relpath, ]
        )

    def _create_html_row_for_field(self, field_content: str) -> str:
        """Creates a row for the previewer showing the current note's field."""
        if audio_files := re.findall(self._media_tag_regex, field_content):
            return f'<div class="cropro__button_list">{self._make_play_buttons(audio_files)}</div>'
        elif image_files := re.findall(self._image_tag_regex, field_content):
            return f'<div class="cropro__image_list">{self._make_images(image_files)}</div>'
        else:
            return f'<span class="cropro__text_item">{html_to_text_line(field_content)}</span>'

    @staticmethod
    def _make_play_buttons(audio_files: Iterable[str]) -> str:
        return ''.join(
            """
            <button class="cropro__play_button" title="{}" onclick='pycmd("cropro__play_file:{}");'></button>
            """.format(_(f"Play file: {f}"), f, )
            for f in audio_files
        )

    def _make_images(self, image_files: Iterable[str]) -> str:
        return ''.join(
            f'<img alt="image:{os.path.basename(f)}" src="{self._image_as_base64_src(f)}"/>'
            for f in image_files
        )

    def _image_as_base64_src(self, file_name: str) -> str:
        with open(os.path.join(self._note_media_dir, file_name), 'rb') as f:
            return f'data:image/{filetype(file_name)};base64,{encode(f.read())}'

    def _handle_play_button_press(self, cmd: str):
        """Play audio files if a play button was pressed."""
        if cmd.startswith('cropro__play_file:'):
            file_name = os.path.basename(cmd.split(':', maxsplit=1)[-1])
            file_path = os.path.join(self._note_media_dir, file_name)
            return sound.av_player.play_tags([SoundOrVideoTag(file_path), ])
        else:
            return self.defaultOnBridgeCmd(cmd)
