import json
import os

DIR_PATH = '/.tyler'
FILE_NAME = DIR_PATH + '/config.json'

# keys
LANDSCAPE_NUM_CONFIG = 'landscape_num'
PATH_CONFIG = 'sources'
ASPECT_RATIO_CONFIG = 'aspect_ratio'
FRAMERATE_CONFIG = 'framerate'
MIDI_PORT_CONFIG = 'midi_port'
MIDI_CONFIG = 'midi_map'
KEYBOARD_CONFIG = 'key_map'
KNOB_CONFIG = 'knob'

DEFAULT_CONFIG = {
    "landscape_num": 6,
    "sources": "",
    "aspect_ratio": (1080, 1080),
    "framerate": 23.976,
    "midi_port": 0,
    "midi_map": ["48", "49", "50", "44", "45", "46"],
    "key_map": ["4", "5", "6", "1", "2", "3"],
    "knob": 2
}


def setup_config():
    if not os.path.exists(DIR_PATH):
        os.mkdir(DIR_PATH)
    if not os.path.exists(FILE_NAME):
        _write_config_file(DEFAULT_CONFIG)


def _read_config_file() -> dict | None:
    config = None
    with open(FILE_NAME) as config_file:
        config = json.load(config_file)
    return config


def _write_config_file(config: dict):
    with open(FILE_NAME, 'w') as config_file:
        json.dump(config, config_file)


def get_config(key: str) -> object | None:
    config = _read_config_file()
    value = None
    if (config is not None):
        value = config.get(key)
    return value


def set_config(key: str, value: object) -> bool:
    config: dict = _read_config_file()
    if (config is None):
        return False
    config[key] = value
    _write_config_file(config)
    return True
