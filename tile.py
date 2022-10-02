from os import listdir
import cv2
import numpy as np
from vidgear.gears import CamGear
from ffpyplayer.player import MediaPlayer
from config import PATH_CONFIG, get_config
from landscape import Landscape
from midi import Midi
from settigns import ENV


class Tiles:

    AR = ENV['ASPECT_RATIO']
    IMG_NOT_FOUND = cv2.resize(
        cv2.imread('./statics/not-found.jpg'),
        AR
    )

    def __init__(self, paths: list[str]) -> None:
        if (len(paths) % 6 != 0):
            raise AttributeError('must pass a multiple of 6 video paths')
        landscape_num = int(len(paths) / 6)
        self.landscape_for_section: list[int] = [0 for i in range(6)]
        self.landscapes: list[Landscape] = [
            Landscape(paths[int(i*6):int(6*(i+1))]) for i in range(landscape_num)]
        self.videos: list[CamGear] = [
            self.landscapes[0].start_section(i) for i in range(6)]

    def update_frame(self) -> None:
        imgs = []
        for i in range(len(self.videos)):
            video = self.videos[i]
            if video is None:
                imgs.append(Tiles.IMG_NOT_FOUND)
            else:
                frame = video.read()
                if frame is None:
                    video = self.restart_section(i)
                    frame = video.read()
                imgs.append(cv2.resize(frame, Tiles.AR))

        l0 = np.hstack(tuple(imgs[:3]))
        l1 = np.hstack(tuple(imgs[3:]))
        out = np.vstack((l0, l1))

        cv2.imshow('Tiles', out)

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


def render():
    num = ENV['LANDSCAPE_NUM']
    srcs_dir = get_config(PATH_CONFIG)

    files = ['' for i in range(6*num)]
    for file in listdir(srcs_dir):
        (a, b) = file.split('.', 1)[0].split('_')
        (landscape_idx, section_idx) = (int(a), int(b))
        i = landscape_idx * 6 + section_idx
        files[i] = srcs_dir + '/' + file

    tiles = Tiles(files)
    midi = Midi()
    while True:
        tiles.update_frame()
        key = cv2.waitKey(1) & 0xFF
        section = midi.get_midi_input()
        if key == ord('q') or key == ord('Q'):
            break
        if section is not None:
            tiles.switch_section(section)

    cv2.destroyAllWindows()
    midi.destroy()
