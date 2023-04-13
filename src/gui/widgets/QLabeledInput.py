from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt
from gui.widgets.QSquareButton import QSquareButton
from gui.widgets.QMidiKnob import QMidiKnob
from typing import Callable, TypeVar, Generic
from midi.midi import Midi

T = TypeVar('T')


class QLabeledInput(QWidget, Generic[T]):

    _input: QLineEdit = None
    _callback: Callable[[T], None] = lambda: None
    _increment: T = None

    _min_value: T = None
    _max_value: T = None

    def __init__(self, midi: Midi, title: str, min: T, max: T, default_value: T, callback: Callable[[T], None], extra_buttons: bool):
        super().__init__()
        self.setMaximumHeight(60)
        hbox = QHBoxLayout()
        self.setLayout(hbox)
        label = QLabel(title)
        self._input = QLineEdit(f'{default_value}')
        self._input.setMaximumWidth(50)
        self._callback = callback
        self._min_value = min
        self._max_value = max
        self._input.textChanged.connect(self.__encapsulated_callback)
        hbox.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addWidget(self._input, alignment=Qt.AlignmentFlag.AlignAbsolute)

        if (extra_buttons):
            dial = QMidiKnob(midi, None, int(default_value),
                             lambda x:  self._dial_change(x))

            minus = QSquareButton('-', 20)
            minus.clicked.connect(self.__decrement)
            plus = QSquareButton('+', 20)
            plus.clicked.connect(self.__increment)
            hbox.addWidget(minus)
            hbox.addWidget(plus)
            hbox.addWidget(dial)

    def _convert_value(value: str) -> T | None:
        pass

    def __encapsulated_callback(self, value: str) -> None:
        v = self._convert_value(value)
        if (v is None):
            return
        self._callback(v)

    def __decrement(self):
        value = self._convert_value(self._input.text())
        if (value is None):
            return
        value -= self._increment
        self._input.setText(f'{value}')

    def __increment(self):
        value = self._convert_value(self._input.text())
        if (value is None):
            return
        value += self._increment
        self._input.setText(f'{value}')

    def _dial_change(self, value: int):
        pass

    def setText(self, text: str):
        self._input.setText(text)


class QLabeledIntInput(QLabeledInput[int]):
    def __init__(self, midi: Midi, title: str, min: int = 0, max: int = 127, default_value: int = 0, callback: Callable[[int], None] = None, extra_buttons: bool = False):
        super().__init__(midi, title, min, max, default_value, callback, extra_buttons)
        validator = QIntValidator()
        self._input.setValidator(validator)
        self._increment = 1

    def _convert_value(self, value: str) -> int | None:
        try:
            return int(value)
        except ValueError:
            return None

    def _dial_change(self, value: int):
        delta = self._max_value - self._min_value
        v = int(self._min_value + delta*(value / 127))
        self.setText(f'{v}')


class QLabeledFloatInput(QLabeledInput[float]):
    def __init__(self, midi: Midi, title: str, min: float, max: float, default_value: float, callback: Callable[[float], None], extra_buttons: bool = False):
        super().__init__(midi, title, min, max, default_value, callback, extra_buttons)
        validator = QDoubleValidator(min, max, 3)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self._input.setValidator(validator)
        self._increment = 0.5

    def _convert_value(self, value: str) -> float | None:
        v = value.replace(',', '.')
        try:
            return float(v)
        except ValueError:
            return None

    def _dial_change(self, value: int):
        delta = self._max_value - self._min_value
        v = float(self._min_value + delta*(value / 127.0))
        self.setText('%.3f' % v)

    def setText(self, text: str):
        v = self._convert_value(text)
        if (v is None):
            return
        return super().setText(f'{v:.3f}')
