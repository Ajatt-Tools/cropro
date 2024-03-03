# Copyright: Ajatt-Tools and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import dataclasses
import enum
import itertools
from typing import TypedDict, Iterable, Optional

import anki.httpclient
import requests

IMAGE_FIELD_NAME = "Image"
AUDIO_FIELD_NAME = "SentAudio"
API_URL = "https://api.immersionkit.com/look_up_dictionary?"


class ApiReturnExampleDict(TypedDict):
    """
    This json dict is what the remote server sends back.
    """

    tags: list[str]
    image_url: str
    sound_url: str
    sentence: str
    sentence_with_furigana: str
    translation: str
    sentence_id: str


@enum.unique
class MediaType(enum.Enum):
    image = enum.auto()
    sound = enum.auto()


@dataclasses.dataclass
class RemoteMediaInfo:
    field_name: str
    url: str
    type: MediaType

    def __post_init__(self):
        self.file_name = self.url.split("/")[-1] if self.is_valid_url() else ""

    def is_valid_url(self) -> bool:
        """
        immersionkit return URLs that always start with https.
        """
        return bool(self.url and self.url.startswith("https://"))

    def as_anki_ref(self):
        if not self.is_valid_url():
            return ""
        if self.type == MediaType.image:
            return f'<img src="{self.file_name}">'
        if self.type == MediaType.sound:
            return f"[sound:{self.file_name}]"
        raise NotImplementedError(f"not implemented: {self.type}")


@dataclasses.dataclass
class RemoteNote:
    """
    Packs the response from the API into a familiar interface.
    """

    sent_kanji: str
    sent_furigana: str
    sent_eng: str
    image_url: str
    sound_url: str
    notes: str
    tags: list[str]

    def __post_init__(self):
        self._media = {
            IMAGE_FIELD_NAME: RemoteMediaInfo(IMAGE_FIELD_NAME, self.image_url, MediaType.image),
            AUDIO_FIELD_NAME: RemoteMediaInfo(AUDIO_FIELD_NAME, self.sound_url, MediaType.sound),
        }
        self._mapping = {
            "SentKanji": self.sent_kanji,
            "SentFurigana": self.sent_furigana,
            "SentEng": self.sent_eng,
            AUDIO_FIELD_NAME: self.audio.as_anki_ref(),
            IMAGE_FIELD_NAME: self.image.as_anki_ref(),
            "Notes": self.notes,
        }

    @property
    def image(self) -> RemoteMediaInfo:
        return self._media[IMAGE_FIELD_NAME]

    @property
    def audio(self) -> RemoteMediaInfo:
        return self._media[AUDIO_FIELD_NAME]

    def __contains__(self, item) -> bool:
        return item in self._mapping

    def __getitem__(self, item) -> str:
        return self._mapping[item]

    def media_info(self) -> Iterable[RemoteMediaInfo]:
        return self._media.values()

    @staticmethod
    def note_type() -> None:
        return None

    def keys(self):
        return self._mapping.keys()

    def items(self):
        """
        Return something similar to what Note.items() returns.
        """
        return self._mapping.items()

    @classmethod
    def from_json(cls, json_dict: ApiReturnExampleDict):
        return RemoteNote(
            tags=json_dict["tags"],
            image_url=json_dict["image_url"],
            sound_url=json_dict["sound_url"],
            sent_kanji=json_dict["sentence"],
            sent_furigana=json_dict["sentence_with_furigana"],
            sent_eng=json_dict["translation"],
            notes=json_dict["sentence_id"],
        )


def get_request_url(request_args: dict[str, str]) -> str:
    if "keyword" in request_args:
        return API_URL + "&".join(f"{key}={val}" for key, val in request_args.items())
    return ""


@dataclasses.dataclass
class CroProWebClientException(Exception):
    response: Optional[requests.Response] = None

    def what(self) -> str:
        return self.__cause__.__class__.__name__


class CroProWebSearchClient:
    def __init__(self) -> None:
        self._client = anki.httpclient.HttpClient()

    def _get(self, url: str) -> requests.Response:
        try:
            resp = self._client.get(url)
        except OSError as ex:
            raise CroProWebClientException() from ex
        try:
            resp.raise_for_status()
        except requests.HTTPError as ex:
            raise CroProWebClientException(ex.response) from ex
        return resp

    def set_timeout(self, timeout_seconds: int):
        self._client.timeout = timeout_seconds

    def download_media(self, url: str) -> bytes:
        return self._client.stream_content(self._get(url))

    def search_notes(self, search_args: dict[str, str]) -> list[RemoteNote]:
        if not search_args:
            return []
        resp = self._get(get_request_url(search_args))
        examples = list(itertools.chain(*(item["examples"] for item in resp.json()["data"])))
        return [RemoteNote.from_json(example) for example in examples]


def main():
    client = CroProWebSearchClient()
    result = client.search_notes({"keyword": "人事"})
    for note in result:
        print(note)


if __name__ == "__main__":
    main()
