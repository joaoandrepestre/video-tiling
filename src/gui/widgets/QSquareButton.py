from PyQt6.QtWidgets import QPushButton


class QSquareButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        w = self.width()
        self.setFixedSize(140, 140)

    def heightForWidth(self, a0: int) -> int:
        return a0
