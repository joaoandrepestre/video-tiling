from config import setup_config
from midi import Midi
from tile import render
from gui import setup_gui, draw_gui, destroy_gui


def main():
    setup_config()
    midi = Midi()
    setup_gui()
    should_start = draw_gui(midi)
    if(should_start):
        render(midi)
    destroy_gui()
    midi.destroy()


if __name__ == '__main__':
    main()
