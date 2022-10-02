from tile import render
from gui import setup_gui, draw_gui, destroy_gui


def main():
    setup_gui()
    should_start = draw_gui()
    if(should_start):
        render()
    destroy_gui()


if __name__ == '__main__':
    main()
