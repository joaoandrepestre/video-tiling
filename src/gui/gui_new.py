from __future__ import annotations
import sys
from typing import Callable
from threading import Thread
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeyEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLayout, QHBoxLayout, QLabel, QFileDialog
)
from gui.widgets.QSelectablesGrid import QSelectablesGrid
from gui.widgets.QLabeledInput import QLabeledIntInput, QLabeledFloatInput
from gui.widgets.QStatusDisplay import QStatusDisplay
from gui.widgets.QTupleInput import QTupleInput
from midi.midi import Midi, MidiMessageType
from tiles import tile as T
from config.config import (
    set_config, get_config,
    LANDSCAPE_NUM_CONFIG, PATH_CONFIG, ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG,
    MIDI_PORT_CONFIG, KNOB_CONFIG, MIDI_CONFIG, KEYBOARD_CONFIG,
    DEFAULT_CONFIG
)

WIDTH = 330
HEIGHT = 600


class Window(QWidget):

    # rendering
    __render_thread: Thread = None

    __midi: Midi = None

    # gui layout
    __layout: QVBoxLayout = QVBoxLayout()
    __midi_status: QStatusDisplay = None

    __timer: QTimer = None

    def __init__(self, midi: Midi) -> None:
        super().__init__()
        self.__midi = midi

        # subscribe to midi events
        midi.subscribe(MidiMessageType.CONTROL_CHANGE,
                       lambda knob, value: Window.__midi_knob_handler(self, knob, value))
        midi.subscribe(MidiMessageType.NOTE_ON,
                       lambda note, velocity: Window.__midi_note_handler(self, note, velocity))

        # set connection checking timer
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__update_midi_status)
        self.__timer.start(1000)

        # draw gui
        self.setWindowIcon(QIcon('./statics/tile-icon.ico'))
        self.setWindowTitle('Tyler - Config')
        self.resize(WIDTH, HEIGHT)
        self.setLayout(self.__layout)

        self.__layout.addWidget(QLabel('VIDEO'))
        self.__layout.addWidget(
            QLabeledIntInput(
                'Landscapes',
                get_config(LANDSCAPE_NUM_CONFIG),
                lambda x: set_config(LANDSCAPE_NUM_CONFIG, x)
            )
        )
        self.__sources_button = self.add_button(
            f'Select sources: {get_config(PATH_CONFIG)}', self.__file_callback)
        self.__layout.addWidget(
            QTupleInput('Aspect Ratio', 'Width', 'Height',
                        get_config(ASPECT_RATIO_CONFIG),
                        lambda x: set_config(ASPECT_RATIO_CONFIG, x)
                        )
        )
        self.framerate_input = QLabeledFloatInput(
            'Framerate',
            get_config(FRAMERATE_CONFIG),
            lambda x: set_config(FRAMERATE_CONFIG, x)
        )
        self.__layout.addWidget(self.framerate_input)

        self.__layout.addWidget(QLabel('MIDI'))
        self.__layout.addWidget(
            QLabeledIntInput(
                'Midi Port',
                get_config(MIDI_PORT_CONFIG),
                lambda x: set_config(MIDI_PORT_CONFIG, x)
            )
        )
        self.__layout.addWidget(
            QLabeledIntInput(
                'Framerate Knob',
                get_config(KNOB_CONFIG),
                lambda x: set_config(KNOB_CONFIG, x)
            )
        )
        self.__midi_status = QStatusDisplay('Connected', 'Disconnected')
        self.__layout.addWidget(self.__midi_status)
        self.selectables_grid = self.add_controls_grid()

        self.add_button('Start', self.__start_callback)

    def destroy(self):
        if (self.is_rendering()):
            self.__render_thread.join()

    # gui utils
    def add_button(self, title: str, callback: Callable, parent: QLayout = None) -> QPushButton:
        parent = self.__layout if parent is None else parent
        button = QPushButton(title)
        button.clicked.connect(callback)
        parent.addWidget(button)
        return button

    def add_controls_grid(self) -> QSelectablesGrid:
        label = QLabel('Define control for each section: (midi | keyboard)')
        grid = QSelectablesGrid()
        midi_map = get_config(MIDI_CONFIG)
        key_map = get_config(KEYBOARD_CONFIG)
        for i in range(len(midi_map)):
            row = int(i / 3)
            column = int(i % 3)
            grid.addSelectable(f'{midi_map[i]} | {key_map[i]}',
                               row, column)
        self.__layout.addWidget(label)
        self.__layout.addWidget(grid)
        return grid

    def is_rendering(self) -> bool:
        return self.__render_thread is not None and self.__render_thread.is_alive()

    # callbacks
    def __start_callback(self) -> None:
        if (not self.is_rendering()):
            self.__render_thread = Thread(target=T.render, args=[self.__midi])
            self.__render_thread.start()

    def __update_midi_status(self) -> None:
        if (self.__midi_status is None):
            return
        status = self.__midi.is_device_connected()
        self.__midi_status.setStatus(status)

    def __file_callback(self) -> None:
        dir = QFileDialog.getExistingDirectory(
            self, 'Select scenes directory...', get_config(PATH_CONFIG))
        set_config(PATH_CONFIG, dir)
        self.__sources_button.setText(f'Select sources: {dir}')

    def keyPressEvent(self, e: QKeyEvent):
        selected_item, index = self.selectables_grid.selected()
        if (selected_item is None):
            return
        try:
            key = chr(e.key()).upper()
        except ValueError:
            return
        midi_map = get_config(MIDI_CONFIG)
        key_map = get_config(KEYBOARD_CONFIG)
        key_map[index] = key
        set_config(KEYBOARD_CONFIG, key_map)
        selected_item.setText(f'{midi_map[index]} | {key_map[index]}')
        self.selectables_grid.cleanSelection()

    def __midi_knob_handler(window: Window, knob: int, value: int) -> None:
        knob_config = get_config(KNOB_CONFIG)
        if (window.framerate_input is None):
            return
        if (knob != knob_config):
            return
        default = DEFAULT_CONFIG[FRAMERATE_CONFIG]
        nfr = (value / 127.0) * default + default / 2.0
        window.framerate_input.setText('%.3f' % nfr)

    def __midi_note_handler(window: Window, note: int, velocity: int) -> None:
        selected_item, index = window.selectables_grid.selected()
        if (selected_item is None):
            return
        if (velocity == 0):
            return
        midi_map = get_config(MIDI_CONFIG)
        key_map = get_config(KEYBOARD_CONFIG)
        midi_map[index] = f'{note}'
        set_config(MIDI_CONFIG, midi_map)
        selected_item.setText(f'{midi_map[index]} | {key_map[index]}')
        window.selectables_grid.cleanSelection()


def draw_gui(midi: Midi):
    app = QApplication(sys.argv)
    window = Window(midi)
    window.show()
    app.exec()
    window.destroy()
