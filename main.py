import threading
from config import setup_config, teardown_config
from midi import Midi
from gui import draw_gui


def main():
    setup_config()
    midi = Midi()
    draw_gui(midi)
    midi.destroy()
    teardown_config()


if __name__ == '__main__':
    main()
