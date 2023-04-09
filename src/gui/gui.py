from __future__ import annotations
import sys
from typing import Callable
from threading import Thread
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeyEvent, QIcon
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QCheckBox
)
from gui.widgets.QSelectablesGrid import QSelectablesGrid
from gui.widgets.QLabeledInput import QLabeledIntInput, QLabeledFloatInput
from gui.widgets.QStatusDisplay import QStatusDisplay
from gui.widgets.QTupleInput import QTupleInput
from gui.widgets.QCollapsableSection import QCollapsableSection
from gui.widgets.QMultiProgress import QMultiProgress
from midi.midi import Midi, MidiMessageType
from tiles import tile as T
from config.config import (
    set_config, get_config,
    LANDSCAPE_NUM_CONFIG, PATH_CONFIG, ASPECT_RATIO_CONFIG, FRAMERATE_CONFIG,
    MIDI_PORT_CONFIG, MIDI_CONFIG, KEYBOARD_CONFIG
)
from utils.video_utils import process_videos

WIDTH = 450
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
        self.move(50, 5)
        self.__midi = midi

        # subscribe to midi events
        midi.subscribe(MidiMessageType.NOTE_ON,
                       lambda note, velocity: self.__midi_note_handler(note, velocity))

        # set connection checking timer
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__update_midi_status)
        self.__timer.start(1000)

        # draw gui
        self.setWindowIcon(QIcon('./statics/tile-icon.ico'))
        self.setWindowTitle('Tyler - Config')
        self.setMaximumWidth(WIDTH)
        self.setMaximumHeight(HEIGHT)
        self.setLayout(self.__layout)

        video_section = QCollapsableSection('VIDEO')
        video_vbox = QVBoxLayout()
        video_vbox.addWidget(
            QLabeledIntInput(
                midi,
                'Landscapes',
                default_value=get_config(LANDSCAPE_NUM_CONFIG),
                callback=lambda x: set_config(LANDSCAPE_NUM_CONFIG, x)
            )
        )
        self.__should_crop_videos: bool = False
        hbox = QHBoxLayout()
        checkbox = self.make_checkbox(
            'Crop videos?', self.__checkbox_callback)
        self.__progress = QMultiProgress(
            0, lambda args: process_videos(args[0], self.__should_crop_videos))
        self.__progress.setHidden(True)
        hbox.addWidget(checkbox)
        hbox.addWidget(self.__progress)
        video_vbox.addLayout(hbox)
        self.__sources_button = self.make_button(
            f'Select sources: {get_config(PATH_CONFIG)}', self.__file_callback)
        video_vbox.addWidget(self.__sources_button)
        video_vbox.addWidget(
            QTupleInput(midi, 'Aspect Ratio', 'Width', 'Height',
                        get_config(ASPECT_RATIO_CONFIG),
                        lambda x: set_config(ASPECT_RATIO_CONFIG, x)
                        )
        )
        self.framerate_input = QLabeledFloatInput(
            midi,
            'Framerate',
            11, 33,
            get_config(FRAMERATE_CONFIG),
            lambda x: set_config(FRAMERATE_CONFIG, x)
        )
        video_vbox.addWidget(self.framerate_input)
        video_section.setContentLayout(video_vbox)
        self.__layout.addWidget(video_section)
        video_section.check()

        midi_section = QCollapsableSection('MIDI')
        midi_vbox = QVBoxLayout()
        midi_vbox.addWidget(
            QLabeledIntInput(
                midi,
                'Midi Port',
                default_value=get_config(MIDI_PORT_CONFIG),
                callback=lambda x: set_config(MIDI_PORT_CONFIG, x)
            )
        )
        self.__midi_status = QStatusDisplay('Connected', 'Disconnected')
        midi_vbox.addWidget(self.__midi_status)
        self.selectables_grid = self.make_controls_grid()
        midi_vbox.addWidget(self.selectables_grid)
        midi_section.setContentLayout(midi_vbox)
        self.__layout.addWidget(midi_section)
        midi_section.check()

        start = self.make_button('Start', self.__start_callback)
        self.__layout.addWidget(start)

    def destroy(self):
        if (self.is_rendering()):
            self.__render_thread.join()

    # gui utils
    def make_button(self, title: str, callback: Callable) -> QPushButton:
        button = QPushButton(title)
        button.clicked.connect(callback)
        return button

    def make_controls_grid(self) -> QSelectablesGrid:
        grid = QSelectablesGrid(
            'Define control for each section: (midi | keyboard)')
        midi_map = get_config(MIDI_CONFIG)
        key_map = get_config(KEYBOARD_CONFIG)
        for i in range(len(midi_map)):
            row = int(i / 3)
            column = int(i % 3)
            grid.addSelectable(f'{midi_map[i]} | {key_map[i]}',
                               row, column)
        return grid

    def make_checkbox(self, title: str, callback: Callable) -> QCheckBox:
        checkbox = QCheckBox()
        checkbox.setText(title)
        checkbox.toggled.connect(callback)
        return checkbox

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
        self.__progress.start(dir)

    def __checkbox_callback(self) -> None:
        self.__should_crop_videos = self.sender().isChecked()

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

    def __midi_note_handler(self, note: int, velocity: int) -> None:
        selected_item, index = self.selectables_grid.selected()
        if (selected_item is None):
            return
        if (velocity == 0):
            return
        midi_map = get_config(MIDI_CONFIG)
        key_map = get_config(KEYBOARD_CONFIG)
        midi_map[index] = f'{note}'
        set_config(MIDI_CONFIG, midi_map)
        selected_item.setText(f'{midi_map[index]} | {key_map[index]}')
        self.selectables_grid.cleanSelection()


def draw_gui(midi: Midi):
    app = QApplication(sys.argv)
    window = Window(midi)
    window.show()
    app.exec()
    window.destroy()
