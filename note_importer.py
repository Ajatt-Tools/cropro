# -*- coding: utf-8 -*-

# Cross-Profile Search and Import add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.

import os.path
from copy import deepcopy
from enum import Enum, auto
from typing import Generator, Tuple

from anki.models import NoteType, NotetypeNameId
from anki.notes import Note
from anki.utils import joinFields
from aqt import mw
from aqt.qt import *

from .config import config


def invalid_note_type() -> NotetypeNameId:
    return NotetypeNameId(name='None', id=0)


class ImportResult(Enum):
    success = auto()
    dupe = auto()


def files_in_note(note: Note) -> Generator[Tuple[str, str], None, None]:
    for file_ref in note.col.media.filesInStr(note.mid, joinFields(note.fields)):
        yield file_ref, os.path.join(note.col.media.dir(), file_ref)


def copy_media_files(new_note: Note, other_note: Note) -> None:
    # check if there are any media files referenced by the note
    for filename, filepath in files_in_note(other_note):
        # referenced media might not exist, in which case we skip it
        if not os.path.exists(filepath):
            continue

        new_filename = new_note.col.media.addFile(filepath)
        # NOTE: this_col_filename may differ from original filename (name conflict, different contents),
        # in which case we need to update the note.
        if new_filename != filename:
            new_note.fields = [field.replace(filename, new_filename) for field in new_note.fields]


def get_matching_model(model_id: int, reference_model: NoteType) -> NoteType:
    if model_id != invalid_note_type().id:
        return mw.col.models.get(model_id)
    else:
        # find a model in current profile that matches the name of model from other profile
        matching_model: NoteType = mw.col.models.by_name(reference_model.get('name'))

        if not matching_model or matching_model.keys() != reference_model.keys():
            matching_model = deepcopy(reference_model)
            matching_model['id'] = 0
            mw.col.models.add(matching_model)
        return matching_model


def import_note(other_note: Note, model_id: int, deck_id: int, tag_exported: bool = True) -> ImportResult:
    matching_model: NoteType = get_matching_model(model_id, other_note.model())
    new_note = Note(mw.col, matching_model)
    new_note.model()['did'] = deck_id

    for key in new_note.keys():
        try:
            new_note[key] = str(other_note[key])
        except KeyError:
            pass

    # copy field tags into new note object
    if config.get('copy_tags'):
        new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

    if tag_exported:
        other_note.addTag(config.get('exported_tag', 'exported'))
        other_note.flush()

    # check if note is dupe of existing one
    if config.get('skip_duplicates') and new_note.dupeOrEmpty():
        return ImportResult.dupe
    else:
        copy_media_files(new_note, other_note)
        mw.col.addNote(new_note)
        return ImportResult.success
