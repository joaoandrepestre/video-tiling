from PyQt6.QtWidgets import QWidget, QGridLayout, QPushButton
from gui.widgets.QSquareButton import QSquareButton


class QSelectablesGrid(QWidget):

    __grid: QGridLayout = None
    __selectables: list[QSquareButton] = []
    __selected: QSquareButton = None
    __selected_index: int = None

    def __init__(self) -> None:
        super().__init__()
        self.__grid = QGridLayout()
        self.setLayout(self.__grid)

    def addSelectable(self, text: str, row: int, column: int) -> QSquareButton:
        button = QSquareButton(text)
        button.setCheckable(True)
        button.clicked.connect(self.__select)
        self.__grid.addWidget(button, row, column)
        self.__selectables.append(button)
        return button

    def selected(self) -> tuple[QSquareButton, int]:
        return (self.__selected,
                self.__selected_index)

    def cleanSelection(self):
        self.__selected = None
        self.__selected_index = None
        for selectable in self.__selectables:
            selectable.setChecked(False)

    # callbacks
    def __select(self):
        self.__selected = self.sender()
        for i in range(len(self.__selectables)):
            selectable = self.__selectables[i]
            if (selectable is not self.__selected):
                selectable.setChecked(False)
                continue
            self.__selected_index = i
