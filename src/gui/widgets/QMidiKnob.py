from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QDial
from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtGui import QMouseEvent
from midi.midi import *


class QMidiKnob(QWidget):
    __knob_number: int = None
    __knob_label: QLabel = None

    __knob_dial: QDial = None

    __callback: Callable[[int], None] = lambda x: None

    def __init__(self, midi: Midi, knob_number: int, default_value: int, callback: Callable[[int], None]) -> None:
        super().__init__()
        self.setMaximumWidth(60)
        self.__knob_number = knob_number
        self.__callback = callback

        hbox = QHBoxLayout()
        self.setLayout(hbox)
        hbox.setContentsMargins(10, 0, 10, 0)
        hbox.setSpacing(0)

        self.__knob_label = QLabel(self.__get_label())

        self.__knob_dial = QDial()
        self.__knob_dial.setValue(default_value)
        self.__knob_dial.setRange(0, 127)
        self.__knob_dial.setSingleStep(1)
        self.__knob_dial.installEventFilter(self)
        self.__knob_dial.valueChanged.connect(self.__dial_value_changed)

        hbox.addWidget(self.__knob_label)
        hbox.addWidget(self.__knob_dial)

        midi.subscribe(MidiMessageType.CONTROL_CHANGE,
                       lambda x, y: self.__redefine_knob_midi_callback(x, y)
                       )
        midi.subscribe(MidiMessageType.CONTROL_CHANGE,
                       lambda x, y: self.__knob_value_changed_midi_callback(
                           x, y)
                       )

    def __dial_value_changed(self, value: int):
        self.__callback(value)

    def __get_label(self) -> str:
        return (f'{self.__knob_number}'
                if self.__knob_number is not None
                else '-'
                )

    def __redefine_knob_midi_callback(self, knob: int, value: int) -> None:
        if (not self.__knob_dial.hasFocus()):
            return
        self.__knob_number = knob
        self.__knob_label.setText(self.__get_label())
        self.__knob_dial.clearFocus()

    def __knob_value_changed_midi_callback(self, knob: int, value: int) -> None:
        if (self.__knob_number != knob):
            return
        self.__knob_dial.setValue(value)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if (source is self.__knob_dial and
                isinstance(
                    event, (QMouseEvent)
                )):
            return True
        return super().eventFilter(source, event)
