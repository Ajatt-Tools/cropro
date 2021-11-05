from aqt import mw


def get_config():
    return mw.addonManager.getConfig(__name__)


def write_config():
    return mw.addonManager.writeConfig(__name__, config)


config = get_config()
