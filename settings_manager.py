import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "sound_volume": 50,
    "music_enabled": True,
    "sound_enabled": True,
    "mobile_controls": False,
}


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file, indent=4)
    except IOError as error:
        print(f"Error sa pag-save: {error}")


def load_settings():
    settings = dict(DEFAULT_SETTINGS)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(settings)
        return settings

    try:
        with open(SETTINGS_FILE, "r") as file:
            data = json.load(file)

        if isinstance(data, dict):
            settings.update(data)
    except (json.JSONDecodeError, IOError):
        pass

    try:
        settings["sound_volume"] = max(
            0, min(100, int(settings["sound_volume"]))
        )
    except (TypeError, ValueError):
        settings["sound_volume"] = DEFAULT_SETTINGS["sound_volume"]

    return settings