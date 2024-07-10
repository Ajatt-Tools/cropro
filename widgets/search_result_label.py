# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import typing

import requests
from aqt.qt import *


class CropProExceptionProtocol(typing.Protocol):
    response: typing.Optional[requests.Response]

    def what(self) -> str: ...


class SearchResultLabel(QLabel):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

    def hide_count(self) -> None:
        self.setText("")
        self.setStyleSheet("")
        self.hide()

    def set_error(self, ex: CropProExceptionProtocol) -> None:
        text = f"Error: {ex.what()}."
        if ex.response:
            text += f" Status code: {ex.response.status_code}"
        self.setText(text)
        self.setStyleSheet("QLabel { color: red; }")
        if self.isHidden():
            self.show()

    def set_count(self, found_notes: int, displayed_notes: int, current_page_n: int, total_pages_count: int) -> None:
        if found_notes == 0:
            self.setText("No notes found")
            self.setStyleSheet("QLabel { color: red; }")
        elif displayed_notes >= found_notes:
            self.setText(f"{found_notes} notes found")
            self.setStyleSheet("QLabel { color: green; }")
        else:
            self.setText(
                f"Displaying {displayed_notes} notes out of {found_notes} total. "
                f"Page {current_page_n}/{total_pages_count}."
            )
            self.setStyleSheet("QLabel { color: orange; }")
        if self.isHidden():
            self.show()
