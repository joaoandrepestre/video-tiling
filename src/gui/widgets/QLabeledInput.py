from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt
from gui.widgets.QSquareButton import QSquareButton
from typing import Callable, TypeVar, Generic

T = TypeVar('T')


class QLabeledInput(QWidget, Generic[T]):

    _input: QLineEdit = None
    _callback: Callable[[T], None] = lambda: None
    _increment: T = None

    def __init__(self, title: str, default_value: T, callback: Callable[[T], None]):
        super().__init__()
        hbox = QHBoxLayout()
        self.setLayout(hbox)
        label = QLabel(title)
        self._input = QLineEdit(f'{default_value}')
        self._input.setMaximumWidth(50)
        self._callback = callback
        self._input.textChanged.connect(self.__encapsulated_callback)
        minus = QSquareButton('-', 20)
        minus.clicked.connect(self.__decrement)
        plus = QSquareButton('+', 20)
        plus.clicked.connect(self.__increment)
        hbox.addWidget(label, alignment=Qt.AlignmentFlag.AlignLeft)
        hbox.addWidget(self._input, alignment=Qt.AlignmentFlag.AlignAbsolute)
        hbox.addWidget(minus)
        hbox.addWidget(plus)

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

    def setText(self, text: str):
        self._input.setText(text)


class QLabeledIntInput(QLabeledInput[int]):
    def __init__(self, title: str, default_value: int, callback: Callable[[int], None]):
        super().__init__(title, default_value, callback)
        validator = QIntValidator()
        self._input.setValidator(validator)
        self._increment = 1

    def _convert_value(self, value: str) -> int | None:
        try:
            return int(value)
        except ValueError:
            return None


class QLabeledFloatInput(QLabeledInput[float]):
    def __init__(self, title: str, default_value: float, callback: Callable[[float], None]):
        super().__init__(title, default_value, callback)
        validator = QDoubleValidator()
        validator.setDecimals(3)
        self._input.setValidator(validator)
        self._increment = 0.5

    def _convert_value(self, value: str) -> float | None:
        try:
            return float(value)
        except ValueError:
            return None
