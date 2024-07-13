# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import enum
import typing

import requests
from aqt.qt import *


class CropProExceptionProtocol(typing.Protocol):
    response: typing.Optional[requests.Response]

    def what(self) -> str: ...


@enum.unique
class CroProSearchResult(enum.Enum):
    ok = "green"
    warn = "orange"
    error = "red"


class SearchResultLabel(QLabel):
    def __init__(self, *args) -> None:
        super().__init__(*args)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

    def hide_count(self) -> None:
        self.setText("")
        self.setStyleSheet("")
        self.hide()

    def _set_status_text(self, text: str, status: CroProSearchResult):
        self.setText(text)
        self.setStyleSheet("QLabel { color: %s; }" % status.value)
        if self.isHidden():
            self.show()

    def set_error(self, ex: CropProExceptionProtocol) -> None:
        text = f"Error: {ex.what()}."
        if ex.response:
            text += f" Status code: {ex.response.status_code}"
        self._set_status_text(text, CroProSearchResult.error)

    def set_nothing_to_do(self) -> None:
        self._set_status_text("Search query is empty. Did nothing.", CroProSearchResult.warn)

    def set_count(self, found_notes: int, displayed_notes: int, current_page_n: int, total_pages_count: int) -> None:
        if found_notes == 0:
            return self._set_status_text("No notes found", CroProSearchResult.error)
        elif displayed_notes >= found_notes:
            return self._set_status_text(f"{found_notes} notes found.", CroProSearchResult.ok)
        else:
            return self._set_status_text(
                f"Displaying {displayed_notes} notes out of {found_notes} total. "
                f"Page {current_page_n}/{total_pages_count}.",
                CroProSearchResult.warn,
            )
