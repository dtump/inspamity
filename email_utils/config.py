import configparser
from pathlib import Path

SYSTEM_CONFIG_PATH = Path("/etc/inspamity/config.ini")
LOCAL_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.ini"


def load_config() -> configparser.ConfigParser:
    """Load configuration from system or local config file.

    Checks /etc/inspamity/config.ini first, then falls back to
    config.ini in the project root.
    """
    config = configparser.ConfigParser()

    if SYSTEM_CONFIG_PATH.exists():
        config.read(SYSTEM_CONFIG_PATH)
    elif LOCAL_CONFIG_PATH.exists():
        config.read(LOCAL_CONFIG_PATH)
    else:
        raise FileNotFoundError(
            f"Config file not found at {SYSTEM_CONFIG_PATH} or {LOCAL_CONFIG_PATH}"
        )

    return config
