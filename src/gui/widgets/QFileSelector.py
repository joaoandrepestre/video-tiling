from typing import Callable
from os.path import expanduser
from collections import OrderedDict
from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QFileDialog, QHBoxLayout
from PyQt6.QtCore import pyqtSignal

FIND = 'Find...'

class ComboBox(QComboBox):
    popup = pyqtSignal()

    def showPopup(self) -> None:
        super().showPopup()
        self.popup.emit()

    def setItems(self, items: list[str]):
        count = self.count()
        for i in range(len(items)):
            if (i < count):
                self.setItemText(i, items[i])
            else:
                self.addItem(items[i])

class QFileSelector(QWidget):

    __dropdown: ComboBox = None

    __latest_selections: list[str] = []
    __file_callback: Callable[[str], None] = None

    __current: str = '~'

    def __init__(self, file_callback: Callable[[str], None], default_dir: str = None) -> None:
        super().__init__()
        self.__file_callback = file_callback
        hbox = QHBoxLayout()
        self.setLayout(hbox)

        title = QLabel('Select sources:')
        hbox.addWidget(title)

        self.__dropdown = ComboBox()
        if (default_dir is not None):
            self.__current = default_dir
            self.__latest_selections.append(default_dir)
            self.__dropdown.setCurrentText(default_dir)
        items = self.__latest_selections + [FIND]
        self.__dropdown.addItems(items)
        self.__dropdown.popup.connect(self.clicked)
        self.__dropdown.currentIndexChanged.connect(self.changed)
        hbox.addWidget(self.__dropdown)



    def setCurrent(self, text: str):
        self.__current = text
        self.__dropdown.setCurrentText(text)

    def updateLatest(self, dir: str):
        latest = [dir] + self.__latest_selections
        self.__latest_selections = list(OrderedDict.fromkeys(latest))
        self.__dropdown.setItems(self.__latest_selections + [FIND])

    def openFileDialog(self, current: str = ''):
        c = current if current != '' else expanduser('~')
        dir: str = QFileDialog.getExistingDirectory(
                self, 'Select scenes directory...', c)
        if (dir == ''):
            return
        self.updateLatest(dir)
        self.setCurrent(dir)
        self.__file_callback(dir)

    def clicked(self):
        if (len(self.__latest_selections) == 0):
            self.openFileDialog()
            self.__dropdown.hidePopup()

    def changed(self):
        text = self.__dropdown.currentText()
        if (text == FIND):
            self.openFileDialog(self.__current)
            return
        if (text == self.__current):
            return
        self.updateLatest(text)
        self.setCurrent(text)
        self.__file_callback(text)