# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os.path
from copy import deepcopy
from enum import Enum, auto
from typing import NamedTuple, Iterable

from anki.cards import Card
from anki.models import NoteType
from anki.notes import Note
from anki.utils import join_fields
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
    for file_ref in note.col.media.files_in_str(note.mid, join_fields(note.fields)):
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
        # use existing note type (even if its name or fields are different)
        return mw.col.models.get(model_id)
    else:
        # find a model in current profile that matches the name of model from other profile
        # create a new note type (clone) if needed.
        matching_model = mw.col.models.by_name(reference_model.get('name'))

        if not matching_model or matching_model.keys() != reference_model.keys():
            matching_model = deepcopy(reference_model)
            matching_model['id'] = 0
            mw.col.models.add(matching_model)
        return matching_model


def import_card_info(new_note: Note, other_note: Note):
    """
    For all cards in the new note,
    copy some scheduling info from the old card to the newly imported one.
    """
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
        new_card.flush()


def import_note(other_note: Note, model_id: int, deck_id: int) -> ImportResult:
    matching_model = get_matching_model(model_id, other_note.note_type())
    new_note = Note(mw.col, matching_model)
    new_note.note_type()['did'] = deck_id

    for key in new_note.keys():
        if key in other_note:
            new_note[key] = str(other_note[key])

    # copy field tags into new note object
    if config.get('copy_tags'):
        new_note.tags = [tag for tag in other_note.tags if tag != 'leech']

    if config.get('tag_exported_cards') and (tag := config.get('exported_tag')):
        other_note.add_tag(tag)
        other_note.flush()

    # check if note is dupe of existing one
    if config.get('skip_duplicates') and new_note.dupeOrEmpty():
        return ImportResult.dupe

    copy_media_files(new_note, other_note)
    mw.col.addNote(new_note)  # new_note has changed its id
    if config['copy_card_data']:
        import_card_info(new_note, other_note)
    return ImportResult.success
