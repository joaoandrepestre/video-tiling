from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel


class QStatusDisplay(QWidget):

    __text_if_true: str = None
    __text_if_false: str = None

    __status: bool = False

    __status_label: QLabel = None

    def __init__(self, true_text: str, false_text: str) -> None:
        super().__init__()
        hbox = QHBoxLayout()
        self.setLayout(hbox)
        label = QLabel('Status: ')
        self.__status_label = QLabel(self.__text_if_false)
        self.__status_label.setStyleSheet('color: red;')

        hbox.addWidget(label)
        hbox.addWidget(self.__status_label)
        self.__text_if_true = true_text
        self.__text_if_false = false_text

    def setStatus(self, value: bool):
        self.__status = value
        text = self.__text_if_true if self.__status else self.__text_if_false
        color = 'green' if self.__status else 'red'
        self.__status_label.setText(text)
        self.__status_label.setStyleSheet(f'color: {color}')
