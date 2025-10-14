# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from pprint import pprint

from cropro.remote_search import CroProWebSearchClient
from run.mock_config import NoAnkiConfig


def main():
    client = CroProWebSearchClient(NoAnkiConfig())
    result = client.search_notes({"q": "人事"})
    for note in result:
        pprint(note)


if __name__ == "__main__":
    main()
