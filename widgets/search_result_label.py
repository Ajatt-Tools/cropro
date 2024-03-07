# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import typing
from collections.abc import Sized

import requests
from aqt.qt import *


class CropProExceptionProtocol(typing.Protocol):
    response: typing.Optional[requests.Response]

    def what(self) -> str:
        ...


class SearchResultLabel(QLabel):
    def __init__(self, *args):
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

    def hide_count(self):
        self.setText("")
        self.setStyleSheet("")
        self.hide()

    def set_error(self, ex: CropProExceptionProtocol):
        text = f"Error: {ex.what()}."
        if ex.response:
            text += f" Status code: {ex.response.status_code}"
        self.setText(text)
        self.setStyleSheet("QLabel { color: red; }")
        if self.isHidden():
            self.show()

    def set_search_result(self, note_ids: Sized, display_limit: int):
        found = len(note_ids)
        displayed = min(found, display_limit)
        return self.set_count(found, displayed)

    def set_count(self, found: int, displayed: int):
        if found == 0:
            self.setText(f"No notes found")
            self.setStyleSheet("QLabel { color: red; }")
        elif displayed >= found:
            self.setText(f"{found} notes found")
            self.setStyleSheet("QLabel { color: green; }")
        else:
            self.setText(f"{found} notes found (displaying first {displayed})")
            self.setStyleSheet("QLabel { color: orange; }")
        if self.isHidden():
            self.show()
