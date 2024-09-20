# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from cropro.remote_search import CroProWebSearchClient
from run.mock_config import NoAnkiConfig


def main():
    client = CroProWebSearchClient(NoAnkiConfig())
    result = client.search_notes({"keyword": "人事"})
    for note in result:
        print(note)


if __name__ == "__main__":
    main()
