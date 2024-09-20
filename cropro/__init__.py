# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


import sys

from aqt import mw


def start_addon():
    from . import cropro, settings_dialog

    cropro.init()


if mw and "pytest" not in sys.modules:
    start_addon()
