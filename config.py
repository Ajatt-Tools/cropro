# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import mw


def get_config():
    return mw.addonManager.getConfig(__name__)


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


def is_hidden(field_name: str) -> bool:
    field_name = field_name.lower()
    return any(hidden_field.lower() in field_name for hidden_field in config['hidden_fields'])


config = get_config()
