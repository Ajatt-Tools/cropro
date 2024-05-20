# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import base64
import io
import os.path
import re
import urllib.parse
from collections.abc import Iterable
from gettext import gettext as _
from typing import Optional

from anki.notes import Note
from anki.sound import SoundOrVideoTag
from anki.utils import html_to_text_line
from aqt import mw
from aqt.qt import *
from aqt.webview import AnkiWebView

from ..ajt_common.media import find_sounds, find_images
from ..remote_search import RemoteNote, RemoteMediaInfo

RE_DANGEROUS = re.compile(r'[\'"<>]+')
QUOTE_SAFE = ":/%"


def name_attr_strip(file_name: str):
    return re.sub(RE_DANGEROUS, " ", os.path.basename(file_name)).strip()


def img2b64(s_bytes):
    return base64.b64encode(s_bytes).decode("ascii")


def filetype(file: str):
    return os.path.splitext(file)[-1]


def format_remote_image(image: RemoteMediaInfo) -> str:
    return (
        f'<img src="{urllib.parse.quote(image.url, safe=QUOTE_SAFE)}" alt="remote image">'
        if image.is_valid_url()
        else ""
    )


def format_local_images(note: Note, image_file_names: Iterable[str]) -> str:
    def image_as_base64_src(file_name: str) -> str:
        with open(os.path.join(note.col.media.dir(), file_name), "rb") as f:
            return f"data:image/{filetype(file_name)};base64,{img2b64(f.read())}"

    return "".join(
        f'<img alt="image:{name_attr_strip(file_name)}" src="{image_as_base64_src(file_name)}"/>'
        for file_name in image_file_names
    )


def format_remote_audio(audio: RemoteMediaInfo):
    if not audio.is_valid_url():
        return ""
    element_id = f"cropro__remote_{urllib.parse.quote(audio.file_name)}"
    return """
    <audio preload="auto" id="{}" src="{}"></audio>
    <button class="cropro__play_button" title="{}" onclick='{}'></button>
    """.format(
        element_id,
        urllib.parse.quote(audio.url, safe=QUOTE_SAFE),
        _(f"Play file: {name_attr_strip(audio.file_name)}"),
        f'cropro__play_remote_audio("{element_id}");',
    )


def format_local_audio(audio_files: Iterable[str]) -> str:
    return "".join(
        """
        <button class="cropro__play_button" title="{}" onclick='pycmd("cropro__play_file:{}");'></button>
        """.format(
            _(f"Play file: {name_attr_strip(file_name)}"),
            urllib.parse.quote(file_name),
        )
        for file_name in audio_files
    )


def format_tags_as_html(tags: list[str]) -> str:
    return "".join(f'<span class="cropro__note_tag">{tag}</span>' for tag in tags)


class NotePreviewer(AnkiWebView):
    """Previews a note in a Form Layout using a webview."""

    assert mw, "Anki must be initialized."

    _web_relpath = f"/_addons/{mw.addonManager.addonFromModule(__name__)}/web"
    _css_relpath = f"{_web_relpath}/previewer.css"
    _js_relpath = f"{_web_relpath}/previewer.js"

    mw.addonManager.setWebExports(__name__, r"(img|web)/.*\.(js|css|html|png|svg)")

    _note: Optional[Union[Note, RemoteNote]]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._note = None
        self.set_title("Note previewer")
        self.disable_zoom()
        self.setProperty("url", QUrl("about:blank"))
        self.setMinimumSize(200, 320)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.set_bridge_command(self._handle_play_button_press, self)

    def unload_note(self) -> None:
        self._note = None
        self.stdHtml("", js=[], css=[])
        self.hide()

    def load_note(self, note: Union[Note, RemoteNote]) -> None:
        self._note = note
        self.stdHtml(
            body=f"<main>{self._generate_html_for_note(note)}</main>",
            js=[
                self._js_relpath,
            ],
            css=[
                self._css_relpath,
            ],
        )
        self.show()

    def _is_remote_note(self) -> bool:
        return isinstance(self._note, RemoteNote)

    def _is_local_note(self) -> bool:
        return isinstance(self._note, Note)

    def _generate_html_for_note(self, note: Union[Note, RemoteNote]) -> str:
        """Creates html for the previewer showing the current note."""
        markup = io.StringIO()
        for field_name, field_content in note.items():
            if not field_content:
                continue
            markup.write(f'<div class="name">{field_name}</div>')
            markup.write('<div class="content">')
            if self._is_remote_note():
                markup.write(self._create_html_for_remote_field(field_name, field_content))
            else:
                markup.write(self._create_html_for_field(field_content))
            markup.write("</div>")
        if note.tags:
            markup.write('<div class="name">Tags</div>')
            markup.write(f'<div class="content">{format_tags_as_html(note.tags)}</div>')
        return markup.getvalue()

    def _create_html_for_remote_field(self, field_name: str, field_content: str) -> str:
        """Creates the content for the previewer showing the remote note's field."""
        assert self._is_remote_note(), "Remote note required."
        markup = io.StringIO()
        if field_name == self._note.image.field_name:
            markup.write(format_remote_image(self._note.image))
        if field_name == self._note.audio.field_name:
            markup.write(format_remote_audio(self._note.audio))
        if text := html_to_text_line(field_content):
            markup.write(f"<div>{html_to_text_line(text)}</div>")
        return markup.getvalue()

    def _create_html_for_field(self, field_content: str) -> str:
        """Creates the content for the previewer showing the local note's field."""
        assert self._is_local_note(), "Local note required."
        markup = io.StringIO()
        if audio_files := find_sounds(field_content):
            markup.write(f'<div class="cropro__audio_list">{format_local_audio(audio_files)}</div>')
        if image_files := find_images(field_content):
            markup.write(f'<div class="cropro__image_list">{format_local_images(self._note, image_files)}</div>')
        if text := html_to_text_line(field_content):
            markup.write(f'<div class="cropro__text_item">{text}</div>')
        return markup.getvalue()

    def _handle_play_button_press(self, cmd: str):
        """Play audio files if a play button was pressed. Works with local files."""
        from aqt import sound

        if cmd.startswith("cropro__play_file:"):
            assert self._is_local_note(), "Only local files can be played with av_player."
            file_name = os.path.basename(urllib.parse.unquote(cmd.split(":", maxsplit=1)[-1]))
            file_path = os.path.join(self._note.col.media.dir(), file_name)
            return sound.av_player.play_tags(
                [
                    SoundOrVideoTag(file_path),
                ]
            )
        else:
            return self.defaultOnBridgeCmd(cmd)
