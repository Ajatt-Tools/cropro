# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import concurrent.futures
import dataclasses
import enum
import math
import os.path
from collections.abc import Iterable
from copy import deepcopy
from typing import NamedTuple, Optional
from collections.abc import MutableSequence

from anki.cards import Card
from anki.collection import Collection, AddNoteRequest, OpChanges
from anki.decks import DeckId
from anki.models import NoteType
from anki.notes import Note
from anki.utils import join_fields
from aqt import mw
from aqt.qt import *

from .collection_manager import NameId, NO_MODEL, CollectionManager
from .common import ADDON_NAME_SHORT
from .config import config
from .remote_search import RemoteNote, CroProWebSearchClient, CroProWebClientException

MAX_WORKERS = 5
CroProAnyNote = Union[Note, RemoteNote]
CroProNoteList = MutableSequence[CroProAnyNote]


@enum.unique
class NoteCreateStatus(enum.Enum):
    success = enum.auto()
    dupe = enum.auto()
    connection_error = enum.auto()


@dataclasses.dataclass
class NoteCreateResult:
    note: CroProAnyNote
    status: NoteCreateStatus


class ImportResultCounter(dict[NoteCreateStatus, CroProNoteList]):
    def __init__(self):
        super().__init__()
        for name in NoteCreateStatus:
            self[name] = []

    @property
    def successes(self) -> CroProNoteList:
        return self[NoteCreateStatus.success]

    @property
    def duplicates(self) -> CroProNoteList:
        return self[NoteCreateStatus.dupe]

    @property
    def errors(self) -> CroProNoteList:
        return self[NoteCreateStatus.connection_error]


class FileInfo(NamedTuple):
    name: str
    path: str


def files_in_note(note: Note) -> Iterable[FileInfo]:
    """
    Returns FileInfo for every file referenced by other_note.
    Skips missing files.
    """
    for file_ref in note.col.media.files_in_str(note.mid, join_fields(note.fields)):
        if os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, str(file_path))


def copy_media_files(new_note: Note, other_note: Note) -> None:
    assert new_note.id == 0, "This function expects a note that hasn't been added yet."
    # check if there are any media files referenced by other_note
    for file in files_in_note(other_note):
        new_filename = new_note.col.media.add_file(file.path)
        # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
        # in which case we need to update the note.
        if new_filename != file.name:
            new_note.fields = [field.replace(file.name, new_filename) for field in new_note.fields]


def remove_media_files(new_note: Note) -> None:
    """
    If the user pressed the Edit button, but then canceled the import operation,
    the collection will contain unused files that need to be trashed.
    But if the same file(s) are referenced by another note, they shouldn't be trashed.
    """
    assert new_note.col == mw.col.weakref()
    new_note.col.media.trash_files(
        [file.name for file in files_in_note(new_note) if not new_note.col.find_cards(file.name)]
    )


class NoteTypeUnavailable(RuntimeError):
    pass


def get_matching_model(target_model: NameId, reference_model: Optional[NoteType]) -> NoteType:
    if target_model != NO_MODEL:
        # use existing note type (even if its name or fields are different)
        return mw.col.models.get(target_model.id)

    if reference_model:
        # find a model in current profile that matches the name of model from other profile
        # create a new note type (clone) if needed.
        matching_model = mw.col.models.by_name(reference_model.get("name"))

        if not matching_model or matching_model.keys() != reference_model.keys():
            matching_model = deepcopy(reference_model)
            matching_model["id"] = 0
            mw.col.models.add(matching_model)
        return matching_model

    raise NoteTypeUnavailable()


def col_diff(col: Collection, other_col: Collection) -> int:
    """
    Because of difference in collection creation times,
    due numbers which are relative to the collection's creation time need to be adjusted by it.
    """
    return math.ceil((other_col.crt - col.crt) / (60 * 60 * 24))


def import_card_info(new_note: Note, other_note: Note, other_col: Collection):
    """
    For all cards in the new note,
    copy some scheduling info from the old card to the newly imported one.
    """
    assert new_note.id == 0, "This function expects a note that hasn't been added yet."

    for new_card, other_card in zip(new_note.cards(), other_note.cards()):
        # If the note types are similar, this loop will iterate over identical cards.
        # Otherwise, some cards might be skipped (lost scheduling info).

        # https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
        new_card: Card
        new_card.mod = other_card.mod
        new_card.type = other_card.type
        new_card.queue = other_card.queue
        new_card.due = other_card.due
        new_card.odue = other_card.odue
        new_card.ivl = other_card.ivl
        new_card.factor = other_card.factor
        new_card.reps = other_card.reps
        new_card.left = other_card.left

        if new_card.type == 2:
            new_card.due += col_diff(mw.col, other_col)


def download_media(new_note: Note, other_note: RemoteNote, web_client: CroProWebSearchClient):
    assert new_note.id == 0, "This function expects a note that hasn't been added yet."
    for file in other_note.media_info():
        if file.is_valid_url() and file.field_name in new_note:
            file.file_name = mw.col.media.write_data(
                desired_fname=file.file_name,
                data=web_client.download_media(file.url),
            )
            new_note[file.field_name] = file.as_anki_ref()


class NoteImporter:
    def __init__(self, col_mgr: CollectionManager, web_client: CroProWebSearchClient):
        self._other_col = col_mgr
        self._web_client = web_client
        self._counter = ImportResultCounter()

    def move_results(self) -> ImportResultCounter:
        ret, self._counter = self._counter, ImportResultCounter()
        return ret

    def import_notes(
        self,
        col: Collection,
        notes: CroProNoteList,
        model: NameId,
        deck: NameId,
    ) -> OpChanges:
        self._web_client.set_timeout(config.timeout_seconds)  # update timeout if the user has changed it.

        if config.search_the_web and model == NO_MODEL:
            raise NoteTypeUnavailable()

        pos = col.add_custom_undo_entry(f"{ADDON_NAME_SHORT}: import {len(notes)} notes")
        requests: list[AddNoteRequest] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(
                    self._construct_new_note,
                    col=col,
                    other_note=note,
                    model=model,
                    deck=deck,
                )
                for note in notes
            ]

            for future in concurrent.futures.as_completed(futures):
                result: NoteCreateResult = future.result()
                if result.status == NoteCreateStatus.success:
                    requests.append(AddNoteRequest(note=result.note, deck_id=DeckId(deck.id)))
                self._counter[result.status].append(result.note)

        col.add_notes(requests)  # new notes have changed their ids

        return col.merge_undo_entries(pos)

    def _construct_new_note(
        self,
        col: Collection,
        other_note: CroProAnyNote,
        model: NameId,
        deck: NameId,
    ) -> NoteCreateResult:
        matching_model = get_matching_model(model, other_note.note_type())
        new_note = Note(col, matching_model)
        new_note.note_type()["did"] = deck.id

        # populate the new note's fields by copying them from the other note.
        for key in new_note.keys():
            if key in other_note:
                new_note[key] = other_note[key].strip()

        # copy field tags into new other_note object
        if config.copy_tags:
            new_note.tags = [tag for tag in other_note.tags if tag != "leech"]

        # check if note is dupe of existing one
        if config.skip_duplicates and new_note.dupeOrEmpty():
            return NoteCreateResult(new_note, NoteCreateStatus.dupe)

        if isinstance(other_note, RemoteNote):
            try:
                download_media(new_note, other_note, self._web_client)
            except CroProWebClientException:
                return NoteCreateResult(new_note, NoteCreateStatus.connection_error)
        else:
            copy_media_files(new_note, other_note)
            if tag := config.tag_original_notes:
                other_note.add_tag(tag)
                other_note.flush()
            if config.copy_card_data:
                import_card_info(new_note, other_note, col_diff(col, self._other_col.col))

        return NoteCreateResult(new_note, NoteCreateStatus.success)
