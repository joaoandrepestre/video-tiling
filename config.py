from asyncore import read
import json
from turtle import circle

FILE_NAME = 'config.json'
PATH_CONFIG = 'sources'
MIDI_CONFIG = 'midi_map'
KEYBOARD_CONFIG = 'key_map'


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
