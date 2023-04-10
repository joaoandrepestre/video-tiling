from typing import Callable, Generator, Any
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QProgressBar, QLabel


class Tracker(QObject):
    initValues = pyqtSignal(tuple)
    updateValues = pyqtSignal(tuple)

    __tracked_function: Callable[[Any],
                                 Generator[tuple[int, int], None, None]] = None

    def __init__(self, func: Callable[[Any], Generator[tuple[int, int], None, None]]):
        super().__init__()
        self.__tracked_function = func

    def doTracking(self, args):
        track = self.__tracked_function(args)
        values = next(track)
        self.initValues.emit(values)
        for values in track:
            self.updateValues.emit(values)


class QMultiProgress(QWidget):
    start = pyqtSignal(str)

    __total: int = 0
    __count: int = 0

    __progress_bar: QProgressBar = None
    __counter_label: QLabel = None

    __tracking_thread: QThread = QThread()
    __tracker: Tracker = None

    def __init__(self, total: int = 0, func: Callable[[Any], Generator[tuple[int, int], None, None]] = None) -> None:
        super().__init__()
        self.__total = total

        self.__tracker = Tracker(func)
        self.__tracker.moveToThread(self.__tracking_thread)
        self.__tracking_thread.finished.connect(self.__tracker.deleteLater)
        self.start.connect(self.__tracker.doTracking)
        self.__tracker.initValues.connect(lambda v: self.setTotal(v[1]))
        self.__tracker.updateValues.connect(self.update)
        self.__tracking_thread.start()

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
        self.setHidden(False)

    def setValue(self, value: int) -> None:
        self.__progress_bar.setValue(value)

    def setCount(self, count: int) -> None:
        self.__count = count
        self.__counter_label.setText(f'{self.__count}/{self.__total}')

    def update(self, values: tuple[int, int]) -> None:
        self.setValue(values[0])
        self.setCount(values[1])
