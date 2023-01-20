from os import listdir
from time import time
import cv2
import numpy as np
import keyboard as kb
from config.config import ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG, KEYBOARD_CONFIG, LANDSCAPE_NUM_CONFIG, PATH_CONFIG, get_config, MIDI_CONFIG
from tiles.landscape import Landscape
from midi.midi import Midi, MidiMessageType
from tiles.section import Section


class Tiles:

    def __init__(self, paths: list[str]) -> None:
        self.AR = tuple(get_config(ASPECT_RATIO_CONFIG))
        self.IMG_NOT_FOUND = cv2.resize(
            cv2.imread('./statics/not-found.jpg'),
            self.AR
        )
        if (len(paths) % 6 != 0):
            raise AttributeError('must pass a multiple of 6 video paths')
        landscape_num = int(len(paths) / 6)
        self.landscape_for_section: list[int] = [0 for i in range(6)]
        self.landscapes: list[Landscape] = [
            Landscape(paths[int(i*6):int(6*(i+1))]) for i in range(landscape_num)]
        self.sections: list[Section] = [
            self.landscapes[0].start_section(i) for i in range(6)]
        cv2.namedWindow('Tyler', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Tyler', self.AR[0]*3, self.AR[1]*2)

    def update_frame(self) -> None:
        imgs = []
        for i in range(len(self.sections)):
            section = self.sections[i]
            if section is None:
                imgs.append(self.IMG_NOT_FOUND)
            else:
                landscape_index = self.landscape_for_section[i]
                frame = self.landscapes[landscape_index].get_frame(i)
                if frame is None:
                    section = self.restart_section(i)
                    frame = self.landscapes[landscape_index].get_frame(i)
                imgs.append(cv2.resize(frame, self.AR))

        l0 = np.hstack(tuple(imgs[:3]))
        l1 = np.hstack(tuple(imgs[3:]))
        out = np.vstack((l0, l1))

        cv2.imshow('Tyler', out)

    def restart_section(self, section_index: int) -> Section:
        landscape_index = self.landscape_for_section[section_index]
        self.sections[section_index] = self.landscapes[landscape_index].restart_section(
            section_index)
        return self.sections[section_index]

    def switch_section(self, section_index: int, resume: bool = False) -> None:
        landscape_index = self.landscape_for_section[section_index]
        self.landscapes[landscape_index].stop_section(section_index)
        landscape_index = (landscape_index + 1) % len(self.landscapes)
        self.sections[section_index] = self.landscapes[landscape_index].start_section(
            section_index, resume)
        self.landscape_for_section[section_index] = landscape_index


def get_keyboard_input() -> tuple[int, bool]:
    key_map: list = get_config(KEYBOARD_CONFIG)
    key = cv2.waitKey(1)
    if key == -1 and not kb.is_pressed('ctrl'):
        return (None, False)
    if key == 27:
        return (-1, False)
    for i in range(len(key_map)):
        key = key_map[i]
        if (kb.is_pressed(f'ctrl + {key}')):
            return (i, True)
        if (kb.is_pressed(key)):
            return (i, False)
    return (None, False)


def setup_tiles() -> Tiles:
    num = get_config(LANDSCAPE_NUM_CONFIG)
    srcs_dir = get_config(PATH_CONFIG)

    # Load files
    files = ['' for i in range(6*num)]
    for file in listdir(srcs_dir):
        (a, b) = file.split('.', 1)[0].split('_')
        (landscape_idx, section_idx) = (int(a), int(b))
        i = landscape_idx * 6 + section_idx
        if (i >= 6*num):
            continue
        files[i] = srcs_dir + '/' + file

    return Tiles(files)


midi_input: int = None


def handle_midi_note_on(note: int, velocity: int) -> None:
    global midi_input
    if (velocity == 0):
        return
    midi_map: list = get_config(MIDI_CONFIG)
    try:
        midi_input = midi_map.index(f'{note}')
    except ValueError:
        return


def render(midi: Midi):
    global midi_input
    tiles = setup_tiles()

    # subscribe to midid events
    midi.subscribe(MidiMessageType.NOTE_ON,
                   handle_midi_note_on)

    prev = 0
    while cv2.getWindowProperty('Tyler', cv2.WND_PROP_VISIBLE) >= 1:
        fps = get_config(FRAMERATE_CONFIG)

        time_elapsed = time() - prev
        if (time_elapsed > 1.0 / fps):
            prev = time()
            tiles.update_frame()

        key, resume = get_keyboard_input()
        if key == -1:
            break
        if midi_input is not None:
            tiles.switch_section(midi_input, resume=kb.is_pressed('ctrl'))
            midi_input = None
        if key is not None:
            tiles.switch_section(key, resume)

    cv2.destroyAllWindows()
