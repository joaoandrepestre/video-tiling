from os import listdir
from time import time
import cv2
import numpy as np
from vidgear.gears import CamGear
from ffpyplayer.player import MediaPlayer
from config import ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG, KEYBOARD_CONFIG, LANDSCAPE_NUM_CONFIG, PATH_CONFIG, get_config
from landscape import Landscape
from midi import Midi


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
        self.videos: list[CamGear] = [
            self.landscapes[0].start_section(i) for i in range(6)]
        cv2.namedWindow('Tyler', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Tyler', self.AR[0]*3, self.AR[1]*2)

    def update_frame(self) -> None:
        imgs = []
        for i in range(len(self.videos)):
            video = self.videos[i]
            if video is None:
                imgs.append(self.IMG_NOT_FOUND)
            else:
                frame = video.read()
                if frame is None:
                    video = self.restart_section(i)
                    frame = video.read()
                imgs.append(cv2.resize(frame, self.AR))

        l0 = np.hstack(tuple(imgs[:3]))
        l1 = np.hstack(tuple(imgs[3:]))
        out = np.vstack((l0, l1))

        cv2.imshow('Tyler', out)

    def restart_section(self, section_index: int) -> None:
        landscape_index = self.landscape_for_section[section_index]
        self.landscapes[landscape_index].stop_section(section_index)
        self.videos[section_index] = self.landscapes[landscape_index].start_section(
            section_index)
        return self.videos[section_index]

    def switch_section(self, section_index: int) -> None:
        landscape_index = self.landscape_for_section[section_index]
        self.landscapes[landscape_index].stop_section(section_index)
        landscape_index = (landscape_index + 1) % len(self.landscapes)
        self.videos[section_index] = self.landscapes[landscape_index].start_section(
            section_index)
        self.landscape_for_section[section_index] = landscape_index

    def is_audio_playing(self) -> bool:
        vals = [l.is_audio_playing() for l in self.landscapes]
        playing = list(filter(lambda x: x == True, vals))
        return len(playing) > 0


def get_keyboard_input():
    key = cv2.waitKey(1)
    if key == -1:
        return None
    if key == 27:
        return -1
    key_map: list = get_config(KEYBOARD_CONFIG)
    try:
        return key_map.index(chr(key).upper())
    except ValueError:
        return None


def render(midi: Midi):
    num = get_config(LANDSCAPE_NUM_CONFIG)
    srcs_dir = get_config(PATH_CONFIG)
    fps = get_config(FRAMERATE_CONFIG)

    files = ['' for i in range(6*num)]
    for file in listdir(srcs_dir):
        (a, b) = file.split('.', 1)[0].split('_')
        (landscape_idx, section_idx) = (int(a), int(b))
        i = landscape_idx * 6 + section_idx
        if (i >= 6*num):
            continue
        files[i] = srcs_dir + '/' + file

    tiles = Tiles(files)
    prev = 0
    while cv2.getWindowProperty('Tyler', cv2.WND_PROP_VISIBLE) >= 1:

        time_elapsed = time() - prev
        if (time_elapsed > 1.0 / fps):
            prev = time()
            if (tiles.is_audio_playing()):
                tiles.update_frame()

        key = get_keyboard_input()
        if key == -1:
            break
        note = midi.get_midi_input()
        if note is not None:
            tiles.switch_section(note)
        elif key is not None:
            tiles.switch_section(key)

    cv2.destroyAllWindows()
