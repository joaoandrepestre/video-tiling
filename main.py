from midi import Midi
from tile import render
from gui import setup_gui, draw_gui, destroy_gui


def main():
    midi = Midi()
    setup_gui()
    should_start = draw_gui(midi)
    if(should_start):
        render(midi)
    destroy_gui()
    midi.destroy()


if __name__ == '__main__':
    main()
