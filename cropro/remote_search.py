# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import dataclasses
import enum
import typing
from collections.abc import Iterable, Sequence
from typing import Optional, TypedDict

import anki.httpclient
import requests

from .config import CroProConfig

# https://apiv2.immersionkit.com/openapi.json
# Example:
# https://apiv2.immersionkit.com/search?q=草&index=&exactMatch=false&limit=0&sort=sentence_length:asc
# https://apiv2.immersionkit.com/search?q=%E3%81%8A%E5%89%8D
API_URL = "https://apiv2.immersionkit.com/search?"


class ApiReturnExampleDict(TypedDict):
    """
    This json dict is what the remote server sends back.
    """

    tags: list[str]
    image: str
    sound: str
    sentence: str
    sentence_with_furigana: str
    translation: str
    id: str
    category: str
    title: str


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
        Immersion kit returns URLs that always start with https.
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


def remote_tags_as_list(json_dict: ApiReturnExampleDict) -> list[str]:
    return [tag.replace(r"\s:", "_") for tag in [*json_dict["tags"], json_dict["title"]]]


@dataclasses.dataclass
class RemoteNote:
    """
    Packs the response from the API into a familiar interface.
    """

    sentence_kanji: str
    sentence_furigana: str
    sentence_eng: str
    image_url: str
    sound_url: str
    notes: str
    tags: list[str]
    _config: CroProConfig

    def __post_init__(self):
        self._media = {
            self._config.remote_fields.image: RemoteMediaInfo(
                self._config.remote_fields.image,
                self.image_url,
                MediaType.image,
            ),
            self._config.remote_fields.sentence_audio: RemoteMediaInfo(
                self._config.remote_fields.sentence_audio,
                self.sound_url,
                MediaType.sound,
            ),
        }
        self._mapping = {
            self._config.remote_fields.sentence_kanji: self.sentence_kanji,
            self._config.remote_fields.sentence_furigana: self.sentence_furigana,
            self._config.remote_fields.sentence_eng: self.sentence_eng,
            self._config.remote_fields.sentence_audio: self.audio.as_anki_ref(),
            self._config.remote_fields.image: self.image.as_anki_ref(),
            self._config.remote_fields.notes: self.notes,
        }

    @property
    def image(self) -> RemoteMediaInfo:
        return self._media[self._config.remote_fields.image]

    @property
    def audio(self) -> RemoteMediaInfo:
        return self._media[self._config.remote_fields.sentence_audio]

    def __contains__(self, item) -> bool:
        return item in self._mapping

    def __getitem__(self, item) -> str:
        return self._mapping[item]

    def media_info(self) -> Iterable[RemoteMediaInfo]:
        return self._media.values()

    @staticmethod
    def note_type() -> None:
        """
        Remote notes do not have a note type.
        """
        return None

    def keys(self):
        return self._mapping.keys()

    def items(self):
        """
        Return something similar to what Note.items() returns.
        """
        return self._mapping.items()

    @classmethod
    def from_json(cls, json_dict: ApiReturnExampleDict, config: CroProConfig):
        # The full url does not come from the api anymore.
        #
        # The url is:
        # https://us-southeast-1.linodeobjects.com/immersionkit/media/${category}/${deckName}/media/${fileName}
        #
        # How to:
        #
        # category - anime
        # deckName - (title from the api) girls_band_cry
        # fileName - (image/sound from the api) girls_band_cry_011_0.12.47.210.jpg
        #
        # Examples:
        # https://apiv2.immersionkit.com/download_media?path=media/anime/Whisper%20of%20the%20Heart/media/A_WhisperOfTheHeart_1_0.48.39.935.jpg
        # https://us-southeast-1.linodeobjects.com/immersionkit/media/anime/Whisper%20of%20the%20Heart/media/A_WhisperOfTheHeart_1_0.48.39.435-0.48.40.435.mp3
        # https://us-southeast-1.linodeobjects.com/immersionkit/media/anime/Lucky%20Star/media/luckystar-nodup_16_0.06.49.235.jpg

        def media_url(file_name: str) -> str:
            if file_name:
                category = json_dict["id"].split("_")[0]
                deck_name = json_dict["title"]
                return f"https://us-southeast-1.linodeobjects.com/immersionkit/media/{category}/{deck_name}/media/{file_name}"
            return ""

        return RemoteNote(
            tags=[
                json_dict["title"],
            ],
            # image_url=media_url(json_dict.get("image")),
            # sound_url=media_url(json_dict.get("sound")),
            image_url=json_dict.get("image", ""),
            sound_url=json_dict.get("sound", ""),
            sentence_kanji=json_dict["sentence"],
            sentence_furigana=json_dict["sentence_with_furigana"],
            sentence_eng=json_dict["translation"],
            notes=json_dict["id"],
            _config=config,
        )


class CroProWebSearchArgs(typing.TypedDict):
    # https://apiv2.immersionkit.com/openapi.json
    q: str
    category: str
    index: str
    locale: str
    sort: str
    exactMatch: str
    jlpt: int
    wk: int
    limit: int
    offset: int


def get_request_url(request_args: CroProWebSearchArgs) -> str:
    if "q" in request_args:
        return API_URL + "&".join(f"{key}={val}" for key, val in request_args.items())
    return ""


@dataclasses.dataclass
class CroProWebClientException(Exception):
    response: Optional[requests.Response] = None

    def what(self) -> str:
        return self.__cause__.__class__.__name__


class CroProWebSearchClient:
    _client: anki.httpclient.HttpClient
    _config: CroProConfig

    def __init__(self, config: CroProConfig) -> None:
        self._client = anki.httpclient.HttpClient()
        self._config = config

    def _get(self, url: str) -> requests.Response:
        print(f"curl -sL '{url}'")
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

    def search_notes(self, search_args: CroProWebSearchArgs) -> Sequence[RemoteNote]:
        if not search_args:
            return []
        resp = self._get(get_request_url(search_args))
        examples = [item for item in resp.json()["examples"]]
        return [RemoteNote.from_json(example, self._config) for example in examples]
