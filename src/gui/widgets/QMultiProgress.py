from typing import Callable, Generator, Any
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel
import time


class Tracker(QObject):
    finished = pyqtSignal()
    initValues = pyqtSignal(tuple)
    updateValues = pyqtSignal(tuple)

    __tracked_function: Callable[[Any],
                                 Generator[tuple[int, int], None, None]] = None
    __args = None

    def __init__(self, func: Callable[[Any], Generator[tuple[int, int], None, None]], args):
        super().__init__()
        self.__tracked_function = func
        self.__args = args

    def doTracking(self):
        start_time = time.time()
        track = self.__tracked_function(self.__args)
        values = next(track)
        self.initValues.emit(values)
        for amnt, cnt, _, msg in track:
            curr_time = time.time()
            elapsed = int(curr_time - start_time)
            self.updateValues.emit((amnt, cnt, elapsed, msg))
        self.finished.emit()


class QMultiProgress(QWidget):
    start = pyqtSignal(str)

    __total: int = 0
    __count: int = 0
    __amount_per_subprocess: list[int] = None

    __eta: int = 0

    __progress_bar: QProgressBar = None
    __counter_label: QLabel = None
    __eta_label: QLabel = None

    __tracking_thread: QThread = None
    __tracker: Tracker = None
    __tracked_function: Callable[[Any],
                                 Generator[tuple[int, int], None, None]] = None

    __window: QWidget = None

    def __init__(self, window: QWidget, total: int = 0, func: Callable[[Any], Generator[tuple[int, int], None, None]] = None) -> None:
        super().__init__()
        self.__window = window
        self.__total = total
        self.__tracked_function = func

        self.start.connect(self.startProcess)

        vbox = QVBoxLayout()
        self.setLayout(vbox)

        hbox = QHBoxLayout()

        self.__progress_bar = QProgressBar()
        self.__counter_label = QLabel(f'{self.__count}/{self.__total}')

        hbox.addWidget(self.__progress_bar)
        hbox.addWidget(self.__counter_label)
        vbox.addLayout(hbox)

        self.__eta_label = QLabel(f'{self.__eta} seconds')

        vbox.addWidget(self.__eta_label)

        self.setHidden(True)

    def setTotal(self, total: int) -> None:
        self.__total = total
        self.__counter_label.setText(f'{self.__count}/{self.__total}')

    def startProcess(self, args):
        self.__progress_bar.setHidden(False)
        self.__counter_label.setHidden(False)
        self.setHidden(False)

        self.__tracker = Tracker(self.__tracked_function, args)
        self.__tracking_thread = QThread()
        self.__tracker.moveToThread(self.__tracking_thread)
        self.__tracker.finished.connect(self.__tracking_thread.quit)
        self.__tracking_thread.finished.connect(self.finish)
        self.__tracking_thread.started.connect(self.__tracker.doTracking)
        self.__tracker.initValues.connect(self.initValues)
        self.__tracker.updateValues.connect(self.update)

        self.__tracking_thread.start()

    def initValues(self, values: tuple[int, int, dict, str]):
        _, total, metadata, msg = values
        if (msg != ''):
            self.__window.alert.emit(msg)
        if (metadata is None):
            return
        self.setTotal(total)
        self.__amount_per_subprocess = metadata['frame_counts']
        self.__window.metadata.emit(metadata)

    def setValue(self, value: int) -> None:
        self.__progress_bar.setValue(value)

    def setCount(self, count: int) -> None:
        self.__count = count
        self.__counter_label.setText(f'{self.__count}/{self.__total}')

    def setETA(self, eta: int) -> None:
        self.__eta = eta
        hours, minutes, seconds = 0, 0, eta
        if (seconds > 60):
            minutes = int(seconds / 60)
            seconds = seconds % 60
        if (minutes > 60):
            hours = int(minutes / 60)
            minutes = minutes % 60
        self.__eta_label.setText(
            f'Time remaining: {hours}h{minutes}m{seconds}s')

    def update(self, values: tuple[int, int, int, str]) -> None:
        amnt, cnt, elapsed, msg = values
        self.setCount(cnt)

        eta = 0
        if (cnt < self.__total):
            current_amount = self.__amount_per_subprocess[cnt]
            self.setValue(int(amnt * 100 / current_amount))

            remaining = current_amount - amnt
            elapsed_amnt = amnt + 0.001  # avoids division by 0
            for i in range(self.__total):
                a = self.__amount_per_subprocess[i]
                if (i < cnt):
                    elapsed_amnt += a
                elif (i > cnt):
                    remaining += a

            unit_time = (elapsed / elapsed_amnt)
            eta = int(unit_time * remaining)

        self.setETA(eta)
        if (msg != ''):
            self.__window.alert.emit(msg)

    def finish(self):
        self.__tracker.deleteLater()
        self.__tracking_thread.deleteLater()

        # hide progress
        self.__progress_bar.setHidden(True)
        self.__counter_label.setHidden(True)

        # Write DONE
        self.__eta_label.setText('Time remaining: DONE!')
        self.__window.progressDone.emit()
