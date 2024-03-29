from typing import Callable, Generator, Any
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel
import time
from utils.video_utils import VideoMetadata, ProcessingUpdateMessage


class Tracker(QObject):
    finished = pyqtSignal()
    initValues = pyqtSignal(ProcessingUpdateMessage)
    updateValues = pyqtSignal(ProcessingUpdateMessage)

    __tracked_function: Callable[[Any],
                                 Generator[ProcessingUpdateMessage, None, None]] = None
    __args = None

    def __init__(self, func: Callable[[Any], Generator[ProcessingUpdateMessage, None, None]], args):
        super().__init__()
        self.__tracked_function = func
        self.__args = args

    def doTracking(self):
        start_time = time.time()
        track = self.__tracked_function(self.__args)
        values = next(track)
        self.initValues.emit(values)
        for update in track:
            curr_time = time.time()
            update.elapsed_time = int(curr_time - start_time)
            self.updateValues.emit(update)
        self.finished.emit()


class QMultiProgress(QWidget):
    start = pyqtSignal(str)

    __total: int = 0
    __count: int = 0
    __amount_per_subprocess: list[int] = None
    __total_amount: int = None
    __size_per_subprocess: list[tuple[int, int]] = None

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

        self.__progress_bar = QProgressBar()
        self.__counter_label = QLabel(
            f'Videos processed: {self.__count}/{self.__total}')

        vbox.addWidget(self.__progress_bar)
        vbox.addWidget(self.__counter_label)

        self.__eta_label = QLabel(f'{self.__eta} seconds')

        vbox.addWidget(self.__eta_label)

        self.setHidden(True)

    def setTotal(self, total: int) -> None:
        self.__total = total
        self.__counter_label.setText(
            f'Videos processed: {self.__count}/{self.__total}')

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

    def initValues(self, init: ProcessingUpdateMessage):
        if (init.metadata is None):
            return
        self.setTotal(len(init.metadata.frame_counts))
        self.__amount_per_subprocess = init.metadata.frame_counts
        self.__size_per_subprocess = init.metadata.sizes
        t = 0
        for i in range(len(self.__amount_per_subprocess)):
            size = self.__size_per_subprocess[i]
            amnt = self.__amount_per_subprocess[i]
            t += (amnt * size[0] * size[1])
        self.__total_amount = t

        self.__window.metadata.emit(init.metadata)
        msg = init.message()
        if (msg != ''):
            self.__window.alert.emit(msg)

    def setValue(self, value: int) -> None:
        self.__progress_bar.setValue(value)

    def setCount(self, count: int) -> None:
        self.__count = count
        self.__counter_label.setText(
            f'Videos processed: {self.__count}/{self.__total}')

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

    def update(self, update: ProcessingUpdateMessage) -> None:
        elapsed = update.elapsed_time
        msg = update.message()

        eta = 0

        elapsed_amnt = 0.001  # avoids division by 0
        cnt = 0
        for i in range(self.__total):
            size = self.__size_per_subprocess[i]
            elapsed_amnt += (update.frames_done[i] * size[0] * size[1])
            if (update.frames_done[i] == self.__amount_per_subprocess[i]):
                cnt += 1
        remaining = self.__total_amount - elapsed_amnt

        self.setValue(int(elapsed_amnt * 100 / self.__total_amount))

        unit_time = (elapsed / elapsed_amnt)
        eta = int(unit_time * remaining)

        self.setCount(cnt)
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
