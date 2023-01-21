from PyQt6.QtWidgets import QPushButton


class QSquareButton(QPushButton):
    def __init__(self, text: str, size: int = 100):
        super().__init__(text)
        self.setFixedSize(size, size)

    def heightForWidth(self, a0: int) -> int:
        return a0
