# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import json
import pathlib
import re

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
CONFIG_JSON_PATH = ROOT_DIR / "cropro" / "config.json"
CONFIG_MD_PATH = ROOT_DIR / "cropro" / "config.md"
CONFIG_KEY_RE = re.compile(r"<li><code>([^<]+)</code>")


def flattened_config_keys(config: dict[str, object]) -> set[str]:
    """Return all top-level config keys and nested remote field keys."""
    keys = set(config)
    remote_fields = config.get("remote_fields")
    if isinstance(remote_fields, dict):
        keys.update(remote_fields)
    return keys


def documented_config_keys(help_text: str) -> set[str]:
    """Return config keys documented as list entries in config.md."""
    return set(CONFIG_KEY_RE.findall(help_text))


class TestConfigDocs:
    def test_config_md_documents_all_config_json_keys(self) -> None:
        with open(CONFIG_JSON_PATH, encoding="utf-8") as config_file:
            expected_keys = flattened_config_keys(json.load(config_file))

        with open(CONFIG_MD_PATH, encoding="utf-8") as help_file:
            actual_keys = documented_config_keys(help_file.read())

        assert actual_keys == expected_keys
