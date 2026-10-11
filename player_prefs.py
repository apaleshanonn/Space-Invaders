import json

PREFS_FILE = "player_prefs.json"
DEFAULTS = {"ship": 0, "avatar": 0}
MAX_INDEX = 3


def _read():
    try:
        with open(PREFS_FILE, "r") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}
    except (IOError, ValueError):
        return {}


def _write(data):
    try:
        with open(PREFS_FILE, "w") as file:
            json.dump(data, file, indent=4)
    except IOError as error:
        print(f"Error sa pag-save sa prefs: {error}")


def get_prefs(player_id):
    prefs = dict(DEFAULTS)

    if player_id is None:
        return prefs

    saved = _read().get(str(player_id))

    if isinstance(saved, dict):
        for key in DEFAULTS:
            value = saved.get(key)

            if isinstance(value, int) and 0 <= value <= MAX_INDEX:
                prefs[key] = value

    return prefs


def set_prefs(player_id, **values):
    if player_id is None:
        return

    data = _read()
    current = get_prefs(player_id)

    for key, value in values.items():
        if key in DEFAULTS:
            current[key] = max(0, min(MAX_INDEX, int(value)))

    data[str(player_id)] = current
    _write(data)


def delete_prefs(player_id):
    data = _read()

    if data.pop(str(player_id), None) is not None:
        _write(data)