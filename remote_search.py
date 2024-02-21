import dataclasses
import itertools
import os.path

import anki.httpclient


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

    def mapping(self):
        return {
            "SentKanji": self.sent_kanji,
            "SentFurigana": self.sent_furigana,
            "SentEng": self.sent_eng,
            "SentAudio": f'[sound:{os.path.basename(self.sound_url)}]',
            "Image": f'<img src="{os.path.basename(self.image_url)}">',
            "Notes": self.notes,
        }

    @classmethod
    def from_json(cls, json_dict: dict[str]):
        return RemoteNote(
            tags=json_dict["tags"],
            image_url=json_dict["image_url"],
            sound_url=json_dict["sound_url"],
            sent_kanji=json_dict["sentence"],
            sent_furigana=json_dict["sentence_with_furigana"],
            sent_eng=json_dict["translation"],
            notes=json_dict["sentence_id"],
        )


class CroProWebSearchClient:
    def __init__(self) -> None:
        self._client = anki.httpclient.HttpClient()
        self._client.timeout = 30

    def search(self, get_url: str):
        resp = self._client.get(get_url)
        resp.raise_for_status()
        examples = list(itertools.chain(*(item["examples"] for item in resp.json()["data"])))
        return [
            RemoteNote.from_json(example)
            for example in examples
        ]


def main():
    client = CroProWebSearchClient()
    result = client.search("https://api.immersionkit.com/look_up_dictionary?keyword=人事")
    for note in result:
        print(note)


if __name__ == "__main__":
    main()