import json
import os
from threading import Thread, Lock
from time import sleep

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

DEFAULT_CONFIG = {
    "landscape_num": 6,
    "sources": "",
    "aspect_ratio": (1080, 1080),
    "framerate": 23.976,
    "midi_port": 0,
    "midi_map": ["48", "49", "50", "44", "45", "46"],
    "key_map": ["4", "5", "6", "1", "2", "3"],
}

cache: dict = dict()
lock: Lock = Lock()
save_thread: Thread = None
dirty: bool = False
kill_save_thread: bool = False


def setup_config():
    global cache, save_thread
    if not os.path.exists(DIR_PATH):
        os.mkdir(DIR_PATH)
    if not os.path.exists(FILE_NAME):
        _write_config_file(DEFAULT_CONFIG)
    cache = _read_config_file()
    save_thread = Thread(group=None, target=save)
    save_thread.start()


def teardown_config():
    global save_thread, kill_save_thread
    kill_save_thread = True
    save_thread.join()


def _read_config_file() -> dict | None:
    config = None
    lock.acquire()
    with open(FILE_NAME) as config_file:
        config = json.load(config_file)
    lock.release()
    return config


def _write_config_file(config: dict):
    lock.acquire()
    with open(FILE_NAME, 'w') as config_file:
        json.dump(config, config_file)
    lock.release()


def save():
    global cache, save_thread, dirty, kill_save_thread
    while (not kill_save_thread):
        if (dirty):
            _write_config_file(cache)
            dirty = False
        sleep(5)


def get_config(key: str) -> object | None:
    value = None
    if (cache is not None):
        value = cache.get(key)
    return value


def set_config(key: str, value: object) -> bool:
    global cache, dirty
    if (cache is None):
        return False
    cache[key] = value
    dirty = True
    return True
