from typing import Callable, Generator, Any
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QLabel


class QMultiProgress(QWidget):
    __total: int = 0
    __count: int = 0

    __progress_bar: QProgressBar = None
    __counter_label: QLabel = None

    __tracked_function: Callable[[Any],
                                 Generator[tuple[int, int], None, None]] = None

    def __init__(self, total: int = 0, func: Callable[[Any], Generator[tuple[int, int], None, None]] = None) -> None:
        super().__init__()
        self.__total = total
        self.__tracked_function = func

        hbox = QHBoxLayout()
        self.setLayout(hbox)

        self.__progress_bar = QProgressBar()
        self.__counter_label = QLabel(f'{self.__count}/{self.__total}')

        hbox.addWidget(self.__progress_bar)
        hbox.addWidget(self.__counter_label)

        self.setHidden(True)

    def setTotal(self, total: int) -> None:
        self.__total = total
        self.__counter_label.setText(f'{self.__count}/{self.__total}')

    def setValue(self, value: int) -> None:
        self.__progress_bar.setValue(value)

    def setCount(self, count: int) -> None:
        self.__count = count
        self.__counter_label.setText(f'{self.__count}/{self.__total}')

    def start(self, *args: Any) -> None:
        self.setHidden(False)
        track = self.__tracked_function(args)
        _, total = next(track)
        self.setTotal(total)
        for pct, cnt in track:
            self.setValue(pct)
            self.setCount(cnt)
