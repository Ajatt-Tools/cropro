from aqt import mw

config = mw.addonManager.getConfig(__name__)


def write_config():
    return mw.addonManager.writeConfig(__name__, config)
