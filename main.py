from os import listdir
import cv2
from midi import Midi
from settigns import ENV
from tile import Tiles


def main():
    num = ENV['LANDSCAPE_NUM']
    srcs_dir = ENV['SOURCES']

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
        if key == ord('q'):
            break
        if section is not None:
            tiles.switch_section(section)

    cv2.destroyAllWindows()
    midi.destroy()


if __name__ == '__main__':
    main()
