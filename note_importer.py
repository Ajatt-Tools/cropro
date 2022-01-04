# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os.path
from copy import deepcopy
from enum import Enum, auto
from typing import NamedTuple, Iterable

from anki.models import NoteType
from anki.notes import Note
from anki.utils import joinFields
from aqt import mw
from aqt.qt import *

from .collection_manager import NameId
from .config import config


class ImportResult(Enum):
    success = auto()
    dupe = auto()


class FileInfo(NamedTuple):
    name: str
    path: str


def files_in_note(note: Note) -> Iterable[FileInfo]:
    """
    Returns FileInfo for every file referenced by the note.
    Skips missing files.
    """
    for file_ref in note.col.media.filesInStr(note.mid, joinFields(note.fields)):
        if os.path.exists(file_path := os.path.join(note.col.media.dir(), file_ref)):
            yield FileInfo(file_ref, file_path)


def copy_media_files(new_note: Note, other_note: Note) -> None:
    # check if there are any media files referenced by the note
    for file in files_in_note(other_note):
        new_filename = new_note.col.media.addFile(file.path)
        # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
        # in which case we need to update the note.
        if new_filename != file.name:
            new_note.fields = [field.replace(file.name, new_filename) for field in new_note.fields]


def get_matching_model(model_id: int, reference_model: NoteType) -> NoteType:
    if model_id != NameId.none_type().id:
        return mw.col.models.get(model_id)
    else:
        # find a model in current profile that matches the name of model from other profile
        matching_model = mw.col.models.by_name(reference_model.get('name'))

        if not matching_model or matching_model.keys() != reference_model.keys():
            matching_model = deepcopy(reference_model)
            matching_model['id'] = 0
            mw.col.models.add(matching_model)
        return matching_model


def import_note(other_note: Note, model_id: int, deck_id: int) -> ImportResult:
    matching_model = get_matching_model(model_id, other_note.note_type())
    new_note = Note(mw.col, matching_model)
    new_note.note_type()['did'] = deck_id

    for key in new_note.keys():
        try:
            new_note[key] = str(other_note[key])
        except KeyError:
            pass

    # copy field tags into new note object
    if config.get('copy_tags'):
        new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

    if config.get('tag_exported_cards') and (tag := config.get('exported_tag')):
        other_note.add_tag(tag)
        other_note.flush()

    # check if note is dupe of existing one
    if config.get('skip_duplicates') and new_note.dupeOrEmpty():
        return ImportResult.dupe
    else:
        copy_media_files(new_note, other_note)
        mw.col.addNote(new_note)
        return ImportResult.success
