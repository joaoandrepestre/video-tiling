from __future__ import annotations
import sys
from typing import Callable
from threading import Thread
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QLayout, QHBoxLayout, QLabel, QLineEdit, QGridLayout, QFileDialog
)
from gui.widgets.QSelectablesGrid import QSelectablesGrid
from midi.midi import Midi, MidiMessageType
from tiles import tile as T
from config.config import (
    set_config, get_config,
    LANDSCAPE_NUM_CONFIG, PATH_CONFIG, FRAMERATE_CONFIG,
    MIDI_PORT_CONFIG, KNOB_CONFIG, MIDI_CONFIG, KEYBOARD_CONFIG,
    DEFAULT_CONFIG
)

WIDTH = 450
HEIGHT = 600


class Window(QWidget):

    # rendering
    __render_thread: Thread = None

    __midi: Midi = None

    # gui layout
    __layout: QVBoxLayout = QVBoxLayout()
    __midi_status: QLabel = None

    __timer: QTimer = None

    def __init__(self, midi: Midi) -> None:
        super().__init__()
        self.__render_thread = Thread(target=T.render, args=[midi])
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
        self.resize(WIDTH, HEIGHT)
        self.setLayout(self.__layout)

        self.__layout.addWidget(QLabel('VIDEO'))
        self.add_left_input_int('Landscapes', get_config(
            LANDSCAPE_NUM_CONFIG), LANDSCAPE_NUM_CONFIG)
        self.__sources_button = self.add_button(
            f'Select sources: {get_config(PATH_CONFIG)}', self.__file_callback)
        self.framerate_input = self.add_left_input_float('Framerate', get_config(
            FRAMERATE_CONFIG), FRAMERATE_CONFIG)

        self.__layout.addWidget(QLabel('MIDI'))
        self.add_left_input_int('Midi Port', get_config(
            MIDI_PORT_CONFIG), MIDI_PORT_CONFIG)
        self.add_left_input_int('Framerate Knob', get_config(
            KNOB_CONFIG), KNOB_CONFIG)
        self.__midi_status = self.add_status_text()
        self.selectables_grid = self.add_controls_grid()

        self.add_button('Start', self.__start_callback)

    # gui utils

    def add_button(self, title: str, callback: Callable, parent: QLayout = None) -> QPushButton:
        parent = self.__layout if parent is None else parent
        button = QPushButton(title)
        button.clicked.connect(callback)
        parent.addWidget(button)
        return button

    def add_left_input_int(self, title: str = '', default_value: int = 0, arg1: str = '') -> QLineEdit:
        hbox = QHBoxLayout()
        label = QLabel(title)
        input = QLineEdit()
        input.setMaximumWidth(20)
        validator = QIntValidator()
        input.setValidator(validator)
        input.setText(f'{default_value}')
        input.textChanged.connect(
            lambda x: Window.__int_input_callback(arg1, x))
        hbox.addWidget(label)
        hbox.addWidget(input)
        self.__layout.addLayout(hbox)
        return input

    def add_left_input_float(self, title: str = '', default_value: float = 0.0, arg1: str = '') -> QWidget:
        hbox = QHBoxLayout()
        label = QLabel(title)
        input = QLineEdit()
        input.setMaximumWidth(100)
        validator = QDoubleValidator()
        validator.setDecimals(3)
        input.setValidator(validator)
        input.setText(f'{default_value}')
        input.textChanged.connect(
            lambda x: Window.__float_input_callback(arg1, x))
        hbox.addWidget(label)
        hbox.addWidget(input)
        self.__layout.addLayout(hbox)
        return input

    def add_status_text(self) -> QWidget:
        hbox = QHBoxLayout()
        label = QLabel('Status: ')
        status = QLabel('Disconnected')
        status.setStyleSheet('color: red;')
        hbox.addWidget(label)
        hbox.addWidget(status)
        self.__layout.addLayout(hbox)
        return status

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
        return self.__render_thread.is_alive()

    # callbacks
    def __start_callback(self) -> None:
        if (not self.is_rendering()):
            self.__render_thread.start()

    def __int_input_callback(key: str, value: str) -> None:
        try:
            int_value = int(value)
            set_config(key, int_value)
        except ValueError:
            pass

    def __float_input_callback(key: str, value: str) -> None:
        try:
            float_value = float(value)
            set_config(key, float_value)
        except ValueError:
            pass

    def __update_midi_status(self) -> None:
        if (self.__midi_status is None):
            return
        status = self.__midi.is_device_connected()
        text = 'Connected' if status else 'Disconnected'
        color = 'green' if status else 'red'
        self.__midi_status.setText(text)
        self.__midi_status.setStyleSheet(f'color: {color}')

    def __file_callback(self) -> None:
        dir = QFileDialog.getExistingDirectory(
            self, 'Select scenes directory...', get_config(PATH_CONFIG))
        set_config(PATH_CONFIG, dir)
        self.__sources_button.setText(f'Select sources: {dir}')

    def keyPressEvent(self, e):
        selected_item, index = self.selectables_grid.selected()
        if (selected_item is None):
            return
        try:
            key = chr(e.key()).upper()
        except ValueError:
            return
        print(key)
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
        window.framerate_input.setText(f'{nfr}')
        set_config(FRAMERATE_CONFIG, nfr)

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
