import threading
from config import setup_config
from midi import Midi
from gui import draw_gui
from tile import render


def main():
    setup_config()
    midi = Midi()
    gui_thread = threading.Thread(group=None, target=draw_gui, args=[midi])
    gui_thread.start()

    gui_thread.join()
    midi.destroy()


if __name__ == '__main__':
    main()
