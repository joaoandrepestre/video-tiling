from typing import Callable
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from gui.widgets.QLabeledInput import QLabeledIntInput
from midi.midi import Midi


class QTupleInput(QWidget):

    __first_input: QLabeledIntInput = None
    __second_input: QLabeledIntInput = None
    __callback: Callable[[tuple[int, int]], None] = lambda: None
    __value: tuple[int, int] = None

    def __init__(self, midi: Midi, main_title: str, first_title: str, second_title: str,
                 default_value: tuple[int, int] = None, callback: Callable[[tuple[int, int]], None] = lambda: None):
        super().__init__()
        self.setMaximumHeight(150)
        vbox = QVBoxLayout()
        self.setLayout(vbox)
        label = QLabel(main_title)
        self.__callback = callback
        self.__value = default_value
        self.__first_input = QLabeledIntInput(
            midi,
            first_title,
            140, 1080,
            default_value=default_value[0],
            callback=lambda x: self.__first_callback(x)
        )
        self.__second_input = QLabeledIntInput(
            midi,
            second_title,
            140, 1080,
            default_value=default_value[1],
            callback=lambda x: self.__second_callback(x)
        )
        vbox.addWidget(label)
        vbox.addWidget(self.__first_input)
        vbox.addWidget(self.__second_input)

    def __first_callback(self, value: int):
        self.__value[0] = value
        self.__callback(self.__value)

    def __second_callback(self, value: int):
        self.__value[1] = value
        self.__callback(self.__value)

    def setValue(self, value: tuple[int, int]):
        self.__first_input.setText(f'{value[0]}')
        self.__second_input.setText(f'{value[1]}')
